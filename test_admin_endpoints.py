import requests
import json
import os
import sys
from datetime import datetime

# Configure stdout for UTF-8 to handle emojis and special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
# Using super admin user
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "superadmin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Global variables for tokens and IDs
ACCESS_TOKEN = None
REFRESH_TOKEN = None
inspection_id = None  # Will use an existing inspection from previous test

def print_section(title):
    print(f"\n================================================================================")
    print(f"  {title}")
    print(f"================================================================================")

def print_result(test_name, success, response=None):
    status = "✓ [PASS]" if success else "✗ [FAIL]"
    print(f"{status} | {test_name}")
    if response is not None and not success:
        try:
            error_data = response.json()
            print(f"     URL: {response.request.url}")
            print(f"     Response: {json.dumps(error_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"     URL: {response.request.url}")
            print(f"     Raw Response: {response.text[:500]}...")
    elif response is not None and success:
        print(f"     Status: {response.status_code}")
        try:
            data = response.json()
            if isinstance(data, dict):
                # Print relevant fields
                for key in ['inspection_id', 'total_tests', 'total_items', 'total_photos', 'machine_test_pass', 'visual_pass']:
                    if key in data:
                        print(f"     {key}: {data[key]}")
        except:
            pass

def get_headers():
    if not ACCESS_TOKEN:
        raise Exception("Access token not available. Please login first.")
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

def test_admin_login():
    global ACCESS_TOKEN, REFRESH_TOKEN
    print_section("TEST 1: Admin Login")
    url = f"{BASE_URL}/api/auth/login/"
    payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        success = response.status_code == 200
        print_result("Admin Login", success, response)
        if success:
            data = response.json()
            ACCESS_TOKEN = data['access']
            REFRESH_TOKEN = data['refresh']
            print(f"     User: {data['user']['username']}")
            print(f"     Token: {ACCESS_TOKEN[:10]}...")
        return success
    except Exception as e:
        print_result("Admin Login", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_inspections_list():
    global inspection_id
    print_section("TEST 2: Get Inspections List")
    url = f"{BASE_URL}/api/inspections/?limit=5"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Inspections List", success, response)
        if success:
            data = response.json()
            results = data.get('results', [])
            print(f"     Total: {data.get('count', 0)}")
            print(f"     Results: {len(results)}")
            if results:
                inspection_id = results[0].get('inspection_id')
                print(f"     First Inspection ID: {inspection_id}")
        return success
    except Exception as e:
        print_result("Get Inspections List", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_inspection_detail():
    print_section("TEST 3: Get Inspection Detail")
    if not inspection_id:
        print_result("Get Inspection Detail", False)
        print("     Error: No inspection_id available.")
        return False

    url = f"{BASE_URL}/api/inspections/{inspection_id}/"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Inspection Detail", success, response)
        if success:
            data = response.json()
            print(f"     Inspection ID: {data.get('inspection_id')}")
            print(f"     Status: {data.get('status')}")
            print(f"     Plate: {data.get('plate_number')}")
            print(f"     Vehicle Type: {data.get('vehicle_type')}")
        return success
    except Exception as e:
        print_result("Get Inspection Detail", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_machine_results():
    print_section("TEST 4: Get Machine Results (Admin Portal Endpoint)")
    if not inspection_id:
        print_result("Get Machine Results", False)
        print("     Error: No inspection_id available.")
        return False

    url = f"{BASE_URL}/api/inspections/{inspection_id}/machine-results/"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Machine Results", success, response)
        if success:
            data = response.json()
            print(f"     Inspection ID: {data.get('inspection_id')}")
            print(f"     Machine Test Pass: {data.get('machine_test_pass')}")
            print(f"     Total Tests: {data.get('total_tests')}")
            tests = data.get('tests', [])
            if tests:
                print(f"     Test Types: {', '.join([t.get('test_type', '') for t in tests])}")
        return success
    except Exception as e:
        print_result("Get Machine Results", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_visual_results():
    print_section("TEST 5: Get Visual Results (Admin Portal Endpoint)")
    if not inspection_id:
        print_result("Get Visual Results", False)
        print("     Error: No inspection_id available.")
        return False

    url = f"{BASE_URL}/api/inspections/{inspection_id}/visual-results/"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Visual Results", success, response)
        if success:
            data = response.json()
            print(f"     Inspection ID: {data.get('inspection_id')}")
            print(f"     Visual Pass: {data.get('visual_pass')}")
            print(f"     Points: {data.get('points_earned')}/{data.get('points_total')}")
            print(f"     Total Items: {data.get('total_items')}")
        return success
    except Exception as e:
        print_result("Get Visual Results", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_photos():
    print_section("TEST 6: Get Photos (Admin Portal Endpoint)")
    if not inspection_id:
        print_result("Get Photos", False)
        print("     Error: No inspection_id available.")
        return False

    url = f"{BASE_URL}/api/inspections/{inspection_id}/photos/"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Photos", success, response)
        if success:
            data = response.json()
            print(f"     Inspection ID: {data.get('inspection_id')}")
            print(f"     Total Photos: {data.get('total_photos')}")
            photos = data.get('photos', [])
            if photos:
                print(f"     Photo Purposes: {', '.join([p.get('purpose', '') for p in photos])}")
        return success
    except Exception as e:
        print_result("Get Photos", False)
        print(f"     Error: {str(e)}")
        return False

def test_filter_inspections_by_status():
    print_section("TEST 7: Filter Inspections by Status")
    url = f"{BASE_URL}/api/inspections/?status=completed&limit=5"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Filter by Status (completed)", success, response)
        if success:
            data = response.json()
            print(f"     Total Completed: {data.get('count', 0)}")
            print(f"     Results: {len(data.get('results', []))}")
        return success
    except Exception as e:
        print_result("Filter by Status", False)
        print(f"     Error: {str(e)}")
        return False

def test_search_by_plate():
    print_section("TEST 8: Search by Plate Number")
    url = f"{BASE_URL}/api/inspections/?plate_number=AA&limit=5"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Search by Plate Number", success, response)
        if success:
            data = response.json()
            print(f"     Total Results: {data.get('count', 0)}")
            print(f"     Results: {len(data.get('results', []))}")
        return success
    except Exception as e:
        print_result("Search by Plate", False)
        print(f"     Error: {str(e)}")
        return False

def run_all_tests():
    results = []
    
    # Authentication
    results.append(("Admin Login", test_admin_login()))
    
    if not ACCESS_TOKEN:
        print("\n[ERROR] CRITICAL: Login failed. Cannot proceed with tests.")
        return

    # Admin Portal Endpoints
    results.append(("Get Inspections List", test_get_inspections_list()))
    
    if not inspection_id:
        print("\n[ERROR] CRITICAL: No inspections found. Please run inspector tests first to create data.")
        return

    results.append(("Get Inspection Detail", test_get_inspection_detail()))
    results.append(("Get Machine Results", test_get_machine_results()))
    results.append(("Get Visual Results", test_get_visual_results()))
    results.append(("Get Photos", test_get_photos()))
    results.append(("Filter by Status", test_filter_inspections_by_status()))
    results.append(("Search by Plate", test_search_by_plate()))
    
    # Print Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%\n")
    
    print("Detailed Results:")
    for test_name, success in results:
        status = "✓ [PASS]" if success else "✗ [FAIL]"
        print(f"  {status} | {test_name}")

    if passed == total:
        print("\n✓ SUCCESS! ALL ADMIN PORTAL ENDPOINTS ARE WORKING!\n")
    else:
        print(f"\n✗ WARNING: {total - passed} test(s) failed. Please review the errors above.\n")


if __name__ == "__main__":
    print("================================================================================")
    print("  VIMS ADMIN PORTAL API - TEST SUITE")
    print("================================================================================")
    print(f"\n  Base URL: {BASE_URL}")
    print(f"  Test User: {ADMIN_USERNAME}")
    print(f"  Note: This test requires existing inspection data from inspector tests.\n")
    
    run_all_tests()

