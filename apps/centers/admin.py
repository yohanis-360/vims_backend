"""
Django admin configuration for Centers app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings
from .models import Center


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    """Admin interface for Center model."""
    list_display = [
        'center_id',
        'name',
        'code',
        'region',
        'zone',
        'status',
        'is_active',
        'has_documents',
        'created_at',
    ]
    list_filter = ['status', 'is_active', 'region', 'created_at']
    search_fields = ['center_id', 'name', 'code', 'region', 'zone', 'woreda', 'email', 'phone']
    readonly_fields = [
        'center_id', 'total_inspections', 'last_inspection_date', 'pass_rate',
        'average_cycle_time_minutes', 'attention_score', 'last_seen',
        'created_at', 'updated_at', 'document_links'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('center_id', 'name', 'code', 'status', 'is_active')
        }),
        ('Location', {
            'fields': ('region', 'zone', 'subcity', 'woreda', 'kebele', 'house_no', 'address')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'fax')
        }),
        ('Business Registration', {
            'fields': (
                'tin', 'vat', 'principal_registration_no', 'business_license_no',
                'business_license_date_of_issuance', 'place_of_issue', 'date_of_issue'
            )
        }),
        ('Owner/Company Information', {
            'fields': ('owner_company_name', 'nationality', 'trade_name', 'general_manager_name')
        }),
        ('Business Details', {
            'fields': ('field_of_business', 'capital_in_etb', 'telebirr_number')
        }),
        ('Additional Information', {
            'fields': ('camera_configuration', 'commercial_registration_procedure'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': (
                'business_license_document',
                'registration_certificate_document',
                'tax_certificate_document',
                'other_documents',
                'document_links'
            )
        }),
        ('Geofence', {
            'fields': ('latitude', 'longitude', 'geofence_radius_meters')
        }),
        ('Metrics', {
            'fields': (
                'total_inspections', 'last_inspection_date', 'pass_rate',
                'average_cycle_time_minutes', 'attention_score', 'last_seen'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_documents(self, obj):
        """Check if center has any documents."""
        has_docs = (
            bool(obj.business_license_document) or
            bool(obj.registration_certificate_document) or
            bool(obj.tax_certificate_document) or
            (obj.other_documents and len(obj.other_documents) > 0)
        )
        if has_docs:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: gray;">No</span>')
    has_documents.short_description = 'Has Documents'
    has_documents.boolean = True
    
    def document_links(self, obj):
        """Display links to all documents."""
        if not obj:
            return '-'
        
        links = []
        
        if obj.business_license_document:
            url = obj.business_license_document.url if hasattr(obj.business_license_document, 'url') else str(obj.business_license_document)
            if not url.startswith('http'):
                url = f"{settings.MEDIA_URL}{url.lstrip('/')}"
            links.append(
                format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; margin: 2px 5px; padding: 4px 8px; background: #007cba; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">📄 Business License</a>',
                    url
                )
            )
        
        if obj.registration_certificate_document:
            url = obj.registration_certificate_document.url if hasattr(obj.registration_certificate_document, 'url') else str(obj.registration_certificate_document)
            if not url.startswith('http'):
                url = f"{settings.MEDIA_URL}{url.lstrip('/')}"
            links.append(
                format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; margin: 2px 5px; padding: 4px 8px; background: #28a745; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">📄 Registration Certificate</a>',
                    url
                )
            )
        
        if obj.tax_certificate_document:
            url = obj.tax_certificate_document.url if hasattr(obj.tax_certificate_document, 'url') else str(obj.tax_certificate_document)
            if not url.startswith('http'):
                url = f"{settings.MEDIA_URL}{url.lstrip('/')}"
            links.append(
                format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; margin: 2px 5px; padding: 4px 8px; background: #6f42c1; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">📄 Tax Certificate</a>',
                    url
                )
            )
        
        if obj.other_documents and isinstance(obj.other_documents, list) and len(obj.other_documents) > 0:
            for idx, doc in enumerate(obj.other_documents):
                if isinstance(doc, str):
                    doc_url = doc if doc.startswith('http') else f"{settings.MEDIA_URL}{doc.lstrip('/')}"
                    links.append(
                        format_html(
                            '<a href="{}" target="_blank" style="display: inline-block; margin: 2px 5px; padding: 4px 8px; background: #6c757d; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">📄 Other Doc {}</a>',
                            doc_url,
                            idx + 1
                        )
                    )
        
        if not links:
            return format_html('<span style="color: gray;">No documents uploaded</span>')
        
        return format_html(''.join(links))
    document_links.short_description = 'Document Links'

