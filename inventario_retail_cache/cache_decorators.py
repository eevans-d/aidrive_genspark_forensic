"""
Cache Decorators para Sistema Inventario Retail Argentino
=========================================================

Decoradores inteligentes para cachear endpoints críticos con configuración
automática de TTL y invalidación basada en eventos del sistema.

Optimizado para:
- Productos y stock (invalida cuando cambia inventario)
- Resultados OCR (cache 24h facturas procesadas)
- Predicciones ML (cache 1h, invalida cuando cambian datos)
- Consultas frecuentes (cache dinámico)
"""

import functools
import inspect
import hashlib
import json
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime
import logging

# Import cache manager
from .intelligent_cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

def cache_key_generator(func: Callable, *args, **kwargs) -> str:
    """
    Genera key única para función y argumentos

    Args:
        func: Función a cachear
        args: Argumentos posicionales
        kwargs: Argumentos nombrados

    Returns:
        Key única para cache
    """
    # Crear signature de la función
    func_name = f"{func.__module__}.{func.__name__}"

    # Serializar argumentos de manera determinística
    args_str = json.dumps(args, sort_keys=True, default=str)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)

    # Crear hash de la combinación
    content = f"{func_name}:{args_str}:{kwargs_str}"
    return hashlib.md5(content.encode()).hexdigest()


