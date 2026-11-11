import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, F
from decimal import Decimal
from apps.accounts.decorators import admin_required
from apps.accounts.models import CustomUser
from apps.accounts.forms import UserCreateForm, UserUpdateForm
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.menu.models import Meal
from apps.audit.models import AuditLog
from apps.audit.services import log_action, get_client_ip


@login_required
@admin_required
def admin_dashboard(request):
    now = timezone.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Orders count
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_week = Order.objects.filter(created_at__date__gte=week_start).count()
    orders_month = Order.objects.filter(created_at__date__gte=month_start).count()

    # Revenue MUST be from completed payments (as specified: do not treat approved order as collected revenue!)
    rev_today = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    rev_week = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date__gte=week_start).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    rev_month = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    # Status counts
    pending_orders = Order.objects.filter(status=Order.Status.PENDING_APPROVAL).count()
    ready_orders = Order.objects.filter(status=Order.Status.READY).count()
    cancelled_orders = Order.objects.filter(status=Order.Status.CANCELLED).count()
    avg_order_val = Order.objects.filter(status__in=[Order.Status.APPROVED, Order.Status.READY, Order.Status.SERVED]).aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00')

    # Top popular meals
    popular_meals = OrderItem.objects.filter(order__status__in=[Order.Status.APPROVED, Order.Status.RECEIVED, Order.Status.PREPARING, Order.Status.READY, Order.Status.SERVED]).values(
        'meal__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum('subtotal'),
        order_count=Count('id')
    ).order_by('-total_qty')[:7]

    # Last 7 days revenue for Chart.js
    daily_labels = []
    daily_revenue_data = []
    daily_orders_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%b %d')
        daily_labels.append(day_str)
        day_rev = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date=day).aggregate(Sum('amount'))['amount__sum'] or 0
        day_ord = Order.objects.filter(created_at__date=day).count()
        daily_revenue_data.append(float(day_rev))
        daily_orders_data.append(day_ord)

    context = {
        'orders_today': orders_today,
        'orders_week': orders_week,
        'orders_month': orders_month,
        'rev_today': rev_today,
        'rev_week': rev_week,
        'rev_month': rev_month,
        'pending_orders': pending_orders,
        'ready_orders': ready_orders,
        'cancelled_orders': cancelled_orders,
        'avg_order_val': avg_order_val,
        'popular_meals': popular_meals,
        'recent_orders': Order.objects.select_related('waiter').order_by('-created_at')[:10],
        'recent_logs': AuditLog.objects.select_related('user').order_by('-created_at')[:4],
        'chart_labels': daily_labels,
        'chart_revenue': daily_revenue_data,
        'chart_orders': daily_orders_data,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@admin_required
def all_orders(request):
    status_filter = request.GET.get('status', 'all')
    orders = Order.objects.select_related('waiter').prefetch_related('items__meal').order_by('-created_at')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    return render(request, 'admin_dashboard/all_orders.html', {
        'orders': orders,
        'current_status': status_filter,
        'status_choices': Order.Status.choices,
    })


@login_required
@admin_required
def reports_view(request):
    today = timezone.localdate()
    period = request.GET.get('period', '7')
    days = int(period) if period.isdigit() else 7
    start_date = today - timedelta(days=days)

    payments = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__date__gte=start_date)
    gross_sales = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_payments_count = payments.count()
    avg_txn = gross_sales / total_payments_count if total_payments_count > 0 else Decimal('0.00')

    orders = Order.objects.filter(created_at__date__gte=start_date)
    total_orders = orders.count()

    popular_meals = OrderItem.objects.filter(order__created_at__date__gte=start_date).values(
        'meal__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum('subtotal')
    ).order_by('-total_qty')[:10]

    context = {
        'days': days,
        'gross_sales': gross_sales,
        'total_payments_count': total_payments_count,
        'avg_txn': avg_txn,
        'total_orders': total_orders,
        'popular_meals': popular_meals,
    }
    return render(request, 'admin_dashboard/reports.html', context)


@login_required
@admin_required
def export_report_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Transaction Reference', 'Order Reference', 'Amount', 'Payment Method', 'Status', 'Date', 'Recorded By'])

    payments = Payment.objects.select_related('order', 'recorded_by').all().order_by('-created_at')
    for p in payments:
        writer.writerow([
            p.transaction_reference,
            p.order.order_number or p.order.order_reference,
            f"{p.amount:.2f}",
            p.get_payment_method_display(),
            p.get_status_display(),
            p.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            p.recorded_by.get_full_name() if p.recorded_by else 'N/A',
        ])
    return response


@login_required
@admin_required
def export_report_pdf(request):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "ROMS - Restaurant Financial Summary Report")
    p.drawString(100, 730, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_sales = Payment.objects.filter(status=Payment.Status.COMPLETED).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_orders = Order.objects.count()
    
    p.drawString(100, 690, f"Total Lifetime Collected Sales: ETB {total_sales:.2f}")
    p.drawString(100, 670, f"Total Orders Placed: {total_orders}")
    p.drawString(100, 650, f"Total Payments Recorded: {Payment.objects.count()}")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="financial_report.pdf"'
    return response


@login_required
@admin_required
def user_management(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'admin_dashboard/users.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(
                user=request.user,
                action='USER_CREATED',
                description=f'User {user.username} ({user.get_role_display()}) created.',
                entity_type='CustomUser',
                entity_id=user.id,
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('analytics:user_management')
    else:
        form = UserCreateForm()
    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@admin_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action='USER_UPDATED',
                description=f'User {user_obj.username} profile updated.',
                entity_type='CustomUser',
                entity_id=user_obj.id,
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'User {user_obj.username} updated.')
            return redirect('analytics:user_management')
    else:
        form = UserUpdateForm(instance=user_obj)
    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'title': f'Edit User: {user_obj.username}'})


@login_required
@admin_required
@require_POST
def user_toggle_status(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id)
    if user_obj == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('analytics:user_management')

    user_obj.is_active_employee = not user_obj.is_active_employee
    user_obj.save(update_fields=['is_active_employee'])
    status_str = "activated" if user_obj.is_active_employee else "deactivated"

    log_action(
        user=request.user,
        action='USER_DEACTIVATED' if not user_obj.is_active_employee else 'USER_UPDATED',
        description=f'User {user_obj.username} was {status_str}.',
        entity_type='CustomUser',
        entity_id=user_obj.id,
        ip_address=get_client_ip(request)
    )

    messages.info(request, f'User {user_obj.username} has been {status_str}.')
    return redirect('analytics:user_management')

