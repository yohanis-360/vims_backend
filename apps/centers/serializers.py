"""
Serializers for Center management.
"""
from rest_framework import serializers
from .models import Center


class CenterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing centers - includes all fields needed for display."""
    
    class Meta:
        model = Center
        fields = [
            # Basic Information
            'center_id', 'name', 'code', 'region', 'zone', 'subcity', 'woreda', 'address',
            # Contact Information
            'phone', 'email', 'fax',
            # Business Registration
            'tin', 'vat', 'principal_registration_no', 'business_license_no',
            'business_license_date_of_issuance', 'place_of_issue', 'date_of_issue',
            # Owner/Company Information
            'owner_company_name', 'nationality', 'trade_name', 'general_manager_name',
            # Additional Location Details
            'kebele', 'house_no',
            # Business Details
            'field_of_business', 'capital_in_etb',
            # Additional Information
            'telebirr_number', 'camera_configuration', 'commercial_registration_procedure',
            # Documents
            'business_license_document', 'registration_certificate_document', 'tax_certificate_document', 'other_documents',
            # Geofence
            'latitude', 'longitude', 'geofence_radius_meters',
            # Status
            'status', 'is_active',
            # Metrics
            'total_inspections', 'pass_rate', 'attention_score',
            'last_inspection_date', 'last_seen', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class CenterDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for center CRUD operations."""
    
    class Meta:
        model = Center
        fields = '__all__'
        read_only_fields = [
            'total_inspections', 'last_inspection_date', 'pass_rate',
            'average_cycle_time_minutes', 'attention_score',
            'last_seen', 'created_at', 'updated_at'
        ]


class CenterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new centers - includes all frontend fields."""
    
    class Meta:
        model = Center
        fields = [
            # Basic Information
            'center_id', 'name', 'code', 'region', 'zone', 'subcity', 'woreda', 'address',
            # Contact Information
            'phone', 'email', 'fax',
            # Business Registration
            'tin', 'vat', 'principal_registration_no', 'business_license_no',
            'business_license_date_of_issuance', 'place_of_issue', 'date_of_issue',
            # Owner/Company Information
            'owner_company_name', 'nationality', 'trade_name', 'general_manager_name',
            # Additional Location Details
            'kebele', 'house_no',
            # Business Details
            'field_of_business', 'capital_in_etb',
            # Additional Information
            'telebirr_number', 'camera_configuration', 'commercial_registration_procedure',
            # Documents
            'business_license_document', 'registration_certificate_document', 'tax_certificate_document', 'other_documents',
            # Geofence
            'latitude', 'longitude', 'geofence_radius_meters',
            # Status
            'status', 'is_active'
        ]
    
    def validate_other_documents(self, value):
        """Validate other_documents is a list."""
        if not isinstance(value, list):
            return []
        return value
    
    def validate_center_id(self, value):
        """Ensure unique center ID."""
        if Center.objects.filter(center_id=value).exists():
            raise serializers.ValidationError("Center ID already exists.")
        return value
    
    def validate_code(self, value):
        """Ensure unique center code."""
        if Center.objects.filter(code=value).exists():
            raise serializers.ValidationError("Center code already exists.")
        return value
    
    def validate(self, data):
        """Validate geofence data."""
        if data.get('latitude') and data.get('longitude'):
            if not (-90 <= float(data['latitude']) <= 90):
                raise serializers.ValidationError("Invalid latitude value.")
            if not (-180 <= float(data['longitude']) <= 180):
                raise serializers.ValidationError("Invalid longitude value.")
        return data


class CenterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating centers - includes all frontend fields."""
    
    class Meta:
        model = Center
        fields = [
            # Basic Information
            'name', 'code', 'region', 'zone', 'subcity', 'woreda', 'address',
            # Contact Information
            'phone', 'email', 'fax',
            # Business Registration
            'tin', 'vat', 'principal_registration_no', 'business_license_no',
            'business_license_date_of_issuance', 'place_of_issue', 'date_of_issue',
            # Owner/Company Information
            'owner_company_name', 'nationality', 'trade_name', 'general_manager_name',
            # Additional Location Details
            'kebele', 'house_no',
            # Business Details
            'field_of_business', 'capital_in_etb',
            # Additional Information
            'telebirr_number', 'camera_configuration', 'commercial_registration_procedure',
            # Documents
            'business_license_document', 'registration_certificate_document', 'tax_certificate_document', 'other_documents',
            # Geofence
            'latitude', 'longitude', 'geofence_radius_meters',
            # Status
            'status', 'is_active'
        ]


class CenterStatisticsSerializer(serializers.Serializer):
    """Serializer for center statistics."""
    total_centers = serializers.IntegerField()
    active_centers = serializers.IntegerField()
    inactive_centers = serializers.IntegerField()
    maintenance_centers = serializers.IntegerField()
    total_inspections = serializers.IntegerField()
    average_pass_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    centers_by_region = serializers.DictField()


class GeofenceUpdateSerializer(serializers.Serializer):
    """Serializer for updating center geofence."""
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    radius_meters = serializers.IntegerField(min_value=50, max_value=5000)
    
    def validate(self, data):
        """Validate geofence coordinates."""
        if not (-90 <= float(data['latitude']) <= 90):
            raise serializers.ValidationError("Invalid latitude value.")
        if not (-180 <= float(data['longitude']) <= 180):
            raise serializers.ValidationError("Invalid longitude value.")
        return data


