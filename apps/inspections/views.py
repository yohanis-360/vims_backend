"""
Inspection API Views.
Optimized for high concurrency (100k+ concurrent users).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
import logging

from .models import (
    Inspection, MachineTest, VisualChecklistItem,
    InspectionPhoto, InspectionVideo
)
from .serializers import (
    InspectionCreateSerializer, InspectionDetailSerializer,
    InspectionUpdateSerializer, LightweightInspectionSerializer,
    VisualChecklistBulkSerializer, MachineTestBulkSerializer,
    InspectionPhotoSerializer, InspectionVideoSerializer,
    InspectionFinalizeSerializer, MachineTestSerializer,
    VisualChecklistItemSerializer
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for list views.
    Optimized for performance.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class InspectionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for inspections.
    
    Optimizations:
    - Caching for read operations
    - Selective field loading with .only() and .select_related()
    - Bulk operations for visual checklists and machine tests
    - Async task delegation for heavy operations
    """
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'inspection_id'
    
    def get_queryset(self):
        """
        Optimized queryset with scope-based filtering.
        Uses select_related and prefetch_related to minimize queries.
        """
        user = self.request.user
        
        # Base queryset with related data
        queryset = Inspection.objects.select_related(
            'center', 'inspector'
        ).prefetch_related(
            Prefetch('machine_tests', queryset=MachineTest.objects.all()),
            Prefetch('visual_items', queryset=VisualChecklistItem.objects.all()),
            Prefetch('photos', queryset=InspectionPhoto.objects.all()),
        )
        
        # Apply scope filtering based on user's scope
        user_scope = self._get_user_scope(user)
        
        if user_scope['type'] == 'National':
            return queryset
        elif user_scope['type'] == 'Regional' and user_scope['ids']:
            return queryset.filter(center__region__in=user_scope['ids'])
        elif user_scope['type'] == 'Center' and user_scope['ids']:
            return queryset.filter(center__center_id__in=user_scope['ids'])
        
        # Default: return inspections conducted by user only
        return queryset.filter(inspector=user)
    
    def _get_user_scope(self, user):
        """Extract user scope from role assignments."""
        # Cache user scope for 5 minutes
        cache_key = f"user_scope:{user.user_id}"
        cached_scope = cache.get(cache_key)
        if cached_scope:
            return cached_scope
        
        # Get from role assignments
        assignments = user.role_assignments.select_related('role').all()
        if not assignments:
            scope = {'type': 'Center', 'ids': []}
        else:
            # Get highest scope
            for assignment in assignments:
                if assignment.scope_type == 'National':
                    scope = {'type': 'National', 'ids': []}
                    break
                elif assignment.scope_type == 'Regional':
                    scope = {'type': 'Regional', 'ids': assignment.scope_ids or []}
                    break
            else:
                scope = {'type': 'Center', 'ids': assignments[0].scope_ids or []}
        
        cache.set(cache_key, scope, timeout=300)
        return scope
    
    def get_serializer_class(self):
        """
        Use lightweight serializer for list,
        full serializer for detail.
        """
        if self.action == 'list':
            return LightweightInspectionSerializer
        elif self.action == 'create':
            return InspectionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InspectionUpdateSerializer
        return InspectionDetailSerializer
    
    # Removed caching to show real-time inspection data
    def list(self, request, *args, **kwargs):
        """List inspections without caching for real-time updates."""
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve single inspection with caching.
        """
        inspection_id = kwargs.get(self.lookup_field, kwargs.get('pk'))
        cache_key = f"inspection:{inspection_id}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # Get from database
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Cache for 10 minutes
        cache.set(cache_key, data, timeout=600)
        
        return Response(data)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create new inspection.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set inspector from request user if not provided
        if 'inspector' not in request.data:
            serializer.validated_data['inspector'] = request.user
        
        inspection = serializer.save()
        
        logger.info(
            f"Inspection created: {inspection.inspection_id} by {request.user.username}"
        )
        
        # Return basic inspection data
        return Response(
            {
                'inspection_id': inspection.inspection_id,
                'plate_number': inspection.plate_number,
                'chassis_number': inspection.chassis_number,
                'vehicle_type': inspection.vehicle_type,
                'vehicle_category': inspection.vehicle_category,
                'status': inspection.status,
                'created_at': inspection.created_at.isoformat(),
                'center': inspection.center.code if inspection.center else None,
                'inspector': inspection.inspector.username if inspection.inspector else None,
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit_visual_checklist(self, request, inspection_id=None):
        """
        Submit 30-point visual checklist.
        Bulk operation for performance.
        
        POST /api/inspections/{id}/submit_visual_checklist/
        Body: {
            "items": [
                {
                    "item_number": 1,
                    "item_name_en": "Registration Plate Validity",
                    "item_name_am": "የሰሌዳ ቁጥር ትክክለኛነት",
                    "zone_id": "zone1",
                    "zone_name_en": "Identification & Documentation",
                    "points_possible": 5,
                    "status": "PASS",
                    "defect_type": "",
                    "is_critical": false,
                    "is_mandatory": false
                },
                ...
            ],
            "notes": "Optional notes"
        }
        """
        inspection = self.get_object()
        
        if inspection.status not in ['in_progress', 'pending_machine']:
            raise ValidationError("Visual checklist already submitted or inspection completed.")
        
        serializer = VisualChecklistBulkSerializer(
            data=request.data,
            context={'inspection': inspection}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        logger.info(
            f"Visual checklist submitted for {inspection.inspection_id}: "
            f"{result['points_earned']}/{result['points_total']} points"
        )
        
        return Response({
            'status': 'success',
            'message': 'Visual checklist submitted successfully',
            'visual_pass': result['visual_pass'],
            'points_earned': result['points_earned'],
            'points_total': result['points_total'],
            'items_count': len(result['items']),
        })
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit_machine_tests(self, request, inspection_id=None):
        """
        Submit machine test results.
        Bulk operation for performance.
        
        POST /api/inspections/{id}/submit_machine_tests/
        Body: {
            "tests": [
                {
                    "machine_test_id": "MT-2025-XXXX-1",
                    "test_type": "alignment",
                    "test_name": "Wheel Alignment & Suspension",
                    "test_data": {
                        "alignment_deviation": 2.5,
                        "suspension_left": 55.2,
                        "suspension_right": 58.1,
                        "suspension_diff": 2.9
                    },
                    "result": "PASS",
                    "pass_status": true,
                    "data_source": "RYME_SMRW",
                    "machine_serial": "RYME-AL-001"
                },
                ...
            ]
        }
        """
        inspection = self.get_object()
        
        # Refresh from database to ensure we have latest status
        inspection.refresh_from_db()
        
        # Log current status for debugging
        logger.info(
            f"Machine test submission attempt for {inspection.inspection_id}: "
            f"current status = {inspection.status}"
        )
        
        # Allow machine test submission if inspection is in progress or pending machine
        # Also allow if status is 'failed' (in case user wants to retest)
        # Note: 'pending_payment' status removed - inspections go directly to 'completed' when they pass
        allowed_statuses = ['pending_machine', 'in_progress', 'failed']
        if inspection.status not in allowed_statuses:
            logger.warning(
                f"Machine test submission rejected for {inspection.inspection_id}: "
                f"status {inspection.status} not in allowed statuses {allowed_statuses}"
            )
            raise ValidationError(
                f"Cannot submit machine tests at this stage. Current status: {inspection.status}. "
                f"Allowed statuses: {', '.join(allowed_statuses)}"
            )
        
        serializer = MachineTestBulkSerializer(
            data=request.data,
            context={'inspection': inspection}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        logger.info(
            f"Machine tests submitted for {inspection.inspection_id}: "
            f"{'PASS' if result['machine_test_pass'] else 'FAIL'}"
        )
        
        return Response({
            'status': 'success',
            'message': 'Machine tests submitted successfully',
            'machine_test_pass': result['machine_test_pass'],
            'overall_result': result['overall_result'],
            'tests_count': len(result['tests']),
        })
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def upload_photo(self, request, inspection_id=None):
        """
        Upload inspection photo.
        
        POST /api/inspections/{id}/upload_photo/
        Body: {
            "photo_id": "PHOTO-2025-XXXX",
            "purpose": "registration",
            "photo_url": "s3://bucket/path/to/photo.jpg",
            "latitude": 9.012345,
            "longitude": 38.765432,
            "gps_accuracy": 10.5,
            "timestamp": "2025-01-15T10:30:00Z",
            "file_size": 1024000
        }
        """
        inspection = self.get_object()
        
        serializer = InspectionPhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        photo = serializer.save(inspection=inspection)
        
        logger.info(f"Photo uploaded for {inspection.inspection_id}: {photo.photo_id}")
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def finalize(self, request, inspection_id=None):
        """
        Finalize inspection with payment.
        
        POST /api/inspections/{id}/finalize/
        Body: {
            "payment_transaction_id": "TXN-2025-XXXX",
            "payment_amount": 250.00
        }
        """
        inspection = self.get_object()
        
        if inspection.status != 'pending_payment':
            raise ValidationError("Inspection cannot be finalized at this stage.")
        
        serializer = InspectionFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        inspection = serializer.update(inspection)
        
        logger.info(f"Inspection finalized: {inspection.inspection_id}")
        
        return Response({
            'status': 'success',
            'message': 'Inspection finalized successfully',
            'inspection_id': inspection.inspection_id,
            'overall_result': inspection.overall_result,
            'status': inspection.status,
        })
    
    @action(detail=True, methods=['get'])
    def validate_geofence(self, request, inspection_id=None):
        """
        Validate if inspection location is within center geofence.
        
        GET /api/inspections/{id}/validate_geofence/?lat=9.012345&lng=38.765432
        """
        inspection = self.get_object()
        
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            raise ValidationError("Latitude and longitude are required.")
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            raise ValidationError("Invalid coordinates.")
        
        # Get center coordinates
        center = inspection.center
        if not center.latitude or not center.longitude:
            return Response({
                'valid': True,
                'message': 'Center geofence not configured',
                'distance_meters': None,
            })
        
        # Calculate distance (Haversine formula)
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        lat1, lon1 = radians(center.latitude), radians(center.longitude)
        lat2, lon2 = radians(lat), radians(lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        # Default geofence radius: 500 meters
        geofence_radius = getattr(center, 'geofence_radius_meters', 500)
        valid = distance <= geofence_radius
        
        return Response({
            'valid': valid,
            'distance_meters': round(distance, 2),
            'geofence_radius_meters': geofence_radius,
            'message': 'Within geofence' if valid else 'Outside geofence',
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get inspection statistics for dashboard.
        Heavily cached.
        
        GET /api/inspections/statistics/?range=today|week|month
        """
        user = request.user
        date_range = request.query_params.get('range', 'today')
        cache_key = f"inspection_stats:{user.user_id}:{date_range}"
        
        # Get filtered queryset
        queryset = self.get_queryset()
        
        # Filter by date range
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Calculate statistics
        # Pass count: inspections with PASS result and completed status
        # This counts inspections that have passed all tests (machine + visual) and are completed
        # No payment step required - inspections go directly to 'completed' when they pass
        pass_count = queryset.filter(overall_result='PASS', status='completed').count()
        
        # Fail count: includes both:
        # 1. Inspections with FAIL result and completed status
        # 2. Inspections with status='failed' (regardless of overall_result)
        # Use Q objects to combine conditions and distinct() to avoid double-counting
        fail_count = queryset.filter(
            Q(overall_result='FAIL', status='completed') | Q(status='failed')
        ).distinct().count()
        
        # Debug logging to verify counts
        completed_count = queryset.filter(status='completed').count()
        completed_with_pass = queryset.filter(status='completed', overall_result='PASS').count()
        completed_with_fail = queryset.filter(status='completed', overall_result='FAIL').count()
        completed_without_result = queryset.filter(status='completed', overall_result='').count()
        
        logger.info(
            f"Statistics calculation for {user.user_id} ({date_range}): "
            f"total={queryset.count()}, "
            f"completed={completed_count}, "
            f"completed_with_PASS={completed_with_pass}, "
            f"completed_with_FAIL={completed_with_fail}, "
            f"completed_without_result={completed_without_result}, "
            f"pass_count={pass_count}, "
            f"fail_count={fail_count}"
        )
        
        stats = {
            'total_inspections': queryset.count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'pending_machine': queryset.filter(status='pending_machine').count(),
            'pending_payment': 0,  # Deprecated - inspections go directly to 'completed' when they pass
            'completed': completed_count,
            'failed': queryset.filter(status='failed').count(),
            'pass_count': pass_count,
            'fail_count': fail_count,
            'pass_rate': 0,
        }
        
        # Calculate pass rate
        if completed_count > 0:
            stats['pass_rate'] = round((pass_count / completed_count) * 100, 2)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_inspections(self, request):
        """
        Get active (in-progress) inspections for inspector.
        
        GET /api/inspections/active/
        """
        queryset = self.get_queryset().filter(
            status__in=['in_progress', 'pending_machine']
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LightweightInspectionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LightweightInspectionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='completed')
    def completed_inspections(self, request):
        """
        Get completed inspections for inspector.
        
        GET /api/inspections/completed/?days=7
        """
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            status='completed',
            completed_at__gte=start_date
        ).order_by('-completed_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LightweightInspectionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LightweightInspectionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='vehicle-history')
    def vehicle_history(self, request):
        """
        Search vehicle inspection history.
        
        GET /api/inspections/vehicle-history/?plate=AA-12345
        GET /api/inspections/vehicle-history/?chassis=WBXXX
        GET /api/inspections/vehicle-history/?engine=N47XXX
        """
        plate = request.query_params.get('plate')
        chassis = request.query_params.get('chassis')
        engine = request.query_params.get('engine')
        
        if not any([plate, chassis, engine]):
            raise ValidationError("Provide at least one search parameter: plate, chassis, or engine")
        
        # Build query
        query = Q()
        if plate:
            query |= Q(plate_number__icontains=plate)
        if chassis:
            query |= Q(chassis_number__icontains=chassis)
        if engine:
            query |= Q(engine_number__icontains=engine)
        
        # Search inspections
        queryset = self.get_queryset().filter(query).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LightweightInspectionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LightweightInspectionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='sync-status')
    def update_sync_status(self, request, inspection_id=None):
        """
        Update inspection sync status.
        
        POST /api/inspections/{id}/sync-status/
        Body: {
            "sync_status": "synced|pending|failed",
            "sync_error": "Optional error message"
        }
        """
        inspection = self.get_object()
        sync_status = request.data.get('sync_status')
        sync_error = request.data.get('sync_error', '')
        
        if sync_status not in ['synced', 'pending', 'failed']:
            raise ValidationError("Invalid sync_status. Must be: synced, pending, or failed")
        
        inspection.sync_status = sync_status
        inspection.sync_error = sync_error
        if sync_status == 'synced':
            inspection.synced_at = timezone.now()
        inspection.save(update_fields=['sync_status', 'sync_error', 'synced_at'])
        
        logger.info(f"Sync status updated for {inspection.inspection_id}: {sync_status}")
        
        return Response({
            'status': 'success',
            'inspection_id': inspection.inspection_id,
            'sync_status': sync_status
        })
    
    @action(detail=True, methods=['post'], url_path='process-payment')
    def process_payment(self, request, inspection_id=None):
        """
        Process payment for inspection.
        
        POST /api/inspections/{id}/process-payment/
        Body: {
            "payment_method": "cash|card|mobile",
            "amount": 250.00,
            "transaction_id": "TXN-2025-XXXX",
            "reference": "Optional reference"
        }
        """
        inspection = self.get_object()
        
        if inspection.status != 'pending_payment':
            raise ValidationError("Inspection is not awaiting payment")
        
        payment_method = request.data.get('payment_method')
        amount = request.data.get('amount')
        transaction_id = request.data.get('transaction_id')
        reference = request.data.get('reference', '')
        
        if not all([payment_method, amount, transaction_id]):
            raise ValidationError("payment_method, amount, and transaction_id are required")
        
        if payment_method not in ['cash', 'card', 'mobile']:
            raise ValidationError("Invalid payment_method. Must be: cash, card, or mobile")
        
        # Ensure overall_result is calculated before marking as completed
        if not inspection.overall_result:
            inspection.calculate_overall_result()
        
        # Update inspection
        inspection.payment_status = 'paid'
        inspection.payment_method = payment_method
        inspection.payment_amount = amount
        inspection.payment_transaction_id = transaction_id
        inspection.payment_reference = reference
        inspection.payment_date = timezone.now()
        inspection.status = 'completed'
        inspection.completed_at = timezone.now()
        inspection.save(update_fields=[
            'payment_status', 'payment_method', 'payment_amount',
            'payment_transaction_id', 'payment_reference', 'payment_date',
            'status', 'completed_at', 'overall_result'
        ])
        
        logger.info(f"Payment processed for {inspection.inspection_id}: {amount} via {payment_method}")
        
        # Invalidate cache
        cache.delete(f"inspection:{inspection.inspection_id}")
        
        return Response({
            'status': 'success',
            'message': 'Payment processed successfully',
            'inspection_id': inspection.inspection_id,
            'payment_status': 'paid',
            'overall_result': inspection.overall_result
        })

    @action(detail=True, methods=['get'], url_path='machine-results')
    def get_machine_results(self, request, inspection_id=None):
        """
        Get all machine test results for an inspection (Admin Portal).
        
        GET /api/inspections/{id}/machine-results/
        
        Returns machine test data in a format expected by the admin portal.
        """
        inspection = self.get_object()
        
        # Get all machine tests
        machine_tests = inspection.machine_tests.all().order_by('timestamp')
        serializer = MachineTestSerializer(machine_tests, many=True)
        
        return Response({
            'inspection_id': inspection.inspection_id,
            'machine_test_pass': inspection.machine_test_pass,
            'tests': serializer.data,
            'total_tests': machine_tests.count()
        })

    @action(detail=True, methods=['get'], url_path='visual-results')
    def get_visual_results(self, request, inspection_id=None):
        """
        Get visual inspection checklist results (Admin Portal).
        
        GET /api/inspections/{id}/visual-results/
        
        Returns visual checklist data in a format expected by the admin portal.
        """
        inspection = self.get_object()
        
        # Get all visual checklist items
        visual_items = inspection.visual_items.all().order_by('item_number')
        serializer = VisualChecklistItemSerializer(visual_items, many=True)
        
        return Response({
            'inspection_id': inspection.inspection_id,
            'visual_pass': inspection.visual_pass,
            'points_earned': inspection.visual_points_earned,
            'points_total': inspection.visual_points_total,
            'items': serializer.data,
            'total_items': visual_items.count()
        })

    @action(detail=True, methods=['get'], url_path='photos')
    def get_photos(self, request, inspection_id=None):
        """
        Get all photos for an inspection (Admin Portal).
        
        GET /api/inspections/{id}/photos/
        
        Returns photo data with GPS metadata in a format expected by the admin portal.
        """
        inspection = self.get_object()
        
        # Get all photos
        photos = inspection.photos.all().order_by('uploaded_at')
        serializer = InspectionPhotoSerializer(photos, many=True)
        
        return Response({
            'inspection_id': inspection.inspection_id,
            'photos': serializer.data,
            'total_photos': photos.count()
        })


class MachineTestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for machine tests.
    Machine tests cannot be modified after submission.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = MachineTestSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get machine tests with inspection filtering."""
        queryset = MachineTest.objects.select_related('inspection').all()
        
        # Filter by inspection if provided
        inspection_id = self.request.query_params.get('inspection_id')
        if inspection_id:
            queryset = queryset.filter(inspection__inspection_id=inspection_id)
        
        # Filter by test type if provided
        test_type = self.request.query_params.get('test_type')
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        return queryset


class VisualChecklistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for visual checklist items.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = VisualChecklistItemSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get visual items with inspection filtering."""
        queryset = VisualChecklistItem.objects.select_related('inspection').all()
        
        # Filter by inspection if provided
        inspection_id = self.request.query_params.get('inspection_id')
        if inspection_id:
            queryset = queryset.filter(inspection__inspection_id=inspection_id)
        
        return queryset


class InspectionPhotoViewSet(viewsets.ModelViewSet):
    """
    API for inspection photos.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = InspectionPhotoSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get photos with inspection filtering."""
        queryset = InspectionPhoto.objects.select_related('inspection').all()
        
        # Filter by inspection if provided
        inspection_id = self.request.query_params.get('inspection_id')
        if inspection_id:
            queryset = queryset.filter(inspection__inspection_id=inspection_id)
        
        # Filter by purpose if provided
        purpose = self.request.query_params.get('purpose')
        if purpose:
            queryset = queryset.filter(purpose=purpose)
        
        return queryset


