"""
Governance models for VIMS Backend.
Administrative Units (Regions, Zones, Woredas, etc.)
"""
from django.db import models
from django.core.validators import MinLengthValidator


class AdminUnit(models.Model):
    """
    Administrative Unit model for hierarchical governance structure.
    Represents Regions, Zones, Sub-cities, Woredas, etc.
    """
    
    ADMIN_UNIT_TYPES = [
        ('Region', 'Region'),
        ('Zone', 'Zone'),
        ('Woreda', 'Woreda'),
        ('Kebele', 'Kebele'),
        ('National', 'National'),
        ('Sub-city', 'Sub-city'),
        ('Center-Cluster', 'Center-Cluster'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]
    
    admin_unit_id = models.CharField(
        max_length=50, 
        unique=True, 
        primary_key=True,
        validators=[MinLengthValidator(3)],
        help_text='Unique identifier for the administrative unit (auto-generated from name if not provided)'
    )
    admin_unit_type = models.CharField(
        max_length=20, 
        choices=ADMIN_UNIT_TYPES,
        db_index=True,
        help_text='Type of administrative unit (Region, Zone, etc.)'
    )
    admin_unit_name_en = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Administrative unit name in English'
    )
    admin_unit_name_am = models.CharField(
        max_length=255,
        blank=True,
        help_text='Administrative unit name in Amharic'
    )
    admin_unit_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Short code for the administrative unit'
    )
    parent_admin_unit_id = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_column='parent_admin_unit_id',
        help_text='Parent administrative unit (for hierarchical structure)'
    )
    jurisdiction_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Full path from root to this unit (e.g., "National > Oromia > East Shewa Zone")'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        db_index=True,
        help_text='Status of the administrative unit'
    )
    effective_from = models.DateField(
        null=True,
        blank=True,
        help_text='Date from which this unit is effective'
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text='Date until which this unit is effective (null = indefinite)'
    )
    created_by = models.CharField(
        max_length=50,
        blank=True,
        help_text='User ID who created this unit'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when this unit was created'
    )
    updated_by = models.CharField(
        max_length=50,
        blank=True,
        help_text='User ID who last updated this unit'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when this unit was last updated'
    )
    
    class Meta:
        db_table = 'admin_units'
        ordering = ['admin_unit_type', 'admin_unit_name_en']
        indexes = [
            models.Index(fields=['admin_unit_type', 'status']),
            models.Index(fields=['parent_admin_unit_id', 'status']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Administrative Unit'
        verbose_name_plural = 'Administrative Units'
    
    def __str__(self):
        return f"{self.admin_unit_name_en} ({self.admin_unit_type})"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate admin_unit_id and jurisdiction_path if not provided."""
        # Auto-generate admin_unit_id from name if not provided
        if not self.admin_unit_id:
            # Create a simple ID from the name: type + first 3 letters of name (uppercase, no spaces)
            name_part = ''.join(word[:3].upper() for word in self.admin_unit_name_en.split()[:2])
            if len(name_part) < 3:
                name_part = self.admin_unit_name_en[:10].upper().replace(' ', '')
            type_prefix = self.admin_unit_type[:3].upper()
            base_id = f"{type_prefix}-{name_part}"
            
            # Make it unique by appending number if needed
            counter = 1
            admin_unit_id = base_id
            while AdminUnit.objects.filter(admin_unit_id=admin_unit_id).exists():
                admin_unit_id = f"{base_id}-{counter}"
                counter += 1
            self.admin_unit_id = admin_unit_id
        
        # Auto-generate jurisdiction_path if not provided
        if not self.jurisdiction_path:
            self.jurisdiction_path = self._generate_jurisdiction_path()
        super().save(*args, **kwargs)
    
    def _generate_jurisdiction_path(self):
        """Generate jurisdiction path from parent hierarchy."""
        path_parts = [self.admin_unit_name_en]
        parent = self.parent_admin_unit_id
        while parent:
            path_parts.insert(0, parent.admin_unit_name_en)
            parent = parent.parent_admin_unit_id
        return ' > '.join(path_parts)
    
    def get_children(self, unit_type=None, status='Active'):
        """Get child administrative units."""
        queryset = self.children.filter(status=status)
        if unit_type:
            queryset = queryset.filter(admin_unit_type=unit_type)
        return queryset
    
    def get_all_descendants(self):
        """Get all descendant units recursively."""
        descendants = []
        children = self.children.all()
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


class Institution(models.Model):
    """Institution model for government and partner institutions."""
    
    INSTITUTION_TYPES = [
        ('Government', 'Government'),
        ('Partner', 'Partner'),
        ('Private', 'Private'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]
    
    institution_id = models.CharField(
        max_length=50,
        unique=True,
        primary_key=True,
        help_text='Unique identifier for the institution'
    )
    institution_type = models.CharField(
        max_length=20,
        choices=INSTITUTION_TYPES,
        db_index=True,
        help_text='Type of institution'
    )
    institution_name_en = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Institution name in English'
    )
    institution_name_am = models.CharField(
        max_length=255,
        blank=True,
        help_text='Institution name in Amharic'
    )
    institution_short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text='Short name or acronym'
    )
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Official registration number'
    )
    contact_person_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Primary contact person name'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    contact_email = models.EmailField(
        blank=True,
        help_text='Contact email address'
    )
    address_text = models.TextField(
        blank=True,
        help_text='Physical address'
    )
    region_id = models.ForeignKey(
        AdminUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='institutions',
        db_column='region_id',
        limit_choices_to={'admin_unit_type': 'Region'},
        help_text='Primary region for this institution'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        db_index=True,
        help_text='Status of the institution'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes or description'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'institutions'
        ordering = ['institution_name_en']
        indexes = [
            models.Index(fields=['institution_type', 'status']),
            models.Index(fields=['region_id', 'status']),
        ]
    
    def __str__(self):
        return f"{self.institution_name_en} ({self.institution_type})"
