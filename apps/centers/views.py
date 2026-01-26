"""
API views for Center management.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg

from .models import Center
from .serializers import (
    CenterListSerializer, CenterDetailSerializer,
    CenterCreateSerializer, CenterUpdateSerializer,
    CenterStatisticsSerializer, GeofenceUpdateSerializer
)


class CenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Center CRUD operations with scope filtering.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'region', 'zone']
    ordering_fields = ['created_at', 'name', 'attention_score', 'total_inspections']
    filterset_fields = ['status', 'region', 'is_active']
    lookup_field = 'center_id'
    
    def get_queryset(self):
        """Filter centers by requesting user's scope."""
        user_scope = self.request.user.get_scope_data()
        
        # Cache key based on user scope
        cache_key = f"centers_list:{user_scope['type']}:{':'.join(map(str, user_scope['ids']))}"
        
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = Center.scoped_objects.filter_by_scope(user_scope)
            
            # Cache for 5 minutes
            cache.set(cache_key, queryset, timeout=300)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CenterListSerializer
        elif self.action == 'create':
            return CenterCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CenterUpdateSerializer
        return CenterDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List centers with caching."""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create new center with audit logging."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        center = serializer.save()
        
        # Invalidate cache
        cache.delete_pattern('centers_list:*')
        cache.delete('centers_statistics')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='CENTER_CREATED',
            resource_type='Center',
            resource_id=center.center_id,
            details={'name': center.name, 'code': center.code}
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            CenterDetailSerializer(center).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Update center with audit logging."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Invalidate cache
        cache.delete_pattern('centers_list:*')
        cache.delete('centers_statistics')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='CENTER_UPDATED',
            resource_type='Center',
            resource_id=instance.center_id,
            details={'name': instance.name}
        )
        
        return Response(CenterDetailSerializer(instance).data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete center (set to inactive)."""
        instance = self.get_object()
        
        # Soft delete by setting inactive
        instance.is_active = False
        instance.status = 'inactive'
        instance.save(update_fields=['is_active', 'status'])
        
        # Invalidate cache
        cache.delete_pattern('centers_list:*')
        cache.delete('centers_statistics')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='CENTER_DELETED',
            resource_type='Center',
            resource_id=instance.center_id,
            details={'name': instance.name}
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get center statistics.
        
        GET /api/centers/statistics/
        """
        cache_key = 'centers_statistics'
        
        stats = cache.get(cache_key)
        if not stats:
            queryset = self.get_queryset()
            
            stats = {
                'total_centers': queryset.count(),
                'active_centers': queryset.filter(status='active').count(),
                'inactive_centers': queryset.filter(status='inactive').count(),
                'maintenance_centers': queryset.filter(status='maintenance').count(),
                'total_inspections': queryset.aggregate(total=Count('total_inspections'))['total'] or 0,
                'average_pass_rate': queryset.aggregate(avg=Avg('pass_rate'))['avg'] or 0,
                'centers_by_region': dict(
                    queryset.values('region').annotate(count=Count('center_id')).values_list('region', 'count')
                )
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, stats, timeout=600)
        
        serializer = CenterStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update-geofence')
    def update_geofence(self, request, center_id=None):
        """
        Update center geofence coordinates and radius.
        
        POST /api/centers/{id}/update-geofence/
        """
        center = self.get_object()
        serializer = GeofenceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            center.latitude = serializer.validated_data['latitude']
            center.longitude = serializer.validated_data['longitude']
            center.geofence_radius_meters = serializer.validated_data['radius_meters']
            center.save(update_fields=['latitude', 'longitude', 'geofence_radius_meters'])
            
            # Invalidate cache
            cache.delete_pattern('centers_list:*')
            
            # Log action
            from apps.security.utils import log_action
            log_action(
                user=request.user,
                action='CENTER_GEOFENCE_UPDATED',
                resource_type='Center',
                resource_id=center.center_id,
                details={
                    'latitude': str(center.latitude),
                    'longitude': str(center.longitude),
                    'radius': center.geofence_radius_meters
                }
            )
            
            return Response(CenterDetailSerializer(center).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def devices(self, request, center_id=None):
        """
        Get all devices registered to this center.
        
        GET /api/centers/{id}/devices/
        """
        center = self.get_object()
        
        # TODO: Implement device registry model and query
        # For now, return empty list
        return Response({
            'center_id': center.center_id,
            'center_name': center.name,
            'devices': []
        })


