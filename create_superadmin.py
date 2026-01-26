"""
Script to create a new super admin user
Usage:
    python create_superadmin.py
    python create_superadmin.py --username admin --password secret123
    python create_superadmin.py --username admin --password secret123 --email admin@vims.et
"""
import os
import sys
import django
import argparse
from uuid import uuid4

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User, Role, RoleAssignment
from django.utils import timezone

def create_superadmin(username, password, full_name=None, email=None, phone=None):
    """Create a new super admin user."""
    print("\n" + "=" * 80)
    print("CREATE NEW SUPER ADMIN USER")
    print("=" * 80)
    
    # Check if username already exists
    existing_user = User.objects.filter(username=username).first()
    if existing_user:
        print(f"\n⚠ Username '{username}' already exists!")
        print(f"  User ID: {existing_user.user_id}")
        print(f"  Full Name: {existing_user.full_name}")
        print(f"  Email: {existing_user.email}")
        print(f"  Status: {existing_user.status}")
        
        # Update password and ensure superuser status
        existing_user.set_password(password)
        existing_user.password_changed_at = timezone.now()
        existing_user.is_active = True
        existing_user.is_staff = True
        existing_user.is_superuser = True
        existing_user.status = 'Active'
        
        if full_name:
            existing_user.full_name = full_name
        if email:
            existing_user.email = email
        if phone:
            existing_user.phone = phone
        
        existing_user.save()
        
        # Ensure NATIONAL_ADMIN role is assigned
        national_admin_role = Role.objects.filter(role_id='NATIONAL_ADMIN').first()
        if not national_admin_role:
            national_admin_role = Role.objects.filter(role_id='ADMIN').first()
        
        if national_admin_role:
            role_assignment_id = f"RA-{existing_user.user_id}-{national_admin_role.role_id}"
            role_assignment, created = RoleAssignment.objects.get_or_create(
                role_assignment_id=role_assignment_id,
                defaults={
                    'user': existing_user,
                    'role': national_admin_role,
                    'scope_type': 'National',
                    'scope_ids': [],
                    'status': 'Active',
                    'approval_status': 'Approved'
                }
            )
            if created:
                print(f"✓ Assigned {national_admin_role.role_id} role")
            else:
                print(f"✓ User already has {national_admin_role.role_id} role")
        
        print("\n✓ Password and user details updated successfully!")
        print(f"\n✓ Credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  User ID: {existing_user.user_id}")
        print(f"  Full Name: {existing_user.full_name}")
        print(f"  Email: {existing_user.email}")
        print(f"  Phone: {existing_user.phone}")
        print(f"  Scope: National (full access)")
        print("\n" + "=" * 80 + "\n")
        return existing_user
    
    # Create new user
    print(f"\n[1] Creating super admin user '{username}'...")
    
    user_id = f"USR-{str(uuid4())[:8].upper()}"
    user = User.objects.create_user(
        username=username,
        password=password,
        user_id=user_id,
        full_name=full_name or f"Super Administrator ({username})",
        email=email or f"{username}@vims.et",
        phone=phone or "+251911000000",
        status='Active',
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    print(f"✓ User created: {user_id}")
    
    # Assign NATIONAL_ADMIN role
    national_admin_role = Role.objects.filter(role_id='NATIONAL_ADMIN').first()
    if not national_admin_role:
        # Fallback to ADMIN role
        national_admin_role = Role.objects.filter(role_id='ADMIN').first()
        if not national_admin_role:
            print("⚠ Warning: NATIONAL_ADMIN or ADMIN role not found!")
            print("  User created but role not assigned. Please assign role manually.")
            print("  Run: python setup_roles.py")
    else:
        role_assignment_id = f"RA-{user.user_id}-{national_admin_role.role_id}"
        role_assignment, created = RoleAssignment.objects.get_or_create(
            role_assignment_id=role_assignment_id,
            defaults={
                'user': user,
                'role': national_admin_role,
                'scope_type': 'National',
                'scope_ids': [],
                'status': 'Active',
                'approval_status': 'Approved'
            }
        )
        if created:
            print(f"✓ Assigned {national_admin_role.role_id} role with National scope")
        else:
            print(f"✓ Role assignment already exists")
    
    print("\n✓ Super admin user created successfully!")
    print(f"\n✓ Credentials:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  User ID: {user_id}")
    print(f"  Full Name: {user.full_name}")
    print(f"  Email: {user.email}")
    print(f"  Phone: {user.phone}")
    print(f"  Scope: National (full access)")
    print("\n" + "=" * 80 + "\n")
    return user

def main():
    parser = argparse.ArgumentParser(description='Create a new super admin user')
    parser.add_argument('--username', '-u', 
                       default=os.getenv('SUPER_ADMIN_USERNAME', 'admin'),
                       help='Username for super admin (default: admin)')
    parser.add_argument('--password', '-p',
                       default=os.getenv('SUPER_ADMIN_PASSWORD', 'admin123'),
                       help='Password for super admin (default: admin123)')
    parser.add_argument('--full-name', '-n',
                       default=None,
                       help='Full name for super admin')
    parser.add_argument('--email', '-e',
                       default=None,
                       help='Email for super admin')
    parser.add_argument('--phone', '-t',
                       default=None,
                       help='Phone number for super admin')
    
    args = parser.parse_args()
    
    create_superadmin(
        username=args.username,
        password=args.password,
        full_name=args.full_name,
        email=args.email,
        phone=args.phone
    )

if __name__ == '__main__':
    main()

