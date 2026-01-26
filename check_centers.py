"""
Script to check what center IDs exist in the database
Uses API endpoint (like other test scripts) instead of direct DB access

Run with: 
  - Via API (recommended): python check_centers.py
  - Via Docker: docker-compose exec web1 python check_centers.py
"""
import requests
import json
import os
import sys

# Configure stdout for UTF-8 (like test_new_admin_endpoints.py)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "superadmin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Alternative: Try inspector user if admin doesn't work
INSPECTOR_USERNAME = os.getenv("INSPECTOR_USERNAME", "inspector001")
INSPECTOR_PASSWORD = os.getenv("INSPECTOR_PASSWORD", "test123")

def login(username=None, password=None):
    """Login and get access token."""
    url = f"{BASE_URL}/api/users/login/"
    payload = {
        "username": username or ADMIN_USERNAME,
        "password": password or ADMIN_PASSWORD,
        "machineId": None
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('access')
        else:
            return None
    except Exception as e:
        return None

def check_centers_via_api():
    """Check centers using API endpoint."""
    print("\n" + "=" * 80)
    print("ACTIVE CENTERS IN DATABASE (via API)")
    print("=" * 80)
    
    # Login first - try admin, then inspector
    print("\n[1] Logging in...")
    access_token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not access_token:
        print(f"  Trying inspector user ({INSPECTOR_USERNAME})...")
        access_token = login(INSPECTOR_USERNAME, INSPECTOR_PASSWORD)
    
    if not access_token:
        print("\n✗ Cannot proceed without authentication!")
        print("  Make sure the backend is running and you have valid credentials.")
        print(f"  Tried: {ADMIN_USERNAME} and {INSPECTOR_USERNAME}")
        print("\n  You can set credentials via environment variables:")
        print("    ADMIN_USERNAME=your_user ADMIN_PASSWORD=your_pass python check_centers.py")
        return
    
    print("✓ Login successful")
    
    # Get centers
    print("\n[2] Fetching centers from API...")
    url = f"{BASE_URL}/api/centers/?is_active=true"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            centers = data.get('results', data.get('data', []))
            
            if isinstance(centers, list) and len(centers) > 0:
                print(f"\n✓ Found {len(centers)} active center(s):\n")
                center_ids = []
                for center in centers:
                    center_id = center.get('center_id') or center.get('id')
                    center_ids.append(center_id)
                    print(f"  Center ID: {center_id}")
                    print(f"  Name:      {center.get('name', 'N/A')}")
                    print(f"  Code:      {center.get('code', 'N/A')}")
                    print(f"  Region:    {center.get('region', 'N/A')}")
                    print(f"  Status:    {center.get('status', 'N/A')}")
                    print("-" * 80)
                
                # Show just the IDs for easy reference
                print("\n✓ Valid Center IDs (for role assignments):")
                print(f"  {', '.join(center_ids)}")
            else:
                print("\n✗ No active centers found in the database!")
                print("\n  To create a center, run:")
                print("    docker-compose exec web1 python setup_test_data.py")
                print("  Or create one manually via Django admin or API")
        else:
            print(f"✗ API request failed: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            
    except Exception as e:
        print(f"✗ Error fetching centers: {e}")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    check_centers_via_api()

