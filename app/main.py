"""Main FastAPI application setup."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import logging
from contextlib import asynccontextmanager

from app.config import get_settings
from app.models.core import ErrorResponse
from app.utils.logging import setup_logging, get_logger
from app.middleware.logging import (
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    ErrorHandlingMiddleware
)
from app.docs.openapi_customization import customize_openapi_schema

# Setup structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting ZERO-COMP Solar Weather API")
    
    # Initialize monitoring and backup services
    try:
        from app.services.monitoring import initialize_monitoring
        from app.services.backup_recovery import initialize_backup_service
        
        await initialize_monitoring()
        logger.info("Monitoring system initialized")
        
        await initialize_backup_service()
        logger.info("Backup service initialized")
        
    except Exception as e:
        logger.error("Failed to initialize monitoring/backup services", exception=e)
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZERO-COMP Solar Weather API")
    
    try:
        from app.services.monitoring import shutdown_monitoring
        from app.services.backup_recovery import shutdown_backup_service
        
        await shutdown_monitoring()
        await shutdown_backup_service()
        logger.info("Services shut down successfully")
        
    except Exception as e:
        logger.error("Error during service shutdown", exception=e)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Enhanced OpenAPI documentation configuration
    app = FastAPI(
        title="ZERO-COMP Solar Weather API",
        version=settings.api.app_version,
        description="""
# ZERO-COMP Solar Weather API

Real-time solar flare prediction API powered by NASA-IBM's Surya-1.0 transformer model.

## Overview

ZERO-COMP provides enterprise-grade solar weather forecasting to industries that depend on space reliability, including:
- **Satellite Operators**: Protect satellite fleets from space weather damage
- **Power Grid Companies**: Plan maintenance windows and prevent outages
- **Aviation Firms**: Adjust polar flight routes during solar storms
- **Research Institutions**: Access historical solar weather data

## Features

- **Real-time Predictions**: Solar flare probability updates every 10 minutes
- **Multiple Access Methods**: REST API, WebSocket alerts, and web dashboard
- **Tiered Subscriptions**: Free, Pro ($50/month), and Enterprise ($500/month) plans
- **Historical Data**: Access to comprehensive solar weather history
- **Custom Alerts**: Configurable probability thresholds and webhook notifications

## Authentication

The API supports two authentication methods:

### 1. JWT Tokens (Dashboard Users)
Obtain JWT tokens through the web dashboard login process using Supabase authentication.

### 2. API Keys (Programmatic Access)
Generate API keys through the dashboard for programmatic access. API keys are available for Pro and Enterprise subscribers.

**Authentication Header Format:**
```
Authorization: Bearer <your-jwt-token-or-api-key>
```

## Rate Limits

Rate limits vary by subscription tier:

| Tier | Alerts Endpoint | History Endpoint | WebSocket |
|------|----------------|------------------|-----------|
| Free | 10/hour | 5/hour | Dashboard only |
| Pro | 1,000/hour | 500/hour | ✓ |
| Enterprise | 10,000/hour | 5,000/hour | ✓ |

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error_code": "HTTP_400",
  "message": "Invalid request parameters",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

## WebSocket Real-time Alerts

Connect to `/ws/alerts` for real-time solar flare notifications:

```javascript
const ws = new WebSocket('wss://api.zero-comp.com/ws/alerts?token=your-jwt-token');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  if (alert.type === 'alert') {
    console.log('Solar flare alert:', alert.data);
  }
};
```

## Support

- **Documentation**: [https://docs.zero-comp.com](https://docs.zero-comp.com)
- **Support Email**: support@zero-comp.com
- **Status Page**: [https://status.zero-comp.com](https://status.zero-comp.com)
        """,
        summary="Enterprise solar weather prediction API",
        contact={
            "name": "ZERO-COMP Support",
            "url": "https://zero-comp.com/support",
            "email": "support@zero-comp.com"
        },
        license_info={
            "name": "Commercial License",
            "url": "https://zero-comp.com/license"
        },
        servers=[
            {
                "url": "https://api.zero-comp.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.zero-comp.com", 
                "description": "Staging server"
            }
        ],
        docs_url="/docs" if settings.api.debug else "/docs",
        redoc_url="/redoc" if settings.api.debug else "/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        tags_metadata=[
            {
                "name": "Alerts",
                "description": "Solar flare prediction and alert endpoints. Get current predictions, historical data, and export functionality.",
            },
            {
                "name": "Users", 
                "description": "User profile and subscription management. Handle API keys, webhooks, and account settings.",
            },
            {
                "name": "WebSocket",
                "description": "Real-time WebSocket connections for live solar flare alerts and notifications.",
            },
            {
                "name": "payments",
                "description": "Payment processing and subscription management through Razorpay integration.",
            },
            {
                "name": "Health & Monitoring",
                "description": "System health checks, performance metrics, and service status endpoints.",
            },
            {
                "name": "Monitoring & Alerting",
                "description": "Internal monitoring, alerting system, and operational metrics for system administrators.",
            },
            {
                "name": "Root",
                "description": "Basic API information and service discovery endpoints.",
            }
        ]
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.zero-comp.com", "*.railway.app", "*.fly.io"]
        )
    
    # Add logging and monitoring middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=2.0)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add unique request ID to each request."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        """Add request processing time to response headers."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Global exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent error format."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        error_response = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    # Global exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.api.app_name,
            "version": settings.api.app_version,
            "environment": settings.environment
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": settings.api.app_name,
            "version": settings.api.app_version,
            "description": "Real-time solar flare prediction API",
            "docs_url": "/docs" if settings.api.debug else None,
            "health_url": "/health"
        }
    
    # Include API routers
    from app.api.alerts import router as alerts_router
    from app.api.users import router as users_router
    from app.api.websockets import router as websockets_router
    from app.api.payments import router as payments_router
    from app.api.health import router as health_router
    from app.api.monitoring import router as monitoring_router
    app.include_router(alerts_router)
    app.include_router(users_router)
    app.include_router(websockets_router)
    app.include_router(payments_router)
    app.include_router(health_router)
    app.include_router(monitoring_router)
    
    # Customize OpenAPI schema with enhanced documentation
    app.openapi = lambda: customize_openapi_schema(app)
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.logging.log_level.lower()
    )