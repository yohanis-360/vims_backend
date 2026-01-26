"""
Script to change super admin password via API
Run with: python change_superadmin_password.py
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
SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'superadmin')
CURRENT_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD', 'admin123')

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
            print(f"✗ Login failed: {response.status_code}")
            if response.text:
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data.get('detail', error_data.get('error', 'Unknown error'))}")
                except:
                    print(f"  Response: {response.text[:200]}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"✗ Login request failed: {e}")
        return None, None

def change_password_api(token, user_id, new_password):
    """Change user password via API."""
    url = f"{BASE_URL}/users/users/{user_id}/change_password/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "old_password": CURRENT_PASSWORD,  # Current password
        "new_password": new_password,
        "new_password_confirm": new_password
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.text else {}
            return {"error": error_data.get('detail', error_data.get('error', f'HTTP {response.status_code}'))}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def change_superadmin_password():
    """Change super admin password."""
    print("\n" + "=" * 80)
    print("CHANGE SUPER ADMIN PASSWORD")
    print("=" * 80)
    
    # Step 1: Login with current password
    print(f"\n[1] Logging in as '{SUPER_ADMIN_USERNAME}'...")
    access_token, user_data = login(SUPER_ADMIN_USERNAME, CURRENT_PASSWORD)
    
    if not access_token:
        print("\n✗ Failed to login with current password!")
        print(f"  Username: {SUPER_ADMIN_USERNAME}")
        print(f"  Current password: {CURRENT_PASSWORD}")
        print("\n  If the password is different, set SUPER_ADMIN_PASSWORD environment variable:")
        print("  set SUPER_ADMIN_PASSWORD=your_current_password")
        return
    
    print("✓ Login successful!")
    user_id = user_data.get('user_id') if user_data else None
    if user_id:
        print(f"  User ID: {user_id}")
    
    # Step 2: Get new password
    print("\n[2] Enter new password:")
    new_password = getpass.getpass("  Password: ")
    
    if not new_password:
        print("\n✗ Password cannot be empty!")
        return
    
    if len(new_password) < 8:
        print("\n⚠ Warning: Password is less than 8 characters. Continue? (y/n): ", end='')
        confirm = input().strip().lower()
        if confirm != 'y':
            print("✗ Password change cancelled.")
            return
    
    print("\n[3] Confirm new password:")
    confirm_password = getpass.getpass("  Confirm: ")
    
    if new_password != confirm_password:
        print("\n✗ Passwords do not match!")
        return
    
    # Step 3: Change password
    print(f"\n[4] Changing password for user '{SUPER_ADMIN_USERNAME}'...")
    result = change_password_api(access_token, user_id, new_password)
    
    if isinstance(result, dict) and "error" in result:
        print(f"✗ Failed to change password: {result['error']}")
        return
    
    print("\n✓ Password changed successfully!")
    print(f"\n✓ You can now login with:")
    print(f"  Username: {SUPER_ADMIN_USERNAME}")
    print(f"  Password: [the password you just entered]")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    change_superadmin_password()
