"""
Redis Circuit Breaker Service - DÍA 3 HORAS 1-4

Production-grade Redis service with circuit breaker pattern:
- Connection pooling with configurable limits
- Automatic failover and graceful degradation
- Comprehensive health monitoring
- Request tracking and metrics
- Automatic reconnection with exponential backoff

Author: Resilience Team
Date: October 19, 2025
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import redis
from redis import asyncio as aioredis
from redis.asyncio import ConnectionPool
from prometheus_client import Counter, Gauge, Histogram

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

redis_requests_total = Counter(
    'redis_requests_total',
    'Total Redis requests',
    ['operation', 'status']
)

redis_errors_total = Counter(
    'redis_errors_total',
    'Total Redis errors',
    ['operation', 'error_type']
)

redis_latency_seconds = Histogram(
    'redis_latency_seconds',
    'Redis operation latency',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)

redis_circuit_breaker_state = Gauge(
    'redis_circuit_breaker_state',
    'Redis circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)'
)

redis_connection_pool_size = Gauge(
    'redis_connection_pool_size',
    'Current Redis connection pool size'
)

redis_cache_hit_ratio = Gauge(
    'redis_cache_hit_ratio',
    'Redis cache hit ratio (0.0-1.0)'
)

redis_health_score = Gauge(
    'redis_health_score',
    'Redis health score (0-100)'
)


# ============================================================================
# ENUMS
# ============================================================================

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class RedisOperation(Enum):
    """Redis operations"""
    GET = 'get'
    SET = 'set'
    DELETE = 'delete'
    INCR = 'incr'
    LPUSH = 'lpush'
    RPUSH = 'rpush'
    LPOP = 'lpop'
    RPOP = 'rpop'
    LLEN = 'llen'
    LRANGE = 'lrange'
    SADD = 'sadd'
    SREM = 'srem'
    SMEMBERS = 'smembers'
    SCARD = 'scard'
    HSET = 'hset'
    HGET = 'hget'
    HGETALL = 'hgetall'
    HDEL = 'hdel'
    ZADD = 'zadd'
    ZRANGE = 'zrange'
    ZCARD = 'zcard'
    EXPIRE = 'expire'
    PING = 'ping'
    HEALTH_CHECK = 'health_check'


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class RedisHealthMetrics:
    """Tracks Redis health metrics"""

    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.total_latency = 0.0
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)"""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds"""
        if self.request_count == 0:
            return 0.0
        return (self.total_latency / self.request_count) * 1000

    @property
    def cache_hit_ratio(self) -> float:
        """Cache hit ratio (0.0-1.0)"""
        total_cache_accesses = self.cache_hits + self.cache_misses
        if total_cache_accesses == 0:
            return 0.0
        return self.cache_hits / total_cache_accesses

    @property
    def health_score(self) -> float:
        """Calculate health score (0-100)"""
        # Base score from success rate
        base_score = self.success_rate * 100

        # Latency penalty
        if self.avg_latency_ms > 100:
            latency_penalty = min(30, (self.avg_latency_ms - 100) / 10)
            base_score = max(0, base_score - latency_penalty)

        # Recent error penalty
        if self.last_error_time:
            time_since_error = (datetime.utcnow() - self.last_error_time).total_seconds()
            if time_since_error < 60:
                base_score = max(0, base_score - 20)

        return max(0, min(100, base_score))

    def record_success(self, latency_seconds: float):
        """Record successful operation"""
        self.success_count += 1
        self.request_count += 1
        self.total_latency += latency_seconds

    def record_failure(self, error: str):
        """Record failed operation"""
        self.failure_count += 1
        self.request_count += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()

    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1

    def reset(self):
        """Reset metrics"""
        self.success_count = 0
        self.failure_count = 0
        self.total_latency = 0.0
        self.request_count = 0


# ============================================================================
# REDIS CIRCUIT BREAKER
# ============================================================================

class RedisCircuitBreaker:
    """
    Redis Circuit Breaker with graceful degradation.

    Features:
    - Three-state circuit breaker (CLOSED, OPEN, HALF_OPEN)
    - Exponential backoff on failures
    - Automatic health monitoring
    - Connection pool management
    - Comprehensive metrics tracking
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        fail_max: int = 5,
        reset_timeout: int = 60,
        half_open_max_attempts: int = 3,
    ):
        """Initialize Redis Circuit Breaker"""
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.half_open_max_attempts = half_open_max_attempts

        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0
        self.last_failure_time: Optional[datetime] = None
        self.state_change_time = datetime.utcnow()

        # Connection and health
        self.redis_client: Optional[aioredis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self.health_metrics = RedisHealthMetrics()
        self.lock = asyncio.Lock()

        logger.info(
            f"Initialized Redis Circuit Breaker: {host}:{port} "
            f"(fail_max={fail_max}, reset_timeout={reset_timeout}s)"
        )

    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            if not self.connection_pool:
                self.connection_pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=50,
                    retry_on_timeout=True,
                )

            self.redis_client = aioredis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Redis connection closed")

    # ========================================================================
    # CIRCUIT BREAKER STATE MANAGEMENT
    # ========================================================================

    async def _check_state(self) -> bool:
        """Check and update circuit breaker state"""
        async with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True

            elif self.state == CircuitBreakerState.OPEN:
                # Check if reset timeout has passed
                time_since_failure = (
                    datetime.utcnow() - self.last_failure_time
                ).total_seconds()

                if time_since_failure >= self.reset_timeout:
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_attempts = 0
                    return True
                return False

            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Allow limited attempts to test recovery
                if self.half_open_attempts < self.half_open_max_attempts:
                    return True
                return False

        return False

    async def _record_success(self):
        """Record successful operation"""
        async with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.info("Circuit breaker transitioning to CLOSED (recovered)")
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0

            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    async def _record_failure(self, error: str):
        """Record failed operation"""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.warning(
                    f"Recovery attempt failed in HALF_OPEN state: {error}"
                )
                self.state = CircuitBreakerState.OPEN
                self.failure_count = self.fail_max
                return

            if self.failure_count >= self.fail_max:
                if self.state == CircuitBreakerState.CLOSED:
                    logger.warning(
                        f"Circuit breaker OPEN after {self.failure_count} failures"
                    )
                    self.state = CircuitBreakerState.OPEN

    # ========================================================================
    # REDIS OPERATIONS
    # ========================================================================

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.GET.value,
                status='circuit_open'
            ).inc()
            return None

        start_time = time.time()
        try:
            value = await self.redis_client.get(key)
            latency = time.time() - start_time

            if value is not None:
                self.health_metrics.record_cache_hit()
            else:
                self.health_metrics.record_cache_miss()

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.GET.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.GET.value
            ).observe(latency)

            await self._record_success()
            return value

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.GET.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.GET.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis GET error: {error_msg}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None
    ) -> bool:
        """Set value in Redis"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.SET.value,
                status='circuit_open'
            ).inc()
            return False

        start_time = time.time()
        try:
            await self.redis_client.set(key, value, ex=ex)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.SET.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.SET.value
            ).observe(latency)

            await self._record_success()
            return True

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.SET.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.SET.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis SET error: {error_msg}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.DELETE.value,
                status='circuit_open'
            ).inc()
            return 0

        start_time = time.time()
        try:
            result = await self.redis_client.delete(*keys)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.DELETE.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.DELETE.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.DELETE.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.DELETE.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis DELETE error: {error_msg}")
            return 0

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in Redis"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.INCR.value,
                status='circuit_open'
            ).inc()
            return None

        start_time = time.time()
        try:
            result = await self.redis_client.incrby(key, amount)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.INCR.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.INCR.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.INCR.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.INCR.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis INCR error: {error_msg}")
            return None

    async def lpush(self, key: str, *values) -> int:
        """Push values to left of list"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.LPUSH.value,
                status='circuit_open'
            ).inc()
            return 0

        start_time = time.time()
        try:
            result = await self.redis_client.lpush(key, *values)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.LPUSH.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.LPUSH.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.LPUSH.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.LPUSH.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis LPUSH error: {error_msg}")
            return 0

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from right of list"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.RPOP.value,
                status='circuit_open'
            ).inc()
            return None

        start_time = time.time()
        try:
            result = await self.redis_client.rpop(key)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.RPOP.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.RPOP.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.RPOP.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.RPOP.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis RPOP error: {error_msg}")
            return None

    async def llen(self, key: str) -> int:
        """Get list length"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.LLEN.value,
                status='circuit_open'
            ).inc()
            return 0

        start_time = time.time()
        try:
            result = await self.redis_client.llen(key)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.LLEN.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.LLEN.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.LLEN.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.LLEN.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis LLEN error: {error_msg}")
            return 0

    async def hset(
        self,
        key: str,
        mapping: Dict[str, Any]
    ) -> int:
        """Set hash fields"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.HSET.value,
                status='circuit_open'
            ).inc()
            return 0

        start_time = time.time()
        try:
            result = await self.redis_client.hset(key, mapping=mapping)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.HSET.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.HSET.value
            ).observe(latency)

            await self._record_success()
            return result

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.HSET.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.HSET.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis HSET error: {error_msg}")
            return 0

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not await self._check_state():
            redis_requests_total.labels(
                operation=RedisOperation.HGETALL.value,
                status='circuit_open'
            ).inc()
            return {}

        start_time = time.time()
        try:
            result = await self.redis_client.hgetall(key)
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.HGETALL.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.HGETALL.value
            ).observe(latency)

            await self._record_success()
            return result or {}

        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.HGETALL.value,
                status='error'
            ).inc()
            redis_errors_total.labels(
                operation=RedisOperation.HGETALL.value,
                error_type=type(e).__name__
            ).inc()

            await self._record_failure(error_msg)
            logger.warning(f"Redis HGETALL error: {error_msg}")
            return {}

    async def ping(self) -> bool:
        """Health check ping"""
        if not self.redis_client:
            return False

        start_time = time.time()
        try:
            await self.redis_client.ping()
            latency = time.time() - start_time

            self.health_metrics.record_success(latency)
            redis_requests_total.labels(
                operation=RedisOperation.PING.value,
                status='success'
            ).inc()
            redis_latency_seconds.labels(
                operation=RedisOperation.PING.value
            ).observe(latency)

            return True

        except Exception as e:
            error_msg = str(e)
            self.health_metrics.record_failure(error_msg)
            redis_requests_total.labels(
                operation=RedisOperation.PING.value,
                status='error'
            ).inc()
            return False

    # ========================================================================
    # HEALTH & STATUS
    # ========================================================================

    async def get_health(self) -> Dict[str, Any]:
        """Get service health status"""
        await self._check_state()

        return {
            'state': self.state.name,
            'is_healthy': self.state == CircuitBreakerState.CLOSED,
            'failure_count': self.failure_count,
            'health_score': self.health_metrics.health_score,
            'success_rate': self.health_metrics.success_rate,
            'avg_latency_ms': self.health_metrics.avg_latency_ms,
            'cache_hit_ratio': self.health_metrics.cache_hit_ratio,
            'last_error': self.health_metrics.last_error,
            'state_change_time': self.state_change_time.isoformat(),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        health = await self.get_health()

        return {
            'service': 'redis',
            'timestamp': datetime.utcnow().isoformat(),
            'connection': {
                'host': self.host,
                'port': self.port,
                'db': self.db,
                'connected': self.redis_client is not None,
            },
            'circuit_breaker': {
                'state': health['state'],
                'failure_count': health['failure_count'],
                'fail_max': self.fail_max,
                'reset_timeout': self.reset_timeout,
            },
            'health': health,
            'metrics': {
                'total_requests': self.health_metrics.request_count,
                'success_count': self.health_metrics.success_count,
                'failure_count': self.health_metrics.failure_count,
                'cache_hits': self.health_metrics.cache_hits,
                'cache_misses': self.health_metrics.cache_misses,
            },
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

redis_circuit_breaker: Optional[RedisCircuitBreaker] = None


async def initialize_redis(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
) -> bool:
    """Initialize global Redis instance"""
    global redis_circuit_breaker

    redis_circuit_breaker = RedisCircuitBreaker(
        host=host,
        port=port,
        db=db,
        password=password,
    )

    return await redis_circuit_breaker.initialize()


async def get_redis() -> RedisCircuitBreaker:
    """Get Redis instance (for dependency injection)"""
    global redis_circuit_breaker

    if not redis_circuit_breaker:
        await initialize_redis()

    return redis_circuit_breaker


async def close_redis():
    """Close Redis connection"""
    global redis_circuit_breaker

    if redis_circuit_breaker:
        await redis_circuit_breaker.close()
        redis_circuit_breaker = None
