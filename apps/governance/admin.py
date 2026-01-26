"""
Django admin configuration for Governance app.
"""
from django.contrib import admin
from django.contrib import messages
from django.db import OperationalError, ProgrammingError, connection
from django.http import HttpResponse
from .models import AdminUnit, Institution


def table_exists(table_name):
    """Check if a database table exists."""
    try:
        with connection.cursor() as cursor:
            # Use PostgreSQL-specific query
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                [table_name]
            )
            return cursor.fetchone()[0]
    except (OperationalError, ProgrammingError):
        return False
    except Exception:
        # If database connection fails or any other error, assume table doesn't exist
        return False


# Always register AdminUnit admin - handle missing table errors gracefully
@admin.register(AdminUnit)
class AdminUnitAdmin(admin.ModelAdmin):
    """Admin interface for AdminUnit model - Simplified for Ethiopian administrative structure."""
    list_display = [
        'admin_unit_name_en',
        'admin_unit_type',
        'parent_admin_unit_id',
        'status',
    ]
    list_filter = ['admin_unit_type', 'status']
    search_fields = ['admin_unit_name_en']
    readonly_fields = ['admin_unit_id', 'created_at', 'updated_at', 'jurisdiction_path']
    actions = ['create_sample_regions']
    
    # Simplified fieldsets - focus on essential fields
    fieldsets = (
        ('Basic Information', {
            'fields': ('admin_unit_name_en', 'admin_unit_type', 'parent_admin_unit_id', 'status'),
            'description': 'Enter the name in English. ID will be auto-generated. Select parent for hierarchy: Region > Zone > Woreda > Kebele'
        }),
        ('Additional Information (Optional)', {
            'fields': ('admin_unit_name_am', 'admin_unit_code'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('admin_unit_id', 'jurisdiction_path', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to make it simpler."""
        form = super().get_form(request, obj, **kwargs)
        # Make parent filter by type based on current selection
        if 'parent_admin_unit_id' in form.base_fields:
            # Filter parent based on hierarchy: Region has no parent, Zone's parent is Region, etc.
            form.base_fields['parent_admin_unit_id'].queryset = AdminUnit.objects.filter(status='Active')
        
        # Make admin_unit_id optional for new objects (will be auto-generated)
        if 'admin_unit_id' in form.base_fields and obj is None:
            form.base_fields['admin_unit_id'].required = False
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Override save to auto-generate admin_unit_id if not provided."""
        if not obj.admin_unit_id:
            # Generate ID from name
            name_part = ''.join(word[:3].upper() for word in obj.admin_unit_name_en.split()[:2])
            if len(name_part) < 3:
                name_part = obj.admin_unit_name_en[:10].upper().replace(' ', '').replace('-', '')
            type_prefix = obj.admin_unit_type[:3].upper()
            base_id = f"{type_prefix}-{name_part}"
            
            # Make it unique by appending number if needed
            counter = 1
            admin_unit_id = base_id
            while AdminUnit.objects.filter(admin_unit_id=admin_unit_id).exists():
                admin_unit_id = f"{base_id}-{counter}"
                counter += 1
            obj.admin_unit_id = admin_unit_id
        
        super().save_model(request, obj, form, change)
    
    def _table_exists(self):
        """Check if admin_units table exists."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                    ['admin_units']
                )
                return cursor.fetchone()[0]
        except:
            return False
    
    def get_queryset(self, request):
        """Override to handle missing table gracefully."""
        # Check if table exists first
        if not self._table_exists():
            messages.warning(
                request,
                'The admin_units table does not exist. Please run migrations: python manage.py migrate governance'
            )
            # Return a queryset that won't hit the database
            return AdminUnit.objects.none()
        
        try:
            return super().get_queryset(request)
        except (OperationalError, ProgrammingError) as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                messages.warning(
                    request,
                    'The admin_units table does not exist. Please run migrations: python manage.py migrate governance'
                )
                return AdminUnit.objects.none()
            raise
    
    def changelist_view(self, request, extra_context=None):
        """Override to handle missing table gracefully."""
        # Check if table exists BEFORE trying to access it
        if not self._table_exists():
            messages.error(
                request,
                'The admin_units table does not exist. Please run migrations: python manage.py migrate governance'
            )
            # Return a simple HTML response instead of trying to create ChangeList
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Table Not Found - {self.model._meta.verbose_name_plural}</title>
            </head>
            <body>
                <h1>Table Not Found</h1>
                <p>The admin_units table does not exist in the database.</p>
                <p><strong>To fix this, run:</strong></p>
                <pre>python manage.py migrate governance</pre>
                <p><a href="/admin/">← Back to Admin</a></p>
            </body>
            </html>
            """
            return HttpResponse(html, status=200)
        
        # Table exists, proceed normally
        try:
            return super().changelist_view(request, extra_context)
        except (OperationalError, ProgrammingError) as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                messages.error(
                    request,
                    'The admin_units table does not exist. Please run migrations: python manage.py migrate governance'
                )
                # Return simple HTML response
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Table Not Found - {self.model._meta.verbose_name_plural}</title>
                </head>
                <body>
                    <h1>Table Not Found</h1>
                    <p>The admin_units table does not exist in the database.</p>
                    <p><strong>To fix this, run:</strong></p>
                    <pre>python manage.py migrate governance</pre>
                    <p><a href="/admin/">← Back to Admin</a></p>
                </body>
                </html>
                """
                return HttpResponse(html, status=200)
            raise
            
    
    def _get_regions_data(self):
        """Get the list of sample regions to create - IDs will be auto-generated."""
        return [
            {
                'admin_unit_name_en': 'Addis Ababa',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Oromia',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Amhara',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Tigray',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Somali',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Afar',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Dire Dawa',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'SNNPR',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Gambela',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Harari',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
            {
                'admin_unit_name_en': 'Benishangul-Gumuz',
                'admin_unit_type': 'Region',
                'status': 'Active',
            },
        ]
    
    @admin.action(description='Create sample regions (Ethiopian regions)')
    def create_sample_regions(self, request, queryset):
        """
        Admin action to create sample Ethiopian regions.
        Works even if no objects are selected.
        """
        try:
            regions_data = self._get_regions_data()
            created_count = 0
            skipped_count = 0
            
            for region_data in regions_data:
                region_name = region_data['admin_unit_name_en']
                try:
                    # Check if region already exists by name
                    if not AdminUnit.objects.filter(
                        admin_unit_name_en=region_name,
                        admin_unit_type='Region'
                    ).exists():
                        # Create without admin_unit_id - it will be auto-generated
                        AdminUnit.objects.create(**region_data)
                        created_count += 1
                    else:
                        skipped_count += 1
                except (OperationalError, ProgrammingError) as e:
                    error_str = str(e).lower()
                    if 'does not exist' in error_str or 'relation' in error_str:
                        self.message_user(
                            request,
                            'Cannot create regions: admin_units table does not exist. Please run migrations: python manage.py migrate governance',
                            messages.ERROR
                        )
                        return
                    raise
            
            if created_count > 0:
                self.message_user(
                    request,
                    f'Successfully created {created_count} regions. {skipped_count} regions already existed.',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f'All {skipped_count} regions already exist. No new regions were created.',
                    messages.INFO
                )
        except (OperationalError, ProgrammingError) as e:
            error_str = str(e).lower()
            if 'does not exist' in error_str or 'relation' in error_str:
                self.message_user(
                    request,
                    'Cannot create regions: admin_units table does not exist. Please run migrations: python manage.py migrate governance',
                    messages.ERROR
                )
            else:
                self.message_user(
                    request,
                    f'Error creating regions: {str(e)}',
                    messages.ERROR
                )
        except Exception as e:
            self.message_user(
                request,
                f'Error creating regions: {str(e)}',
                messages.ERROR
            )


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """Admin interface for Institution model."""
    list_display = [
        'institution_id',
        'institution_name_en',
        'institution_type',
        'region_id',
        'status',
        'created_at',
    ]
    list_filter = ['institution_type', 'status', 'region_id', 'created_at']
    search_fields = ['institution_id', 'institution_name_en', 'institution_name_am', 'institution_short_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('institution_id', 'institution_type', 'institution_name_en', 'institution_name_am', 'institution_short_name')
        }),
        ('Registration', {
            'fields': ('registration_number',)
        }),
        ('Contact Information', {
            'fields': ('contact_person_name', 'contact_phone', 'contact_email', 'address_text')
        }),
        ('Location', {
            'fields': ('region_id',)
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


