"""
AgenteNegocio con OCR Avanzado
=============================

API FastAPI del AgenteNegocio mejorada con OCR avanzado multi-engine,
manteniendo compatibilidad con API existente pero agregando endpoints
y funcionalidades del sistema OCR avanzado.

Autor: Sistema Inventario Retail Argentino
Fecha: 2025-08-22
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import asyncio
import logging
import os
from datetime import datetime
import json
import uuid

# Importar nuestros nuevos módulos OCR
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_engine_advanced import OCREngineAdvanced, FacturaType
from image_preprocessor import ImagePreprocessor
from factura_validator import FacturaValidatorArgentino, ValidationResult
from ocr_postprocessor import OCRPostprocessor

# Importar cache manager si está disponible
try:
    from cache.intelligent_cache_manager import IntelligentCacheManager
    cache_manager = IntelligentCacheManager()
except ImportError:
    cache_manager = None
    print("⚠️ Cache manager no disponible, funcionando sin cache")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgenteNegocio OCR Avanzado",
    description="API para procesamiento avanzado de facturas con OCR multi-engine",
    version="2.0.0"
)

# Modelos Pydantic para API
class FacturaProcessRequest(BaseModel):
    """Request para procesar factura"""
    auto_enhance: bool = True
    validate_fields: bool = True
    return_debug_info: bool = False

class FacturaProcessResponse(BaseModel):
    """Response de procesamiento de factura"""
    success: bool
    factura_id: str
    processing_time: float
    ocr_confidence: float
    validation_passed: bool
    extracted_data: Dict
    errors: List[str] = []
    warnings: List[str] = []
    debug_info: Optional[Dict] = None

class OCRStatsResponse(BaseModel):
    """Response de estadísticas OCR"""
    ocr_engine_stats: Dict
    postprocessor_stats: Dict
    cache_stats: Optional[Dict] = None
    total_processed: int
    avg_processing_time: float

# Instancias globales de nuestros componentes
ocr_engine = OCREngineAdvanced(cache_manager=cache_manager)
image_preprocessor = ImagePreprocessor()
factura_validator = FacturaValidatorArgentino()
ocr_postprocessor = OCRPostprocessor()

# Directorio temporal para subidas
UPLOAD_DIR = "/tmp/facturas_upload"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Inicialización del sistema OCR avanzado"""
    logger.info("🚀 Iniciando AgenteNegocio OCR Avanzado v2.0")

    # Health check de componentes
    health = await ocr_engine.health_check()
    logger.info(f"OCR Engine Health: {health}")

    if cache_manager:
        logger.info("✅ Cache inteligente activado")
    else:
        logger.warning("⚠️ Sin cache - performance reducido")

@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "service": "AgenteNegocio OCR Avanzado",
        "version": "2.0.0",
        "status": "online",
        "features": [
            "OCR Multi-Engine (EasyOCR + Tesseract + PaddleOCR)",
            "Computer Vision Preprocessing",
            "Validación Argentina AFIP",
            "Postprocessing Inteligente",
            "Cache Avanzado",
            "Backward Compatibility"
        ],
        "endpoints": {
            "legacy": "/procesar-factura (compatible v1.0)",
            "advanced": "/procesar-factura-avanzada",
            "batch": "/procesar-facturas-batch",
            "stats": "/ocr-stats",
            "health": "/health"
        }
    }

