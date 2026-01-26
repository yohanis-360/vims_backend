"""
Serializers for Security and Audit Log APIs.
"""
from rest_framework import serializers
from .models import AuditLog, SuspiciousActivity


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""
    
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = fields
    
    def get_user_full_name(self, obj):
        """Get user's full name if user exists."""
        return obj.user.full_name if obj.user else 'Deleted User'


class AuditLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing audit logs."""
    
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'log_id', 'username', 'user_full_name', 'action',
            'resource_type', 'resource_id', 'timestamp', 'severity'
        ]
        read_only_fields = fields
    
    def get_user_full_name(self, obj):
        """Get user's full name if user exists."""
        return obj.user.full_name if obj.user else 'Deleted User'


class SuspiciousActivitySerializer(serializers.ModelSerializer):
    """Serializer for suspicious activities."""
    
    user_username = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    resolved_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = SuspiciousActivity
        fields = '__all__'
        read_only_fields = [
            'activity_id', 'detected_at', 'user', 'related_logs'
        ]
    
    def get_user_username(self, obj):
        """Get username."""
        return obj.user.username if obj.user else 'Unknown'
    
    def get_user_full_name(self, obj):
        """Get user's full name."""
        return obj.user.full_name if obj.user else 'Unknown User'
    
    def get_resolved_by_username(self, obj):
        """Get resolver's username."""
        return obj.resolved_by.username if obj.resolved_by else None


class SuspiciousActivityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing suspicious activities."""
    
    user_username = serializers.SerializerMethodField()
    
    class Meta:
        model = SuspiciousActivity
        fields = [
            'activity_id', 'user_username', 'activity_type',
            'description', 'risk_score', 'status', 'detected_at'
        ]
        read_only_fields = fields
    
    def get_user_username(self, obj):
        """Get username."""
        return obj.user.username if obj.user else 'Unknown'


