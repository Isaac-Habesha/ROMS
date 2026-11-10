from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that checks if the user has the required role."""
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard_redirect')


class WaiterRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['WAITER']


class SupervisorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['SUPERVISOR']


class KitchenStaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['KITCHEN_STAFF']


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['ADMIN']
