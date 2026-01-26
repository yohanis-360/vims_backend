"""
Script to directly reset admin password (bypasses API, uses Django ORM)
Usage:
    python reset_admin_password_direct.py --password NewPass123!
    docker-compose exec web1 python reset_admin_password_direct.py --password NewPass123!
"""
import os
import sys
import django
import argparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User
from django.utils import timezone

def reset_admin_password_direct(new_password, username=None):
    """Directly reset admin password using Django ORM."""
    print("\n" + "=" * 80)
    print("RESET ADMIN PASSWORD (DIRECT)")
    print("=" * 80)
    
    # Find admin user
    admin_username = username or os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
    admin_user = User.objects.filter(username=admin_username).first()
    
    if not admin_user:
        print(f"\n✗ Admin user '{admin_username}' not found!")
        print("  Available users:")
        for user in User.objects.all()[:10]:
            print(f"    - {user.username} ({user.email})")
        return
    
    print(f"\n✓ Found admin user:")
    print(f"  Username: {admin_user.username}")
    print(f"  Email: {admin_user.email}")
    print(f"  Full Name: {admin_user.full_name}")
    print(f"  User ID: {admin_user.user_id}")
    print(f"  Status: {admin_user.status}")
    
    if not new_password:
        print("\n✗ Password is required!")
        print("  Usage: python reset_admin_password_direct.py --password NewPass123!")
        return
    
    if len(new_password) < 8:
        print("⚠ Warning: Password is less than 8 characters.")
    
    # Reset password
    try:
        admin_user.set_password(new_password)
        admin_user.password_changed_at = timezone.now()
        admin_user.failed_login_attempts = 0  # Reset failed login attempts
        admin_user.account_locked_until = None  # Unlock account if locked
        admin_user.save(update_fields=['password', 'password_changed_at', 'failed_login_attempts', 'account_locked_until'])
        
        print("\n✓ Password reset successfully!")
        print(f"\n✓ Credentials:")
        print(f"  Username: {admin_user.username}")
        print(f"  Password: {new_password}")
        print(f"  Email: {admin_user.email}")
        print(f"  Password changed at: {admin_user.password_changed_at}")
        
    except Exception as e:
        print(f"\n✗ Error resetting password: {e}")
        return
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reset admin password directly')
    parser.add_argument('--password', '-p', required=True, help='New password')
    parser.add_argument('--username', '-u', default=None, help='Admin username (default: superadmin)')
    
    args = parser.parse_args()
    reset_admin_password_direct(args.password, args.username)

