"""
Security utilities for audit logging.
"""
from django.utils import timezone


def log_action(user, action, resource_type, resource_id, details=None, severity='LOW', request=None):
    """
    Log user action for audit trail.
    
    Args:
        user: User who performed the action
        action: Action type (e.g., 'USER_LOGIN', 'INSPECTION_CREATED')
        resource_type: Type of resource (e.g., 'User', 'Inspection')
        resource_id: ID of the resource
        details: Additional details (dict)
        severity: Severity level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        request: HTTP request object (optional, for IP/user agent)
    """
    from .models import AuditLog
    
    # Extract request metadata
    ip_address = None
    user_agent = ''
    session_id = ''
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_id = request.session.session_key if hasattr(request, 'session') else ''
    
    # Create audit log
    audit_log = AuditLog.objects.create(
        user=user,
        username=user.username if user else 'system',
        user_ip_address=ip_address,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details=details or {},
        severity=severity,
        session_id=session_id,
        user_agent=user_agent
    )
    
    # Print for console visibility
    print(f"[AUDIT] {user.username if user else 'system'} - {action} - {resource_type}:{resource_id}")
    
    return audit_log


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def detect_suspicious_activity(user, activity_type, description, risk_score, metadata=None):
    """
    Create a suspicious activity record.
    
    Args:
        user: User involved in suspicious activity
        activity_type: Type of suspicious activity
        description: Description of the activity
        risk_score: Risk score 0-100
        metadata: Additional metadata
    """
    from .models import SuspiciousActivity
    
    activity = SuspiciousActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        risk_score=risk_score,
        metadata=metadata or {}
    )
    
    print(f"[SECURITY ALERT] {activity_type} - User: {user.username} - Risk: {risk_score}/100")
    
    return activity
