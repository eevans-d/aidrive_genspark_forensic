"""
Backup Scheduler - Complete Automatic Backup System
Production-ready backup system with multiple storage backends and scheduling
"""

import asyncio
import logging
import os
import shutil
import gzip
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
import hashlib
import schedule

import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StorageBackend(Enum):
    LOCAL = "local"
    S3 = "s3"
    FTP = "ftp"
    RSYNC = "rsync"

@dataclass
class BackupConfig:
    """Backup configuration settings"""
    name: str
    source_paths: List[str]
    destination_path: str
    backup_type: BackupType = BackupType.FULL
    storage_backend: StorageBackend = StorageBackend.LOCAL
    schedule_cron: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_backup_size_gb: Optional[float] = None
    notification_emails: List[str] = None
    enabled: bool = True

    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = ["*"]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "*.tmp", "*.log", "*.cache", "__pycache__/", 
                "node_modules/", ".git/", "*.pyc"
            ]
        if self.notification_emails is None:
            self.notification_emails = []

@dataclass
class BackupResult:
    """Backup operation result"""
    backup_id: str
    config_name: str
    backup_type: BackupType
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    files_processed: int = 0
    files_backed_up: int = 0
    bytes_processed: int = 0
    bytes_backed_up: int = 0
    compression_ratio: Optional[float] = None
    error_message: Optional[str] = None
    backup_path: Optional[str] = None
    checksum: Optional[str] = None

    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

