# VIMS Backend API Documentation

## Overview
Complete RESTful API for Vehicle Inspection Management System (VIMS), optimized for 100,000+ concurrent users.

---

## Architecture & Optimization

### Core Stack
- **Django 5.0+** with async view support
- **Django REST Framework** for API
- **PostgreSQL** with read replicas
- **Redis** for caching & sessions
- **Celery** for async task processing
- **Nginx** for load balancing
- **Docker & Kubernetes** for horizontal scaling

### Performance Optimizations

#### 1. Database Optimization
```python
# Query optimization with select_related & prefetch_related
queryset = Inspection.objects.select_related(
    'center', 'inspector'
).prefetch_related(
    'machine_tests', 'visual_items', 'photos'
).only('inspection_id', 'plate_number', 'status')
```

#### 2. Caching Strategy
- **View-level caching**: 1-minute cache for list views
- **Object-level caching**: 10-minute cache for detail views
- **Statistics caching**: 5-minute cache for dashboard data
- **Scope caching**: 5-minute cache for user permissions

#### 3. Async Task Processing
- Certificate generation
- Photo processing (resize, compress, watermark)
- Notification sending
- Report generation
- Metrics calculation

#### 4. Connection Pooling
- PgBouncer for database connection pooling
- Redis connection pooling
- Persistent HTTP connections

---

## API Endpoints

### Authentication

#### Obtain JWT Token
```http
POST /api/auth/token/
Content-Type: application/json

{
    "username": "inspector001",
    "password": "secure_password"
}

Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Inspections API

#### 1. List Inspections (Paginated, Scope-Filtered)
```http
GET /api/inspections/?page=1&page_size=50
Authorization: Bearer {access_token}

Response:
{
    "count": 1234,
    "next": "http://api.example.com/api/inspections/?page=2",
    "previous": null,
    "results": [
        {
            "inspection_id": "VIMS-LV-2025-ABCD",
            "plate_number": "AA-12345",
            "status": "completed",
            "overall_result": "PASS",
            "created_at": "2025-01-15T10:30:00Z",
            "test_start_time": "2025-01-15T10:30:00Z"
        },
        ...
    ]
}
```

#### 2. Create Inspection
```http
POST /api/inspections/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "inspection_id": "VIMS-LV-2025-ABCD",
    "plate_number": "AA-12345",
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
    "inspector": "USR-INS-001",
    "form_id": "LV-FORM-2025",
    "test_start_time": "2025-01-15T10:30:00Z"
}

Response: 201 Created
{
    "inspection_id": "VIMS-LV-2025-ABCD",
    "status": "in_progress",
    ...
}
```

#### 3. Get Inspection Detail
```http
GET /api/inspections/{inspection_id}/
Authorization: Bearer {access_token}

Response:
{
    "inspection_id": "VIMS-LV-2025-ABCD",
    "plate_number": "AA-12345",
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
    "center": {...},
    "inspector": {...},
    "status": "completed",
    "overall_result": "PASS",
    "visual_pass": true,
    "machine_test_pass": true,
    "visual_points_earned": 95,
    "visual_points_total": 100,
    "machine_tests": [...],
    "visual_items": [...],
    "photos": [...],
    "machine_test_count": 5,
    "visual_items_count": 30,
    "photos_count": 8
}
```

#### 4. Submit Visual Checklist
```http
POST /api/inspections/{inspection_id}/submit_visual_checklist/
Authorization: Bearer {access_token}
Content-Type: application/json

{
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
            "is_critical": false,
            "is_mandatory": false
        },
        {
            "item_number": 2,
            "item_name_en": "Chassis Number Match",
            "item_name_am": "የቻሲስ ቁጥር ማዛመድ",
            "zone_id": "zone1",
            "zone_name_en": "Identification & Documentation",
            "points_possible": 5,
            "status": "FAIL",
            "defect_type": "missing",
            "is_critical": true,
            "is_mandatory": false
        },
        ...  // 30 items total
    ],
    "notes": "Additional observations..."
}

Response:
{
    "status": "success",
    "message": "Visual checklist submitted successfully",
    "visual_pass": true,
    "points_earned": 95,
    "points_total": 100,
    "items_count": 30
}
```

#### 5. Submit Machine Tests
```http
POST /api/inspections/{inspection_id}/submit_machine_tests/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "tests": [
        {
            "machine_test_id": "MT-2025-ABCD-1",
            "test_type": "alignment",
            "test_name": "Wheel Alignment & Suspension",
            "test_data": {
                "alignment_deviation": 2.5,
                "suspension_left": 55.2,
                "suspension_right": 58.1,
                "suspension_diff": 2.9
            },
            "result": "PASS",
            "pass_status": true,
            "data_source": "RYME_SMRW",
            "machine_serial": "RYME-AL-001"
        },
        {
            "machine_test_id": "MT-2025-ABCD-2",
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
            "pass_status": true,
            "data_source": "RYME_SMRW",
            "machine_serial": "RYME-BR-002"
        },
        ...  // All 5-6 machine tests
    ]
}

Response:
{
    "status": "success",
    "message": "Machine tests submitted successfully",
    "machine_test_pass": true,
    "overall_result": "PASS",
    "tests_count": 5
}
```

#### 6. Upload Photo
```http
POST /api/inspections/{inspection_id}/upload_photo/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "photo_id": "PHOTO-2025-ABCD-001",
    "purpose": "registration",
    "photo_url": "s3://vims-photos/2025/01/15/PHOTO-2025-ABCD-001.jpg",
    "latitude": 9.012345,
    "longitude": 38.765432,
    "gps_accuracy": 10.5,
    "timestamp": "2025-01-15T10:30:00Z",
    "file_size": 1024000
}

