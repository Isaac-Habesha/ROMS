from django.db import models


class MealCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Meal Category'
        verbose_name_plural = 'Meal Categories'

    def __str__(self):
        return self.name


class Meal(models.Model):
    category = models.ForeignKey(MealCategory, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='meals/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    preparation_time_minutes = models.PositiveIntegerField(default=15, help_text="Estimated preparation time")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Meal'
        verbose_name_plural = 'Meals'

    def __str__(self):
        return f"{self.name} - ETB {self.price}"

