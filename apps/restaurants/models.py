from django.db import models


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='restaurant/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'

    def __str__(self):
        return self.name


class RestaurantSettings(models.Model):
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='settings')
    currency_symbol = models.CharField(max_length=10, default='$')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    order_prefix = models.CharField(max_length=10, default='ORD')
    enable_sound_notifications = models.BooleanField(default=True)
    auto_print_on_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Restaurant Settings'
        verbose_name_plural = 'Restaurant Settings'

    def __str__(self):
        return f"Settings for {self.restaurant.name}"
