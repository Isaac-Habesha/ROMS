from django.contrib import admin
from .models import Restaurant, RestaurantSettings


class RestaurantSettingsInline(admin.StackedInline):
    model = RestaurantSettings
    can_delete = False


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'email')
    inlines = [RestaurantSettingsInline]
