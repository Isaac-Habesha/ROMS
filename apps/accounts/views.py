from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import LoginForm
from .models import CustomUser


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active_employee:
                messages.error(request, 'Your account has been deactivated. Contact an administrator.')
                return render(request, 'accounts/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    """Redirect user to their role-specific dashboard."""
    user = request.user
    if user.is_admin:
        return redirect('analytics:admin_dashboard')
    elif user.is_supervisor:
        return redirect('approvals:supervisor_dashboard')
    elif user.is_waiter:
        return redirect('orders:waiter_dashboard')
    elif user.is_kitchen_staff:
        return redirect('kitchen:kitchen_dashboard')
    else:
        messages.error(request, 'Your role is not configured. Contact an administrator.')
        return redirect('accounts:login')
