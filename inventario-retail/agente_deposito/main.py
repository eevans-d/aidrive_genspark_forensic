"""
AgenteDepósito - FastAPI App para gestión ACID de stock
Puerto 8002 con endpoints CRUD, validaciones y auditoría
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import time
from datetime import datetime

# Imports del sistema
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import get_db, health_check_db
from shared.auth import require_role, DEPOSITO_ROLE
from shared.models import Producto, MovimientoStock
from shared.config import get_settings, setup_logging
from shared.errors import register_fastapi_error_handlers
from shared.config import validate_env_vars
from shared.utils import formateador, obtener_factor_estacional

from .stock_manager import StockManager, StockUpdateRequest
from .schemas import (
    ProductoCreate, ProductoResponse, ProductoUpdate,
    StockCriticoResponse, StockUpdateResponse,
    HealthResponse, ProductoListResponse
)
from .exceptions import StockInsuficienteError, ProductoNoEncontradoError

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuración
settings = get_settings()

# Crear app FastAPI
app = FastAPI(
    title="AgenteDepósito - Gestión Stock ACID",
    description="Sistema de gestión de inventario con transacciones ACID y auditoría completa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
register_fastapi_error_handlers(app)
validate_env_vars([
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
])

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]  # En producción ser más restrictivo
)

# Manager de stock
stock_manager = StockManager()

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Request processed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4)
        }
    )

    return response

# Exception handlers
@app.exception_handler(StockInsuficienteError)
async def stock_insuficiente_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "stock_insuficiente",
            "message": str(exc),
            "stock_actual": exc.stock_actual if hasattr(exc, 'stock_actual') else None
        }
    )

@app.exception_handler(ProductoNoEncontradoError)
async def producto_no_encontrado_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "producto_no_encontrado",
            "message": str(exc)
        }
    )

# ==========================================
# ENDPOINTS DE HEALTH CHECK
# ==========================================

@app.get("/health", response_model=HealthResponse)
async def health_check(current_user: dict = Depends(require_role(DEPOSITO_ROLE))):
    """Health check del AgenteDepósito"""
    try:
        # Verificar BD
        db_health = health_check_db()

        # Calcular uptime
        uptime_seconds = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0

        return HealthResponse(
            status="healthy",
            service="agente_deposito",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=round(uptime_seconds, 2),
            database=db_health,
            endpoints_disponibles=[
                "GET /health",
                "POST /productos", 
                "GET /productos",
                "GET /productos/{id}",
                "PUT /productos/{id}",
                "POST /stock/update",
                "GET /stock/critical"
            ]
        )
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# ==========================================
# ENDPOINTS CRUD PRODUCTOS
# ==========================================

@app.post("/productos", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_role(DEPOSITO_ROLE))):
    """
    Crea un nuevo producto con validaciones
    """
    try:
        logger.info(f"Creando producto: {producto.codigo}")

        # Verificar que código no existe
        existing = db.query(Producto).filter(Producto.codigo == producto.codigo).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con código {producto.codigo}"
            )

        # Crear producto
        db_producto = Producto(**producto.dict())
        db.add(db_producto)
        db.commit()
        db.refresh(db_producto)

        logger.info(f"Producto creado: {db_producto.id} - {db_producto.codigo}")

        return ProductoResponse.from_orm(db_producto)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creando producto: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/productos", response_model=ProductoListResponse)
async def listar_productos(
    categoria: Optional[str] = None,
    activos_solo: bool = True,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Lista productos con paginación y filtros
    """
    try:
        query = db.query(Producto).filter(Producto.activo == activos_solo)

        if categoria:
            query = query.filter(Producto.categoria.ilike(f"%{categoria}%"))

        total = query.count()
        productos = query.offset(offset).limit(limit).all()

        return ProductoListResponse(
            productos=[ProductoResponse.from_orm(p) for p in productos],
            total=total,
            skip=offset,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Error listando productos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/productos/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(producto_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role(DEPOSITO_ROLE))):
    """
    Obtiene un producto específico por ID
    """
    try:
        producto = db.query(Producto).filter(Producto.id == producto_id).first()

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {producto_id} no encontrado"
            )

        return ProductoResponse.from_orm(producto)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.put("/productos/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
    producto_id: int,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un producto existente
    """
    try:
        db_producto = db.query(Producto).filter(Producto.id == producto_id).first()

        if not db_producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {producto_id} no encontrado"
            )

        # Actualizar campos
        update_data = producto_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_producto, field, value)

        db.commit()
        db.refresh(db_producto)

        logger.info(f"Producto actualizado: {producto_id}")

        return ProductoResponse.from_orm(db_producto)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando producto {producto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# ==========================================
# ENDPOINTS GESTIÓN DE STOCK
# ==========================================

@app.post("/stock/update", response_model=StockUpdateResponse)
async def actualizar_stock(
    stock_request: StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Actualizar stock con transacciones ACID e idempotencia
    """
    try:
        logger.info(
            f"Actualizando stock producto {stock_request.producto_id}: "
            f"{stock_request.tipo_movimiento} {stock_request.cantidad}"
        )

        # Usar stock manager para operación ACID
        resultado = stock_manager.update_stock(db, stock_request)

        logger.info(f"Stock actualizado exitosamente: {resultado.movimiento_id}")

        return resultado

    except (StockInsuficienteError, ProductoNoEncontradoError):
        raise  # Re-raise para exception handlers
    except Exception as e:
        logger.error(f"Error actualizando stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.get("/stock/critical", response_model=List[StockCriticoResponse])
async def obtener_stock_critico(
    limite_critico: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(DEPOSITO_ROLE))
):
    """
    Obtiene productos con stock crítico ajustado por temporada
    """
    try:
        # Obtener factor estacional actual
        factor_temporada = obtener_factor_estacional(settings.TEMPORADA)

        logger.info(f"Consultando stock crítico - Factor temporada: {factor_temporada}")

        # Query productos con stock crítico
        productos = db.query(Producto).filter(Producto.activo == True).all()

        productos_criticos = []
        for producto in productos:
            stock_minimo_ajustado = producto.stock_minimo * factor_temporada

            if producto.stock_actual <= stock_minimo_ajustado:
                productos_criticos.append(
                    StockCriticoResponse(
                        producto_id=producto.id,
                        codigo=producto.codigo,
                        nombre=producto.nombre,
                        categoria=producto.categoria,
                        stock_actual=producto.stock_actual,
                        stock_minimo_original=producto.stock_minimo,
                        stock_minimo_ajustado=int(stock_minimo_ajustado),
                        factor_temporada=factor_temporada,
                        temporada=settings.TEMPORADA,
                        deficit=int(stock_minimo_ajustado - producto.stock_actual),
                        precio_compra_formateado=formateador.precio(producto.precio_compra)
                    )
                )

        logger.info(f"Encontrados {len(productos_criticos)} productos con stock crítico")

        return productos_criticos

    except Exception as e:
        logger.error(f"Error obteniendo stock crítico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

# ==========================================
# EVENTOS DE APLICACIÓN
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Configuración al iniciar la aplicación"""
    app.state.start_time = time.time()
    logger.info("🏭 AgenteDepósito iniciado")
    logger.info(f"Puerto: {settings.AGENTE_DEPOSITO_PORT}")
    logger.info(f"Temporada actual: {settings.TEMPORADA}")
    logger.info(f"Factor stock temporada: {obtener_factor_estacional(settings.TEMPORADA)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("🏭 AgenteDepósito cerrando...")

# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.AGENTE_DEPOSITO_PORT,
        reload=True,
        log_level="info"
    )