Response: 201 Created
{
    "photo_id": "PHOTO-2025-ABCD-001",
    "purpose": "registration",
    "photo_url": "s3://vims-photos/2025/01/15/PHOTO-2025-ABCD-001.jpg",
    ...
}
```

#### 7. Validate Geofence
```http
GET /api/inspections/{inspection_id}/validate_geofence/?lat=9.012345&lng=38.765432
Authorization: Bearer {access_token}

Response:
{
    "valid": true,
    "distance_meters": 125.45,
    "geofence_radius_meters": 500,
    "message": "Within geofence"
}
```

#### 8. Finalize Inspection
```http
POST /api/inspections/{inspection_id}/finalize/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "payment_transaction_id": "TXN-2025-001234",
    "payment_amount": 250.00
}

Response:
{
    "status": "success",
    "message": "Inspection finalized successfully",
    "inspection_id": "VIMS-LV-2025-ABCD",
    "overall_result": "PASS",
    "status": "completed"
}
```

#### 9. Get Statistics
```http
GET /api/inspections/statistics/
Authorization: Bearer {access_token}

Response:
{
    "total_inspections": 12345,
    "in_progress": 45,
    "pending_machine": 23,
    "pending_payment": 12,
    "completed": 12150,
    "failed": 115,
    "pass_rate": 99.07
}
```

---

### Machine Tests API (Read-Only)

#### List Machine Tests
```http
GET /api/machine-tests/?inspection_id=VIMS-LV-2025-ABCD
Authorization: Bearer {access_token}

Response:
{
    "count": 5,
    "results": [
        {
            "machine_test_id": "MT-2025-ABCD-1",
            "inspection": "VIMS-LV-2025-ABCD",
            "test_type": "alignment",
            "test_name": "Wheel Alignment & Suspension",
            "test_data": {...},
            "result": "PASS",
            "pass_status": true,
            "data_source": "RYME_SMRW",
            "machine_serial": "RYME-AL-001",
            "timestamp": "2025-01-15T11:00:00Z",
            "is_locked": true
        },
        ...
    ]
}
```

---

### Visual Checklist API (Read-Only)

#### List Visual Items
```http
GET /api/visual-checklist/?inspection_id=VIMS-LV-2025-ABCD
Authorization: Bearer {access_token}

Response:
{
    "count": 30,
    "results": [
        {
            "item_number": 1,
            "item_name_en": "Registration Plate Validity",
            "item_name_am": "የሰሌዳ ቁጥር ትክክለኛነት",
            "zone_id": "zone1",
            "zone_name_en": "Identification & Documentation",
            "points_possible": 5,
            "points_earned": 5,
            "status": "PASS",
            "defect_type": "",
            "is_critical": false,
            "is_mandatory": false,
            "checked_at": "2025-01-15T10:45:00Z"
        },
        ...
    ]
}
```

---

## RYME Machine Integration

### Data Flow
```
RYME Machines → RYME SMRW → Access DB → Inspector Client → Django Backend
```

### Inspector Client Workflow
1. **Poll Access DB**: Use `rymeAccessReader.js` to read test results
2. **Map Data**: Convert RYME format to VIMS format
3. **Send to Backend**: POST to `/api/inspections/{id}/submit_machine_tests/`

### Machine Test Types
1. **Alignment & Suspension**
2. **Service Brake**
3. **Parking Brake**
4. **Gas Analyzer** (Petrol)
5. **Smoke Meter** (Diesel)
6. **Headlight Test**

### Data Integrity
- ✅ Machine test data is **READ-ONLY** after submission
- ✅ `is_locked = True` prevents modification
- ✅ Audit trail with timestamp and data source
- ✅ GPS coordinates for geofence validation

---

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid inspection data",
        "details": {
            "plate_number": ["Invalid format. Expected: AA-12345"]
        }
    }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

---

## Rate Limiting
- **Authentication endpoints**: 10 requests/minute
- **Read endpoints**: 1000 requests/minute
- **Write endpoints**: 100 requests/minute

---

## Pagination
```http
GET /api/inspections/?page=2&page_size=100

Response:
{
    "count": 12345,
    "next": "http://api.example.com/api/inspections/?page=3&page_size=100",
    "previous": "http://api.example.com/api/inspections/?page=1&page_size=100",
    "results": [...]
}
```
- Default page size: 50
- Max page size: 200

---

## Filtering & Search

### Filter by Status
```http
GET /api/inspections/?status=completed
```

### Filter by Date Range
```http
GET /api/inspections/?created_after=2025-01-01&created_before=2025-01-31
```

### Search
```http
GET /api/inspections/?search=AA-12345
```

---

## Deployment

### Environment Variables
```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/vims
REDIS_URL=redis://localhost:6379/0

# Optional
DEBUG=False
ALLOWED_HOSTS=api.vims.example.com
CORS_ALLOWED_ORIGINS=https://admin.vims.example.com,https://app.vims.example.com
```

### Docker Compose (Development)
```bash
cd vims-backend
docker-compose up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f k8s/
```

---

## Monitoring

### Health Checks
```http
GET /health/basic/       # Basic health check
GET /health/readiness/   # Kubernetes readiness probe
GET /health/liveness/    # Kubernetes liveness probe
```

### Metrics
```http
GET /metrics/            # Prometheus metrics
```

---

## Testing

### Run Tests
```bash
pytest apps/inspections/tests/
```

### Load Testing
```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## Support
For technical support or questions, contact the VIMS development team.





