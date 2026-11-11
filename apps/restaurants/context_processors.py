from .models import RestaurantSettings


def restaurant_context(request):
    try:
        settings_obj = RestaurantSettings.objects.first()
        currency = settings_obj.currency_symbol if settings_obj and settings_obj.currency_symbol else 'ETB'
    except Exception:
        currency = 'ETB'
        settings_obj = None

    return {
        'CURRENCY_SYMBOL': currency,
        'restaurant_settings': settings_obj,
    }
