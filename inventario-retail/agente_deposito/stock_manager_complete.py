"""
Stock Manager Complete - Gestión ACID avanzada
Versión: 2.0 - Production Ready

Características:
- Transacciones ACID completas
- Manejo de concurrencia optimista
- Rollback automático
- Audit trail completo
- Performance optimizado
- Error handling robusto
"""

import logging
from contextlib import contextmanager
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, func, select, update
from sqlalchemy.orm.exc import StaleDataError

from .models import Producto, MovimientoStock
from .schemas import TipoMovimiento, StockUpdateRequest, StockAdjustmentRequest, StockMovementRequest

# Configurar logging
logger = logging.getLogger(__name__)

class StockManagerError(Exception):
    """Excepción base para errores del StockManager"""
    pass

class InsufficientStockError(StockManagerError):
    """Error cuando no hay suficiente stock"""
    pass

class ProductNotFoundError(StockManagerError):
    """Error cuando no se encuentra el producto"""
    pass

class ConcurrencyError(StockManagerError):
    """Error de concurrencia en operaciones de stock"""
    pass


class StockManagerComplete:
    """
    Gestor completo de stock con transacciones ACID y manejo de concurrencia
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    @contextmanager
    def transaction(self):
        """
        Context manager para transacciones ACID con rollback automático
        """
        savepoint = None
        try:
            # Crear savepoint para nested transactions
            savepoint = self.db.begin_nested() if self.db.in_transaction() else None
            yield
            if savepoint:
                savepoint.commit()
            else:
                self.db.commit()
            logger.debug("Transacción de stock completada exitosamente")
        except Exception as e:
            if savepoint:
                savepoint.rollback()
            else:
                self.db.rollback()
            logger.error(f"Error en transacción de stock, rollback ejecutado: {str(e)}")
            raise

    def _get_producto_with_lock(self, producto_id: int) -> Producto:
        """
        Obtiene producto con lock optimista para prevenir condiciones de carrera
        """
        producto = self.db.query(Producto).filter(
            Producto.id == producto_id,
            Producto.activo == True
        ).with_for_update().first()

        if not producto:
            raise ProductNotFoundError(f"Producto con ID {producto_id} no encontrado o inactivo")

        return producto

    def _validate_stock_operation(self, producto: Producto, cantidad: int, operacion: str):
        """
        Valida que la operación de stock sea válida
        """
        if operacion == "SALIDA" and producto.stock_actual < cantidad:
            raise InsufficientStockError(
                f"Stock insuficiente para producto {producto.codigo}. "
                f"Stock actual: {producto.stock_actual}, Solicitado: {cantidad}"
            )

        nueva_cantidad = producto.stock_actual + cantidad if operacion == "ENTRADA" else producto.stock_actual - cantidad

        if nueva_cantidad < 0:
            raise InsufficientStockError(
                f"La operación resultaría en stock negativo para producto {producto.codigo}"
            )

        if operacion == "ENTRADA" and nueva_cantidad > producto.stock_maximo:
            logger.warning(
                f"Producto {producto.codigo} excederá stock máximo. "
                f"Nuevo stock: {nueva_cantidad}, Máximo: {producto.stock_maximo}"
            )

    def _create_movimiento(
        self, 
        producto: Producto, 
        tipo_movimiento: TipoMovimiento, 
        cantidad: int,
        cantidad_anterior: int,
        cantidad_nueva: int,
        motivo: Optional[str] = None,
        referencia: Optional[str] = None,
        usuario: Optional[str] = None
    ) -> MovimientoStock:
        """
        Crea registro de movimiento de stock para audit trail
        """
        movimiento = MovimientoStock(
            producto_id=producto.id,
            tipo_movimiento=tipo_movimiento.value,
            cantidad=cantidad,
            cantidad_anterior=cantidad_anterior,
            cantidad_nueva=cantidad_nueva,
            motivo=motivo,
            referencia=referencia,
            usuario=usuario or "SYSTEM",
            fecha_movimiento=datetime.utcnow()
        )

        self.db.add(movimiento)
        return movimiento

    def update_stock(self, request: StockUpdateRequest) -> Tuple[Producto, MovimientoStock]:
        """
        Actualiza stock a una cantidad específica con transacción ACID
        """
        with self.transaction():
            try:
                producto = self._get_producto_with_lock(request.producto_id)
                cantidad_anterior = producto.stock_actual

                if cantidad_anterior == request.nueva_cantidad:
                    logger.info(f"Stock ya está en la cantidad solicitada para producto {producto.codigo}")
                    return producto, None

                # Actualizar stock
                producto.stock_actual = request.nueva_cantidad
                producto.updated_at = datetime.utcnow()

                # Crear movimiento de ajuste
                cantidad_diferencia = request.nueva_cantidad - cantidad_anterior
                movimiento = self._create_movimiento(
                    producto=producto,
                    tipo_movimiento=TipoMovimiento.AJUSTE,
                    cantidad=cantidad_diferencia,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=request.nueva_cantidad,
                    motivo=request.motivo or "Actualización directa de stock",
                    usuario=request.usuario
                )

                self.db.flush()  # Forzar SQL execution

                logger.info(
                    f"Stock actualizado para producto {producto.codigo}: "
                    f"{cantidad_anterior} → {request.nueva_cantidad}"
                )

                return producto, movimiento

            except StaleDataError:
                raise ConcurrencyError("Conflicto de concurrencia detectado. Intente nuevamente.")

    def adjust_stock(self, request: StockAdjustmentRequest) -> Tuple[Producto, MovimientoStock]:
        """
        Ajusta stock por una cantidad específica (+ o -)
        """
        with self.transaction():
            try:
                producto = self._get_producto_with_lock(request.producto_id)
                cantidad_anterior = producto.stock_actual
                cantidad_nueva = cantidad_anterior + request.cantidad_ajuste

                # Validar que no resulte en stock negativo
                if cantidad_nueva < 0:
                    raise InsufficientStockError(
                        f"El ajuste resultaría en stock negativo. "
                        f"Stock actual: {cantidad_anterior}, Ajuste: {request.cantidad_ajuste}"
                    )

                # Actualizar stock
                producto.stock_actual = cantidad_nueva
                producto.updated_at = datetime.utcnow()

                # Determinar tipo de movimiento
                tipo_movimiento = TipoMovimiento.ENTRADA if request.cantidad_ajuste > 0 else TipoMovimiento.SALIDA

                # Crear movimiento
                movimiento = self._create_movimiento(
                    producto=producto,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=abs(request.cantidad_ajuste),
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=cantidad_nueva,
                    motivo=request.motivo,
                    usuario=request.usuario
                )

                self.db.flush()

                logger.info(
                    f"Stock ajustado para producto {producto.codigo}: "
                    f"{cantidad_anterior} → {cantidad_nueva} (ajuste: {request.cantidad_ajuste:+d})"
                )

                return producto, movimiento

            except StaleDataError:
                raise ConcurrencyError("Conflicto de concurrencia detectado. Intente nuevamente.")

    def process_movement(self, request: StockMovementRequest) -> Tuple[Producto, MovimientoStock]:
        """
        Procesa movimiento de stock (entrada o salida)
        """
        with self.transaction():
            try:
                producto = self._get_producto_with_lock(request.producto_id)
                cantidad_anterior = producto.stock_actual

                # Validar operación
                self._validate_stock_operation(producto, request.cantidad, request.tipo_movimiento.value)

                # Calcular nueva cantidad
                if request.tipo_movimiento == TipoMovimiento.ENTRADA:
                    cantidad_nueva = cantidad_anterior + request.cantidad
                else:  # SALIDA
                    cantidad_nueva = cantidad_anterior - request.cantidad

                # Actualizar stock
                producto.stock_actual = cantidad_nueva
                producto.updated_at = datetime.utcnow()

                # Crear movimiento
                movimiento = self._create_movimiento(
                    producto=producto,
                    tipo_movimiento=request.tipo_movimiento,
                    cantidad=request.cantidad,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=cantidad_nueva,
                    motivo=request.motivo,
                    referencia=request.referencia,
                    usuario=request.usuario
                )

                self.db.flush()

                logger.info(
                    f"Movimiento procesado para producto {producto.codigo}: "
                    f"{request.tipo_movimiento.value} de {request.cantidad} unidades. "
                    f"Stock: {cantidad_anterior} → {cantidad_nueva}"
                )

                return producto, movimiento

            except StaleDataError:
                raise ConcurrencyError("Conflicto de concurrencia detectado. Intente nuevamente.")

    def bulk_stock_update(self, updates: List[StockUpdateRequest]) -> List[Tuple[Producto, MovimientoStock]]:
        """
        Actualización masiva de stock con transacción única
        """
        results = []

        with self.transaction():
            try:
                for update_request in updates:
                    producto, movimiento = self.update_stock(update_request)
                    results.append((producto, movimiento))

                logger.info(f"Actualización masiva completada: {len(updates)} productos actualizados")
                return results

            except Exception as e:
                logger.error(f"Error en actualización masiva: {str(e)}")
                raise

    def get_stock_movements_history(
        self, 
        producto_id: Optional[int] = None, 
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        tipo_movimiento: Optional[TipoMovimiento] = None,
        limit: int = 100
    ) -> List[MovimientoStock]:
        """
        Obtiene historial de movimientos de stock con filtros
        """
        query = self.db.query(MovimientoStock)

        if producto_id:
            query = query.filter(MovimientoStock.producto_id == producto_id)

        if fecha_desde:
            query = query.filter(MovimientoStock.fecha_movimiento >= fecha_desde)

        if fecha_hasta:
            query = query.filter(MovimientoStock.fecha_movimiento <= fecha_hasta)

        if tipo_movimiento:
            query = query.filter(MovimientoStock.tipo_movimiento == tipo_movimiento.value)

        return query.order_by(MovimientoStock.fecha_movimiento.desc()).limit(limit).all()

    def get_productos_stock_critico(self) -> List[Producto]:
        """
        Obtiene productos con stock crítico (stock_actual <= stock_minimo)
        """
        return self.db.query(Producto).filter(
            and_(
                Producto.activo == True,
                Producto.stock_actual <= Producto.stock_minimo
            )
        ).order_by(Producto.stock_actual.asc()).all()

    def get_productos_sobrestock(self) -> List[Producto]:
        """
        Obtiene productos con sobrestock (stock_actual >= stock_maximo)
        """
        return self.db.query(Producto).filter(
            and_(
                Producto.activo == True,
                Producto.stock_actual >= Producto.stock_maximo
            )
        ).order_by(Producto.stock_actual.desc()).all()

    def validate_stock_integrity(self) -> dict:
        """
        Valida la integridad del stock comparando con movimientos
        """
        inconsistencies = []

        # Obtener todos los productos activos
        productos = self.db.query(Producto).filter(Producto.activo == True).all()

        for producto in productos:
            # Calcular stock según movimientos
            movimientos = self.db.query(MovimientoStock).filter(
                MovimientoStock.producto_id == producto.id
            ).order_by(MovimientoStock.fecha_movimiento.asc()).all()

            stock_calculado = 0
            for mov in movimientos:
                if mov.tipo_movimiento == "ENTRADA":
                    stock_calculado += mov.cantidad
                elif mov.tipo_movimiento == "SALIDA":
                    stock_calculado -= mov.cantidad
                else:  # AJUSTE
                    stock_calculado = mov.cantidad_nueva

            if stock_calculado != producto.stock_actual:
                inconsistencies.append({
                    "producto_id": producto.id,
                    "codigo": producto.codigo,
                    "stock_actual": producto.stock_actual,
                    "stock_calculado": stock_calculado,
                    "diferencia": producto.stock_actual - stock_calculado
                })

        return {
            "total_productos_revisados": len(productos),
            "inconsistencias_encontradas": len(inconsistencies),
            "inconsistencias": inconsistencies,
            "integridad_ok": len(inconsistencies) == 0
        }
