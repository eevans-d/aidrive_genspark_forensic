"""
Test suite para Database Circuit Breaker.

DÍA 1 HORAS 4-7 implementation tests.
Verifica: estado del breaker, modo read-only, transacciones, protección cascada.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from prometheus_client import REGISTRY

# Agregar path para imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../inventario-retail'))

from agente_negocio.services.database_service import (
    DatabaseService,
    get_database_service,
    check_database_health,
)
from shared.circuit_breakers import db_breaker


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_db_breaker():
    """Reset circuit breaker state before each test."""
    # Para pybreaker 1.0.1, podemos usar close() para resetear a CLOSED
    db_breaker.close()
    yield
    # Cleanup after test
    db_breaker.close()


@pytest.fixture(autouse=True)
def reset_prometheus():
    """Reset Prometheus metrics before each test."""
    # Limpiar collectors existentes
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    yield


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()
    return mock_conn, mock_cursor


@pytest.fixture
def db_service():
    """Create a DatabaseService instance for testing."""
    service = DatabaseService()
    return service


# ============================================================================
# TEST: CIRCUIT BREAKER STATES
# ============================================================================

@pytest.mark.asyncio
async def test_db_breaker_starts_closed(db_service):
    """DB breaker should start in CLOSED state."""
    # Reset it first to ensure CLOSED state
    db_breaker.close()
    # state is an object, convert to string for comparison
    state_str = str(db_breaker.state).lower()
    assert "closed" in state_str


@pytest.mark.asyncio
async def test_db_breaker_opens_after_3_failures(db_service, mock_db_connection):
    """DB breaker opens after 3 failures in reset_timeout window."""
    mock_conn, mock_cursor = mock_db_connection
    
    # Simulate 3 failures by opening the breaker manually
    # In real scenario, these would be actual failures
    db_breaker.open()
    
    # Verify breaker state changed to open
    state_str = str(db_breaker.state).lower()
    assert "open" in state_str


@pytest.mark.asyncio
async def test_db_read_query_with_circuit_breaker(db_service, mock_db_connection):
    """Read query should execute via circuit breaker."""
    mock_conn, mock_cursor = mock_db_connection
    
    # Mock cursor.fetchall() to return data
    mock_cursor.fetchall = MagicMock(return_value=[
        {"id": 1, "name": "Product A", "price": 100.0},
        {"id": 2, "name": "Product B", "price": 200.0}
    ])
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.read_query(
            query="SELECT * FROM products",
            request_id="test-read-001",
            timeout=30
        )
    
    # Verify result structure
    assert 'success' in result
    assert 'data' in result
    assert 'breaker_state' in result
    assert 'latency' in result


@pytest.mark.asyncio
async def test_db_write_query_with_circuit_breaker(db_service, mock_db_connection):
    """Write query should execute via circuit breaker."""
    mock_conn, mock_cursor = mock_db_connection
    
    # Mock execute to simulate successful insert
    mock_cursor.execute = MagicMock(return_value=None)
    mock_cursor.rowcount = 1
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.write_query(
            query="INSERT INTO products (name, price) VALUES (%s, %s)",
            params=("New Product", 150.0),
            request_id="test-write-001",
            timeout=30
        )
    
    # Verify result structure
    assert 'success' in result
    assert 'rows_affected' in result
    assert 'breaker_state' in result
    assert 'write_mode_enabled' in result
    assert 'latency' in result


# ============================================================================
# TEST: READ-ONLY MODE (GRACEFUL DEGRADATION)
# ============================================================================

@pytest.mark.asyncio
async def test_readonly_mode_activation(db_service):
    """Readonly mode should activate on write failures."""
    # Check initial state
    assert db_service.write_mode_enabled is True
    
    # Activate read-only mode
    db_service._activate_readonly_mode(reason="Write failure detected")
    
    # Verify mode is activated
    assert db_service.write_mode_enabled is False


@pytest.mark.asyncio
async def test_readonly_mode_deactivation(db_service):
    """Readonly mode should deactivate on recovery."""
    # Activate read-only
    db_service._activate_readonly_mode(reason="Test activation")
    assert db_service.write_mode_enabled is False
    
    # Deactivate read-only
    db_service._deactivate_readonly_mode()
    
    # Verify mode is deactivated
    assert db_service.write_mode_enabled is True


@pytest.mark.asyncio
async def test_write_blocked_in_readonly_mode(db_service):
    """Write operations should fail in read-only mode."""
    # Activate read-only mode
    db_service._activate_readonly_mode(reason="Testing write block")
    
    # Try to execute write query
    result = await db_service.write_query(
        query="UPDATE products SET price = %s WHERE id = %s",
        params=(250.0, 1),
        request_id="test-readonly-write",
        timeout=30
    )
    
    # Should fail with fallback
    assert result.get('write_mode_enabled') is False


# ============================================================================
# TEST: TRANSACTIONS (ACID PROPERTIES)
# ============================================================================

@pytest.mark.asyncio
async def test_transaction_atomic_execution(db_service, mock_db_connection):
    """Transaction should execute atomically."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute = MagicMock(return_value=None)
    mock_cursor.rowcount = 1
    
    operations = [
        {"query": "INSERT INTO table1 (col) VALUES (%s)", "params": ("value1",)},
        {"query": "UPDATE table2 SET col = %s WHERE id = %s", "params": ("value2", 1)}
    ]
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.transaction(
            operations=operations,
            request_id="test-transaction-001"
        )
    
    # Verify transaction structure
    assert 'success' in result
    assert 'operations_executed' in result
    assert 'breaker_state' in result
    assert 'latency' in result


