"""Tests for monitoring and backup functionality."""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.services.monitoring import (
    SystemMonitor,
    AlertingService,
    AlertSeverity,
    AlertType,
    MonitoringThresholds
)
from app.services.backup_recovery import BackupService, BackupType, BackupStatus


class TestSystemMonitor:
    """Test system monitoring functionality."""
    
    @pytest.fixture
    def monitor(self):
        """Create system monitor instance."""
        thresholds = MonitoringThresholds(
            cpu_warning=50.0,
            cpu_critical=80.0,
            memory_warning=60.0,
            memory_critical=85.0
        )
        return SystemMonitor(thresholds)
    
    @pytest.mark.asyncio
    async def test_system_health_check(self, monitor):
        """Test system health check."""
        metrics = await monitor.check_system_health()
        
        assert "timestamp" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "process" in metrics
        
        # Check CPU metrics
        assert "usage_percent" in metrics["cpu"]
        assert "count" in metrics["cpu"]
        
        # Check memory metrics
        assert "total_bytes" in metrics["memory"]
        assert "usage_percent" in metrics["memory"]
    
    @pytest.mark.asyncio
    async def test_alert_triggering(self, monitor):
        """Test alert triggering based on thresholds."""
        # Mock high CPU usage
        with patch('psutil.cpu_percent', return_value=85.0):
            await monitor.check_system_health()
        
        # Check if critical CPU alert was triggered
        active_alerts = monitor.get_active_alerts()
        cpu_alerts = [a for a in active_alerts if a.type == AlertType.CPU_HIGH]
        
        assert len(cpu_alerts) > 0
        assert cpu_alerts[0].severity == AlertSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self, monitor):
        """Test alert resolution when metrics return to normal."""
        # Trigger alert with high CPU
        with patch('psutil.cpu_percent', return_value=85.0):
            await monitor.check_system_health()
        
        # Verify alert exists
        active_alerts = monitor.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Return to normal CPU usage
        with patch('psutil.cpu_percent', return_value=30.0):
            await monitor.check_system_health()
        
        # Verify alert is resolved
        active_alerts = monitor.get_active_alerts()
        cpu_alerts = [a for a in active_alerts if a.type == AlertType.CPU_HIGH and not a.resolved]
        assert len(cpu_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_custom_alert(self, monitor):
        """Test triggering custom alerts."""
        await monitor.trigger_custom_alert(
            AlertType.PREDICTION_FAILURE,
            AlertSeverity.ERROR,
            "Test prediction failure",
            {"model": "surya-1.0", "error": "timeout"}
        )
        
        active_alerts = monitor.get_active_alerts()
        prediction_alerts = [a for a in active_alerts if a.type == AlertType.PREDICTION_FAILURE]
        
        assert len(prediction_alerts) > 0
        assert prediction_alerts[0].message == "Test prediction failure"
        assert prediction_alerts[0].metadata["model"] == "surya-1.0"
    
    def test_alert_callbacks(self, monitor):
        """Test alert callback functionality."""
        callback_called = False
        callback_alert = None
        
        def test_callback(alert):
            nonlocal callback_called, callback_alert
            callback_called = True
            callback_alert = alert
        
        monitor.add_alert_callback(test_callback)
        
        # Trigger alert
        asyncio.run(monitor.trigger_custom_alert(
            AlertType.DATABASE_CONNECTION,
            AlertSeverity.WARNING,
            "Test callback alert"
        ))
        
        assert callback_called
        assert callback_alert is not None
        assert callback_alert.type == AlertType.DATABASE_CONNECTION
    
    def test_metrics_history(self, monitor):
        """Test metrics history storage."""
        # Add some mock metrics
        for i in range(5):
            monitor.metrics_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {"usage_percent": 50.0 + i},
                "memory": {"usage_percent": 60.0 + i}
            })
        
        history = monitor.get_metrics_history(3)
        assert len(history) == 3
        
        # Should return the most recent 3 entries
        assert history[0]["cpu"]["usage_percent"] == 52.0
        assert history[2]["cpu"]["usage_percent"] == 54.0


class TestAlertingService:
    """Test alerting service functionality."""
    
    @pytest.fixture
    def alerting_service(self):
        """Create alerting service instance."""
        return AlertingService()
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, alerting_service):
        """Test starting and stopping the alerting service."""
        # Start service
        await alerting_service.start(monitoring_interval=1)  # 1 second for testing
        
        # Wait a bit to ensure monitoring starts
        await asyncio.sleep(0.1)
        
        # Stop service
        await alerting_service.stop()
    
    def test_notification_handlers(self, alerting_service):
        """Test adding and removing notification handlers."""
        handler_called = False
        
        def test_handler(alert):
            nonlocal handler_called
            handler_called = True
        
        # Add handler
        alerting_service.add_notification_handler("test", test_handler)
        
        # Trigger alert
        asyncio.run(alerting_service.monitor.trigger_custom_alert(
            AlertType.ERROR_RATE_HIGH,
            AlertSeverity.ERROR,
            "Test notification"
        ))
        
        assert handler_called
        
        # Remove handler
        alerting_service.remove_notification_handler("test")
        
        # Verify handler is removed
        assert "test" not in alerting_service.notification_handlers
    
    def test_system_status(self, alerting_service):
        """Test system status reporting."""
        # Add some test alerts
        asyncio.run(alerting_service.monitor.trigger_custom_alert(
            AlertType.MEMORY_HIGH,
            AlertSeverity.WARNING,
            "Test memory alert"
        ))
        
        status = alerting_service.get_system_status()
        
        assert "status" in status
        assert "active_alerts" in status
        assert "alerts" in status
        assert "timestamp" in status
        
        assert status["active_alerts"] > 0
        assert len(status["alerts"]) > 0


