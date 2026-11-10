from django.contrib import admin
from .models import KitchenTicket, KitchenStatusHistory


@admin.register(KitchenTicket)
class KitchenTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'order', 'printed_count', 'first_printed_at', 'last_printed_at')
    readonly_fields = ('created_at', 'first_printed_at', 'last_printed_at')


@admin.register(KitchenStatusHistory)
class KitchenStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'updated_by', 'timestamp')
    list_filter = ('status', 'timestamp')
    readonly_fields = ('order', 'status', 'updated_by', 'timestamp')

