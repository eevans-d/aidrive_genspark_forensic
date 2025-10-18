
# Imports principales
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from shared.security_headers import apply_fastapi_security
from shared.errors import register_fastapi_error_handlers
from shared.config import validate_env_vars
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Inicialización de logging y settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import get_settings, setup_logging
from shared.auth import require_role, NEGOCIO_ROLE
from .ocr.processor import OCRProcessor
from .pricing.engine import PricingEngine
from .invoice.processor import InvoiceProcessor
from .integrations.deposito_client import DepositoClient
from .services.openai_service import get_openai_service, check_openai_health

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# Inicialización de la aplicación FastAPI
app = FastAPI(title="AgenteNegocio - OCR & Pricing", version="1.0.0")
register_fastapi_error_handlers(app)
validate_env_vars([
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
])

# Métricas Prometheus
REQUEST_COUNT = Counter('agente_negocio_requests_total', 'Total de requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('agente_negocio_request_latency_seconds', 'Latencia de requests', ['endpoint'])

# Middleware para logging y métricas
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()

    # Prometheus metrics
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(process_time)

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

# Endpoint /metrics Prometheus
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

"""
Agente de Negocio - FastAPI
Procesamiento de facturas AFIP con OCR, pricing por inflación y actualización de stock.
Puerto 8001 con integración completa al Agente Depósito.
"""

# Imports principales
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from shared.security_headers import apply_fastapi_security
from shared.errors import register_fastapi_error_handlers
from shared.config import validate_env_vars
import os

# Configuración de rutas y entorno
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import get_settings, setup_logging
from shared.auth import require_role, NEGOCIO_ROLE
from .ocr.processor import OCRProcessor
from .pricing.engine import PricingEngine
from .invoice.processor import InvoiceProcessor
from .integrations.deposito_client import DepositoClient

# Inicialización de logging y settings
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# Inicialización de la aplicación FastAPI
app = FastAPI(title="AgenteNegocio - OCR & Pricing", version="1.0.0")
register_fastapi_error_handlers(app)
validate_env_vars([
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
])
# CORS seguro por entorno
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
_cors_methods = [m.strip() for m in os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",") if m.strip()]
_cors_headers = [h.strip() for h in os.getenv("CORS_HEADERS", "Authorization,Content-Type").split(",") if h.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=_cors_methods,
    allow_headers=_cors_headers,
)

# Security headers
apply_fastapi_security(app)

# Inicializar componentes de negocio
ocr_processor = OCRProcessor()
pricing_engine = PricingEngine()
invoice_processor = InvoiceProcessor()
deposito_client = DepositoClient()


