"""
Health Aggregator Module - DÍA 2 HORAS 4-6

Centraliza el cálculo de health scores con:
  1. Weighted health scoring (cada componente tiene peso)
  2. Cascading impact calculations
  3. State machine transitions
  4. Historical trending
  5. Anomaly detection

Este módulo es complementario al DegradationManager pero se enfoca
específicamente en calcular y predecir scores.

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation - DÍA 2 HORAS 4-6
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# WEIGHTED HEALTH SCORE CALCULATION
# ============================================================================

@dataclass
class HealthScoreMetrics:
    """Métricas que componen el health score"""
    success_rate: float  # 0.0-1.0
    latency_percentile_95_ms: float
    error_rate: float  # 0.0-1.0
    availability_percent: float  # 0.0-100
    circuit_breaker_state: str  # "closed", "open", "half-open"
    
    def to_dict(self) -> Dict:
        """Convierte a dict para logging/export"""
        return {
            'success_rate': round(self.success_rate, 3),
            'latency_p95_ms': round(self.latency_percentile_95_ms, 1),
            'error_rate': round(self.error_rate, 3),
            'availability_percent': round(self.availability_percent, 1),
            'circuit_breaker_state': self.circuit_breaker_state
        }


class HealthScoreCalculator:
    """Calcula el health score de un componente usando múltiples métricas"""
    
    @staticmethod
    def calculate_component_score(metrics: HealthScoreMetrics, 
                                 latency_threshold_ms: int = 500) -> float:
        """
        Calcula score 0-100 para un componente.
        
        Fórmula:
          Base = success_rate * 100
          Penalidad latencia = max(0, (p95_latency - threshold) / threshold * 20)
          CB Open penalidad = 50 si open, 10 si half-open
          Score = max(0, Base - penalidades)
        """
        base_score = metrics.success_rate * 100
        
        # Penalizar por latencia alta
        latency_penalty = max(0, 
            (metrics.latency_percentile_95_ms - latency_threshold_ms) / latency_threshold_ms * 20
        )
        
        # Penalizar por circuit breaker abierto
        cb_penalty = 0
        if "open" in metrics.circuit_breaker_state.lower():
            cb_penalty = 50
        elif "half" in metrics.circuit_breaker_state.lower():
            cb_penalty = 10
        
        # Penalizar por baja availability
        availability_penalty = (100 - metrics.availability_percent) / 5
        
        final_score = base_score - latency_penalty - cb_penalty - availability_penalty
        
        return max(0.0, min(100.0, final_score))
    
    @staticmethod
    def calculate_weighted_system_score(component_scores: Dict[str, Tuple[float, float]]) -> float:
        """
        Calcula el score del sistema usando weighted average.
        
        Args:
            component_scores: {
                'database': (95.0, 0.40),      # score, weight
                'cache': (80.0, 0.20),
                ...
            }
            
        Returns:
            Score 0-100 ponderado
        """
        total_weight = sum(weight for _, weight in component_scores.values())
        
        if total_weight == 0:
            return 100.0
        
        weighted_sum = sum(
            score * weight 
            for score, weight in component_scores.values()
        )
        
        return round(weighted_sum / total_weight, 2)


# ============================================================================
# CASCADING IMPACT CALCULATOR
# ============================================================================

class CascadingImpactCalculator:
    """Calcula cómo los fallos se propagan entre componentes"""
    
    def __init__(self, impact_matrix: Dict[str, Dict[str, float]]):
        """
        Args:
            impact_matrix: {
                'database': {'cache': 0.2, 'openai': 0.0},
                ...
            }
        """
        self.impact_matrix = impact_matrix
        self.cascade_history: List[Dict] = []
    
    def calculate_cascading_effect(self, 
                                  failed_component: str,
                                  affected_component: str,
                                  failure_severity: float) -> float:
        """
        Calcula el efecto en cascada de un fallo.
        
        Args:
            failed_component: Componente que falló
            affected_component: Componente potencialmente afectado
            failure_severity: Severidad del fallo (0.0-1.0)
            
        Returns:
            Impacto en cascada (0.0-1.0) en el componente afectado
        """
        base_impact = self.impact_matrix.get(
            failed_component.lower(), {}
        ).get(affected_component.lower(), 0.0)
        
        # Amplificar por severidad
        cascading_impact = base_impact * failure_severity
        
        # Registrar en histórico
        self.cascade_history.append({
            'timestamp': datetime.utcnow(),
            'source': failed_component,
            'affected': affected_component,
            'impact': cascading_impact
        })
        
        if len(self.cascade_history) > 200:
            self.cascade_history = self.cascade_history[-200:]
        
        return min(cascading_impact, 1.0)
    
    def get_total_cascading_load(self, component: str) -> float:
        """
        Obtiene la carga en cascada total que sufre un componente.
        
        Returns:
            Suma de impactos en cascada recientes (0.0-5.0+)
        """
        recent_cascades = [
            e['impact'] for e in self.cascade_history[-20:]
            if e['affected'].lower() == component.lower()
        ]
        
        return sum(recent_cascades) if recent_cascades else 0.0


# ============================================================================
# STATE MACHINE FOR HEALTH TRANSITIONS
# ============================================================================

class HealthState:
    """Estados posibles del health de un componente"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    CRITICAL = "critical"


