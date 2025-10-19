"""
Degradation Configuration Module - DÍA 2 HORAS 2-4

Configuración centralizada para el sistema de degradación:
  - Feature availability matrix (qué features en cada nivel)
  - Threshold configurations (umbrales de transición)
  - Auto-scaling rules (multiplicadores de recursos)
  - Circuit breaker thresholds por componente
  - Response time targets y SLAs

Este módulo separa la configuración de la lógica, permitiendo cambios sin
modificar el código del DegradationManager.

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation - DÍA 2 HORAS 2-4
"""

from typing import Dict, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# FEATURE AVAILABILITY MATRIX
# ============================================================================

class FeatureAvailability:
    """
    Define qué features están disponibles en cada nivel de degradación.
    
    Niveles requeridos:
    - OPTIMAL (1): Full functionality
    - DEGRADED (2): Cache disabled
    - LIMITED (3): OpenAI/AI disabled
    - MINIMAL (4): Read-only DB
    - EMERGENCY (5): Maintenance mode
    """
    
    # Features que requieren OPTIMAL (unavailable si degradado)
    OPTIMAL_FEATURES = {
        'cache_write',
        'cache_read_from_cache',
        'cache_ttl_standard',
    }
    
    # Features que requieren máximo DEGRADED
    DEGRADED_FEATURES = {
        'database_write',
        'database_complex_queries',
        'batch_processing',
    }
    
    # Features que requieren máximo LIMITED (OpenAI can be down)
    LIMITED_FEATURES = {
        'openai_enhancement',
        'ai_recommendations',
        'ai_pricing_optimization',
    }
    
    # Features que requieren máximo MINIMAL (DB issues)
    MINIMAL_FEATURES = {
        'inventory_write',
        'pricing_update',
        'order_processing',
    }
    
    # Features siempre disponibles (incluso en EMERGENCY)
    EMERGENCY_FEATURES = {
        'health_check',
        'status_page',
        'metrics_export',
        'database_read_readonly',
    }
    
    @staticmethod
    def get_available_features(level_name: str) -> Set[str]:
        """Retorna set de features disponibles en un nivel específico"""
        features = set(FeatureAvailability.EMERGENCY_FEATURES)
        
        if level_name in ['MINIMAL', 'LIMITED', 'DEGRADED', 'OPTIMAL']:
            features.update(FeatureAvailability.MINIMAL_FEATURES)
        
        if level_name in ['LIMITED', 'DEGRADED', 'OPTIMAL']:
            features.update(FeatureAvailability.LIMITED_FEATURES)
        
        if level_name in ['DEGRADED', 'OPTIMAL']:
            features.update(FeatureAvailability.DEGRADED_FEATURES)
        
        if level_name == 'OPTIMAL':
            features.update(FeatureAvailability.OPTIMAL_FEATURES)
        
        return features


# ============================================================================
# DEGRADATION THRESHOLDS & TRANSITION RULES
# ============================================================================

@dataclass
class DegradationThresholds:
    """
    Define los umbrales de health score para transiciones de nivel.
    
    Scores utilizan rangos:
    - 90-100: OPTIMAL (todos saludables)
    - 70-89: DEGRADED (cache down pero rest ok)
    - 50-69: LIMITED (OpenAI down)
    - 30-49: MINIMAL (DB problemas)
    - 0-29: EMERGENCY (múltiples fallos críticos)
    """
    
    # Umbrales de transición (health score)
    optimal_min: float = 90.0          # >= 90% → OPTIMAL
    degraded_min: float = 70.0         # >= 70% → DEGRADED
    limited_min: float = 50.0          # >= 50% → LIMITED
    minimal_min: float = 30.0          # >= 30% → MINIMAL
    emergency_min: float = 0.0         # < 30% → EMERGENCY
    
    # Hysteresis (evitar oscilaciones frecuentes)
    hysteresis_margin: float = 2.0     # 2% margen para cambios
    
    # Time windows para estabilidad
    min_stable_time_seconds: int = 10  # Mantener nivel por mínimo 10s
    max_check_failures_before_downgrade: int = 3  # 3 checks fallidos → downgrade
    
    @property
    def thresholds_dict(self) -> Dict[str, float]:
        """Retorna dict para fácil acceso"""
        return {
            'OPTIMAL': self.optimal_min,
            'DEGRADED': self.degraded_min,
            'LIMITED': self.limited_min,
            'MINIMAL': self.minimal_min,
            'EMERGENCY': self.emergency_min
        }


