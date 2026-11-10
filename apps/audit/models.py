from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        ORDER_CREATED = 'ORDER_CREATED', 'Order Created'
        ORDER_SUBMITTED = 'ORDER_SUBMITTED', 'Order Submitted'
        ORDER_APPROVED = 'ORDER_APPROVED', 'Order Approved'
        ORDER_REJECTED = 'ORDER_REJECTED', 'Order Rejected'
        ORDER_RESUBMITTED = 'ORDER_RESUBMITTED', 'Order Resubmitted'
        ORDER_DISPATCHED = 'ORDER_DISPATCHED', 'Order Dispatched'
        ORDER_STATUS_CHANGED = 'ORDER_STATUS_CHANGED', 'Order Status Changed'
        ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
        PAYMENT_RECORDED = 'PAYMENT_RECORDED', 'Payment Recorded'
        USER_CREATED = 'USER_CREATED', 'User Created'
        USER_UPDATED = 'USER_UPDATED', 'User Updated'
        USER_DEACTIVATED = 'USER_DEACTIVATED', 'User Deactivated'
        MEAL_CREATED = 'MEAL_CREATED', 'Meal Created'
        MEAL_UPDATED = 'MEAL_UPDATED', 'Meal Updated'
        TICKET_PRINTED = 'TICKET_PRINTED', 'Ticket Printed'
        LOGIN = 'LOGIN', 'User Login'
        LOGOUT = 'LOGOUT', 'User Logout'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=ActionType.choices)
    description = models.TextField()
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.get_action_display()} by {self.user}"
