"""
Health check views for monitoring and load balancing.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis


def health_check(request):
    """Basic health check - always returns 200 if service is running."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'VIMS Backend'
    })


def liveness_check(request):
    """
    Liveness check for Kubernetes.
    Returns 200 if the application is alive (even if dependencies are down).
    """
    return JsonResponse({
        'status': 'alive',
        'service': 'VIMS Backend'
    })


def readiness_check(request):
    """
    Readiness check for Kubernetes.
    Returns 200 only if all critical dependencies are available.
    """
    checks = {
        'database': False,
        'cache': False,
    }
    
    # Check database
    try:
        connection.ensure_connection()
        checks['database'] = True
    except Exception as e:
        checks['database'] = str(e)
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', timeout=10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception as e:
        checks['cache'] = str(e)
    
    # Determine overall status
    all_healthy = all(v is True for v in checks.values())
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks
    }, status=status_code)





