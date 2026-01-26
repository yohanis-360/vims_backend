"""
URL configuration for VIMS Backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health checks
    path('health/', include('vims.health_urls')),
    
    # Prometheus metrics
    path('metrics/', include('django_prometheus.urls')),
    
    # Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/', include('apps.users.urls')),
    
    # API endpoints
    path('api/inspections/', include('apps.inspections.urls')),
    path('api/centers/', include('apps.centers.urls')),
    path('api/governance/', include('apps.governance.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/security/', include('apps.security.urls')),
    path('api/configuration/', include('apps.configuration.urls')),
    path('api/users/', include('apps.users.urls')),
]

# Dashboard endpoints
from apps.dashboard import DashboardOverviewView, CentersAttentionView, RevenueStatisticsView, UserScopeDebugView

urlpatterns += [
    path('api/dashboard/overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('api/dashboard/centers-attention/', CentersAttentionView.as_view(), name='centers-attention'),
    path('api/dashboard/revenue/', RevenueStatisticsView.as_view(), name='dashboard-revenue'),
    path('api/dashboard/debug-scope/', UserScopeDebugView.as_view(), name='debug-scope'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
handler404 = 'vims.views.handler404'
handler500 = 'vims.views.handler500'




