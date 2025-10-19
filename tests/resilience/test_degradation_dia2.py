"""
Test Suite for DÍA 2 Degradation Manager - Integration Tests (HORAS 6-8)

Covers:
  1. DegradationManager (enhanced version)
  2. DegradationConfig
  3. Integration with circuit breakers
  4. Recovery loop orchestration
  5. Health aggregator calculations
  6. Cascading failures
  7. State transitions

Author: Operations Team
Date: October 18, 2025
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import all components
from inventario_retail.shared.degradation_manager import (
    DegradationManager, DegradationLevel, ComponentHealth, AutoScalingConfig,
    degradation_manager
)
from inventario_retail.shared.degradation_config import (
    DegradationThresholds, ComponentWeights, FeatureAvailability,
    ResponseTimeThresholds, CascadingFailureRules, RecoveryStrategies,
    degradation_config
)
from inventario_retail.shared.recovery_loop import (
    AutoRecoveryLoop, RecoveryCheckpoint, CascadingFailurePatternDetector,
    RecoveryPredictor
)
from inventario_retail.shared.health_aggregator import (
    HealthAggregator, HealthScoreCalculator, HealthScoreMetrics,
    HealthStateMachine, HealthState, CascadingImpactCalculator
)
from inventario_retail.shared.integration_degradation_breakers import (
    DegradationBreakerIntegration, CircuitBreakerSnapshot,
    CascadingFailureDetector, CircuitBreakerMonitor
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def degradation_mgr():
    """Fresh DegradationManager instance"""
    return DegradationManager()


@pytest.fixture
def health_aggregator():
    """Fresh HealthAggregator instance"""
    weights = ComponentWeights.get_weights_dict()
    rules = CascadingFailureRules.FAILURE_IMPACTS
    return HealthAggregator(weights, rules)


@pytest.fixture
def recovery_loop(degradation_mgr, health_aggregator):
    """Fresh AutoRecoveryLoop instance"""
    return AutoRecoveryLoop(degradation_mgr, health_aggregator)


@pytest.fixture
def breaker_integration(degradation_mgr):
    """Fresh DegradationBreakerIntegration instance"""
    rules = CascadingFailureRules.FAILURE_IMPACTS
    return DegradationBreakerIntegration(degradation_mgr, rules)


# ============================================================================
# DEGRADATION MANAGER TESTS
# ============================================================================

class TestDegradationManagerHealthScoring:
    """Test health score calculation and component tracking"""
    
    @pytest.mark.asyncio
    async def test_component_health_tracking(self, degradation_mgr):
        """Verifica que los componentes se registren correctamente"""
        async def check_db():
            return True
        
        await degradation_mgr.register_health_check('database', check_db, weight=0.4)
        
        assert 'database' in degradation_mgr.component_health
        assert degradation_mgr.component_health['database'].weight == 0.4
    
    @pytest.mark.asyncio
    async def test_health_score_calculation(self, degradation_mgr):
        """Verifica el cálculo de health score (0-100)"""
        async def check_ok():
            return True
        
        async def check_fail():
            return False
        
        await degradation_mgr.register_health_check('db', check_ok, weight=0.5)
        await degradation_mgr.register_health_check('cache', check_fail, weight=0.5)
        
        await degradation_mgr.evaluate_health()
        score = degradation_mgr.calculate_overall_health_score()
        
        # Cache fails pero DB ok, así que score debería ser ~50
        assert 40 < score < 60
    
    @pytest.mark.asyncio
    async def test_weighted_health_calculation(self, degradation_mgr):
        """Verifica que los pesos se apliquen correctamente"""
        async def always_ok():
            return True
        
        async def always_fail():
            return False
        
        # DB crítico (0.8), OpenAI menos importante (0.2)
        await degradation_mgr.register_health_check('database', always_ok, weight=0.8)
        await degradation_mgr.register_health_check('openai', always_fail, weight=0.2)
        
        await degradation_mgr.evaluate_health()
        score = degradation_mgr.calculate_overall_health_score()
        
        # Score debería estar más cerca de 100 porque DB es 80% del peso
        assert score > 75


class TestDegradationLevelTransitions:
    """Test transiciones entre niveles de degradación"""
    
    @pytest.mark.asyncio
    async def test_optimal_to_degraded_transition(self, degradation_mgr):
        """Verifica transición OPTIMAL → DEGRADED"""
        async def cache_fails():
            return False
        
        async def rest_ok():
            return True
        
        await degradation_mgr.register_health_check('cache', cache_fails)
        await degradation_mgr.register_health_check('database', rest_ok)
        await degradation_mgr.register_health_check('openai', rest_ok)
        
        new_level = await degradation_mgr.evaluate_health()
        assert new_level == DegradationLevel.DEGRADED
        
        await degradation_mgr.set_level(new_level)
        assert degradation_mgr.current_level == DegradationLevel.DEGRADED
    
    @pytest.mark.asyncio
    async def test_recovery_transition(self, degradation_mgr):
        """Verifica transición DEGRADED → OPTIMAL (recuperación)"""
        # Comienza en DEGRADED
        degradation_mgr.current_level = DegradationLevel.DEGRADED
        
        async def all_healthy():
            return True
        
        await degradation_mgr.register_health_check('database', all_healthy)
        await degradation_mgr.register_health_check('cache', all_healthy)
        await degradation_mgr.register_health_check('openai', all_healthy)
        
        new_level = await degradation_mgr.evaluate_health()
        assert new_level == DegradationLevel.OPTIMAL
        
        # Verificar que se registre el tiempo de recuperación
        assert degradation_mgr._degradation_start_time is None or isinstance(
            degradation_mgr._last_recovery_time, timedelta
        )


class TestResourceScalingConfig:
    """Test configuración de auto-scaling de recursos"""
    
    def test_scaling_config_optimal(self, degradation_mgr):
        """Verifica config de recursos en OPTIMAL"""
        degradation_mgr.current_level = DegradationLevel.OPTIMAL
        cfg = degradation_mgr.get_resource_scaling_config()
        
        assert cfg['connection_pool_multiplier'] == 1.0
        assert cfg['batch_size_multiplier'] == 1.0
        assert cfg['cache_ttl_seconds'] == 3600
    
    def test_scaling_config_minimal(self, degradation_mgr):
        """Verifica config de recursos en MINIMAL"""
        degradation_mgr.current_level = DegradationLevel.MINIMAL
        cfg = degradation_mgr.get_resource_scaling_config()
        
        assert cfg['connection_pool_multiplier'] == 0.5
        assert cfg['batch_size_multiplier'] == 0.25
        assert cfg['cache_ttl_seconds'] == 300
    
    def test_scaling_config_emergency(self, degradation_mgr):
        """Verifica config de recursos en EMERGENCY"""
        degradation_mgr.current_level = DegradationLevel.EMERGENCY
        cfg = degradation_mgr.get_resource_scaling_config()
        
        assert cfg['connection_pool_multiplier'] == 0.2
        assert cfg['batch_size_multiplier'] == 0.1
        assert cfg['cache_ttl_seconds'] == 60


# ============================================================================
# DEGRADATION CONFIG TESTS
# ============================================================================

class TestFeatureAvailability:
    """Test matriz de disponibilidad de features"""
    
    def test_features_optimal(self):
        """Todas las features disponibles en OPTIMAL"""
        features = FeatureAvailability.get_available_features('OPTIMAL')
        
        assert 'cache_write' in features
        assert 'openai_enhancement' in features
        assert 'inventory_write' in features
    
    def test_features_limited(self):
        """Features de AI deshabilitadas en LIMITED"""
        features = FeatureAvailability.get_available_features('LIMITED')
        
        assert 'cache_write' not in features  # No disponible
        assert 'openai_enhancement' not in features  # No disponible
        assert 'database_read_readonly' in features  # Siempre disponible
    
    def test_features_emergency(self):
        """Solo features críticas en EMERGENCY"""
        features = FeatureAvailability.get_available_features('EMERGENCY')
        
        assert 'health_check' in features
        assert 'status_page' in features
        assert 'database_write' not in features


class TestComponentWeights:
    """Test configuración de pesos de componentes"""
    
    def test_weights_sum_to_one(self):
        """Los pesos suman exactamente 1.0"""
        assert ComponentWeights.validate()
    
    def test_database_most_critical(self):
        """Database tiene el mayor peso"""
        weights = ComponentWeights.get_weights_dict()
        
        assert weights['database'] == 0.40
        assert weights['database'] > weights['cache']
        assert weights['database'] > weights['openai']


# ============================================================================
# RECOVERY LOOP TESTS
# ============================================================================

class TestRecoveryLoop:
    """Test sistema de recuperación automática"""
    
    def test_recovery_checkpoint_backoff(self):
        """Verifica exponential backoff en recuperación"""
        checkpoint = RecoveryCheckpoint(
            component_name='database',
            failed_at=datetime.utcnow(),
            last_check_at=datetime.utcnow()
        )
        
        # Simular 3 intentos fallidos
        checkpoint.record_attempt(False)  # Primer fallo
        assert checkpoint.next_retry_at is not None
        first_backoff = checkpoint.next_retry_at
        
        checkpoint.record_attempt(False)  # Segundo fallo
        second_backoff = checkpoint.next_retry_at
        
        # El segundo backoff debe ser mayor que el primero
        assert second_backoff > first_backoff
    
    def test_cascading_pattern_detection(self):
        """Detecta patrones de fallos en cascada"""
        detector = CascadingFailurePatternDetector()
        
        # Registrar patrón: A→B→C→A→B→C
        for _ in range(3):
            detector.record_failure('database')
            detector.record_failure('cache')
            detector.record_failure('openai')
        
        pattern = detector.detect_sequential_pattern()
        assert pattern is not None
        assert len(pattern) == 3
    
    def test_recovery_predictor(self):
        """Predice probabilidad de éxito de recuperación"""
        predictor = RecoveryPredictor()
        
        # Registrar recuperación exitosa
        predictor.record_recovery_attempt(
            'database',
            was_successful=True,
            recovery_duration_seconds=15.0,
            health_score_before=40.0,
            health_score_after=85.0
        )
        
        # Predicción para el mismo componente debería ser optimista
        prob = predictor.predict_recovery_success(
            'database',
            time_since_failure_seconds=35.0,
            current_health_score=60.0
        )
        
        assert prob > 0.4  # Probabilidad razonable


# ============================================================================
# HEALTH AGGREGATOR TESTS
# ============================================================================

class TestHealthScoreCalculation:
    """Test cálculo de health scores"""
    
    def test_perfect_health_score(self):
        """Score 100 cuando todo está perfecto"""
        metrics = HealthScoreMetrics(
            success_rate=1.0,
            latency_percentile_95_ms=100.0,
            error_rate=0.0,
            availability_percent=100.0,
            circuit_breaker_state='closed'
        )
        
        score = HealthScoreCalculator.calculate_component_score(metrics)
        assert score == 100.0
    
    def test_degraded_health_score(self):
        """Score reduce con latencia alta"""
        metrics = HealthScoreMetrics(
            success_rate=0.95,
            latency_percentile_95_ms=1000.0,  # Muy alta
            error_rate=0.05,
            availability_percent=95.0,
            circuit_breaker_state='closed'
        )
        
        score = HealthScoreCalculator.calculate_component_score(
            metrics, 
            latency_threshold_ms=500
        )
        assert score < 80  # Penalizado por latencia
    
    def test_circuit_breaker_open_penalty(self):
        """Score very low cuando CB está open"""
        metrics = HealthScoreMetrics(
            success_rate=0.5,
            latency_percentile_95_ms=100.0,
            error_rate=0.5,
            availability_percent=50.0,
            circuit_breaker_state='open'
        )
        
        score = HealthScoreCalculator.calculate_component_score(metrics)
        assert score < 30  # Gran penalidad


class TestHealthStateMachine:
    """Test transiciones de estado de salud"""
    
    @pytest.mark.asyncio
    async def test_healthy_to_degraded_transition(self):
        """Transición HEALTHY → DEGRADED"""
        sm = HealthStateMachine()
        
        # Comenzar saludable
        assert sm.current_state == HealthState.HEALTHY
        
        # Score intermedio dispara DEGRADED
        next_state = sm.get_next_state(75.0)
        await sm.transition(next_state)
        
        assert sm.current_state == HealthState.DEGRADED
    
    @pytest.mark.asyncio
    async def test_hysteresis_prevents_oscillation(self):
        """La histéresis previene oscilaciones"""
        sm = HealthStateMachine()
        sm.current_state = HealthState.HEALTHY
        
        # Score 75 (justo en el borde)
        # Pero con hysteresis de HEALTHY (75), no debería cambiar
        next_state = sm.get_next_state(75.0)
        assert next_state == HealthState.HEALTHY  # Se mantiene


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCascadingFailureDetection:
    """Test detección de fallos en cascada"""
    
    async def test_database_failure_cascades(self):
        """Fallo en DB afecta a Cache"""
        detector = CascadingFailureDetector(CascadingFailureRules.FAILURE_IMPACTS)
        
        snapshots = {
            'database': CircuitBreakerSnapshot('database', 'open', 3),
            'cache': CircuitBreakerSnapshot('cache', 'closed', 0),
        }
        
        impact = detector.evaluate_cascading_impact('database', snapshots)
        assert impact > 0  # Hay impacto en cascada


class TestCircuitBreakerMonitor:
    """Test monitoreo de circuit breakers"""
    
    @pytest.mark.asyncio
    async def test_state_change_callback(self):
        """Callbacks se invocan en cambios de estado"""
        monitor = CircuitBreakerMonitor()
        callback_called = {'called': False}
        
        async def on_state_change(name, old, new):
            callback_called['called'] = True
        
        await monitor.register_state_change_callback(on_state_change)
        
        snapshot = CircuitBreakerSnapshot('test', 'open', 1)
        await monitor.update_breaker_snapshot('test', snapshot)
        
        # Cambiar estado
        snapshot2 = CircuitBreakerSnapshot('test', 'half-open', 0)
        await monitor.update_breaker_snapshot('test', snapshot2)
        
        assert callback_called['called']


# ============================================================================
# INTEGRATION END-TO-END TESTS
# ============================================================================

class TestEndToEndDegradation:
    """Test completo: degradación y recuperación"""
    
    @pytest.mark.asyncio
    async def test_full_degradation_cycle(self, degradation_mgr, health_aggregator):
        """Test ciclo completo: OPTIMAL → MINIMAL → OPTIMAL"""
        
        # Setup
        async def db_ok():
            return True
        
        async def openai_ok():
            return True
        
        async def cache_ok():
            return True
        
        await degradation_mgr.register_health_check('database', db_ok)
        await degradation_mgr.register_health_check('openai', openai_ok)
        await degradation_mgr.register_health_check('cache', cache_ok)
        
        # Fase 1: Verificar OPTIMAL
        level = await degradation_mgr.evaluate_health()
        assert level == DegradationLevel.OPTIMAL
        
        # Fase 2: Simular degradación
        async def db_fail():
            return False
        
        degradation_mgr.health_checks['database'] = db_fail
        
        level = await degradation_mgr.evaluate_health()
        assert level != DegradationLevel.OPTIMAL
        
        # Fase 3: Recuperarse
        async def db_recover():
            return True
        
        degradation_mgr.health_checks['database'] = db_recover
        
        level = await degradation_mgr.evaluate_health()
        assert level == DegradationLevel.OPTIMAL


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test que el sistema sea performante"""
    
    def test_health_score_calculation_fast(self):
        """Health score se calcula en <1ms"""
        metrics = HealthScoreMetrics(
            success_rate=0.98,
            latency_percentile_95_ms=120.0,
            error_rate=0.02,
            availability_percent=99.5,
            circuit_breaker_state='closed'
        )
        
        import time
        start = time.time()
        for _ in range(1000):
            HealthScoreCalculator.calculate_component_score(metrics)
        duration = time.time() - start
        
        # 1000 iteraciones en <100ms
        assert duration < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
