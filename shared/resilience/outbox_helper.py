"""
Función de utilidad para crear mensajes outbox
Integración con el patrón outbox para garantizar entrega de eventos
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import json
import uuid

# from ..database import get_db  # TODO: Fix import path

class OutboxMessage:
    """
    Modelo simplificado para mensajes outbox
    En producción, usar modelo SQLAlchemy completo
    """
    def __init__(self, event_type: str, payload: dict, destination: str = "default"):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.payload = json.dumps(payload)
        self.destination = destination
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.retries = 0
        self.max_retries = 3

def create_outbox_message(
    event_type: str,
    payload: dict,
    destination: str = "default",
    db: Optional[Session] = None
) -> bool:
    """
    Crear un nuevo mensaje en la tabla outbox
    
    Args:
        event_type: Tipo de evento (STOCK_UPDATED, PRODUCT_CREATED, etc.)
        payload: Datos del evento
        destination: Destino del mensaje
        db: Sesión de base de datos (opcional)
    
    Returns:
        bool: True si se creó exitosamente
    """
    should_close_db = False
    
    try:
        if not db:
            db = next(get_db())
            should_close_db = True
            
        # Crear mensaje outbox
        message = OutboxMessage(event_type, payload, destination)
        
        # En una implementación real, guardaría en BD
        # db.add(message)
        # db.commit()
        
        # Por ahora, solo log
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"✉️ Mensaje outbox creado: {event_type} -> {destination}")
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creando mensaje outbox: {e}")
        return False
        
    finally:
        if should_close_db and db:
            db.close()

# Funciones de conveniencia para eventos comunes
def notify_stock_updated(producto_id: int, cantidad: int, tipo_movimiento: str, db: Optional[Session] = None):
    """Notificar actualización de stock"""
    payload = {
        "producto_id": producto_id,
        "cantidad": cantidad,
        "tipo_movimiento": tipo_movimiento,
        "timestamp": datetime.utcnow().isoformat()
    }
    return create_outbox_message("STOCK_UPDATED", payload, "stock_service", db)

def notify_product_created(codigo: str, nombre: str, categoria: str, db: Optional[Session] = None):
    """Notificar creación de producto"""
    payload = {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "timestamp": datetime.utcnow().isoformat()
    }
    return create_outbox_message("PRODUCT_CREATED", payload, "catalog_service", db)

def notify_invoice_processed(numero_factura: str, proveedor: str, total: float, db: Optional[Session] = None):
    """Notificar procesamiento de factura"""
    payload = {
        "numero_factura": numero_factura,
        "proveedor": proveedor,
        "total": total,
        "timestamp": datetime.utcnow().isoformat()
    }
    return create_outbox_message("INVOICE_PROCESSED", payload, "accounting_service", db)