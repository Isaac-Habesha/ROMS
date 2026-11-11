from django.db import models
from django.conf import settings
import uuid


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Credit / Debit Card'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money / QR'
        OTHER = 'OTHER', 'Other / Manual'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        PENDING = 'PENDING', 'Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_payments'
    )
    transaction_reference = models.CharField(max_length=64, unique=True, editable=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def save(self, *args, **kwargs):
        if not self.transaction_reference:
            self.transaction_reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_reference} - ETB {self.amount} ({self.get_payment_method_display()})"

