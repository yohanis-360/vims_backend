"""
Custom error views.
"""
from django.http import JsonResponse


def handler404(request, exception=None):
    """Custom 404 handler."""
    return JsonResponse({
        'success': False,
        'error': {
            'message': 'Resource not found',
            'code': 404
        }
    }, status=404)


def handler500(request):
    """Custom 500 handler."""
    return JsonResponse({
        'success': False,
        'error': {
            'message': 'Internal server error',
            'code': 500
        }
    }, status=500)





