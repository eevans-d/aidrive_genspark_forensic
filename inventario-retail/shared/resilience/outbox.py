"""
Outbox Pattern para garantizar eventual consistency
"""
from sqlalchemy.orm import Session
from shared.models import OutboxMessage
from shared.database import get_db
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OutboxWorker:
    def __init__(self):
        self.running = False

    async def process_pending_messages(self):
        """Procesar mensajes pendientes en outbox"""
        db = next(get_db())
        try:
            # Obtener mensajes listos para retry
            now = datetime.utcnow()
            messages = db.query(OutboxMessage).filter(
                OutboxMessage.status.in_(["pending", "failed"]),
                OutboxMessage.retries < OutboxMessage.max_retries,
                OutboxMessage.next_retry_at <= now
            ).limit(10).all()

            for message in messages:
                try:
                    # Simular envío del mensaje
                    await self._send_message(message)
                    message.mark_sent()
                    db.commit()
                    logger.info(f"Mensaje enviado: {message.id}")
                except Exception as e:
                    message.mark_failed(str(e))
                    db.commit()
                    logger.error(f"Error enviando mensaje {message.id}: {e}")
        finally:
            db.close()

    async def _send_message(self, message: OutboxMessage):
        """Enviar mensaje (simular)"""
        # Aquí iría la lógica real de envío HTTP
        import asyncio
        await asyncio.sleep(0.1)  # Simular latencia
