"""
Interactive script to create a new super admin user
Uses Django ORM directly (requires database access)
Run with: python create_superadmin_interactive.py
"""
import os
import sys
import django
import getpass
from uuid import uuid4

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User, Role, RoleAssignment
from django.utils import timezone

def create_superadmin_interactive():
    """Create a new super admin user interactively."""
    print("\n" + "=" * 80)
    print("CREATE NEW SUPER ADMIN USER")
    print("=" * 80)
    
    # Get user input
    print("\n[1] Enter super admin details:")
    username = input("  Username: ").strip()
    if not username:
        print("✗ Username cannot be empty!")
        return
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        print(f"✗ Username '{username}' already exists!")
        overwrite = input("  Do you want to update this user's password? (y/n): ").strip().lower()
        if overwrite != 'y':
            return
        
        user = User.objects.get(username=username)
        print(f"\n✓ Found existing user: {user.user_id}")
        print(f"  Full Name: {user.full_name}")
        print(f"  Email: {user.email}")
        
        # Update password
        print("\n[2] Enter new password:")
        password = getpass.getpass("  Password: ")
        if not password:
            print("✗ Password cannot be empty!")
            return
        
        if len(password) < 8:
            print("⚠ Warning: Password is less than 8 characters. Continue? (y/n): ", end='')
            confirm = input().strip().lower()
            if confirm != 'y':
                print("✗ Password update cancelled.")
                return
        
        print("\n[3] Confirm password:")
        confirm_password = getpass.getpass("  Confirm: ")
        if password != confirm_password:
            print("✗ Passwords do not match!")
            return
        
        # Update user
        user.set_password(password)
        user.password_changed_at = timezone.now()
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.status = 'Active'
        user.save()
        
        # Ensure NATIONAL_ADMIN role is assigned
        national_admin_role = Role.objects.filter(role_id='NATIONAL_ADMIN').first()
        if not national_admin_role:
            national_admin_role = Role.objects.filter(role_id='ADMIN').first()
        
        if national_admin_role:
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
                print(f"✓ Assigned {national_admin_role.role_id} role")
            else:
                print(f"✓ User already has {national_admin_role.role_id} role")
        
        print("\n✓ Password updated successfully!")
        print(f"\n✓ Credentials:")
        print(f"  Username: {username}")
        print(f"  Password: [the password you just entered]")
        print(f"  User ID: {user.user_id}")
        print("\n" + "=" * 80 + "\n")
        return
    
    # Create new user
    full_name = input("  Full Name (optional): ").strip() or f"Super Administrator ({username})"
    email = input("  Email (optional): ").strip() or f"{username}@vims.et"
    phone = input("  Phone (optional): ").strip() or "+251911000000"
    
    print("\n[2] Enter password:")
    password = getpass.getpass("  Password: ")
    if not password:
        print("✗ Password cannot be empty!")
        return
    
    if len(password) < 8:
        print("⚠ Warning: Password is less than 8 characters. Continue? (y/n): ", end='')
        confirm = input().strip().lower()
        if confirm != 'y':
            print("✗ User creation cancelled.")
            return
    
    print("\n[3] Confirm password:")
    confirm_password = getpass.getpass("  Confirm: ")
    if password != confirm_password:
        print("✗ Passwords do not match!")
        return
    
    # Create user
    print(f"\n[4] Creating super admin user '{username}'...")
    try:
        user_id = f"USR-{str(uuid4())[:8].upper()}"
        user = User.objects.create_user(
            username=username,
            password=password,
            user_id=user_id,
            full_name=full_name,
            email=email,
            phone=phone,
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
        print(f"  Password: [the password you just entered]")
        print(f"  User ID: {user_id}")
        print(f"  Full Name: {full_name}")
        print(f"  Email: {email}")
        print(f"  Phone: {phone}")
        print(f"  Scope: National (full access)")
        
    except Exception as e:
        print(f"\n✗ Error creating user: {e}")
        return
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    create_superadmin_interactive()

