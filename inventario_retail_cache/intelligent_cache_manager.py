"""
Redis Cache Manager Inteligente para Sistema Inventario Retail Argentino
=========================================================================

Manager central para cache con TTL dinámico, invalidación automática
y optimizaciones específicas para productos, OCR y predicciones ML.

Features:
- TTL dinámico basado en frecuencia de acceso
- Invalidación automática por eventos
- Cache warming para productos frecuentes
- Estadísticas de performance
- Fallback automático si Redis falla
"""

import redis
import json
import time
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from functools import wraps
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Estadísticas del cache para monitoring"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    @property
    def hit_rate(self) -> float:
        """Calcula hit rate porcentual"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def reset(self):
        """Resetea todas las estadísticas"""
        self.hits = 0
        self.misses = 0  
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_requests = 0
        self.last_reset = datetime.now()


class IntelligentCacheManager:
    """
    Cache Manager inteligente con TTL dinámico y invalidación automática
    Optimizado para sistema de inventario retail argentino
    """

    # TTL predefinidos por tipo de dato (en segundos)
    DEFAULT_TTLS = {
        'product': 3600,        # Productos: 1 hora
        'stock': 600,           # Stock: 10 minutos (cambia frecuentemente)
        'ocr_result': 86400,    # OCR: 24 horas (facturas no cambian)
        'ml_prediction': 3600,  # ML: 1 hora (recalcula periódicamente)
        'price': 1800,          # Precios: 30 minutos (inflación argentina)
        'report': 7200,         # Reportes: 2 horas
        'user_session': 1800,   # Sesiones: 30 minutos
        'frequent_query': 300,  # Queries frecuentes: 5 minutos
    }

    # Prefijos para organizar keys por categorías
    KEY_PREFIXES = {
        'product': 'prod:',
        'stock': 'stock:',
        'ocr': 'ocr:',
        'ml': 'ml:',
        'price': 'price:',
        'report': 'report:',
        'query': 'query:',
        'stats': 'stats:',
        'freq': 'freq:',        # Frecuencia de acceso
        'warm': 'warm:',        # Cache warming
    }

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, 
                 redis_db: int = 0, redis_password: Optional[str] = None):
        """
        Inicializa el cache manager

        Args:
            redis_host: Host Redis
            redis_port: Puerto Redis
            redis_db: Database Redis
            redis_password: Password Redis (opcional)
        """
        self.redis_client = None
        self.stats = CacheStats()
        self._connect_redis(redis_host, redis_port, redis_db, redis_password)

        # Cargar estadísticas previas si existen
        self._load_stats()

        logger.info(f"Redis Cache Manager iniciado - Host: {redis_host}:{redis_port}")

    def _connect_redis(self, host: str, port: int, db: int, password: Optional[str]):
        """Conecta a Redis con retry automático"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Test conexión
            self.redis_client.ping()
            logger.info("✅ Conexión Redis establecida exitosamente")

        except Exception as e:
            logger.error(f"❌ Error conectando Redis: {e}")
            self.redis_client = None

    def _is_redis_available(self) -> bool:
        """Verifica si Redis está disponible"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            logger.warning("Redis no disponible - usando fallback")
            return False

    def _generate_key(self, key_type: str, identifier: str, extra: str = "") -> str:
        """
        Genera key estandarizada para Redis

        Args:
            key_type: Tipo de key (product, stock, ocr, etc.)
            identifier: Identificador único
            extra: Información adicional opcional

        Returns:
            Key formateada para Redis
        """
        prefix = self.KEY_PREFIXES.get(key_type, "cache:")
        if extra:
            return f"{prefix}{identifier}:{extra}"
        return f"{prefix}{identifier}"

    def _serialize_value(self, value: Any) -> str:
        """Serializa valor para almacenar en Redis"""
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error serializando valor: {e}")
            return json.dumps(str(value))

    def _deserialize_value(self, value: str) -> Any:
        """Deserializa valor de Redis"""
        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"Error deserializando valor: {e}")
            return value

    def _calculate_dynamic_ttl(self, key_type: str, identifier: str) -> int:
        """
        Calcula TTL dinámico basado en frecuencia de acceso

        Args:
            key_type: Tipo de cache
            identifier: Identificador del item

        Returns:
            TTL en segundos optimizado
        """
        base_ttl = self.DEFAULT_TTLS.get(key_type, 3600)

        if not self._is_redis_available():
            return base_ttl

        try:
            # Contar accesos en la última hora
            freq_key = self._generate_key('freq', f"{key_type}:{identifier}")
            access_count = self.redis_client.get(freq_key) or 0
            access_count = int(access_count)

            # TTL dinámico basado en frecuencia
            if access_count > 50:  # Muy frecuente
                return base_ttl * 2
            elif access_count > 20:  # Frecuente
                return int(base_ttl * 1.5)
            elif access_count < 5:  # Poco frecuente
                return int(base_ttl * 0.5)

            return base_ttl

        except Exception as e:
            logger.error(f"Error calculando TTL dinámico: {e}")
            return base_ttl

    def _update_access_frequency(self, key_type: str, identifier: str):
        """Actualiza contador de frecuencia de acceso"""
        if not self._is_redis_available():
            return

        try:
            freq_key = self._generate_key('freq', f"{key_type}:{identifier}")
            pipeline = self.redis_client.pipeline()
            pipeline.incr(freq_key)
            pipeline.expire(freq_key, 3600)  # Resetea cada hora
            pipeline.execute()
        except Exception as e:
            logger.error(f"Error actualizando frecuencia: {e}")

    def set(self, key_type: str, identifier: str, value: Any, 
            ttl: Optional[int] = None, extra: str = "") -> bool:
        """
        Almacena valor en cache con TTL inteligente

        Args:
            key_type: Tipo de cache (product, stock, ocr, ml, etc.)
            identifier: Identificador único
            value: Valor a cachear
            ttl: TTL personalizado (opcional)
            extra: Información extra para la key

        Returns:
            True si se almacenó exitosamente
        """
        self.stats.total_requests += 1

        if not self._is_redis_available():
            self.stats.errors += 1
            return False

        try:
            cache_key = self._generate_key(key_type, identifier, extra)
            serialized_value = self._serialize_value(value)

            # TTL dinámico si no se especifica
            if ttl is None:
                ttl = self._calculate_dynamic_ttl(key_type, identifier)

            # Almacenar en Redis
            success = self.redis_client.setex(cache_key, ttl, serialized_value)

            if success:
                self.stats.sets += 1
                logger.debug(f"✅ Cache SET: {cache_key} (TTL: {ttl}s)")
                return True
            else:
                self.stats.errors += 1
                return False

        except Exception as e:
            logger.error(f"Error en cache SET: {e}")
            self.stats.errors += 1
            return False

    def get(self, key_type: str, identifier: str, extra: str = "") -> Optional[Any]:
        """
        Obtiene valor del cache y actualiza estadísticas

        Args:
            key_type: Tipo de cache
            identifier: Identificador único
            extra: Información extra para la key

        Returns:
            Valor del cache o None si no existe
        """
        self.stats.total_requests += 1

        if not self._is_redis_available():
            self.stats.misses += 1
            self.stats.errors += 1
            return None

        try:
            cache_key = self._generate_key(key_type, identifier, extra)
            cached_value = self.redis_client.get(cache_key)

            if cached_value is not None:
                # Cache HIT
                self.stats.hits += 1
                self._update_access_frequency(key_type, identifier)
                logger.debug(f"✅ Cache HIT: {cache_key}")
                return self._deserialize_value(cached_value)
            else:
                # Cache MISS
                self.stats.misses += 1
                logger.debug(f"❌ Cache MISS: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Error en cache GET: {e}")
            self.stats.misses += 1
            self.stats.errors += 1
            return None

    def delete(self, key_type: str, identifier: str, extra: str = "") -> bool:
        """
        Elimina valor del cache

        Args:
            key_type: Tipo de cache
            identifier: Identificador único
            extra: Información extra para la key

        Returns:
            True si se eliminó exitosamente
        """
        if not self._is_redis_available():
            return False

        try:
            cache_key = self._generate_key(key_type, identifier, extra)
            deleted = self.redis_client.delete(cache_key)

            if deleted:
                self.stats.deletes += 1
                logger.debug(f"🗑️ Cache DELETE: {cache_key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error en cache DELETE: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida múltiples keys por patrón

        Args:
            pattern: Patrón de keys a eliminar (ej: "prod:*", "stock:123:*")

        Returns:
            Número de keys eliminadas
        """
        if not self._is_redis_available():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                logger.info(f"🗑️ Invalidados {deleted} keys con patrón: {pattern}")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Error invalidando patrón {pattern}: {e}")
            return 0

    def invalidate_product_cache(self, product_id: str):
        """Invalida todo el cache relacionado a un producto"""
        patterns = [
            f"prod:{product_id}*",
            f"stock:{product_id}*", 
            f"price:{product_id}*",
            f"ml:*{product_id}*"
        ]

        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)

        logger.info(f"🗑️ Invalidado cache completo producto {product_id}: {total_deleted} keys")

    def warm_frequent_products(self, product_ids: List[str], 
                             get_product_func: callable) -> int:
        """
        Pre-carga productos frecuentes en cache

        Args:
            product_ids: Lista de IDs de productos frecuentes
            get_product_func: Función para obtener datos del producto

        Returns:
            Número de productos pre-cargados
        """
        if not self._is_redis_available():
            return 0

        warmed = 0
        for product_id in product_ids:
            try:
                # Verificar si ya está en cache
                if self.get('product', product_id) is None:
                    # Obtener del source y cachear
                    product_data = get_product_func(product_id)
                    if product_data:
                        self.set('product', product_id, product_data, ttl=7200)  # 2 horas
                        warmed += 1

            except Exception as e:
                logger.error(f"Error warming producto {product_id}: {e}")

        logger.info(f"🔥 Cache warming completado: {warmed} productos")
        return warmed

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del cache

        Returns:
            Diccionario con estadísticas detalladas
        """
        redis_info = {}
        if self._is_redis_available():
            try:
                info = self.redis_client.info()
                redis_info = {
                    'redis_version': info.get('redis_version'),
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception as e:
                logger.error(f"Error obteniendo info Redis: {e}")

        return {
            'cache_stats': {
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'hit_rate': round(self.stats.hit_rate, 2),
                'sets': self.stats.sets,
                'deletes': self.stats.deletes,
                'errors': self.stats.errors,
                'total_requests': self.stats.total_requests,
                'last_reset': self.stats.last_reset.isoformat()
            },
            'redis_info': redis_info,
            'ttl_config': self.DEFAULT_TTLS
        }

    def _save_stats(self):
        """Guarda estadísticas en Redis para persistencia"""
        if self._is_redis_available():
            try:
                stats_key = self._generate_key('stats', 'manager')
                stats_data = {
                    'hits': self.stats.hits,
                    'misses': self.stats.misses,
                    'sets': self.stats.sets,
                    'deletes': self.stats.deletes,
                    'errors': self.stats.errors,
                    'total_requests': self.stats.total_requests,
                    'last_reset': self.stats.last_reset.isoformat()
                }
                self.redis_client.setex(stats_key, 86400, json.dumps(stats_data))
            except Exception as e:
                logger.error(f"Error guardando estadísticas: {e}")

    def _load_stats(self):
        """Carga estadísticas previas de Redis"""
        if self._is_redis_available():
            try:
                stats_key = self._generate_key('stats', 'manager')
                cached_stats = self.redis_client.get(stats_key)
                if cached_stats:
                    stats_data = json.loads(cached_stats)
                    self.stats.hits = stats_data.get('hits', 0)
                    self.stats.misses = stats_data.get('misses', 0)
                    self.stats.sets = stats_data.get('sets', 0)
                    self.stats.deletes = stats_data.get('deletes', 0)
                    self.stats.errors = stats_data.get('errors', 0)
                    self.stats.total_requests = stats_data.get('total_requests', 0)
                    logger.info("📊 Estadísticas cache restauradas")
            except Exception as e:
                logger.error(f"Error cargando estadísticas: {e}")

    def reset_stats(self):
        """Resetea todas las estadísticas"""
        self.stats.reset()
        self._save_stats()
        logger.info("📊 Estadísticas cache reseteadas")

    def cleanup_expired_keys(self) -> int:
        """
        Limpia keys expiradas manualmente (útil para debugging)

        Returns:
            Número de keys limpiadas
        """
        if not self._is_redis_available():
            return 0

        try:
            # Redis limpia automáticamente, pero podemos forzar
            cleaned = 0
            all_keys = self.redis_client.keys("*")

            for key in all_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key expirada
                    self.redis_client.delete(key)
                    cleaned += 1

            logger.info(f"🧹 Limpieza manual: {cleaned} keys expiradas eliminadas")
            return cleaned

        except Exception as e:
            logger.error(f"Error en limpieza manual: {e}")
            return 0

    def __del__(self):
        """Destructor - guarda estadísticas al cerrar"""
        try:
            self._save_stats()
        except:
            pass


# Instancia global del cache manager
cache_manager = IntelligentCacheManager()

def get_cache_manager() -> IntelligentCacheManager:
    """
    Obtiene instancia global del cache manager

    Returns:
        Instancia del cache manager
    """
    return cache_manager
