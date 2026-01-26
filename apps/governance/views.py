"""
API views for Governance management.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import OperationalError, ProgrammingError

from .models import AdminUnit, Institution
from .serializers import (
    AdminUnitListSerializer,
    AdminUnitDetailSerializer,
    AdminUnitCreateSerializer,
    AdminUnitUpdateSerializer,
    InstitutionListSerializer,
    InstitutionDetailSerializer,
    InstitutionCreateSerializer,
    InstitutionUpdateSerializer,
)


class AdminUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AdminUnit CRUD operations.
    
    GET /api/governance/admin-units/ - List all admin units
    GET /api/governance/admin-units/{id}/ - Get admin unit details
    POST /api/governance/admin-units/ - Create new admin unit
    PUT/PATCH /api/governance/admin-units/{id}/ - Update admin unit
    DELETE /api/governance/admin-units/{id}/ - Delete admin unit
    GET /api/governance/admin-units/?type=Region - Filter by type
    GET /api/governance/admin-units/?parent_id={id} - Filter by parent
    GET /api/governance/admin-units/?status=Active - Filter by status
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['admin_unit_name_en', 'admin_unit_name_am', 'admin_unit_code']
    ordering_fields = ['admin_unit_name_en', 'admin_unit_type', 'created_at']
    filterset_fields = ['admin_unit_type', 'parent_admin_unit_id', 'status']
    lookup_field = 'admin_unit_id'
    
    def get_queryset(self):
        """Get queryset with optional filtering - handles missing table gracefully."""
        # Try to build the queryset - errors will be caught when it's evaluated
        queryset = AdminUnit.objects.all()
        
        # Filter by type if provided
        unit_type = self.request.query_params.get('type', None)
        if unit_type:
            queryset = queryset.filter(admin_unit_type=unit_type)
        
        # Filter by parent if provided
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_id:
            queryset = queryset.filter(parent_admin_unit_id=parent_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Try to add select_related, but don't fail if table doesn't exist
        # The error will be caught when queryset is evaluated
        try:
            return queryset.select_related('parent_admin_unit_id')
        except (OperationalError, ProgrammingError):
            # If select_related fails, return queryset without it
            return queryset
    
    def filter_queryset(self, queryset):
        """Override to catch database errors during filtering."""
        try:
            return super().filter_queryset(queryset)
        except (OperationalError, ProgrammingError) as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                # Return empty queryset if table doesn't exist
                return AdminUnit.objects.none()
            raise
        except Exception as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return AdminUnit.objects.none()
            raise
    
    def list(self, request, *args, **kwargs):
        """List admin units with error handling for missing table."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError) as e:
            # If table doesn't exist, return empty array
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
        except Exception as e:
            # Catch any other database errors related to missing table
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str or 'table' in error_str:
                return Response([])
            raise
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve admin unit with error handling for missing table."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except (OperationalError, ProgrammingError) as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response(
                    {'error': 'Admin units table does not exist. Please run migrations.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            raise
        except Exception as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response(
                    {'error': 'Admin units table does not exist. Please run migrations.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            raise
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AdminUnitListSerializer
        elif self.action == 'create':
            return AdminUnitCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUnitUpdateSerializer
        return AdminUnitDetailSerializer
    
    @action(detail=True, methods=['get'])
    def children(self, request, admin_unit_id=None):
        """
        Get all child admin units.
        
        GET /api/governance/admin-units/{id}/children/
        """
        admin_unit = self.get_object()
        children = admin_unit.children.all()
        serializer = AdminUnitListSerializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, admin_unit_id=None):
        """
        Get all descendant admin units (recursive).
        
        GET /api/governance/admin-units/{id}/descendants/
        """
        admin_unit = self.get_object()
        descendants = admin_unit.get_all_descendants()
        serializer = AdminUnitListSerializer(descendants, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def regions(self, request):
        """
        Get all regions.
        
        GET /api/governance/admin-units/regions/
        """
        try:
            regions = AdminUnit.objects.filter(
                admin_unit_type='Region',
                status='Active'
            ).order_by('admin_unit_name_en')
            serializer = AdminUnitListSerializer(regions, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError) as e:
            # If table doesn't exist, return empty array
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
        except Exception as e:
            # Catch any other database errors
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
    
    @action(detail=False, methods=['get'])
    def zones(self, request):
        """
        Get all zones for a given region.
        
        GET /api/governance/admin-units/zones/?region_id={id}
        """
        try:
            region_id = request.query_params.get('region_id', None)
            if not region_id:
                return Response(
                    {'error': 'region_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                region = AdminUnit.objects.get(admin_unit_id=region_id, admin_unit_type='Region')
            except AdminUnit.DoesNotExist:
                return Response(
                    {'error': 'Region not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            zones = AdminUnit.objects.filter(
                parent_admin_unit_id=region,
                admin_unit_type__in=['Zone', 'Sub-city'],
                status='Active'
            ).order_by('admin_unit_name_en')
            serializer = AdminUnitListSerializer(zones, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError) as e:
            # If table doesn't exist, return empty array
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
        except Exception as e:
            # Catch any other database errors
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
    
    @action(detail=False, methods=['get'])
    def woredas(self, request):
        """
        Get all woredas for a given zone/sub-city.
        
        GET /api/governance/admin-units/woredas/?zone_id={id}
        """
        try:
            zone_id = request.query_params.get('zone_id', None)
            if not zone_id:
                return Response(
                    {'error': 'zone_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                zone = AdminUnit.objects.get(
                    admin_unit_id=zone_id,
                    admin_unit_type__in=['Zone', 'Sub-city']
                )
            except AdminUnit.DoesNotExist:
                return Response(
                    {'error': 'Zone/Sub-city not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            woredas = AdminUnit.objects.filter(
                parent_admin_unit_id=zone,
                admin_unit_type='Woreda',
                status='Active'
            ).order_by('admin_unit_name_en')
            serializer = AdminUnitListSerializer(woredas, many=True)
            return Response(serializer.data)
        except (OperationalError, ProgrammingError) as e:
            # If table doesn't exist, return empty array
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise
        except Exception as e:
            # Catch any other database errors
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                return Response([])
            raise


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Institution CRUD operations.
    
    GET /api/governance/institutions/ - List all institutions
    GET /api/governance/institutions/{id}/ - Get institution details
    POST /api/governance/institutions/ - Create new institution
    PUT/PATCH /api/governance/institutions/{id}/ - Update institution
    DELETE /api/governance/institutions/{id}/ - Delete institution
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['institution_name_en', 'institution_name_am', 'institution_short_name']
    ordering_fields = ['institution_name_en', 'institution_type', 'created_at']
    filterset_fields = ['institution_type', 'region_id', 'status']
    lookup_field = 'institution_id'
    
    def get_queryset(self):
        """Get queryset."""
        return Institution.objects.select_related('region_id').all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InstitutionListSerializer
        elif self.action == 'create':
            return InstitutionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InstitutionUpdateSerializer
        return InstitutionDetailSerializer


