"""
URL Configuration for Inspections API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InspectionViewSet,
    MachineTestViewSet,
    VisualChecklistViewSet,
    InspectionPhotoViewSet
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'', InspectionViewSet, basename='inspection')
router.register(r'machine-tests', MachineTestViewSet, basename='machine-test')
router.register(r'visual-checklist', VisualChecklistViewSet, basename='visual-checklist')
router.register(r'photos', InspectionPhotoViewSet, basename='inspection-photo')

urlpatterns = [
    path('', include(router.urls)),
]

"""
API Endpoints:

# Inspections
GET     /api/inspections/                                   - List inspections (paginated, filtered by scope)
POST    /api/inspections/                                   - Create new inspection
GET     /api/inspections/{id}/                              - Get inspection detail
PUT     /api/inspections/{id}/                              - Update inspection
PATCH   /api/inspections/{id}/                              - Partial update inspection
DELETE  /api/inspections/{id}/                              - Delete inspection
GET     /api/inspections/statistics/                        - Get inspection statistics

# Inspection Actions
POST    /api/inspections/{id}/submit_visual_checklist/      - Submit 30-point visual checklist
POST    /api/inspections/{id}/submit_machine_tests/         - Submit machine test results
POST    /api/inspections/{id}/upload_photo/                 - Upload inspection photo
POST    /api/inspections/{id}/finalize/                     - Finalize inspection with payment
GET     /api/inspections/{id}/validate_geofence/            - Validate geofence (query: lat, lng)

# Machine Tests (Read-Only)
GET     /api/machine-tests/                                 - List machine tests (query: inspection_id, test_type)
GET     /api/machine-tests/{id}/                            - Get machine test detail

# Visual Checklist (Read-Only)
GET     /api/visual-checklist/                              - List visual items (query: inspection_id)
GET     /api/visual-checklist/{id}/                         - Get visual item detail

# Photos
GET     /api/photos/                                        - List photos (query: inspection_id, purpose)
POST    /api/photos/                                        - Upload photo
GET     /api/photos/{id}/                                   - Get photo detail
DELETE  /api/photos/{id}/                                   - Delete photo
"""
