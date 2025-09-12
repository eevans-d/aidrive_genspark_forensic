"""
AgenteDepósito - FastAPI Application with Intelligent Cache
Versión: 2.1 - Cache Optimized

Aplicación completa con cache inteligente:
- Cache layer para endpoints críticos  
- TTL dinámico basado en frecuencia
- Invalidación automática en updates
- Estadísticas de performance
- Fallback automático si Redis falla
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
from .schemas_updated import (
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoList,
    StockMovement, StockMovementResponse, StockQuery, StockSummary,
    PaginationParams, FilterParams, HealthResponse, SystemHealth
)

# Importar cache system
from cache import (
    cache_product, cache_stock, cache_frequent_query, cache_report,
    invalidate_product_cache, invalidate_cache_by_type, get_cache_status,
    CacheBatchInvalidation, track_cache_stats
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifecycle manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    logger.info("🚀 AgenteDepósito iniciando...")

    # Startup
    try:
        # Test cache connection
        cache_stats = get_cache_status()
        logger.info(f"✅ Cache disponible: {cache_stats.get('redis_info', {}).get('redis_version', 'N/A')}")
    except Exception as e:
        logger.warning(f"⚠️ Cache no disponible: {e}")

    yield

    # Shutdown
    logger.info("🛑 AgenteDepósito cerrando...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema Inventario - AgenteDepósito",
    description="API REST para gestión de productos y stock con cache inteligente",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para requests lentas
app.middleware("http")(log_slow_requests)

# === ENDPOINTS DE PRODUCTOS (CACHEADOS) ===

@app.get("/productos", response_model=ProductoList, tags=["productos"])
@cache_frequent_query(ttl=300)  # Cache 5 min, TTL dinámico
@track_cache_stats
async def listar_productos(
    skip: int = Query(0, ge=0, description="Elementos a omitir"),
    limit: int = Query(10, ge=1, le=100, description="Máximo elementos"),
    search: Optional[str] = Query(None, description="Buscar por nombre/código"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    orden: Optional[str] = Query("nombre", description="Campo de ordenamiento"),
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Lista productos con paginación, filtros y cache inteligente"""
    try:
        logger.info(f"📋 Listando productos: skip={skip}, limit={limit}, search={search}")

        producto_service = ProductoService(db)

        # Construir filtros
        filtros = FilterParams(
            search=search,
            categoria=categoria, 
            activo=activo,
            orden=orden
        )

        # Obtener productos (función será cacheada automáticamente)
        productos, total = producto_service.listar_productos(
            skip=skip, 
            limit=limit, 
            filtros=filtros
        )

        return response_builder.success_response(
            data={
                "productos": productos,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            },
            message=f"Productos listados: {len(productos)} de {total}"
        )

    except Exception as e:
        logger.error(f"❌ Error listando productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.get("/productos/{producto_id}", response_model=ProductoResponse, tags=["productos"])
@cache_product(ttl=3600)  # Cache 1h con TTL dinámico
@track_cache_stats
async def obtener_producto(
    producto_id: int = Path(..., description="ID del producto"),
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Obtiene producto por ID con cache inteligente"""
    try:
        logger.info(f"🔍 Obteniendo producto ID: {producto_id}")

        producto_service = ProductoService(db)
        producto = producto_service.obtener_producto(producto_id)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {producto_id} no encontrado"
            )

        return response_builder.success_response(
            data=producto,
            message=f"Producto {producto_id} obtenido exitosamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.post("/productos", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED, tags=["productos"])
@track_cache_stats
async def crear_producto(
    producto_data: ProductoCreate,
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Crea nuevo producto e invalida cache relacionado"""
    try:
        logger.info(f"➕ Creando producto: {producto_data.nombre}")

        producto_service = ProductoService(db)

        # Verificar si código ya existe
        if producto_service.obtener_producto_por_codigo(producto_data.codigo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto con código {producto_data.codigo} ya existe"
            )

        # Crear producto
        nuevo_producto = producto_service.crear_producto(producto_data)

        # Invalidar cache de listings
        invalidate_cache_by_type('query', '*productos*')
        logger.info(f"🗑️ Cache listings invalidado por creación producto {nuevo_producto.id}")

        return response_builder.success_response(
            data=nuevo_producto,
            message=f"Producto {nuevo_producto.nombre} creado exitosamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.put("/productos/{producto_id}", response_model=ProductoResponse, tags=["productos"])
@track_cache_stats
async def actualizar_producto(
    producto_id: int = Path(..., description="ID del producto"),
    producto_data: ProductoUpdate = ...,
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Actualiza producto e invalida cache automáticamente"""
    try:
        logger.info(f"✏️ Actualizando producto ID: {producto_id}")

        producto_service = ProductoService(db)

        # Verificar que existe
        producto_existente = producto_service.obtener_producto(producto_id)
        if not producto_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {producto_id} no encontrado"
            )

        # Usar batch invalidation para operación atómica
        with CacheBatchInvalidation() as batch:
            # Actualizar producto
            producto_actualizado = producto_service.actualizar_producto(
                producto_id, producto_data
            )

            # Invalidar cache del producto y relacionados
            batch.add_product(str(producto_id))
            batch.add_pattern('query:*productos*')  # Listings

        return response_builder.success_response(
            data=producto_actualizado,
            message=f"Producto {producto_id} actualizado exitosamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["productos"])
@track_cache_stats
async def eliminar_producto(
    producto_id: int = Path(..., description="ID del producto"),
    db: Session = Depends(get_database)
):
    """Elimina producto e invalida todo su cache"""
    try:
        logger.info(f"🗑️ Eliminando producto ID: {producto_id}")

        producto_service = ProductoService(db)

        # Verificar que existe
        if not producto_service.obtener_producto(producto_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {producto_id} no encontrado"
            )

        # Eliminar con invalidación batch
        with CacheBatchInvalidation() as batch:
            # Eliminar producto
            producto_service.eliminar_producto(producto_id)

            # Invalidar todo el cache relacionado
            batch.add_product(str(producto_id))
            batch.add_pattern('query:*productos*')
            batch.add_pattern('stock:*')  # Stock podría verse afectado

        logger.info(f"✅ Producto {producto_id} eliminado y cache invalidado")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ENDPOINTS DE STOCK (CACHEADOS) ===

@app.get("/productos/{producto_id}/stock", response_model=StockSummary, tags=["stock"])
@cache_stock(ttl=300)  # Cache 5 min (stock cambia frecuentemente)
@track_cache_stats
async def obtener_stock_producto(
    producto_id: int = Path(..., description="ID del producto"),
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Obtiene stock actual de producto con cache"""
    try:
        logger.info(f"📦 Obteniendo stock producto ID: {producto_id}")

        stock_service = StockService(db)
        stock_info = stock_service.obtener_stock_producto(producto_id)

        if stock_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock para producto {producto_id} no encontrado"
            )

        return response_builder.success_response(
            data=stock_info,
            message=f"Stock producto {producto_id} obtenido"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo stock producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.post("/productos/{producto_id}/stock/movimiento", 
          response_model=StockMovementResponse, 
          status_code=status.HTTP_201_CREATED,
          tags=["stock"])
@track_cache_stats
async def registrar_movimiento_stock(
    producto_id: int = Path(..., description="ID del producto"),
    movimiento: StockMovement = ...,
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Registra movimiento de stock e invalida cache automáticamente"""
    try:
        logger.info(f"📝 Registrando movimiento stock producto {producto_id}: {movimiento.tipo}")

        stock_service = StockService(db)

        # Usar batch invalidation para operación ACID
        with CacheBatchInvalidation() as batch:
            # Registrar movimiento (transacción ACID)
            resultado = stock_service.registrar_movimiento(
                producto_id=producto_id,
                tipo=movimiento.tipo,
                cantidad=movimiento.cantidad,
                motivo=movimiento.motivo,
                referencia=movimiento.referencia
            )

            # Invalidar cache relacionado al stock
            batch.add_pattern(f'stock:{producto_id}*')
            batch.add_pattern('stock:*summary*')  # Resúmenes de stock
            batch.add_pattern('query:*stock*')    # Queries de stock

        return response_builder.success_response(
            data=resultado,
            message=f"Movimiento stock registrado para producto {producto_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registrando movimiento stock {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.get("/stock/resumen", response_model=List[StockSummary], tags=["stock"])
@cache_frequent_query(ttl=600)  # Cache 10 min con TTL dinámico
@track_cache_stats
async def obtener_resumen_stock(
    limite_critico: Optional[int] = Query(10, description="Límite stock crítico"),
    solo_criticos: bool = Query(False, description="Solo productos con stock crítico"),
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Obtiene resumen de stock con cache inteligente"""
    try:
        logger.info(f"📊 Obteniendo resumen stock: crítico={limite_critico}, solo_críticos={solo_criticos}")

        stock_service = StockService(db)
        resumen = stock_service.obtener_resumen_stock(
            limite_critico=limite_critico,
            solo_criticos=solo_criticos
        )

        return response_builder.success_response(
            data=resumen,
            message=f"Resumen stock obtenido: {len(resumen)} productos"
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ENDPOINTS DE REPORTES (CACHEADOS) ===

@app.get("/reportes/productos", tags=["reportes"])
@cache_report(ttl=7200)  # Cache 2h (reportes costosos)
@track_cache_stats
async def generar_reporte_productos(
    formato: str = Query("json", regex="^(json|csv|excel)$", description="Formato del reporte"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    db: Session = Depends(get_database),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Genera reporte de productos con cache de larga duración"""
    try:
        logger.info(f"📈 Generando reporte productos: formato={formato}")

        reporte_service = ReporteService(db)
        reporte = reporte_service.generar_reporte_productos(
            formato=formato,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            categoria=categoria
        )

        return response_builder.success_response(
            data=reporte,
            message="Reporte productos generado exitosamente"
        )

    except Exception as e:
        logger.error(f"❌ Error generando reporte productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ENDPOINTS DE SISTEMA Y CACHE ===

@app.get("/health", response_model=HealthResponse, tags=["sistema"])
async def health_check(
    db: Session = Depends(get_database)
):
    """Health check incluyendo estado del cache"""
    try:
        # Check database
        db_health = check_database_health(db)

        # Check cache
        try:
            cache_stats = get_cache_status()
            cache_health = {
                "status": "healthy",
                "hit_rate": cache_stats.get('cache_stats', {}).get('hit_rate', 0),
                "total_requests": cache_stats.get('cache_stats', {}).get('total_requests', 0),
                "redis_version": cache_stats.get('redis_info', {}).get('redis_version', 'N/A')
            }
        except Exception as e:
            cache_health = {"status": "unhealthy", "error": str(e)}

        # System health
        system_health = get_system_health()

        return HealthResponse(
            status="healthy",
            timestamp=system_health.timestamp,
            database=db_health,
            cache=cache_health,
            system=system_health.dict()
        )

    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sistema no disponible: {str(e)}"
        )

@app.get("/cache/stats", tags=["sistema"])
@track_cache_stats
async def obtener_estadisticas_cache(
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Obtiene estadísticas detalladas del cache"""
    try:
        cache_stats = get_cache_status()

        return response_builder.success_response(
            data=cache_stats,
            message="Estadísticas cache obtenidas exitosamente"
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo stats cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.post("/cache/invalidate/{cache_type}", tags=["sistema"])
@track_cache_stats
async def invalidar_cache_manual(
    cache_type: str = Path(..., description="Tipo de cache a invalidar"),
    pattern: str = Query("*", description="Patrón para invalidar"),
    response_builder: ResponseBuilder = Depends(get_response_builder)
):
    """Invalida cache manualmente (útil para debugging)"""
    try:
        logger.info(f"🗑️ Invalidación manual cache: {cache_type}:{pattern}")

        deleted_count = invalidate_cache_by_type(cache_type, pattern)

        return response_builder.success_response(
            data={"deleted_keys": deleted_count},
            message=f"Cache invalidado: {deleted_count} keys eliminadas"
        )

    except Exception as e:
        logger.error(f"❌ Error invalidando cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ERROR HANDLERS ===

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones"""
    logger.error(f"❌ Excepción no manejada en {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "detail": str(exc) if app.debug else "Error interno",
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_cached:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