# ============================================================================
# CIRCUIT BREAKER CONFIGURATIONS PER COMPONENT
# ============================================================================

@dataclass
class CircuitBreakerConfig:
    """Configuración específica para cada circuit breaker"""
    fail_max: int
    reset_timeout: int
    half_open_max_attempts: int = 1
    expected_exception: type = Exception  # (now unused with pybreaker 1.0.1)


class ComponentCircuitBreakerThresholds:
    """Define thresholds específicos para cada componente"""
    
    # OpenAI: Menos crítico (5 fallos en 60s antes de abrir)
    OPENAI = CircuitBreakerConfig(
        fail_max=5,
        reset_timeout=60,
        half_open_max_attempts=2
    )
    
    # Database: Muy crítico (3 fallos en 30s)
    DATABASE = CircuitBreakerConfig(
        fail_max=3,
        reset_timeout=30,
        half_open_max_attempts=1
    )
    
    # Redis: Moderado (5 fallos en 20s - rápida recuperación)
    REDIS = CircuitBreakerConfig(
        fail_max=5,
        reset_timeout=20,
        half_open_max_attempts=2
    )
    
    # S3: Menos crítico (5 fallos en 30s)
    S3 = CircuitBreakerConfig(
        fail_max=5,
        reset_timeout=30,
        half_open_max_attempts=2
    )
    
    @staticmethod
    def get_config(component_name: str) -> CircuitBreakerConfig:
        """Obtiene configuración por nombre de componente"""
        configs = {
            'openai': ComponentCircuitBreakerThresholds.OPENAI,
            'database': ComponentCircuitBreakerThresholds.DATABASE,
            'redis': ComponentCircuitBreakerThresholds.REDIS,
            's3': ComponentCircuitBreakerThresholds.S3
        }
        return configs.get(component_name.lower(), ComponentCircuitBreakerThresholds.OPENAI)


# ============================================================================
# COMPONENT HEALTH WEIGHTS FOR SCORING
# ============================================================================

class ComponentWeights:
    """
    Pesos relativos de cada componente en el health score general.
    
    Total = 1.0, distribuir según criticidad:
    - Database: 0.40 (muy crítico para operaciones)
    - Cache: 0.20 (importante pero degradable)
    - OpenAI: 0.20 (enhancements, no critical)
    - S3: 0.10 (archivos, fallback local)
    - External API: 0.10 (recomendaciones, optional)
    """
    
    DATABASE_WEIGHT: float = 0.40
    CACHE_WEIGHT: float = 0.20
    OPENAI_WEIGHT: float = 0.20
    S3_WEIGHT: float = 0.10
    EXTERNAL_API_WEIGHT: float = 0.10
    
    TOTAL_WEIGHT: float = 1.0
    
    @staticmethod
    def validate() -> bool:
        """Verifica que weights sumen 1.0"""
        total = (ComponentWeights.DATABASE_WEIGHT +
                ComponentWeights.CACHE_WEIGHT +
                ComponentWeights.OPENAI_WEIGHT +
                ComponentWeights.S3_WEIGHT +
                ComponentWeights.EXTERNAL_API_WEIGHT)
        return abs(total - 1.0) < 0.001
    
    @staticmethod
    def get_weights_dict() -> Dict[str, float]:
        """Retorna dict para fácil acceso"""
        return {
            'database': ComponentWeights.DATABASE_WEIGHT,
            'cache': ComponentWeights.CACHE_WEIGHT,
            'openai': ComponentWeights.OPENAI_WEIGHT,
            's3': ComponentWeights.S3_WEIGHT,
            'external_api': ComponentWeights.EXTERNAL_API_WEIGHT
        }


