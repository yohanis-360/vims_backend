"""
API views for Configuration management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import VisualChecklistConfig, TestStandard, FeeStructure
from .serializers import (
    VisualChecklistConfigSerializer,
    TestStandardSerializer,
    FeeStructureSerializer
)


class VisualChecklistConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing visual checklist configuration.
    Admin can create, update, and manage checklist items.
    """
    queryset = VisualChecklistConfig.objects.all()
    serializer_class = VisualChecklistConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vehicle_category', 'zone_id', 'status']
    ordering_fields = ['display_order', 'item_number']
    ordering = ['vehicle_category', 'zone_id', 'display_order', 'item_number']
    
    def get_permissions(self):
        """
        Allow unauthenticated access to by_category action for reading checklist config.
        """
        if self.action == 'by_category':
            return []
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get checklist items grouped by zone for a vehicle category.
        Returns format compatible with frontend.
        """
        vehicle_category = request.query_params.get('category', 'LIGHT')
        
        items = self.queryset.filter(
            vehicle_category=vehicle_category,
            status='active'
        ).order_by('zone_id', 'display_order', 'item_number')
        
        # Group by zone
        zones = {}
        for item in items:
            zone_id = item.zone_id
            if zone_id not in zones:
                zones[zone_id] = {
                    'id': zone_id,
                    'titleEn': item.zone_name_en,
                    'titleAm': item.zone_name_am or '',
                    'items': []
                }
            
            zones[zone_id]['items'].append({
                'id': item.item_number,
                'am': item.item_name_am or '',
                'en': item.item_name_en,
                'points': item.points_possible,
                'points_possible': item.points_possible,
                'is_critical': item.is_critical,
                'is_mandatory': item.is_mandatory,
            })
        
        return Response({
            'category': vehicle_category,
            'zones': list(zones.values())
        })
    
    @action(detail=False, methods=['post'], url_path='populate')
    def populate(self, request):
        """
        Populate checklist configuration from hardcoded data.
        This will create/update items for both LIGHT and HEAVY vehicles.
        """
        try:
            from .populate_utils import populate_checklist_config
            result = populate_checklist_config(request.user)
            return Response({
                'success': True,
                'message': 'Checklist configuration populated successfully',
                'data': result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestStandardViewSet(viewsets.ModelViewSet):
    """ViewSet for test standards configuration."""
    queryset = TestStandard.objects.filter(is_active=True)
    serializer_class = TestStandardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vehicle_category', 'test_type']


class FeeStructureViewSet(viewsets.ModelViewSet):
    """ViewSet for fee structure configuration."""
    queryset = FeeStructure.objects.filter(is_active=True)
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['vehicle_category', 'vehicle_type']

