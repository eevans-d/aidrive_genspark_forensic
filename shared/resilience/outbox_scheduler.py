"""
Programador de tareas para OutboxConsumer
Gestiona la ejecución periódica del procesamiento de mensajes outbox
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from .outbox_consumer import OutboxConsumer
# from ..config import get_settings  # TODO: Fix import path

logger = logging.getLogger(__name__)
settings = get_settings()

class OutboxScheduler:
    """
    Programador para el consumidor outbox con gestión de lifecycle
    """
    
    def __init__(self):
        self.consumer = OutboxConsumer()
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        
    async def start_scheduler(self):
        """Iniciar el programador de outbox"""
        if self.is_running:
            logger.warning("OutboxScheduler ya está ejecutándose")
            return
            
        self.is_running = True
        logger.info("🚀 Iniciando OutboxScheduler")
        
        # Crear tarea asíncrona para el consumidor
        self.task = asyncio.create_task(self._run_consumer_loop())
        
    async def stop_scheduler(self):
        """Detener el programador de outbox"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.consumer.stop_consuming()
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        logger.info("🛑 OutboxScheduler detenido")
        
    async def _run_consumer_loop(self):
        """Loop principal del consumidor"""
        try:
            await self.consumer.start_consuming()
        except asyncio.CancelledError:
            logger.info("OutboxConsumer cancelado")
        except Exception as e:
            logger.error(f"Error en OutboxConsumer: {e}")
            self.is_running = False
            
    def get_status(self) -> dict:
        """Obtener estado del scheduler"""
        return {
            "is_running": self.is_running,
            "task_done": self.task.done() if self.task else True,
            "timestamp": datetime.utcnow().isoformat()
        }

# Singleton global
outbox_scheduler = OutboxScheduler()

async def start_outbox_scheduler():
    """Función de conveniencia para iniciar el scheduler"""
    await outbox_scheduler.start_scheduler()
    
async def stop_outbox_scheduler():
    """Función de conveniencia para detener el scheduler"""
    await outbox_scheduler.stop_scheduler()
    
def get_outbox_status() -> dict:
    """Función de conveniencia para obtener estado"""
    return outbox_scheduler.get_status()