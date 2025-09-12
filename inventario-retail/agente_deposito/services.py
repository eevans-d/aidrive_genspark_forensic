"""
Services - Business Logic Layer
Versión: 2.0 - Production Ready

Servicios de negocio que encapsulan la lógica de dominio:
- ProductoService: Gestión completa de productos
- StockService: Operaciones de stock con validaciones
- ReporteService: Generación de reportes y estadísticas
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from math import ceil

from .models import Producto, MovimientoStock, ConfiguracionSistema
from .schemas import (
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoFilters,
    StockUpdateRequest, StockAdjustmentRequest, StockMovementRequest,
    TipoMovimiento, PaginacionParams, PaginatedResponse,
    StockCriticoResponse, ReporteStockResponse
)
from .stock_manager_complete import StockManagerComplete, StockManagerError

# Configurar logging
logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Excepción base para errores de servicios"""
    pass

class ValidationError(ServiceError):
    """Error de validación de business logic"""
    pass

class NotFoundError(ServiceError):
    """Error cuando no se encuentra el recurso"""
    pass


class ProductoService:
    """
    Servicio para gestión completa de productos
    """

    def __init__(self, db: Session):
        self.db = db
        self.stock_manager = StockManagerComplete(db)

    def create_producto(self, producto_data: ProductoCreate) -> ProductoResponse:
        """
        Crea un nuevo producto con validaciones business
        """
        # Validar código único
        existing = self.db.query(Producto).filter(Producto.codigo == producto_data.codigo).first()
        if existing:
            raise ValidationError(f"Ya existe un producto con código: {producto_data.codigo}")

        # Validar reglas de negocio
        self._validate_producto_business_rules(producto_data)

        # Crear producto
        producto = Producto(**producto_data.model_dump())
        producto.created_at = datetime.utcnow()
        producto.updated_at = datetime.utcnow()

        try:
            self.db.add(producto)
            self.db.commit()
            self.db.refresh(producto)

            logger.info(f"Producto creado exitosamente: {producto.codigo}")

            # Si hay stock inicial, crear movimiento de entrada
            if producto_data.stock_actual > 0:
                stock_request = StockMovementRequest(
                    producto_id=producto.id,
                    tipo_movimiento=TipoMovimiento.ENTRADA,
                    cantidad=producto_data.stock_actual,
                    motivo="Stock inicial",
                    usuario="SYSTEM"
                )
                self.stock_manager.process_movement(stock_request)

            return ProductoResponse.model_validate(producto)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando producto: {str(e)}")
            raise ServiceError(f"Error al crear producto: {str(e)}")

    def get_producto(self, producto_id: int) -> Optional[ProductoResponse]:
        """
        Obtiene un producto por ID
        """
        producto = self.db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            return None

        return ProductoResponse.model_validate(producto)

    def get_producto_by_codigo(self, codigo: str) -> Optional[ProductoResponse]:
        """
        Obtiene un producto por código
        """
        producto = self.db.query(Producto).filter(Producto.codigo == codigo).first()
        if not producto:
            return None

        return ProductoResponse.model_validate(producto)

    def update_producto(self, producto_id: int, update_data: ProductoUpdate) -> ProductoResponse:
        """
        Actualiza un producto existente
        """
        producto = self.db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise NotFoundError(f"Producto con ID {producto_id} no encontrado")

        # Aplicar actualizaciones
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(producto, field, value)

        producto.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(producto)

            logger.info(f"Producto actualizado: {producto.codigo}")
            return ProductoResponse.model_validate(producto)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando producto: {str(e)}")
            raise ServiceError(f"Error al actualizar producto: {str(e)}")

    def delete_producto(self, producto_id: int) -> bool:
        """
        Elimina un producto (soft delete)
        """
        producto = self.db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise NotFoundError(f"Producto con ID {producto_id} no encontrado")

        # Verificar si tiene stock
        if producto.stock_actual > 0:
            raise ValidationError("No se puede eliminar un producto con stock existente")

        # Soft delete
        producto.activo = False
        producto.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            logger.info(f"Producto eliminado (soft delete): {producto.codigo}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando producto: {str(e)}")
            raise ServiceError(f"Error al eliminar producto: {str(e)}")

    def get_productos_paginated(
        self, 
        pagination: PaginacionParams, 
        filters: Optional[ProductoFilters] = None
    ) -> PaginatedResponse:
        """
        Obtiene productos con paginación y filtros
        """
        query = self.db.query(Producto)

        # Aplicar filtros
        if filters:
            if filters.codigo:
                query = query.filter(Producto.codigo.ilike(f"%{filters.codigo}%"))
            if filters.nombre:
                query = query.filter(Producto.nombre.ilike(f"%{filters.nombre}%"))
            if filters.categoria:
                query = query.filter(Producto.categoria.ilike(f"%{filters.categoria}%"))
            if filters.activo is not None:
                query = query.filter(Producto.activo == filters.activo)
            if filters.stock_critico:
                query = query.filter(Producto.stock_actual <= Producto.stock_minimo)
            if filters.sobrestock:
                query = query.filter(Producto.stock_actual >= Producto.stock_maximo)

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (pagination.page - 1) * pagination.size
        productos = query.offset(offset).limit(pagination.size).all()

        # Convertir a respuesta
        items = [ProductoResponse.model_validate(p).model_dump() for p in productos]

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=ceil(total / pagination.size)
        )

    def search_productos(self, query: str, limit: int = 20) -> List[ProductoResponse]:
        """
        Búsqueda full-text de productos
        """
        productos = self.db.query(Producto).filter(
            and_(
                Producto.activo == True,
                or_(
                    Producto.codigo.ilike(f"%{query}%"),
                    Producto.nombre.ilike(f"%{query}%"),
                    Producto.descripcion.ilike(f"%{query}%"),
                    Producto.categoria.ilike(f"%{query}%")
                )
            )
        ).limit(limit).all()

        return [ProductoResponse.model_validate(p) for p in productos]

    def _validate_producto_business_rules(self, producto_data):
        """
        Valida reglas de negocio para productos
        """
        if producto_data.stock_minimo > producto_data.stock_maximo:
            raise ValidationError("Stock mínimo no puede ser mayor que stock máximo")

        if producto_data.precio <= 0:
            raise ValidationError("El precio debe ser mayor que cero")

        if len(producto_data.codigo) < 3:
            raise ValidationError("El código debe tener al menos 3 caracteres")


