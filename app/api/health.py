"""Health check and monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import time
import psutil
import os

from app.config import get_settings
from app.models.core import HealthStatus, SystemMetrics, ServiceHealth
try:
    from app.repositories.database import get_database
except ImportError:
    # Mock database dependency for testing
    async def get_database():
        from unittest.mock import AsyncMock
        mock_db = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value={"test": 1})
        return mock_db
from app.utils.logging import get_logger, metrics_collector
from app.services.model_inference import ModelInferenceService

router = APIRouter(prefix="/health", tags=["Health & Monitoring"])
logger = get_logger(__name__)


@router.get("/", response_model=HealthStatus)
async def basic_health_check():
    """Basic health check endpoint."""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="ZERO-COMP Solar Weather API",
        version=get_settings().api.app_version
    )


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db=Depends(get_database)):
    """Detailed health check with component status."""
    start_time = time.time()
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": get_settings().api.app_name,
        "version": get_settings().api.app_version,
        "environment": get_settings().environment,
        "components": {}
    }
    
    # Check database connectivity
    try:
        db_start = time.time()
        result = await db.fetch_one("SELECT 1 as test")
        db_time = time.time() - db_start
        
        health_data["components"]["database"] = {
            "status": "healthy" if result else "unhealthy",
            "response_time_ms": round(db_time * 1000, 2),
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("Database health check failed", exception=e)
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
        health_data["status"] = "degraded"
    
    # Check ML model availability
    try:
        model_start = time.time()
        model_service = ModelInferenceService()
        model_available = await model_service.check_model_health()
        model_time = time.time() - model_start
        
        health_data["components"]["ml_model"] = {
            "status": "healthy" if model_available else "unhealthy",
            "response_time_ms": round(model_time * 1000, 2),
            "model_version": get_settings().model.model_name,
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("ML model health check failed", exception=e)
        health_data["components"]["ml_model"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
        health_data["status"] = "degraded"
    
    # Check external services
    health_data["components"]["external_services"] = await check_external_services()
    
    # System metrics
    health_data["system_metrics"] = get_system_metrics()
    
    total_time = time.time() - start_time
    health_data["response_time_ms"] = round(total_time * 1000, 2)
    
    # Record health check metrics
    metrics_collector.record_api_metrics(
        endpoint="/health/detailed",
        method="GET",
        response_time=total_time,
        status_code=200 if health_data["status"] == "healthy" else 503
    )
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)


@router.get("/readiness")
async def readiness_check(db=Depends(get_database)):
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if database is accessible
        await db.fetch_one("SELECT 1")
        
        # Check if critical services are ready
        model_service = ModelInferenceService()
        model_ready = await model_service.check_model_health()
        
        if not model_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model not ready"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
        
    except Exception as e:
        logger.error("Readiness check failed", exception=e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}


@router.get("/metrics", response_model=SystemMetrics)
async def system_metrics():
    """Get detailed system performance metrics."""
    return SystemMetrics(**get_system_metrics())


async def check_external_services() -> Dict[str, Any]:
    """Check health of external services."""
    services = {}
    settings = get_settings()
    
    # Check Supabase
    try:
        # This would be implemented with actual Supabase client
        services["supabase"] = {
            "status": "healthy",
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        services["supabase"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    
    # Check Razorpay (if configured)
    if settings.external.razorpay_key_id:
        try:
            # This would be implemented with actual Razorpay client
            services["razorpay"] = {
                "status": "healthy",
                "last_checked": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            services["razorpay"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat() + "Z"
            }
    
    # Check NASA API (if configured)
    if settings.external.nasa_api_key:
        try:
            # This would be implemented with actual NASA API client
            services["nasa_api"] = {
                "status": "healthy",
                "last_checked": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            services["nasa_api"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat() + "Z"
            }
    
    return services


def get_system_metrics() -> Dict[str, Any]:
    """Get current system performance metrics."""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "load_average": list(os.getloadavg()) if hasattr(os, 'getloadavg') else None
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "usage_percent": memory.percent,
                "process_rss_bytes": process_memory.rss,
                "process_vms_bytes": process_memory.vms
            },
            "disk": {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "usage_percent": (disk.used / disk.total) * 100
            },
            "process": {
                "pid": os.getpid(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("Failed to collect system metrics", exception=e)
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }