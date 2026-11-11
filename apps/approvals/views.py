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

        # Generate unique order number (e.g. #ORD-0006) by scanning existing orders safely
        import re
        max_num = 0
        for o in Order.objects.exclude(order_number__isnull=True).exclude(order_number=''):
            m = re.search(r'\d+', o.order_number)
            if m:
                val = int(m.group(0))
                if val > max_num:
                    max_num = val
        next_num = max(max_num + 1, order.id)
        candidate_num = f"#ORD-{next_num:04d}"
        
        # Ensure candidate_num is strictly unique in DB
        while Order.objects.filter(order_number=candidate_num).exists():
            next_num += 1
            candidate_num = f"#ORD-{next_num:04d}"
        
        order.order_number = candidate_num
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

        # Create kitchen ticket (from kitchen app) safely ensuring unique ticket_number
        from apps.kitchen.models import KitchenTicket
        tkt_num = f"TKT-{order.order_number.replace('#', '')}"
        counter = 1
        base_tkt = tkt_num
        while KitchenTicket.objects.filter(ticket_number=tkt_num).exclude(order=order).exists():
            tkt_num = f"{base_tkt}-{counter}"
            counter += 1

        KitchenTicket.objects.update_or_create(
            order=order,
            defaults={
                'ticket_number': tkt_num,
                'status': KitchenTicket.Status.RECEIVED,
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

