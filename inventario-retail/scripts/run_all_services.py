#!/usr/bin/env python3
"""
Run All Services - Startup Script for Complete System
Starts ML service and all schedulers in coordinated manner
"""

import os
import sys
import time
import signal
import subprocess
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.is_running = False

    def start_ml_service(self):
        """Start ML service on port 8003"""
        try:
            logger.info("Starting ML Service...")

            # Change to ml directory and start service
            cmd = [sys.executable, "main_ml_service.py"]
            process = subprocess.Popen(
                cmd,
                cwd="ml",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes["ml_service"] = process
            logger.info(f"ML Service started with PID: {process.pid}")

        except Exception as e:
            logger.error(f"Failed to start ML service: {e}")

    def start_schedulers(self):
        """Start scheduler orchestrator"""
        try:
            logger.info("Starting Scheduler Orchestrator...")

            cmd = [sys.executable, "main_scheduler.py"]
            process = subprocess.Popen(
                cmd,
                cwd="schedulers",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes["schedulers"] = process
            logger.info(f"Schedulers started with PID: {process.pid}")

        except Exception as e:
            logger.error(f"Failed to start schedulers: {e}")

    def start_all_services(self):
        """Start all services"""
        try:
            self.is_running = True

            logger.info("=== STARTING ALL SERVICES ===")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")

            # Start ML service first
            self.start_ml_service()

            # Wait a bit for ML service to initialize
            time.sleep(5)

            # Start schedulers
            self.start_schedulers()

            logger.info("All services started successfully!")
            logger.info("Services running:")
            for name, process in self.processes.items():
                logger.info(f"  - {name}: PID {process.pid}")

        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self.stop_all_services()

    def stop_all_services(self):
        """Stop all services"""
        try:
            logger.info("Stopping all services...")

            for name, process in self.processes.items():
                try:
                    logger.info(f"Stopping {name} (PID: {process.pid})")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {name}")
                        process.kill()

                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")

            self.processes.clear()
            self.is_running = False

            logger.info("All services stopped")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def monitor_services(self):
        """Monitor running services"""
        while self.is_running:
            time.sleep(30)  # Check every 30 seconds

            # Check if processes are still running
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    logger.error(f"Service {name} has stopped unexpectedly (exit code: {process.returncode})")
                    del self.processes[name]

                    # Try to restart critical services
                    if name == "ml_service":
                        logger.info("Attempting to restart ML service...")
                        self.start_ml_service()
                    elif name == "schedulers":
                        logger.info("Attempting to restart schedulers...")
                        self.start_schedulers()

            if not self.processes:
                logger.error("All services have stopped")
                self.is_running = False
                break

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all_services()
        sys.exit(0)

    def run(self):
        """Main run method"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # Start all services
            self.start_all_services()

            if self.processes:
                logger.info("System is running. Press Ctrl+C to stop.")

                # Monitor services
                self.monitor_services()
            else:
                logger.error("Failed to start any services")
                sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop_all_services()

def check_dependencies():
    """Check if required directories and files exist"""
    required_paths = [
        "ml/main_ml_service.py",
        "schedulers/main_scheduler.py"
    ]

    missing = []
    for path in required_paths:
        if not Path(path).exists():
            missing.append(path)

    if missing:
        logger.error("Missing required files:")
        for path in missing:
            logger.error(f"  - {path}")
        return False

    return True

def main():
    """Main entry point"""
    logger.info("Sistema ML Completo - Service Manager")
    logger.info("====================================")

    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        sys.exit(1)

    # Create service manager and run
    manager = ServiceManager()
    manager.run()

if __name__ == "__main__":
    main()
