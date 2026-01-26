"""
Custom exception handlers for DRF.
Provides consistent error responses across the API.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(
        f"Exception in {context['view'].__class__.__name__}: {exc}",
        exc_info=True,
        extra={'request': context.get('request')}
    )
    
    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'code': response.status_code,
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data
    else:
        # Handle exceptions that DRF doesn't handle
        custom_response_data = {
            'success': False,
            'error': {
                'message': 'An unexpected error occurred.',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'details': {'detail': str(exc)}
            }
        }
        response = Response(
            custom_response_data,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


class ScopePermissionDenied(Exception):
    """
    Exception raised when user tries to access data outside their scope.
    """
    def __init__(self, message="You don't have permission to access this resource."):
        self.message = message
        super().__init__(self.message)


class GeofenceViolation(Exception):
    """
    Exception raised when inspection occurs outside geofence boundaries.
    """
    def __init__(self, message="Inspection location is outside authorized geofence."):
        self.message = message
        super().__init__(self.message)


class MachineDataIntegrityError(Exception):
    """
    Exception raised when machine test data integrity is compromised.
    """
    def __init__(self, message="Machine test data cannot be modified."):
        self.message = message
        super().__init__(self.message)





