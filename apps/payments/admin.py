from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_reference', 'order', 'amount', 'payment_method', 'status', 'recorded_by', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('transaction_reference', 'order__order_number', 'order__order_reference')
    readonly_fields = ('transaction_reference', 'created_at')