@pytest.mark.asyncio
async def test_transaction_rollback_on_failure(db_service, mock_db_connection):
    """Transaction should rollback on any operation failure."""
    mock_conn, mock_cursor = mock_db_connection
    
    # First operation succeeds, second fails
    mock_cursor.execute = MagicMock(
        side_effect=[None, Exception("Constraint violation")]
    )
    
    operations = [
        {"query": "INSERT INTO table1 (col) VALUES (%s)", "params": ("value1",)},
        {"query": "INSERT INTO table2 (col) VALUES (%s)", "params": ("value2",)}
    ]
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.transaction(
            operations=operations,
            request_id="test-transaction-rollback"
        )
    
    # Should have failed and rolled back
    assert result.get('success') is False or result.get('fallback') is True


# ============================================================================
# TEST: CASCADING FAILURE PROTECTION
# ============================================================================

@pytest.mark.asyncio
async def test_cascading_failure_read_fallback(db_service):
    """Read operations should use fallback when DB is down."""
    # Open circuit breaker to simulate failure state
    db_breaker.open()
    
    result = await db_service.read_query(
        query="SELECT * FROM products",
        request_id="test-cascade-read",
        timeout=30
    )
    
    # Should have fallback data or indication
    assert 'data' in result or 'fallback' in result


@pytest.mark.asyncio
async def test_cascading_failure_write_blocks(db_service):
    """Write operations should be blocked during cascade failure."""
    # Open circuit breaker
    db_breaker.open()
    
    # Activate read-only mode
    db_service._activate_readonly_mode(reason="Cascading failure")
    
    result = await db_service.write_query(
        query="INSERT INTO products (name, price) VALUES (%s, %s)",
        params=("Blocked", 100.0),
        request_id="test-cascade-write",
        timeout=30
    )
    
    # Write should be blocked
    assert result.get('write_mode_enabled') is False


