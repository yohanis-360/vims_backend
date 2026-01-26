"""
Serializers for Governance app.
"""
from rest_framework import serializers
from .models import AdminUnit, Institution


class AdminUnitListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing admin units."""
    
    class Meta:
        model = AdminUnit
        fields = [
            'admin_unit_id',
            'admin_unit_type',
            'admin_unit_name_en',
            'admin_unit_name_am',
            'admin_unit_code',
            'parent_admin_unit_id',
            'status',
        ]
        read_only_fields = fields


class AdminUnitDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for admin unit CRUD operations."""
    parent_admin_unit_name = serializers.CharField(
        source='parent_admin_unit_id.admin_unit_name_en',
        read_only=True
    )
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminUnit
        fields = '__all__'
        read_only_fields = [
            'created_at',
            'updated_at',
        ]
    
    def get_children_count(self, obj):
        """Get count of child admin units."""
        return obj.children.count()


class AdminUnitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating admin units."""
    
    admin_unit_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    jurisdiction_path = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = AdminUnit
        fields = [
            'admin_unit_id',
            'admin_unit_type',
            'admin_unit_name_en',
            'admin_unit_name_am',
            'admin_unit_code',
            'parent_admin_unit_id',
            'jurisdiction_path',
            'status',
            'effective_from',
            'effective_to',
        ]
    
    def validate_admin_unit_id(self, value):
        """Ensure unique admin unit ID if provided."""
        if value and AdminUnit.objects.filter(admin_unit_id=value).exists():
            raise serializers.ValidationError("Admin unit ID already exists.")
        return value
    
    def validate(self, data):
        """Validate hierarchical structure."""
        parent = data.get('parent_admin_unit_id')
        unit_type = data.get('admin_unit_type')
        
        # Validate parent-child relationship
        if parent:
            parent_type = parent.admin_unit_type
            valid_parents = {
                'Region': ['National'],
                'Zone': ['Region'],
                'Sub-city': ['Region'],
                'Woreda': ['Zone', 'Sub-city'],
                'Center-Cluster': ['Woreda'],
            }
            
            if unit_type in valid_parents:
                if parent_type not in valid_parents[unit_type]:
                    raise serializers.ValidationError(
                        f"{unit_type} must have a parent of type: {', '.join(valid_parents[unit_type])}"
                    )
        
        return data


class AdminUnitUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating admin units."""
    
    class Meta:
        model = AdminUnit
        fields = [
            'admin_unit_name_en',
            'admin_unit_name_am',
            'admin_unit_code',
            'status',
            'effective_from',
            'effective_to',
        ]


class InstitutionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing institutions."""
    region_name = serializers.CharField(
        source='region_id.admin_unit_name_en',
        read_only=True
    )
    
    class Meta:
        model = Institution
        fields = [
            'institution_id',
            'institution_type',
            'institution_name_en',
            'institution_name_am',
            'institution_short_name',
            'region_name',
            'status',
        ]
        read_only_fields = fields


class InstitutionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for institution CRUD operations."""
    region_name = serializers.CharField(
        source='region_id.admin_unit_name_en',
        read_only=True
    )
    
    class Meta:
        model = Institution
        fields = [
            'institution_id',
            'institution_type',
            'institution_name_en',
            'institution_name_am',
            'institution_short_name',
            'registration_number',
            'contact_person_name',
            'contact_phone',
            'contact_email',
            'address_text',
            'region_id',
            'region_name',
            'status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'institution_id',
            'created_at',
            'updated_at',
            'region_name',
        ]


class InstitutionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating institutions."""
    
    class Meta:
        model = Institution
        fields = [
            'institution_type',
            'institution_name_en',
            'institution_name_am',
            'institution_short_name',
            'registration_number',
            'contact_person_name',
            'contact_phone',
            'contact_email',
            'address_text',
            'region_id',
            'status',
            'notes',
        ]


class InstitutionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating institutions."""
    
    institution_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Institution
        fields = [
            'institution_id',
            'institution_type',
            'institution_name_en',
            'institution_name_am',
            'institution_short_name',
            'registration_number',
            'contact_person_name',
            'contact_phone',
            'contact_email',
            'address_text',
            'region_id',
            'status',
            'notes',
        ]
    
    def validate_institution_id(self, value):
        """Ensure unique institution ID if provided."""
        if value and Institution.objects.filter(institution_id=value).exists():
            raise serializers.ValidationError("Institution ID already exists.")
        return value
    
    def create(self, validated_data):
        """Create institution with auto-generated ID if not provided."""
        if not validated_data.get('institution_id'):
            # Auto-generate institution_id
            institution_type = validated_data.get('institution_type', 'INST')
            name_part = ''.join(word[:3].upper() for word in validated_data.get('institution_name_en', 'INST').split()[:2])
            if len(name_part) < 3:
                name_part = validated_data.get('institution_name_en', 'INST')[:10].upper().replace(' ', '')
            type_prefix = institution_type[:3].upper()
            base_id = f"{type_prefix}-{name_part}"
            
            counter = 1
            institution_id = base_id
            while Institution.objects.filter(institution_id=institution_id).exists():
                institution_id = f"{base_id}-{counter}"
                counter += 1
            validated_data['institution_id'] = institution_id
        
        return super().create(validated_data)


