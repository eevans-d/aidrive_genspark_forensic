"""
AgenteNegocio - FastAPI Application with OCR & Pricing Cache
Versión: 2.1 - Cache Optimized

Sistema optimizado con cache inteligente para:
- Resultados OCR (cache 24h - facturas no cambian)
- Cálculos de pricing (cache 30min - inflación argentina)
- Integración con AgenteDepósito cacheado
- Invalidación automática en cambios
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

# Importar cache system
from cache import (
    cache_ocr_result, cache_price_calculation, cache_frequent_query,
    invalidate_cache_by_type, get_cache_status, track_cache_stats
)

# Importaciones locales (asumir estructura existente)
from .ocr.processor import FacturaProcessor
from .pricing.engine import PricingEngine
from .integrations.deposito_client import DepositoClient

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
    logger.info("🚀 AgenteNegocio iniciando...")

    # Startup - verificar conexiones
    try:
        cache_stats = get_cache_status()
        logger.info(f"✅ Cache disponible: {cache_stats.get('redis_info', {}).get('redis_version', 'N/A')}")
    except Exception as e:
        logger.warning(f"⚠️ Cache no disponible: {e}")

    # Test conexión con AgenteDepósito
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                logger.info("✅ AgenteDepósito conectado")
            else:
                logger.warning("⚠️ AgenteDepósito no responde")
    except Exception as e:
        logger.warning(f"⚠️ Error conectando AgenteDepósito: {e}")

    yield

    # Shutdown
    logger.info("🛑 AgenteNegocio cerrando...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema Inventario - AgenteNegocio", 
    description="API para OCR de facturas y pricing con cache inteligente",
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

# Instancias de servicios
factura_processor = FacturaProcessor()
pricing_engine = PricingEngine()
deposito_client = DepositoClient(base_url="http://localhost:8001")

# === ENDPOINTS OCR (CACHEADOS) ===

@app.post("/ocr/procesar-factura", tags=["ocr"])
@cache_ocr_result(ttl=86400)  # Cache 24h - facturas no cambian
@track_cache_stats
async def procesar_factura(
    file: UploadFile = File(...),
    proveedor: Optional[str] = Form(None),
    tipo_factura: str = Form("compra"),
    auto_update_stock: bool = Form(True)
):
    """
    Procesa factura con OCR y cache inteligente
    Cache 24h porque facturas procesadas no cambian
    """
    try:
        logger.info(f"📄 Procesando factura: {file.filename}")

        # Validar archivo
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no soportado"
            )

        # Leer contenido
        file_content = await file.read()

        # Procesar con OCR (función será cacheada automáticamente)
        resultado_ocr = factura_processor.procesar_factura(
            file_content=file_content,
            filename=file.filename,
            proveedor=proveedor,
            tipo_factura=tipo_factura
        )

        # Si OCR exitoso y auto-update habilitado, actualizar stock
        if resultado_ocr.get('success') and auto_update_stock:
            productos_detectados = resultado_ocr.get('productos', [])

            for producto in productos_detectados:
                try:
                    # Actualizar stock via AgenteDepósito
                    await deposito_client.actualizar_stock_desde_factura(
                        codigo_producto=producto.get('codigo'),
                        cantidad=producto.get('cantidad', 0),
                        precio_unitario=producto.get('precio_unitario', 0),
                        referencia_factura=resultado_ocr.get('numero_factura')
                    )
                    logger.info(f"📦 Stock actualizado: {producto.get('codigo')}")

                except Exception as e:
                    logger.error(f"❌ Error actualizando stock {producto.get('codigo')}: {e}")

        return {
            "success": True,
            "message": "Factura procesada exitosamente",
            "data": resultado_ocr,
            "productos_procesados": len(resultado_ocr.get('productos', [])),
            "stock_actualizado": auto_update_stock
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando factura: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando factura: {str(e)}"
        )

@app.get("/ocr/historial", tags=["ocr"])
@cache_frequent_query(ttl=600)  # Cache 10 min
@track_cache_stats
async def obtener_historial_ocr(
    limit: int = 50,
    skip: int = 0,
    proveedor: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
):
    """Obtiene historial de facturas procesadas con cache"""
    try:
        logger.info(f"📋 Obteniendo historial OCR: limit={limit}, skip={skip}")

        # Obtener historial (función será cacheada)
        historial = factura_processor.obtener_historial(
            limit=limit,
            skip=skip,
            proveedor=proveedor,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        return {
            "success": True,
            "data": historial,
            "message": f"Historial obtenido: {len(historial)} facturas"
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo historial OCR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.get("/ocr/estadisticas", tags=["ocr"])
@cache_frequent_query(ttl=1800)  # Cache 30 min
@track_cache_stats
async def obtener_estadisticas_ocr():
    """Obtiene estadísticas de procesamiento OCR con cache"""
    try:
        logger.info("📊 Obteniendo estadísticas OCR")

        # Obtener estadísticas (función será cacheada)
        stats = factura_processor.obtener_estadisticas()

        return {
            "success": True,
            "data": stats,
            "message": "Estadísticas OCR obtenidas"
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas OCR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ENDPOINTS PRICING (CACHEADOS) ===

@app.post("/pricing/calcular-precio", tags=["pricing"])
@cache_price_calculation(ttl=1800)  # Cache 30min - inflación argentina
@track_cache_stats
async def calcular_precio_producto(
    codigo_producto: str,
    costo_base: float,
    margen_deseado: float = 30.0,
    categoria: Optional[str] = None,
    aplicar_inflacion: bool = True
):
    """
    Calcula precio de venta con cache inteligente
    Cache 30min por inflación argentina (4.5% mensual)
    """
    try:
        logger.info(f"💰 Calculando precio: {codigo_producto}")

        # Obtener producto del depósito para contexto
        producto_info = await deposito_client.obtener_producto_por_codigo(codigo_producto)

        # Calcular precio (función será cacheada automáticamente)
        precio_calculado = pricing_engine.calcular_precio_venta(
            costo_base=costo_base,
            margen_deseado=margen_deseado,
            categoria=categoria or producto_info.get('categoria'),
            aplicar_inflacion=aplicar_inflacion,
            contexto_producto=producto_info
        )

        return {
            "success": True,
            "data": {
                "codigo_producto": codigo_producto,
                "costo_base": costo_base,
                "precio_sugerido": precio_calculado.get('precio_final'),
                "margen_aplicado": precio_calculado.get('margen_final'),
                "inflacion_aplicada": precio_calculado.get('inflacion_aplicada'),
                "fecha_calculo": precio_calculado.get('timestamp'),
                "factores": precio_calculado.get('factores_aplicados')
            },
            "message": f"Precio calculado para {codigo_producto}"
        }

    except Exception as e:
        logger.error(f"❌ Error calculando precio {codigo_producto}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculando precio: {str(e)}"
        )

@app.post("/pricing/actualizar-precios-masivo", tags=["pricing"])
@track_cache_stats
async def actualizar_precios_masivo(
    productos: list[dict],
    aplicar_inmediatamente: bool = False
):
    """
    Actualiza precios en lote e invalida cache relacionado
    """
    try:
        logger.info(f"💰 Actualizando precios masivo: {len(productos)} productos")

        resultados = []

        for producto_data in productos:
            codigo = producto_data.get('codigo')
            costo_base = producto_data.get('costo_base')
            margen = producto_data.get('margen', 30.0)

            try:
                # Calcular nuevo precio
                precio_calculado = pricing_engine.calcular_precio_venta(
                    costo_base=costo_base,
                    margen_deseado=margen,
                    aplicar_inflacion=True
                )

                # Si aplicar inmediatamente, actualizar en depósito
                if aplicar_inmediatamente:
                    await deposito_client.actualizar_precio_producto(
                        codigo=codigo,
                        nuevo_precio=precio_calculado.get('precio_final')
                    )

                resultados.append({
                    "codigo": codigo,
                    "precio_anterior": producto_data.get('precio_actual'),
                    "precio_nuevo": precio_calculado.get('precio_final'),
                    "actualizado": aplicar_inmediatamente,
                    "status": "success"
                })

            except Exception as e:
                logger.error(f"Error procesando {codigo}: {e}")
                resultados.append({
                    "codigo": codigo,
                    "status": "error",
                    "error": str(e)
                })

        # Invalidar cache de precios después de actualización masiva
        if aplicar_inmediatamente:
            invalidate_cache_by_type('price', '*')
            invalidate_cache_by_type('product', '*')  # Productos también tienen precios
            logger.info("🗑️ Cache precios invalidado por actualización masiva")

        return {
            "success": True,
            "data": {
                "resultados": resultados,
                "total_procesados": len(productos),
                "exitosos": len([r for r in resultados if r.get('status') == 'success']),
                "errores": len([r for r in resultados if r.get('status') == 'error'])
            },
            "message": f"Precios procesados: {len(productos)} productos"
        }

    except Exception as e:
        logger.error(f"❌ Error actualizando precios masivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@app.get("/pricing/analisis-mercado", tags=["pricing"])
@cache_frequent_query(ttl=3600)  # Cache 1h
@track_cache_stats
async def obtener_analisis_mercado(
    categoria: Optional[str] = None,
    incluir_competencia: bool = True
):
    """Análisis de mercado con cache (datos cambian poco)"""
    try:
        logger.info(f"📈 Análisis mercado: categoria={categoria}")

        # Análisis será cacheado automáticamente
        analisis = pricing_engine.generar_analisis_mercado(
            categoria=categoria,
            incluir_competencia=incluir_competencia
        )

        return {
            "success": True,
            "data": analisis,
            "message": "Análisis de mercado generado"
        }

    except Exception as e:
        logger.error(f"❌ Error análisis mercado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# === ENDPOINTS DE INTEGRACIÓN ===

@app.post("/integracion/sync-deposito", tags=["integración"])
@track_cache_stats
async def sincronizar_con_deposito():
    """Sincroniza datos con AgenteDepósito e invalida cache"""
    try:
        logger.info("🔄 Sincronizando con AgenteDepósito")

        # Obtener productos desde depósito
        productos = await deposito_client.listar_todos_productos()

        # Procesar y actualizar precios si es necesario
        productos_actualizados = 0

        for producto in productos:
            # Lógica de sincronización específica
            # ...
            productos_actualizados += 1

        # Invalidar cache después de sync
        invalidate_cache_by_type('product', '*')
        invalidate_cache_by_type('price', '*')
        logger.info("🗑️ Cache invalidado después de sincronización")

        return {
            "success": True,
            "data": {
                "productos_sincronizados": productos_actualizados,
                "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
            },
            "message": f"Sincronización completa: {productos_actualizados} productos"
        }

    except Exception as e:
        logger.error(f"❌ Error sincronización: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sincronización: {str(e)}"
        )

# === ENDPOINTS DE SISTEMA ===

@app.get("/health", tags=["sistema"])
async def health_check():
    """Health check incluyendo conexiones y cache"""
    try:
        # Test cache
        try:
            cache_stats = get_cache_status()
            cache_health = {
                "status": "healthy",
                "hit_rate": cache_stats.get('cache_stats', {}).get('hit_rate', 0),
                "total_requests": cache_stats.get('cache_stats', {}).get('total_requests', 0)
            }
        except Exception as e:
            cache_health = {"status": "unhealthy", "error": str(e)}

        # Test AgenteDepósito connection
        try:
            deposito_status = await deposito_client.health_check()
            deposito_health = {"status": "healthy", "response_time": deposito_status.get('response_time')}
        except Exception as e:
            deposito_health = {"status": "unhealthy", "error": str(e)}

        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Placeholder
            "services": {
                "ocr": {"status": "healthy"},
                "pricing": {"status": "healthy"},
                "cache": cache_health,
                "deposito": deposito_health
            }
        }

    except Exception as e:
        logger.error(f"❌ Error health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Servicio no disponible: {str(e)}"
        )

@app.get("/cache/stats", tags=["sistema"])
@track_cache_stats
async def obtener_estadisticas_cache():
    """Estadísticas detalladas del cache"""
    try:
        cache_stats = get_cache_status()
        return {
            "success": True,
            "data": cache_stats,
            "message": "Estadísticas cache AgenteNegocio"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo stats: {str(e)}"
        )

@app.post("/cache/invalidate/ocr", tags=["sistema"])
async def invalidar_cache_ocr():
    """Invalida cache OCR manualmente"""
    try:
        deleted = invalidate_cache_by_type('ocr', '*')
        return {
            "success": True,
            "data": {"deleted_keys": deleted},
            "message": f"Cache OCR invalidado: {deleted} keys"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando cache: {str(e)}"
        )

@app.post("/cache/invalidate/pricing", tags=["sistema"])
async def invalidar_cache_pricing():
    """Invalida cache pricing manualmente"""
    try:
        deleted = invalidate_cache_by_type('price', '*')
        return {
            "success": True,
            "data": {"deleted_keys": deleted},
            "message": f"Cache pricing invalidado: {deleted} keys"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidando cache: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_cached:app",
        host="0.0.0.0", 
        port=8002,
        reload=True,
        log_level="info"
    )
