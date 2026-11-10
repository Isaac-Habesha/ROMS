from django.db import models
from django.conf import settings


class KitchenTicket(models.Model):
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='kitchen_ticket')
    ticket_number = models.CharField(max_length=64, unique=True)
    printed_count = models.PositiveIntegerField(default=0)
    first_printed_at = models.DateTimeField(null=True, blank=True)
    last_printed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Kitchen Ticket'
        verbose_name_plural = 'Kitchen Tickets'

    def __str__(self):
        return f"{self.ticket_number} for {self.order.order_number or self.order.order_reference}"


class KitchenStatusHistory(models.Model):
    class KitchenStatus(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Kitchen Received'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready for Serving'

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='kitchen_history')
    status = models.CharField(max_length=20, choices=KitchenStatus.choices)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Kitchen Status History'
        verbose_name_plural = 'Kitchen Status Histories'

    def __str__(self):
        return f"{self.order.order_number}: {self.status} at {self.timestamp}"