class HealthStateMachine:
    """
    State machine para transiciones de salud con hysteresis.
    
    Transiciones:
    HEALTHY (score >= 80) ↔ DEGRADED (60-79) ↔ FAILING (40-59) ↔ CRITICAL (<40)
    """
    
    # Umbrales con hysteresis (evitar oscilaciones)
    HEALTHY_THRESHOLD = 80.0
    HEALTHY_HYSTERESIS = 75.0
    
    DEGRADED_THRESHOLD = 60.0
    DEGRADED_HYSTERESIS = 65.0
    
    FAILING_THRESHOLD = 40.0
    FAILING_HYSTERESIS = 45.0
    
    def __init__(self):
        self.current_state = HealthState.HEALTHY
        self.transition_history: List[Tuple[datetime, str, str]] = []
    
    def get_next_state(self, health_score: float) -> str:
        """Calcula el siguiente estado basado en el score"""
        
        # Usar hysteresis según el estado actual
        if self.current_state == HealthState.HEALTHY:
            threshold = self.HEALTHY_HYSTERESIS
        elif self.current_state == HealthState.DEGRADED:
            threshold = self.DEGRADED_THRESHOLD
        elif self.current_state == HealthState.FAILING:
            threshold = self.FAILING_THRESHOLD
        else:  # CRITICAL
            threshold = self.FAILING_THRESHOLD + 5
        
        # Determinar nuevo estado
        if health_score >= self.HEALTHY_THRESHOLD:
            return HealthState.HEALTHY
        elif health_score >= self.DEGRADED_THRESHOLD:
            return HealthState.DEGRADED
        elif health_score >= self.FAILING_THRESHOLD:
            return HealthState.FAILING
        else:
            return HealthState.CRITICAL
    
    async def transition(self, new_state: str) -> bool:
        """
        Transiciona a un nuevo estado.
        
        Returns:
            True si hubo transición, False si se mantuvo en el mismo estado
        """
        if new_state == self.current_state:
            return False
        
        old_state = self.current_state
        self.current_state = new_state
        
        self.transition_history.append((
            datetime.utcnow(),
            old_state,
            new_state
        ))
        
        if len(self.transition_history) > 100:
            self.transition_history = self.transition_history[-100:]
        
        logger.info(
            f"Health state transition: {old_state} → {new_state}",
            extra={"old": old_state, "new": new_state}
        )
        
        return True
    
    def get_stability_duration(self) -> Optional[timedelta]:
        """Cuánto tiempo lleva en el estado actual"""
        if not self.transition_history:
            return None
        
        last_transition_time = self.transition_history[-1][0]
        return datetime.utcnow() - last_transition_time


# ============================================================================
# HEALTH AGGREGATOR (MAIN CLASS)
# ============================================================================

