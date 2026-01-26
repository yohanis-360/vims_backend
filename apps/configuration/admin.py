"""
Admin interface for Configuration models.
"""
from django.contrib import admin
from .models import VisualChecklistConfig, TestStandard, FeeStructure


@admin.register(VisualChecklistConfig)
class VisualChecklistConfigAdmin(admin.ModelAdmin):
    """Admin interface for Visual Checklist Configuration."""
    list_display = [
        'item_number', 'item_name_en', 'vehicle_category', 'zone_id',
        'points_possible', 'is_critical', 'is_mandatory', 'status', 'display_order'
    ]
    list_filter = ['vehicle_category', 'zone_id', 'status', 'is_critical', 'is_mandatory']
    search_fields = ['item_name_en', 'item_name_am', 'zone_name_en']
    ordering = ['vehicle_category', 'zone_id', 'display_order', 'item_number']
    fieldsets = (
        ('Basic Information', {
            'fields': ('config_id', 'vehicle_category', 'zone_id', 'zone_name_en', 'zone_name_am')
        }),
        ('Item Details', {
            'fields': ('item_number', 'item_name_en', 'item_name_am', 'display_order')
        }),
        ('Points & Requirements', {
            'fields': ('points_possible', 'is_critical', 'is_mandatory')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )


@admin.register(TestStandard)
class TestStandardAdmin(admin.ModelAdmin):
    """Admin interface for Test Standards."""
    list_display = ['standard_id', 'vehicle_category', 'test_type', 'min_value', 'max_value', 'unit', 'is_active']
    list_filter = ['vehicle_category', 'test_type', 'is_active']
    search_fields = ['description']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    """Admin interface for Fee Structures."""
    list_display = ['fee_id', 'vehicle_category', 'vehicle_type', 'inspection_fee', 'retest_fee', 'is_active', 'effective_from']
    list_filter = ['vehicle_category', 'is_active']
    search_fields = ['vehicle_type']

