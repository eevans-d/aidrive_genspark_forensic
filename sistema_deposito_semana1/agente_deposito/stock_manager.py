"""
Stock Manager - Sistema Gestión Depósito
Lógica ACID completa para control de stock y movimientos
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, func
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from decimal import Decimal

from .models import Producto, MovimientoStock
from .database import db_manager
from .schemas import StockUpdateRequest, TipoMovimiento

logger = logging.getLogger(__name__)

class StockManagerError(Exception):
    """Excepción personalizada para errores de gestión de stock"""
    pass

class InsufficientStockError(StockManagerError):
    """Error cuando no hay stock suficiente para una operación"""
    pass

class ProductoNotFoundError(StockManagerError):
    """Error cuando el producto no existe"""
    pass

class StockManager:
    """
    Gestor de Stock con control ACID completo

    Garantiza:
    - Atomicidad: Todas las operaciones se completan o fallan juntas
    - Consistencia: Stock nunca queda en estado inválido
    - Isolation: Transacciones concurrentes no interfieren
    - Durability: Cambios confirmados persisten
    """

    def __init__(self):
        self.logger = logger

    def update_stock(self, session: Session, request: StockUpdateRequest) -> Dict:
        """
        Actualiza stock de un producto con control ACID completo

        Args:
            session: Sesión de base de datos (debe estar en transacción)
            request: Datos de la actualización de stock

        Returns:
            Dict con resultado de la operación

        Raises:
            ProductoNotFoundError: Si el producto no existe
            InsufficientStockError: Si no hay stock suficiente
            StockManagerError: Para otros errores de negocio
        """
        try:
            # 1. Obtener producto con LOCK para evitar condiciones de carrera
            producto = session.query(Producto).filter(
                Producto.id == request.producto_id,
                Producto.activo == True
            ).with_for_update().first()

            if not producto:
                raise ProductoNotFoundError(f"Producto ID {request.producto_id} no encontrado o inactivo")

            # 2. Validar stock disponible para salidas
            stock_anterior = producto.stock_actual

            if request.tipo_movimiento == TipoMovimiento.SALIDA:
                if abs(request.cantidad) > stock_anterior:
                    raise InsufficientStockError(
                        f"Stock insuficiente. Disponible: {stock_anterior}, Solicitado: {abs(request.cantidad)}"
                    )
                cantidad_real = -abs(request.cantidad)  # Asegurar negativo para salidas
            elif request.tipo_movimiento == TipoMovimiento.ENTRADA:
                cantidad_real = abs(request.cantidad)  # Asegurar positivo para entradas
            else:
                cantidad_real = request.cantidad  # Para ajustes y transferencias

            # 3. Calcular nuevo stock
            stock_nuevo = stock_anterior + cantidad_real

            if stock_nuevo < 0:
                raise InsufficientStockError(f"El movimiento resultaría en stock negativo: {stock_nuevo}")

            # 4. Crear movimiento de stock
            valor_total = None
            if request.precio_unitario:
                valor_total = request.precio_unitario * abs(cantidad_real)

            movimiento = MovimientoStock(
                producto_id=request.producto_id,
                tipo_movimiento=request.tipo_movimiento,
                subtipo=request.subtipo,
                cantidad=cantidad_real,
                stock_anterior=stock_anterior,
                stock_posterior=stock_nuevo,
                precio_unitario=request.precio_unitario,
                valor_total=valor_total,
                documento_referencia=request.documento_referencia,
                usuario=request.usuario,
                observaciones=request.observaciones,
                ubicacion_origen=request.ubicacion_origen,
                ubicacion_destino=request.ubicacion_destino,
                fecha_movimiento=datetime.now(),
                estado='CONFIRMADO',
                fecha_confirmacion=datetime.now(),
                usuario_confirmacion=request.usuario
            )

            session.add(movimiento)

            # 5. Actualizar stock del producto
            producto.stock_actual = stock_nuevo
            producto.fecha_modificacion = datetime.now()

            # 6. Flush para obtener ID del movimiento antes del commit
            session.flush()

            self.logger.info(
                f"Stock actualizado: Producto {producto.codigo}, "
                f"Stock {stock_anterior} -> {stock_nuevo}, "
                f"Movimiento ID {movimiento.id}"
            )

            return {
                'success': True,
                'message': 'Stock actualizado exitosamente',
                'producto_id': request.producto_id,
                'stock_anterior': stock_anterior,
                'stock_nuevo': stock_nuevo,
                'movimiento_id': movimiento.id,
                'stock_critico': stock_nuevo <= producto.stock_minimo
            }

        except (ProductoNotFoundError, InsufficientStockError, StockManagerError):
            # Re-lanzar errores de negocio
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando stock: {e}")
            raise StockManagerError(f"Error interno actualizando stock: {str(e)}")

    def update_multiple_stock(self, requests: List[StockUpdateRequest]) -> Dict:
        """
        Actualiza stock de múltiples productos en una sola transacción ACID

        Args:
            requests: Lista de actualizaciones de stock

        Returns:
            Dict con resultado de todas las operaciones
        """
        results = []
        errors = []

        try:
            with db_manager.get_session() as session:
                # Procesar todos los movimientos en una sola transacción
                for i, request in enumerate(requests):
                    try:
                        result = self.update_stock(session, request)
                        results.append({
                            'index': i,
                            'producto_id': request.producto_id,
                            'result': result
                        })
                    except Exception as e:
                        errors.append({
                            'index': i,
                            'producto_id': request.producto_id,
                            'error': str(e)
                        })

                # Si hay errores, rollback automático por el context manager
                if errors:
                    raise StockManagerError(f"Errores en {len(errors)} operaciones")

                # Commit solo si todas las operaciones fueron exitosas
                session.commit()

                return {
                    'success': True,
                    'message': f'{len(results)} movimientos procesados exitosamente',
                    'results': results,
                    'errors': errors
                }

        except Exception as e:
            self.logger.error(f"Error en batch de actualizaciones: {e}")
            return {
                'success': False,
                'message': 'Error procesando movimientos en lote',
                'results': results,
                'errors': errors + [{'error': str(e)}]
            }

    def get_stock_movements(self, 
                           producto_id: Optional[int] = None,
                           tipo_movimiento: Optional[str] = None,
                           fecha_desde: Optional[datetime] = None,
                           fecha_hasta: Optional[datetime] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[MovimientoStock]:
        """
        Obtiene historial de movimientos de stock con filtros

        Args:
            producto_id: ID del producto (opcional)
            tipo_movimiento: Tipo de movimiento (opcional)
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
            limit: Límite de resultados
            offset: Offset para paginación

        Returns:
            Lista de movimientos de stock
        """
        try:
            with db_manager.get_session() as session:
                query = session.query(MovimientoStock)

                # Aplicar filtros
                if producto_id:
                    query = query.filter(MovimientoStock.producto_id == producto_id)

                if tipo_movimiento:
                    query = query.filter(MovimientoStock.tipo_movimiento == tipo_movimiento)

                if fecha_desde:
                    query = query.filter(MovimientoStock.fecha_movimiento >= fecha_desde)

                if fecha_hasta:
                    query = query.filter(MovimientoStock.fecha_movimiento <= fecha_hasta)

                # Ordenar por fecha descendente
                query = query.order_by(MovimientoStock.fecha_movimiento.desc())

                # Aplicar paginación
                movimientos = query.offset(offset).limit(limit).all()

                return movimientos

        except Exception as e:
            self.logger.error(f"Error obteniendo movimientos: {e}")
            raise StockManagerError(f"Error consultando movimientos: {str(e)}")

    def get_critical_stock_products(self) -> List[Producto]:
        """
        Obtiene productos con stock crítico (stock actual <= stock mínimo)

        Returns:
            Lista de productos con stock crítico
        """
        try:
            with db_manager.get_session() as session:
                productos_criticos = session.query(Producto).filter(
                    and_(
                        Producto.stock_actual <= Producto.stock_minimo,
                        Producto.activo == True
                    )
                ).order_by(
                    (Producto.stock_minimo - Producto.stock_actual).desc()
                ).all()

                return productos_criticos

        except Exception as e:
            self.logger.error(f"Error obteniendo productos críticos: {e}")
            raise StockManagerError(f"Error consultando productos críticos: {str(e)}")

    def validate_stock_consistency(self) -> Dict:
        """
        Valida la consistencia del stock comparando con el historial de movimientos

        Returns:
            Dict con resultado de la validación
        """
        inconsistencias = []

        try:
            with db_manager.get_session() as session:
                productos = session.query(Producto).filter(Producto.activo == True).all()

                for producto in productos:
                    # Obtener último movimiento
                    ultimo_movimiento = session.query(MovimientoStock).filter(
                        MovimientoStock.producto_id == producto.id
                    ).order_by(MovimientoStock.fecha_movimiento.desc()).first()

                    if ultimo_movimiento:
                        if ultimo_movimiento.stock_posterior != producto.stock_actual:
                            inconsistencias.append({
                                'producto_id': producto.id,
                                'codigo': producto.codigo,
                                'nombre': producto.nombre,
                                'stock_bd': producto.stock_actual,
                                'stock_movimiento': ultimo_movimiento.stock_posterior,
                                'diferencia': producto.stock_actual - ultimo_movimiento.stock_posterior,
                                'ultimo_movimiento_id': ultimo_movimiento.id,
                                'fecha_ultimo_movimiento': ultimo_movimiento.fecha_movimiento
                            })

                return {
                    'consistente': len(inconsistencias) == 0,
                    'total_productos_verificados': len(productos),
                    'inconsistencias_encontradas': len(inconsistencias),
                    'inconsistencias': inconsistencias
                }

        except Exception as e:
            self.logger.error(f"Error validando consistencia: {e}")
            raise StockManagerError(f"Error en validación de consistencia: {str(e)}")

    def fix_stock_inconsistency(self, producto_id: int, usuario: str) -> Dict:
        """
        Corrige inconsistencia de stock ajustando al último movimiento

        Args:
            producto_id: ID del producto a corregir
            usuario: Usuario que ejecuta la corrección

        Returns:
            Dict con resultado de la corrección
        """
        try:
            with db_manager.get_session() as session:
                # Obtener producto
                producto = session.query(Producto).filter(
                    Producto.id == producto_id
                ).with_for_update().first()

                if not producto:
                    raise ProductoNotFoundError(f"Producto ID {producto_id} no encontrado")

                # Obtener último movimiento
                ultimo_movimiento = session.query(MovimientoStock).filter(
                    MovimientoStock.producto_id == producto_id
                ).order_by(MovimientoStock.fecha_movimiento.desc()).first()

                if not ultimo_movimiento:
                    raise StockManagerError("No hay movimientos para este producto")

                stock_actual = producto.stock_actual
                stock_correcto = ultimo_movimiento.stock_posterior

                if stock_actual == stock_correcto:
                    return {
                        'success': True,
                        'message': 'Stock ya está consistente',
                        'ajuste_realizado': False
                    }

                # Crear movimiento de ajuste
                diferencia = stock_correcto - stock_actual

                movimiento_ajuste = MovimientoStock(
                    producto_id=producto_id,
                    tipo_movimiento=TipoMovimiento.AJUSTE,
                    subtipo='CORRECCION_SISTEMA',
                    cantidad=diferencia,
                    stock_anterior=stock_actual,
                    stock_posterior=stock_correcto,
                    usuario=usuario,
                    observaciones=f'Corrección automática de inconsistencia. '
                                 f'Stock BD: {stock_actual}, Stock correcto: {stock_correcto}',
                    fecha_movimiento=datetime.now(),
                    estado='CONFIRMADO',
                    fecha_confirmacion=datetime.now(),
                    usuario_confirmacion=usuario
                )

                session.add(movimiento_ajuste)

                # Actualizar stock del producto
                producto.stock_actual = stock_correcto
                producto.fecha_modificacion = datetime.now()

                session.commit()

                self.logger.info(
                    f"Corrección de stock: Producto {producto.codigo}, "
                    f"Stock {stock_actual} -> {stock_correcto}"
                )

                return {
                    'success': True,
                    'message': 'Stock corregido exitosamente',
                    'ajuste_realizado': True,
                    'stock_anterior': stock_actual,
                    'stock_corregido': stock_correcto,
                    'diferencia': diferencia,
                    'movimiento_id': movimiento_ajuste.id
                }

        except Exception as e:
            self.logger.error(f"Error corrigiendo stock: {e}")
            raise StockManagerError(f"Error en corrección de stock: {str(e)}")

    def get_stock_summary(self) -> Dict:
        """
        Obtiene resumen general del estado del stock

        Returns:
            Dict con resumen del stock
        """
        try:
            with db_manager.get_session() as session:
                # Estadísticas básicas
                total_productos = session.query(Producto).filter(Producto.activo == True).count()

                productos_sin_stock = session.query(Producto).filter(
                    and_(Producto.stock_actual == 0, Producto.activo == True)
                ).count()

                productos_stock_critico = session.query(Producto).filter(
                    and_(
                        Producto.stock_actual <= Producto.stock_minimo,
                        Producto.activo == True,
                        Producto.stock_actual > 0
                    )
                ).count()

                # Valor total del inventario
                valor_inventario = session.query(
                    func.sum(Producto.stock_actual * Producto.precio_costo)
                ).filter(Producto.activo == True).scalar() or Decimal('0')

                # Categorías con stock crítico
                categorias_criticas = session.query(Producto.categoria).filter(
                    and_(
                        Producto.stock_actual <= Producto.stock_minimo,
                        Producto.activo == True
                    )
                ).distinct().all()

                # Movimientos recientes (últimos 7 días)
                fecha_limite = datetime.now() - timedelta(days=7)
                movimientos_recientes = session.query(MovimientoStock).filter(
                    MovimientoStock.fecha_movimiento >= fecha_limite
                ).count()

                return {
                    'total_productos': total_productos,
                    'productos_sin_stock': productos_sin_stock,
                    'productos_stock_critico': productos_stock_critico,
                    'valor_total_inventario': float(valor_inventario),
                    'categorias_con_stock_critico': [cat[0] for cat in categorias_criticas],
                    'movimientos_ultimos_7_dias': movimientos_recientes,
                    'porcentaje_stock_critico': round((productos_stock_critico / total_productos * 100), 2) if total_productos > 0 else 0,
                    'fecha_consulta': datetime.now()
                }

        except Exception as e:
            self.logger.error(f"Error obteniendo resumen: {e}")
            raise StockManagerError(f"Error consultando resumen de stock: {str(e)}")

# Instancia global del gestor de stock
stock_manager = StockManager()

# Para usar con timedelta
from datetime import timedelta
