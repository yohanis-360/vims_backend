"""
Serializers for Inspection API.
Optimized for performance with selective field loading.
"""
from rest_framework import serializers
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .models import (
    Inspection, MachineTest, AlignmentTest, BrakeTest,
    EmissionsTest, HeadlightTest, VisualChecklistItem,
    InspectionPhoto, InspectionVideo
)
from apps.centers.models import Center
from apps.centers.serializers import CenterDetailSerializer
from apps.users.models import User
from apps.users.serializers import UserDetailSerializer


class AnyValueField(serializers.Field):
    """Field that accepts any value without validation - NO VALIDATION AT ALL."""
    def to_internal_value(self, data):
        """Accept any value - NO VALIDATION, accept anything."""
        # Accept any value - no validation, no restrictions
        if data is None or data == '':
            return None
        # Try to convert to Decimal for the model field, but if it fails, return None
        # This allows the model to handle it (field allows null)
        try:
            return Decimal(str(data))
        except (InvalidOperation, ValueError, TypeError, Exception):
            # If ANY error occurs, just return None - field allows null
            return None
    
    def to_representation(self, value):
        """Return value as-is."""
        return value
    
    def run_validation(self, data):
        """Override to skip all validation - just return the value."""
        # Skip all validation - just convert and return
        return self.to_internal_value(data)


class LightweightInspectionSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views - includes essential fields for display."""
    
    # Include nested inspector and center data
    inspector = UserDetailSerializer(read_only=True)
    center = CenterDetailSerializer(read_only=True)
    
    class Meta:
        model = Inspection
        fields = [
            'inspection_id', 'plate_number', 'status', 'overall_result',
            'created_at', 'test_start_time', 'completed_at',
            'chassis_number', 'engine_number', 'brand_model', 'vehicle_type', 'vehicle_category',
            'owner_name', 'fuel_type', 'kilometer_reading',
            'inspector', 'center', 'center_id',
            'machine_test_pass', 'visual_pass',
            'form_id'
        ]
        read_only_fields = fields


class VisualChecklistItemSerializer(serializers.ModelSerializer):
    """Serializer for visual checklist items."""
    
    class Meta:
        model = VisualChecklistItem
        fields = [
            'item_number', 'item_name_en', 'item_name_am', 'zone_id',
            'zone_name_en', 'points_possible', 'points_earned', 'status',
            'defect_type', 'is_critical', 'is_mandatory', 'checked_at'
        ]
        read_only_fields = ['points_earned', 'checked_at']
    
    def validate(self, data):
        """Calculate points based on status."""
        if data.get('status') == 'PASS':
            data['points_earned'] = data.get('points_possible', 0)
        else:
            data['points_earned'] = 0
        return data


class InspectionPhotoSerializer(serializers.ModelSerializer):
    """Serializer for inspection photos with GPS metadata."""
    
    # Use custom field that accepts any value without validation
    latitude = AnyValueField(required=False, allow_null=True)
    longitude = AnyValueField(required=False, allow_null=True)
    
    class Meta:
        model = InspectionPhoto
        fields = [
            'photo_id', 'purpose', 'photo_url', 'latitude', 'longitude',
            'gps_accuracy', 'timestamp', 'file_size', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']
        extra_kwargs = {
            'gps_accuracy': {'required': False, 'allow_null': True},
        }
    
    def validate_photo_url(self, value):
        """Accept any photo URL/path or base64 data URL - no validation, no restrictions."""
        # Accept any value - no validation, no size limits, no format checks
        return value or ''  # Even accept empty string


class InspectionVideoSerializer(serializers.ModelSerializer):
    """Serializer for inspection videos."""
    
    class Meta:
        model = InspectionVideo
        fields = [
            'video_id', 'video_url', 'duration_seconds', 'file_size',
            'timestamp', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at']


class MachineTestSerializer(serializers.ModelSerializer):
    """
    Serializer for machine test data.
    Machine data is READ-ONLY after submission.
    """
    
    inspection = serializers.PrimaryKeyRelatedField(
        queryset=Inspection.objects.all(),
        required=False  # Set automatically in bulk operations
    )
    
    class Meta:
        model = MachineTest
        fields = [
            'machine_test_id', 'inspection', 'test_type', 'test_name',
            'test_data', 'result', 'pass_status', 'data_source',
            'machine_serial', 'timestamp', 'is_locked'
        ]
        read_only_fields = ['timestamp', 'is_locked']
        extra_kwargs = {
            'test_data': {'required': True},
            'result': {'required': True},
            'pass_status': {'required': True},
        }
    
    def validate(self, data):
        """Prevent modification of locked machine tests."""
        instance = getattr(self, 'instance', None)
        if instance and instance.is_locked:
            raise serializers.ValidationError(
                "Machine test data is locked and cannot be modified."
            )
        
        # Auto-lock on creation
        data['is_locked'] = True
        return data
    
    def create(self, validated_data):
        """Create machine test with audit trail."""
        test = super().create(validated_data)
        
        # Invalidate inspection cache
        cache_key = f"inspection:{test.inspection.inspection_id}"
        cache.delete(cache_key)
        
        return test


class AlignmentTestSerializer(serializers.ModelSerializer):
    """Detailed serializer for alignment tests."""
    
    class Meta:
        model = AlignmentTest
        fields = '__all__'


class BrakeTestSerializer(serializers.ModelSerializer):
    """Detailed serializer for brake tests."""
    
    class Meta:
        model = BrakeTest
        fields = '__all__'


class EmissionsTestSerializer(serializers.ModelSerializer):
    """Detailed serializer for emissions tests."""
    
    class Meta:
        model = EmissionsTest
        fields = '__all__'


class HeadlightTestSerializer(serializers.ModelSerializer):
    """Detailed serializer for headlight tests."""
    
    class Meta:
        model = HeadlightTest
        fields = '__all__'


class InspectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new inspections."""
    
    inspector = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,  # Will be set automatically from request.user
        allow_null=True
    )
    
    class Meta:
        model = Inspection
        fields = [
            'inspection_id', 'plate_number', 'chassis_number', 'engine_number',
            'vehicle_type', 'vehicle_category', 'brand_model', 'fuel_type',
            'kilometer_reading', 'licensed_capacity', 'title_certificate',
            'owner_name', 'center', 'inspector', 'form_id', 'test_start_time'
        ]
    
    def validate_inspection_id(self, value):
        """Ensure unique inspection ID."""
        if Inspection.objects.filter(inspection_id=value).exists():
            raise serializers.ValidationError(
                "Inspection ID already exists. Please generate a new one."
            )
        return value
    
    def validate_center(self, value):
        """Validate center exists and is active."""
        if not Center.objects.filter(center_id=value.center_id, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive center.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Create inspection with proper defaults."""
        validated_data.setdefault('status', 'in_progress')
        validated_data.setdefault('payment_status', 'unpaid')
        validated_data.setdefault('payment_amount', 0)
        
        inspection = super().create(validated_data)
        
        # Note: Caching will be handled by the retrieve view when needed
        
        return inspection


class InspectionDetailSerializer(serializers.ModelSerializer):
    """Full detailed serializer for inspection with all related data."""
    
    machine_tests = MachineTestSerializer(many=True, read_only=True)
    visual_items = VisualChecklistItemSerializer(many=True, read_only=True)
    photos = InspectionPhotoSerializer(many=True, read_only=True)
    videos = InspectionVideoSerializer(many=True, read_only=True)
    
    # Return inspector and center as nested objects (like machine_tests, photos, etc.)
    inspector = UserDetailSerializer(read_only=True)
    center = CenterDetailSerializer(read_only=True)
    
    # Computed fields
    machine_test_count = serializers.SerializerMethodField()
    visual_items_count = serializers.SerializerMethodField()
    photos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Inspection
        fields = '__all__'
    
    def get_machine_test_count(self, obj):
        """Get count of machine tests."""
        return obj.machine_tests.count()
    
    def get_visual_items_count(self, obj):
        """Get count of visual items."""
        return obj.visual_items.count()
    
    def get_photos_count(self, obj):
        """Get count of photos."""
        return obj.photos.count()


class InspectionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating inspection status."""
    
    class Meta:
        model = Inspection
        fields = [
            'status', 'overall_result', 'visual_pass', 'machine_test_pass',
            'test_end_time', 'payment_status', 'payment_amount',
            'payment_transaction_id'
        ]
    
    def update(self, instance, validated_data):
        """Update inspection with cache invalidation."""
        inspection = super().update(instance, validated_data)
        
        # Invalidate cache
        cache_key = f"inspection:{inspection.inspection_id}"
        cache.delete(cache_key)
        
        return inspection


class VisualChecklistBulkSerializer(serializers.Serializer):
    """Bulk create visual checklist items."""
    
    items = VisualChecklistItemSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    @transaction.atomic
    def create(self, validated_data):
        """Create all visual items in a single transaction."""
        inspection = self.context['inspection']
        items_data = validated_data['items']
        
        # Delete existing items (if any)
        VisualChecklistItem.objects.filter(inspection=inspection).delete()
        
        # Create new items
        visual_items = [
            VisualChecklistItem(inspection=inspection, **item_data)
            for item_data in items_data
        ]
        VisualChecklistItem.objects.bulk_create(visual_items)
        
        # Calculate visual pass
        total_items = len(visual_items)
        passed_items = sum(1 for item in items_data if item['status'] == 'PASS')
        visual_pass = (passed_items / total_items >= 0.8) if total_items > 0 else False  # 80% pass threshold
        
        # Update inspection
        inspection.visual_pass = visual_pass
        inspection.visual_points_earned = sum(
            item['points_earned'] for item in items_data
        )
        inspection.visual_points_total = sum(
            item['points_possible'] for item in items_data
        )
        if getattr(inspection, 'vehicle_category', None) == 'MOTOR':
            # Motor / 3-wheel: no machine tests — complete after visual only
            inspection.overall_result = 'PASS' if visual_pass else 'FAIL'
            inspection.status = 'completed'
            inspection.completed_at = timezone.now()
            inspection.machine_test_pass = True  # N/A for motor
            inspection.save(update_fields=[
                'visual_pass', 'visual_points_earned', 'visual_points_total',
                'status', 'overall_result', 'completed_at', 'machine_test_pass'
            ])
        else:
            inspection.status = 'pending_machine'
            inspection.save(update_fields=[
                'visual_pass', 'visual_points_earned', 'visual_points_total', 'status'
            ])
        
        # Invalidate cache
        cache_key = f"inspection:{inspection.inspection_id}"
        cache.delete(cache_key)
        
        return {
            'items': visual_items,
            'visual_pass': visual_pass,
            'points_earned': inspection.visual_points_earned,
            'points_total': inspection.visual_points_total,
        }


class MachineTestBulkSerializer(serializers.Serializer):
    """Bulk submit machine tests."""
    
    tests = MachineTestSerializer(many=True)
    
    @transaction.atomic
    def create(self, validated_data):
        """Submit all machine tests in a single transaction."""
        inspection = self.context['inspection']
        tests_data = validated_data['tests']
        
        # Create machine tests
        machine_tests = []
        for test_data in tests_data:
            test_data['inspection'] = inspection
            test_data['is_locked'] = True
            machine_test = MachineTest.objects.create(**test_data)
            machine_tests.append(machine_test)
        
        # Calculate machine test pass
        all_passed = all(test['pass_status'] for test in tests_data)
        
        # Log machine test results for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Machine test submission for {inspection.inspection_id}: "
            f"total_tests={len(tests_data)}, "
            f"all_passed={all_passed}, "
            f"test_results={[{'type': t.get('test_type'), 'passed': t.get('pass_status')} for t in tests_data]}"
        )
        
        # Update inspection
        inspection.machine_test_pass = all_passed
        
        # Calculate overall result first
        inspection.calculate_overall_result()
        
        # When machine tests pass, set status directly to 'completed' (no payment step)
        # When machine tests fail, set status to 'failed'
        if all_passed:
            # Check if visual inspection also passed
            if inspection.visual_pass:
                inspection.status = 'completed'
                inspection.completed_at = timezone.now()
                logger.info(
                    f"Inspection {inspection.inspection_id} completed: "
                    f"machine_test_pass={all_passed}, visual_pass={inspection.visual_pass}, "
                    f"overall_result={inspection.overall_result}, status=completed"
                )
            else:
                # Machine tests passed but visual failed
                inspection.status = 'failed'
                logger.info(
                    f"Inspection {inspection.inspection_id} failed: "
                    f"machine_test_pass={all_passed}, visual_pass={inspection.visual_pass}, "
                    f"overall_result={inspection.overall_result}, status=failed"
                )
        else:
            # Machine tests failed
            inspection.status = 'failed'
            logger.info(
                f"Inspection {inspection.inspection_id} failed: "
                f"machine_test_pass={all_passed}, overall_result={inspection.overall_result}, status=failed"
            )
        
        inspection.save(update_fields=['machine_test_pass', 'status', 'overall_result', 'completed_at'])
        
        # Invalidate cache
        cache_key = f"inspection:{inspection.inspection_id}"
        cache.delete(cache_key)
        
        return {
            'tests': machine_tests,
            'machine_test_pass': all_passed,
            'overall_result': inspection.overall_result,
        }


class InspectionFinalizeSerializer(serializers.Serializer):
    """Finalize inspection with payment."""
    
    payment_transaction_id = serializers.CharField(max_length=100)
    payment_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    @transaction.atomic
    def update(self, instance):
        """Finalize inspection."""
        # Ensure overall_result is calculated before marking as completed
        if not instance.overall_result:
            instance.calculate_overall_result()
        
        instance.payment_status = 'paid'
        instance.payment_transaction_id = self.validated_data['payment_transaction_id']
        instance.payment_amount = self.validated_data['payment_amount']
        instance.status = 'completed'
        instance.test_end_time = timezone.now()
        instance.completed_at = timezone.now()
        instance.save(update_fields=[
            'payment_status', 'payment_transaction_id', 'payment_amount',
            'status', 'test_end_time', 'completed_at', 'overall_result'
        ])
        
        # Invalidate cache
        cache_key = f"inspection:{instance.inspection_id}"
        cache.delete(cache_key)
        
        # Trigger async tasks (certificate generation, etc.)
        from .tasks import generate_inspection_certificate
        generate_inspection_certificate.delay(instance.inspection_id)
        
        return instance
