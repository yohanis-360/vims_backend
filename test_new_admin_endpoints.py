"""
Comprehensive test script for NEW admin portal endpoints.
Tests Users, Centers, Roles, Dashboard, and Security APIs.
"""
import requests
import json
import os
import sys
from datetime import datetime

# Configure stdout for UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = "superadmin"
ADMIN_PASSWORD = "admin123"

# Global tokens
ACCESS_TOKEN = None
REFRESH_TOKEN = None

# Test data IDs
test_user_id = None
test_center_id = None
test_role_id = None

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_result(test_name, success, response=None):
    status = "✓ [PASS]" if success else "✗ [FAIL]"
    print(f"{status} | {test_name}")
    if response is not None:
        print(f"     Status: {response.status_code}")
        if not success and response.status_code >= 400:
            try:
                error = response.json()
                print(f"     Error: {json.dumps(error, indent=2)[:200]}")
            except:
                print(f"     Error: {response.text[:200]}")

def get_headers():
    if not ACCESS_TOKEN:
        raise Exception("Access token not available. Please login first.")
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

def test_login():
    global ACCESS_TOKEN, REFRESH_TOKEN
    print_section("TEST 1: Super Admin Login")
    url = f"{BASE_URL}/api/auth/login/"
    payload = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        success = response.status_code == 200
        print_result("Admin Login", success, response)
        
        if success:
            data = response.json()
            ACCESS_TOKEN = data['access']
            REFRESH_TOKEN = data['refresh']
            print(f"     User: {data['user']['username']}")
            print(f"     Token: {ACCESS_TOKEN[:20]}...")
        return success
    except Exception as e:
        print_result("Admin Login", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== USERS API TESTS ====================

def test_users_list():
    print_section("TEST 2: GET /api/auth/users/ - List Users")
    url = f"{BASE_URL}/api/auth/users/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("List Users", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Users: {data.get('count', len(data))}")
        return success
    except Exception as e:
        print_result("List Users", False)
        print(f"     Error: {str(e)}")
        return False

