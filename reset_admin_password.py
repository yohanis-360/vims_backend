"""
Script to reset admin password using forgot password API
Run with: python reset_admin_password.py
"""
import requests
import json
import os
import sys
import time

# Configure encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'superadmin@vims.et')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'superadmin')

def reset_admin_password():
    """Reset admin password using forgot password flow."""
    print("\n" + "=" * 80)
    print("RESET ADMIN PASSWORD")
    print("=" * 80)
    
    # Step 1: Request password reset
    print(f"\n[1] Requesting password reset for admin...")
    print(f"  Username: {ADMIN_USERNAME}")
    print(f"  Email: {ADMIN_EMAIL}")
    
    url = f"{BASE_URL}/users/password/forgot-password/"
    payload = {
        'username': ADMIN_USERNAME,
        'email': ADMIN_EMAIL
    }
    
    try:
        print(f"\n  Calling: {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Password reset request sent!")
            print(f"  Message: {data.get('message', 'No message')}")
            print("\n  Check the email inbox for the password reset link.")
            print("  The reset link will contain a token that you can use to reset the password.")
            print("\n  To complete the reset, you can:")
            print("  1. Check email for reset link")
            print("  2. Extract the token from the URL")
            print("  3. Use: python reset_admin_password.py --token YOUR_TOKEN --new-password NewPass123!")
        else:
            error_data = response.json() if response.text else {}
            print(f"✗ Failed: {error_data.get('error', error_data.get('detail', response.status_text))}")
            print(f"  Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out. Is the backend server running?")
        print("  Try: docker-compose up -d")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend server.")
        print("  Make sure the backend is running at http://localhost:8000")
        print("  Or set API_BASE_URL environment variable")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 80 + "\n")

def reset_with_token(token, new_password):
    """Reset password using token."""
    print("\n" + "=" * 80)
    print("RESET PASSWORD WITH TOKEN")
    print("=" * 80)
    
    url = f"{BASE_URL}/users/password/reset-password/"
    payload = {
        'token': token,
        'new_password': new_password,
        'new_password_confirm': new_password
    }
    
    print(f"\n[1] Resetting password...")
    print(f"  Token: {token[:20]}...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Password reset successful!")
            print(f"\n  Message: {data.get('message', 'No message')}")
            print(f"\n  You can now login with:")
            print(f"  Username: {ADMIN_USERNAME}")
            print(f"  Password: {new_password}")
        else:
            error_data = response.json() if response.text else {}
            print(f"✗ Failed: {error_data.get('error', error_data.get('detail', response.status_text))}")
            print(f"  Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("✗ Request timed out. Is the backend server running?")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend server.")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Reset admin password')
    parser.add_argument('--token', '-t', help='Reset token from email')
    parser.add_argument('--new-password', '-p', help='New password')
    parser.add_argument('--email', '-e', default=ADMIN_EMAIL, help='Admin email')
    parser.add_argument('--username', '-u', default=ADMIN_USERNAME, help='Admin username')
    
    args = parser.parse_args()
    
    if args.token and args.new_password:
        reset_with_token(args.token, args.new_password)
    else:
        reset_admin_password()