def cache_product(ttl: Optional[int] = None, invalidate_on_update: bool = True):
    """
    Decorador para cachear funciones relacionadas a productos

    Args:
        ttl: Tiempo de vida en segundos (None = TTL dinámico)
        invalidate_on_update: Si invalidar cache cuando producto se actualiza
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # Generar key de cache
            cache_key = cache_key_generator(func, *args, **kwargs)

            # Intentar obtener del cache
            cached_result = cache_manager.get('product', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT producto: {func.__name__}")
                return cached_result

            # Ejecutar función original
            try:
                result = func(*args, **kwargs)

                # Cachear resultado
                cache_manager.set('product', cache_key, result, ttl=ttl)
                logger.debug(f"💾 Cache SET producto: {func.__name__}")

                return result

            except Exception as e:
                logger.error(f"Error en función cacheada {func.__name__}: {e}")
                raise

        # Metadata para invalidación
        wrapper._cache_type = 'product'
        wrapper._invalidate_on_update = invalidate_on_update
        return wrapper

    return decorator


def cache_stock(ttl: Optional[int] = 600, auto_invalidate: bool = True):
    """
    Decorador para cachear consultas de stock
    TTL corto por defecto (10 min) porque stock cambia frecuentemente

    Args:
        ttl: Tiempo de vida en segundos 
        auto_invalidate: Si invalidar automáticamente en cambios stock
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Intentar cache
            cached_result = cache_manager.get('stock', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT stock: {func.__name__}")
                return cached_result

            # Ejecutar y cachear
            try:
                result = func(*args, **kwargs)
                cache_manager.set('stock', cache_key, result, ttl=ttl)
                logger.debug(f"💾 Cache SET stock: {func.__name__}")
                return result

            except Exception as e:
                logger.error(f"Error en función stock cacheada {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'stock'
        wrapper._auto_invalidate = auto_invalidate
        return wrapper

    return decorator


def cache_ocr_result(ttl: int = 86400):
    """
    Decorador para cachear resultados OCR
    TTL largo (24h) porque facturas no cambian una vez procesadas

    Args:
        ttl: Tiempo de vida en segundos (default: 24h)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Verificar cache
            cached_result = cache_manager.get('ocr', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT OCR: {func.__name__}")
                return cached_result

            # Procesar OCR y cachear
            try:
                result = func(*args, **kwargs)

                # Solo cachear si OCR fue exitoso
                if result and result.get('success', False):
                    cache_manager.set('ocr', cache_key, result, ttl=ttl)
                    logger.debug(f"💾 Cache SET OCR exitoso: {func.__name__}")

                return result

            except Exception as e:
                logger.error(f"Error en OCR cacheado {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'ocr'
        return wrapper

    return decorator


def cache_ml_prediction(ttl: int = 3600, invalidate_on_retrain: bool = True):
    """
    Decorador para cachear predicciones ML
    TTL medio (1h) balance entre performance y frescura

    Args:
        ttl: Tiempo de vida en segundos (default: 1h)
        invalidate_on_retrain: Si invalidar cuando modelo se re-entrena
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Verificar cache
            cached_result = cache_manager.get('ml', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT ML: {func.__name__}")
                return cached_result

            # Ejecutar predicción y cachear
            try:
                result = func(*args, **kwargs)

                # Cachear resultado con metadata
                cache_data = {
                    'prediction': result,
                    'timestamp': datetime.now().isoformat(),
                    'model_version': getattr(func, '_model_version', '1.0')
                }

                cache_manager.set('ml', cache_key, cache_data, ttl=ttl)
                logger.debug(f"💾 Cache SET ML: {func.__name__}")

                return result

            except Exception as e:
                logger.error(f"Error en ML cacheado {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'ml'
        wrapper._invalidate_on_retrain = invalidate_on_retrain
        return wrapper

    return decorator


def cache_price_calculation(ttl: int = 1800):
    """
    Decorador para cachear cálculos de pricing
    TTL corto (30 min) por inflación argentina

    Args:
        ttl: Tiempo de vida en segundos (default: 30 min)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Verificar cache
            cached_result = cache_manager.get('price', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT pricing: {func.__name__}")
                return cached_result

            # Calcular precio y cachear
            try:
                result = func(*args, **kwargs)

                # Agregar timestamp para tracking inflación
                cache_data = {
                    'price_data': result,
                    'calculated_at': datetime.now().isoformat(),
                    'inflation_rate': 4.5  # Argentina context
                }

                cache_manager.set('price', cache_key, cache_data, ttl=ttl)
                logger.debug(f"💾 Cache SET pricing: {func.__name__}")

                return result

            except Exception as e:
                logger.error(f"Error en pricing cacheado {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'price'
        return wrapper

    return decorator


def cache_frequent_query(ttl: int = 300, track_frequency: bool = True):
    """
    Decorador para cachear queries frecuentes del sistema
    TTL corto (5 min) pero se ajusta dinámicamente por frecuencia

    Args:
        ttl: Tiempo de vida base en segundos
        track_frequency: Si trackear frecuencia para TTL dinámico
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Verificar cache
            cached_result = cache_manager.get('query', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT query: {func.__name__}")
                return cached_result

            # Ejecutar query y cachear
            try:
                result = func(*args, **kwargs)

                # TTL dinámico si está habilitado
                final_ttl = ttl
                if track_frequency:
                    # Cache manager calculará TTL basado en frecuencia
                    final_ttl = None

                cache_manager.set('query', cache_key, result, ttl=final_ttl)
                logger.debug(f"💾 Cache SET query: {func.__name__}")

                return result

            except Exception as e:
                logger.error(f"Error en query cacheada {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'query'
        wrapper._track_frequency = track_frequency
        return wrapper

    return decorator


def cache_report(ttl: int = 7200, include_generation_time: bool = True):
    """
    Decorador para cachear reportes generados
    TTL largo (2h) porque reportes son costosos de generar

    Args:
        ttl: Tiempo de vida en segundos (default: 2h)
        include_generation_time: Si incluir tiempo de generación
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            cache_key = cache_key_generator(func, *args, **kwargs)

            # Verificar cache
            cached_result = cache_manager.get('report', cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT report: {func.__name__}")
                return cached_result

            # Generar reporte y cachear
            try:
                start_time = datetime.now()
                result = func(*args, **kwargs)
                generation_time = (datetime.now() - start_time).total_seconds()

                # Metadata del reporte
                cache_data = {
                    'report_data': result,
                    'generated_at': start_time.isoformat(),
                    'generation_time_seconds': generation_time if include_generation_time else None
                }

                cache_manager.set('report', cache_key, cache_data, ttl=ttl)
                logger.debug(f"💾 Cache SET report: {func.__name__} (generado en {generation_time:.2f}s)")

                return result

            except Exception as e:
                logger.error(f"Error en reporte cacheado {func.__name__}: {e}")
                raise

        wrapper._cache_type = 'report'
        return wrapper

    return decorator


# === INVALIDATION HELPERS ===

def invalidate_product_cache(product_id: str):
    """
    Invalida todo el cache relacionado a un producto específico

    Args:
        product_id: ID del producto a invalidar
    """
    cache_manager = get_cache_manager()
    cache_manager.invalidate_product_cache(product_id)
    logger.info(f"🗑️ Cache producto {product_id} invalidado")


def invalidate_cache_by_type(cache_type: str, pattern: str = "*"):
    """
    Invalida cache por tipo

    Args:
        cache_type: Tipo de cache (product, stock, ocr, ml, etc.)
        pattern: Patrón adicional para filtrar
    """
    cache_manager = get_cache_manager()
    prefix = cache_manager.KEY_PREFIXES.get(cache_type, "cache:")
    full_pattern = f"{prefix}{pattern}"

    deleted = cache_manager.invalidate_pattern(full_pattern)
    logger.info(f"🗑️ Invalidado cache tipo {cache_type}: {deleted} keys")


def warm_cache_for_products(product_ids: List[str], get_product_func: Callable):
    """
    Pre-carga cache para productos frecuentes

    Args:
        product_ids: Lista de IDs de productos
        get_product_func: Función para obtener datos del producto
    """
    cache_manager = get_cache_manager()
    warmed = cache_manager.warm_frequent_products(product_ids, get_product_func)
    logger.info(f"🔥 Cache warming: {warmed} productos pre-cargados")


# === CACHE STATISTICS DECORATOR ===

def track_cache_stats(func: Callable) -> Callable:
    """
    Decorador para trackear estadísticas de uso de endpoints cacheados
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_manager = get_cache_manager()

        # Ejecutar función
        result = func(*args, **kwargs)

        # Trackear uso si la función tiene cache
        if hasattr(func, '_cache_type'):
            cache_type = func._cache_type
            logger.debug(f"📊 Endpoint cacheado usado: {func.__name__} (tipo: {cache_type})")

        return result

    return wrapper


# === CONTEXT MANAGER PARA BATCH OPERATIONS ===

class CacheBatchInvalidation:
    """
    Context manager para invalidar cache en batch al final de operaciones
    Útil para operaciones que afectan múltiples productos/stock
    """

    def __init__(self):
        self.products_to_invalidate = set()
        self.patterns_to_invalidate = set()

    def add_product(self, product_id: str):
        """Agregar producto para invalidar"""
        self.products_to_invalidate.add(product_id)

    def add_pattern(self, pattern: str):
        """Agregar patrón para invalidar"""
        self.patterns_to_invalidate.add(pattern)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ejecutar invalidaciones batch al salir"""
        cache_manager = get_cache_manager()

        # Invalidar productos
        for product_id in self.products_to_invalidate:
            cache_manager.invalidate_product_cache(product_id)

        # Invalidar patrones
        for pattern in self.patterns_to_invalidate:
            cache_manager.invalidate_pattern(pattern)

        logger.info(f"🗑️ Batch invalidation: {len(self.products_to_invalidate)} productos, "
                   f"{len(self.patterns_to_invalidate)} patrones")


# === FUNCIONES DE UTILIDAD ===

def get_cache_status() -> Dict[str, Any]:
    """
    Obtiene status completo del sistema de cache

    Returns:
        Diccionario con estadísticas y configuración
    """
    cache_manager = get_cache_manager()
    return cache_manager.get_stats()


def reset_all_cache_stats():
    """Resetea todas las estadísticas de cache"""
    cache_manager = get_cache_manager()
    cache_manager.reset_stats()
    logger.info("📊 Todas las estadísticas de cache reseteadas")


def cleanup_expired_cache() -> int:
    """
    Fuerza limpieza de keys expiradas

    Returns:
        Número de keys limpiadas
    """
    cache_manager = get_cache_manager()
    cleaned = cache_manager.cleanup_expired_keys()
    logger.info(f"🧹 Limpieza forzada: {cleaned} keys expiradas eliminadas")
    return cleaned
