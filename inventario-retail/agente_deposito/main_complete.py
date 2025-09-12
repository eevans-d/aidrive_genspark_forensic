"""
AgenteDepósito - FastAPI Application Complete
Versión: 2.0 - Production Ready

Aplicación completa con:
- CRUD completo de productos
- Operaciones de stock ACID
- Paginación y filtros avanzados
- Error handling robusto
- Logging completo
- Health checks
- Documentación API automática
"""

import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, Path, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Importaciones locales
from .dependencies import (
    get_database, get_error_handler, get_current_user, get_request_logger,
    validate_pagination_params, get_response_builder, check_database_health,
    get_system_health, log_slow_requests, ErrorHandler, ResponseBuilder
)
from .services import ProductoService, StockService, ReporteService
from .schemas import (
    # Producto schemas
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoFilters,
    # Stock schemas  
    StockUpdateRequest, StockAdjustmentRequest, StockMovementRequest,
    TipoMovimiento,
    # Paginación
    PaginacionParams, PaginatedResponse,
    # Respuestas
    MessageResponse, StockCriticoResponse, ReporteStockResponse
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan para inicialización y cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    logger.info("🚀 Iniciando AgenteDepósito v2.0")

    # Inicialización
    try:
        # Aquí se pueden agregar inicializaciones adicionales
        logger.info("✅ Inicialización completada")
        yield
    finally:
        # Cleanup
        logger.info("🛑 Cerrando AgenteDepósito")

# Crear aplicación FastAPI
app = FastAPI(
    title="AgenteDepósito API",
    description="""
    ## Sistema de Gestión de Depósito - Versión 2.0 Production Ready

    API completa para gestión de inventario con:

    ### 🏢 Gestión de Productos
    - CRUD completo con validaciones business
    - Búsqueda avanzada y filtros
    - Paginación optimizada

    ### 📦 Gestión de Stock
    - Operaciones ACID con transacciones
    - Movimientos de entrada, salida y ajustes
    - Tracking completo de movimientos
    - Detección de stock crítico

    ### 📊 Reportes y Estadísticas
    - Reportes de stock en tiempo real
    - Análisis de movimientos
    - Validación de integridad

    ### 🔧 Características Técnicas
    - Error handling robusto
    - Logging completo
    - Health checks
    - Documentación automática
    """,
    version="2.0.0",
    contact={
        "name": "AgenteDepósito Support",
        "email": "support@agentedeposito.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar origins exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para requests lentos
app.middleware("http")(log_slow_requests)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global de excepciones
    """
    error_handler = ErrorHandler()
    http_exc = error_handler.handle_service_error(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )


# === HEALTH CHECK ENDPOINTS ===

@app.get("/health", 
         summary="Health Check",
         description="Verifica el estado de salud del sistema",
         tags=["Health"])
async def health_check(
    db_health: dict = Depends(check_database_health)
):
    """
    Endpoint de health check básico
    """
    system_health = get_system_health()

    overall_status = "healthy" if db_health.get("database") == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": system_health["timestamp"],
        "components": {
            "database": db_health,
            "system": {
                "cpu_percent": system_health["cpu_percent"],
                "memory_percent": system_health["memory_percent"],
                "disk_percent": system_health["disk_percent"]
            }
        }
    }


@app.get("/health/detailed",
         summary="Detailed Health Check", 
         description="Health check detallado del sistema",
         tags=["Health"])
async def detailed_health_check(
    db_health: dict = Depends(check_database_health)
):
    """
    Health check detallado con métricas del sistema
    """
    system_health = get_system_health()

    return {
        "status": "healthy" if db_health.get("database") == "healthy" else "unhealthy",
        "version": "2.0.0",
        "database": db_health,
        "system": system_health,
        "endpoints": {
            "productos": "/api/v1/productos",
            "stock": "/api/v1/stock", 
            "reportes": "/api/v1/reportes"
        }
    }


# === PRODUCTOS ENDPOINTS ===

@app.post("/api/v1/productos",
          response_model=ProductoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Crear Producto",
          description="Crea un nuevo producto en el sistema",
          tags=["Productos"])
async def create_producto(
    producto_data: ProductoCreate,
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """
    Crea un nuevo producto con validaciones business completas.

    - **codigo**: Código único del producto (requerido)
    - **nombre**: Nombre descriptivo del producto
    - **precio**: Precio unitario del producto
    - **stock_inicial**: Stock inicial (opcional, default 0)
    - **stock_minimo**: Stock mínimo para alertas
    - **stock_maximo**: Stock máximo permitido
    """
    try:
        service = ProductoService(db)
        producto = service.create_producto(producto_data)

        logger.info(f"Producto creado por {current_user}: {producto.codigo}")
        return producto

    except Exception as e:
        logger.error(f"Error creando producto: {str(e)}")
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/productos/{producto_id}",
         response_model=ProductoResponse,
         summary="Obtener Producto",
         description="Obtiene un producto específico por ID",
         tags=["Productos"])
async def get_producto(
    producto_id: int = Path(..., description="ID del producto", ge=1),
    db: Session = Depends(get_database)
):
    """
    Obtiene un producto específico por su ID.
    """
    try:
        service = ProductoService(db)
        producto = service.get_producto(producto_id)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {producto_id} no encontrado"
            )

        return producto

    except HTTPException:
        raise
    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/productos/codigo/{codigo}",
         response_model=ProductoResponse,
         summary="Obtener Producto por Código",
         description="Obtiene un producto específico por código",
         tags=["Productos"])
async def get_producto_by_codigo(
    codigo: str = Path(..., description="Código del producto"),
    db: Session = Depends(get_database)
):
    """
    Obtiene un producto específico por su código único.
    """
    try:
        service = ProductoService(db)
        producto = service.get_producto_by_codigo(codigo)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con código '{codigo}' no encontrado"
            )

        return producto

    except HTTPException:
        raise
    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.put("/api/v1/productos/{producto_id}",
         response_model=ProductoResponse,
         summary="Actualizar Producto",
         description="Actualiza un producto existente",
         tags=["Productos"])
async def update_producto(
    producto_id: int = Path(..., description="ID del producto", ge=1),
    update_data: ProductoUpdate = ...,
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user)
):
    """
    Actualiza un producto existente.
    Solo se actualizan los campos proporcionados (partial update).
    """
    try:
        service = ProductoService(db)
        producto = service.update_producto(producto_id, update_data)

        logger.info(f"Producto {producto_id} actualizado por {current_user}")
        return producto

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.delete("/api/v1/productos/{producto_id}",
            response_model=MessageResponse,
            summary="Eliminar Producto",
            description="Elimina un producto (soft delete)",
            tags=["Productos"])
async def delete_producto(
    producto_id: int = Path(..., description="ID del producto", ge=1),
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user)
):
    """
    Elimina un producto del sistema (soft delete).
    Solo se pueden eliminar productos sin stock.
    """
    try:
        service = ProductoService(db)
        success = service.delete_producto(producto_id)

        if success:
            logger.info(f"Producto {producto_id} eliminado por {current_user}")
            return MessageResponse(
                message=f"Producto {producto_id} eliminado exitosamente",
                success=True
            )

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/productos",
         response_model=PaginatedResponse,
         summary="Listar Productos",
         description="Lista productos con paginación y filtros avanzados",
         tags=["Productos"])
async def list_productos(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (parcial)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    stock_critico: Optional[bool] = Query(None, description="Solo productos con stock crítico"),
    sobrestock: Optional[bool] = Query(None, description="Solo productos con sobrestock"),
    db: Session = Depends(get_database)
):
    """
    Lista productos con paginación y filtros avanzados.

    **Filtros disponibles:**
    - **codigo**: Búsqueda parcial por código
    - **nombre**: Búsqueda parcial por nombre  
    - **categoria**: Filtro exacto por categoría
    - **activo**: Solo productos activos/inactivos
    - **stock_critico**: Solo productos con stock <= stock_mínimo
    - **sobrestock**: Solo productos con stock >= stock_máximo
    """
    try:
        service = ProductoService(db)

        # Crear filtros
        filters = ProductoFilters(
            codigo=codigo,
            nombre=nombre,
            categoria=categoria,
            activo=activo,
            stock_critico=stock_critico,
            sobrestock=sobrestock
        )

        # Crear paginación
        pagination = PaginacionParams(page=page, size=size)

        # Obtener productos
        result = service.get_productos_paginated(pagination, filters)

        return result

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/productos/search",
         response_model=List[ProductoResponse],
         summary="Buscar Productos",
         description="Búsqueda full-text de productos",
         tags=["Productos"])
async def search_productos(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=50, description="Límite de resultados"),
    db: Session = Depends(get_database)
):
    """
    Búsqueda full-text en productos.
    Busca en código, nombre, descripción y categoría.
    """
    try:
        service = ProductoService(db)
        productos = service.search_productos(q, limit)

        return productos

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


# === STOCK ENDPOINTS ===

@app.put("/api/v1/stock/update",
         summary="Actualizar Stock",
         description="Actualiza stock a una cantidad específica",
         tags=["Stock"])
async def update_stock(
    request: StockUpdateRequest,
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user)
):
    """
    Actualiza el stock de un producto a una cantidad específica.

    - **producto_id**: ID del producto a actualizar
    - **nueva_cantidad**: Nueva cantidad de stock
    - **motivo**: Motivo del cambio (opcional)
    - **usuario**: Usuario que realiza el cambio
    """
    try:
        # Asignar usuario actual si no se proporciona
        if not request.usuario:
            request.usuario = current_user

        service = StockService(db)
        result = service.update_stock(request)

        logger.info(f"Stock actualizado por {current_user}: {result['message']}")
        return result

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.put("/api/v1/stock/adjust",
         summary="Ajustar Stock",
         description="Ajusta stock por una cantidad específica (+ o -)",
         tags=["Stock"])
async def adjust_stock(
    request: StockAdjustmentRequest,
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user)
):
    """
    Ajusta el stock de un producto por una cantidad específica.

    - **producto_id**: ID del producto a ajustar
    - **cantidad_ajuste**: Cantidad a ajustar (positiva para aumentar, negativa para disminuir)
    - **motivo**: Motivo del ajuste (requerido)
    - **usuario**: Usuario que realiza el ajuste
    """
    try:
        if not request.usuario:
            request.usuario = current_user

        service = StockService(db)
        result = service.adjust_stock(request)

        logger.info(f"Stock ajustado por {current_user}: {result['message']}")
        return result

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.post("/api/v1/stock/movement",
          summary="Procesar Movimiento",
          description="Procesa movimiento de stock (entrada/salida)",
          tags=["Stock"])
async def process_stock_movement(
    request: StockMovementRequest,
    db: Session = Depends(get_database),
    current_user: str = Depends(get_current_user)
):
    """
    Procesa un movimiento de stock (entrada o salida).

    - **producto_id**: ID del producto
    - **tipo_movimiento**: ENTRADA o SALIDA
    - **cantidad**: Cantidad del movimiento (siempre positiva)
    - **motivo**: Motivo del movimiento (opcional)
    - **referencia**: Referencia externa como número de factura (opcional)
    - **usuario**: Usuario que realiza el movimiento
    """
    try:
        if not request.usuario:
            request.usuario = current_user

        service = StockService(db)
        result = service.process_movement(request)

        logger.info(f"Movimiento procesado por {current_user}: {result['message']}")
        return result

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/stock/critical",
         response_model=StockCriticoResponse,
         summary="Stock Crítico",
         description="Obtiene productos con stock crítico",
         tags=["Stock"])
async def get_stock_critico(
    db: Session = Depends(get_database)
):
    """
    Obtiene todos los productos con stock crítico.
    Un producto tiene stock crítico cuando stock_actual <= stock_minimo.
    """
    try:
        service = StockService(db)
        result = service.get_stock_critico()

        return result

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/stock/movements",
         summary="Historial de Movimientos",
         description="Obtiene historial de movimientos de stock",
         tags=["Stock"])
async def get_stock_movements(
    producto_id: Optional[int] = Query(None, description="ID del producto (opcional)"),
    dias: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
    db: Session = Depends(get_database)
):
    """
    Obtiene el historial de movimientos de stock.

    - **producto_id**: Filtrar por producto específico (opcional)
    - **dias**: Número de días hacia atrás (default 30)
    - **limit**: Máximo número de resultados (default 100)
    """
    try:
        service = StockService(db)
        movimientos = service.get_movimientos_history(
            producto_id=producto_id,
            dias=dias,
            limit=limit
        )

        return {
            "movimientos": movimientos,
            "total": len(movimientos),
            "filtros": {
                "producto_id": producto_id,
                "dias": dias,
                "limit": limit
            }
        }

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


# === REPORTES ENDPOINTS ===

@app.get("/api/v1/reportes/stock",
         response_model=ReporteStockResponse,
         summary="Reporte de Stock",
         description="Genera reporte completo de stock",
         tags=["Reportes"])
async def generate_stock_report(
    db: Session = Depends(get_database)
):
    """
    Genera un reporte completo del estado del stock.

    Incluye:
    - Total de productos
    - Productos activos
    - Productos con stock crítico
    - Productos con sobrestock
    - Valor total del inventario
    """
    try:
        service = ReporteService(db)
        reporte = service.generate_stock_report()

        return reporte

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/reportes/top-movimientos",
         summary="Top Movimientos",
         description="Productos con más movimientos en el período",
         tags=["Reportes"])
async def get_top_movimientos(
    dias: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    db: Session = Depends(get_database)
):
    """
    Obtiene los productos con más movimientos en el período especificado.
    """
    try:
        service = ReporteService(db)
        top_movimientos = service.get_top_movimientos(dias=dias, limit=limit)

        return {
            "top_movimientos": top_movimientos,
            "periodo_dias": dias,
            "limit": limit
        }

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


@app.get("/api/v1/reportes/integrity-check",
         summary="Validación de Integridad",
         description="Valida la integridad del stock",
         tags=["Reportes"])
async def validate_stock_integrity(
    db: Session = Depends(get_database)
):
    """
    Valida la integridad del stock comparando con el historial de movimientos.
    Detecta inconsistencias entre el stock actual y los movimientos registrados.
    """
    try:
        service = ReporteService(db)
        integrity_report = service.validate_stock_integrity()

        return integrity_report

    except Exception as e:
        error_handler = ErrorHandler()
        raise error_handler.handle_service_error(e)


# === ROOT ENDPOINT ===

@app.get("/",
         summary="API Info",
         description="Información básica de la API",
         tags=["Info"])
async def root():
    """
    Endpoint raíz con información básica de la API.
    """
    return {
        "message": "AgenteDepósito API v2.0 - Production Ready",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "productos": "/api/v1/productos",
            "stock": "/api/v1/stock",
            "reportes": "/api/v1/reportes"
        },
        "features": [
            "CRUD completo de productos",
            "Operaciones de stock ACID",
            "Paginación y filtros avanzados",
            "Reportes en tiempo real",
            "Validación de integridad",
            "Health checks",
            "Error handling robusto"
        ]
    }


# === STARTUP EVENT ===

@app.on_event("startup")
async def startup_event():
    """
    Evento de startup para inicializaciones adicionales
    """
    logger.info("🔧 Ejecutando tareas de startup...")

    # Aquí se pueden agregar tareas de inicialización:
    # - Crear datos de ejemplo
    # - Verificar conexiones externas
    # - Cargar configuraciones

    logger.info("✅ Startup completado")


@app.on_event("shutdown") 
async def shutdown_event():
    """
    Evento de shutdown para cleanup
    """
    logger.info("🧹 Ejecutando cleanup...")
    logger.info("👋 AgenteDepósito v2.0 cerrado exitosamente")


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Iniciando servidor de desarrollo...")
    uvicorn.run(
        "main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