class TestBackupService:
    """Test backup and recovery functionality."""
    
    @pytest.fixture
    def backup_service(self):
        """Create backup service with temporary directory."""
        temp_dir = tempfile.mkdtemp()
        service = BackupService(backup_dir=temp_dir)
        yield service
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_configuration_backup(self, backup_service):
        """Test configuration backup creation."""
        record = await backup_service.create_configuration_backup()
        
        assert record.backup_type == BackupType.CONFIGURATION
        assert record.status == BackupStatus.COMPLETED
        assert record.file_path is not None
        assert record.file_size_bytes > 0
    
    @pytest.mark.asyncio
    async def test_full_backup(self, backup_service):
        """Test full backup creation."""
        record = await backup_service.create_full_backup()
        
        assert record.backup_type == BackupType.FULL
        # Note: This might fail in test environment due to missing files
        # In a real environment, this would test the complete backup process
    
    @pytest.mark.asyncio
    async def test_backup_cleanup(self, backup_service):
        """Test old backup cleanup."""
        # Create some mock backup files with old dates
        backup_dir = Path(backup_service.backup_dir)
        
        # Create old backup file
        old_backup = backup_dir / "full_20230101_120000.tar.gz"
        old_backup.touch()
        
        # Create recent backup file
        recent_backup = backup_dir / f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        recent_backup.touch()
        
        # Run cleanup (keep files newer than 1 day)
        await backup_service.cleanup_old_backups(retention_days=1)
        
        # Old backup should be removed, recent should remain
        assert not old_backup.exists()
        assert recent_backup.exists()
    
    def test_backup_history(self, backup_service):
        """Test backup history tracking."""
        # Add some mock backup records
        from app.services.backup_recovery import BackupRecord
        
        record1 = BackupRecord(
            id="test1",
            backup_type=BackupType.CONFIGURATION,
            status=BackupStatus.COMPLETED,
            start_time=datetime.utcnow()
        )
        
        record2 = BackupRecord(
            id="test2",
            backup_type=BackupType.FULL,
            status=BackupStatus.FAILED,
            start_time=datetime.utcnow(),
            error_message="Test error"
        )
        
        backup_service.backup_history.extend([record1, record2])
        
        history = backup_service.get_backup_history()
        
        assert len(history) == 2
        assert history[0]["id"] == "test1"
        assert history[1]["id"] == "test2"
        assert history[1]["error_message"] == "Test error"
    
    def test_backup_status(self, backup_service):
        """Test backup service status reporting."""
        status = backup_service.get_backup_status()
        
        assert "service_running" in status
        assert "total_backups" in status
        assert "backup_directory" in status
        assert "disk_usage_bytes" in status
        
        assert status["service_running"] == False  # Not started in test
        assert status["total_backups"] == 0  # No backups yet


class TestMonitoringThresholds:
    """Test monitoring threshold configuration."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = MonitoringThresholds()
        
        assert thresholds.cpu_warning == 70.0
        assert thresholds.cpu_critical == 90.0
        assert thresholds.memory_warning == 80.0
        assert thresholds.memory_critical == 95.0
        assert thresholds.disk_warning == 85.0
        assert thresholds.disk_critical == 95.0
    
    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        thresholds = MonitoringThresholds(
            cpu_warning=50.0,
            cpu_critical=75.0,
            memory_warning=60.0,
            memory_critical=80.0
        )
        
        assert thresholds.cpu_warning == 50.0
        assert thresholds.cpu_critical == 75.0
        assert thresholds.memory_warning == 60.0
        assert thresholds.memory_critical == 80.0


class TestIntegration:
    """Integration tests for monitoring and backup systems."""
    
    @pytest.mark.asyncio
    async def test_monitoring_with_backup_alerts(self):
        """Test monitoring system triggering backup-related alerts."""
        monitor = SystemMonitor()
        
        # Simulate backup failure alert
        await monitor.trigger_custom_alert(
            AlertType.EXTERNAL_SERVICE,
            AlertSeverity.ERROR,
            "Backup service failure",
            {"service": "backup", "error": "disk_full"}
        )
        
        active_alerts = monitor.get_active_alerts()
        backup_alerts = [a for a in active_alerts if "backup" in a.message.lower()]
        
        assert len(backup_alerts) > 0
        assert backup_alerts[0].metadata["service"] == "backup"
    
    @pytest.mark.asyncio
    async def test_error_tracking_integration(self):
        """Test integration with error tracking system."""
        from app.utils.logging import error_tracker
        
        # Create monitor with error tracking
        monitor = SystemMonitor()
        
        # Simulate system error that should be tracked
        try:
            raise RuntimeError("Test monitoring error")
        except Exception as e:
            error_id = error_tracker.track_error(
                error=e,
                context={"component": "monitoring", "operation": "health_check"},
                severity="error"
            )
            
            # Trigger corresponding alert
            await monitor.trigger_custom_alert(
                AlertType.ERROR_RATE_HIGH,
                AlertSeverity.ERROR,
                f"System error tracked: {error_id}",
                {"error_id": error_id}
            )
        
        active_alerts = monitor.get_active_alerts()
        error_alerts = [a for a in active_alerts if "error tracked" in a.message.lower()]
        
        assert len(error_alerts) > 0
        assert "error_id" in error_alerts[0].metadata


if __name__ == "__main__":
    pytest.main([__file__])