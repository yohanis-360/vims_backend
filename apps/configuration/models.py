"""
Configuration models for VIMS Backend.
Allows admins to configure inspection checklists, test standards, and fee structures.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class VisualChecklistConfig(models.Model):
    """
    Admin-configurable visual inspection checklist items.
    Replaces hardcoded checklist in frontend.
    """
    
    VEHICLE_CATEGORY_CHOICES = [
        ('LIGHT', 'Light Vehicle'),
        ('HEAVY', 'Heavy Vehicle'),
        ('MOTOR', 'Motor / 3-Wheel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    # Configuration metadata
    config_id = models.CharField(max_length=50, unique=True, primary_key=True)
    vehicle_category = models.CharField(max_length=10, choices=VEHICLE_CATEGORY_CHOICES, db_index=True)
    zone_id = models.CharField(max_length=20, db_index=True)
    zone_name_en = models.CharField(max_length=100)
    zone_name_am = models.CharField(max_length=100, blank=True)
    
    # Item details
    item_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        db_index=True
    )
    item_name_en = models.CharField(max_length=200)
    item_name_am = models.CharField(max_length=200, blank=True)
    
    # Points and requirements
    points_possible = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_critical = models.BooleanField(default=False, help_text='Critical items cause automatic failure if failed')
    is_mandatory = models.BooleanField(default=True, help_text='Mandatory items must be checked')
    
    # Display order
    display_order = models.IntegerField(default=0, db_index=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_checklist_configs'
    )
    
    class Meta:
        db_table = 'visual_checklist_configs'
        ordering = ['vehicle_category', 'zone_id', 'display_order', 'item_number']
        unique_together = ['vehicle_category', 'zone_id', 'item_number']
        indexes = [
            models.Index(fields=['vehicle_category', 'status']),
            models.Index(fields=['zone_id', 'display_order']),
        ]
    
    def __str__(self):
        return f"{self.vehicle_category} - {self.zone_name_en} - Item {self.item_number}: {self.item_name_en}"


class TestStandard(models.Model):
    """
    Test standards configuration for machine tests.
    """
    
    VEHICLE_CATEGORY_CHOICES = [
        ('LIGHT', 'Light Vehicle'),
        ('HEAVY', 'Heavy Vehicle'),
        ('MOTOR', 'Motor / 3-Wheel'),
    ]
    
    TEST_TYPE_CHOICES = [
        ('emissions', 'Emissions Test'),
        ('headlight', 'Headlight Test'),
        ('brake', 'Brake Test'),
        ('suspension', 'Suspension Test'),
    ]
    
    standard_id = models.CharField(max_length=50, unique=True, primary_key=True)
    vehicle_category = models.CharField(max_length=10, choices=VEHICLE_CATEGORY_CHOICES)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    
    # Standard values
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_standards'
        ordering = ['vehicle_category', 'test_type']
    
    def __str__(self):
        return f"{self.vehicle_category} - {self.test_type}"


class FeeStructure(models.Model):
    """
    Fee structure configuration.
    """
    
    fee_id = models.CharField(max_length=50, unique=True, primary_key=True)
    vehicle_category = models.CharField(max_length=10)
    vehicle_type = models.CharField(max_length=50, blank=True)
    
    # Fee amounts
    inspection_fee = models.DecimalField(max_digits=10, decimal_places=2)
    retest_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fee_structures'
        ordering = ['vehicle_category', 'vehicle_type']
    
    def __str__(self):
        return f"{self.vehicle_category} - {self.vehicle_type}: {self.inspection_fee} ETB"
