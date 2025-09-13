"""Logging and monitoring middleware."""

import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logging import request_logger, error_tracker, metrics_collector, get_logger
from app.models.core import ErrorResponse

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID if not present
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())
        
        # Record request start time
        start_time = time.time()
        
        # Extract user information if available
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None)
        
        response = None
        error = None
        
        try:
            # Process request
            response = await call_next(request)
            
        except Exception as e:
            # Track error and create error response
            error = e
            error_id = error_tracker.track_error(
                error=e,
                context={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers)
                },
                user_id=user_id,
                request_id=request.state.request_id
            )
            
            # Create standardized error response
            error_response = ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={"error_id": error_id},
                request_id=request.state.request_id
            )
            
            response = JSONResponse(
                status_code=500,
                content=error_response.model_dump(mode='json')
            )
        
        finally:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add timing headers
            if response:
                response.headers["X-Request-ID"] = request.state.request_id
                response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            # Log request
            await request_logger.log_request(
                request=request,
                response_status=response.status_code if response else 500,
                response_time=response_time,
                user_id=user_id,
                error=error
            )
            
            # Record API metrics
            metrics_collector.record_api_metrics(
                endpoint=request.url.path,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code if response else 500,
                user_tier=getattr(request.state, "user_tier", None)
            )
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring performance and tracking slow requests."""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance."""
        start_time = time.time()
        
        response = await call_next(request)
        
        response_time = time.time() - start_time
        
        # Track slow requests
        if response_time > self.slow_request_threshold:
            error_tracker.track_performance_issue(
                operation=f"{request.method} {request.url.path}",
                duration=response_time,
                threshold=self.slow_request_threshold,
                context={
                    "query_params": dict(request.query_params),
                    "user_agent": request.headers.get("user-agent"),
                    "status_code": response.status_code
                }
            )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and tracking."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and create consistent error responses."""
        try:
            response = await call_next(request)
            return response
            
        except ValueError as e:
            # Handle validation errors
            error_id = error_tracker.track_error(
                error=e,
                context={"endpoint": request.url.path},
                request_id=getattr(request.state, "request_id", "unknown"),
                severity="warning"
            )
            
            error_response = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message=str(e),
                details={"error_id": error_id},
                request_id=getattr(request.state, "request_id", "unknown")
            )
            
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump(mode='json')
            )
            
        except PermissionError as e:
            # Handle permission errors
            error_id = error_tracker.track_error(
                error=e,
                context={"endpoint": request.url.path},
                request_id=getattr(request.state, "request_id", "unknown"),
                severity="warning"
            )
            
            error_response = ErrorResponse(
                error_code="PERMISSION_DENIED",
                message="Insufficient permissions",
                details={"error_id": error_id},
                request_id=getattr(request.state, "request_id", "unknown")
            )
            
            return JSONResponse(
                status_code=403,
                content=error_response.model_dump(mode='json')
            )
            
        except TimeoutError as e:
            # Handle timeout errors
            error_id = error_tracker.track_error(
                error=e,
                context={"endpoint": request.url.path},
                request_id=getattr(request.state, "request_id", "unknown"),
                severity="error"
            )
            
            error_response = ErrorResponse(
                error_code="REQUEST_TIMEOUT",
                message="Request timed out",
                details={"error_id": error_id},
                request_id=getattr(request.state, "request_id", "unknown")
            )
            
            return JSONResponse(
                status_code=408,
                content=error_response.model_dump(mode='json')
            )
            
        except ConnectionError as e:
            # Handle connection errors
            error_id = error_tracker.track_error(
                error=e,
                context={"endpoint": request.url.path},
                request_id=getattr(request.state, "request_id", "unknown"),
                severity="error"
            )
            
            error_response = ErrorResponse(
                error_code="SERVICE_UNAVAILABLE",
                message="External service unavailable",
                details={"error_id": error_id},
                request_id=getattr(request.state, "request_id", "unknown")
            )
            
            return JSONResponse(
                status_code=503,
                content=error_response.model_dump(mode='json')
            )
            
        except Exception as e:
            # Handle all other unexpected errors
            error_id = error_tracker.track_error(
                error=e,
                context={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "headers": dict(request.headers)
                },
                request_id=getattr(request.state, "request_id", "unknown"),
                severity="critical"
            )
            
            error_response = ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={"error_id": error_id},
                request_id=getattr(request.state, "request_id", "unknown")
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump(mode='json')
            )