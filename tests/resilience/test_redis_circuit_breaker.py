"""
Test Suite for Redis Circuit Breaker - DÍA 3 HORAS 1-4

Comprehensive tests for Redis service with circuit breaker pattern

Author: Resilience Team
Date: October 19, 2025
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from inventario_retail.shared.redis_service import (
    RedisCircuitBreaker,
    CircuitBreakerState,
    RedisHealthMetrics,
    RedisOperation,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def redis_metrics():
    """Fresh RedisHealthMetrics instance"""
    return RedisHealthMetrics()


@pytest.fixture
def redis_breaker():
    """Fresh RedisCircuitBreaker instance"""
    return RedisCircuitBreaker(
        host='localhost',
        port=6379,
        db=0,
        fail_max=3,
        reset_timeout=30,
        half_open_max_attempts=2,
    )


# ============================================================================
# REDIS HEALTH METRICS TESTS
# ============================================================================

class TestRedisHealthMetrics:
    """Test Redis health metrics tracking"""
    
    def test_initial_state(self, redis_metrics):
        """Verifica estado inicial de métricas"""
        assert redis_metrics.success_count == 0
        assert redis_metrics.failure_count == 0
        assert redis_metrics.request_count == 0
        assert redis_metrics.success_rate == 1.0  # No requests yet
        assert redis_metrics.health_score == 100.0
    
    def test_success_rate_calculation(self, redis_metrics):
        """Calcula correctamente el success rate"""
        redis_metrics.record_success(0.01)
        redis_metrics.record_success(0.01)
        redis_metrics.record_failure("error")
        
        assert redis_metrics.success_count == 2
        assert redis_metrics.failure_count == 1
        assert redis_metrics.request_count == 3
        assert abs(redis_metrics.success_rate - 2/3) < 0.01
    
    def test_latency_calculation(self, redis_metrics):
        """Calcula correctamente latencia promedio"""
        redis_metrics.record_success(0.010)
        redis_metrics.record_success(0.020)
        redis_metrics.record_success(0.030)
        
        avg_latency_ms = redis_metrics.avg_latency_ms
        assert 15 < avg_latency_ms < 25  # ~20ms
    
    def test_cache_hit_ratio(self, redis_metrics):
        """Calcula correctamente ratio de cache hits"""
        redis_metrics.record_cache_hit()
        redis_metrics.record_cache_hit()
        redis_metrics.record_cache_miss()
        
        assert redis_metrics.cache_hit_ratio == 2/3
    
    def test_health_score_perfect(self, redis_metrics):
        """Health score 100 en condiciones perfectas"""
        redis_metrics.record_success(0.001)
        redis_metrics.record_success(0.002)
        
        assert redis_metrics.health_score == 100.0
    
    def test_health_score_with_failures(self, redis_metrics):
        """Health score reduce con fallos"""
        for _ in range(5):
            redis_metrics.record_success(0.010)
        redis_metrics.record_failure("connection error")
        
        score = redis_metrics.health_score
        assert score < 100.0
        assert score > 70.0


# ============================================================================
# CIRCUIT BREAKER STATE TESTS
# ============================================================================

class TestCircuitBreakerState:
    """Test circuit breaker state transitions"""
    
    @pytest.mark.asyncio
    async def test_initial_state_closed(self, redis_breaker):
        """Comienza en estado CLOSED"""
        assert redis_breaker.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_check_state_closed(self, redis_breaker):
        """Permite acceso en estado CLOSED"""
        result = await redis_breaker._check_state()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_open_after_max_failures(self, redis_breaker):
        """Transición a OPEN después de max fallos"""
        redis_breaker.failure_count = redis_breaker.fail_max
        await redis_breaker._record_failure("test error")
        
        assert redis_breaker.state == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, redis_breaker):
        """Transición a HALF_OPEN después del timeout"""
        redis_breaker.state = CircuitBreakerState.OPEN
        redis_breaker.last_failure_time = datetime.utcnow() - timedelta(
            seconds=redis_breaker.reset_timeout + 1
        )
        
        result = await redis_breaker._check_state()
        assert result is True
        assert redis_breaker.state == CircuitBreakerState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_recover_to_closed_from_half_open(self, redis_breaker):
        """Transición a CLOSED desde HALF_OPEN con éxito"""
        redis_breaker.state = CircuitBreakerState.HALF_OPEN
        
        await redis_breaker._record_success()
        
        assert redis_breaker.state == CircuitBreakerState.CLOSED


# ============================================================================
# REDIS OPERATIONS TESTS
# ============================================================================

class TestRedisOperations:
    """Test Redis operations through circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_get_success(self, redis_breaker):
        """GET exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.return_value = "test_value"
        
        result = await redis_breaker.get("test_key")
        
        assert result == "test_value"
        redis_breaker.redis_client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, redis_breaker):
        """GET con cache hit registra métrica"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.return_value = "value"
        
        await redis_breaker.get("key")
        
        assert redis_breaker.health_metrics.cache_hits == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, redis_breaker):
        """GET sin valor registra cache miss"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.return_value = None
        
        await redis_breaker.get("nonexistent")
        
        assert redis_breaker.health_metrics.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_set_success(self, redis_breaker):
        """SET exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.set.return_value = True
        
        result = await redis_breaker.set("key", "value", ex=3600)
        
        assert result is True
        redis_breaker.redis_client.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_success(self, redis_breaker):
        """DELETE exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.delete.return_value = 2
        
        result = await redis_breaker.delete("key1", "key2")
        
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_incr_success(self, redis_breaker):
        """INCR exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.incrby.return_value = 42
        
        result = await redis_breaker.incr("counter", 5)
        
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_lpush_success(self, redis_breaker):
        """LPUSH exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.lpush.return_value = 3
        
        result = await redis_breaker.lpush("list", "a", "b", "c")
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_rpop_success(self, redis_breaker):
        """RPOP exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.rpop.return_value = "item"
        
        result = await redis_breaker.rpop("list")
        
        assert result == "item"
    
    @pytest.mark.asyncio
    async def test_llen_success(self, redis_breaker):
        """LLEN exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.llen.return_value = 5
        
        result = await redis_breaker.llen("list")
        
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_hset_success(self, redis_breaker):
        """HSET exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.hset.return_value = 3
        
        result = await redis_breaker.hset("hash", {"a": 1, "b": 2, "c": 3})
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_hgetall_success(self, redis_breaker):
        """HGETALL exitoso"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.hgetall.return_value = {"a": "1", "b": "2"}
        
        result = await redis_breaker.hgetall("hash")
        
        assert result == {"a": "1", "b": "2"}


# ============================================================================
# CIRCUIT BREAKER PROTECTION TESTS
# ============================================================================

class TestCircuitBreakerProtection:
    """Test circuit breaker protection mechanisms"""
    
    @pytest.mark.asyncio
    async def test_operation_rejected_when_open(self, redis_breaker):
        """Operación rechazada cuando CB está OPEN"""
        redis_breaker.state = CircuitBreakerState.OPEN
        redis_breaker.last_failure_time = datetime.utcnow()
        
        result = await redis_breaker.get("key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cascading_failures_trigger_open(self, redis_breaker):
        """Fallos en cascada abren el CB"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.side_effect = Exception("Connection error")
        
        # Registrar múltiples fallos
        for _ in range(redis_breaker.fail_max):
            await redis_breaker.get("key")
        
        assert redis_breaker.state == CircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_failed_recovery_reopens_breaker(self, redis_breaker):
        """Recuperación fallida reabre el CB"""
        redis_breaker.state = CircuitBreakerState.HALF_OPEN
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.side_effect = Exception("Still broken")
        
        await redis_breaker.get("key")
        
        assert redis_breaker.state == CircuitBreakerState.OPEN


