from django.db import models
from django.conf import settings
import uuid


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
        REJECTED = 'REJECTED', 'Rejected'
        APPROVED = 'APPROVED', 'Approved'
        RECEIVED = 'RECEIVED', 'Kitchen Received'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready for Serving'
        SERVED = 'SERVED', 'Served'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order_reference = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    order_number = models.CharField(max_length=32, blank=True, null=True, unique=True, db_index=True)
    waiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='waiter_orders'
    )
    customer_count = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_APPROVAL,
        db_index=True
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def save(self, *args, **kwargs):
        if not self.order_reference:
            self.order_reference = f"REF-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    def __str__(self):
        num = self.order_number or self.order_reference
        return f"{num} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    meal = models.ForeignKey('menu.Meal', on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def save(self, *args, **kwargs):
        if self.unit_price is None and self.meal_id:
            self.unit_price = self.meal.price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.meal.name} - ETB {self.subtotal}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=24, blank=True)
    new_status = models.CharField(max_length=24)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'

    def __str__(self):
        return f"Order {self.order.order_reference}: {self.previous_status} -> {self.new_status}"

