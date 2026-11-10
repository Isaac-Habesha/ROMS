from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from apps.accounts.decorators import supervisor_required
from apps.orders.models import Order, OrderStatusHistory
from apps.approvals.models import OrderApproval
from apps.audit.services import log_action, get_client_ip


@login_required
@supervisor_required
def supervisor_dashboard(request):
    pending = Order.objects.filter(status=Order.Status.PENDING_APPROVAL)
    approved = Order.objects.filter(status=Order.Status.APPROVED)
    kitchen_active = Order.objects.filter(status__in=[Order.Status.RECEIVED, Order.Status.PREPARING])
    ready = Order.objects.filter(status=Order.Status.READY)
    rejected = Order.objects.filter(status=Order.Status.REJECTED)

    context = {
        'pending_count': pending.count(),
        'approved_count': approved.count(),
        'kitchen_active_count': kitchen_active.count(),
        'ready_count': ready.count(),
        'rejected_count': rejected.count(),
        'incoming_orders': pending[:15],
    }
    return render(request, 'supervisor/dashboard.html', context)


@login_required
@supervisor_required
def pending_orders(request):
    orders = Order.objects.filter(status=Order.Status.PENDING_APPROVAL).select_related('waiter').prefetch_related('items__meal')
    return render(request, 'supervisor/pending_orders.html', {'orders': orders})


@login_required
@supervisor_required
def order_history(request):
    orders = Order.objects.exclude(status=Order.Status.PENDING_APPROVAL).select_related('waiter').prefetch_related('items__meal')
    return render(request, 'supervisor/order_history.html', {'orders': orders})


@login_required
@supervisor_required
def review_order(request, order_id):
    order = get_object_or_404(Order.objects.select_related('waiter').prefetch_related('items__meal'), id=order_id)
    return render(request, 'supervisor/review_order.html', {'order': order})


@login_required
@supervisor_required
@require_POST
def approve_order(request, order_id):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)
        
        # Prevent duplicate approval
        if order.status != Order.Status.PENDING_APPROVAL:
            messages.warning(request, f'Order {order.order_reference} is already {order.get_status_display()}.')
            return redirect('approvals:supervisor_dashboard')

        # Generate unique order number (e.g. #ORD-0001)
        last_order = Order.objects.exclude(order_number__isnull=True).exclude(order_number='').order_by('-id').first()
        next_num = 1
        if last_order and last_order.order_number:
            try:
                num_str = last_order.order_number.replace('#ORD-', '').replace('ORD-', '')
                next_num = int(num_str) + 1
            except ValueError:
                next_num = order.id
        
        order.order_number = f"#ORD-{next_num:04d}"
        order.status = Order.Status.APPROVED
        order.approved_at = timezone.now()
        order.save(update_fields=['order_number', 'status', 'approved_at'])

        # Create or update approval record
        OrderApproval.objects.update_or_create(
            order=order,
            defaults={
                'supervisor': request.user,
                'decision': OrderApproval.Decision.APPROVED,
                'rejection_reason': '',
            }
        )

        # Create kitchen ticket (from kitchen app)
        from apps.kitchen.models import KitchenTicket
        KitchenTicket.objects.get_or_create(
            order=order,
            defaults={
                'ticket_number': f"TKT-{order.order_number.replace('#', '')}",
            }
        )

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=Order.Status.PENDING_APPROVAL,
            new_status=Order.Status.APPROVED,
            changed_by=request.user,
            notes=f'Approved by supervisor {request.user.get_full_name() or request.user.username}'
        )

        log_action(
            user=request.user,
            action='ORDER_APPROVED',
            description=f'Order {order.order_number} ({order.order_reference}) approved and kitchen ticket generated.',
            entity_type='Order',
            entity_id=order.id,
            ip_address=get_client_ip(request)
        )

        messages.success(request, f'Order {order.order_number} approved and dispatched to kitchen!')
        return redirect('kitchen:print_ticket', order_id=order.id)


@login_required
@supervisor_required
@require_POST
def reject_order(request, order_id):
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    if not rejection_reason:
        messages.error(request, 'A rejection reason is mandatory.')
        return redirect('approvals:review_order', order_id=order_id)

    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)
        if order.status != Order.Status.PENDING_APPROVAL:
            messages.warning(request, f'Order {order.order_reference} cannot be rejected.')
            return redirect('approvals:supervisor_dashboard')

        order.status = Order.Status.REJECTED
        order.rejection_reason = rejection_reason
        order.save(update_fields=['status', 'rejection_reason'])

        OrderApproval.objects.update_or_create(
            order=order,
            defaults={
                'supervisor': request.user,
                'decision': OrderApproval.Decision.REJECTED,
                'rejection_reason': rejection_reason,
            }
        )

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=Order.Status.PENDING_APPROVAL,
            new_status=Order.Status.REJECTED,
            changed_by=request.user,
            notes=f'Rejected: {rejection_reason}'
        )

        log_action(
            user=request.user,
            action='ORDER_REJECTED',
            description=f'Order {order.order_reference} rejected. Reason: {rejection_reason}',
            entity_type='Order',
            entity_id=order.id,
            ip_address=get_client_ip(request)
        )

        messages.info(request, f'Order {order.order_reference} was rejected and waiter notified.')
        return redirect('approvals:supervisor_dashboard')

