"""
Fallback Strategies - Estrategias de Fallback para Circuit Breakers

Este módulo define las estrategias de fallback cuando los circuit breakers
están abiertos y las dependencias no están disponibles.

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation (Resilience Hardening)
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# OPENAI API FALLBACKS
# ============================================================================

def openai_fallback(prompt: str, model: str = "gpt-4", **kwargs) -> Dict[str, Any]:
    """
    Fallback cuando OpenAI API no está disponible.
    
    Args:
        prompt: El prompt que se iba a enviar
        model: Modelo que se iba a usar
        **kwargs: Otros parámetros
        
    Returns:
        Respuesta de fallback con información del sistema degradado
    """
    logger.warning(
        f"OpenAI circuit breaker open, usando fallback",
        extra={
            "prompt_length": len(prompt),
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "response": "Sistema temporalmente en modo degradado. Las funciones de IA están deshabilitadas. Por favor intente nuevamente en unos momentos.",
        "status": "fallback",
        "reason": "openai_circuit_open",
        "degraded": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def openai_ocr_enhancement_fallback(raw_ocr_text: str) -> str:
    """
    Fallback para OCR enhancement cuando OpenAI no disponible.
    Retorna el texto OCR sin enhancement.
    
    Args:
        raw_ocr_text: Texto crudo del OCR
        
    Returns:
        Texto sin enhancement con nota
    """
    logger.info("Using OCR without AI enhancement (fallback)")
    
    return f"{raw_ocr_text}\n\n[Nota: Procesado sin mejora de IA]"


def openai_pricing_fallback(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback para pricing cuando OpenAI no disponible.
    Usa algoritmo básico sin IA.
    
    Args:
        item_data: Datos del item
        
    Returns:
        Precio calculado con método básico
    """
    logger.info(f"Using basic pricing fallback for item: {item_data.get('id')}")
    
    # Algoritmo básico: costo + markup estándar
    cost = item_data.get('cost', 0)
    markup = 1.3  # 30% markup por defecto
    
    return {
        "price": cost * markup,
        "method": "basic_fallback",
        "confidence": "low",
        "degraded": True,
        "note": "Calculado con algoritmo básico (sin IA)"
    }


# ============================================================================
# DATABASE FALLBACKS
# ============================================================================

