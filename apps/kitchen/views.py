from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from apps.accounts.decorators import kitchen_staff_required, supervisor_required, role_required
from apps.orders.models import Order, OrderStatusHistory
from apps.kitchen.models import KitchenTicket, KitchenStatusHistory
from apps.restaurants.models import Restaurant
from apps.audit.services import log_action, get_client_ip


@login_required
@kitchen_staff_required
def kitchen_dashboard(request):
    # Only approved and dispatched orders reach the kitchen!
    kitchen_orders = Order.objects.filter(
        status__in=[Order.Status.APPROVED, Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY]
    ).select_related('waiter').prefetch_related('items__meal').order_by('approved_at')

    new_qs = kitchen_orders.filter(status__in=[Order.Status.APPROVED, Order.Status.RECEIVED])
    prep_qs = kitchen_orders.filter(status=Order.Status.PREPARING)
    ready_qs = kitchen_orders.filter(status=Order.Status.READY)

    new_count = new_qs.count()
    prep_count = prep_qs.count()
    ready_count = ready_qs.count()

    context = {
        'new_orders': new_qs,
        'preparing_orders': prep_qs,
        'ready_orders': ready_qs,
        'new_count': new_count,
        'preparing_count': prep_count,
        'ready_count': ready_count,
        'active_count': new_count + prep_count,
    }
    return render(request, 'kitchen/dashboard.html', context)


@login_required
@kitchen_staff_required
@require_POST
def update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    valid_transitions = {
        Order.Status.APPROVED: [Order.Status.RECEIVED],
        Order.Status.RECEIVED: [Order.Status.PREPARING],
        Order.Status.PREPARING: [Order.Status.READY],
    }

    if new_status in [Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY]:
        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status'])

        KitchenStatusHistory.objects.create(
            order=order,
            status=new_status,
            updated_by=request.user,
            notes=f'Status updated from {old_status} to {new_status}'
        )

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes='Kitchen progress update'
        )

        log_action(
            user=request.user,
            action='ORDER_STATUS_CHANGED',
            description=f'Order {order.order_number} marked {new_status} by kitchen staff.',
            entity_type='Order',
            entity_id=order.id,
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Order {order.order_number} updated to {new_status}.')

    return redirect('kitchen:kitchen_dashboard')


@login_required
def print_ticket(request, order_id):
    order = get_object_or_404(Order.objects.select_related('waiter').prefetch_related('items__meal'), id=order_id)
    restaurant = Restaurant.objects.first()
    ticket, _ = KitchenTicket.objects.get_or_create(
        order=order,
        defaults={'ticket_number': f"TKT-{order.order_number.replace('#', '') if order.order_number else order.order_reference}"}
    )
    
    supervisor_approval = getattr(order, 'approval_record', None)
    supervisor_name = supervisor_approval.supervisor.get_full_name() if supervisor_approval and supervisor_approval.supervisor else 'Supervisor'

    context = {
        'order': order,
        'ticket': ticket,
        'restaurant': restaurant,
        'supervisor_name': supervisor_name,
        'total_items_count': sum(item.quantity for item in order.items.all()),
    }
    return render(request, 'kitchen/ticket.html', context)


@login_required
@require_POST
def record_print(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    ticket, _ = KitchenTicket.objects.get_or_create(
        order=order,
        defaults={'ticket_number': f"TKT-{order.order_number.replace('#', '') if order.order_number else order.order_reference}"}
    )
    now = timezone.now()
    if not ticket.first_printed_at:
        ticket.first_printed_at = now
    ticket.last_printed_at = now
    ticket.printed_count += 1
    ticket.save()

    log_action(
        user=request.user,
        action='TICKET_PRINTED',
        description=f'Kitchen ticket for order {order.order_number} printed (print count: {ticket.printed_count}).',
        entity_type='KitchenTicket',
        entity_id=ticket.id,
        ip_address=get_client_ip(request)
    )

    return JsonResponse({'status': 'ok', 'printed_count': ticket.printed_count})


@login_required
def active_orders_api(request):
    """API endpoint for live dashboard polling."""
    orders = Order.objects.filter(
        status__in=[Order.Status.APPROVED, Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY]
    ).select_related('waiter').prefetch_related('items__meal').order_by('approved_at')

    data = []
    for o in orders:
        data.append({
            'id': o.id,
            'order_number': o.order_number or o.order_reference,
            'status': o.status,
            'customer_count': o.customer_count,
            'waiter': o.waiter.get_full_name() or o.waiter.username,
            'created_at': o.created_at.strftime('%H:%M:%S'),
            'approved_at': o.approved_at.strftime('%H:%M:%S') if o.approved_at else None,
            'items': [
                {
                    'name': item.meal.name,
                    'quantity': item.quantity,
                    'instructions': item.special_instructions,
                }
                for item in o.items.all()
            ]
        })
    return JsonResponse({'orders': data})