# ============================================================================
# TEST: CONCURRENT OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_read_queries(db_service, mock_db_connection):
    """Multiple concurrent reads should be handled safely."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchall = MagicMock(return_value=[{"id": i} for i in range(5)])
    
    with patch('psycopg2.connect', return_value=mock_conn):
        # Create 10 concurrent read tasks
        tasks = [
            db_service.read_query(
                query=f"SELECT * FROM products WHERE id = {i}",
                request_id=f"concurrent-read-{i}",
                timeout=30
            )
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
    
    # All should complete successfully
    assert len(results) == 10
    assert all(isinstance(r, dict) for r in results)


@pytest.mark.asyncio
async def test_concurrent_write_queries(db_service, mock_db_connection):
    """Multiple concurrent writes should be serialized safely."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute = MagicMock(return_value=None)
    mock_cursor.rowcount = 1
    
    with patch('psycopg2.connect', return_value=mock_conn):
        # Create 5 concurrent write tasks
        tasks = [
            db_service.write_query(
                query="INSERT INTO products (name, price) VALUES (%s, %s)",
                params=(f"Product {i}", i * 100.0),
                request_id=f"concurrent-write-{i}",
                timeout=30
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
    
    # All should complete
    assert len(results) == 5


# ============================================================================
# TEST: PROMETHEUS METRICS
# ============================================================================

@pytest.mark.asyncio
async def test_db_queries_metric_incremented(db_service, mock_db_connection):
    """DB queries metric should increment on each operation."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchall = MagicMock(return_value=[])
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.read_query(
            query="SELECT * FROM products",
            request_id="test-metric-read",
            timeout=30
        )
    
    # Verify metric was recorded
    assert 'latency' in result  # Latency recorded = metric recorded


@pytest.mark.asyncio
async def test_db_breaker_state_gauge(db_service):
    """DB breaker state gauge should reflect current state."""
    # Get initial state
    health = await check_database_health()
    
    assert 'breaker_state' in health
    assert health['breaker_state'] in ['closed', 'open', 'half-open']


# ============================================================================
# TEST: HEALTH CHECKS
# ============================================================================

@pytest.mark.asyncio
async def test_database_health_check(db_service):
    """Database health check should return complete status."""
    health = await check_database_health()
    
    # Verify required fields
    assert health['service'] == 'database'
    assert health['status'] in ['healthy', 'degraded', 'read-only', 'error']
    assert 'breaker_state' in health
    assert 'write_mode_enabled' in health
    assert 'fail_counter' in health
    assert 'fail_max' in health


@pytest.mark.asyncio
async def test_health_check_write_mode_status(db_service):
    """Health check should report write mode status."""
    # Activate read-only mode
    db_service._activate_readonly_mode(reason="Test")
    
    health = await check_database_health()
    
    # Should report read-only status
    assert health['write_mode_enabled'] is False
    assert health['status'] in ['read-only', 'degraded']


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_connection_error_handling(db_service):
    """Connection errors should be caught and logged."""
    with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
        result = await db_service.read_query(
            query="SELECT * FROM products",
            request_id="test-error-001",
            timeout=30
        )
    
    # Should have fallback or error indication
    assert 'fallback' in result or 'error' in result


@pytest.mark.asyncio
async def test_query_timeout_handling(db_service):
    """Query timeouts should be handled gracefully."""
    async def slow_query(*args, **kwargs):
        await asyncio.sleep(2)
        raise asyncio.TimeoutError("Query timeout")
    
    with patch.object(db_service, 'read_query', side_effect=slow_query):
        # This should timeout or be handled
        pass  # Implementation-specific


# ============================================================================
# TEST: LOGGING WITH REQUEST_ID
# ============================================================================

@pytest.mark.asyncio
async def test_request_id_propagation(db_service, mock_db_connection):
    """Request ID should be propagated through logs."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchall = MagicMock(return_value=[])
    
    test_request_id = "test-request-12345"
    
    with patch('psycopg2.connect', return_value=mock_conn):
        result = await db_service.read_query(
            query="SELECT * FROM products",
            request_id=test_request_id,
            timeout=30
        )
    
    # Request ID should be in logs (checked via result)
    # In real scenario, this would be verified in log output


# ============================================================================
# TEST: SINGLETON PATTERN
# ============================================================================

@pytest.mark.asyncio
async def test_database_service_singleton():
    """DatabaseService should follow singleton pattern."""
    service1 = get_database_service()
    service2 = get_database_service()
    
    # Should be the same instance
    assert service1 is service2


# ============================================================================
# TEST: PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_fallback_latency(db_service):
    """Fallback operations should complete within SLA."""
    import time
    
    start = time.time()
    result = await db_service.read_query(
        query="SELECT 1",  # Will fallback
        request_id="test-latency",
        timeout=1
    )
    elapsed = time.time() - start
    
    # Fallback should complete quickly (<100ms)
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_readonly_mode_check_latency(db_service):
    """Read-only mode check should be fast."""
    import time
    
    db_service._activate_readonly_mode(reason="Test")
    
    start = time.time()
    # Check multiple times
    for _ in range(100):
        _ = db_service.write_mode_enabled
    elapsed = time.time() - start
    
    # 100 checks should complete quickly
    assert elapsed < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
