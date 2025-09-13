"""
Consumidor del patrón Outbox para garantizar entrega de mensajes
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# from shared.database import get_db  # TODO: Fix import path
# from shared.models import OutboxEvent  # TODO: Fix import path

logger = logging.getLogger(__name__)

class OutboxConsumer:
    """
    Consumidor que procesa eventos pendientes del patrón Outbox
    Garantiza entrega eventual de mensajes entre microservicios
    """
    
    def __init__(self):
        self.is_running = False
        self.poll_interval = 5  # segundos
        self.max_retries = 3
        self.retry_delay = 60  # segundos
        
    async def start_consuming(self):
        """Iniciar el consumidor de eventos outbox"""
        self.is_running = True
        logger.info("🚀 Iniciando OutboxConsumer")
        
        while self.is_running:
            try:
                await self._process_pending_events()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error en OutboxConsumer: {e}")
                await asyncio.sleep(self.poll_interval * 2)
    
    def stop_consuming(self):
        """Detener el consumidor"""
        self.is_running = False
        logger.info("🛑 Deteniendo OutboxConsumer")
    
    async def _process_pending_events(self):
        """Procesar eventos pendientes"""
        db = next(get_db())
        try:
            # Obtener eventos pendientes
            pending_events = db.query(OutboxEvent).filter(
                OutboxEvent.processed == False,
                OutboxEvent.retry_count < self.max_retries,
                OutboxEvent.next_retry_at <= datetime.utcnow()
            ).order_by(OutboxEvent.created_at).limit(50).all()
            
            for event in pending_events:
                try:
                    await self._process_event(event, db)
                except Exception as e:
                    logger.error(f"Error procesando evento {event.id}: {e}")
                    await self._handle_event_failure(event, db)
                    
        finally:
            db.close()
    
    async def _process_event(self, event: OutboxEvent, db: Session):
        """Procesar un evento específico"""
        logger.info(f"Procesando evento {event.id}: {event.event_type}")
        
        # Simular procesamiento del evento
        event_data = json.loads(event.event_data)
        
        if event.event_type == "STOCK_UPDATED":
            await self._handle_stock_update(event_data)
        elif event.event_type == "PRODUCT_CREATED":
            await self._handle_product_created(event_data)
        elif event.event_type == "INVOICE_PROCESSED":
            await self._handle_invoice_processed(event_data)
        else:
            logger.warning(f"Tipo de evento desconocido: {event.event_type}")
        
        # Marcar como procesado
        event.processed = True
        event.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Evento {event.id} procesado exitosamente")
    
    async def _handle_event_failure(self, event: OutboxEvent, db: Session):
        """Manejar falla en procesamiento de evento"""
        event.retry_count += 1
        event.next_retry_at = datetime.utcnow() + timedelta(
            seconds=self.retry_delay * (2 ** event.retry_count)  # Backoff exponencial
        )
        
        if event.retry_count >= self.max_retries:
            event.failed = True
            logger.error(f"❌ Evento {event.id} falló después de {self.max_retries} intentos")
        
        db.commit()
    
    async def _handle_stock_update(self, data: Dict):
        """Manejar evento de actualización de stock"""
        # Aquí se enviaría notificación a otros servicios
        logger.info(f"Notificando actualización de stock: {data}")
        
    async def _handle_product_created(self, data: Dict):
        """Manejar evento de producto creado"""
        # Aquí se sincronizaría con servicios externos
        logger.info(f"Notificando nuevo producto: {data}")
        
    async def _handle_invoice_processed(self, data: Dict):
        """Manejar evento de factura procesada"""
        # Aquí se actualizarían sistemas contables
        logger.info(f"Notificando factura procesada: {data}")

# Singleton para uso global
outbox_consumer = OutboxConsumer()

async def start_outbox_consumer():
    """Función para iniciar el consumidor"""
    await outbox_consumer.start_consuming()

def stop_outbox_consumer():
    """Función para detener el consumidor"""
    outbox_consumer.stop_consuming()