# ============================================================================
# HEALTH & STATUS TESTS
# ============================================================================

class TestHealthAndStatus:
    """Test health check and status reporting"""
    
    @pytest.mark.asyncio
    async def test_get_health(self, redis_breaker):
        """Get health returns válido dict"""
        health = await redis_breaker.get_health()
        
        assert 'state' in health
        assert 'is_healthy' in health
        assert 'health_score' in health
        assert 'success_rate' in health
    
    @pytest.mark.asyncio
    async def test_healthy_status_when_closed(self, redis_breaker):
        """Estado es healthy cuando CB está CLOSED"""
        redis_breaker.state = CircuitBreakerState.CLOSED
        health = await redis_breaker.get_health()
        
        assert health['state'] == 'CLOSED'
        assert health['is_healthy'] is True
    
    @pytest.mark.asyncio
    async def test_unhealthy_status_when_open(self, redis_breaker):
        """Estado es unhealthy cuando CB está OPEN"""
        redis_breaker.state = CircuitBreakerState.OPEN
        health = await redis_breaker.get_health()
        
        assert health['state'] == 'OPEN'
        assert health['is_healthy'] is False
    
    @pytest.mark.asyncio
    async def test_get_status_comprehensive(self, redis_breaker):
        """Get status retorna información completa"""
        status = await redis_breaker.get_status()
        
        assert status['service'] == 'redis'
        assert 'timestamp' in status
        assert 'connection' in status
        assert 'circuit_breaker' in status
        assert 'health' in status
        assert 'metrics' in status


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_get_latency_acceptable(self, redis_breaker):
        """GET latency es aceptable"""
        redis_breaker.redis_client = AsyncMock()
        redis_breaker.redis_client.get.return_value = "value"
        
        import time
        start = time.time()
        for _ in range(100):
            await redis_breaker.get("key")
        duration = time.time() - start
        
        # 100 operaciones en <1 segundo
        assert duration < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
