"""Structured logging configuration and utilities."""

import logging
import logging.config
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

import structlog
from structlog.types import EventDict, Processor
from fastapi import Request

from app.config import get_settings


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dict."""
    event_dict["level"] = method_name.upper()
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service information to log events."""
    settings = get_settings()
    event_dict.update({
        "service": settings.api.app_name,
        "version": settings.api.app_version,
        "environment": settings.environment
    })
    return event_dict


def format_exception(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Format exception information for structured logging."""
    if "exception" in event_dict:
        exc = event_dict["exception"]
        if isinstance(exc, Exception):
            event_dict["exception"] = {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)
            }
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
    # Configure processors based on log format
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_timestamp,
        add_log_level,
        add_service_info,
        format_exception,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.logging.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.logging.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.logging.log_format == "json" else "standard",
                "stream": sys.stdout
            }
        },
        "root": {
            "level": settings.logging.log_level.upper(),
            "handlers": ["console"]
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if settings.logging.log_file:
        log_file_path = Path(settings.logging.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_file_path),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
        logging_config["root"]["handlers"].append("file")
        logging_config["loggers"]["uvicorn"]["handlers"].append("file")
        logging_config["loggers"]["uvicorn.access"]["handlers"].append("file")
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for HTTP requests with structured context."""
    
    def __init__(self, logger_name: str = "api.requests"):
        self.logger = get_logger(logger_name)
    
    async def log_request(
        self,
        request: Request,
        response_status: int,
        response_time: float,
        user_id: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> None:
        """Log HTTP request with structured data."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                "user-agent": request.headers.get("user-agent"),
                "content-type": request.headers.get("content-type"),
                "authorization": "***" if request.headers.get("authorization") else None
            },
            "client_ip": request.client.host if request.client else None,
            "response_status": response_status,
            "response_time_ms": round(response_time * 1000, 2),
            "user_id": user_id
        }
        
        if error:
            log_data["error"] = {
                "type": error.__class__.__name__,
                "message": str(error)
            }
            self.logger.error("Request failed", **log_data, exception=error)
        elif response_status >= 400:
            self.logger.warning("Request completed with error", **log_data)
        else:
            self.logger.info("Request completed successfully", **log_data)


class ErrorTracker:
    """Error tracking and reporting system."""
    
    def __init__(self, logger_name: str = "api.errors"):
        self.logger = get_logger(logger_name)
    
    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        severity: str = "error"
    ) -> str:
        """Track an error with context information."""
        error_id = f"err_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
        
        error_data = {
            "error_id": error_id,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "severity": severity,
            "user_id": user_id,
            "request_id": request_id,
            "context": context or {},
            "traceback": traceback.format_exception(type(error), error, error.__traceback__)
        }
        
        if severity == "critical":
            self.logger.critical("Critical error occurred", **error_data, exception=error)
        elif severity == "warning":
            self.logger.warning("Warning condition detected", **error_data, exception=error)
        else:
            self.logger.error("Error occurred", **error_data, exception=error)
        
        return error_id
    
    def track_performance_issue(
        self,
        operation: str,
        duration: float,
        threshold: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track performance issues when operations exceed thresholds."""
        if duration > threshold:
            self.logger.warning(
                "Performance threshold exceeded",
                operation=operation,
                duration_ms=round(duration * 1000, 2),
                threshold_ms=round(threshold * 1000, 2),
                context=context or {}
            )


class MetricsCollector:
    """Collect and log performance metrics."""
    
    def __init__(self, logger_name: str = "api.metrics"):
        self.logger = get_logger(logger_name)
    
    def record_prediction_metrics(
        self,
        model_version: str,
        inference_time: float,
        accuracy_score: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Record ML model prediction metrics."""
        metrics = {
            "metric_type": "prediction",
            "model_version": model_version,
            "inference_time_ms": round(inference_time * 1000, 2),
            "accuracy_score": accuracy_score,
            "error": error
        }
        
        if error:
            self.logger.error("Prediction failed", **metrics)
        else:
            self.logger.info("Prediction completed", **metrics)
    
    def record_api_metrics(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        user_tier: Optional[str] = None
    ) -> None:
        """Record API endpoint performance metrics."""
        metrics = {
            "metric_type": "api_performance",
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": round(response_time * 1000, 2),
            "status_code": status_code,
            "user_tier": user_tier
        }
        
        self.logger.info("API metrics", **metrics)
    
    def record_websocket_metrics(
        self,
        event_type: str,
        connection_count: int,
        message_size: Optional[int] = None,
        delivery_time: Optional[float] = None
    ) -> None:
        """Record WebSocket connection and message metrics."""
        metrics = {
            "metric_type": "websocket",
            "event_type": event_type,
            "connection_count": connection_count,
            "message_size_bytes": message_size,
            "delivery_time_ms": round(delivery_time * 1000, 2) if delivery_time else None
        }
        
        self.logger.info("WebSocket metrics", **metrics)
    
    def record_database_metrics(
        self,
        operation: str,
        table: str,
        query_time: float,
        rows_affected: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """Record database operation metrics."""
        metrics = {
            "metric_type": "database",
            "operation": operation,
            "table": table,
            "query_time_ms": round(query_time * 1000, 2),
            "rows_affected": rows_affected,
            "error": error
        }
        
        if error:
            self.logger.error("Database operation failed", **metrics)
        else:
            self.logger.info("Database operation completed", **metrics)


# Global instances
request_logger = RequestLogger()
error_tracker = ErrorTracker()
metrics_collector = MetricsCollector()