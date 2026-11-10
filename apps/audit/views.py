from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required
from .models import AuditLog


@login_required
@admin_required
def audit_logs_view(request):
    action_filter = request.GET.get('action', '')
    logs = AuditLog.objects.select_related('user').all()
    if action_filter:
        logs = logs.filter(action=action_filter)
    return render(request, 'audit/audit_logs.html', {
        'logs': logs[:100],
        'action_choices': AuditLog.ActionType.choices,
        'current_action': action_filter,
    })

