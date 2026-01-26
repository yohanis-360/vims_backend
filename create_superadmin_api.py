"""
Script to create a new super admin user via API
Usage:
    python create_superadmin_api.py --username admin --password Admin123!
    python create_superadmin_api.py --username admin --password Admin123! --admin-user existing_admin --admin-pass existing_pass
"""
import requests
import json
import os
import sys
import argparse
import getpass

# Configure encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

def login(username, password):
    """Login and get access token."""
    url = f"{BASE_URL}/users/login/"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token'), data.get('user')
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"✗ Login request failed: {e}")
        return None, None

def create_user_via_api(admin_token, username, password, full_name=None, email=None, phone=None):
    """Create user via API."""
    url = f"{BASE_URL}/users/users/"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "username": username,
        "password": password,
        "password_confirm": password,
        "full_name": full_name or f"Super Administrator ({username})",
        "email": email or f"{username}@vims.et",
        "phone": phone or "+251911000000",
        "status": "Active",
        "is_active": True,
        "is_staff": True,
        "is_superuser": True
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return response.json(), None
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('detail', error_data.get('error', f'HTTP {response.status_code}'))
            return None, error_msg
    except requests.exceptions.RequestException as e:
        return None, str(e)

def assign_role_via_api(admin_token, user_id, role_id='NATIONAL_ADMIN', scope_type='National', scope_ids=None):
    """Assign role to user via API."""
    url = f"{BASE_URL}/users/users/{user_id}/assign_role/"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "role_id": role_id,
        "scope_type": scope_type,
        "scope_ids": scope_ids or []
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return response.json(), None
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('detail', error_data.get('error', f'HTTP {response.status_code}'))
            return None, error_msg
    except requests.exceptions.RequestException as e:
        return None, str(e)

def create_superadmin_via_api(username, password, full_name=None, email=None, phone=None, admin_username=None, admin_password=None):
    """Create super admin via API."""
    print("\n" + "=" * 80)
    print("CREATE NEW SUPER ADMIN USER (via API)")
    print("=" * 80)
    
    # Step 1: Get admin credentials
    if not admin_username:
        print("\n✗ Admin username required!")
        print("  Usage: python create_superadmin_api.py --username NEW_USER --password NEW_PASS --admin-user EXISTING_ADMIN --admin-pass EXISTING_PASS")
        return
    
    if not admin_password:
        print("\n✗ Admin password required!")
        print("  Usage: python create_superadmin_api.py --username NEW_USER --password NEW_PASS --admin-user EXISTING_ADMIN --admin-pass EXISTING_PASS")
        return
    
    # Step 2: Login as admin
    print(f"\n[2] Logging in as admin '{admin_username}'...")
    admin_token, admin_user = login(admin_username, admin_password)
    
    if not admin_token:
        print("✗ Admin login failed! Please check credentials.")
        return
    
    print("✓ Admin login successful!")
    
    # Step 3: Create user
    print(f"\n[3] Creating super admin user '{username}'...")
    user_data, error = create_user_via_api(admin_token, username, password, full_name, email, phone)
    
    if error:
        if "already exists" in error.lower() or "unique constraint" in error.lower():
            print(f"⚠ User '{username}' already exists!")
            print("  You can update the password using the change_password endpoint.")
            return
        else:
            print(f"✗ Failed to create user: {error}")
            return
    
    user_id = user_data.get('user_id')
    print(f"✓ User created: {user_id}")
    
    # Step 4: Assign NATIONAL_ADMIN role
    print(f"\n[4] Assigning NATIONAL_ADMIN role...")
    role_data, role_error = assign_role_via_api(admin_token, user_id, 'NATIONAL_ADMIN', 'National', [])
    
    if role_error:
        print(f"⚠ Role assignment failed: {role_error}")
        print("  User created but role not assigned. You may need to assign role manually.")
    else:
        print(f"✓ Role assigned successfully!")
    
    print("\n✓ Super admin user created successfully!")
    print(f"\n✓ Credentials:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  User ID: {user_id}")
    print(f"  Full Name: {user_data.get('full_name', full_name)}")
    print(f"  Email: {user_data.get('email', email)}")
    print(f"  Phone: {user_data.get('phone', phone)}")
    print(f"  Scope: National (full access)")
    print("\n" + "=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Create a new super admin user via API')
    parser.add_argument('--username', '-u', 
                       required=True,
                       help='Username for new super admin')
    parser.add_argument('--password', '-p',
                       required=True,
                       help='Password for new super admin')
    parser.add_argument('--full-name', '-n',
                       default=None,
                       help='Full name for super admin')
    parser.add_argument('--email', '-e',
                       default=None,
                       help='Email for super admin')
    parser.add_argument('--phone', '-t',
                       default=None,
                       help='Phone number for super admin')
    parser.add_argument('--admin-user', '-a',
                       default=None,
                       help='Existing admin username (for authentication)')
    parser.add_argument('--admin-pass', '-w',
                       default=None,
                       help='Existing admin password (for authentication)')
    
    args = parser.parse_args()
    
    create_superadmin_via_api(
        username=args.username,
        password=args.password,
        full_name=args.full_name,
        email=args.email,
        phone=args.phone,
        admin_username=args.admin_user,
        admin_password=args.admin_pass
    )

if __name__ == '__main__':
    main()