def test_user_create():
    global test_user_id
    print_section("TEST 3: POST /api/auth/users/ - Create User")
    url = f"{BASE_URL}/api/auth/users/"
    
    unique_suffix = datetime.now().strftime("%H%M%S")
    payload = {
        "username": f"testuser{unique_suffix}",
        "email": f"test{unique_suffix}@vims.et",
        "full_name": "Test User",
        "phone": "+251911000000",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "status": "Active",
        "job_title": "Test Inspector"
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 201
        print_result("Create User", success, response)
        
        if success:
            data = response.json()
            test_user_id = data.get('user_id')
            print(f"     Created User ID: {test_user_id}")
        return success
    except Exception as e:
        print_result("Create User", False)
        print(f"     Error: {str(e)}")
        return False

def test_user_suspend():
    print_section("TEST 4: POST /api/auth/users/{id}/suspend/ - Suspend User")
    if not test_user_id:
        print("     Skipped: No test user created")
        return False
    
    url = f"{BASE_URL}/api/auth/users/{test_user_id}/suspend/"
    
    try:
        response = requests.post(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Suspend User", success, response)
        return success
    except Exception as e:
        print_result("Suspend User", False)
        print(f"     Error: {str(e)}")
        return False

def test_user_activate():
    print_section("TEST 5: POST /api/auth/users/{id}/activate/ - Activate User")
    if not test_user_id:
        print("     Skipped: No test user created")
        return False
    
    url = f"{BASE_URL}/api/auth/users/{test_user_id}/activate/"
    
    try:
        response = requests.post(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Activate User", success, response)
        return success
    except Exception as e:
        print_result("Activate User", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== CENTERS API TESTS ====================

def test_centers_list():
    print_section("TEST 6: GET /api/centers/ - List Centers")
    url = f"{BASE_URL}/api/centers/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("List Centers", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Centers: {data.get('count', len(data))}")
        return success
    except Exception as e:
        print_result("List Centers", False)
        print(f"     Error: {str(e)}")
        return False

def test_center_create():
    global test_center_id
    print_section("TEST 7: POST /api/centers/ - Create Center")
    url = f"{BASE_URL}/api/centers/"
    
    unique_suffix = datetime.now().strftime("%H%M%S")
    test_center_id = f"CTR-TEST-{unique_suffix}"
    
    payload = {
        "center_id": test_center_id,
        "name": f"Test Center {unique_suffix}",
        "code": f"TEST{unique_suffix}",
        "region": "Test Region",
        "zone": "Test Zone",
        "address": "Test Address",
        "phone": "+251911000000",
        "email": f"center{unique_suffix}@vims.et",
        "latitude": 9.012345,
        "longitude": 38.765432,
        "geofence_radius_meters": 500,
        "status": "active",
        "is_active": True
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 201
        print_result("Create Center", success, response)
        
        if success:
            print(f"     Created Center ID: {test_center_id}")
        return success
    except Exception as e:
        print_result("Create Center", False)
        print(f"     Error: {str(e)}")
        return False

def test_center_update_geofence():
    print_section("TEST 8: POST /api/centers/{id}/update-geofence/ - Update Geofence")
    if not test_center_id:
        print("     Skipped: No test center created")
        return False
    
    url = f"{BASE_URL}/api/centers/{test_center_id}/update-geofence/"
    payload = {
        "latitude": 9.015000,
        "longitude": 38.770000,
        "radius_meters": 600
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Update Geofence", success, response)
        return success
    except Exception as e:
        print_result("Update Geofence", False)
        print(f"     Error: {str(e)}")
        return False

def test_centers_statistics():
    print_section("TEST 9: GET /api/centers/statistics/ - Get Center Statistics")
    url = f"{BASE_URL}/api/centers/statistics/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Center Statistics", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Centers: {data.get('total_centers')}")
            print(f"     Active: {data.get('active_centers')}")
        return success
    except Exception as e:
        print_result("Center Statistics", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== ROLES API TESTS ====================

def test_roles_list():
    print_section("TEST 10: GET /api/auth/roles/ - List Roles")
    url = f"{BASE_URL}/api/auth/roles/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("List Roles", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Roles: {len(data)}")
        return success
    except Exception as e:
        print_result("List Roles", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== DASHBOARD API TESTS ====================

def test_dashboard_overview():
    print_section("TEST 11: GET /api/dashboard/overview/ - Dashboard Overview")
    url = f"{BASE_URL}/api/dashboard/overview/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Dashboard Overview", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Inspections: {data.get('inspections', {}).get('total')}")
            print(f"     Total Centers: {data.get('centers', {}).get('total')}")
            print(f"     Total Users: {data.get('users', {}).get('total')}")
        return success
    except Exception as e:
        print_result("Dashboard Overview", False)
        print(f"     Error: {str(e)}")
        return False

def test_centers_attention():
    print_section("TEST 12: GET /api/dashboard/centers-attention/ - Centers Attention")
    url = f"{BASE_URL}/api/dashboard/centers-attention/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Centers Attention", success, response)
        return success
    except Exception as e:
        print_result("Centers Attention", False)
        print(f"     Error: {str(e)}")
        return False

def test_dashboard_revenue():
    print_section("TEST 13: GET /api/dashboard/revenue/ - Revenue Statistics")
    url = f"{BASE_URL}/api/dashboard/revenue/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Revenue Statistics", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Revenue: ${data.get('total_revenue', 0)}")
        return success
    except Exception as e:
        print_result("Revenue Statistics", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== SECURITY API TESTS ====================

def test_audit_logs_list():
    print_section("TEST 14: GET /api/security/audit-logs/ - List Audit Logs")
    url = f"{BASE_URL}/api/security/audit-logs/?limit=10"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("List Audit Logs", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Logs: {data.get('count', 0)}")
        return success
    except Exception as e:
        print_result("List Audit Logs", False)
        print(f"     Error: {str(e)}")
        return False

def test_audit_logs_statistics():
    print_section("TEST 15: GET /api/security/audit-logs/statistics/ - Audit Statistics")
    url = f"{BASE_URL}/api/security/audit-logs/statistics/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Audit Log Statistics", success, response)
        
        if success:
            data = response.json()
            print(f"     Total Logs: {data.get('total_logs', 0)}")
            print(f"     Logs Today: {data.get('logs_today', 0)}")
        return success
    except Exception as e:
        print_result("Audit Log Statistics", False)
        print(f"     Error: {str(e)}")
        return False

# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    results = []
    
    # Authentication
    if not test_login():
        print("\n[ERROR] Login failed. Cannot proceed.")
        return
    
    # Users API Tests
    results.append(("List Users", test_users_list()))
    results.append(("Create User", test_user_create()))
    results.append(("Suspend User", test_user_suspend()))
    results.append(("Activate User", test_user_activate()))
    
    # Centers API Tests
    results.append(("List Centers", test_centers_list()))
    results.append(("Create Center", test_center_create()))
    results.append(("Update Geofence", test_center_update_geofence()))
    results.append(("Center Statistics", test_centers_statistics()))
    
    # Roles API Tests
    results.append(("List Roles", test_roles_list()))
    
    # Dashboard API Tests
    results.append(("Dashboard Overview", test_dashboard_overview()))
    results.append(("Centers Attention", test_centers_attention()))
    results.append(("Dashboard Revenue", test_dashboard_revenue()))
    
    # Security API Tests
    results.append(("List Audit Logs", test_audit_logs_list()))
    results.append(("Audit Statistics", test_audit_logs_statistics()))
    
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
        print("\n✅ SUCCESS! ALL NEW ADMIN ENDPOINTS ARE WORKING!\n")
    else:
        print(f"\n⚠️ WARNING: {total - passed} test(s) failed. Please review the errors above.\n")


if __name__ == "__main__":
    print("="*80)
    print("  VIMS ADMIN PORTAL - NEW ENDPOINTS TEST SUITE")
    print("="*80)
    print(f"\n  Base URL: {BASE_URL}")
    print(f"  Test User: {ADMIN_USERNAME}\n")
    
    run_all_tests()

