"""URL routing for Security app"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, SuspiciousActivityViewSet

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'suspicious-activities', SuspiciousActivityViewSet, basename='suspicious-activity')

urlpatterns = [
    path('', include(router.urls)),
]
