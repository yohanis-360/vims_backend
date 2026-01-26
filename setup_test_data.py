"""
Setup script to create test data for inspector endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.centers.models import Center
from apps.users.models import User

def create_test_data():
    """Create test center and ensure test user exists."""
    
    # Create test center if it doesn't exist
    center_code = "CTR-AA-001"
    if not Center.objects.filter(code=center_code).exists():
        center = Center.objects.create(
            center_id=center_code,
            code=center_code,
            name="Test Center AA",
            region="Addis Ababa",
            zone="Zone 1",
            subcity="Subcity 1",
            woreda="Woreda 1",
            address="Test Address, Addis Ababa",
            latitude=9.012345,
            longitude=38.765432,
            geofence_radius_meters=500,
            status="Active",
            is_active=True
        )
        print(f"✓ Test center created: {center_code}")
    else:
        print(f"✓ Test center already exists: {center_code}")
    
    # Verify test user exists
    username = 'inspector001'
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"✓ Test user exists: {username} (ID: {user.user_id})")
    else:
        print(f"✗ Test user '{username}' not found! Run setup_test_user.py first")
    
    print("\n✓ Test data setup complete!")

if __name__ == '__main__':
    create_test_data()

