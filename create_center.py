"""
Script to create a new center via API
Run with: python create_center.py
"""
import requests
import json
import os
import sys

# Configure stdout for UTF-8
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
        return None
    except Exception as e:
        return None

def create_center(center_id, name, code=None, region="Addis Ababa", access_token=None):
    """Create a new center via API."""
    url = f"{BASE_URL}/api/centers/"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        "center_id": center_id,
        "name": name,
        "code": code or center_id,
        "region": region,
        "zone": "",
        "subcity": "",
        "woreda": "",
        "address": "",
        "phone": "",
        "email": "",
        "latitude": None,
        "longitude": None,
        "geofence_radius_meters": 500,
        "status": "active",
        "is_active": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 201:
            return response.json()
        else:
            error_data = response.json() if response.content else {}
            return {"error": error_data, "status": response.status_code}
    except Exception as e:
        return {"error": str(e), "status": 0}

def main():
    print("\n" + "=" * 80)
    print("CREATE NEW CENTER")
    print("=" * 80)
    
    # Login first
    print("\n[1] Logging in...")
    access_token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not access_token:
        print(f"  Trying inspector user ({INSPECTOR_USERNAME})...")
        access_token = login(INSPECTOR_USERNAME, INSPECTOR_PASSWORD)
    
    if not access_token:
        print("\n✗ Cannot proceed without authentication!")
        print("  Make sure the backend is running and you have valid credentials.")
        return
    
    print("✓ Login successful")
    
    # Create center "CTR-001" to match user's role assignment
    print("\n[2] Creating center 'CTR-001'...")
    result = create_center(
        center_id="CTR-001",
        name="Inspection Center 001",
        code="CTR-001",
        region="Addis Ababa",
        access_token=access_token
    )
    
    if "error" in result:
        if result.get("status") == 400:
            error_detail = result.get("error", {})
            if "center_id" in str(error_detail):
                print("✗ Center 'CTR-001' already exists!")
            else:
                print(f"✗ Error creating center: {json.dumps(error_detail, indent=2)}")
        else:
            print(f"✗ Error: {result.get('error')}")
    else:
        print("✓ Center created successfully!")
        print(f"  Center ID: {result.get('center_id')}")
        print(f"  Name: {result.get('name')}")
        print(f"  Code: {result.get('code')}")
        print(f"  Region: {result.get('region')}")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    main()

