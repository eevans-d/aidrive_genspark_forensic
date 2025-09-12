"""
Main Scheduler - Orchestrator for All Schedulers
Manages and coordinates all scheduling services
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Import all schedulers
from backup_scheduler import BackupScheduler, BackupConfig, BackupType
from maintenance_scheduler import MaintenanceScheduler
from report_scheduler import ReportScheduler  
from health_scheduler import HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SchedulerOrchestrator:
    """Main scheduler orchestrator"""

    def __init__(self):
        self.backup_scheduler = BackupScheduler()
        self.maintenance_scheduler = MaintenanceScheduler()
        self.report_scheduler = ReportScheduler()
        self.health_monitor = HealthMonitor()

        self.is_running = False
        self.start_time = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize_default_configs(self):
        """Initialize default scheduler configurations"""

        # Default backup configuration
        default_backup = BackupConfig(
            name="system_backup",
            source_paths=["models", "data", "logs", "reports"],
            destination_path="backups",
            backup_type=BackupType.FULL,
            retention_days=30,
            compression_enabled=True,
            exclude_patterns=["*.tmp", "*.log", "__pycache__/", "*.pyc"]
        )

        try:
            self.backup_scheduler.add_config(default_backup)
            logger.info("Default backup configuration added")
        except Exception as e:
            logger.warning(f"Failed to add default backup config: {e}")

    def start_all_schedulers(self):
        """Start all schedulers"""
        try:
            self.is_running = True
            self.start_time = datetime.now()

            logger.info("Starting all schedulers...")

            # Initialize default configurations
            self.initialize_default_configs()

            # Start individual schedulers
            self.backup_scheduler.start_scheduler()
            self.maintenance_scheduler.start_scheduler()
            self.report_scheduler.start_scheduler()
            self.health_monitor.start_monitoring()

            logger.info("All schedulers started successfully")

        except Exception as e:
            logger.error(f"Failed to start schedulers: {e}")
            raise

    def stop_all_schedulers(self):
        """Stop all schedulers"""
        try:
            logger.info("Stopping all schedulers...")

            self.backup_scheduler.stop_scheduler()
            self.maintenance_scheduler.stop_scheduler()
            self.report_scheduler.stop_scheduler()
            self.health_monitor.stop_monitoring()

            self.is_running = False

            logger.info("All schedulers stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping schedulers: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "timestamp": datetime.now().isoformat(),
            "running": self.is_running,
            "uptime_seconds": uptime,
            "schedulers": {
                "backup": {
                    "active": self.backup_scheduler.scheduler_active,
                    "status": self.backup_scheduler.get_backup_status()
                },
                "maintenance": {
                    "active": self.maintenance_scheduler.scheduler_active,
                    "tasks": len(self.maintenance_scheduler.tasks)
                },
                "reports": {
                    "active": self.report_scheduler.scheduler_active,
                    "reports": len(self.report_scheduler.reports)
                },
                "health": {
                    "active": self.health_monitor.scheduler_active,
                    "status": self.health_monitor.get_current_status()
                }
            }
        }

    async def run_manual_backup(self, config_name: str = None) -> Dict[str, Any]:
        """Run manual backup"""
        try:
            if config_name and config_name in self.backup_scheduler.configs:
                config = self.backup_scheduler.configs[config_name]
                result = await self.backup_scheduler.run_backup(config)
                return {
                    "success": True,
                    "backup_id": result.backup_id,
                    "status": result.status.value,
                    "message": f"Manual backup completed: {result.status.value}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Backup configuration not found: {config_name}"
                }
        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            return {
                "success": False,
                "message": f"Manual backup failed: {str(e)}"
            }

    async def run_health_check(self) -> Dict[str, Any]:
        """Run immediate health check"""
        try:
            health_report = await self.health_monitor.check_system_health()
            return {
                "success": True,
                "health_report": health_report
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "message": f"Health check failed: {str(e)}"
            }

    def save_status_report(self):
        """Save current status to file"""
        try:
            status = self.get_system_status()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            Path("status").mkdir(exist_ok=True)
            status_file = f"status/scheduler_status_{timestamp}.json"

            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)

            logger.info(f"Status report saved: {status_file}")

        except Exception as e:
            logger.error(f"Failed to save status report: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop_all_schedulers()
        sys.exit(0)

    async def run_forever(self):
        """Run scheduler orchestrator forever"""
        try:
            self.start_all_schedulers()

            logger.info("Scheduler orchestrator running. Press Ctrl+C to stop.")

            # Run indefinitely
            while self.is_running:
                await asyncio.sleep(60)  # Check every minute

                # Save periodic status report
                if datetime.now().minute % 15 == 0:  # Every 15 minutes
                    self.save_status_report()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Scheduler orchestrator error: {e}")
        finally:
            self.stop_all_schedulers()

def main():
    """Main entry point"""
    orchestrator = SchedulerOrchestrator()

    try:
        # Run the orchestrator
        asyncio.run(orchestrator.run_forever())
    except Exception as e:
        logger.error(f"Failed to start scheduler orchestrator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
