#!/usr/bin/env python
"""Test creating an inspector user and sending email."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User, Role, RoleAssignment
from apps.users.utils import send_temporary_password_email
import uuid
import secrets
import string
from django.utils import timezone

print("=" * 60)
print("Testing Inspector User Creation with Email")
print("=" * 60)

# Generate temporary password
alphabet = string.ascii_letters + string.digits + '!@#$%'
temporary_password = ''.join(secrets.choice(alphabet) for _ in range(12))

# Create test inspector user
test_username = f"test_inspector_{uuid.uuid4().hex[:6]}"
test_email = f"test_{uuid.uuid4().hex[:6]}@test.com"

print(f"\nCreating test user:")
print(f"  Username: {test_username}")
print(f"  Email: {test_email}")
print(f"  Temporary Password: {temporary_password}")

try:
    # Create user
    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password=temporary_password,
        full_name="Test Inspector",
        phone="+251911234567",
        status='Active',
        user_id=f"U-{uuid.uuid4().hex[:8].upper()}"
    )
    
    print(f"\n✓ User created successfully!")
    print(f"  User ID: {user.user_id}")
    
    # Set temporary_password attribute (like serializer does)
    user.temporary_password = temporary_password
    print(f"  Set user.temporary_password = {temporary_password}")
    
    # Try to get INSPECTOR role
    try:
        inspector_role = Role.objects.get(role_id='INSPECTOR')
        print(f"\n✓ Found INSPECTOR role: {inspector_role.role_name_en}")
        
        # Create role assignment
        role_assignment_id = f"RA-{user.user_id}-INSPECTOR"
        role_assignment = RoleAssignment.objects.create(
            role_assignment_id=role_assignment_id,
            user=user,
            role=inspector_role,
            scope_type='Center',
            scope_ids=['test-center-1'],
            status='Active',
            approval_status='Approved',
            assigned_at=timezone.now()
        )
        print(f"✓ Role assignment created")
        
    except Role.DoesNotExist:
        print(f"\n⚠ INSPECTOR role not found - skipping role assignment")
    
    # Test email sending
    print(f"\n" + "=" * 60)
    print("Testing Email Sending...")
    print("=" * 60)
    
    try:
        send_temporary_password_email(user, temporary_password)
        print(f"\n✓ Email sent successfully!")
        print(f"  Check your inbox at: tayeyohanis8@gmail.com")
    except Exception as e:
        print(f"\n✗ Error sending email: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"  User ID: {user.user_id}")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Temporary Password: {temporary_password}")
    print(f"\n  You can now:")
    print(f"    1. Check email inbox: tayeyohanis8@gmail.com")
    print(f"    2. Check backend logs for email logs")
    print(f"    3. Try logging in with username: {test_username}")
    print(f"    4. Password: {temporary_password}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()


