#!/usr/bin/env python3
"""
Automated Backup and Disaster Recovery System
for Argentine Retail System

Features:
- Database backups (PostgreSQL)
- File system backups
- Cloud storage integration (AWS S3)
- Backup verification and integrity checks
- Disaster recovery procedures
- Automated retention policies
"""

import os
import sys
import logging
import subprocess
import datetime
import hashlib
import json
import boto3
import psycopg2
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import schedule
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/retail-backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupType(Enum):
    DATABASE = "database"
    FILES = "files"
    FULL = "full"

class BackupStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

@dataclass
class BackupJob:
    """Represents a backup job with metadata"""
    job_id: str
    backup_type: BackupType
    source_path: str
    destination_path: str
    timestamp: datetime.datetime
    status: BackupStatus
    size_bytes: int = 0
    checksum: Optional[str] = None
    compression_ratio: float = 0.0
    duration_seconds: float = 0.0

class RetailBackupManager:
    """Main backup management class"""

    def __init__(self, config_path: str = "/etc/retail-backup/config.json"):
        self.config = self._load_config(config_path)
        self.s3_client = self._initialize_s3_client()
        self.backup_history: List[BackupJob] = []

    def _load_config(self, config_path: str) -> Dict:
        """Load backup configuration"""
        default_config = {
            "database": {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", 5432)),
                "database": os.getenv("POSTGRES_DB", "retail_argentina"),
                "username": os.getenv("POSTGRES_USER", "retail_user"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
            },
            "aws": {
                "bucket_name": os.getenv("AWS_BUCKET_NAME", "retail-argentina-backups"),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            },
            "backup_paths": [
                "/app/uploads",
                "/app/data", 
                "/app/logs",
                "/app/models"
            ],
            "retention": {
                "daily_backups": 7,
                "weekly_backups": 4,
                "monthly_backups": 12
            },
            "compression": True,
            "encryption": True,
            "notification": {
                "email": os.getenv("BACKUP_NOTIFICATION_EMAIL", ""),
                "slack_webhook": os.getenv("SLACK_WEBHOOK_URL", "")
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")

        return default_config

    def _initialize_s3_client(self):
        """Initialize AWS S3 client"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=self.config['aws']['access_key_id'],
                aws_secret_access_key=self.config['aws']['secret_access_key'],
                region_name=self.config['aws']['region']
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None

    def create_database_backup(self) -> BackupJob:
        """Create PostgreSQL database backup"""
        timestamp = datetime.datetime.now()
        job_id = f"db_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        backup_job = BackupJob(
            job_id=job_id,
            backup_type=BackupType.DATABASE,
            source_path="postgresql_database",
            destination_path=f"/tmp/{job_id}.sql.gz",
            timestamp=timestamp,
            status=BackupStatus.IN_PROGRESS
        )

        try:
            start_time = time.time()

            # Create pg_dump command
            db_config = self.config['database']
            dump_command = [
                'pg_dump',
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['username']}",
                f"--dbname={db_config['database']}",
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges'
            ]

            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']

            # Execute backup with compression
            if self.config.get('compression', True):
                with open(backup_job.destination_path, 'wb') as f:
                    dump_process = subprocess.Popen(
                        dump_command, 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    gzip_process = subprocess.Popen(
                        ['gzip', '-c'],
                        stdin=dump_process.stdout,
                        stdout=f,
                        stderr=subprocess.PIPE
                    )

                    dump_process.stdout.close()
                    gzip_process.communicate()
                    dump_process.wait()

                    if dump_process.returncode != 0:
                        raise Exception(f"pg_dump failed with return code {dump_process.returncode}")
            else:
                with open(backup_job.destination_path, 'w') as f:
                    result = subprocess.run(
                        dump_command,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        text=True
                    )
                    if result.returncode != 0:
                        raise Exception(f"pg_dump failed: {result.stderr}")

            # Calculate metrics
            backup_job.duration_seconds = time.time() - start_time
            backup_job.size_bytes = os.path.getsize(backup_job.destination_path)
            backup_job.checksum = self._calculate_checksum(backup_job.destination_path)
            backup_job.status = BackupStatus.SUCCESS

            logger.info(f"Database backup completed: {job_id}")
            return backup_job

        except Exception as e:
            backup_job.status = BackupStatus.FAILED
            logger.error(f"Database backup failed: {e}")
            raise

    def create_files_backup(self, paths: Optional[List[str]] = None) -> BackupJob:
        """Create file system backup using tar"""
        timestamp = datetime.datetime.now()
        job_id = f"files_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        if paths is None:
            paths = self.config['backup_paths']

        backup_job = BackupJob(
            job_id=job_id,
            backup_type=BackupType.FILES,
            source_path=",".join(paths),
            destination_path=f"/tmp/{job_id}.tar.gz",
            timestamp=timestamp,
            status=BackupStatus.IN_PROGRESS
        )

        try:
            start_time = time.time()

            # Create tar command
            tar_command = ['tar', '-czf', backup_job.destination_path]

            # Add existing paths only
            existing_paths = [p for p in paths if os.path.exists(p)]
            if not existing_paths:
                logger.warning("No backup paths exist, skipping files backup")
                backup_job.status = BackupStatus.SUCCESS
                return backup_job

            tar_command.extend(existing_paths)

            # Execute backup
            result = subprocess.run(
                tar_command,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")

            # Calculate metrics
            backup_job.duration_seconds = time.time() - start_time
            backup_job.size_bytes = os.path.getsize(backup_job.destination_path)
            backup_job.checksum = self._calculate_checksum(backup_job.destination_path)
            backup_job.status = BackupStatus.SUCCESS

            logger.info(f"Files backup completed: {job_id}")
            return backup_job

        except Exception as e:
            backup_job.status = BackupStatus.FAILED
            logger.error(f"Files backup failed: {e}")
            raise

    def upload_to_cloud(self, backup_job: BackupJob) -> bool:
        """Upload backup to AWS S3"""
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False

        try:
            bucket_name = self.config['aws']['bucket_name']

            # Create S3 key with organized structure
            s3_key = f"retail-argentina/{backup_job.backup_type.value}/{backup_job.timestamp.strftime('%Y/%m/%d')}/{backup_job.job_id}"

            # Add file extension if not present
            if backup_job.destination_path.endswith('.gz'):
                s3_key += '.gz'
            elif backup_job.destination_path.endswith('.sql'):
                s3_key += '.sql'

            # Upload file
            self.s3_client.upload_file(
                backup_job.destination_path,
                bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'job_id': backup_job.job_id,
                        'backup_type': backup_job.backup_type.value,
                        'timestamp': backup_job.timestamp.isoformat(),
                        'checksum': backup_job.checksum or '',
                        'size_bytes': str(backup_job.size_bytes)
                    }
                }
            )

            logger.info(f"Backup uploaded to S3: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            return False

    def verify_backup_integrity(self, backup_job: BackupJob) -> bool:
        """Verify backup file integrity"""
        try:
            if not os.path.exists(backup_job.destination_path):
                logger.error(f"Backup file not found: {backup_job.destination_path}")
                return False

            # Verify checksum
            current_checksum = self._calculate_checksum(backup_job.destination_path)
            if current_checksum != backup_job.checksum:
                logger.error(f"Checksum mismatch for {backup_job.job_id}")
                return False

            # Test archive integrity if it's a compressed file
            if backup_job.destination_path.endswith('.gz'):
                if backup_job.backup_type == BackupType.DATABASE:
                    # Test gzip integrity
                    result = subprocess.run(
                        ['gzip', '-t', backup_job.destination_path],
                        capture_output=True
                    )
                    if result.returncode != 0:
                        logger.error(f"Gzip integrity check failed for {backup_job.job_id}")
                        return False
                else:
                    # Test tar.gz integrity
                    result = subprocess.run(
                        ['tar', '-tzf', backup_job.destination_path],
                        capture_output=True,
                        stdout=subprocess.DEVNULL
                    )
                    if result.returncode != 0:
                        logger.error(f"Tar integrity check failed for {backup_job.job_id}")
                        return False

            logger.info(f"Backup integrity verified: {backup_job.job_id}")
            return True

        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            return False

    def cleanup_old_backups(self) -> None:
        """Clean up old backup files based on retention policy"""
        try:
            retention = self.config['retention']
            now = datetime.datetime.now()

            # Define retention periods
            daily_cutoff = now - datetime.timedelta(days=retention['daily_backups'])
            weekly_cutoff = now - datetime.timedelta(weeks=retention['weekly_backups'])
            monthly_cutoff = now - datetime.timedelta(days=retention['monthly_backups'] * 30)

            # List files in /tmp matching backup pattern
            tmp_path = Path('/tmp')
            backup_files = list(tmp_path.glob('*backup_*.tar.gz')) + list(tmp_path.glob('*backup_*.sql.gz'))

            for backup_file in backup_files:
                try:
                    # Extract timestamp from filename
                    filename = backup_file.name
                    if 'backup_' in filename:
                        timestamp_str = filename.split('backup_')[1].split('.')[0]
                        file_timestamp = datetime.datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                        # Determine if file should be deleted
                        should_delete = False
                        if file_timestamp < monthly_cutoff:
                            should_delete = True
                        elif file_timestamp < weekly_cutoff and file_timestamp.weekday() != 0:  # Keep weekly (Monday)
                            should_delete = True
                        elif file_timestamp < daily_cutoff:
                            should_delete = True

                        if should_delete:
                            backup_file.unlink()
                            logger.info(f"Deleted old backup: {backup_file}")

                except Exception as e:
                    logger.warning(f"Could not process backup file {backup_file}: {e}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def create_full_backup(self) -> Tuple[BackupJob, BackupJob]:
        """Create both database and files backup"""
        logger.info("Starting full backup procedure")

        db_backup = self.create_database_backup()
        files_backup = self.create_files_backup()

        # Upload to cloud if successful
        if db_backup.status == BackupStatus.SUCCESS:
            self.upload_to_cloud(db_backup)
            self.verify_backup_integrity(db_backup)

        if files_backup.status == BackupStatus.SUCCESS:
            self.upload_to_cloud(files_backup)
            self.verify_backup_integrity(files_backup)

        # Store in history
        self.backup_history.extend([db_backup, files_backup])

        # Cleanup old backups
        self.cleanup_old_backups()

        logger.info("Full backup procedure completed")
        return db_backup, files_backup

    def restore_database_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            logger.info(f"Starting database restore from {backup_path}")

            db_config = self.config['database']

            # Prepare restore command
            if backup_path.endswith('.gz'):
                # Compressed backup
                restore_command = f"gunzip -c {backup_path} | psql -h {db_config['host']} -p {db_config['port']} -U {db_config['username']} -d {db_config['database']}"
            else:
                # Uncompressed backup
                restore_command = f"psql -h {db_config['host']} -p {db_config['port']} -U {db_config['username']} -d {db_config['database']} -f {backup_path}"

            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']

            # Execute restore
            result = subprocess.run(
                restore_command,
                shell=True,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Database restore completed successfully")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False

    def schedule_backups(self):
        """Schedule automated backups"""
        # Daily database backup at 2 AM
        schedule.every().day.at("02:00").do(self.create_database_backup)

        # Weekly full backup on Sunday at 1 AM
        schedule.every().sunday.at("01:00").do(self.create_full_backup)

        # Monthly cleanup on 1st day at 3 AM  
        schedule.every().month.do(self.cleanup_old_backups)

        logger.info("Backup schedule configured")

        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main entry point"""
    backup_manager = RetailBackupManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "database":
            backup_job = backup_manager.create_database_backup()
            print(f"Database backup: {backup_job.status.value}")

        elif command == "files":
            backup_job = backup_manager.create_files_backup()
            print(f"Files backup: {backup_job.status.value}")

        elif command == "full":
            db_backup, files_backup = backup_manager.create_full_backup()
            print(f"Full backup - DB: {db_backup.status.value}, Files: {files_backup.status.value}")

        elif command == "restore" and len(sys.argv) > 2:
            backup_path = sys.argv[2]
            success = backup_manager.restore_database_backup(backup_path)
            print(f"Restore: {'success' if success else 'failed'}")

        elif command == "schedule":
            backup_manager.schedule_backups()

        else:
            print("Usage: backup.py [database|files|full|restore <path>|schedule]")
    else:
        print("Usage: backup.py [database|files|full|restore <path>|schedule]")

if __name__ == "__main__":
    main()
