"""
Center models for VIMS Backend.
"""
from django.db import models


class Center(models.Model):
    """
    Inspection Center model.
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('suspended', 'Suspended'),
    ]
    
    center_id = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    
    # Location
    region = models.CharField(max_length=100, db_index=True)
    zone = models.CharField(max_length=100, blank=True)
    subcity = models.CharField(max_length=100, blank=True)
    woreda = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    fax = models.CharField(max_length=20, blank=True)
    
    # Business Registration
    tin = models.CharField(max_length=50, blank=True, help_text='Tax Identification Number')
    vat = models.CharField(max_length=50, blank=True, help_text='VAT Number')
    principal_registration_no = models.CharField(max_length=100, blank=True, help_text='Principal Registration Number')
    business_license_no = models.CharField(max_length=100, blank=True, help_text='Business License Number')
    business_license_date_of_issuance = models.DateField(null=True, blank=True, help_text='Business License Date of Issuance')
    place_of_issue = models.CharField(max_length=255, blank=True, help_text='Place of Issue')
    date_of_issue = models.DateField(null=True, blank=True, help_text='Date of Issue')
    
    # Owner/Company Information
    owner_company_name = models.CharField(max_length=255, blank=True, help_text='Owner/Company Name')
    nationality = models.CharField(max_length=100, blank=True, help_text='Nationality')
    trade_name = models.CharField(max_length=255, blank=True, help_text='Trade Name')
    general_manager_name = models.CharField(max_length=255, blank=True, help_text='General Manager Name')
    
    # Additional Location Details
    kebele = models.CharField(max_length=100, blank=True, help_text='Kebele')
    house_no = models.CharField(max_length=50, blank=True, help_text='House Number')
    
    # Business Details
    field_of_business = models.CharField(max_length=255, blank=True, help_text='Field of Business')
    capital_in_etb = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text='Capital in ETB')
    
    # Additional Information
    telebirr_number = models.CharField(max_length=50, blank=True, help_text='TeleBirr Number')
    camera_configuration = models.TextField(blank=True, help_text='Camera Configuration')
    commercial_registration_procedure = models.TextField(blank=True, help_text='Commercial Registration Procedure')
    
    # Documents
    business_license_document = models.FileField(upload_to='centers/documents/business_license/', blank=True, null=True, help_text='Business License Document')
    registration_certificate_document = models.FileField(upload_to='centers/documents/registration_certificate/', blank=True, null=True, help_text='Registration Certificate Document')
    tax_certificate_document = models.FileField(upload_to='centers/documents/tax_certificate/', blank=True, null=True, help_text='Tax Certificate Document')
    other_documents = models.JSONField(default=list, blank=True, help_text='List of other document file paths/URLs')
    
    # Geofence
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    geofence_radius_meters = models.IntegerField(default=500, help_text='Geofence radius in meters')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    attention_score = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Inspection Metrics
    total_inspections = models.IntegerField(default=0)
    last_inspection_date = models.DateTimeField(null=True, blank=True)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Pass rate percentage')
    average_cycle_time_minutes = models.IntegerField(default=0, help_text='Average inspection cycle time')
    
    # Metadata
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'centers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['region', 'status']),
            models.Index(fields=['-attention_score']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# Manager for scope-based filtering
class CenterManager(models.Manager):
    """Manager for filtering centers by user scope."""
    
    def filter_by_scope(self, user_scope):
        """Filter centers based on user scope."""
        queryset = self.get_queryset()
        
        if user_scope['type'] == 'National':
            return queryset
        
        if user_scope['type'] == 'Regional':
            # Filter by region IDs (assuming scope_ids contain region names)
            return queryset.filter(region__in=user_scope['ids'])
        
        if user_scope['type'] == 'Zone':
            # Filter by zone IDs
            return queryset.filter(zone__in=user_scope['ids'])
        
        if user_scope['type'] == 'Woreda':
            # Filter by woreda IDs
            return queryset.filter(woreda__in=user_scope['ids'])
        
        if user_scope['type'] == 'Center':
            # Filter by specific center IDs
            return queryset.filter(center_id__in=user_scope['ids'])
        
        return queryset.none()


# Add the custom manager
Center.add_to_class('scoped_objects', CenterManager())
