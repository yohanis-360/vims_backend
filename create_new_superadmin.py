"""
Script to create a new super admin user with custom credentials
Run with: python create_new_superadmin.py
"""
import requests
import json
import os
import sys
import getpass

# Configure encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

def create_superadmin_via_api():
    """Create a new super admin user via API."""
    print("\n" + "=" * 80)
    print("CREATE NEW SUPER ADMIN USER")
    print("=" * 80)
    
    # Get user input
    print("\n[1] Enter super admin details:")
    username = input("  Username: ").strip()
    if not username:
        print("✗ Username cannot be empty!")
        return
    
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
    
    # Create user via API
    print(f"\n[4] Creating super admin user '{username}'...")
    
    # First, we need to login as an existing admin or use a different method
    # Since we don't have admin credentials, let's try to create via direct API
    # But actually, we need admin access to create users with roles
    
    # Alternative: Use Django management command approach
    print("\n⚠ Note: Creating super admin requires admin access.")
    print("   If you don't have admin credentials, you can:")
    print("   1. Use Django shell: python manage.py shell")
    print("   2. Or run: python setup_super_admin.py (creates default superadmin)")
    print("\n   This script will attempt to create via API if you have admin access.")
    
    # Try to create user (requires admin token)
    print("\n   Do you have admin credentials to create this user? (y/n): ", end='')
    has_admin = input().strip().lower()
    
    if has_admin == 'y':
        admin_username = input("  Admin Username: ").strip()
        admin_password = getpass.getpass("  Admin Password: ")
        
        # Login as admin
        login_url = f"{BASE_URL}/users/login/"
        login_payload = {
            "username": admin_username,
            "password": admin_password
        }
        
        try:
            response = requests.post(login_url, json=login_payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                admin_token = data.get('access_token')
                
                if admin_token:
                    # Create user
                    create_url = f"{BASE_URL}/users/users/"
                    headers = {
                        "Authorization": f"Bearer {admin_token}",
                        "Content-Type": "application/json"
                    }
                    user_payload = {
                        "username": username,
                        "password": password,
                        "password_confirm": password,
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "status": "Active",
                        "is_active": True,
                        "is_staff": True,
                        "is_superuser": True
                    }
                    
                    create_response = requests.post(create_url, json=user_payload, headers=headers, timeout=10)
                    
                    if create_response.status_code in [200, 201]:
                        user_data = create_response.json()
                        user_id = user_data.get('user_id')
                        
                        # Assign NATIONAL_ADMIN role
                        assign_url = f"{BASE_URL}/users/users/{user_id}/assign_role/"
                        role_payload = {
                            "role_id": "NATIONAL_ADMIN",
                            "scope_type": "National",
                            "scope_ids": []
                        }
                        
                        assign_response = requests.post(assign_url, json=role_payload, headers=headers, timeout=10)
                        
                        print("\n✓ Super admin user created successfully!")
                        print(f"\n✓ Credentials:")
                        print(f"  Username: {username}")
                        print(f"  Password: [the password you entered]")
                        print(f"  User ID: {user_id}")
                        print(f"  Email: {email}")
                        
                        if assign_response.status_code in [200, 201]:
                            print(f"  Role: NATIONAL_ADMIN (National scope)")
                        else:
                            print(f"  ⚠ Role assignment may have failed. You may need to assign role manually.")
                        
                        print("\n" + "=" * 80 + "\n")
                        return
                    else:
                        error_data = create_response.json() if create_response.text else {}
                        print(f"✗ Failed to create user: {error_data.get('detail', error_data.get('error', f'HTTP {create_response.status_code}'))}")
                        return
            else:
                print("✗ Admin login failed!")
                return
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed: {e}")
            return
    else:
        print("\n⚠ To create super admin without API access, use Django shell:")
        print("\n   python manage.py shell")
        print("\n   Then run:")
        print(f"   from apps.users.models import User, Role, RoleAssignment")
        print(f"   user = User.objects.create_user(")
        print(f"       username='{username}',")
        print(f"       password='{password}',")
        print(f"       full_name='{full_name}',")
        print(f"       email='{email}',")
        print(f"       phone='{phone}',")
        print(f"       status='Active',")
        print(f"       is_active=True,")
        print(f"       is_staff=True,")
        print(f"       is_superuser=True")
        print(f"   )")
        print(f"   role = Role.objects.get(role_id='NATIONAL_ADMIN')")
        print(f"   RoleAssignment.objects.create(")
        print(f"       user=user,")
        print(f"       role=role,")
        print(f"       scope_type='National',")
        print(f"       scope_ids=[],")
        print(f"       status='Active',")
        print(f"       approval_status='Approved'")
        print(f"   )")
        print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    create_superadmin_via_api()

