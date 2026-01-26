"""
Test script for forgot password functionality
Run with: python test_forgot_password.py
"""
import requests
import json
import os
import sys

# Configure encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

def test_forgot_password(email=None, username=None):
    """Test forgot password endpoint."""
    print("\n" + "=" * 80)
    print("TEST FORGOT PASSWORD")
    print("=" * 80)
    
    url = f"{BASE_URL}/users/password/forgot-password/"
    
    payload = {}
    if email:
        payload['email'] = email
    if username:
        payload['username'] = username
    
    if not payload:
        print("\n✗ Email or username is required!")
        print("  Usage: python test_forgot_password.py --email admin@vims.et")
        print("  Or:    python test_forgot_password.py --username admin")
        return
    
    print(f"\n[1] Requesting password reset...")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\n[2] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Password reset request successful!")
            print(f"\n  Message: {data.get('message', 'No message')}")
            print("\n  Check the email inbox for the password reset link.")
            print("  The reset link will be valid for 24 hours.")
        else:
            error_data = response.json() if response.text else {}
            print(f"✗ Failed: {error_data.get('error', error_data.get('detail', response.status_text))}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return
    
    print("\n" + "=" * 80 + "\n")

def test_reset_password(token, new_password):
    """Test reset password endpoint."""
    print("\n" + "=" * 80)
    print("TEST RESET PASSWORD")
    print("=" * 80)
    
    url = f"{BASE_URL}/users/password/reset-password/"
    
    payload = {
        'token': token,
        'new_password': new_password,
        'new_password_confirm': new_password
    }
    
    print(f"\n[1] Resetting password with token...")
    print(f"  URL: {url}")
    print(f"  Token: {token[:20]}...")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\n[2] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Password reset successful!")
            print(f"\n  Message: {data.get('message', 'No message')}")
            print(f"\n  You can now login with:")
            print(f"  Password: {new_password}")
        else:
            error_data = response.json() if response.text else {}
            print(f"✗ Failed: {error_data.get('error', error_data.get('detail', response.status_text))}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test forgot password functionality')
    parser.add_argument('--email', '-e', help='Email address for password reset')
    parser.add_argument('--username', '-u', help='Username for password reset')
    parser.add_argument('--token', '-t', help='Reset token (for reset password test)')
    parser.add_argument('--new-password', '-p', help='New password (for reset password test)')
    
    args = parser.parse_args()
    
    if args.token and args.new_password:
        test_reset_password(args.token, args.new_password)
    elif args.email or args.username:
        test_forgot_password(email=args.email, username=args.username)
    else:
        print("\nUsage:")
        print("  Request password reset:")
        print("    python test_forgot_password.py --email admin@vims.et")
        print("    python test_forgot_password.py --username admin")
        print("\n  Reset password with token:")
        print("    python test_forgot_password.py --token YOUR_TOKEN --new-password NewPass123!")
        print("\n" + "=" * 80 + "\n")