@app.post("/procesar-factura", response_model=Dict)
async def procesar_factura_legacy(
    archivo: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Endpoint LEGACY compatible con v1.0
    Mantiene compatibilidad total con API existente
    """
    try:
        # Procesar con OCR avanzado pero formato legacy
        result = await _procesar_factura_internal(
            archivo, 
            auto_enhance=True,
            validate_fields=True,
            return_debug_info=False
        )

        # Formatear respuesta compatible con v1.0
        legacy_response = {
            "success": result["success"],
            "mensaje": "Factura procesada correctamente" if result["success"] else "Error procesando factura",
            "datos_extraidos": result.get("extracted_data", {}),
            "confidence_score": result.get("ocr_confidence", 0.0),
            "tiempo_procesamiento": result.get("processing_time", 0.0)
        }

        if result["errors"]:
            legacy_response["errores"] = result["errors"]

        return legacy_response

    except Exception as e:
        logger.error(f"Error en procesamiento legacy: {e}")
        return {
            "success": False,
            "mensaje": f"Error procesando factura: {str(e)}",
            "datos_extraidos": {},
            "confidence_score": 0.0
        }

@app.post("/procesar-factura-avanzada", response_model=FacturaProcessResponse)
async def procesar_factura_avanzada(
    archivo: UploadFile = File(...),
    request: FacturaProcessRequest = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Endpoint AVANZADO con todas las funcionalidades OCR v2.0
    """
    try:
        result = await _procesar_factura_internal(
            archivo,
            auto_enhance=request.auto_enhance,
            validate_fields=request.validate_fields,
            return_debug_info=request.return_debug_info
        )

        return FacturaProcessResponse(**result)

    except Exception as e:
        logger.error(f"Error en procesamiento avanzado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def _procesar_factura_internal(
    archivo: UploadFile,
    auto_enhance: bool = True,
    validate_fields: bool = True,
    return_debug_info: bool = False
) -> Dict:
    """Función interna para procesar facturas (compartida por ambas APIs)"""

    start_time = datetime.now()
    factura_id = str(uuid.uuid4())

    try:
        # 1. Guardar archivo subido
        file_extension = os.path.splitext(archivo.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.pdf', '.tiff']:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

        temp_file_path = os.path.join(UPLOAD_DIR, f"{factura_id}{file_extension}")

        with open(temp_file_path, "wb") as buffer:
            content = await archivo.read()
            buffer.write(content)

        debug_info = {"temp_file": temp_file_path} if return_debug_info else {}

        # 2. Preprocessar imagen
        logger.info(f"📸 Preprocessando imagen: {archivo.filename}")
        preprocess_result = image_preprocessor.preprocess_factura(temp_file_path, auto_enhance)

        if return_debug_info:
            debug_info["preprocessing"] = {
                "original_size": preprocess_result.original_size,
                "rotation_angle": preprocess_result.rotation_angle,
                "perspective_corrected": preprocess_result.perspective_corrected,
                "roi_detected": preprocess_result.roi_detected,
                "quality_score": preprocess_result.quality_score,
                "processing_steps": preprocess_result.processing_steps
            }

        # Guardar imagen preprocessada temporalmente
        preprocessed_file_path = os.path.join(UPLOAD_DIR, f"{factura_id}_preprocessed.jpg")
        import cv2
        cv2.imwrite(preprocessed_file_path, preprocess_result.processed_image)

        # 3. OCR Avanzado Multi-Engine
        logger.info(f"🔍 Ejecutando OCR avanzado multi-engine")
        ocr_result = await ocr_engine.process_factura(preprocessed_file_path)

        if not ocr_result.get("success", False):
            raise Exception(f"OCR falló: {ocr_result.get('error', 'Error desconocido')}")

        # 4. Postprocesamiento
        logger.info(f"🧹 Postprocesando resultados OCR")
        postprocess_result = ocr_postprocessor.postprocess_ocr_result(
            ocr_result["text_raw"], 
            ocr_result["confidence"]
        )

        # 5. Validación Argentina (si se solicitó)
        validation_result = None
        if validate_fields:
            logger.info(f"✅ Validando campos argentinos")
            validation_result = factura_validator.validate_factura_completa(
                postprocess_result.cleaned_text
            )

        # 6. Combinar datos extraídos
        extracted_data = {
            **ocr_result.get("campos_extraidos", {}),
            **postprocess_result.structured_data
        }

        if validation_result and validation_result.is_valid:
            extracted_data.update(validation_result.normalized_data)

        # 7. Calcular tiempo total
        processing_time = (datetime.now() - start_time).total_seconds()

        # 8. Preparar respuesta
        response = {
            "success": True,
            "factura_id": factura_id,
            "processing_time": processing_time,
            "ocr_confidence": postprocess_result.confidence_score,
            "validation_passed": validation_result.is_valid if validation_result else True,
            "extracted_data": extracted_data,
            "errors": validation_result.errors if validation_result else [],
            "warnings": validation_result.warnings if validation_result else []
        }

        if return_debug_info:
            debug_info.update({
                "ocr_engine": ocr_result.get("engine", "unknown"),
                "engines_used": ocr_result.get("engines_used", 0),
                "postprocessing": {
                    "corrections_made": postprocess_result.corrections_made,
                    "processing_stats": postprocess_result.processing_stats
                },
                "validation_confidence": validation_result.confidence_score if validation_result else None
            })
            response["debug_info"] = debug_info

        # 9. Limpiar archivos temporales
        try:
            os.unlink(temp_file_path)
            os.unlink(preprocessed_file_path)
        except OSError:
            logger.warning("No se pudieron limpiar archivos temporales")

        logger.info(f"✅ Factura {factura_id} procesada en {processing_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f"❌ Error procesando factura {factura_id}: {e}")

        # Limpiar archivos en caso de error
        for file_path in [temp_file_path, preprocessed_file_path]:
            try:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass

        return {
            "success": False,
            "factura_id": factura_id,
            "processing_time": (datetime.now() - start_time).total_seconds(),
            "ocr_confidence": 0.0,
            "validation_passed": False,
            "extracted_data": {},
            "errors": [str(e)],
            "warnings": []
        }

@app.post("/procesar-facturas-batch")
async def procesar_facturas_batch(
    archivos: List[UploadFile] = File(...),
    auto_enhance: bool = Form(True),
    validate_fields: bool = Form(True)
):
    """Procesar múltiples facturas en paralelo"""

    if len(archivos) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 facturas por batch")

    start_time = datetime.now()

    # Procesar en paralelo
    tasks = []
    for archivo in archivos:
        task = _procesar_factura_internal(
            archivo, auto_enhance, validate_fields, return_debug_info=False
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Formatear resultados
    batch_response = {
        "success": True,
        "batch_id": str(uuid.uuid4()),
        "total_files": len(archivos),
        "processing_time": (datetime.now() - start_time).total_seconds(),
        "results": []
    }

    successful = 0
    failed = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            batch_response["results"].append({
                "file_index": i,
                "filename": archivos[i].filename,
                "success": False,
                "error": str(result)
            })
            failed += 1
        else:
            batch_response["results"].append({
                "file_index": i,
                "filename": archivos[i].filename,
                **result
            })
            if result["success"]:
                successful += 1
            else:
                failed += 1

    batch_response.update({
        "successful": successful,
        "failed": failed,
        "success_rate": successful / len(archivos) if archivos else 0
    })

    return batch_response

@app.get("/ocr-stats", response_model=OCRStatsResponse)
async def get_ocr_stats():
    """Obtener estadísticas del sistema OCR"""
    try:
        ocr_stats = ocr_engine.get_stats()
        postprocessor_stats = ocr_postprocessor.get_stats()

        cache_stats = None
        if cache_manager:
            try:
                cache_stats = await cache_manager.get_stats()
            except Exception as e:
                logger.warning(f"Error obteniendo stats cache: {e}")

        return OCRStatsResponse(
            ocr_engine_stats=ocr_stats,
            postprocessor_stats=postprocessor_stats,
            cache_stats=cache_stats,
            total_processed=ocr_stats.get("total_processed", 0),
            avg_processing_time=ocr_stats.get("avg_processing_time", 0.0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {e}")

@app.get("/health")
async def health_check():
    """Health check completo del sistema"""
    try:
        # Health check OCR engine
        ocr_health = await ocr_engine.health_check()

        # Health check cache
        cache_health = {"status": "not_available"}
        if cache_manager:
            try:
                cache_health = await cache_manager.health_check()
            except Exception as e:
                cache_health = {"status": "error", "error": str(e)}

        # Health check sistema
        system_health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "upload_dir_writable": os.access(UPLOAD_DIR, os.W_OK),
            "temp_space_mb": _get_disk_space_mb(UPLOAD_DIR)
        }

        overall_status = "healthy"
        if ocr_health["status"] != "healthy" or cache_health["status"] == "error":
            overall_status = "degraded"

        return {
            "status": overall_status,
            "components": {
                "ocr_engine": ocr_health,
                "cache_manager": cache_health,
                "system": system_health
            },
            "endpoints_available": [
                "/procesar-factura",
                "/procesar-factura-avanzada", 
                "/procesar-facturas-batch",
                "/ocr-stats",
                "/health"
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def _get_disk_space_mb(path: str) -> int:
    """Obtener espacio disponible en disco"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return free // (1024 * 1024)  # MB
    except Exception:
        return 0

@app.get("/test-ocr")
async def test_ocr_endpoint():
    """Endpoint de test para verificar OCR sin subir archivo"""
    try:
        # Crear imagen de test
        import cv2
        import numpy as np

        # Imagen de test simple
        test_image = np.ones((200, 600, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "FACTURA B", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_image, "CUIT: 20-12345678-9", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(test_image, "TOTAL: $1.234,56", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # Guardar imagen de test
        test_file = os.path.join(UPLOAD_DIR, "test_ocr.jpg")
        cv2.imwrite(test_file, test_image)

        # Procesar con OCR
        ocr_result = await ocr_engine.process_factura(test_file)

        # Limpiar
        os.unlink(test_file)

        return {
            "success": True,
            "message": "Test OCR completado",
            "ocr_result": ocr_result,
            "engines_available": ocr_result.get("engines_used", 0) > 0
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Test OCR falló"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
