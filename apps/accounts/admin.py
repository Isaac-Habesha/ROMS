from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'is_active_employee', 'created_at')
    list_filter = ('role', 'is_active_employee', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('ROMS Info', {
            'fields': ('role', 'phone_number', 'is_active_employee', 'avatar'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('ROMS Info', {
            'fields': ('role', 'first_name', 'last_name', 'phone_number'),
        }),
    )
