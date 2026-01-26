"""URL routing for Governance app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminUnitViewSet, InstitutionViewSet

router = DefaultRouter()
router.register(r'admin-units', AdminUnitViewSet, basename='adminunit')
router.register(r'institutions', InstitutionViewSet, basename='institution')

urlpatterns = [
    path('', include(router.urls)),
]
