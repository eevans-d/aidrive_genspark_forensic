"""
Cliente Redis optimizado para sistema inventario retail argentino
Manejo de cache inteligente con TTL y contexto local
"""

import redis
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
from functools import wraps

logger = logging.getLogger(__name__)

class ArgentinaRedisClient:
    """Cliente Redis optimizado para contexto argentino"""

    def __init__(
        self, 
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20
    ):
        """Inicializar cliente Redis con pool de conexiones"""

        self.pool = redis.ConnectionPool(
            host=host,
            port=port, 
            db=db,
            password=password,
            max_connections=max_connections,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        self.client = redis.Redis(connection_pool=self.pool)

        # Configuración específica Argentina
        self.currency = "ARS"
        self.timezone = "America/Argentina/Buenos_Aires"

        # TTL por defecto por tipo de datos
        self.default_ttl = {
            'precio': 3600 * 4,      # 4 horas (inflación)
            'ocr': 3600 * 24,        # 24 horas (facturas)
            'stock': 300,            # 5 minutos (alta rotación)
            'session': 3600 * 8,     # 8 horas (sesiones usuario)
            'ml_prediction': 1800,   # 30 minutos (predicciones)
            'dashboard': 300,        # 5 minutos (métricas)
        }

        # Prefijos para organización
        self.prefixes = {
            'precio': 'ar:precio:',
            'ocr': 'ar:ocr:',
            'stock': 'ar:stock:',
            'session': 'ar:session:',
            'ml': 'ar:ml:',
            'dash': 'ar:dash:',
        }

        self._test_connection()

    def _test_connection(self):
        """Verificar conexión Redis"""
        try:
            self.client.ping()
            logger.info("✅ Redis conectado correctamente")
        except redis.ConnectionError as e:
            logger.error(f"❌ Error conexión Redis: {e}")
            raise

    def _make_key(self, prefix_type: str, key: str) -> str:
        """Generar key con prefijo organizado"""
        prefix = self.prefixes.get(prefix_type, 'ar:general:')
        return f"{prefix}{key}"

    def _serialize_data(self, data: Any) -> str:
        """Serializar datos con metadata argentina"""
        payload = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'currency': self.currency,
            'version': 1
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    def _deserialize_data(self, serialized: str) -> Any:
        """Deserializar datos con validación"""
        try:
            payload = json.loads(serialized)
            return payload.get('data')
        except (json.JSONDecodeError, KeyError):
            return None

    # === CACHE PRECIOS CON INFLACIÓN ===

    def cache_precio(
        self, 
        producto_id: int, 
        precio_base: float, 
        precio_inflacion: float,
        ttl: Optional[int] = None
    ):
        """Cache precio con inflación aplicada"""
        key = self._make_key('precio', str(producto_id))

        data = {
            'producto_id': producto_id,
            'precio_base': precio_base,
            'precio_inflacion': precio_inflacion,
            'factor_inflacion': precio_inflacion / precio_base if precio_base > 0 else 1,
            'fecha_calculo': datetime.now().isoformat()
        }

        ttl = ttl or self.default_ttl['precio']
        serialized = self._serialize_data(data)

        self.client.setex(key, ttl, serialized)
        logger.debug(f"💰 Precio cacheado: {producto_id} = ${precio_inflacion}")

    def get_precio_cache(self, producto_id: int) -> Optional[Dict]:
        """Obtener precio desde cache"""
        key = self._make_key('precio', str(producto_id))
        cached = self.client.get(key)

        if cached:
            data = self._deserialize_data(cached.decode('utf-8'))
            logger.debug(f"💰 Precio desde cache: {producto_id}")
            return data

        return None

    # === CACHE OCR FACTURAS ===

    def cache_ocr_result(
        self, 
        file_hash: str, 
        ocr_data: Dict,
        ttl: Optional[int] = None
    ):
        """Cache resultado OCR por hash de archivo"""
        key = self._make_key('ocr', file_hash)
        ttl = ttl or self.default_ttl['ocr']

        data = {
            'file_hash': file_hash,
            'ocr_result': ocr_data,
            'processed_at': datetime.now().isoformat()
        }

        serialized = self._serialize_data(data)
        self.client.setex(key, ttl, serialized)
        logger.debug(f"📄 OCR cacheado: {file_hash[:8]}...")

    def get_ocr_cache(self, file_hash: str) -> Optional[Dict]:
        """Obtener resultado OCR desde cache"""
        key = self._make_key('ocr', file_hash)
        cached = self.client.get(key)

        if cached:
            data = self._deserialize_data(cached.decode('utf-8'))
            logger.debug(f"📄 OCR desde cache: {file_hash[:8]}...")
            return data.get('ocr_result')

        return None

    # === CACHE STOCK ===

    def cache_stock_info(
        self, 
        producto_id: int, 
        stock_actual: int,
        stock_minimo: int,
        critico: bool = None
    ):
        """Cache información de stock"""
        key = self._make_key('stock', str(producto_id))

        data = {
            'producto_id': producto_id,
            'stock_actual': stock_actual,
            'stock_minimo': stock_minimo,
            'critico': critico if critico is not None else (stock_actual <= stock_minimo),
            'updated_at': datetime.now().isoformat()
        }

        ttl = self.default_ttl['stock']
        serialized = self._serialize_data(data)
        self.client.setex(key, ttl, serialized)

    def get_stock_cache(self, producto_id: int) -> Optional[Dict]:
        """Obtener stock desde cache"""
        key = self._make_key('stock', str(producto_id))
        cached = self.client.get(key)

        if cached:
            return self._deserialize_data(cached.decode('utf-8'))

        return None

    # === CACHE PREDICCIONES ML ===

    def cache_ml_prediction(
        self,
        model_key: str,
        input_params: Dict,
        prediction_result: Dict,
        ttl: Optional[int] = None
    ):
        """Cache predicción ML con parámetros"""
        # Generar hash de parámetros para key única
        params_hash = hashlib.md5(
            json.dumps(input_params, sort_keys=True).encode()
        ).hexdigest()[:8]

        key = self._make_key('ml', f"{model_key}:{params_hash}")
        ttl = ttl or self.default_ttl['ml_prediction']

        data = {
            'model_key': model_key,
            'input_params': input_params,
            'prediction': prediction_result,
            'cached_at': datetime.now().isoformat()
        }

        serialized = self._serialize_data(data)
        self.client.setex(key, ttl, serialized)
        logger.debug(f"🤖 ML prediction cacheada: {model_key}")

    def get_ml_prediction_cache(
        self, 
        model_key: str, 
        input_params: Dict
    ) -> Optional[Dict]:
        """Obtener predicción ML desde cache"""
        params_hash = hashlib.md5(
            json.dumps(input_params, sort_keys=True).encode()
        ).hexdigest()[:8]

        key = self._make_key('ml', f"{model_key}:{params_hash}")
        cached = self.client.get(key)

        if cached:
            data = self._deserialize_data(cached.decode('utf-8'))
            logger.debug(f"🤖 ML prediction desde cache: {model_key}")
            return data.get('prediction')

        return None

    # === CACHE DASHBOARD ===

    def cache_dashboard_metrics(self, metrics_data: Dict):
        """Cache métricas de dashboard"""
        key = self._make_key('dash', 'metrics')
        ttl = self.default_ttl['dashboard']

        serialized = self._serialize_data(metrics_data)
        self.client.setex(key, ttl, serialized)

    def get_dashboard_cache(self) -> Optional[Dict]:
        """Obtener métricas dashboard desde cache"""
        key = self._make_key('dash', 'metrics')
        cached = self.client.get(key)

        if cached:
            return self._deserialize_data(cached.decode('utf-8'))

        return None

    # === UTILIDADES ===

    def invalidate_pattern(self, pattern: str):
        """Invalidar keys por patrón"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️ Invalidadas {len(keys)} keys: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidando pattern {pattern}: {e}")

    def invalidate_producto(self, producto_id: int):
        """Invalidar todo el cache de un producto"""
        patterns = [
            self._make_key('precio', f'{producto_id}*'),
            self._make_key('stock', f'{producto_id}*'),
            self._make_key('ml', f'*{producto_id}*')
        ]

        for pattern in patterns:
            self.invalidate_pattern(pattern)

    def get_cache_stats(self) -> Dict:
        """Obtener estadísticas de cache"""
        try:
            info = self.client.info()

            stats = {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
            }

            # Calcular hit ratio
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total = hits + misses

            if total > 0:
                stats['hit_ratio'] = round((hits / total) * 100, 2)
            else:
                stats['hit_ratio'] = 0

            # Contar keys por prefijo
            key_counts = {}
            for prefix_type, prefix in self.prefixes.items():
                pattern = f"{prefix}*"
                count = len(self.client.keys(pattern))
                key_counts[prefix_type] = count

            stats['keys_by_type'] = key_counts

            return stats

        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {}

    def health_check(self) -> Dict:
        """Health check completo de Redis"""
        try:
            start_time = datetime.now()

            # Test básico de conexión
            pong = self.client.ping()

            # Test write/read
            test_key = "health_check_test"
            test_value = datetime.now().isoformat()
            self.client.setex(test_key, 60, test_value)
            retrieved = self.client.get(test_key).decode('utf-8')
            self.client.delete(test_key)

            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            return {
                'status': 'healthy',
                'ping': pong,
                'write_read_test': retrieved == test_value,
                'latency_ms': round(latency_ms, 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# === DECORADORES PARA CACHE AUTOMÁTICO ===

def redis_cache(
    cache_type: str = 'general',
    ttl: int = 3600,
    key_func: Optional[callable] = None
):
    """Decorador para cache automático de funciones"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener cliente Redis desde contexto o crear uno nuevo
            try:
                redis_client = kwargs.pop('redis_client', ArgentinaRedisClient())
            except:
                # Si falla Redis, ejecutar función sin cache
                return func(*args, **kwargs)

            # Generar key de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Key por defecto basada en función y argumentos
                func_name = func.__name__
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                cache_key = f"{func_name}:{args_hash}"

            # Intentar obtener desde cache
            full_key = redis_client._make_key(cache_type, cache_key)
            cached_result = redis_client.client.get(full_key)

            if cached_result:
                logger.debug(f"Cache hit: {cache_key}")
                return redis_client._deserialize_data(cached_result.decode('utf-8'))

            # Ejecutar función y guardar en cache
            result = func(*args, **kwargs)

            try:
                serialized = redis_client._serialize_data(result)
                redis_client.client.setex(full_key, ttl, serialized)
                logger.debug(f"Cache miss → stored: {cache_key}")
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")

            return result

        return wrapper
    return decorator


# === INSTANCIA GLOBAL ===
_redis_client = None

def get_redis_client() -> ArgentinaRedisClient:
    """Obtener instancia global de Redis client"""
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = ArgentinaRedisClient()
        except Exception as e:
            logger.warning(f"Redis no disponible: {e}")
            raise

    return _redis_client


if __name__ == "__main__":
    # Test básico del cliente
    try:
        client = ArgentinaRedisClient()

        # Test health check
        health = client.health_check()
        print(f"Health Check: {health}")

        # Test cache precio
        client.cache_precio(1, 100.0, 104.5)
        precio = client.get_precio_cache(1)
        print(f"Precio cache: {precio}")

        # Test stats
        stats = client.get_cache_stats()
        print(f"Stats: {stats}")

        print("✅ Redis client funcionando correctamente")

    except Exception as e:
        print(f"❌ Error testing Redis: {e}")
