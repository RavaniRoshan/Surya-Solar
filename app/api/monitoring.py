"""Monitoring and alerting API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.monitoring import get_alerting_service, AlertSeverity, AlertType
from app.models.core import SystemMetrics
from app.utils.logging import get_logger

router = APIRouter(prefix="/monitoring", tags=["Monitoring & Alerting"])
logger = get_logger(__name__)


@router.get("/status")
async def get_system_status():
    """Get overall system status and active alerts."""
    alerting_service = get_alerting_service()
    return alerting_service.get_system_status()


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(False, description="Return only active alerts"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return")
):
    """Get system alerts with optional filtering."""
    alerting_service = get_alerting_service()
    
    if active_only:
        alerts = alerting_service.monitor.get_active_alerts()
    else:
        alerts = alerting_service.monitor.get_alert_history(limit)
    
    # Apply filters
    if severity:
        alerts = [alert for alert in alerts if alert.severity == severity]
    
    if alert_type:
        alerts = [alert for alert in alerts if alert.type == alert_type]
    
    # Convert to response format
    return {
        "alerts": [
            {
                "id": alert.id,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat() + "Z",
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() + "Z" if alert.resolved_at else None,
                "metadata": alert.metadata
            }
            for alert in alerts
        ],
        "total_count": len(alerts),
        "active_count": len([a for a in alerts if not a.resolved])
    }


@router.post("/alerts/custom")
async def trigger_custom_alert(
    alert_type: AlertType,
    severity: AlertSeverity,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Trigger a custom alert (for testing or manual alerts)."""
    alerting_service = get_alerting_service()
    
    await alerting_service.monitor.trigger_custom_alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        metadata=metadata
    )
    
    return {
        "message": "Alert triggered successfully",
        "alert_type": alert_type.value,
        "severity": severity.value
    }


@router.get("/metrics/current")
async def get_current_metrics():
    """Get current system performance metrics."""
    alerting_service = get_alerting_service()
    metrics = await alerting_service.monitor.check_system_health()
    return metrics


