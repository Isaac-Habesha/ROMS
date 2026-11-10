from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import Restaurant, RestaurantSettings


@login_required
@admin_required
def restaurant_settings(request):
    restaurant, _ = Restaurant.objects.get_or_create(id=1, defaults={'name': 'My Restaurant'})
    settings_obj, _ = RestaurantSettings.objects.get_or_create(restaurant=restaurant)
    
    if request.method == 'POST':
        restaurant.name = request.POST.get('name', restaurant.name)
        restaurant.phone = request.POST.get('phone', restaurant.phone)
        restaurant.email = request.POST.get('email', restaurant.email)
        restaurant.address = request.POST.get('address', restaurant.address)
        restaurant.save()

        settings_obj.currency_symbol = request.POST.get('currency_symbol', '$')
        settings_obj.order_prefix = request.POST.get('order_prefix', 'ORD')
        settings_obj.enable_sound_notifications = 'enable_sound_notifications' in request.POST
        settings_obj.auto_print_on_approval = 'auto_print_on_approval' in request.POST
        settings_obj.save()

        messages.success(request, 'Restaurant settings updated successfully.')
        return redirect('restaurants:settings')

    return render(request, 'restaurants/settings.html', {
        'restaurant': restaurant,
        'settings': settings_obj,
    })

