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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting ZERO-COMP Solar Weather API")
    yield
    # Shutdown
    logger.info("Shutting down ZERO-COMP Solar Weather API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api.app_name,
        version=settings.api.app_version,
        description="Real-time solar flare prediction API powered by NASA-IBM Surya-1.0 model",
        docs_url="/docs" if settings.api.debug else None,
        redoc_url="/redoc" if settings.api.debug else None,
        lifespan=lifespan
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
            content=error_response.dict()
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
            content=error_response.dict()
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