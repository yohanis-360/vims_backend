"""
Inspection models for VIMS Backend.
Handles vehicle inspections with machine tests, visual checklists, and evidence.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Inspection(models.Model):
    """
    Main inspection record for a vehicle.
    """
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('pending_machine', 'Pending Machine Tests'),
        ('pending_payment', 'Pending Payment'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    VEHICLE_CATEGORIES = [
        ('LIGHT', 'Light Vehicle'),
        ('HEAVY', 'Heavy Vehicle'),
        ('MOTOR', 'Motor / 3-Wheel'),
    ]
    
    FUEL_TYPES = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Hybrid', 'Hybrid'),
    ]
    
    # Inspection ID
    inspection_id = models.CharField(max_length=50, unique=True, db_index=True, primary_key=True)
    
    # Vehicle Information
    plate_number = models.CharField(
        max_length=20,
        db_index=True
    )
    chassis_number = models.CharField(max_length=50, db_index=True)
    engine_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=50)
    vehicle_category = models.CharField(max_length=10, choices=VEHICLE_CATEGORIES, db_index=True)
    brand_model = models.CharField(max_length=100)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    kilometer_reading = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    licensed_capacity = models.IntegerField(validators=[MinValueValidator(1)])
    title_certificate = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=255)
    
    # Inspection Center & Inspector
    center = models.ForeignKey(
        'centers.Center',
        on_delete=models.PROTECT,
        related_name='inspections',
        db_index=True
    )
    inspector = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='inspections_conducted',
        db_index=True
    )
    
    # Status & Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', db_index=True)
    overall_result = models.CharField(max_length=10, blank=True)  # PASS/FAIL
    
    # Visual Inspection Results
    visual_points_earned = models.IntegerField(default=0)
    visual_points_total = models.IntegerField(default=0)
    visual_pass = models.BooleanField(null=True)
    
    # Machine Test Results
    machine_test_pass = models.BooleanField(null=True)
    
    # Payment
    payment_status = models.CharField(max_length=20, default='unpaid', db_index=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_transaction_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=20, blank=True)  # cash, card, mobile
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Sync Status (for offline inspector clients)
    sync_status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('synced', 'Synced'), ('failed', 'Failed')],
        default='pending',
        db_index=True
    )
    sync_error = models.TextField(blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    
    # Form Metadata
    form_id = models.CharField(max_length=50)  # LV-FORM-2025 or HV-FORM-2025
    test_start_time = models.DateTimeField()
    test_end_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inspections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['center', 'created_at']),
            models.Index(fields=['inspector', 'status', 'created_at']),
            models.Index(fields=['plate_number', 'created_at']),
            models.Index(fields=['status', 'overall_result']),
        ]
    
    def __str__(self):
        return f"{self.inspection_id} - {self.plate_number}"
    
    def calculate_overall_result(self):
        """Calculate overall pass/fail based on machine + visual tests."""
        if self.machine_test_pass and self.visual_pass:
            self.overall_result = 'PASS'
        else:
            self.overall_result = 'FAIL'
        self.save(update_fields=['overall_result'])


class MachineTest(models.Model):
    """
    Machine test results - READ ONLY after creation.
    Data comes directly from machine interfaces.
    """
    
    TEST_TYPES = [
        ('alignment', 'Alignment'),
        ('suspension', 'Suspension'),
        ('service_brake', 'Service Brake'),
        ('parking_brake', 'Parking Brake'),
        ('gas_analyzer', 'Gas Analyzer'),
        ('smoke_meter', 'Smoke Meter'),
        ('headlight', 'Headlight Test'),
    ]
    
    RESULTS = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('NA', 'Not Applicable'),
    ]
    
    machine_test_id = models.CharField(max_length=50, unique=True, primary_key=True)
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='machine_tests'
    )
    
    # Test Identification
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, db_index=True)
    test_name = models.CharField(max_length=100)
    
    # Test Data (JSON for flexibility)
    test_data = models.JSONField(help_text='Raw machine data')
    
    # Results
    result = models.CharField(max_length=10, choices=RESULTS)
    pass_status = models.BooleanField()
    
    # Metadata
    data_source = models.CharField(max_length=50, default='Machine_Interface')
    machine_serial = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # READ-ONLY flag
    is_locked = models.BooleanField(default=True, help_text='Machine data cannot be edited')
    
    class Meta:
        db_table = 'machine_tests'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['inspection', 'test_type']),
        ]
    
    def __str__(self):
        return f"{self.inspection.inspection_id} - {self.test_name}"
    
    def save(self, *args, **kwargs):
        """Override save to prevent editing locked records."""
        if self.pk and self.is_locked:
            # Check if this is an update (not creation)
            existing = MachineTest.objects.filter(pk=self.pk).first()
            if existing:
                raise ValueError("Machine test data is locked and cannot be modified.")
        super().save(*args, **kwargs)


class AlignmentTest(models.Model):
    """Specific model for Alignment & Suspension test."""
    
    machine_test = models.OneToOneField(
        MachineTest,
        on_delete=models.CASCADE,
        related_name='alignment_details'
    )
    
    # Alignment
    alignment_deviation = models.DecimalField(max_digits=5, decimal_places=2)  # m/km
    alignment_pass = models.BooleanField()
    
    # Suspension
    suspension_left = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # %
    suspension_right = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # %
    suspension_diff = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # %
    suspension_pass = models.BooleanField(null=True, blank=True)
    
    class Meta:
        db_table = 'alignment_tests'


class BrakeTest(models.Model):
    """Brake test results (Service and Parking)."""
    
    BRAKE_TYPES = [
        ('service', 'Service Brake'),
        ('parking', 'Parking Brake'),
    ]
    
    machine_test = models.OneToOneField(
        MachineTest,
        on_delete=models.CASCADE,
        related_name='brake_details'
    )
    
    brake_type = models.CharField(max_length=10, choices=BRAKE_TYPES)
    
    # Front axle
    front_left_force = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True)  # N
    front_right_force = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True)  # N
    front_balance = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)  # %
    
    # Rear axle
    rear_left_force = models.DecimalField(max_digits=7, decimal_places=1)  # N
    rear_right_force = models.DecimalField(max_digits=7, decimal_places=1)  # N
    rear_balance = models.DecimalField(max_digits=5, decimal_places=1)  # %
    
    # Total
    total_force = models.DecimalField(max_digits=7, decimal_places=1)  # N
    
    # Pass/Fail
    force_pass = models.BooleanField()
    balance_pass = models.BooleanField()
    overall_pass = models.BooleanField()
    
    class Meta:
        db_table = 'brake_tests'


class EmissionsTest(models.Model):
    """Emissions test (Gas Analyzer for Petrol or Smoke Meter for Diesel)."""
    
    EMISSION_TYPES = [
        ('gas_analyzer', 'Gas Analyzer (Petrol)'),
        ('smoke_meter', 'Smoke Meter (Diesel)'),
    ]
    
    machine_test = models.OneToOneField(
        MachineTest,
        on_delete=models.CASCADE,
        related_name='emissions_details'
    )
    
    emission_type = models.CharField(max_length=20, choices=EMISSION_TYPES)
    
    # Gas Analyzer (Petrol)
    hc = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True)  # ppm
    co = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # %
    co2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # %
    o2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # %
    lambda_value = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    
    # Smoke Meter (Diesel)
    opacity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # m⁻¹
    
    # Pass/Fail
    overall_pass = models.BooleanField()
    
    class Meta:
        db_table = 'emissions_tests'


class HeadlightTest(models.Model):
    """Headlight intensity and aim test."""
    
    machine_test = models.OneToOneField(
        MachineTest,
        on_delete=models.CASCADE,
        related_name='headlight_details'
    )
    
    # Left headlight
    left_intensity = models.DecimalField(max_digits=8, decimal_places=0)  # cd
    left_aim_horizontal = models.DecimalField(max_digits=6, decimal_places=2)  # mrad
    left_aim_vertical = models.DecimalField(max_digits=6, decimal_places=2)  # mrad
    left_pass = models.BooleanField()
    
    # Right headlight
    right_intensity = models.DecimalField(max_digits=8, decimal_places=0)  # cd
    right_aim_horizontal = models.DecimalField(max_digits=6, decimal_places=2)  # mrad
    right_aim_vertical = models.DecimalField(max_digits=6, decimal_places=2)  # mrad
    right_pass = models.BooleanField()
    
    # Overall
    overall_pass = models.BooleanField()
    
    class Meta:
        db_table = 'headlight_tests'


class VisualChecklistItem(models.Model):
    """
    30-point visual inspection checklist results.
    """
    
    STATUS_CHOICES = [
        ('PASS', 'Correct'),
        ('FAIL', 'Not Correct'),
        ('NA', 'Not Applicable'),
    ]
    
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='visual_items'
    )
    
    # Item identification
    item_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    item_name_en = models.CharField(max_length=100)
    item_name_am = models.CharField(max_length=100)
    zone_id = models.CharField(max_length=20)
    zone_name_en = models.CharField(max_length=100)
    
    # Points
    points_possible = models.IntegerField()
    points_earned = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    # Defect info (if failed)
    defect_type = models.CharField(max_length=50, blank=True)  # broken, missing, etc.
    
    # Flags
    is_critical = models.BooleanField(default=False)
    is_mandatory = models.BooleanField(default=False)
    
    # Timestamp
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visual_checklist_items'
        ordering = ['item_number']
        unique_together = ['inspection', 'item_number']


class InspectionPhoto(models.Model):
    """
    Evidence photos with GPS coordinates and timestamps.
    """
    
    PHOTO_PURPOSES = [
        ('registration', 'Registration Photo'),
        ('visual_inspection', 'Visual Inspection Evidence'),
        ('machine_test', 'Machine Test Evidence'),
        ('defect', 'Defect Documentation'),
    ]
    
    photo_id = models.CharField(max_length=50, unique=True, primary_key=True)
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    
    # Photo details
    purpose = models.CharField(max_length=30, choices=PHOTO_PURPOSES)
    photo_url = models.TextField()  # S3 URL, file path, or base64 data URL (no length limit for base64)
    
    # GPS coordinates (increased max_digits to support full GPS precision)
    latitude = models.DecimalField(max_digits=30, decimal_places=9, null=True, blank=True)
    longitude = models.DecimalField(max_digits=30, decimal_places=9, null=True, blank=True)
    gps_accuracy = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField()
    file_size = models.IntegerField(null=True, blank=True)  # bytes
    
    # Linked visual item (if applicable)
    visual_item = models.ForeignKey(
        VisualChecklistItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos'
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inspection_photos'
        ordering = ['timestamp']


class InspectionVideo(models.Model):
    """Video evidence for inspections."""
    
    video_id = models.CharField(max_length=50, unique=True, primary_key=True)
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    
    video_url = models.URLField(max_length=500)
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    timestamp = models.DateTimeField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inspection_videos'


# Manager for scope-based filtering
class InspectionManager(models.Manager):
    """Manager for filtering inspections by user scope."""
    
    def filter_by_scope(self, user_scope):
        """Filter inspections based on user scope."""
        queryset = self.get_queryset()
        
        if user_scope['type'] == 'National':
            return queryset
        
        if user_scope['type'] == 'Regional':
            # Filter by centers in the region
            return queryset.filter(center__region__in=user_scope['ids'])
        
        if user_scope['type'] == 'Center':
            # Filter by specific centers
            return queryset.filter(center__center_id__in=user_scope['ids'])
        
        return queryset.none()


# Add the custom manager to Inspection model
Inspection.add_to_class('scoped_objects', InspectionManager())
