"""
Security models for audit logging and fraud detection.
"""
from django.db import models
from django.conf import settings
import uuid


class AuditLog(models.Model):
    """
    Audit log for tracking all user actions in the system.
    """
    
    ACTION_TYPES = [
        # User Actions
        ('USER_LOGIN', 'User Login'),
        ('USER_LOGOUT', 'User Logout'),
        ('USER_CREATED', 'User Created'),
        ('USER_UPDATED', 'User Updated'),
        ('USER_DELETED', 'User Deleted'),
        ('USER_SUSPENDED', 'User Suspended'),
        ('USER_ACTIVATED', 'User Activated'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        
        # Role Actions
        ('ROLE_CREATED', 'Role Created'),
        ('ROLE_UPDATED', 'Role Updated'),
        ('ROLE_DELETED', 'Role Deleted'),
        ('ROLE_ASSIGNED', 'Role Assigned'),
        
        # Center Actions
        ('CENTER_CREATED', 'Center Created'),
        ('CENTER_UPDATED', 'Center Updated'),
        ('CENTER_DELETED', 'Center Deleted'),
        ('CENTER_GEOFENCE_UPDATED', 'Center Geofence Updated'),
        
        # Inspection Actions
        ('INSPECTION_CREATED', 'Inspection Created'),
        ('INSPECTION_UPDATED', 'Inspection Updated'),
        ('INSPECTION_COMPLETED', 'Inspection Completed'),
        ('INSPECTION_FAILED', 'Inspection Failed'),
        
        # Security Actions
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity Detected'),
        ('GEOFENCE_VIOLATION', 'Geofence Violation'),
        
        # System Actions
        ('SYSTEM_CONFIG_CHANGED', 'System Configuration Changed'),
        ('DATA_EXPORT', 'Data Exported'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, db_index=True)  # Stored for deleted users
    user_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # What
    action = models.CharField(max_length=50, choices=ACTION_TYPES, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.CharField(max_length=100)
    
    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Details
    details = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='LOW')
    
    # Context
    session_id = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"


class SuspiciousActivity(models.Model):
    """
    Track suspicious activities for fraud detection.
    """
    
    ACTIVITY_TYPES = [
        ('RAPID_ACTIONS', 'Rapid Actions'),
        ('UNUSUAL_LOCATION', 'Unusual Location'),
        ('AFTER_HOURS', 'After Hours Activity'),
        ('MULTIPLE_FAILED_LOGINS', 'Multiple Failed Logins'),
        ('GEOFENCE_VIOLATION', 'Geofence Violation'),
        ('UNUSUAL_PATTERN', 'Unusual Pattern'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    ]
    
    activity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Related objects
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='suspicious_activities'
    )
    related_logs = models.ManyToManyField(AuditLog, related_name='suspicious_activities')
    
    # Activity details
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, db_index=True)
    description = models.TextField()
    risk_score = models.IntegerField(default=0, help_text='Risk score 0-100')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_activities'
    )
    
    # Additional data
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'suspicious_activities'
        ordering = ['-detected_at']
        verbose_name_plural = 'Suspicious Activities'
        indexes = [
            models.Index(fields=['status', 'detected_at']),
            models.Index(fields=['user', 'activity_type']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} - {self.user.username if self.user else 'Unknown'} - {self.detected_at}"
