"""System monitoring and alerting service."""

import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.utils.logging import get_logger, error_tracker, metrics_collector
from app.config import get_settings


logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of system alerts."""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    DISK_HIGH = "disk_high"
    RESPONSE_TIME_HIGH = "response_time_high"
    ERROR_RATE_HIGH = "error_rate_high"
    PREDICTION_FAILURE = "prediction_failure"
    DATABASE_CONNECTION = "database_connection"
    EXTERNAL_SERVICE = "external_service"
    WEBSOCKET_CONNECTIONS = "websocket_connections"


@dataclass
class Alert:
    """System alert data structure."""
    id: str
    type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()


@dataclass
class MonitoringThresholds:
    """System monitoring thresholds."""
    cpu_warning: float = 70.0  # CPU usage percentage
    cpu_critical: float = 90.0
    memory_warning: float = 80.0  # Memory usage percentage
    memory_critical: float = 95.0
    disk_warning: float = 85.0  # Disk usage percentage
    disk_critical: float = 95.0
    response_time_warning: float = 1.0  # Response time in seconds
    response_time_critical: float = 3.0
    error_rate_warning: float = 5.0  # Error rate percentage
    error_rate_critical: float = 10.0
    prediction_failure_threshold: int = 3  # Consecutive failures
    websocket_connection_limit: int = 1000  # Max WebSocket connections


class SystemMonitor:
    """System performance and health monitor."""
    
    def __init__(self, thresholds: Optional[MonitoringThresholds] = None):
        self.thresholds = thresholds or MonitoringThresholds()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add callback function to be called when alerts are triggered."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Remove alert callback function."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    async def start_monitoring(self, interval: int = 60) -> None:
        """Start continuous system monitoring."""
        if self._is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
        logger.info(f"Started system monitoring with {interval}s interval")
    
    async def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped system monitoring")
    
    async def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                await self.check_system_health()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", exception=e)
                await asyncio.sleep(interval)
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        start_time = time.time()
        
        try:
            # Collect system metrics
            metrics = await self._collect_system_metrics()
            
            # Store metrics history (keep last 1000 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
            
            # Check thresholds and trigger alerts
            await self._check_thresholds(metrics)
            
            # Record monitoring metrics
            monitoring_time = time.time() - start_time
            metrics_collector.record_database_metrics(
                operation="health_check",
                table="system_monitoring",
                query_time=monitoring_time
            )
            
            return metrics
            
        except Exception as e:
            error_tracker.track_error(
                error=e,
                context={"operation": "system_health_check"},
                severity="error"
            )
            raise
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = list(os.getloadavg()) if hasattr(os, 'getloadavg') else None
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Process metrics
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except Exception:
                network_stats = None
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": load_avg
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
                    "connections": len(process.connections()) if hasattr(process, 'connections') else 0
                },
                "network": network_stats
            }
            
        except Exception as e:
            logger.error("Failed to collect system metrics", exception=e)
            raise
    
    async def _check_thresholds(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against thresholds and trigger alerts."""
        current_time = datetime.utcnow()
        
        # Check CPU usage
        cpu_usage = metrics["cpu"]["usage_percent"]
        if cpu_usage >= self.thresholds.cpu_critical:
            await self._trigger_alert(
                AlertType.CPU_HIGH,
                AlertSeverity.CRITICAL,
                f"Critical CPU usage: {cpu_usage:.1f}%",
                {"cpu_usage": cpu_usage}
            )
        elif cpu_usage >= self.thresholds.cpu_warning:
            await self._trigger_alert(
                AlertType.CPU_HIGH,
                AlertSeverity.WARNING,
                f"High CPU usage: {cpu_usage:.1f}%",
                {"cpu_usage": cpu_usage}
            )
        else:
            await self._resolve_alert(AlertType.CPU_HIGH)
        
        # Check memory usage
        memory_usage = metrics["memory"]["usage_percent"]
        if memory_usage >= self.thresholds.memory_critical:
            await self._trigger_alert(
                AlertType.MEMORY_HIGH,
                AlertSeverity.CRITICAL,
                f"Critical memory usage: {memory_usage:.1f}%",
                {"memory_usage": memory_usage}
            )
        elif memory_usage >= self.thresholds.memory_warning:
            await self._trigger_alert(
                AlertType.MEMORY_HIGH,
                AlertSeverity.WARNING,
                f"High memory usage: {memory_usage:.1f}%",
                {"memory_usage": memory_usage}
            )
        else:
            await self._resolve_alert(AlertType.MEMORY_HIGH)
        
        # Check disk usage
        disk_usage = metrics["disk"]["usage_percent"]
        if disk_usage >= self.thresholds.disk_critical:
            await self._trigger_alert(
                AlertType.DISK_HIGH,
                AlertSeverity.CRITICAL,
                f"Critical disk usage: {disk_usage:.1f}%",
                {"disk_usage": disk_usage}
            )
        elif disk_usage >= self.thresholds.disk_warning:
            await self._trigger_alert(
                AlertType.DISK_HIGH,
                AlertSeverity.WARNING,
                f"High disk usage: {disk_usage:.1f}%",
                {"disk_usage": disk_usage}
            )
        else:
            await self._resolve_alert(AlertType.DISK_HIGH)
    
    async def _trigger_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Trigger a system alert."""
        alert_key = f"{alert_type.value}_{severity.value}"
        
        # Check if alert already exists
        if alert_key in self.active_alerts:
            # Update existing alert
            self.active_alerts[alert_key].timestamp = datetime.utcnow()
            self.active_alerts[alert_key].metadata.update(metadata)
            return
        
        # Create new alert
        alert = Alert(
            id=f"alert_{int(time.time())}_{alert_type.value}",
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # Keep alert history limited
        if len(self.alert_history) > 1000:
            self.alert_history.pop(0)
        
        # Log alert
        if severity == AlertSeverity.CRITICAL:
            logger.critical(f"System alert: {message}", **metadata)
        elif severity == AlertSeverity.ERROR:
            logger.error(f"System alert: {message}", **metadata)
        elif severity == AlertSeverity.WARNING:
            logger.warning(f"System alert: {message}", **metadata)
        else:
            logger.info(f"System alert: {message}", **metadata)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error("Error in alert callback", exception=e)
    
    async def _resolve_alert(self, alert_type: AlertType) -> None:
        """Resolve alerts of a specific type."""
        keys_to_remove = []
        for key, alert in self.active_alerts.items():
            if alert.type == alert_type and not alert.resolved:
                alert.resolve()
                keys_to_remove.append(key)
                logger.info(f"Resolved alert: {alert.message}")
        
        for key in keys_to_remove:
            del self.active_alerts[key]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return self.alert_history[-limit:]
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metrics history."""
        return self.metrics_history[-limit:]
    
    async def trigger_custom_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Trigger a custom alert."""
        await self._trigger_alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata or {}
        )


class AlertingService:
    """Service for managing system alerts and notifications."""
    
    def __init__(self):
        self.monitor = SystemMonitor()
        self.notification_handlers: Dict[str, Callable[[Alert], None]] = {}
    
    def add_notification_handler(
        self,
        name: str,
        handler: Callable[[Alert], None]
    ) -> None:
        """Add notification handler for alerts."""
        self.notification_handlers[name] = handler
        self.monitor.add_alert_callback(handler)
    
    def remove_notification_handler(self, name: str) -> None:
        """Remove notification handler."""
        if name in self.notification_handlers:
            handler = self.notification_handlers.pop(name)
            self.monitor.remove_alert_callback(handler)
    
    async def start(self, monitoring_interval: int = 60) -> None:
        """Start the alerting service."""
        await self.monitor.start_monitoring(monitoring_interval)
        logger.info("Alerting service started")
    
    async def stop(self) -> None:
        """Stop the alerting service."""
        await self.monitor.stop_monitoring()
        logger.info("Alerting service stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        active_alerts = self.monitor.get_active_alerts()
        recent_metrics = self.monitor.get_metrics_history(1)
        
        # Determine overall status
        if any(alert.severity == AlertSeverity.CRITICAL for alert in active_alerts):
            status = "critical"
        elif any(alert.severity == AlertSeverity.ERROR for alert in active_alerts):
            status = "error"
        elif any(alert.severity == AlertSeverity.WARNING for alert in active_alerts):
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "active_alerts": len(active_alerts),
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat() + "Z"
                }
                for alert in active_alerts
            ],
            "current_metrics": recent_metrics[0] if recent_metrics else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# Default notification handlers
def log_alert_handler(alert: Alert) -> None:
    """Default alert handler that logs to structured logging."""
    logger.info(
        "Alert notification",
        alert_id=alert.id,
        alert_type=alert.type.value,
        severity=alert.severity.value,
        message=alert.message,
        metadata=alert.metadata
    )


def console_alert_handler(alert: Alert) -> None:
    """Console alert handler for development."""
    print(f"🚨 ALERT [{alert.severity.value.upper()}]: {alert.message}")
    if alert.metadata:
        print(f"   Metadata: {alert.metadata}")


# Global alerting service instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """Get or create the global alerting service instance."""
    global _alerting_service
    
    if _alerting_service is None:
        _alerting_service = AlertingService()
        
        # Add default notification handlers
        _alerting_service.add_notification_handler("log", log_alert_handler)
        
        # Add console handler in development
        settings = get_settings()
        if settings.environment == "development":
            _alerting_service.add_notification_handler("console", console_alert_handler)
    
    return _alerting_service


async def initialize_monitoring() -> None:
    """Initialize the monitoring system."""
    alerting_service = get_alerting_service()
    await alerting_service.start()


async def shutdown_monitoring() -> None:
    """Shutdown the monitoring system."""
    global _alerting_service
    
    if _alerting_service:
        await _alerting_service.stop()
        _alerting_service = None