def db_read_fallback(item_id: str, cache_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Fallback cuando DB no está disponible para reads.
    Intenta usar cache o retorna mensaje de degradación.
    
    Args:
        item_id: ID del item solicitado
        cache_data: Datos en cache si existen
        
    Returns:
        Datos desde cache o mensaje de no disponibilidad
    """
    if cache_data:
        logger.info(f"Using cached data for item {item_id} (DB circuit open)")
        return {
            **cache_data,
            "source": "cache_fallback",
            "degraded": True
        }
    
    logger.warning(f"No cached data for item {item_id}, DB unavailable")
    return {
        "item_id": item_id,
        "status": "unavailable",
        "message": "Sistema temporalmente en mantenimiento. Datos no disponibles.",
        "degraded": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def db_write_fallback(operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback cuando DB no está disponible para writes.
    En modo degradado, no se permiten escrituras.
    
    Args:
        operation: Tipo de operación (insert, update, delete)
        data: Datos que se iban a escribir
        
    Returns:
        Mensaje indicando que write no permitido en modo degradado
    """
    logger.warning(
        f"Write operation '{operation}' blocked (DB circuit open)",
        extra={"operation": operation, "data_keys": list(data.keys())}
    )
    
    return {
        "status": "rejected",
        "message": "Operaciones de escritura temporalmente deshabilitadas. Sistema en modo read-only.",
        "operation": operation,
        "degraded": True,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# REDIS CACHE FALLBACKS
# ============================================================================

def cache_read_fallback(key: str, fetch_from_db_func: Optional[callable] = None) -> Optional[Any]:
    """
    Fallback cuando cache no está disponible.
    Intenta fetch directo desde DB.
    
    Args:
        key: Key del cache
        fetch_from_db_func: Función para fetch desde DB
        
    Returns:
        Datos desde DB o None
    """
    logger.info(f"Cache miss (Redis circuit open), fetching from DB for key: {key}")
    
    if fetch_from_db_func:
        try:
            return fetch_from_db_func(key)
        except Exception as e:
            logger.error(f"DB fetch fallback failed for key {key}: {e}")
            return None
    
    return None


def cache_write_fallback(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Fallback cuando cache no está disponible para writes.
    Log el intento pero no falla la operación.
    
    Args:
        key: Key del cache
        value: Valor a cachear
        ttl: Time to live
        
    Returns:
        False (cache write failed pero no crítico)
    """
    logger.debug(f"Cache write skipped (Redis circuit open) for key: {key}")
    return False


# ============================================================================
# S3 STORAGE FALLBACKS
# ============================================================================

def s3_upload_fallback(file_path: str, bucket: str) -> Dict[str, Any]:
    """
    Fallback cuando S3 no está disponible para uploads.
    
    Args:
        file_path: Path del archivo
        bucket: Bucket destino
        
    Returns:
        Mensaje indicando que upload falló
    """
    logger.warning(f"S3 upload blocked (circuit open): {file_path}")
    
    return {
        "status": "deferred",
        "message": "Almacenamiento temporalmente no disponible. El archivo se guardará localmente y se sincronizará después.",
        "file_path": file_path,
        "bucket": bucket,
        "degraded": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def s3_download_fallback(key: str, bucket: str) -> Optional[bytes]:
    """
    Fallback cuando S3 no está disponible para downloads.
    
    Args:
        key: Key del objeto
        bucket: Bucket origen
        
    Returns:
        None (descarga no posible)
    """
    logger.warning(f"S3 download failed (circuit open): {key}")
    return None


# ============================================================================
# GENERIC FALLBACK FACTORY
# ============================================================================

class FallbackFactory:
    """
    Factory para crear fallbacks genéricos basados en tipo de operación.
    """
    
    @staticmethod
    def create_generic_fallback(
        service_name: str,
        operation: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea un fallback genérico para cualquier servicio.
        
        Args:
            service_name: Nombre del servicio (openai, db, redis, etc.)
            operation: Tipo de operación (read, write, call, etc.)
            data: Datos opcionales del contexto
            
        Returns:
            Respuesta de fallback genérica
        """
        logger.warning(
            f"Generic fallback triggered: {service_name}/{operation}",
            extra={"service": service_name, "operation": operation}
        )
        
        return {
            "status": "fallback",
            "message": f"Servicio {service_name} temporalmente no disponible. Usando modo degradado.",
            "service": service_name,
            "operation": operation,
            "degraded": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def should_retry(exception: Exception) -> bool:
    """
    Determina si una excepción debe ser reintentada.
    
    Args:
        exception: Excepción a evaluar
        
    Returns:
        True si debe reintentar, False si no
    """
    # Lista de excepciones que NO deben reintentarse
    non_retryable = [
        'ValidationError',
        'ValueError',
        'KeyError',
        'AuthenticationError'
    ]
    
    exception_name = exception.__class__.__name__
    return exception_name not in non_retryable


def get_fallback_message(service: str, lang: str = "es") -> str:
    """
    Obtiene mensaje de fallback localizado.
    
    Args:
        service: Nombre del servicio
        lang: Idioma (es, en)
        
    Returns:
        Mensaje localizado
    """
    messages = {
        "es": {
            "openai": "Funciones de IA temporalmente no disponibles",
            "database": "Base de datos en mantenimiento",
            "cache": "Sistema de caché no disponible",
            "storage": "Almacenamiento temporalmente no disponible",
            "generic": "Servicio temporalmente no disponible"
        },
        "en": {
            "openai": "AI features temporarily unavailable",
            "database": "Database under maintenance",
            "cache": "Cache system unavailable",
            "storage": "Storage temporarily unavailable",
            "generic": "Service temporarily unavailable"
        }
    }
    
    return messages.get(lang, messages["es"]).get(service, messages[lang]["generic"])


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

"""
EJEMPLO 1: Usar fallback con decorator

from shared.circuit_breakers import openai_breaker
from shared.fallbacks import openai_fallback

@openai_breaker
async def call_openai_api(prompt: str):
    try:
        # Llamada real
        response = await openai.ChatCompletion.acreate(...)
        return response
    except Exception:
        # Circuit breaker detectará el fallo
        raise

# Cuando circuit está abierto, usar fallback:
try:
    result = await call_openai_api(prompt)
except Exception:
    result = openai_fallback(prompt)


EJEMPLO 2: Fallback automático en servicio

async def get_item_from_cache_or_db(item_id: str):
    try:
        # Intentar cache primero
        return await cache.get(item_id)
    except Exception:
        # Cache down, usar fallback
        return cache_read_fallback(
            item_id,
            fetch_from_db_func=lambda: db.get_item(item_id)
        )


EJEMPLO 3: Factory para fallback genérico

fallback_result = FallbackFactory.create_generic_fallback(
    service_name="payment_gateway",
    operation="process_payment",
    data={"amount": 100, "currency": "ARS"}
)
"""

# ============================================================================
# TODO: IMPLEMENTACIÓN DÍA 1-2
# ============================================================================

"""
DÍA 1-2: Integrar con Circuit Breakers
  [ ] Crear este módulo (fallbacks.py)
  [ ] Implementar fallbacks para OpenAI
  [ ] Implementar fallbacks para DB
  [ ] Implementar fallbacks para Redis
  [ ] Implementar fallbacks para S3
  [ ] Tests unitarios para cada fallback
  [ ] Integration con circuit breakers

DÍA 3-5: Integrar con Degradation Manager
  [ ] Conectar fallbacks con niveles de degradación
  [ ] Implementar fallback selection based on degradation level
  [ ] Documentation de estrategias de fallback
"""
