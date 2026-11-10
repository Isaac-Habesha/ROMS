from django.contrib import admin
from .models import OrderApproval


@admin.register(OrderApproval)
class OrderApprovalAdmin(admin.ModelAdmin):
    list_display = ('order', 'supervisor', 'decision', 'reviewed_at')
    list_filter = ('decision', 'reviewed_at')
    search_fields = ('order__order_reference', 'order__order_number', 'supervisor__username')
    readonly_fields = ('order', 'supervisor', 'decision', 'rejection_reason', 'reviewed_at')

