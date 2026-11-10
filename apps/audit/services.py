from .models import AuditLog


def log_action(user, action, description, entity_type='', entity_id=None, ip_address=None, extra_data=None):
    """Create an audit log entry."""
    return AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        extra_data=extra_data or {},
    )


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
