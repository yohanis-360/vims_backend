import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import Role

def setup_roles():
    """Create roles: National Admin, Regional Admin, and Inspector"""
    print("Setting up roles...")

    # National Admin Role
    national_admin_role, created = Role.objects.get_or_create(
        role_id='NATIONAL_ADMIN',
        defaults={
            'role_name_en': 'National Admin',
            'role_name_am': 'የአገር አስተዳዳሪ',
            'role_category': 'Admin',
            'default_scope_type': 'National',
            'is_sensitive_role': True,
            'two_person_approval_required': False,
            'permissions': ['*'],  # Full access
            'enabled': True,
            'version': '1.0'
        }
    )
    if created:
        print(f"✓ National Admin role created: {national_admin_role.role_id}")
    else:
        print(f"✓ National Admin role exists: {national_admin_role.role_id}")

    # Regional Admin Role
    regional_admin_role, created = Role.objects.get_or_create(
        role_id='REGIONAL_ADMIN',
        defaults={
            'role_name_en': 'Regional Admin',
            'role_name_am': 'ክልላዊ አስተዳዳሪ',
            'role_category': 'Admin',
            'default_scope_type': 'Region',
            'is_sensitive_role': False,
            'two_person_approval_required': False,
            'permissions': [
                'CENTER.CREATE',
                'CENTER.UPDATE',
                'CENTER.VIEW',
                'USER.CREATE',
                'USER.UPDATE',
                'USER.VIEW',
                'INSPECTION.VIEW',
                'INSPECTION.UPDATE',
                'REPORT.VIEW',
                'REPORT.GENERATE'
            ],
            'enabled': True,
            'version': '1.0'
        }
    )
    if created:
        print(f"✓ Regional Admin role created: {regional_admin_role.role_id}")
    else:
        print(f"✓ Regional Admin role exists: {regional_admin_role.role_id}")

    # Inspector Role
    inspector_role, created = Role.objects.get_or_create(
        role_id='INSPECTOR',
        defaults={
            'role_name_en': 'Inspector',
            'role_name_am': 'መመርመሪያ',
            'role_category': 'Operations',
            'default_scope_type': 'Center',
            'is_sensitive_role': False,
            'two_person_approval_required': False,
            'permissions': [
                'INSPECTION.CREATE',
                'INSPECTION.VIEW',
                'INSPECTION.UPDATE',
                'CENTER.VIEW'
            ],
            'enabled': True,
            'version': '1.0'
        }
    )
    if created:
        print(f"✓ Inspector role created: {inspector_role.role_id}")
    else:
        print(f"✓ Inspector role exists: {inspector_role.role_id}")

    # Also create ADMIN role for backward compatibility (maps to National Admin)
    admin_role, created = Role.objects.get_or_create(
        role_id='ADMIN',
        defaults={
            'role_name_en': 'Admin',
            'role_name_am': 'አስተዳዳሪ',
            'role_category': 'Admin',
            'default_scope_type': 'National',
            'is_sensitive_role': True,
            'two_person_approval_required': False,
            'permissions': ['*'],  # Full access
            'enabled': True,
            'version': '1.0'
        }
    )
    if created:
        print(f"✓ Admin role created (backward compatibility): {admin_role.role_id}")
    else:
        print(f"✓ Admin role exists: {admin_role.role_id}")

    # Clear roles cache to ensure fresh data
    from django.core.cache import cache
    cache.delete('roles_list')
    print("✓ Cleared roles cache")

    print("\n" + "="*60)
    print("ROLES SETUP COMPLETE:")
    print("="*60)
    print(f"1. National Admin (NATIONAL_ADMIN) - National scope, full access")
    print(f"2. Regional Admin (REGIONAL_ADMIN) - Regional scope")
    print(f"3. Inspector (INSPECTOR) - Center scope")
    print(f"4. Admin (ADMIN) - National scope (backward compatibility)")
    print("="*60)
    print("\n✓ Roles are ready to use!")
    print("✓ Cache cleared - refresh your frontend to see all roles\n")

if __name__ == "__main__":
    setup_roles()

