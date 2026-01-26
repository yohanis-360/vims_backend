"""
Serializers for Configuration models.
"""
from rest_framework import serializers
from .models import VisualChecklistConfig, TestStandard, FeeStructure


class VisualChecklistConfigSerializer(serializers.ModelSerializer):
    """Serializer for visual checklist configuration."""
    
    class Meta:
        model = VisualChecklistConfig
        fields = [
            'config_id', 'vehicle_category', 'zone_id', 'zone_name_en', 'zone_name_am',
            'item_number', 'item_name_en', 'item_name_am', 'points_possible',
            'is_critical', 'is_mandatory', 'display_order', 'status'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Auto-generate config_id if not provided."""
        if not data.get('config_id'):
            vehicle_category = data.get('vehicle_category')
            zone_id = data.get('zone_id')
            item_number = data.get('item_number')
            if vehicle_category and zone_id and item_number:
                data['config_id'] = f"CFG-{vehicle_category}-{zone_id}-{item_number:02d}"
        return data
    
    def validate_item_number(self, value):
        """Validate item number is within range."""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Item number must be between 1 and 100.")
        return value


class TestStandardSerializer(serializers.ModelSerializer):
    """Serializer for test standards."""
    
    class Meta:
        model = TestStandard
        fields = '__all__'
        read_only_fields = ['standard_id', 'created_at', 'updated_at']


class FeeStructureSerializer(serializers.ModelSerializer):
    """Serializer for fee structures."""
    
    class Meta:
        model = FeeStructure
        fields = '__all__'
        read_only_fields = ['fee_id', 'created_at', 'updated_at']

