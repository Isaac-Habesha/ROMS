from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.accounts.decorators import role_required
from apps.orders.models import Order, OrderStatusHistory
from apps.payments.models import Payment
from apps.audit.services import log_action, get_client_ip
from decimal import Decimal


@login_required
def payment_list(request):
    payments = Payment.objects.select_related('order', 'recorded_by').all()
    return render(request, 'payments/payment_list.html', {'payments': payments})


@login_required
@require_POST
def record_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    amount_str = request.POST.get('amount', str(order.total_amount))
    method = request.POST.get('payment_method', Payment.Method.CASH)
    notes = request.POST.get('notes', '')

    try:
        amount = Decimal(amount_str)
    except Exception:
        amount = order.total_amount

    payment = Payment.objects.create(
        order=order,
        amount=amount,
        payment_method=method,
        status=Payment.Status.COMPLETED,
        recorded_by=request.user,
        notes=notes,
    )

    # Mark order as SERVED once payment is collected
    previous_status = order.status
    order.status = Order.Status.SERVED
    order.save(update_fields=['status'])

    OrderStatusHistory.objects.create(
        order=order,
        previous_status=previous_status,
        new_status=Order.Status.SERVED,
        changed_by=request.user,
        notes=f'Payment of ${amount:.2f} recorded via {payment.get_payment_method_display()}. Order marked as Served.'
    )

    log_action(
        user=request.user,
        action='PAYMENT_RECORDED',
        description=f'Payment of ${amount:.2f} recorded for order {order.order_number or order.order_reference} via {payment.get_payment_method_display()} by {request.user.get_full_name() or request.user.username}. Order marked as Served.',
        entity_type='Payment',
        entity_id=payment.id,
        ip_address=get_client_ip(request)
    )

    log_action(
        user=request.user,
        action='ORDER_SERVED',
        description=f'Order {order.order_number or order.order_reference} marked as Served after payment collected.',
        entity_type='Order',
        entity_id=order.id,
        ip_address=get_client_ip(request)
    )

    messages.success(request, f'Payment of ${amount:.2f} for Order {order.order_number or order.order_reference} confirmed. Order marked as Served!')
    
    # Redirect back to where the user came from or to order detail
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('orders:order_detail', order_id=order.id)

