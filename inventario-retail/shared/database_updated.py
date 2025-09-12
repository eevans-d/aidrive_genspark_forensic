"""
Sistema de Gestión de Inventario - Módulo de Base de Datos
Archivo: shared/database.py

Descripción:
Módulo centralizado para la gestión de conexiones a base de datos con optimizaciones de performance,
pooling de conexiones, transacciones ACID y monitoreo de performance.

Características:
- Pool de conexiones optimizado con configuración dinámica
- Transacciones ACID con rollback automático
- Índices optimizados para consultas frecuentes
- Monitoreo y métricas de performance
- Logging detallado de queries y transacciones
- Retry logic para conexiones fallidas
- Connection health checks automáticos
- Query caching para consultas frecuentes
"""

import asyncio
import asyncpg
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
import os
from dataclasses import dataclass
from functools import wraps
import json
import hashlib

# Configuración de logging
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuración de base de datos con valores por defecto optimizados."""
    host: str = "localhost"
    port: int = 5432
    database: str = "inventario_system"
    user: str = "postgres"
    password: str = "postgres123"

    # Configuración de pool
    min_size: int = 5
    max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    command_timeout: float = 60.0

    # Configuración de retry
    max_retries: int = 3
    retry_delay: float = 1.0

    # Performance settings
    enable_query_cache: bool = True
    cache_ttl: int = 300  # 5 minutos
    slow_query_threshold: float = 1.0  # 1 segundo

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Crear configuración desde variables de entorno."""
        return cls(
            host=os.getenv('DB_HOST', cls.host),
            port=int(os.getenv('DB_PORT', cls.port)),
            database=os.getenv('DB_NAME', cls.database),
            user=os.getenv('DB_USER', cls.user),
            password=os.getenv('DB_PASSWORD', cls.password),
            min_size=int(os.getenv('DB_MIN_CONNECTIONS', cls.min_size)),
            max_size=int(os.getenv('DB_MAX_CONNECTIONS', cls.max_size)),
            command_timeout=float(os.getenv('DB_COMMAND_TIMEOUT', cls.command_timeout))
        )

@dataclass
class QueryMetrics:
    """Métricas de performance de queries."""
    query_hash: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    table_name: Optional[str] = None

class QueryCache:
    """Cache simple en memoria para queries frecuentes."""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl

    def _make_key(self, query: str, params: tuple) -> str:
        """Generar clave única para query y parámetros."""
        content = f"{query}:{str(params)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, query: str, params: tuple = ()) -> Optional[List[Any]]:
        """Obtener resultado desde cache si existe y no ha expirado."""
        key = self._make_key(query, params)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry['timestamp'] < timedelta(seconds=self.ttl):
                return entry['result']
            else:
                del self.cache[key]
        return None

    def set(self, query: str, params: tuple, result: List[Any]) -> None:
        """Guardar resultado en cache."""
        if len(self.cache) >= self.max_size:
            # Remover entrada más antigua
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]

        key = self._make_key(query, params)
        self.cache[key] = {
            'result': result,
            'timestamp': datetime.now()
        }

    def clear(self) -> None:
        """Limpiar todo el cache."""
        self.cache.clear()

