"""
URL routing for Users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RoleViewSet, LoginView, ForgotPasswordView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'password', ForgotPasswordView, basename='password')
router.register(r'', LoginView, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]




