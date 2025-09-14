"""
Sistema de automatización y schedulers para integraciones
Maneja tareas programadas de AFIP, MercadoLibre y compliance fiscal
"""
import asyncio
import os
import schedule
import time
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import threading
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import psutil
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler(os.getenv('LOG_PATH', 'logs/scheduler.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScheduledTask:
    """Tarea programada del sistema"""
    id: str
    name: str
    description: str
    schedule_pattern: str  # Patrón cron-like
    function: Callable
    priority: TaskPriority
    timeout_minutes: int = 30
    retry_attempts: int = 3
    retry_delay_minutes: int = 5
    enabled: bool = True

    # Estado de ejecución
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_duration_seconds: float = 0
    success_count: int = 0
    failure_count: int = 0
    last_error: str = ""

@dataclass
class TaskExecution:
    """Registro de ejecución de tarea"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.RUNNING
    result: Optional[Dict[str, Any]] = None
    error_message: str = ""
    execution_logs: List[str] = None

    def __post_init__(self):
        if self.execution_logs is None:
            self.execution_logs = []

class IntegrationScheduler:
    """Scheduler principal para integraciones"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: List[TaskExecution] = []
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Control de shutdown graceful
        self.shutdown_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Estadísticas del sistema
        self.stats = {
            'started_at': datetime.now(),
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }

        # Registrar tareas predefinidas
        self._register_default_tasks()

    def _signal_handler(self, signum, frame):
        """Maneja señales de shutdown"""
        logger.info(f"Recibida señal {signum}, iniciando shutdown graceful...")
        self.shutdown_event.set()
        self.stop()

    def _register_default_tasks(self):
        """Registra tareas predeterminadas del sistema"""

        # Sincronización AFIP cada 6 horas
        self.register_task(ScheduledTask(
            id="afip_sync",
            name="Sincronización AFIP",
            description="Sincroniza facturas electrónicas con AFIP WSFE",
            schedule_pattern="every(6).hours",
            function=self._afip_sync_task,
            priority=TaskPriority.HIGH,
            timeout_minutes=45,
            retry_attempts=3
        ))

        # Sincronización MercadoLibre cada hora
        self.register_task(ScheduledTask(
            id="ml_sync",
            name="Sincronización MercadoLibre",
            description="Sincroniza inventario con MercadoLibre",
            schedule_pattern="every().hour",
            function=self._ml_sync_task,
            priority=TaskPriority.MEDIUM,
            timeout_minutes=30,
            retry_attempts=2
        ))

        # Generación de reportes IVA mensuales
        self.register_task(ScheduledTask(
            id="iva_monthly_report",
            name="Reporte IVA Mensual",
            description="Genera libro IVA del mes anterior",
            schedule_pattern="monthly.at('02:00')",
            function=self._iva_monthly_report_task,
            priority=TaskPriority.HIGH,
            timeout_minutes=60,
            retry_attempts=1
        ))

        # Backup de datos fiscales diario
        self.register_task(ScheduledTask(
            id="fiscal_backup",
            name="Backup Fiscal Diario",
            description="Respaldo incremental de datos fiscales",
            schedule_pattern="daily.at('01:30')",
            function=self._fiscal_backup_task,
            priority=TaskPriority.MEDIUM,
            timeout_minutes=20
        ))

        # Limpieza de logs y archivos temporales
        self.register_task(ScheduledTask(
            id="cleanup_temp",
            name="Limpieza de Archivos Temporales",
            description="Elimina archivos temporales y logs antiguos",
            schedule_pattern="weekly.monday.at('03:00')",
            function=self._cleanup_temp_task,
            priority=TaskPriority.LOW,
            timeout_minutes=15
        ))

        # Monitoreo de salud del sistema
        self.register_task(ScheduledTask(
            id="health_check",
            name="Monitoreo de Salud",
            description="Verifica estado de servicios y recursos",
            schedule_pattern="every(15).minutes",
            function=self._health_check_task,
            priority=TaskPriority.CRITICAL,
            timeout_minutes=5
        ))

    def register_task(self, task: ScheduledTask):
        """Registra una nueva tarea programada"""
        try:
            # Configurar el schedule según el patrón
            self._configure_schedule(task)

            # Registrar tarea
            self.tasks[task.id] = task

            logger.info(f"Tarea registrada: {task.name} ({task.id})")

        except Exception as e:
            logger.error(f"Error registrando tarea {task.id}: {e}")

    def _configure_schedule(self, task: ScheduledTask):
        """Configura el schedule según el patrón especificado"""
        pattern = task.schedule_pattern.lower()

        if pattern.startswith("every(") and ").hours" in pattern:
            # every(6).hours
            hours = int(pattern.split("(")[1].split(")")[0])
            schedule.every(hours).hours.do(self._execute_task_wrapper, task.id)

        elif pattern == "every().hour":
            schedule.every().hour.do(self._execute_task_wrapper, task.id)

        elif pattern.startswith("every(") and ").minutes" in pattern:
            # every(15).minutes
            minutes = int(pattern.split("(")[1].split(")")[0])
            schedule.every(minutes).minutes.do(self._execute_task_wrapper, task.id)

        elif pattern.startswith("daily.at("):
            # daily.at('02:00')
            time_str = pattern.split("'")[1]
            schedule.every().day.at(time_str).do(self._execute_task_wrapper, task.id)

        elif pattern.startswith("weekly.") and ".at(" in pattern:
            # weekly.monday.at('03:00')
            parts = pattern.split(".")
            day = parts[1]
            time_str = pattern.split("'")[1]

            if day == "monday":
                schedule.every().monday.at(time_str).do(self._execute_task_wrapper, task.id)
            elif day == "tuesday":
                schedule.every().tuesday.at(time_str).do(self._execute_task_wrapper, task.id)
            # Agregar más días según necesidad

        elif pattern.startswith("monthly.at("):
            # monthly.at('02:00') - primer día del mes
            time_str = pattern.split("'")[1]
            # Nota: schedule no soporta mensual directamente, usar cron alternativo
            schedule.every().day.at(time_str).do(self._check_monthly_task, task.id)

        else:
            raise ValueError(f"Patrón de schedule no soportado: {pattern}")

    def _check_monthly_task(self, task_id: str):
        """Verifica si debe ejecutar tarea mensual"""
        if datetime.now().day == 1:  # Primer día del mes
            self._execute_task_wrapper(task_id)

    def _execute_task_wrapper(self, task_id: str):
        """Wrapper para ejecutar tarea con manejo de errores"""
        if not self.is_running:
            return

        task = self.tasks.get(task_id)
        if not task or not task.enabled:
            return

        # Verificar si ya está ejecutándose
        if task.status == TaskStatus.RUNNING:
            logger.warning(f"Tarea {task_id} ya está en ejecución, saltando")
            return

        # Ejecutar en thread separado
        self.executor.submit(self._execute_task, task_id)

    def _execute_task(self, task_id: str):
        """Ejecuta una tarea específica"""
        task = self.tasks[task_id]
        execution = TaskExecution(
            task_id=task_id,
            start_time=datetime.now()
        )

        try:
            logger.info(f"Iniciando ejecución de tarea: {task.name}")

            # Actualizar estado de tarea
            task.status = TaskStatus.RUNNING
            task.last_run = execution.start_time

            # Ejecutar función con timeout
            result = asyncio.run(
                asyncio.wait_for(
                    self._run_task_function(task),
                    timeout=task.timeout_minutes * 60
                )
            )

            # Marcar como completada
            task.status = TaskStatus.COMPLETED
            task.success_count += 1
            task.last_error = ""

            execution.status = TaskStatus.COMPLETED
            execution.result = result
            execution.end_time = datetime.now()

            duration = (execution.end_time - execution.start_time).total_seconds()
            task.last_duration_seconds = duration

            logger.info(f"Tarea {task.name} completada en {duration:.2f}s")

            # Actualizar estadísticas
            self.stats['successful_executions'] += 1

        except asyncio.TimeoutError:
            self._handle_task_timeout(task, execution)
        except Exception as e:
            self._handle_task_error(task, execution, e)
        finally:
            self.stats['total_executions'] += 1
            self.executions.append(execution)

            # Mantener solo últimas 1000 ejecuciones
            if len(self.executions) > 1000:
                self.executions = self.executions[-1000:]

    async def _run_task_function(self, task: ScheduledTask) -> Dict[str, Any]:
        """Ejecuta la función de la tarea"""
        if asyncio.iscoroutinefunction(task.function):
            return await task.function()
        else:
            # Ejecutar función síncrona en executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, task.function)

    def _handle_task_timeout(self, task: ScheduledTask, execution: TaskExecution):
        """Maneja timeout de tarea"""
        error_msg = f"Tarea {task.name} expiró después de {task.timeout_minutes} minutos"
        logger.error(error_msg)

        task.status = TaskStatus.FAILED
        task.failure_count += 1
        task.last_error = error_msg

        execution.status = TaskStatus.FAILED
        execution.error_message = error_msg
        execution.end_time = datetime.now()

        self.stats['failed_executions'] += 1

    def _handle_task_error(self, task: ScheduledTask, execution: TaskExecution, error: Exception):
        """Maneja error en ejecución de tarea"""
        error_msg = f"Error en tarea {task.name}: {str(error)}"
        logger.error(error_msg)

        task.status = TaskStatus.FAILED
        task.failure_count += 1
        task.last_error = error_msg

        execution.status = TaskStatus.FAILED
        execution.error_message = error_msg
        execution.end_time = datetime.now()

        self.stats['failed_executions'] += 1

        # Implementar retry logic si corresponde
        if task.retry_attempts > 0:
            self._schedule_retry(task)

    def _schedule_retry(self, task: ScheduledTask):
        """Programa reintento de tarea"""
        def retry_task():
            time.sleep(task.retry_delay_minutes * 60)
            if task.retry_attempts > 0:
                task.retry_attempts -= 1
                self._execute_task(task.id)

        threading.Thread(target=retry_task, daemon=True).start()

    def start(self):
        """Inicia el scheduler"""
        if self.is_running:
            logger.warning("Scheduler ya está en ejecución")
            return

        self.is_running = True
        logger.info("Iniciando Integration Scheduler...")

        # Calcular próximas ejecuciones
        for task in self.tasks.values():
            if task.enabled:
                task.next_run = self._calculate_next_run(task)

        # Loop principal del scheduler
        while self.is_running and not self.shutdown_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(30)  # Verificar cada 30 segundos

                # Actualizar próximas ejecuciones
                self._update_next_runs()

            except Exception as e:
                logger.error(f"Error en loop principal del scheduler: {e}")
                time.sleep(60)  # Esperar más tiempo en caso de error

        logger.info("Scheduler detenido")

    def stop(self):
        """Detiene el scheduler"""
        logger.info("Deteniendo scheduler...")
        self.is_running = False

        # Esperar que terminen las tareas en ejecución
        self.executor.shutdown(wait=True)

        # Limpiar schedule
        schedule.clear()

        logger.info("Scheduler detenido completamente")

    def _calculate_next_run(self, task: ScheduledTask) -> datetime:
        """Calcula próxima ejecución de tarea"""
        # Implementación simplificada - en producción usar librería cron
        now = datetime.now()
        pattern = task.schedule_pattern.lower()

        if "hours" in pattern:
            hours = int(pattern.split("(")[1].split(")")[0])
            return now + timedelta(hours=hours)
        elif "hour" in pattern:
            return now + timedelta(hours=1)
        elif "minutes" in pattern:
            minutes = int(pattern.split("(")[1].split(")")[0])
            return now + timedelta(minutes=minutes)
        elif "daily" in pattern:
            return now + timedelta(days=1)
        elif "weekly" in pattern:
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(hours=1)  # Default

    def _update_next_runs(self):
        """Actualiza próximas ejecuciones de tareas"""
        for task in self.tasks.values():
            if task.enabled and task.status != TaskStatus.RUNNING:
                task.next_run = self._calculate_next_run(task)

    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del scheduler"""
        return {
            "is_running": self.is_running,
            "stats": self.stats,
            "total_tasks": len(self.tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t.enabled]),
            "running_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "system_info": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles de una tarea específica"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task": asdict(task),
            "recent_executions": [
                asdict(exec) for exec in self.executions
                if exec.task_id == task_id
            ][-10:]  # Últimas 10 ejecuciones
        }

    # Implementaciones de tareas específicas

    async def _afip_sync_task(self) -> Dict[str, Any]:
        """Tarea de sincronización con AFIP"""
        logger.info("Ejecutando sincronización AFIP...")

        try:
            # Mock implementation - reemplazar con lógica real
            await asyncio.sleep(2)  # Simular trabajo

            return {
                "success": True,
                "facturas_procesadas": 25,
                "cae_obtenidos": 25,
                "errores": 0,
                "tiempo_respuesta_ms": 1500
            }

        except Exception as e:
            logger.error(f"Error en sincronización AFIP: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _ml_sync_task(self) -> Dict[str, Any]:
        """Tarea de sincronización con MercadoLibre"""
        logger.info("Ejecutando sincronización MercadoLibre...")

        try:
            # Mock implementation
            await asyncio.sleep(1)

            return {
                "success": True,
                "items_actualizados": 150,
                "conflictos_resueltos": 3,
                "stock_sincronizado": True,
                "precios_actualizados": 45
            }

        except Exception as e:
            logger.error(f"Error en sincronización ML: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _iva_monthly_report_task(self) -> Dict[str, Any]:
        """Tarea de reporte IVA mensual"""
        logger.info("Generando reporte IVA mensual...")

        try:
            # Mock implementation
            time.sleep(1)

            return {
                "success": True,
                "archivo_generado": "iva_ventas_202401.txt",
                "total_comprobantes": 450,
                "total_iva": 125000.50,
                "archivo_size_kb": 85
            }

        except Exception as e:
            logger.error(f"Error generando reporte IVA: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _fiscal_backup_task(self) -> Dict[str, Any]:
        """Tarea de backup fiscal"""
        logger.info("Ejecutando backup fiscal...")

        try:
            # Mock implementation
            time.sleep(0.5)

            return {
                "success": True,
                "archivos_respaldados": 1250,
                "backup_size_mb": 45.7,
                "backup_location": "/backups/fiscal_20240115.zip"
            }

        except Exception as e:
            logger.error(f"Error en backup fiscal: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _cleanup_temp_task(self) -> Dict[str, Any]:
        """Tarea de limpieza de archivos temporales"""
        logger.info("Ejecutando limpieza de archivos temporales...")

        try:
            # Mock implementation
            return {
                "success": True,
                "archivos_eliminados": 45,
                "espacio_liberado_mb": 128.5,
                "logs_rotados": 8
            }

        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _health_check_task(self) -> Dict[str, Any]:
        """Tarea de monitoreo de salud"""
        try:
            # Verificar recursos del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Verificar servicios críticos
            services_status = {
                "database": "healthy",  # Mock
                "afip_api": "healthy",
                "ml_api": "healthy"
            }

            # Determinar estado general
            is_healthy = (
                cpu_percent < 90 and
                memory.percent < 90 and
                disk.percent < 90 and
                all(status == "healthy" for status in services_status.values())
            )

            return {
                "success": True,
                "healthy": is_healthy,
                "system_resources": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                },
                "services": services_status,
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {
                "success": False,
                "healthy": False,
                "error": str(e)
            }


# Utilidades adicionales
class SchedulerConfig:
    """Configuración del scheduler"""

    @staticmethod
    def load_from_file(config_path: str) -> Dict[str, Any]:
        """Carga configuración desde archivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return {}

    @staticmethod
    def save_to_file(config: Dict[str, Any], config_path: str):
        """Guarda configuración a archivo JSON"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")

class SchedulerMonitor:
    """Monitor y métricas del scheduler"""

    def __init__(self, scheduler: IntegrationScheduler):
        self.scheduler = scheduler

    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte completo del scheduler"""
        status = self.scheduler.get_status()

        # Calcular métricas adicionales
        recent_executions = self.scheduler.executions[-100:]  # Últimas 100
        success_rate = 0
        if recent_executions:
            successful = len([e for e in recent_executions if e.status == TaskStatus.COMPLETED])
            success_rate = (successful / len(recent_executions)) * 100

        return {
            "timestamp": datetime.now().isoformat(),
            "scheduler_status": status,
            "success_rate_percent": round(success_rate, 2),
            "task_summary": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "success_count": task.success_count,
                    "failure_count": task.failure_count
                }
                for task_id, task in self.scheduler.tasks.items()
            }
        }


# Ejemplo de uso y main
if __name__ == "__main__":
    # Configuración por defecto
    config = {
        "max_workers": 4,
        "log_level": "INFO",
        "health_check_interval": 900  # 15 minutos
    }

    # Crear y configurar scheduler
    scheduler = IntegrationScheduler(config)

    try:
        # Iniciar scheduler
        logger.info("Iniciando Integration Scheduler...")
        scheduler.start()

    except KeyboardInterrupt:
        logger.info("Deteniendo scheduler...")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        scheduler.stop()
        sys.exit(1)
