"""
API Principal - Sistema Gestión Depósito
FastAPI con endpoints CRUD completos y control ACID
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from shared.security_headers import apply_fastapi_security
import os
from shared.errors import register_fastapi_error_handlers
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from shared.config import validate_env_vars
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func
from typing import List, Optional
import logging
from datetime import datetime
from decimal import Decimal
import uvicorn

# Imports del proyecto
 
from .database import get_database_session, db_manager
from .models import Producto, MovimientoStock, Cliente, Proveedor
from .schemas import (
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoFilter,
    MovimientoStockCreate, MovimientoStockResponse, MovimientoFilter,
    StockUpdateRequest, StockUpdateResponse,
    ClienteCreate, ClienteUpdate, ClienteResponse,
    ProveedorCreate, ProveedorResponse,
    PaginatedResponse, ErrorResponse, SuccessResponse,
    ProductoStockCritico, ResumenStock,
    StockMovementsResponse, StockCriticoResponse, StockSummaryResponse, HealthResponse
)
from .stock_manager import (
    stock_manager, StockManagerError, InsufficientStockError, 
    ProductoNotFoundError
)

import os
from shared.auth import require_role, DEPOSITO_ROLE

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler(os.getenv('LOG_PATH', 'logs/api.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión de Depósito",
    description="API completa para gestión de productos, stock y movimientos con control ACID",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
register_fastapi_error_handlers(app)
validate_env_vars([
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
])

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()],
    allow_credentials=True,
    allow_methods=[m.strip() for m in os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',') if m.strip()],
    allow_headers=[h.strip() for h in os.getenv('CORS_HEADERS', 'Authorization,Content-Type').split(',') if h.strip()]
)

# Security headers
apply_fastapi_security(app)

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

# ===== ENDPOINTS DE PRODUCTOS =====

@app.post("/productos", 
          response_model=ProductoResponse, 
          status_code=status.HTTP_201_CREATED,
          summary="Crear producto",
          description="Crea un nuevo producto en el catálogo")
async def create_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Crea un nuevo producto con validaciones completas
    """
    try:
        # Verificar que el código no exista
        existing_producto = db.query(Producto).filter(
            Producto.codigo == producto.codigo
        ).first()

        if existing_producto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código {producto.codigo}"
            )

        # Crear el producto
        db_producto = Producto(**producto.dict())
        db.add(db_producto)
        db.commit()
        db.refresh(db_producto)

        logger.info(f"Producto creado: {db_producto.codigo} - {db_producto.nombre}")

        return db_producto

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error de integridad creando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad en los datos del producto"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/productos", 
         response_model=PaginatedResponse,
         summary="Listar productos",
         description="Lista productos con filtros y paginación")
