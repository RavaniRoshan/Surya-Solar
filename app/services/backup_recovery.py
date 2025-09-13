"""Automated backup and recovery service."""

import asyncio
import os
import shutil
import gzip
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from app.utils.logging import get_logger, error_tracker
from app.config import get_settings


logger = get_logger(__name__)


class BackupType(str, Enum):
    """Types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    CONFIGURATION = "configuration"
    LOGS = "logs"


class BackupStatus(str, Enum):
    """Backup operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupRecord:
    """Record of a backup operation."""
    id: str
    backup_type: BackupType
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BackupService:
    """Service for automated backup and recovery operations."""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_history: List[BackupRecord] = []
        self._backup_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_scheduled_backups(
        self,
        interval_hours: int = 24,
        retention_days: int = 30
    ) -> None:
        """Start scheduled backup operations."""
        if self._is_running:
            logger.warning("Backup service already running")
            return
        
        self._is_running = True
        self._backup_task = asyncio.create_task(
            self._backup_loop(interval_hours, retention_days)
        )
        logger.info(f"Started scheduled backups every {interval_hours} hours")
    
    async def stop_scheduled_backups(self) -> None:
        """Stop scheduled backup operations."""
        self._is_running = False
        if self._backup_task:
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped scheduled backups")
    
    async def _backup_loop(self, interval_hours: int, retention_days: int) -> None:
        """Main backup scheduling loop."""
        while self._is_running:
            try:
                # Perform backup
                await self.create_full_backup()
                
                # Clean up old backups
                await self.cleanup_old_backups(retention_days)
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in backup loop", exception=e)
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def create_full_backup(self) -> BackupRecord:
        """Create a full system backup."""
        backup_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        record = BackupRecord(
            id=backup_id,
            backup_type=BackupType.FULL,
            status=BackupStatus.PENDING,
            start_time=datetime.utcnow()
        )
        
        self.backup_history.append(record)
        
        try:
            record.status = BackupStatus.RUNNING
            logger.info(f"Starting full backup: {backup_id}")
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            await self._backup_configuration(backup_path)
            
            # Backup application logs
            await self._backup_logs(backup_path)
            
            # Backup database schema and critical data
            await self._backup_database_schema(backup_path)
            
            # Create backup manifest
            await self._create_backup_manifest(backup_path, record)
            
            # Compress backup
            compressed_path = await self._compress_backup(backup_path)
            
            # Update record
            record.status = BackupStatus.COMPLETED
            record.end_time = datetime.utcnow()
            record.file_path = str(compressed_path)
            record.file_size_bytes = compressed_path.stat().st_size if compressed_path.exists() else 0
            
            logger.info(f"Full backup completed: {backup_id}")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.end_time = datetime.utcnow()
            record.error_message = str(e)
            
            error_tracker.track_error(
                error=e,
                context={"backup_id": backup_id, "backup_type": "full"},
                severity="error"
            )
            
            logger.error(f"Full backup failed: {backup_id}", exception=e)
        
        return record
    
    async def create_configuration_backup(self) -> BackupRecord:
        """Create a backup of configuration files only."""
        backup_id = f"config_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        record = BackupRecord(
            id=backup_id,
            backup_type=BackupType.CONFIGURATION,
            status=BackupStatus.PENDING,
            start_time=datetime.utcnow()
        )
        
        self.backup_history.append(record)
        
        try:
            record.status = BackupStatus.RUNNING
            logger.info(f"Starting configuration backup: {backup_id}")
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            await self._backup_configuration(backup_path)
            
            # Create manifest
            await self._create_backup_manifest(backup_path, record)
            
            # Compress backup
            compressed_path = await self._compress_backup(backup_path)
            
            # Update record
            record.status = BackupStatus.COMPLETED
            record.end_time = datetime.utcnow()
            record.file_path = str(compressed_path)
            record.file_size_bytes = compressed_path.stat().st_size if compressed_path.exists() else 0
            
            logger.info(f"Configuration backup completed: {backup_id}")
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.end_time = datetime.utcnow()
            record.error_message = str(e)
            
            error_tracker.track_error(
                error=e,
                context={"backup_id": backup_id, "backup_type": "configuration"},
                severity="error"
            )
            
            logger.error(f"Configuration backup failed: {backup_id}", exception=e)
        
        return record
    
    async def _backup_configuration(self, backup_path: Path) -> None:
        """Backup configuration files."""
        config_dir = backup_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Backup environment files
        env_files = [".env", ".env.example", ".env.local"]
        for env_file in env_files:
            if Path(env_file).exists():
                shutil.copy2(env_file, config_dir / env_file)
        
        # Backup application configuration
        app_config = {
            "settings": get_settings().model_dump(),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        with open(config_dir / "app_config.json", "w") as f:
            json.dump(app_config, f, indent=2, default=str)
        
        # Backup requirements
        if Path("requirements.txt").exists():
            shutil.copy2("requirements.txt", config_dir / "requirements.txt")
        
        logger.debug("Configuration backup completed")
    
    async def _backup_logs(self, backup_path: Path) -> None:
        """Backup application logs."""
        logs_dir = backup_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Backup log files if they exist
        log_patterns = ["*.log", "logs/*.log", "app.log"]
        
        for pattern in log_patterns:
            for log_file in Path(".").glob(pattern):
                if log_file.is_file():
                    shutil.copy2(log_file, logs_dir / log_file.name)
        
        logger.debug("Logs backup completed")
    
    async def _backup_database_schema(self, backup_path: Path) -> None:
        """Backup database schema and critical data."""
        db_dir = backup_path / "database"
        db_dir.mkdir(exist_ok=True)
        
        # Backup database schema file
        if Path("database/schema.sql").exists():
            shutil.copy2("database/schema.sql", db_dir / "schema.sql")
        
        # Backup migration files
        migrations_dir = Path("database/migrations")
        if migrations_dir.exists():
            backup_migrations_dir = db_dir / "migrations"
            shutil.copytree(migrations_dir, backup_migrations_dir, dirs_exist_ok=True)
        
        # Note: In a real implementation, you would also backup actual database data
        # This would involve connecting to Supabase and exporting critical tables
        
        logger.debug("Database schema backup completed")
    
    async def _create_backup_manifest(self, backup_path: Path, record: BackupRecord) -> None:
        """Create a manifest file for the backup."""
        manifest = {
            "backup_id": record.id,
            "backup_type": record.backup_type.value,
            "created_at": record.start_time.isoformat(),
            "version": "1.0.0",
            "files": []
        }
        
        # List all files in backup
        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(backup_path)
                manifest["files"].append({
                    "path": str(relative_path),
                    "size_bytes": file_path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        with open(backup_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.debug("Backup manifest created")
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory."""
        compressed_path = backup_path.with_suffix(".tar.gz")
        
        # Create compressed archive
        shutil.make_archive(
            str(backup_path),
            "gztar",
            root_dir=backup_path.parent,
            base_dir=backup_path.name
        )
        
        # Remove uncompressed directory
        shutil.rmtree(backup_path)
        
        logger.debug(f"Backup compressed: {compressed_path}")
        return compressed_path
    
    async def cleanup_old_backups(self, retention_days: int) -> None:
        """Clean up old backup files."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        removed_count = 0
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                # Extract date from filename
                file_date_str = backup_file.stem.split("_", 1)[1]  # Remove type prefix
                file_date = datetime.strptime(file_date_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old backup: {backup_file.name}")
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse backup file date: {backup_file.name}", exception=e)
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backup files")
    
    async def restore_from_backup(self, backup_id: str, restore_path: str = "./restore") -> bool:
        """Restore system from a backup."""
        try:
            backup_file = self.backup_dir / f"{backup_id}.tar.gz"
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            restore_dir = Path(restore_path)
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            shutil.unpack_archive(str(backup_file), str(restore_dir))
            
            logger.info(f"Backup restored to: {restore_dir}")
            return True
            
        except Exception as e:
            error_tracker.track_error(
                error=e,
                context={"backup_id": backup_id, "restore_path": restore_path},
                severity="error"
            )
            logger.error(f"Restore failed for backup: {backup_id}", exception=e)
            return False
    
    def get_backup_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get backup history."""
        return [
            {
                "id": record.id,
                "backup_type": record.backup_type.value,
                "status": record.status.value,
                "start_time": record.start_time.isoformat(),
                "end_time": record.end_time.isoformat() if record.end_time else None,
                "file_path": record.file_path,
                "file_size_bytes": record.file_size_bytes,
                "error_message": record.error_message,
                "metadata": record.metadata
            }
            for record in self.backup_history[-limit:]
        ]
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup service status."""
        recent_backups = self.backup_history[-10:] if self.backup_history else []
        
        return {
            "service_running": self._is_running,
            "total_backups": len(self.backup_history),
            "recent_backups": len(recent_backups),
            "last_backup": recent_backups[-1].start_time.isoformat() if recent_backups else None,
            "backup_directory": str(self.backup_dir),
            "disk_usage_bytes": sum(
                f.stat().st_size for f in self.backup_dir.glob("*.tar.gz") if f.is_file()
            )
        }


# Global backup service instance
_backup_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    """Get or create the global backup service instance."""
    global _backup_service
    
    if _backup_service is None:
        settings = get_settings()
        backup_dir = getattr(settings, 'backup_directory', './backups')
        _backup_service = BackupService(backup_dir)
    
    return _backup_service


async def initialize_backup_service() -> None:
    """Initialize the backup service."""
    backup_service = get_backup_service()
    await backup_service.start_scheduled_backups(
        interval_hours=24,  # Daily backups
        retention_days=30   # Keep backups for 30 days
    )


async def shutdown_backup_service() -> None:
    """Shutdown the backup service."""
    global _backup_service
    
    if _backup_service:
        await _backup_service.stop_scheduled_backups()
        _backup_service = None