"""
Dashboard statistics API for Admin Portal.
Aggregates data from multiple apps for overview display.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from apps.inspections.models import Inspection
from apps.centers.models import Center
from apps.users.models import User
from apps.security.models import AuditLog


class DashboardOverviewView(APIView):
    """
    Get overall dashboard statistics for admin portal.
    
    GET /api/dashboard/overview/
    """
    permission_classes = [IsAuthenticated]
    
    def _get_filtered_centers(self, user_scope):
        """Filter centers by user scope."""
        centers = Center.objects.all()
        
        if user_scope['type'] == 'Regional' and user_scope['ids']:
            centers = centers.filter(region__in=user_scope['ids'])
        elif user_scope['type'] == 'Zone' and user_scope['ids']:
            centers = centers.filter(zone__in=user_scope['ids'])
        elif user_scope['type'] == 'Woreda' and user_scope['ids']:
            centers = centers.filter(woreda__in=user_scope['ids'])
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            centers = centers.filter(center_id__in=user_scope['ids'])
        # National scope sees all centers
        
        return centers
    
    def get(self, request):
        """Get comprehensive dashboard overview."""
        user_scope = request.user.get_scope_data()
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Dashboard request - User: {request.user.username}")
        logger.info(f"User scope: {user_scope}")
        logger.info(f"Scope type: {user_scope['type']}, Scope IDs: {user_scope['ids']}")
        
        cache_key = f"dashboard_overview:{user_scope['type']}:{':'.join(map(str, user_scope['ids']))}"
        
        # Try cache (5 minutes)
        stats = cache.get(cache_key)
        if stats:
            return Response(stats)
        
        # Calculate statistics
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Inspection Statistics - Apply scope filtering
        inspections = Inspection.objects.all()
        
        # Filter inspections by user scope
        if user_scope['type'] == 'Regional' and user_scope['ids']:
            logger.info(f"Filtering inspections by region: {user_scope['ids']}")
            inspections = inspections.filter(center__region__in=user_scope['ids'])
            logger.info(f"Filtered inspections count: {inspections.count()}")
        elif user_scope['type'] == 'Zone' and user_scope['ids']:
            logger.info(f"Filtering inspections by zone: {user_scope['ids']}")
            inspections = inspections.filter(center__zone__in=user_scope['ids'])
            logger.info(f"Filtered inspections count: {inspections.count()}")
        elif user_scope['type'] == 'Woreda' and user_scope['ids']:
            logger.info(f"Filtering inspections by woreda: {user_scope['ids']}")
            inspections = inspections.filter(center__woreda__in=user_scope['ids'])
            logger.info(f"Filtered inspections count: {inspections.count()}")
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            logger.info(f"Filtering inspections by center: {user_scope['ids']}")
            inspections = inspections.filter(center__center_id__in=user_scope['ids'])
            logger.info(f"Filtered inspections count: {inspections.count()}")
        else:
            logger.info(f"No filtering applied - showing all inspections (scope: {user_scope['type']})")
        # National scope sees all inspections (no filter needed)
        
        # Get completed inspections for pass/fail counts and pass rate
        # Pass: completed with PASS result
        # Fail: completed with FAIL result OR status='failed'
        from django.db.models import Q
        completed_inspections = inspections.filter(status='completed')
        passed_count = completed_inspections.filter(overall_result='PASS').count()
        
        # Failed count includes both:
        # 1. Completed inspections with FAIL result
        # 2. Inspections with status='failed' (regardless of overall_result)
        failed_count = inspections.filter(
            Q(status='completed', overall_result='FAIL') | Q(status='failed')
        ).distinct().count()
        
        total_completed = passed_count + failed_count
        
        # Calculate pass rate from completed/failed inspections only
        pass_rate = 0
        if total_completed > 0:
            pass_rate = round((passed_count / total_completed) * 100, 2)
        
        stats = {
            'inspections': {
                'total': inspections.count(),
                'today': inspections.filter(created_at__gte=today_start).count(),
                'this_week': inspections.filter(created_at__gte=week_start).count(),
                'this_month': inspections.filter(created_at__gte=month_start).count(),
                'passed': passed_count,  # Only completed with PASS
                'failed': failed_count,  # Completed with FAIL OR status='failed'
                'pending': inspections.filter(status__in=['in_progress', 'pending_machine', 'pending_payment']).count(),
                'pass_rate': pass_rate,  # Already calculated above: passed / (passed + failed) * 100
            },
            'centers': {
                'total': self._get_filtered_centers(user_scope).count(),
                'active': self._get_filtered_centers(user_scope).filter(status='active').count(),
                'inactive': self._get_filtered_centers(user_scope).filter(status='inactive').count(),
                'maintenance': self._get_filtered_centers(user_scope).filter(status='maintenance').count(),
            },
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(status='Active', is_active=True).count(),
                'suspended': User.objects.filter(status='Suspended').count(),
            },
            'recent_activity': {
                'audit_logs_today': AuditLog.objects.filter(timestamp__gte=today_start).count(),
                'logins_today': AuditLog.objects.filter(
                    action='USER_LOGIN',
                    timestamp__gte=today_start
                ).count(),
            },
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, timeout=300)
        
        return Response(stats)


class CentersAttentionView(APIView):
    """
    Get centers requiring attention based on various metrics.
    
    GET /api/dashboard/centers-attention/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get centers requiring attention."""
        user_scope = request.user.get_scope_data()
        
        # Get centers with high attention scores - filtered by scope
        centers = Center.objects.filter(is_active=True)
        
        # Apply scope filtering
        if user_scope['type'] == 'Regional' and user_scope['ids']:
            centers = centers.filter(region__in=user_scope['ids'])
        elif user_scope['type'] == 'Zone' and user_scope['ids']:
            centers = centers.filter(zone__in=user_scope['ids'])
        elif user_scope['type'] == 'Woreda' and user_scope['ids']:
            centers = centers.filter(woreda__in=user_scope['ids'])
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            centers = centers.filter(center_id__in=user_scope['ids'])
        
        centers = centers.order_by('-attention_score')[:10]
        
        attention_centers = []
        for center in centers:
            attention_centers.append({
                'center_id': center.center_id,
                'name': center.name,
                'region': center.region,
                'attention_score': center.attention_score,
                'status': center.status,
                'total_inspections': center.total_inspections,
                'pass_rate': float(center.pass_rate),
                'last_inspection': center.last_inspection_date
            })
        
        return Response({
            'centers': attention_centers,
            'total_requiring_attention': len([c for c in attention_centers if c['attention_score'] > 50])
        })


class UserScopeDebugView(APIView):
    """
    Debug endpoint to check current user's scope.
    
    GET /api/dashboard/debug-scope/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's scope information for debugging."""
        user = request.user
        scope_data = user.get_scope_data()
        
        # Get role assignments
        role_assignments = []
        for ra in user.role_assignments.all():
            role_assignments.append({
                'role_id': ra.role.role_id,
                'role_name': ra.role.role_name_en,
                'scope_type': ra.scope_type,
                'scope_ids': ra.scope_ids,
                'status': ra.status,
                'is_active': ra.is_active(),
            })
        
        return Response({
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'full_name': user.full_name,
                'is_superuser': user.is_superuser,
            },
            'scope_data': scope_data,
            'role_assignments': role_assignments,
            'has_active_role': user.get_primary_role() is not None,
        })