class VerifyByPlateView(APIView):
    """
    Public verification by plate number for mobile/checker apps.
    No authentication required. Returns latest completed inspection result and center.

    GET /api/verify/?plate=AA-12345
    """
    permission_classes = [AllowAny]

    def get(self, request):
        plate = (request.query_params.get('plate') or '').strip()
        if not plate:
            return Response(
                {'found': False, 'error': 'plate is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        inspection = (
            Inspection.objects
            .filter(status='completed', plate_number__iexact=plate)
            .select_related('center')
            .order_by('-completed_at')
            .first()
        )
        if not inspection:
            return Response({
                'found': False,
                'plate': plate,
                'message': 'No completed inspection found for this plate.',
            })
        return Response({
            'found': True,
            'plate_number': inspection.plate_number,
            'passed': (inspection.overall_result or '').upper() == 'PASS',
            'overall_result': inspection.overall_result or None,
            'inspection_id': inspection.inspection_id,
            'completed_at': inspection.completed_at.isoformat() if inspection.completed_at else None,
            'center': {
                'center_id': inspection.center.center_id,
                'name': inspection.center.name,
                'code': inspection.center.code,
                'region': inspection.center.region,
                'zone': getattr(inspection.center, 'zone', None) or '',
                'address': getattr(inspection.center, 'address', None) or '',
            } if inspection.center else None,
        })
