"""
Test script for VIMS Inspector Client API Endpoints
Tests all inspection-related endpoints end-to-end
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "inspector001"
TEST_PASSWORD = "test123"  # You'll need to create this user
MACHINE_ID = "M-001B44AC5678"
MAC_ADDRESS = "00:1B:44:AC:56:78"

# Global variables
access_token = None
inspection_id = None

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(test_name, success, response=None):
    """Print test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} | {test_name}")
    if response:
        print(f"     Status: {response.status_code}")
        if not success:
            print(f"     Response: {response.text[:300]}")
    print()

def test_machine_verification():
    """Test 1: Verify Machine"""
    print_section("TEST 1: Machine Verification")
    
    url = f"{BASE_URL}/api/users/machine/verify/"
    payload = {
        "macAddress": MAC_ADDRESS,
        "certificateSerial": "CERT-2025-001"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        success = response.status_code == 200 and response.json().get('trusted') == True
        print_result("Machine Verification", success, response)
        if success:
            print(f"     Machine ID: {response.json().get('machineId')}")
        else:
            print(f"     URL: {url}")
            print(f"     Response: {response.text}")
        return success
    except requests.exceptions.ConnectionError as e:
        print_result("Machine Verification", False)
        print(f"     Connection Error: Backend not responding at {BASE_URL}")
        print(f"     URL: {url}")
        return False
    except Exception as e:
        print_result("Machine Verification", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_machine_handshake():
    """Test 2: Machine Handshake"""
    print_section("TEST 2: Machine Handshake")
    
    url = f"{BASE_URL}/api/users/machine/handshake/"
    payload = {
        "machineId": MACHINE_ID,
        "macAddress": MAC_ADDRESS
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        success = response.status_code == 200 and response.json().get('status') == 'INITIATED'
        print_result("Machine Handshake", success, response)
        if success:
            print(f"     Session ID: {response.json().get('sessionId')}")
        else:
            print(f"     URL: {url}")
            print(f"     Response: {response.text}")
        return success
    except Exception as e:
        print_result("Machine Handshake", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_login():
    """Test 3: Inspector Login"""
    global access_token
    print_section("TEST 3: Inspector Login")
    
    url = f"{BASE_URL}/api/users/login/"
    payload = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "machineId": MACHINE_ID
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        success = response.status_code == 200 and 'access' in response.json()
        print_result("Inspector Login", success, response)
        
        if success:
            data = response.json()
            access_token = data['access']
            print(f"     User: {data.get('user', {}).get('username')}")
            print(f"     Token: {access_token[:50]}...")
        else:
            print(f"     URL: {url}")
            print(f"     Response: {response.text}")
        return success
    except Exception as e:
        print_result("Inspector Login", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def get_headers():
    """Get headers with auth token."""
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

def test_create_inspection():
    """Test 4: Create Inspection"""
    global inspection_id
    print_section("TEST 4: Create Inspection")
    
    url = f"{BASE_URL}/api/inspections/"
    payload = {
        "inspection_id": f"VIMS-LV-2025-TEST{datetime.now().strftime('%H%M%S')}",
        "plate_number": "AA12345",  # Fixed format without dash
        "chassis_number": "WBADT43452G123456",
        "engine_number": "N47D20A12345",
        "vehicle_type": "Passenger Car",
        "vehicle_category": "LIGHT",
        "brand_model": "Toyota Camry",
        "fuel_type": "Petrol",
        "kilometer_reading": 125480,
        "licensed_capacity": 5,
        "title_certificate": "TC-2024-001234",
        "owner_name": "John Doe",
        "center": "CTR-AA-001",
        "form_id": "LV-FORM-2025",
        "test_start_time": datetime.now().isoformat()
        # inspector will be set automatically from auth token
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=15)
        success = response.status_code == 201
        print_result("Create Inspection", success, response)
        
        if success:
            data = response.json()
            inspection_id = data['inspection_id']
            print(f"     Inspection ID: {inspection_id}")
            print(f"     Status: {data.get('status')}")
        else:
            print(f"     URL: {url}")
            print(f"     Response: {response.text[:500]}")
        return success
    except Exception as e:
        print_result("Create Inspection", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_submit_visual_checklist():
    """Test 5: Submit Visual Checklist"""
    print_section("TEST 5: Submit Visual Checklist (30-Point)")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/submit_visual_checklist/"
    payload = {
        "items": [
            {
                "item_number": 1,
                "item_name_en": "Registration Plate Validity",
                "item_name_am": "የሰሌዳ ቁጥር ትክክለኛነት",
                "zone_id": "zone1",
                "zone_name_en": "Identification & Documentation",
                "points_possible": 5,
                "status": "PASS",
                "defect_type": "",
                "is_critical": False,
                "is_mandatory": False
            },
            {
                "item_number": 2,
                "item_name_en": "Chassis Number Match",
                "item_name_am": "የቻሲስ ቁጥር ማዛመድ",
                "zone_id": "zone1",
                "zone_name_en": "Identification & Documentation",
                "points_possible": 5,
                "status": "PASS",
                "defect_type": "",
                "is_critical": True,
                "is_mandatory": False
            },
            # Add remaining 28 items for complete test
        ] + [
            {
                "item_number": i,
                "item_name_en": f"Test Item {i}",
                "item_name_am": f"ፈተና {i}",
                "zone_id": f"zone{((i-1)//6)+1}",
                "zone_name_en": "Test Zone",
                "points_possible": 3,
                "status": "PASS",
                "defect_type": "",
                "is_critical": False,
                "is_mandatory": False
            }
            for i in range(3, 31)
        ],
        "notes": "All items verified and passed"
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=15)
        success = response.status_code == 200
        print_result("Submit Visual Checklist", success, response)
        
        if success:
            data = response.json()
            print(f"     Points: {data.get('points_earned')}/{data.get('points_total')}")
            print(f"     Visual Pass: {data.get('visual_pass')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Submit Visual Checklist", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_submit_machine_tests():
    """Test 6: Submit Machine Tests (RYME Data)"""
    print_section("TEST 6: Submit Machine Tests (RYME Integration)")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/submit_machine_tests/"
    payload = {
        "tests": [
            {
                "machine_test_id": f"MT-{inspection_id}-1",
                "test_type": "alignment",
                "test_name": "Wheel Alignment & Suspension",
                "test_data": {
                    "alignment_deviation": 2.5,
                    "suspension_left": 55.2,
                    "suspension_right": 58.1,
                    "suspension_diff": 2.9
                },
                "result": "PASS",
                "pass_status": True,
                "data_source": "RYME_SMRW",
                "machine_serial": "RYME-AL-001"
            },
            {
                "machine_test_id": f"MT-{inspection_id}-2",
                "test_type": "service_brake",
                "test_name": "Service Brake Test",
                "test_data": {
                    "front_left": 2850.5,
                    "front_right": 2920.3,
                    "rear_left": 3100.2,
                    "rear_right": 3050.8,
                    "total_force": 11921.8,
                    "front_balance": 2.4,
                    "rear_balance": 1.6
                },
                "result": "PASS",
                "pass_status": True,
                "data_source": "RYME_SMRW",
                "machine_serial": "RYME-BR-002"
            },
            {
                "machine_test_id": f"MT-{inspection_id}-3",
                "test_type": "parking_brake",
                "test_name": "Parking Brake Test",
                "test_data": {
                    "rear_left": 1850.5,
                    "rear_right": 1920.3,
                    "total_force": 3770.8,
                    "balance": 3.7
                },
                "result": "PASS",
                "pass_status": True,
                "data_source": "RYME_SMRW",
                "machine_serial": "RYME-BR-002"
            },
            {
                "machine_test_id": f"MT-{inspection_id}-4",
                "test_type": "gas_analyzer",
                "test_name": "Gas Analyzer (Petrol)",
                "test_data": {
                    "HC": 120,
                    "CO": 0.35,
                    "CO2": 13.5,
                    "O2": 1.2,
                    "lambda": 1.01
                },
                "result": "PASS",
                "pass_status": True,
                "data_source": "RYME_SMRW",
                "machine_serial": "RYME-GA-003"
            },
            {
                "machine_test_id": f"MT-{inspection_id}-5",
                "test_type": "headlight",
                "test_name": "Headlight Test",
                "test_data": {
                    "left_intensity": 15000,
                    "left_aim_h": 2.5,
                    "left_aim_v": -1.2,
                    "right_intensity": 15200,
                    "right_aim_h": 2.3,
                    "right_aim_v": -1.1
                },
                "result": "PASS",
                "pass_status": True,
                "data_source": "RYME_SMRW",
                "machine_serial": "RYME-HL-004"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=15)
        success = response.status_code == 200
        print_result("Submit Machine Tests", success, response)
        
        if success:
            data = response.json()
            print(f"     Tests Count: {data.get('tests_count')}")
            print(f"     Machine Pass: {data.get('machine_test_pass')}")
            print(f"     Overall Result: {data.get('overall_result')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Submit Machine Tests", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_upload_photo():
    """Test 7: Upload GPS-Stamped Photo"""
    print_section("TEST 7: Upload GPS-Stamped Photo")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/upload_photo/"
    payload = {
        "photo_id": f"PHOTO-{inspection_id}-001",
        "purpose": "registration",
        "photo_url": f"https://vims-photos.s3.amazonaws.com/2025/01/{inspection_id}-001.jpg",
        "latitude": 9.012345,
        "longitude": 38.765432,
        "gps_accuracy": 10.5,
        "timestamp": datetime.now().isoformat(),
        "file_size": 1024000
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 201
        print_result("Upload Photo", success, response)
        
        if success:
            data = response.json()
            print(f"     Photo ID: {data.get('photo_id')}")
            print(f"     GPS: {data.get('latitude')}, {data.get('longitude')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Upload Photo", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_validate_geofence():
    """Test 8: Validate Geofence"""
    print_section("TEST 8: Validate Geofence")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/validate_geofence/"
    params = {
        "lat": "9.012345",
        "lng": "38.765432"
    }
    
    try:
        response = requests.get(url, params=params, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Validate Geofence", success, response)
        
        if success:
            data = response.json()
            print(f"     Valid: {data.get('valid')}")
            print(f"     Distance: {data.get('distance_meters')}m")
        else:
            print(f"     URL: {url}?{params}")
        return success
    except Exception as e:
        print_result("Validate Geofence", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_update_sync_status():
    """Test 9: Update Sync Status"""
    print_section("TEST 9: Update Sync Status")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/sync-status/"
    payload = {
        "sync_status": "synced",
        "sync_error": ""
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Update Sync Status", success, response)
        
        if success:
            data = response.json()
            print(f"     Sync Status: {data.get('sync_status')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Update Sync Status", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_process_payment():
    """Test 10: Process Payment"""
    print_section("TEST 10: Process Payment & Finalize")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/process-payment/"
    payload = {
        "payment_method": "cash",
        "amount": 250.00,
        "transaction_id": f"TXN-{inspection_id}",
        "reference": "Inspector payment - test"
    }
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Process Payment", success, response)
        
        if success:
            data = response.json()
            print(f"     Payment Status: {data.get('payment_status')}")
            print(f"     Overall Result: {data.get('overall_result')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Process Payment", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def test_get_statistics():
    """Test 11: Get Dashboard Statistics"""
    print_section("TEST 11: Get Dashboard Statistics")
    
    for range_type in ['today', 'week', 'month']:
        url = f"{BASE_URL}/api/inspections/statistics/"
        params = {"range": range_type}
        
        try:
            response = requests.get(url, params=params, headers=get_headers())
            success = response.status_code == 200
            print_result(f"Statistics ({range_type})", success, response)
            
            if success:
                data = response.json()
                print(f"     Total: {data.get('total_inspections')}")
                print(f"     Pass Rate: {data.get('pass_rate')}%")
        except Exception as e:
            print_result(f"Statistics ({range_type})", False)
            print(f"     Error: {str(e)}")
            return False
    
    return True

def test_active_inspections():
    """Test 12: Get Active Inspections"""
    print_section("TEST 12: Get Active Inspections")
    
    url = f"{BASE_URL}/api/inspections/active/"
    
    try:
        response = requests.get(url, headers=get_headers())
        success = response.status_code == 200
        print_result("Get Active Inspections", success, response)
        
        if success:
            data = response.json()
            count = data.get('count', len(data) if isinstance(data, list) else 0)
            print(f"     Active Count: {count}")
        return success
    except Exception as e:
        print_result("Get Active Inspections", False)
        print(f"     Error: {str(e)}")
        return False

def test_completed_inspections():
    """Test 13: Get Completed Inspections"""
    print_section("TEST 13: Get Completed Inspections")
    
    url = f"{BASE_URL}/api/inspections/completed/"
    params = {"days": 7}
    
    try:
        response = requests.get(url, params=params, headers=get_headers())
        success = response.status_code == 200
        print_result("Get Completed Inspections", success, response)
        
        if success:
            data = response.json()
            count = data.get('count', len(data) if isinstance(data, list) else 0)
            print(f"     Completed Count: {count}")
        return success
    except Exception as e:
        print_result("Get Completed Inspections", False)
        print(f"     Error: {str(e)}")
        return False

def test_vehicle_history():
    """Test 14: Search Vehicle History"""
    print_section("TEST 14: Search Vehicle History")
    
    url = f"{BASE_URL}/api/inspections/vehicle-history/"
    params = {"plate": "AA-TEST"}
    
    try:
        response = requests.get(url, params=params, headers=get_headers())
        success = response.status_code == 200
        print_result("Search Vehicle History", success, response)
        
        if success:
            data = response.json()
            count = data.get('count', len(data) if isinstance(data, list) else 0)
            print(f"     History Count: {count}")
        return success
    except Exception as e:
        print_result("Search Vehicle History", False)
        print(f"     Error: {str(e)}")
        return False

def test_get_inspection_detail():
    """Test 15: Get Inspection Detail"""
    print_section("TEST 15: Get Inspection Detail")
    
    url = f"{BASE_URL}/api/inspections/{inspection_id}/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        success = response.status_code == 200
        print_result("Get Inspection Detail", success, response)
        
        if success:
            data = response.json()
            print(f"     Inspection ID: {data.get('inspection_id')}")
            print(f"     Status: {data.get('status')}")
            print(f"     Overall Result: {data.get('overall_result')}")
            print(f"     Visual Pass: {data.get('visual_pass')}")
            print(f"     Machine Pass: {data.get('machine_test_pass')}")
        else:
            print(f"     URL: {url}")
        return success
    except Exception as e:
        print_result("Get Inspection Detail", False)
        print(f"     Error: {str(e)}")
        print(f"     URL: {url}")
        return False

def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*80)
    print("  VIMS INSPECTOR CLIENT API - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"\n  Base URL: {BASE_URL}")
    print(f"  Test User: {TEST_USERNAME}")
    print(f"  Machine ID: {MACHINE_ID}\n")
    
    results = []
    
    # Authentication & Setup
    results.append(("Machine Verification", test_machine_verification()))
    results.append(("Machine Handshake", test_machine_handshake()))
    results.append(("Inspector Login", test_login()))
    
    if not access_token:
        print("\n[ERROR] CRITICAL: Login failed. Cannot proceed with inspection tests.")
        return
    
    # Inspection Workflow
    results.append(("Create Inspection", test_create_inspection()))
    
    if not inspection_id:
        print("\n[ERROR] CRITICAL: Inspection creation failed. Cannot proceed with remaining tests.")
        return
    
    results.append(("Submit Visual Checklist", test_submit_visual_checklist()))
    results.append(("Submit Machine Tests", test_submit_machine_tests()))
    results.append(("Upload Photo", test_upload_photo()))
    results.append(("Validate Geofence", test_validate_geofence()))
    results.append(("Update Sync Status", test_update_sync_status()))
    results.append(("Process Payment", test_process_payment()))
    
    # Dashboard & Query Endpoints
    results.append(("Dashboard Statistics", test_get_statistics()))
    results.append(("Active Inspections", test_active_inspections()))
    results.append(("Completed Inspections", test_completed_inspections()))
    results.append(("Vehicle History", test_vehicle_history()))
    results.append(("Inspection Detail", test_get_inspection_detail()))
    
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
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} | {test_name}")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! Inspector API is fully functional.\n")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review the errors above.\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Tests interrupted by user.\n")
    except Exception as e:
        print(f"\n\n[ERROR] CRITICAL ERROR: {str(e)}\n")