class StockService:
    """
    Servicio para operaciones de stock con business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.stock_manager = StockManagerComplete(db)
        self.producto_service = ProductoService(db)

    def update_stock(self, request: StockUpdateRequest) -> dict:
        """
        Actualiza stock con validaciones de negocio
        """
        try:
            # Validar que el producto existe
            producto = self.producto_service.get_producto(request.producto_id)
            if not producto:
                raise NotFoundError(f"Producto con ID {request.producto_id} no encontrado")

            # Procesar actualización
            producto_actualizado, movimiento = self.stock_manager.update_stock(request)

            return {
                "success": True,
                "message": f"Stock actualizado para producto {producto_actualizado.codigo}",
                "producto": ProductoResponse.model_validate(producto_actualizado).model_dump(),
                "movimiento_id": movimiento.id if movimiento else None
            }

        except StockManagerError as e:
            logger.error(f"Error en StockManager: {str(e)}")
            raise ServiceError(str(e))

    def adjust_stock(self, request: StockAdjustmentRequest) -> dict:
        """
        Ajusta stock con validaciones
        """
        try:
            producto = self.producto_service.get_producto(request.producto_id)
            if not producto:
                raise NotFoundError(f"Producto con ID {request.producto_id} no encontrado")

            producto_actualizado, movimiento = self.stock_manager.adjust_stock(request)

            return {
                "success": True,
                "message": f"Stock ajustado para producto {producto_actualizado.codigo}",
                "producto": ProductoResponse.model_validate(producto_actualizado).model_dump(),
                "movimiento": {
                    "id": movimiento.id,
                    "tipo": movimiento.tipo_movimiento,
                    "cantidad": movimiento.cantidad,
                    "cantidad_anterior": movimiento.cantidad_anterior,
                    "cantidad_nueva": movimiento.cantidad_nueva
                }
            }

        except StockManagerError as e:
            logger.error(f"Error en StockManager: {str(e)}")
            raise ServiceError(str(e))

    def process_movement(self, request: StockMovementRequest) -> dict:
        """
        Procesa movimiento de stock
        """
        try:
            producto = self.producto_service.get_producto(request.producto_id)
            if not producto:
                raise NotFoundError(f"Producto con ID {request.producto_id} no encontrado")

            producto_actualizado, movimiento = self.stock_manager.process_movement(request)

            return {
                "success": True,
                "message": f"Movimiento {request.tipo_movimiento.value} procesado",
                "producto": ProductoResponse.model_validate(producto_actualizado).model_dump(),
                "movimiento": {
                    "id": movimiento.id,
                    "tipo": movimiento.tipo_movimiento,
                    "cantidad": movimiento.cantidad,
                    "stock_anterior": movimiento.cantidad_anterior,
                    "stock_nuevo": movimiento.cantidad_nueva,
                    "fecha": movimiento.fecha_movimiento.isoformat()
                }
            }

        except StockManagerError as e:
            logger.error(f"Error en StockManager: {str(e)}")
            raise ServiceError(str(e))

    def get_stock_critico(self) -> StockCriticoResponse:
        """
        Obtiene productos con stock crítico
        """
        productos_criticos = self.stock_manager.get_productos_stock_critico()
        productos_response = [ProductoResponse.model_validate(p) for p in productos_criticos]

        return StockCriticoResponse(
            productos=productos_response,
            total=len(productos_response),
            message=f"Se encontraron {len(productos_response)} productos con stock crítico"
        )

    def get_movimientos_history(
        self, 
        producto_id: Optional[int] = None,
        dias: int = 30,
        limit: int = 100
    ) -> List[dict]:
        """
        Obtiene historial de movimientos
        """
        fecha_desde = datetime.utcnow() - timedelta(days=dias)

        movimientos = self.stock_manager.get_stock_movements_history(
            producto_id=producto_id,
            fecha_desde=fecha_desde,
            limit=limit
        )

        return [
            {
                "id": mov.id,
                "producto_id": mov.producto_id,
                "producto_codigo": mov.producto.codigo,
                "producto_nombre": mov.producto.nombre,
                "tipo_movimiento": mov.tipo_movimiento,
                "cantidad": mov.cantidad,
                "cantidad_anterior": mov.cantidad_anterior,
                "cantidad_nueva": mov.cantidad_nueva,
                "motivo": mov.motivo,
                "referencia": mov.referencia,
                "usuario": mov.usuario,
                "fecha_movimiento": mov.fecha_movimiento.isoformat()
            }
            for mov in movimientos
        ]


class ReporteService:
    """
    Servicio para generación de reportes y estadísticas
    """

    def __init__(self, db: Session):
        self.db = db
        self.stock_manager = StockManagerComplete(db)

    def generate_stock_report(self) -> ReporteStockResponse:
        """
        Genera reporte completo de stock
        """
        # Estadísticas básicas
        total_productos = self.db.query(func.count(Producto.id)).scalar()
        productos_activos = self.db.query(func.count(Producto.id)).filter(Producto.activo == True).scalar()

        # Productos con stock crítico
        productos_criticos = self.db.query(func.count(Producto.id)).filter(
            and_(
                Producto.activo == True,
                Producto.stock_actual <= Producto.stock_minimo
            )
        ).scalar()

        # Productos con sobrestock
        productos_sobrestock = self.db.query(func.count(Producto.id)).filter(
            and_(
                Producto.activo == True,
                Producto.stock_actual >= Producto.stock_maximo
            )
        ).scalar()

        # Valor total del inventario
        valor_total = self.db.query(func.sum(Producto.precio * Producto.stock_actual)).filter(
            Producto.activo == True
        ).scalar() or 0.0

        return ReporteStockResponse(
            total_productos=total_productos,
            productos_activos=productos_activos,
            productos_stock_critico=productos_criticos,
            productos_sobrestock=productos_sobrestock,
            valor_total_inventario=valor_total,
            fecha_reporte=datetime.utcnow()
        )

    def get_top_movimientos(self, dias: int = 30, limit: int = 10) -> List[dict]:
        """
        Obtiene productos con más movimientos en el período
        """
        fecha_desde = datetime.utcnow() - timedelta(days=dias)

        query = text("""
            SELECT p.id, p.codigo, p.nombre, COUNT(m.id) as total_movimientos,
                   SUM(CASE WHEN m.tipo_movimiento = 'ENTRADA' THEN m.cantidad ELSE 0 END) as total_entradas,
                   SUM(CASE WHEN m.tipo_movimiento = 'SALIDA' THEN m.cantidad ELSE 0 END) as total_salidas
            FROM productos p
            LEFT JOIN movimientos_stock m ON p.id = m.producto_id 
                AND m.fecha_movimiento >= :fecha_desde
            WHERE p.activo = true
            GROUP BY p.id, p.codigo, p.nombre
            ORDER BY total_movimientos DESC
            LIMIT :limit
        """)

        result = self.db.execute(query, {"fecha_desde": fecha_desde, "limit": limit})

        return [
            {
                "producto_id": row[0],
                "codigo": row[1],
                "nombre": row[2],
                "total_movimientos": row[3],
                "total_entradas": row[4],
                "total_salidas": row[5]
            }
            for row in result
        ]

    def validate_stock_integrity(self) -> dict:
        """
        Valida la integridad del stock
        """
        return self.stock_manager.validate_stock_integrity()
