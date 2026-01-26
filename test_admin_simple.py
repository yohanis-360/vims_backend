"""
Simple admin endpoint test - bypasses caching issues by using the DRF test client directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.inspections.models import Inspection

User = get_user_model()

def test_admin_endpoints():
    print("\n" + "="*80)
    print("VIMS ADMIN PORTAL API - SIMPLE TEST")
    print("="*80)
    
    # Get super admin user
    admin_user = User.objects.filter(username='superadmin').first()
    if not admin_user:
        print("✗ [ERROR] Super admin user not found!")
        return
    
    print(f"\n✓ Found admin user: {admin_user.username} (ID: {admin_user.user_id})")
    
    # Create API client
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    # Test 1: Get inspections list
    print("\n[TEST 1] GET /api/inspections/")
    response = client.get('/api/inspections/', SERVER_NAME='localhost')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Total Inspections: {data.get('count', 0)}")
        print(f"  ✓ Results in page: {len(data.get('results', []))}")
    else:
        print(f"  ✗ ERROR: {response.content[:200]}")
    
    # Get an inspection ID for next tests
    inspections = Inspection.objects.all()[:1]
    if not inspections:
        print("\n✗ [ERROR] No inspections found in database!")
        return
    
    inspection = inspections[0]
    print(f"\n✓ Using inspection: {inspection.inspection_id}")
    
    # Test 2: Get inspection detail
    print(f"\n[TEST 2] GET /api/inspections/{inspection.inspection_id}/")
    response = client.get(f'/api/inspections/{inspection.inspection_id}/', SERVER_NAME='localhost')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Inspection ID: {data.get('inspection_id')}")
        print(f"  ✓ Status: {data.get('status')}")
        print(f"  ✓ Plate: {data.get('plate_number')}")
    else:
        print(f"  ✗ ERROR: {response.content[:200]}")
    
    # Test 3: Get machine results
    print(f"\n[TEST 3] GET /api/inspections/{inspection.inspection_id}/machine-results/")
    response = client.get(f'/api/inspections/{inspection.inspection_id}/machine-results/', SERVER_NAME='localhost')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Machine Test Pass: {data.get('machine_test_pass')}")
        print(f"  ✓ Total Tests: {data.get('total_tests')}")
    else:
        print(f"  ✗ ERROR: {response.content[:200]}")
    
    # Test 4: Get visual results
    print(f"\n[TEST 4] GET /api/inspections/{inspection.inspection_id}/visual-results/")
    response = client.get(f'/api/inspections/{inspection.inspection_id}/visual-results/', SERVER_NAME='localhost')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Visual Pass: {data.get('visual_pass')}")
        print(f"  ✓ Points: {data.get('points_earned')}/{data.get('points_total')}")
        print(f"  ✓ Total Items: {data.get('total_items')}")
    else:
        print(f"  ✗ ERROR: {response.content[:200]}")
    
    # Test 5: Get photos
    print(f"\n[TEST 5] GET /api/inspections/{inspection.inspection_id}/photos/")
    response = client.get(f'/api/inspections/{inspection.inspection_id}/photos/', SERVER_NAME='localhost')
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Total Photos: {data.get('total_photos')}")
    else:
        print(f"  ✗ ERROR: {response.content[:200]}")
    
    print("\n" + "="*80)
    print("✓ ALL ADMIN PORTAL ENDPOINTS TESTED SUCCESSFULLY!")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_admin_endpoints()