@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(1, ge=1, le=24, description="Number of hours of history to return"),
    resolution: int = Query(60, ge=30, le=3600, description="Resolution in seconds")
):
    """Get historical system metrics."""
    alerting_service = get_alerting_service()
    
    # Get all metrics history
    all_metrics = alerting_service.monitor.get_metrics_history(1000)
    
    if not all_metrics:
        return {"metrics": [], "total_count": 0}
    
    # Filter by time range
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    filtered_metrics = []
    
    for metric in all_metrics:
        try:
            metric_time = datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00"))
            if metric_time >= cutoff_time:
                filtered_metrics.append(metric)
        except (KeyError, ValueError):
            continue
    
    # Apply resolution (downsample if needed)
    if len(filtered_metrics) > 100:  # Downsample if too many points
        step = max(1, len(filtered_metrics) // 100)
        filtered_metrics = filtered_metrics[::step]
    
    return {
        "metrics": filtered_metrics,
        "total_count": len(filtered_metrics),
        "time_range_hours": hours,
        "resolution_seconds": resolution
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = Query(24, ge=1, le=168, description="Number of hours for summary")
):
    """Get summarized metrics over a time period."""
    alerting_service = get_alerting_service()
    
    # Get metrics history
    all_metrics = alerting_service.monitor.get_metrics_history(1000)
    
    if not all_metrics:
        return {"summary": {}, "period_hours": hours}
    
    # Filter by time range
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    filtered_metrics = []
    
    for metric in all_metrics:
        try:
            metric_time = datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00"))
            if metric_time >= cutoff_time:
                filtered_metrics.append(metric)
        except (KeyError, ValueError):
            continue
    
    if not filtered_metrics:
        return {"summary": {}, "period_hours": hours}
    
    # Calculate summary statistics
    cpu_values = [m["cpu"]["usage_percent"] for m in filtered_metrics if "cpu" in m]
    memory_values = [m["memory"]["usage_percent"] for m in filtered_metrics if "memory" in m]
    disk_values = [m["disk"]["usage_percent"] for m in filtered_metrics if "disk" in m]
    
    summary = {
        "cpu": {
            "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            "min": min(cpu_values) if cpu_values else 0,
            "max": max(cpu_values) if cpu_values else 0
        },
        "memory": {
            "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
            "min": min(memory_values) if memory_values else 0,
            "max": max(memory_values) if memory_values else 0
        },
        "disk": {
            "avg": sum(disk_values) / len(disk_values) if disk_values else 0,
            "min": min(disk_values) if disk_values else 0,
            "max": max(disk_values) if disk_values else 0
        },
        "data_points": len(filtered_metrics),
        "period_start": filtered_metrics[0]["timestamp"] if filtered_metrics else None,
        "period_end": filtered_metrics[-1]["timestamp"] if filtered_metrics else None
    }
    
    return {
        "summary": summary,
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/thresholds")
async def get_monitoring_thresholds():
    """Get current monitoring thresholds."""
    alerting_service = get_alerting_service()
    thresholds = alerting_service.monitor.thresholds
    
    return {
        "cpu_warning": thresholds.cpu_warning,
        "cpu_critical": thresholds.cpu_critical,
        "memory_warning": thresholds.memory_warning,
        "memory_critical": thresholds.memory_critical,
        "disk_warning": thresholds.disk_warning,
        "disk_critical": thresholds.disk_critical,
        "response_time_warning": thresholds.response_time_warning,
        "response_time_critical": thresholds.response_time_critical,
        "error_rate_warning": thresholds.error_rate_warning,
        "error_rate_critical": thresholds.error_rate_critical,
        "prediction_failure_threshold": thresholds.prediction_failure_threshold,
        "websocket_connection_limit": thresholds.websocket_connection_limit
    }


@router.put("/thresholds")
async def update_monitoring_thresholds(
    cpu_warning: Optional[float] = None,
    cpu_critical: Optional[float] = None,
    memory_warning: Optional[float] = None,
    memory_critical: Optional[float] = None,
    disk_warning: Optional[float] = None,
    disk_critical: Optional[float] = None,
    response_time_warning: Optional[float] = None,
    response_time_critical: Optional[float] = None,
    error_rate_warning: Optional[float] = None,
    error_rate_critical: Optional[float] = None,
    prediction_failure_threshold: Optional[int] = None,
    websocket_connection_limit: Optional[int] = None
):
    """Update monitoring thresholds."""
    alerting_service = get_alerting_service()
    thresholds = alerting_service.monitor.thresholds
    
    # Update provided thresholds
    if cpu_warning is not None:
        thresholds.cpu_warning = cpu_warning
    if cpu_critical is not None:
        thresholds.cpu_critical = cpu_critical
    if memory_warning is not None:
        thresholds.memory_warning = memory_warning
    if memory_critical is not None:
        thresholds.memory_critical = memory_critical
    if disk_warning is not None:
        thresholds.disk_warning = disk_warning
    if disk_critical is not None:
        thresholds.disk_critical = disk_critical
    if response_time_warning is not None:
        thresholds.response_time_warning = response_time_warning
    if response_time_critical is not None:
        thresholds.response_time_critical = response_time_critical
    if error_rate_warning is not None:
        thresholds.error_rate_warning = error_rate_warning
    if error_rate_critical is not None:
        thresholds.error_rate_critical = error_rate_critical
    if prediction_failure_threshold is not None:
        thresholds.prediction_failure_threshold = prediction_failure_threshold
    if websocket_connection_limit is not None:
        thresholds.websocket_connection_limit = websocket_connection_limit
    
    logger.info("Monitoring thresholds updated")
    
    return {
        "message": "Thresholds updated successfully",
        "thresholds": {
            "cpu_warning": thresholds.cpu_warning,
            "cpu_critical": thresholds.cpu_critical,
            "memory_warning": thresholds.memory_warning,
            "memory_critical": thresholds.memory_critical,
            "disk_warning": thresholds.disk_warning,
            "disk_critical": thresholds.disk_critical,
            "response_time_warning": thresholds.response_time_warning,
            "response_time_critical": thresholds.response_time_critical,
            "error_rate_warning": thresholds.error_rate_warning,
            "error_rate_critical": thresholds.error_rate_critical,
            "prediction_failure_threshold": thresholds.prediction_failure_threshold,
            "websocket_connection_limit": thresholds.websocket_connection_limit
        }
    }


@router.post("/test")
async def test_monitoring_system():
    """Test the monitoring system by triggering test alerts."""
    alerting_service = get_alerting_service()
    
    # Trigger test alerts
    await alerting_service.monitor.trigger_custom_alert(
        AlertType.CPU_HIGH,
        AlertSeverity.INFO,
        "Test alert: Monitoring system test",
        {"test": True, "timestamp": datetime.utcnow().isoformat()}
    )
    
    # Get current system metrics
    metrics = await alerting_service.monitor.check_system_health()
    
    return {
        "message": "Monitoring system test completed",
        "test_alert_triggered": True,
        "current_metrics": metrics,
        "active_alerts": len(alerting_service.monitor.get_active_alerts())
    }