# ============================================================================
# RESPONSE TIME THRESHOLDS & SLA
# ============================================================================

@dataclass
class ResponseTimeThresholds:
    """Define latencias máximas por nivel de degradación"""
    
    # P95 latencies (95th percentile)
    optimal_p95_ms: int = 100       # OPTIMAL: <100ms
    degraded_p95_ms: int = 200      # DEGRADED: <200ms
    limited_p95_ms: int = 500       # LIMITED: <500ms
    minimal_p95_ms: int = 1000      # MINIMAL: <1s
    emergency_p95_ms: int = 5000    # EMERGENCY: <5s
    
    # Timeout values
    optimal_timeout_ms: int = 2000
    degraded_timeout_ms: int = 3000
    limited_timeout_ms: int = 5000
    minimal_timeout_ms: int = 10000
    emergency_timeout_ms: int = 30000
    
    @property
    def thresholds_dict(self) -> Dict[str, int]:
        """Retorna dict de P95 thresholds"""
        return {
            'OPTIMAL': self.optimal_p95_ms,
            'DEGRADED': self.degraded_p95_ms,
            'LIMITED': self.limited_p95_ms,
            'MINIMAL': self.minimal_p95_ms,
            'EMERGENCY': self.emergency_p95_ms
        }
    
    @property
    def timeout_dict(self) -> Dict[str, int]:
        """Retorna dict de timeouts"""
        return {
            'OPTIMAL': self.optimal_timeout_ms,
            'DEGRADED': self.degraded_timeout_ms,
            'LIMITED': self.limited_timeout_ms,
            'MINIMAL': self.minimal_timeout_ms,
            'EMERGENCY': self.emergency_timeout_ms
        }


# ============================================================================
# CASCADING FAILURE RULES
# ============================================================================

class CascadingFailureRules:
    """
    Define cómo los fallos en un componente afectan a otros.
    
    Ejemplo:
    - Si Database falla → No se pueden hacer writes
    - Si Cache falla → Mayor carga en Database
    - Si OpenAI falla → Features AI disabled, pero resto funciona
    """
    
    # Mapping de impactos: si X falla, Y se ve afectado
    FAILURE_IMPACTS = {
        'database': {
            'cache': 0.2,        # 20% impacto negativo en cache
            'openai': 0.0,       # Sin impacto en openai
            's3': 0.1            # 10% impacto en s3
        },
        'cache': {
            'database': 0.3,     # 30% impacto en database (más queries)
            'openai': 0.0,
            's3': 0.0
        },
        'openai': {
            'database': 0.0,
            'cache': 0.0,
            's3': 0.0            # No afecta a otros
        },
        's3': {
            'database': 0.0,
            'cache': 0.0,
            'openai': 0.0        # No afecta a otros (fallback local)
        }
    }
    
    @staticmethod
    def get_cascading_penalty(failed_component: str, affected_component: str) -> float:
        """
        Obtiene la penalidad en cascada.
        
        Args:
            failed_component: Componente que falló
            affected_component: Componente afectado
            
        Returns:
            Penalidad (0.0-1.0) a aplicar al health score del componente afectado
        """
        return CascadingFailureRules.FAILURE_IMPACTS.get(
            failed_component.lower(), {}
        ).get(affected_component.lower(), 0.0)


# ============================================================================
# RECOVERY STRATEGIES PER LEVEL
# ============================================================================

@dataclass
class RecoveryStrategy:
    """Estrategia de recuperación para cada nivel de degradación"""
    name: str
    retry_backoff_multiplier: float = 1.5
    max_retries: int = 3
    exponential_backoff: bool = True
    circuit_breaker_aggressive: bool = False
    