class RevenueStatisticsView(APIView):
    """
    Get revenue statistics from inspections.
    
    GET /api/dashboard/revenue/
    """
    permission_classes = [IsAuthenticated]
    
    def _get_pending_payments(self, user_scope):
        """Get pending payments filtered by scope."""
        pending = Inspection.objects.filter(
            payment_status='unpaid',
            status='pending_payment'
        )
        
        # Apply scope filtering
        if user_scope['type'] == 'Regional' and user_scope['ids']:
            pending = pending.filter(center__region__in=user_scope['ids'])
        elif user_scope['type'] == 'Zone' and user_scope['ids']:
            pending = pending.filter(center__zone__in=user_scope['ids'])
        elif user_scope['type'] == 'Woreda' and user_scope['ids']:
            pending = pending.filter(center__woreda__in=user_scope['ids'])
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            pending = pending.filter(center__center_id__in=user_scope['ids'])
        
        return pending
    
    def get(self, request):
        """Get revenue statistics."""
        user_scope = request.user.get_scope_data()
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get paid inspections - filtered by scope
        paid_inspections = Inspection.objects.filter(payment_status='paid')
        
        # Apply scope filtering
        if user_scope['type'] == 'Regional' and user_scope['ids']:
            paid_inspections = paid_inspections.filter(center__region__in=user_scope['ids'])
        elif user_scope['type'] == 'Zone' and user_scope['ids']:
            paid_inspections = paid_inspections.filter(center__zone__in=user_scope['ids'])
        elif user_scope['type'] == 'Woreda' and user_scope['ids']:
            paid_inspections = paid_inspections.filter(center__woreda__in=user_scope['ids'])
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            paid_inspections = paid_inspections.filter(center__center_id__in=user_scope['ids'])
        
        stats = {
            'total_revenue': float(paid_inspections.aggregate(
                total=Sum('payment_amount')
            )['total'] or 0),
            'revenue_today': float(paid_inspections.filter(
                payment_date__gte=today_start
            ).aggregate(total=Sum('payment_amount'))['total'] or 0),
            'revenue_this_month': float(paid_inspections.filter(
                payment_date__gte=month_start
            ).aggregate(total=Sum('payment_amount'))['total'] or 0),
            'paid_inspections': paid_inspections.count(),
            'pending_payments': self._get_pending_payments(user_scope).count(),
        }
        
        return Response(stats)


