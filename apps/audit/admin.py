from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'description', 'entity_type', 'entity_id')
    list_filter = ('action', 'entity_type', 'created_at')
    search_fields = ('description', 'user__username')
    readonly_fields = ('user', 'action', 'description', 'entity_type', 'entity_id', 'ip_address', 'extra_data', 'created_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