class HealthAggregator:
    """
    Agregador central de health: combina todas las métricas y calcula
    el estado global del sistema.
    """
    
    def __init__(self, 
                 component_weights: Dict[str, float],
                 impact_matrix: Dict[str, Dict[str, float]]):
        self.component_weights = component_weights
        self.impact_calculator = CascadingImpactCalculator(impact_matrix)
        self.component_states: Dict[str, HealthStateMachine] = {}
        self.health_history: List[Tuple[datetime, float]] = []
        self.component_metrics: Dict[str, HealthScoreMetrics] = {}
        self._max_history = 200
        
        # Inicializar state machines
        for component in component_weights:
            self.component_states[component] = HealthStateMachine()
    
    async def update_component_metrics(self, component: str, 
                                       metrics: HealthScoreMetrics):
        """Actualiza las métricas de un componente"""
        self.component_metrics[component] = metrics
        
        # Calcular health score
        score = HealthScoreCalculator.calculate_component_score(metrics)
        
        # Obtener siguiente estado
        state_machine = self.component_states.get(component)
        if not state_machine:
            state_machine = HealthStateMachine()
            self.component_states[component] = state_machine
        
        next_state = state_machine.get_next_state(score)
        await state_machine.transition(next_state)
        
        logger.debug(
            f"{component} health: score={score:.1f}%, state={next_state}",
            extra={
                "component": component,
                "health_score": score,
                "health_state": next_state,
                "metrics": metrics.to_dict()
            }
        )
    
    def calculate_system_health_score(self) -> float:
        """Calcula el score global del sistema"""
        if not self.component_metrics:
            return 100.0
        
        component_scores = {}
        for component, metrics in self.component_metrics.items():
            score = HealthScoreCalculator.calculate_component_score(metrics)
            weight = self.component_weights.get(component, 0.1)
            component_scores[component] = (score, weight)
        
        system_score = HealthScoreCalculator.calculate_weighted_system_score(
            component_scores
        )
        
        # Guardar en histórico
        self.health_history.append((datetime.utcnow(), system_score))
        if len(self.health_history) > self._max_history:
            self.health_history = self.health_history[-self._max_history:]
        
        return system_score
    
    def get_failing_components(self) -> List[str]:
        """Retorna componentes que están fallando o críticos"""
        failing = []
        for component, state_machine in self.component_states.items():
            if state_machine.current_state in [HealthState.FAILING, HealthState.CRITICAL]:
                failing.append(component)
        return failing
    
    def get_health_trend(self, minutes: int = 5) -> Optional[str]:
        """
        Analiza el trend de health en los últimos N minutos.
        
        Returns:
            "improving", "stable", "declining" o None
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_scores = [s for t, s in self.health_history if t > cutoff]
        
        if len(recent_scores) < 2:
            return None
        
        # Comparar primero vs último
        first_score = recent_scores[0]
        last_score = recent_scores[-1]
        
        diff = last_score - first_score
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def get_system_status(self) -> Dict:
        """Retorna status completo del sistema"""
        system_score = self.calculate_system_health_score()
        
        return {
            'system_health_score': system_score,
            'health_trend': self.get_health_trend(),
            'component_states': {
                name: {
                    'state': sm.current_state,
                    'stability_seconds': (
                        sm.get_stability_duration().total_seconds()
                        if sm.get_stability_duration() else None
                    ),
                    'transitions': len(sm.transition_history)
                }
                for name, sm in self.component_states.items()
            },
            'failing_components': self.get_failing_components(),
            'component_scores': {
                component: {
                    'score': HealthScoreCalculator.calculate_component_score(metrics),
                    'metrics': metrics.to_dict()
                }
                for component, metrics in self.component_metrics.items()
            },
            'cascading_load': {
                component: self.impact_calculator.get_total_cascading_load(component)
                for component in self.component_states.keys()
            },
            'history_size': len(self.health_history),
            'recent_scores': [s for _, s in self.health_history[-5:]]
        }