class RecoveryStrategies:
    """Define diferentes estrategias de recuperación"""
    
    OPTIMAL_STRATEGY = RecoveryStrategy(
        name="Optimal - Normal operation",
        retry_backoff_multiplier=1.0,
        max_retries=3,
        exponential_backoff=False,
        circuit_breaker_aggressive=False
    )
    
    DEGRADED_STRATEGY = RecoveryStrategy(
        name="Degraded - Cache bypass",
        retry_backoff_multiplier=1.5,
        max_retries=2,
        exponential_backoff=True,
        circuit_breaker_aggressive=False
    )
    
    LIMITED_STRATEGY = RecoveryStrategy(
        name="Limited - AI disabled",
        retry_backoff_multiplier=2.0,
        max_retries=1,
        exponential_backoff=True,
        circuit_breaker_aggressive=False
    )
    
    MINIMAL_STRATEGY = RecoveryStrategy(
        name="Minimal - Read-only DB",
        retry_backoff_multiplier=3.0,
        max_retries=0,
        exponential_backoff=True,
        circuit_breaker_aggressive=True
    )
    
    EMERGENCY_STRATEGY = RecoveryStrategy(
        name="Emergency - Maintenance mode",
        retry_backoff_multiplier=5.0,
        max_retries=0,
        exponential_backoff=True,
        circuit_breaker_aggressive=True
    )
    
    @staticmethod
    def get_strategy(level_name: str) -> RecoveryStrategy:
        """Obtiene estrategia por nombre de nivel"""
        strategies = {
            'OPTIMAL': RecoveryStrategies.OPTIMAL_STRATEGY,
            'DEGRADED': RecoveryStrategies.DEGRADED_STRATEGY,
            'LIMITED': RecoveryStrategies.LIMITED_STRATEGY,
            'MINIMAL': RecoveryStrategies.MINIMAL_STRATEGY,
            'EMERGENCY': RecoveryStrategies.EMERGENCY_STRATEGY
        }
        return strategies.get(level_name.upper(), RecoveryStrategies.OPTIMAL_STRATEGY)


# ============================================================================
# ALERTS & NOTIFICATIONS
# ============================================================================

@dataclass
class AlertConfig:
    """Configuración para alerts basadas en degradación"""
    enabled: bool = True
    degradation_alert_threshold: int = 3  # Alerta si degradado por 3+ minutos
    recovery_alert_enabled: bool = True
    recovery_alert_above_seconds: int = 60  # Alerta si recuperación toma >60s
    metrics_export_interval_seconds: int = 30


# ============================================================================
# SINGLETON CONFIG INSTANCE
# ============================================================================

class DegradationConfig:
    """Configuración centralizada del sistema de degradación"""
    
    def __init__(self):
        self.thresholds = DegradationThresholds()
        self.response_times = ResponseTimeThresholds()
        self.alerts = AlertConfig()
        self.feature_availability = FeatureAvailability()
        self.component_weights = ComponentWeights()
        self.recovery_strategies = RecoveryStrategies()
        self.cascading_rules = CascadingFailureRules()
        
        # Validate
        if not ComponentWeights.validate():
            raise ValueError("Component weights do not sum to 1.0")
    
    def get_level_config(self, level_name: str) -> Dict:
        """Retorna configuración completa para un nivel"""
        return {
            'level': level_name,
            'health_threshold': self.thresholds.thresholds_dict.get(level_name),
            'response_time_p95': self.response_times.thresholds_dict.get(level_name),
            'timeout_ms': self.response_times.timeout_dict.get(level_name),
            'available_features': self.feature_availability.get_available_features(level_name),
            'recovery_strategy': self.recovery_strategies.get_strategy(level_name).__dict__
        }


# Global instance
degradation_config = DegradationConfig()
