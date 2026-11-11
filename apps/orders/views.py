from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import waiter_required
from apps.menu.models import Meal, MealCategory
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.audit.services import log_action, get_client_ip
from django.utils import timezone


@login_required
@waiter_required
def waiter_dashboard(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(waiter=request.user, created_at__date=today)
    
    context = {
        'total_today': today_orders.count(),
        'pending_count': today_orders.filter(status=Order.Status.PENDING_APPROVAL).count(),
        'approved_count': today_orders.filter(status__in=[Order.Status.APPROVED, Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY]).count(),
        'served_count': today_orders.filter(status=Order.Status.SERVED).count(),
        'rejected_count': today_orders.filter(status=Order.Status.REJECTED).count(),
        'recent_orders': Order.objects.filter(waiter=request.user)[:10],
    }
    return render(request, 'waiter/dashboard.html', context)


@login_required
@waiter_required
def create_order(request):
    categories = MealCategory.objects.filter(is_active=True).prefetch_related('meals')
    available_meals = Meal.objects.filter(is_available=True, is_archived=False)
    
    if request.method == 'POST':
        customer_count = request.POST.get('customer_count', 1)
        order_notes = request.POST.get('order_notes', '')
        meal_ids = request.POST.getlist('meal_id[]')
        quantities = request.POST.getlist('quantity[]')
        instructions = request.POST.getlist('instructions[]')
        
        if not meal_ids:
            messages.error(request, 'Please select at least one meal.')
            return redirect('orders:create_order')
            
        order = Order.objects.create(
            waiter=request.user,
            customer_count=int(customer_count or 1),
            order_notes=order_notes,
            status=Order.Status.PENDING_APPROVAL,
            submitted_at=timezone.now(),
        )
        
        total = 0
        for m_id, qty, note in zip(meal_ids, quantities, instructions):
            try:
                qty_int = int(qty)
                if qty_int <= 0:
                    continue
                meal = Meal.objects.get(id=m_id, is_available=True, is_archived=False)
                subtotal = meal.price * qty_int
                total += subtotal
                OrderItem.objects.create(
                    order=order,
                    meal=meal,
                    quantity=qty_int,
                    unit_price=meal.price,
                    subtotal=subtotal,
                    special_instructions=note,
                )
            except (Meal.DoesNotExist, ValueError):
                continue
                
        order.total_amount = total
        order.save(update_fields=['total_amount'])
        
        OrderStatusHistory.objects.create(
            order=order,
            previous_status='',
            new_status=Order.Status.PENDING_APPROVAL,
            changed_by=request.user,
            notes='Initial order submitted for supervisor approval'
        )
        
        log_action(
            user=request.user,
            action='ORDER_SUBMITTED',
            description=f'Order {order.order_reference} created with {order.items.count()} items, total ${total:.2f}',
            entity_type='Order',
            entity_id=order.id,
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f'Order {order.order_reference} submitted successfully!')
        return redirect('orders:waiter_orders')
        
    return render(request, 'waiter/create_order.html', {
        'categories': categories,
        'meals': available_meals,
    })


@login_required
@waiter_required
def waiter_orders(request):
    status_filter = request.GET.get('status', 'all')
    orders = Order.objects.filter(waiter=request.user)
    
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
        
    return render(request, 'waiter/orders_list.html', {
        'orders': orders,
        'current_status': status_filter,
        'status_choices': Order.Status.choices,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def live_notifications_api(request):
    """
    Lightweight polling API that returns recent pending orders, approvals, or kitchen tickets
    based on the logged-in user's role.
    """
    from django.http import JsonResponse
    user = request.user
    notifications = []
    unread_count = 0

    if user.role in ['ADMIN', 'SUPERVISOR']:
        # Fetch pending orders waiting for approval
        pending_qs = Order.objects.filter(status=Order.Status.PENDING_APPROVAL).order_by('-created_at')[:8]
        unread_count = pending_qs.count()
        for ord_obj in pending_qs:
            notifications.append({
                'id': ord_obj.id,
                'title': f'New Order: {ord_obj.order_reference}',
                'body': f'Waiter {ord_obj.waiter.get_full_name() or ord_obj.waiter.username} submitted an order for {ord_obj.customer_count} guests (${ord_obj.total_amount}).',
                'time': ord_obj.created_at.strftime('%H:%M'),
                'url': f'/approvals/review/{ord_obj.id}/',
                'type': 'order'
            })
    elif user.role == 'KITCHEN_STAFF':
        # Fetch orders approved for kitchen
        kitchen_qs = Order.objects.filter(status=Order.Status.APPROVED).order_by('-approved_at')[:8]
        unread_count = kitchen_qs.count()
        for ord_obj in kitchen_qs:
            notifications.append({
                'id': ord_obj.id,
                'title': f'Kitchen Ticket Ready: {ord_obj.order_number or ord_obj.order_reference}',
                'body': f'{ord_obj.items.count()} items to cook for {ord_obj.customer_count} guests.',
                'time': ord_obj.approved_at.strftime('%H:%M') if ord_obj.approved_at else '',
                'url': '/kitchen/dashboard/',
                'type': 'kitchen'
            })
    elif user.role == 'WAITER':
        # Fetch orders recently ready for serving or rejected
        waiter_updates = Order.objects.filter(
            waiter=user,
            status__in=[Order.Status.READY, Order.Status.REJECTED]
        ).order_by('-updated_at')[:8]
        unread_count = waiter_updates.count()
        for ord_obj in waiter_updates:
            status_text = 'READY TO SERVE' if ord_obj.status == Order.Status.READY else 'REJECTED'
            notifications.append({
                'id': ord_obj.id,
                'title': f'Order {ord_obj.order_number or ord_obj.order_reference}: {status_text}',
                'body': ord_obj.rejection_reason if ord_obj.status == Order.Status.REJECTED else 'Dishes are ready for table serving!',
                'time': ord_obj.updated_at.strftime('%H:%M'),
                'url': f'/orders/waiter/orders/{ord_obj.id}/',
                'type': 'status'
            })

    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications
    })


@login_required
@waiter_required
def resubmit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, waiter=request.user, status=Order.Status.REJECTED)
    if request.method == 'POST':
        order.status = Order.Status.PENDING_APPROVAL
        order.submitted_at = timezone.now()
        order.save(update_fields=['status', 'submitted_at'])
        
        OrderStatusHistory.objects.create(
            order=order,
            previous_status=Order.Status.REJECTED,
            new_status=Order.Status.PENDING_APPROVAL,
            changed_by=request.user,
            notes='Order corrected and resubmitted by waiter'
        )
        messages.success(request, f'Order {order.order_reference} has been resubmitted.')
        return redirect('orders:waiter_orders')
    return redirect('orders:order_detail', order_id=order.id)

