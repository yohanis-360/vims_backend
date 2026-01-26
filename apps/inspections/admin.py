"""
Django Admin Configuration for Inspections.
"""
from django.contrib import admin
from .models import (
    Inspection, MachineTest, AlignmentTest, BrakeTest,
    EmissionsTest, HeadlightTest, VisualChecklistItem,
    InspectionPhoto, InspectionVideo
)


class MachineTestInline(admin.TabularInline):
    """Inline display for machine tests."""
    model = MachineTest
    extra = 0
    readonly_fields = ['machine_test_id', 'test_type', 'result', 'timestamp', 'is_locked']
    can_delete = False  # Machine tests cannot be deleted
    
    def has_add_permission(self, request, obj=None):
        """Machine tests can only be added via API."""
        return False


class VisualChecklistItemInline(admin.TabularInline):
    """Inline display for visual checklist items."""
    model = VisualChecklistItem
    extra = 0
    fields = ['item_number', 'item_name_en', 'status', 'points_earned', 'points_possible']
    readonly_fields = ['checked_at']


class InspectionPhotoInline(admin.TabularInline):
    """Inline display for inspection photos."""
    model = InspectionPhoto
    extra = 0
    fields = ['photo_id', 'purpose', 'photo_url', 'timestamp']
    readonly_fields = ['uploaded_at']


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    """Admin interface for Inspection model."""
    
    list_display = [
        'inspection_id', 'plate_number', 'vehicle_category', 'center',
        'inspector', 'status', 'overall_result', 'created_at'
    ]
    list_filter = [
        'status', 'overall_result', 'vehicle_category', 'fuel_type',
        'payment_status', 'created_at'
    ]
    search_fields = [
        'inspection_id', 'plate_number', 'chassis_number', 'engine_number',
        'owner_name'
    ]
    readonly_fields = [
        'inspection_id', 'created_at', 'updated_at', 'test_start_time',
        'test_end_time', 'visual_points_earned', 'visual_points_total'
    ]
    
    fieldsets = (
        ('Identification', {
            'fields': ('inspection_id', 'form_id', 'center', 'inspector')
        }),
        ('Vehicle Information', {
            'fields': (
                'plate_number', 'chassis_number', 'engine_number',
                'vehicle_type', 'vehicle_category', 'brand_model',
                'fuel_type', 'kilometer_reading', 'licensed_capacity',
                'title_certificate', 'owner_name'
            )
        }),
        ('Inspection Results', {
            'fields': (
                'status', 'overall_result', 'visual_pass', 'machine_test_pass',
                'visual_points_earned', 'visual_points_total'
            )
        }),
        ('Payment', {
            'fields': (
                'payment_status', 'payment_amount', 'payment_transaction_id'
            )
        }),
        ('Timestamps', {
            'fields': ('test_start_time', 'test_end_time', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [VisualChecklistItemInline, MachineTestInline, InspectionPhotoInline]
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related('center', 'inspector')


@admin.register(MachineTest)
class MachineTestAdmin(admin.ModelAdmin):
    """Admin interface for Machine Test model."""
    
    list_display = [
        'machine_test_id', 'inspection', 'test_type', 'result',
        'data_source', 'timestamp'
    ]
    list_filter = ['test_type', 'result', 'data_source', 'timestamp']
    search_fields = ['machine_test_id', 'inspection__inspection_id', 'machine_serial']
    readonly_fields = ['machine_test_id', 'timestamp', 'is_locked']
    
    fieldsets = (
        ('Test Information', {
            'fields': (
                'machine_test_id', 'inspection', 'test_type', 'test_name'
            )
        }),
        ('Test Data', {
            'fields': ('test_data', 'result', 'pass_status')
        }),
        ('Source & Metadata', {
            'fields': (
                'data_source', 'machine_serial', 'timestamp', 'is_locked'
            )
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Machine tests cannot be deleted."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Machine tests cannot be modified if locked."""
        if obj and obj.is_locked:
            return False
        return super().has_change_permission(request, obj)


@admin.register(VisualChecklistItem)
class VisualChecklistItemAdmin(admin.ModelAdmin):
    """Admin interface for Visual Checklist Item model."""
    
    list_display = [
        'inspection', 'item_number', 'item_name_en', 'status',
        'points_earned', 'points_possible', 'is_critical'
    ]
    list_filter = ['status', 'is_critical', 'is_mandatory', 'zone_id']
    search_fields = ['inspection__inspection_id', 'item_name_en']
    readonly_fields = ['checked_at']


@admin.register(InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    """Admin interface for Inspection Photo model."""
    
    list_display = [
        'photo_id', 'inspection', 'purpose', 'timestamp', 'uploaded_at'
    ]
    list_filter = ['purpose', 'timestamp']
    search_fields = ['photo_id', 'inspection__inspection_id']
    readonly_fields = ['photo_id', 'uploaded_at']
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('photo_id', 'inspection', 'purpose', 'photo_url')
        }),
        ('GPS Metadata', {
            'fields': ('latitude', 'longitude', 'gps_accuracy')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'file_size', 'uploaded_at')
        }),
    )


@admin.register(InspectionVideo)
class InspectionVideoAdmin(admin.ModelAdmin):
    """Admin interface for Inspection Video model."""
    
    list_display = [
        'video_id', 'inspection', 'duration_seconds', 'file_size',
        'timestamp', 'uploaded_at'
    ]
    search_fields = ['video_id', 'inspection__inspection_id']
    readonly_fields = ['video_id', 'uploaded_at']


@admin.register(AlignmentTest)
class AlignmentTestAdmin(admin.ModelAdmin):
    """Admin interface for Alignment Test model."""
    
    list_display = [
        'machine_test', 'alignment_deviation', 'alignment_pass',
        'suspension_left', 'suspension_right', 'suspension_pass'
    ]
    readonly_fields = ['machine_test']


@admin.register(BrakeTest)
class BrakeTestAdmin(admin.ModelAdmin):
    """Admin interface for Brake Test model."""
    
    list_display = [
        'machine_test', 'brake_type', 'total_force', 'overall_pass'
    ]
    list_filter = ['brake_type', 'overall_pass']
    readonly_fields = ['machine_test']


@admin.register(EmissionsTest)
class EmissionsTestAdmin(admin.ModelAdmin):
    """Admin interface for Emissions Test model."""
    
    list_display = [
        'machine_test', 'emission_type', 'overall_pass'
    ]
    list_filter = ['emission_type', 'overall_pass']
    readonly_fields = ['machine_test']


@admin.register(HeadlightTest)
class HeadlightTestAdmin(admin.ModelAdmin):
    """Admin interface for Headlight Test model."""
    
    list_display = [
        'machine_test', 'left_intensity', 'left_pass',
        'right_intensity', 'right_pass', 'overall_pass'
    ]
    readonly_fields = ['machine_test']
