"""
URL routing for Configuration app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VisualChecklistConfigViewSet,
    TestStandardViewSet,
    FeeStructureViewSet
)

router = DefaultRouter()
router.register(r'visual-checklist-config', VisualChecklistConfigViewSet, basename='visual-checklist-config')
router.register(r'test-standards', TestStandardViewSet, basename='test-standards')
router.register(r'fee-structures', FeeStructureViewSet, basename='fee-structures')

urlpatterns = [
    path('', include(router.urls)),
]