@app.get("/health")
async def health(current_user: dict = Depends(require_role(NEGOCIO_ROLE))):
    """
    Health check con verificación de conectividad al Agente Depósito.
    """
    try:
        deposito_status = await deposito_client.health_check()
        return {
            "status": "healthy",
            "service": "agente_negocio",
            "timestamp": datetime.utcnow().isoformat(),
            "deposito_status": "connected" if deposito_status else "disconnected"
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/precios/consultar")
async def consultar_precio(codigo: str, dias_desde_compra: int = 0, current_user: dict = Depends(require_role(NEGOCIO_ROLE))):
    """
    Consultar precio actualizado aplicando inflación.
    """
    try:
        precio = await pricing_engine.calcular_precio_inflacion(codigo, dias_desde_compra)
        return {
            "codigo": codigo,
            "precio_actualizado": precio,
            "dias_transcurridos": dias_desde_compra,
            "inflacion_aplicada": settings.INFLACION_MENSUAL
        }
    except Exception as e:
        logger.error(f"Error consultando precio: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/facturas/procesar")
async def procesar_factura(
    file: UploadFile = File(...),
    proveedor_cuit: str = Form(...),
    current_user: dict = Depends(require_role(NEGOCIO_ROLE))
):
    """
    Procesar factura E2E: OCR → Pricing → Actualización de stock.
    """
    try:
        logger.info(f"Procesando factura de proveedor CUIT: {proveedor_cuit}")
        resultado = await invoice_processor.process_invoice_e2e(file, proveedor_cuit)
        logger.info(f"Factura procesada exitosamente: {resultado['factura_id']}")
        return resultado
    except Exception as e:
        logger.error(f"Error procesando factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DÍA 1: CIRCUIT BREAKER ENDPOINTS (New)
# ============================================================================

@app.post("/ai/enhance-ocr")
async def enhance_ocr(
    text: str,
    current_user: dict = Depends(require_role(NEGOCIO_ROLE))
):
    """
    Mejorar texto OCR usando OpenAI con protección de circuit breaker.
    
    Features:
    - Circuit breaker protection (abre después de 5 fallos en 60s)
    - Fallback automático si OpenAI está down
    - Prometheus metrics
    - Structured logging
    
    Returns:
        - success: bool (True si OpenAI disponible)
        - data: str (texto mejorado o fallback)
        - fallback: bool (True si se usó fallback)
        - breaker_state: str (closed, open, half-open)
        - latency: float (segundos)
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    try:
        service = get_openai_service()
        result = await service.enhance_ocr_text(text, request_id=request_id)
        
        logger.info(
            f"OCR enhancement completed",
            extra={
                "request_id": request_id,
                "status": "success" if result['success'] else "fallback",
                "breaker_state": result['breaker_state'],
                "latency": result['latency']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en enhance-ocr: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/pricing")
async def generate_pricing(
    item_data: dict,
    current_user: dict = Depends(require_role(NEGOCIO_ROLE))
):
    """
    Generar pricing usando OpenAI con protección de circuit breaker.
    
    Features:
    - Circuit breaker protection
    - Fallback a algoritmo básico si OpenAI está down
    - Smart pricing recommendations
    
    Request body:
        {
            "name": "Item name",
            "category": "electronics",
            "cost": 100.0,
            "target_margin": "30%"
        }
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    try:
        service = get_openai_service()
        result = await service.generate_pricing(item_data, request_id=request_id)
        
        logger.info(
            f"Pricing generated",
            extra={
                "request_id": request_id,
                "status": "success" if result['success'] else "fallback",
                "breaker_state": result['breaker_state'],
                "latency": result['latency']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en pricing: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/analyze-invoice")
async def analyze_invoice(
    invoice_text: str,
    current_user: dict = Depends(require_role(NEGOCIO_ROLE))
):
    """
    Analizar factura usando OpenAI con protección de circuit breaker.
    
    Features:
    - Extracción inteligente de datos
    - Fallback a análisis manual si OpenAI down
    - Circuit breaker protection
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    try:
        service = get_openai_service()
        result = await service.analyze_invoice(invoice_text, request_id=request_id)
        
        logger.info(
            f"Invoice analyzed",
            extra={
                "request_id": request_id,
                "status": "success" if result['success'] else "fallback",
                "breaker_state": result['breaker_state'],
                "latency": result['latency']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en analyze-invoice: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/openai")
async def openai_health():
    """
    Health check para OpenAI service y circuit breaker.
    
    No requiere autenticación (es un health check).
    
    Returns:
        {
            "service": "openai",
            "status": "healthy" | "degraded",
            "breaker_state": "closed" | "open" | "half-open",
            "fail_counter": int,
            "fail_max": int
        }
    """
    try:
        health = await check_openai_health()
        return health
    except Exception as e:
        logger.error(f"Error en health check OpenAI: {e}")
        return {
            "service": "openai",
            "status": "error",
            "error": str(e)
        }


@app.on_event("startup")
async def startup():
    logger.info("🧠 AgenteNegocio iniciado - Puerto 8001")
    logger.info("🔌 OpenAI Circuit Breaker initialized")
    health = await check_openai_health()
    logger.info(f"   OpenAI health: {health['status']} (state: {health['breaker_state']})")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.AGENTE_NEGOCIO_PORT, reload=True)
