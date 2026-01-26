"""
API views for Security and Audit Logs.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models

from .models import AuditLog, SuspiciousActivity
from .serializers import (
    AuditLogSerializer, AuditLogListSerializer,
    SuspiciousActivitySerializer, SuspiciousActivityListSerializer
)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Audit Log viewing (read-only).
    Only authorized security/audit admins can view audit logs.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'action', 'resource_type', 'resource_id']
    ordering_fields = ['timestamp', 'severity']
    filterset_fields = ['action', 'resource_type', 'severity', 'username']
    lookup_field = 'log_id'
    
    def get_queryset(self):
        """Filter audit logs based on user permissions."""
        user = self.request.user
        
        # Only admins and security roles can view audit logs
        # TODO: Add proper permission check based on roles
        queryset = AuditLog.objects.select_related('user').all()
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get audit log statistics.
        
        GET /api/security/audit-logs/statistics/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_logs': queryset.count(),
            'logs_by_action': dict(
                queryset.values_list('action').annotate(count=models.Count('log_id')).values_list('action', 'count')
            ),
            'logs_by_severity': dict(
                queryset.values_list('severity').annotate(count=models.Count('log_id')).values_list('severity', 'count')
            ),
            'logs_today': queryset.filter(
                timestamp__gte=timezone.now().replace(hour=0, minute=0, second=0)
            ).count(),
        }
        
        return Response(stats)


class SuspiciousActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Suspicious Activity management.
    Security admins can view, update status, and resolve activities.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'activity_type', 'description']
    ordering_fields = ['detected_at', 'risk_score']
    filterset_fields = ['activity_type', 'status', 'user']
    lookup_field = 'activity_id'
    
    def get_queryset(self):
        """Get suspicious activities."""
        queryset = SuspiciousActivity.objects.select_related('user', 'resolved_by').all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SuspiciousActivityListSerializer
        return SuspiciousActivitySerializer
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, activity_id=None):
        """
        Resolve a suspicious activity.
        
        POST /api/security/suspicious-activities/{id}/resolve/
        Body: {"resolution": "FALSE_POSITIVE" or "RESOLVED", "notes": "..."}
        """
        activity = self.get_object()
        
        resolution = request.data.get('resolution', 'RESOLVED')
        notes = request.data.get('notes', '')
        
        if resolution not in ['RESOLVED', 'FALSE_POSITIVE']:
            return Response(
                {'error': 'Invalid resolution status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activity.status = resolution
        activity.resolved_at = timezone.now()
        activity.resolved_by = request.user
        
        # Add notes to metadata
        if notes:
            activity.metadata['resolution_notes'] = notes
        
        activity.save()
        
        # Log action
        from .utils import log_action
        log_action(
            user=request.user,
            action='SUSPICIOUS_ACTIVITY_RESOLVED',
            resource_type='SuspiciousActivity',
            resource_id=activity.activity_id,
            details={'resolution': resolution, 'notes': notes},
            severity='MEDIUM'
        )
        
        return Response(SuspiciousActivitySerializer(activity).data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get suspicious activity statistics.
        
        GET /api/security/suspicious-activities/statistics/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_activities': queryset.count(),
            'open_activities': queryset.filter(status='OPEN').count(),
            'investigating_activities': queryset.filter(status='INVESTIGATING').count(),
            'resolved_activities': queryset.filter(status='RESOLVED').count(),
            'false_positives': queryset.filter(status='FALSE_POSITIVE').count(),
            'high_risk_activities': queryset.filter(risk_score__gte=70).count(),
            'activities_by_type': dict(
                queryset.values_list('activity_type').annotate(count=models.Count('activity_id')).values_list('activity_type', 'count')
            ),
        }
        
        return Response(stats)

