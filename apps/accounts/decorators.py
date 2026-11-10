from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """Decorator that checks if the user has one of the allowed roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard_redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def waiter_required(view_func):
    return role_required('WAITER')(view_func)


def supervisor_required(view_func):
    return role_required('SUPERVISOR')(view_func)


def kitchen_staff_required(view_func):
    return role_required('KITCHEN_STAFF')(view_func)


def admin_required(view_func):
    return role_required('ADMIN')(view_func)
