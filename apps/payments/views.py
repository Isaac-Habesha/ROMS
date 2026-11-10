from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.accounts.decorators import role_required
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.audit.services import log_action, get_client_ip
from decimal import Decimal


@login_required
@role_required('ADMIN', 'SUPERVISOR')
def payment_list(request):
    payments = Payment.objects.select_related('order', 'recorded_by').all()
    return render(request, 'payments/payment_list.html', {'payments': payments})


@login_required
@role_required('ADMIN', 'SUPERVISOR')
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

    log_action(
        user=request.user,
        action='PAYMENT_RECORDED',
        description=f'Payment of ${amount:.2f} recorded for order {order.order_number or order.order_reference} via {payment.get_payment_method_display()}.',
        entity_type='Payment',
        entity_id=payment.id,
        ip_address=get_client_ip(request)
    )

    messages.success(request, f'Payment of ${amount:.2f} recorded successfully!')
    return redirect('orders:order_detail', order_id=order.id)