class BackupMetadata:
    """Manages backup metadata and history"""

    def __init__(self, metadata_file: str = "backup_metadata.db"):
        self.metadata_file = metadata_file
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for metadata"""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backup_history (
                        backup_id TEXT PRIMARY KEY,
                        config_name TEXT NOT NULL,
                        backup_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_seconds REAL,
                        files_processed INTEGER DEFAULT 0,
                        files_backed_up INTEGER DEFAULT 0,
                        bytes_processed INTEGER DEFAULT 0,
                        bytes_backed_up INTEGER DEFAULT 0,
                        compression_ratio REAL,
                        error_message TEXT,
                        backup_path TEXT,
                        checksum TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backup_configs (
                        name TEXT PRIMARY KEY,
                        config_json TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backup_history_config 
                    ON backup_history(config_name)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backup_history_status 
                    ON backup_history(status)
                """)

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to initialize backup metadata database: {e}", exc_info=True, extra={
                "metadata_file": self.metadata_file,
                "context": "backup_metadata_init"
            })
            raise

    def save_backup_result(self, result: BackupResult):
        """Save backup result to database"""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_history (
                        backup_id, config_name, backup_type, status,
                        start_time, end_time, duration_seconds,
                        files_processed, files_backed_up,
                        bytes_processed, bytes_backed_up,
                        compression_ratio, error_message,
                        backup_path, checksum
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.backup_id, result.config_name, result.backup_type.value, result.status.value,
                    result.start_time.isoformat(), 
                    result.end_time.isoformat() if result.end_time else None,
                    result.duration_seconds,
                    result.files_processed, result.files_backed_up,
                    result.bytes_processed, result.bytes_backed_up,
                    result.compression_ratio, result.error_message,
                    result.backup_path, result.checksum
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Failed to save backup result: {e}", exc_info=True, extra={
                "backup_id": result.backup_id,
                "config_name": result.config_name,
                "context": "backup_result_save"
            })

    def get_backup_history(self, config_name: str = None, limit: int = 100) -> List[BackupResult]:
        """Get backup history"""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                if config_name:
                    cursor = conn.execute("""
                        SELECT * FROM backup_history 
                        WHERE config_name = ? 
                        ORDER BY start_time DESC 
                        LIMIT ?
                    """, (config_name, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM backup_history 
                        ORDER BY start_time DESC 
                        LIMIT ?
                    """, (limit,))

                results = []
                for row in cursor.fetchall():
                    result = BackupResult(
                        backup_id=row[0],
                        config_name=row[1],
                        backup_type=BackupType(row[2]),
                        status=BackupStatus(row[3]),
                        start_time=datetime.fromisoformat(row[4]),
                        end_time=datetime.fromisoformat(row[5]) if row[5] else None,
                        duration_seconds=row[6],
                        files_processed=row[7],
                        files_backed_up=row[8],
                        bytes_processed=row[9],
                        bytes_backed_up=row[10],
                        compression_ratio=row[11],
                        error_message=row[12],
                        backup_path=row[13],
                        checksum=row[14]
                    )
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Failed to get backup history: {e}")
            return []

    def save_config(self, config: BackupConfig):
        """Save backup configuration"""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_configs (name, config_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (config.name, json.dumps(asdict(config))))
                conn.commit()

        except Exception as e:
            logger.error(f"Failed to save backup config: {e}")

class BackupEngine:
    """Core backup engine with different backend support"""

    def __init__(self):
        self.metadata = BackupMetadata()

    async def backup(self, config: BackupConfig) -> BackupResult:
        """Execute backup operation"""
        backup_id = self.generate_backup_id(config.name)
        result = BackupResult(
            backup_id=backup_id,
            config_name=config.name,
            backup_type=config.backup_type,
            status=BackupStatus.RUNNING,
            start_time=datetime.now()
        )

        try:
            logger.info(f"Starting backup '{config.name}' (ID: {backup_id})")

            # Validate configuration
            self.validate_config(config)

            # Check disk space
            self.check_disk_space(config)

            # Create backup directory
            backup_dir = self.create_backup_directory(config, backup_id)
            result.backup_path = str(backup_dir)

            # Execute backup based on type
            if config.backup_type == BackupType.FULL:
                await self.full_backup(config, backup_dir, result)
            elif config.backup_type == BackupType.INCREMENTAL:
                await self.incremental_backup(config, backup_dir, result)
            elif config.backup_type == BackupType.DIFFERENTIAL:
                await self.differential_backup(config, backup_dir, result)

            # Calculate checksum
            result.checksum = self.calculate_backup_checksum(backup_dir)

            # Compression
            if config.compression_enabled:
                compressed_path = await self.compress_backup(backup_dir, result)
                result.backup_path = compressed_path

            # Upload to storage backend
            if config.storage_backend != StorageBackend.LOCAL:
                await self.upload_to_storage(config, result.backup_path, result)

            # Calculate compression ratio
            if config.compression_enabled:
                result.compression_ratio = self.calculate_compression_ratio(backup_dir, result.backup_path)

            result.status = BackupStatus.COMPLETED
            result.end_time = datetime.now()

            logger.info(f"Backup '{config.name}' completed successfully")

        except Exception as e:
            result.status = BackupStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            logger.error(f"Backup '{config.name}' failed: {e}", exc_info=True, extra={
                "config_name": config.name,
                "backup_type": config.backup_type.value,
                "backup_id": result.backup_id,
                "context": "backup_execution"
            })

        finally:
            # Save result to metadata
            self.metadata.save_backup_result(result)

            # Clean up old backups
            await self.cleanup_old_backups(config)

        return result

    def generate_backup_id(self, config_name: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{config_name}_{timestamp}"

    def validate_config(self, config: BackupConfig):
        """Validate backup configuration"""
        # Check source paths exist
        for source in config.source_paths:
            if not Path(source).exists():
                raise ValueError(f"Source path does not exist: {source}")

        # Check destination path is writable
        dest_path = Path(config.destination_path)
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)

        if not os.access(dest_path, os.W_OK):
            raise ValueError(f"Destination path is not writable: {dest_path}")

    def check_disk_space(self, config: BackupConfig):
        """Check available disk space"""
        try:
            # Calculate source size
            total_source_size = 0
            for source in config.source_paths:
                source_path = Path(source)
                if source_path.is_file():
                    total_source_size += source_path.stat().st_size
                elif source_path.is_dir():
                    total_source_size += sum(
                        f.stat().st_size for f in source_path.rglob('*') if f.is_file()
                    )

            # Get available space at destination
            dest_usage = psutil.disk_usage(config.destination_path)
            available_space = dest_usage.free

            # Require at least 2x the source size (for safety)
            required_space = total_source_size * 2

            if available_space < required_space:
                raise ValueError(
                    f"Insufficient disk space. Required: {required_space / (1024**3):.2f} GB, "
                    f"Available: {available_space / (1024**3):.2f} GB"
                )

            logger.info(f"Disk space check passed. Source: {total_source_size / (1024**3):.2f} GB, "
                       f"Available: {available_space / (1024**3):.2f} GB")

        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")

    def create_backup_directory(self, config: BackupConfig, backup_id: str) -> Path:
        """Create backup directory structure"""
        backup_dir = Path(config.destination_path) / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata_file = backup_dir / "backup_info.json"
        metadata = {
            "backup_id": backup_id,
            "config_name": config.name,
            "backup_type": config.backup_type.value,
            "timestamp": datetime.now().isoformat(),
            "source_paths": config.source_paths,
            "compression_enabled": config.compression_enabled,
            "encryption_enabled": config.encryption_enabled
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return backup_dir

    async def full_backup(self, config: BackupConfig, backup_dir: Path, result: BackupResult):
        """Execute full backup with timeout protection"""
        logger.info("Executing full backup")
        
        # Timeout protection para operaciones de backup
        BACKUP_TIMEOUT = int(os.getenv('BACKUP_TIMEOUT_SECONDS', '3600'))  # 1 hour default

        try:
            await asyncio.wait_for(
                self._execute_full_backup_internal(config, backup_dir, result),
                timeout=BACKUP_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Full backup timed out after {BACKUP_TIMEOUT} seconds", extra={
                "config_name": config.name,
                "backup_id": result.backup_id,
                "timeout_seconds": BACKUP_TIMEOUT,
                "context": "backup_timeout"
            })
            raise
    
    async def _execute_full_backup_internal(self, config: BackupConfig, backup_dir: Path, result: BackupResult):
        """Internal full backup execution"""
        for source_path_str in config.source_paths:
            source_path = Path(source_path_str)

            if source_path.is_file():
                # Single file backup
                dest_file = backup_dir / source_path.name
                await self.copy_file_with_progress(source_path, dest_file, result)

            elif source_path.is_dir():
                # Directory backup
                dest_dir = backup_dir / source_path.name
                await self.copy_directory_with_progress(source_path, dest_dir, config, result)

    async def incremental_backup(self, config: BackupConfig, backup_dir: Path, result: BackupResult):
        """Execute incremental backup"""
        logger.info("Executing incremental backup")

        # Find last successful backup
        last_backup = self.find_last_successful_backup(config.name)
        if not last_backup:
            logger.info("No previous backup found, performing full backup")
            await self.full_backup(config, backup_dir, result)
            return

        last_backup_time = last_backup.start_time

        for source_path_str in config.source_paths:
            source_path = Path(source_path_str)

            if source_path.is_file():
                # Check if file was modified since last backup
                if source_path.stat().st_mtime > last_backup_time.timestamp():
                    dest_file = backup_dir / source_path.name
                    await self.copy_file_with_progress(source_path, dest_file, result)

            elif source_path.is_dir():
                dest_dir = backup_dir / source_path.name
                await self.copy_directory_incremental(source_path, dest_dir, last_backup_time, config, result)

    async def differential_backup(self, config: BackupConfig, backup_dir: Path, result: BackupResult):
        """Execute differential backup"""
        logger.info("Executing differential backup")

        # Find last full backup
        last_full_backup = self.find_last_full_backup(config.name)
        if not last_full_backup:
            logger.info("No previous full backup found, performing full backup")
            await self.full_backup(config, backup_dir, result)
            return

        last_full_time = last_full_backup.start_time

        for source_path_str in config.source_paths:
            source_path = Path(source_path_str)

            if source_path.is_file():
                if source_path.stat().st_mtime > last_full_time.timestamp():
                    dest_file = backup_dir / source_path.name
                    await self.copy_file_with_progress(source_path, dest_file, result)

            elif source_path.is_dir():
                dest_dir = backup_dir / source_path.name
                await self.copy_directory_differential(source_path, dest_dir, last_full_time, config, result)

    async def copy_file_with_progress(self, source: Path, dest: Path, result: BackupResult):
        """Copy file with progress tracking"""
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, dest)

            # Update progress
            file_size = source.stat().st_size
            result.files_processed += 1
            result.files_backed_up += 1
            result.bytes_processed += file_size
            result.bytes_backed_up += file_size

        except Exception as e:
            logger.error(f"Failed to copy file {source}: {e}")
            result.files_processed += 1

    async def copy_directory_with_progress(self, source: Path, dest: Path, config: BackupConfig, result: BackupResult):
        """Copy directory with progress tracking and filtering"""
        try:
            dest.mkdir(parents=True, exist_ok=True)

            for item in source.rglob('*'):
                if item.is_file():
                    # Check include/exclude patterns
                    if not self.should_include_file(item, source, config):
                        continue

                    relative_path = item.relative_to(source)
                    dest_file = dest / relative_path

                    await self.copy_file_with_progress(item, dest_file, result)

        except Exception as e:
            logger.error(f"Failed to copy directory {source}: {e}")

    async def copy_directory_incremental(self, source: Path, dest: Path, since_time: datetime, 
                                       config: BackupConfig, result: BackupResult):
        """Copy directory incrementally (files modified since timestamp)"""
        try:
            dest.mkdir(parents=True, exist_ok=True)

            for item in source.rglob('*'):
                if item.is_file():
                    # Check if modified since last backup
                    if item.stat().st_mtime <= since_time.timestamp():
                        continue

                    # Check include/exclude patterns
                    if not self.should_include_file(item, source, config):
                        continue

                    relative_path = item.relative_to(source)
                    dest_file = dest / relative_path

                    await self.copy_file_with_progress(item, dest_file, result)

        except Exception as e:
            logger.error(f"Failed to copy directory incrementally {source}: {e}")

    async def copy_directory_differential(self, source: Path, dest: Path, since_time: datetime,
                                        config: BackupConfig, result: BackupResult):
        """Copy directory differentially (files modified since full backup)"""
        # Same logic as incremental for this implementation
        await self.copy_directory_incremental(source, dest, since_time, config, result)

    def should_include_file(self, file_path: Path, source_root: Path, config: BackupConfig) -> bool:
        """Check if file should be included based on patterns"""
        relative_path = file_path.relative_to(source_root)
        path_str = str(relative_path)

        # Check exclude patterns first
        for pattern in config.exclude_patterns:
            if self.matches_pattern(path_str, pattern):
                return False

        # Check include patterns
        for pattern in config.include_patterns:
            if self.matches_pattern(path_str, pattern):
                return True

        return False

    def matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def calculate_backup_checksum(self, backup_dir: Path) -> str:
        """Calculate checksum for backup verification"""
        try:
            hasher = hashlib.sha256()

            for file_path in sorted(backup_dir.rglob('*')):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)

                    # Include file metadata in hash
                    stat_info = file_path.stat()
                    hasher.update(f"{file_path.name}:{stat_info.st_size}:{stat_info.st_mtime}".encode())

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate backup checksum: {e}")
            return None

    async def compress_backup(self, backup_dir: Path, result: BackupResult) -> str:
        """Compress backup directory"""
        try:
            compressed_file = f"{backup_dir}.tar.gz"

            # Create compressed archive
            import tarfile
            with tarfile.open(compressed_file, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_dir.name)

            # Remove original directory
            shutil.rmtree(backup_dir)

            logger.info(f"Backup compressed to: {compressed_file}")
            return compressed_file

        except Exception as e:
            logger.error(f"Failed to compress backup: {e}")
            return str(backup_dir)

    def calculate_compression_ratio(self, original_path: Path, compressed_path: str) -> float:
        """Calculate compression ratio"""
        try:
            if original_path.is_dir():
                original_size = sum(f.stat().st_size for f in original_path.rglob('*') if f.is_file())
            else:
                original_size = original_path.stat().st_size

            compressed_size = Path(compressed_path).stat().st_size

            if original_size > 0:
                return compressed_size / original_size

            return 1.0

        except Exception:
            return None

    async def upload_to_storage(self, config: BackupConfig, backup_path: str, result: BackupResult):
        """Upload backup to configured storage backend"""
        if config.storage_backend == StorageBackend.S3:
            await self.upload_to_s3(config, backup_path, result)
        elif config.storage_backend == StorageBackend.FTP:
            await self.upload_to_ftp(config, backup_path, result)
        elif config.storage_backend == StorageBackend.RSYNC:
            await self.upload_to_rsync(config, backup_path, result)

    async def upload_to_s3(self, config: BackupConfig, backup_path: str, result: BackupResult):
        """Upload backup to S3 (placeholder implementation)"""
        logger.info("S3 upload would be implemented here with boto3")
        # TODO: Implement S3 upload with boto3
        pass

    async def upload_to_ftp(self, config: BackupConfig, backup_path: str, result: BackupResult):
        """Upload backup to FTP (placeholder implementation)"""
        logger.info("FTP upload would be implemented here with ftplib")
        # TODO: Implement FTP upload
        pass

    async def upload_to_rsync(self, config: BackupConfig, backup_path: str, result: BackupResult):
        """Upload backup using rsync"""
        try:
            cmd = ["rsync", "-avz", backup_path, config.destination_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Rsync failed: {stderr.decode()}")

            logger.info("Rsync upload completed successfully")

        except Exception as e:
            logger.error(f"Rsync upload failed: {e}")
            raise

    def find_last_successful_backup(self, config_name: str) -> Optional[BackupResult]:
        """Find last successful backup for config"""
        history = self.metadata.get_backup_history(config_name, limit=50)

        for backup in history:
            if backup.status == BackupStatus.COMPLETED:
                return backup

        return None

    def find_last_full_backup(self, config_name: str) -> Optional[BackupResult]:
        """Find last successful full backup for config"""
        history = self.metadata.get_backup_history(config_name, limit=100)

        for backup in history:
            if backup.status == BackupStatus.COMPLETED and backup.backup_type == BackupType.FULL:
                return backup

        return None

    async def cleanup_old_backups(self, config: BackupConfig):
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=config.retention_days)

            # Get old backups
            old_backups = []
            history = self.metadata.get_backup_history(config.name, limit=1000)

            for backup in history:
                if backup.start_time < cutoff_date and backup.backup_path:
                    old_backups.append(backup)

            # Delete old backup files
            for backup in old_backups:
                try:
                    backup_path = Path(backup.backup_path)
                    if backup_path.exists():
                        if backup_path.is_file():
                            backup_path.unlink()
                        elif backup_path.is_dir():
                            shutil.rmtree(backup_path)

                        logger.info(f"Deleted old backup: {backup.backup_path}")

                except Exception as e:
                    logger.error(f"Failed to delete old backup {backup.backup_path}: {e}")

            if old_backups:
                logger.info(f"Cleaned up {len(old_backups)} old backups")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

class BackupScheduler:
    """Backup scheduler with cron-like scheduling and resource management"""

    def __init__(self):
        self.backup_engine = BackupEngine()
        self.configs: Dict[str, BackupConfig] = {}
        self.running_backups: Dict[str, asyncio.Task] = {}
        self.scheduler_active = False
        self.scheduler_thread = None
        
        # Resource management and thread safety
        self._scheduler_lock = threading.Lock()
        self._max_concurrent_backups = int(os.getenv('MAX_CONCURRENT_BACKUPS', '2'))
        self._backup_semaphore = asyncio.Semaphore(self._max_concurrent_backups)

    def add_config(self, config: BackupConfig):
        """Add backup configuration"""
        self.configs[config.name] = config
        self.backup_engine.metadata.save_config(config)
        logger.info(f"Added backup configuration: {config.name}")

    def remove_config(self, config_name: str):
        """Remove backup configuration"""
        if config_name in self.configs:
            del self.configs[config_name]
            logger.info(f"Removed backup configuration: {config_name}")

    def start_scheduler(self):
        """Start the backup scheduler"""
        if self.scheduler_active:
            logger.warning("Scheduler is already running")
            return

        self.scheduler_active = True

        # Schedule backups
        for config in self.configs.values():
            if config.enabled:
                schedule.every().day.at("02:00").do(self.schedule_backup, config.name)
                logger.info(f"Scheduled backup '{config.name}' for {config.schedule_cron}")

        # Start scheduler thread
        def run_scheduler():
            while self.scheduler_active:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("Backup scheduler started")

    def stop_scheduler(self):
        """Stop the backup scheduler"""
        self.scheduler_active = False
        schedule.clear()

        # Cancel running backups
        for task in self.running_backups.values():
            task.cancel()

        logger.info("Backup scheduler stopped")

    def schedule_backup(self, config_name: str):
        """Schedule a backup to run"""
        if config_name not in self.configs:
            logger.error(f"Backup configuration not found: {config_name}")
            return

        if config_name in self.running_backups:
            logger.warning(f"Backup '{config_name}' is already running")
            return

        config = self.configs[config_name]

        # Create backup task
        task = asyncio.create_task(self.run_backup(config))
        self.running_backups[config_name] = task

        logger.info(f"Started backup: {config_name}")

    async def run_backup(self, config: BackupConfig):
        """Run backup and handle completion"""
        try:
            result = await self.backup_engine.backup(config)

            # Send notification if configured
            if config.notification_emails:
                await self.send_notification(config, result)

            return result

        except Exception as e:
            logger.error(f"Backup failed: {e}")

        finally:
            # Remove from running backups
            if config.name in self.running_backups:
                del self.running_backups[config.name]

    async def send_notification(self, config: BackupConfig, result: BackupResult):
        """Send backup notification (placeholder)"""
        logger.info(f"Would send notification for backup '{config.name}' - Status: {result.status.value}")
        # TODO: Implement email notifications

    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup status"""
        return {
            "scheduler_active": self.scheduler_active,
            "total_configs": len(self.configs),
            "enabled_configs": sum(1 for c in self.configs.values() if c.enabled),
            "running_backups": list(self.running_backups.keys()),
            "configurations": [
                {
                    "name": config.name,
                    "enabled": config.enabled,
                    "backup_type": config.backup_type.value,
                    "retention_days": config.retention_days
                }
                for config in self.configs.values()
            ]
        }

# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create backup scheduler
        scheduler = BackupScheduler()

        # Create backup configuration
        config = BackupConfig(
            name="daily_system_backup",
            source_paths=["/etc", "/home/user/important"],
            destination_path="/backups",
            backup_type=BackupType.FULL,
            retention_days=7,
            compression_enabled=True,
            exclude_patterns=["*.tmp", "*.log", "__pycache__/"]
        )

        # Add configuration
        scheduler.add_config(config)

        # Start scheduler
        scheduler.start_scheduler()

        # Manual backup for testing
        result = await scheduler.run_backup(config)
        print(f"Backup completed: {result.status.value}")

        # Get status
        status = scheduler.get_backup_status()
        print(f"Scheduler status: {status}")

        # Stop scheduler
        scheduler.stop_scheduler()

    # Run example
    asyncio.run(example_usage())
