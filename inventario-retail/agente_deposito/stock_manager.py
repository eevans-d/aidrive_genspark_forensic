"""
StockManager - Lógica ACID para gestión de stock
Transacciones robustas con rollback automático
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from shared.models import Producto, MovimientoStock
from shared.config import get_settings
from .exceptions import StockInsuficienteError, ProductoNoEncontradoError

logger = logging.getLogger(__name__)
settings = get_settings()

class StockUpdateRequest(BaseModel):
    """Request para actualización de stock"""
    producto_id: int
    tipo_movimiento: str  # entrada, salida, ajuste
    cantidad: int  # positivo=entrada, negativo=salida
    motivo: Optional[str] = None
    referencia: Optional[str] = None
    precio_unitario: Optional[float] = None
    usuario: Optional[str] = "sistema"
    idempotency_key: Optional[str] = None

class StockUpdateResponse(BaseModel):
    """Response de actualización de stock"""
    success: bool
    movimiento_id: int
    producto_id: int
    stock_anterior: int
    stock_nuevo: int
    mensaje: str

class StockManager:
    """Manager para operaciones ACID de stock"""

    def update_stock(self, db: Session, request: StockUpdateRequest) -> StockUpdateResponse:
        """
        Actualizar stock con transacción ACID
        Garantiza consistencia y auditoría completa
        """
        try:
            # Iniciar transacción explícita
            with db.begin():
                # Verificar idempotencia
                if request.idempotency_key:
                    existing_mov = db.query(MovimientoStock).filter(
                        MovimientoStock.idempotency_key == request.idempotency_key
                    ).first()

                    if existing_mov:
                        logger.info(f"Operación idempotente detectada: {request.idempotency_key}")
                        return StockUpdateResponse(
                            success=True,
                            movimiento_id=existing_mov.id,
                            producto_id=existing_mov.producto_id,
                            stock_anterior=existing_mov.stock_anterior,
                            stock_nuevo=existing_mov.stock_posterior,
                            mensaje="Operación ya procesada (idempotente)"
                        )

                # Obtener producto con lock FOR UPDATE
                producto = db.query(Producto).filter(
                    Producto.id == request.producto_id
                ).with_for_update().first()

                if not producto:
                    raise ProductoNoEncontradoError(f"Producto {request.producto_id} no encontrado")

                # Validar stock suficiente para salidas
                stock_anterior = producto.stock_actual
                stock_nuevo = stock_anterior + request.cantidad

                if stock_nuevo < 0:
                    raise StockInsuficienteError(
                        f"Stock insuficiente. Actual: {stock_anterior}, Solicitado: {abs(request.cantidad)}",
                        stock_actual=stock_anterior
                    )

                # Actualizar stock del producto
                producto.stock_actual = stock_nuevo

                # Crear movimiento de auditoría
                movimiento = MovimientoStock(
                    producto_id=request.producto_id,
                    tipo_movimiento=request.tipo_movimiento,
                    cantidad=request.cantidad,
                    stock_anterior=stock_anterior,
                    stock_posterior=stock_nuevo,
                    motivo=request.motivo,
                    referencia=request.referencia,
                    precio_unitario=request.precio_unitario,
                    usuario=request.usuario,
                    agente_origen="agente_deposito",
                    idempotency_key=request.idempotency_key
                )

                db.add(movimiento)
                db.flush()  # Para obtener ID del movimiento

                logger.info(
                    f"Stock actualizado - Producto: {request.producto_id}, "
                    f"Anterior: {stock_anterior}, Nuevo: {stock_nuevo}, "
                    f"Movimiento: {movimiento.id}"
                )

                return StockUpdateResponse(
                    success=True,
                    movimiento_id=movimiento.id,
                    producto_id=request.producto_id,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_nuevo,
                    mensaje="Stock actualizado exitosamente"
                )

        except (StockInsuficienteError, ProductoNoEncontradoError):
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error en actualización de stock: {e}")
            raise SQLAlchemyError(f"Error en base de datos: {e}")
