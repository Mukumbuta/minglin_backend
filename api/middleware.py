import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger('api')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all API requests with timing and response status.
    """
    def process_request(self, request):
        request.start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path}")

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"Request completed: {request.method} {request.path} - "
                f"Status: {response.status_code} - Duration: {duration:.3f}s"
            )
        return response

class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Log all errors with detailed context for debugging.
    """
    def process_exception(self, request, exception):
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'request_method': request.method,
                'request_path': request.path,
                'user_id': getattr(request.user, 'id', None),
            }
        )
        return JsonResponse(
            {'error': 'Internal server error', 'detail': str(exception)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor slow requests and log performance metrics.
    """
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} - "
                    f"Duration: {duration:.3f}s"
                )
        return response

# See README.md and inline comments for documentation. 