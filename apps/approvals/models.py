from django.db import models
from django.conf import settings


class OrderApproval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='approval_record')
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='supervisor_approvals'
    )
    decision = models.CharField(max_length=16, choices=Decision.choices)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reviewed_at']
        verbose_name = 'Order Approval'
        verbose_name_plural = 'Order Approvals'

    def __str__(self):
        return f"{self.order.order_reference} - {self.decision} by {self.supervisor}"

