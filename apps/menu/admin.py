from django.contrib import admin
from .models import MealCategory, Meal


@admin.register(MealCategory)
class MealCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active', 'created_at')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name',)


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_archived', 'created_at')
    list_filter = ('category', 'is_available', 'is_archived')
    list_editable = ('price', 'is_available', 'is_archived')
    search_fields = ('name', 'description')

