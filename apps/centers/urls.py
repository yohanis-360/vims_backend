"""URL routing for Centers app"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet

router = DefaultRouter()
router.register(r'', CenterViewSet, basename='center')

urlpatterns = [
    path('', include(router.urls)),
]