class DatabaseManager:
    """
    Manager centralizado para conexiones de base de datos con optimizaciones avanzadas.
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
        self.query_metrics: List[QueryMetrics] = []
        self.cache = QueryCache() if config.enable_query_cache else None

        # Contadores de performance
        self.total_queries = 0
        self.slow_queries = 0
        self.failed_queries = 0

    async def connect(self) -> None:
        """Establecer conexión con pool optimizado."""
        if self.is_connected:
            return

        try:
            logger.info(f"🔌 Conectando a base de datos: {self.config.host}:{self.config.port}")

            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
                setup=self._setup_connection
            )

            self.is_connected = True
            logger.info(f"✅ Pool de conexiones creado: {self.config.min_size}-{self.config.max_size} conexiones")

            # Verificar conexión
            await self.health_check()

        except Exception as e:
            logger.error(f"❌ Error conectando a base de datos: {e}")
            raise

    async def _setup_connection(self, connection: asyncpg.Connection) -> None:
        """Configurar cada nueva conexión del pool."""
        # Configuraciones optimizadas para performance
        await connection.execute("SET default_transaction_isolation TO 'read committed'")
        await connection.execute("SET statement_timeout TO '60s'")
        await connection.execute("SET work_mem TO '256MB'")

    async def disconnect(self) -> None:
        """Cerrar pool de conexiones."""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("🔒 Pool de conexiones cerrado")

    async def health_check(self) -> bool:
        """Verificar salud de la conexión."""
        try:
            if not self.is_connected or not self.pool:
                return False

            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1

        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return False

    def _analyze_query(self, query: str) -> Dict[str, str]:
        """Analizar query para extraer metadatos."""
        query_upper = query.strip().upper()

        if query_upper.startswith('SELECT'):
            query_type = 'SELECT'
        elif query_upper.startswith('INSERT'):
            query_type = 'INSERT'
        elif query_upper.startswith('UPDATE'):
            query_type = 'UPDATE'
        elif query_upper.startswith('DELETE'):
            query_type = 'DELETE'
        else:
            query_type = 'OTHER'

        # Extraer nombre de tabla (simplificado)
        table_name = None
        words = query_upper.split()
        if 'FROM' in words:
            try:
                from_index = words.index('FROM')
                if from_index + 1 < len(words):
                    table_name = words[from_index + 1].strip('();,')
            except:
                pass
        elif query_type in ['INSERT', 'UPDATE', 'DELETE']:
            try:
                into_index = next((i for i, word in enumerate(words) if word in ['INTO', 'FROM']), -1)
                if into_index != -1 and into_index + 1 < len(words):
                    table_name = words[into_index + 1].strip('();,')
            except:
                pass

        return {
            'query_type': query_type,
            'table_name': table_name
        }

    def _record_metrics(self, query: str, execution_time: float, rows_affected: int = 0) -> None:
        """Registrar métricas de performance."""
        query_info = self._analyze_query(query)

        metrics = QueryMetrics(
            query_hash=hashlib.md5(query.encode()).hexdigest()[:12],
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            query_type=query_info['query_type'],
            table_name=query_info['table_name']
        )

        self.query_metrics.append(metrics)
        self.total_queries += 1

        if execution_time > self.config.slow_query_threshold:
            self.slow_queries += 1
            logger.warning(f"🐌 Query lenta detectada ({execution_time:.2f}s): {query[:100]}...")

        # Mantener solo las últimas 1000 métricas
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]

    async def execute_query(self, query: str, *params, use_cache: bool = True) -> List[asyncpg.Record]:
        """Ejecutar query con métricas y cache opcional."""
        start_time = time.time()

        try:
            # Verificar cache primero (solo para SELECT)
            if use_cache and self.cache and query.strip().upper().startswith('SELECT'):
                cached_result = self.cache.get(query, params)
                if cached_result is not None:
                    logger.debug(f"📋 Cache hit para query: {query[:50]}...")
                    return cached_result

            if not self.is_connected or not self.pool:
                await self.connect()

            async with self.pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)

                execution_time = time.time() - start_time
                self._record_metrics(query, execution_time, len(result))

                # Guardar en cache si aplica
                if (use_cache and self.cache and 
                    query.strip().upper().startswith('SELECT') and 
                    len(result) < 1000):  # No cachear resultados muy grandes
                    self.cache.set(query, params, result)

                logger.debug(f"✅ Query ejecutada en {execution_time:.3f}s: {len(result)} filas")
                return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_queries += 1
            logger.error(f"❌ Error ejecutando query ({execution_time:.3f}s): {e}")
            logger.error(f"Query: {query}")
            raise

    async def execute_command(self, query: str, *params) -> str:
        """Ejecutar comando que no retorna filas (INSERT, UPDATE, DELETE)."""
        start_time = time.time()

        try:
            if not self.is_connected or not self.pool:
                await self.connect()

            async with self.pool.acquire() as conn:
                if params:
                    result = await conn.execute(query, *params)
                else:
                    result = await conn.execute(query)

                execution_time = time.time() - start_time

                # Extraer número de filas afectadas del resultado
                rows_affected = 0
                if isinstance(result, str) and result.startswith(('INSERT', 'UPDATE', 'DELETE')):
                    try:
                        rows_affected = int(result.split()[-1])
                    except:
                        pass

                self._record_metrics(query, execution_time, rows_affected)

                logger.debug(f"✅ Comando ejecutado en {execution_time:.3f}s: {result}")
                return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_queries += 1
            logger.error(f"❌ Error ejecutando comando ({execution_time:.3f}s): {e}")
            logger.error(f"Query: {query}")
            raise

    async def fetchval(self, query: str, *params) -> Any:
        """Ejecutar query y retornar un solo valor."""
        start_time = time.time()

        try:
            if not self.is_connected or not self.pool:
                await self.connect()

            async with self.pool.acquire() as conn:
                if params:
                    result = await conn.fetchval(query, *params)
                else:
                    result = await conn.fetchval(query)

                execution_time = time.time() - start_time
                self._record_metrics(query, execution_time, 1 if result is not None else 0)

                logger.debug(f"✅ Fetchval ejecutado en {execution_time:.3f}s")
                return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_queries += 1
            logger.error(f"❌ Error en fetchval ({execution_time:.3f}s): {e}")
            raise

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Context manager para transacciones ACID."""
        if not self.is_connected or not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                start_time = time.time()
                logger.debug("🔄 Iniciando transacción")

                try:
                    yield conn
                    execution_time = time.time() - start_time
                    logger.debug(f"✅ Transacción completada en {execution_time:.3f}s")

                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"❌ Transacción falló en {execution_time:.3f}s: {e}")
                    logger.info("🔄 Ejecutando rollback automático")
                    raise

    async def execute_in_transaction(self, operations: List[tuple]) -> List[Any]:
        """
        Ejecutar múltiples operaciones en una sola transacción.

        Args:
            operations: Lista de tuplas (query, params)

        Returns:
            Lista de resultados
        """
        results = []

        async with self.transaction() as conn:
            for query, params in operations:
                if params:
                    if query.strip().upper().startswith('SELECT'):
                        result = await conn.fetch(query, *params)
                    else:
                        result = await conn.execute(query, *params)
                else:
                    if query.strip().upper().startswith('SELECT'):
                        result = await conn.fetch(query)
                    else:
                        result = await conn.execute(query)

                results.append(result)

        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de performance."""
        if not self.query_metrics:
            return {
                'total_queries': 0,
                'average_time': 0,
                'slow_queries': 0,
                'failed_queries': 0
            }

        avg_time = sum(m.execution_time for m in self.query_metrics) / len(self.query_metrics)

        # Estadísticas por tipo de query
        query_types = {}
        for metric in self.query_metrics:
            if metric.query_type not in query_types:
                query_types[metric.query_type] = {'count': 0, 'avg_time': 0, 'total_time': 0}

            query_types[metric.query_type]['count'] += 1
            query_types[metric.query_type]['total_time'] += metric.execution_time

        for qtype in query_types:
            query_types[qtype]['avg_time'] = (
                query_types[qtype]['total_time'] / query_types[qtype]['count']
            )

        return {
            'total_queries': self.total_queries,
            'average_time': round(avg_time, 3),
            'slow_queries': self.slow_queries,
            'failed_queries': self.failed_queries,
            'slow_query_percentage': round((self.slow_queries / self.total_queries) * 100, 2) if self.total_queries > 0 else 0,
            'query_types': query_types,
            'cache_enabled': self.cache is not None,
            'connection_pool_size': f"{self.config.min_size}-{self.config.max_size}",
            'is_connected': self.is_connected
        }

    def clear_cache(self) -> None:
        """Limpiar cache de queries."""
        if self.cache:
            self.cache.clear()
            logger.info("🧹 Cache de queries limpiado")

    async def optimize_tables(self, tables: List[str] = None) -> None:
        """Ejecutar optimizaciones en tablas específicas."""
        if not tables:
            tables = ['products', 'product_locations', 'stock_movements', 'locations']

        logger.info(f"⚡ Iniciando optimización de tablas: {tables}")

        async with self.pool.acquire() as conn:
            for table in tables:
                try:
                    # ANALYZE para actualizar estadísticas del planificador
                    await conn.execute(f"ANALYZE {table}")
                    logger.debug(f"✅ ANALYZE completado en tabla: {table}")

                except Exception as e:
                    logger.error(f"❌ Error optimizando tabla {table}: {e}")

        logger.info("⚡ Optimización de tablas completada")

# Instancia global del database manager
db_config = DatabaseConfig.from_env()
db_manager = DatabaseManager(db_config)

# Funciones de conveniencia para uso directo
async def init_database() -> None:
    """Inicializar conexión a base de datos."""
    await db_manager.connect()

async def close_database() -> None:
    """Cerrar conexión a base de datos."""
    await db_manager.disconnect()

async def execute_query(query: str, *params, use_cache: bool = True) -> List[asyncpg.Record]:
    """Ejecutar query con cache opcional."""
    return await db_manager.execute_query(query, *params, use_cache=use_cache)

async def execute_command(query: str, *params) -> str:
    """Ejecutar comando sin retorno."""
    return await db_manager.execute_command(query, *params)

async def fetchval(query: str, *params) -> Any:
    """Obtener un solo valor."""
    return await db_manager.fetchval(query, *params)

def get_transaction():
    """Obtener context manager para transacciones."""
    return db_manager.transaction()

async def get_performance_stats() -> Dict[str, Any]:
    """Obtener estadísticas de performance."""
    return db_manager.get_performance_stats()

def clear_query_cache() -> None:
    """Limpiar cache de queries."""
    db_manager.clear_cache()

# Decorador para retry automático
def with_db_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorador para retry automático en operaciones de BD."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} para {func.__name__}: {e}")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"❌ Falló después de {max_retries} intentos: {e}")

            raise last_exception
        return wrapper
    return decorator

# Context manager para manejo automático de conexiones
@asynccontextmanager
async def database_session():
    """Context manager para sesiones de base de datos con cleanup automático."""
    await init_database()
    try:
        yield db_manager
    finally:
        # No cerramos la conexión aquí para reutilizar el pool
        pass

# Funciones de utilidad para queries comunes
async def get_total_products() -> int:
    """Obtener total de productos activos."""
    return await fetchval("SELECT COUNT(*) FROM products WHERE is_active = TRUE")

async def get_low_stock_products(threshold: int = None) -> List[asyncpg.Record]:
    """Obtener productos con stock bajo."""
    if threshold is None:
        query = """
        SELECT p.id, p.sku, p.name, 
               COALESCE(SUM(pl.available_quantity), 0) as total_stock,
               p.reorder_point
        FROM products p
        LEFT JOIN product_locations pl ON p.id = pl.product_id
        WHERE p.is_active = TRUE
        GROUP BY p.id, p.sku, p.name, p.reorder_point
        HAVING COALESCE(SUM(pl.available_quantity), 0) <= p.reorder_point
        ORDER BY total_stock ASC
        """
        return await execute_query(query)
    else:
        query = """
        SELECT p.id, p.sku, p.name, 
               COALESCE(SUM(pl.available_quantity), 0) as total_stock
        FROM products p
        LEFT JOIN product_locations pl ON p.id = pl.product_id
        WHERE p.is_active = TRUE
        GROUP BY p.id, p.sku, p.name
        HAVING COALESCE(SUM(pl.available_quantity), 0) <= $1
        ORDER BY total_stock ASC
        """
        return await execute_query(query, threshold)

async def get_warehouse_capacity() -> List[asyncpg.Record]:
    """Obtener información de capacidad por depósito."""
    query = """
    SELECT w.id, w.name, w.code,
           COUNT(l.id) as total_locations,
           COUNT(CASE WHEN l.is_active THEN 1 END) as active_locations,
           COALESCE(SUM(l.capacity_units), 0) as total_capacity,
           COALESCE(SUM(CASE WHEN pl.id IS NOT NULL THEN pl.quantity ELSE 0 END), 0) as used_capacity
    FROM warehouses w
    LEFT JOIN locations l ON w.id = l.warehouse_id
    LEFT JOIN product_locations pl ON l.id = pl.location_id
    WHERE w.is_active = TRUE
    GROUP BY w.id, w.name, w.code
    ORDER BY w.name
    """
    return await execute_query(query)

if __name__ == "__main__":
    # Ejemplo de uso y testing
    async def test_database():
        """Función de testing para verificar funcionamiento."""
        try:
            await init_database()

            # Test básico de conexión
            result = await fetchval("SELECT 1 as test")
            print(f"✅ Test de conexión: {result}")

            # Test de health check
            health = await db_manager.health_check()
            print(f"✅ Health check: {health}")

            # Mostrar estadísticas
            stats = await get_performance_stats()
            print(f"📊 Estadísticas: {stats}")

        except Exception as e:
            print(f"❌ Error en testing: {e}")
        finally:
            await close_database()

    # Ejecutar test si se llama directamente
    import asyncio
    asyncio.run(test_database())
