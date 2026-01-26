import os
import django
from uuid import uuid4

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User, Role, RoleAssignment

def create_super_admin():
    print("Setting up Super Admin user...")

    # Use NATIONAL_ADMIN role (or ADMIN for backward compatibility)
    national_admin_role = Role.objects.filter(role_id='NATIONAL_ADMIN').first()
    if not national_admin_role:
        # Fallback to ADMIN role
        national_admin_role, created = Role.objects.get_or_create(
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
    super_admin_role = national_admin_role  # Use national admin role for super admin
    if national_admin_role.role_id == 'NATIONAL_ADMIN':
        print(f"✓ Using National Admin role: {national_admin_role.role_id}")
    else:
        print(f"✓ Using Admin role: {national_admin_role.role_id}")

    # Check if super admin user already exists
    admin_username = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
    admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
    
    admin_user = User.objects.filter(username=admin_username).first()
    
    if admin_user:
        print(f"✓ Super Admin user exists: {admin_username} (ID: {admin_user.user_id})")
        # Update password in case it was changed
        admin_user.set_password(admin_password)
        admin_user.save()
        print(f"✓ Password updated for: {admin_username}")
    else:
        # Create super admin user
        print(f"Creating Super Admin user '{admin_username}'...")
        user_id = f"USR-{str(uuid4())[:8].upper()}"
        admin_user = User.objects.create_user(
            username=admin_username,
            password=admin_password,
            user_id=user_id,
            full_name='System Super Administrator',
            email='superadmin@vims.et',
            phone='+251911000000',
            status='Active',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        print(f"✓ Super Admin user created: {admin_username} (ID: {admin_user.user_id})")

    # Assign National Admin role with National scope
    role_assignment_id = f"RA-{admin_user.user_id}-{super_admin_role.role_id}"
    role_assignment, created = RoleAssignment.objects.get_or_create(
        role_assignment_id=role_assignment_id,
        defaults={
            'user': admin_user,
            'role': super_admin_role,
            'scope_type': 'National',
            'scope_ids': [],  # National scope means all
            'status': 'Active',
            'approval_status': 'Approved'
        }
    )
    if created:
        print(f"✓ Admin role assigned with National scope")
    else:
        print(f"✓ Admin role assignment exists")

    print("\n" + "="*60)
    print("SUPER ADMIN CREDENTIALS:")
    print("="*60)
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print(f"User ID:  {admin_user.user_id}")
    print(f"Scope:    National (full access)")
    print("="*60)
    print("\n✓ Super Admin setup complete!")
    print(f"You can now login to the admin portal with these credentials.\n")

if __name__ == "__main__":
    create_super_admin()

