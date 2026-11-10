from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        WAITER = 'WAITER', 'Waiter'
        KITCHEN_STAFF = 'KITCHEN_STAFF', 'Kitchen Staff'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WAITER,
    )
    phone_number = models.CharField(max_length=20, blank=True)
    is_active_employee = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_waiter(self):
        return self.role == self.Role.WAITER

    @property
    def is_kitchen_staff(self):
        return self.role == self.Role.KITCHEN_STAFF