async def list_productos(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    marca: Optional[str] = Query(None, description="Filtrar por marca"),
    stock_critico: Optional[bool] = Query(None, description="Solo productos con stock crítico"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    precio_min: Optional[Decimal] = Query(None, description="Precio mínimo"),
    precio_max: Optional[Decimal] = Query(None, description="Precio máximo"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Lista productos con filtros avanzados y paginación
    """
    try:
        # Construir query base
        query = db.query(Producto)

        # Aplicar filtros
        if codigo:
            query = query.filter(Producto.codigo.ilike(f"%{codigo}%"))

        if nombre:
            query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))

        if categoria:
            query = query.filter(Producto.categoria == categoria)

        if marca:
            query = query.filter(Producto.marca.ilike(f"%{marca}%"))

        if stock_critico is not None:
            if stock_critico:
                query = query.filter(Producto.stock_actual <= Producto.stock_minimo)
            else:
                query = query.filter(Producto.stock_actual > Producto.stock_minimo)

        if activo is not None:
            query = query.filter(Producto.activo == activo)

        if precio_min is not None:
            query = query.filter(Producto.precio_venta >= precio_min)

        if precio_max is not None:
            query = query.filter(Producto.precio_venta <= precio_max)

        # Contar total de resultados
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * size
        productos = query.order_by(Producto.fecha_creacion.desc()).offset(offset).limit(size).all()

        # Calcular páginas totales
        pages = (total + size - 1) // size

        # Convertir a diccionarios para respuesta
        items = []
        for producto in productos:
            producto_dict = {
                "id": producto.id,
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "categoria": producto.categoria,
                "marca": producto.marca,
                "modelo": producto.modelo,
                "precio_costo": float(producto.precio_costo),
                "precio_venta": float(producto.precio_venta),
                "precio_mayorista": float(producto.precio_mayorista) if producto.precio_mayorista else None,
                "stock_actual": producto.stock_actual,
                "stock_minimo": producto.stock_minimo,
                "stock_maximo": producto.stock_maximo,
                "ubicacion_deposito": producto.ubicacion_deposito,
                "peso_kg": float(producto.peso_kg) if producto.peso_kg else None,
                "dimensiones": producto.dimensiones,
                "activo": producto.activo,
                "fecha_creacion": producto.fecha_creacion.isoformat(),
                "fecha_modificacion": producto.fecha_modificacion.isoformat() if producto.fecha_modificacion else None,
                "stock_critico": producto.stock_critico,
                "margen_ganancia": producto.margen_ganancia
            }
            items.append(producto_dict)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

    except Exception as e:
        logger.error(f"Error listando productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando productos"
        )

@app.get("/productos/{producto_id}", 
         response_model=ProductoResponse,
         summary="Obtener producto",
         description="Obtiene un producto específico por ID")
async def get_producto(
    producto_id: int,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Obtiene un producto específico por su ID
    """
    try:
        producto = db.query(Producto).filter(Producto.id == producto_id).first()

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado"
            )

        return producto

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando producto"
        )

@app.put("/productos/{producto_id}", 
         response_model=ProductoResponse,
         summary="Actualizar producto",
         description="Actualiza un producto existente")
async def update_producto(
    producto_id: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Actualiza un producto existente con validaciones
    """
    try:
        # Obtener producto existente
        db_producto = db.query(Producto).filter(Producto.id == producto_id).first()

        if not db_producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado"
            )

        # Verificar código único si se está cambiando
        if producto_update.codigo and producto_update.codigo != db_producto.codigo:
            existing_codigo = db.query(Producto).filter(
                and_(
                    Producto.codigo == producto_update.codigo,
                    Producto.id != producto_id
                )
            ).first()

            if existing_codigo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otro producto con código {producto_update.codigo}"
                )

        # Actualizar campos proporcionados
        update_data = producto_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_producto, field, value)

        db_producto.fecha_modificacion = datetime.now()

        db.commit()
        db.refresh(db_producto)

        logger.info(f"Producto actualizado: {db_producto.codigo}")

        return db_producto

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Error de integridad actualizando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad en los datos"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.delete("/productos/{producto_id}", 
            response_model=SuccessResponse,
            summary="Eliminar producto",
            description="Elimina un producto (soft delete)")
async def delete_producto(
    producto_id: int,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Elimina un producto (marcado como inactivo - soft delete)
    """
    try:
        # Obtener producto
        db_producto = db.query(Producto).filter(Producto.id == producto_id).first()

        if not db_producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado"
            )

        # Verificar si tiene movimientos recientes
        movimientos_recientes = db.query(MovimientoStock).filter(
            and_(
                MovimientoStock.producto_id == producto_id,
                MovimientoStock.fecha_movimiento >= datetime.now() - timedelta(days=30)
            )
        ).count()

        if movimientos_recientes > 0:
            # Solo desactivar si tiene movimientos recientes
            db_producto.activo = False
            mensaje = f"Producto {db_producto.codigo} desactivado (tenía movimientos recientes)"
        else:
            # Eliminar físicamente si no tiene movimientos recientes
            db.delete(db_producto)
            mensaje = f"Producto {db_producto.codigo} eliminado permanentemente"

        db_producto.fecha_modificacion = datetime.now()

        db.commit()

        logger.info(mensaje)

        return {
            "success": True,
            "message": mensaje
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# ===== ENDPOINTS DE STOCK =====

@app.post("/stock/update", 
          response_model=StockUpdateResponse, 
          summary="Actualizar stock",
          description="Actualiza el stock de un producto")
async def update_stock(
    stock_update: StockUpdateRequest,
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Actualiza stock de un producto con control ACID completo
    """
    try:
        result = stock_manager.update_stock(db, stock_update)
        db.commit()  # Commit explícito después de operaciones de stock

        return StockUpdateResponse(**result)

    except ProductoNotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientStockError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except StockManagerError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/stock/movements", 
         response_model=StockMovementsResponse, 
         summary="Historial de movimientos",
         description="Obtiene el historial de movimientos de stock")
async def get_stock_movements(
    producto_id: Optional[int] = Query(None, description="ID del producto (opcional)"),
    dias: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
    usuario: Optional[str] = Query(None, description="Usuario que realizó el movimiento"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    documento_referencia: Optional[str] = Query(None, description="Documento de referencia"),
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(100, ge=1, le=500, description="Tamaño de página"),
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Obtiene historial de movimientos con filtros y paginación
    """
    try:
        # Construir query
        query = db.query(MovimientoStock).join(Producto)

        # Aplicar filtros
        if producto_id:
            query = query.filter(MovimientoStock.producto_id == producto_id)

        if usuario:
            query = query.filter(MovimientoStock.usuario.ilike(f"%{usuario}%"))

        if fecha_desde:
            query = query.filter(MovimientoStock.fecha_movimiento >= fecha_desde)

        if fecha_hasta:
            query = query.filter(MovimientoStock.fecha_movimiento <= fecha_hasta)

        if documento_referencia:
            query = query.filter(MovimientoStock.documento_referencia.ilike(f"%{documento_referencia}%"))

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * size
        movimientos = query.order_by(MovimientoStock.fecha_movimiento.desc()).offset(offset).limit(size).all()

        # Preparar respuesta
        pages = (total + size - 1) // size

        items = []
        for mov in movimientos:
            item = {
                "id": mov.id,
                "producto_id": mov.producto_id,
                "producto_codigo": mov.producto.codigo,
                "producto_nombre": mov.producto.nombre,
                "tipo_movimiento": mov.tipo_movimiento,
                "subtipo": mov.subtipo,
                "cantidad": mov.cantidad,
                "stock_anterior": mov.stock_anterior,
                "stock_posterior": mov.stock_posterior,
                "precio_unitario": float(mov.precio_unitario) if mov.precio_unitario else None,
                "valor_total": float(mov.valor_total) if mov.valor_total else None,
                "documento_referencia": mov.documento_referencia,
                "fecha_movimiento": mov.fecha_movimiento.isoformat(),
                "usuario": mov.usuario,
                "observaciones": mov.observaciones,
                "estado": mov.estado
            }
            items.append(item)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

    except Exception as e:
        logger.error(f"Error obteniendo movimientos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando movimientos"
        )

@app.get("/stock/critical", 
         response_model=StockCriticoResponse, 
         summary="Stock crítico",
         description="Obtiene productos con stock crítico")
async def get_stock_critical(
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Obtiene productos con stock crítico
    """
    try:
        productos_criticos = stock_manager.get_critical_stock_products()

        result = []
        for producto in productos_criticos:
            item = ProductoStockCritico(
                id=producto.id,
                codigo=producto.codigo,
                nombre=producto.nombre,
                categoria=producto.categoria,
                stock_actual=producto.stock_actual,
                stock_minimo=producto.stock_minimo,
                diferencia=producto.stock_minimo - producto.stock_actual,
                ubicacion_deposito=producto.ubicacion_deposito
            )
            result.append(item)

        return result

    except Exception as e:
        logger.error(f"Error obteniendo stock crítico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando stock crítico"
        )

@app.get("/stock/summary", 
         response_model=StockSummaryResponse, 
         summary="Resumen de stock",
         description="Obtiene resumen de stock")
async def get_stock_summary(
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Obtiene resumen general del estado del stock
    """
    try:
        summary = stock_manager.get_stock_summary()

        return ResumenStock(
            total_productos=summary['total_productos'],
            productos_activos=summary['total_productos'],  # Asumiendo que solo consultamos activos
            productos_stock_critico=summary['productos_stock_critico'],
            valor_total_inventario=Decimal(str(summary['valor_total_inventario'])),
            productos_sin_stock=summary['productos_sin_stock'],
            categorias_con_stock_critico=summary['categorias_con_stock_critico']
        )

    except Exception as e:
        logger.error(f"Error obteniendo resumen de stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando resumen de stock"
        )

# ===== ENDPOINTS DE HEALTH CHECK =====

@app.get("/health", 
         response_model=HealthResponse, 
         summary="Health check",
         description="Verifica el estado del sistema")
async def health_check(
    db: Session = Depends(get_database_session),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Endpoint de health check para monitoreo
    """
    try:
        # Verificar conexión a BD
        db_status = db_manager.test_connection()

        # Obtener estadísticas básicas
        stats = db_manager.get_table_stats()

        return {
            "status": "healthy" if db_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": db_status,
                "stats": stats
            },
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# ===== EJECUTAR APLICACIÓN =====

def main():
    """Función principal para ejecutar la API"""
    try:
        # Verificar conexión a BD al inicio
        if not db_manager.test_connection():
            logger.error("No se pudo conectar a la base de datos")
            return 1

        logger.info("Iniciando API del Sistema de Gestión de Depósito")
        logger.info("Documentación disponible en: http://localhost:8000/docs")

        # Ejecutar servidor
        uvicorn.run(
            "agente_deposito.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Cambiar a True para desarrollo
            log_level="info"
        )

        return 0

    except Exception as e:
        logger.error(f"Error iniciando API: {e}")
        return 1

# Para usar con timedelta en delete_producto
from datetime import timedelta

if __name__ == "__main__":
    exit(main())
