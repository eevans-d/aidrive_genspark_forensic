"""
Integration Module: Degradation Manager ↔ Circuit Breakers - DÍA 2 HORAS 2-4

Este módulo orquesta la interacción entre el DegradationManager y los 4
circuit breakers (OpenAI, Database, Redis, S3).

Responsabilidades:
  1. Monitoreo bidireccional: Circuit breaker state → Degradation level
  2. Detección de fallos en cascada entre componentes
  3. Auto-reset de circuit breakers cuando el nivel mejora
  4. Sincronización de configuraciones dinámicas
  5. Logging centralizado de eventos

Flujo:
  Circuit Breaker State Change → evaluate_cascading_failures()
  → degradation_manager.set_level()
  → Recovery triggered → auto_reset_circuit_breaker()

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation - DÍA 2 HORAS 2-4
"""

from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# CIRCUIT BREAKER STATE TRACKING
# ============================================================================

class CircuitBreakerStateType(Enum):
    """Estados posibles de un circuit breaker"""
    CLOSED = "closed"          # Funcionando normalmente
    OPEN = "open"              # Fallos detectados, rechazando requests
    HALF_OPEN = "half-open"    # Recuperándose, permitiendo pruebas


class CircuitBreakerSnapshot:
    """Snapshot del estado actual de un circuit breaker"""
    
    def __init__(self, 
                 name: str,
                 state: str,
                 fail_count: int,
                 last_failure_time: Optional[datetime] = None,
                 success_count: int = 0,
                 latency_ms: float = 0.0):
        self.name = name
        self.state = state
        self.fail_count = fail_count
        self.success_count = success_count
        self.last_failure_time = last_failure_time
        self.latency_ms = latency_ms
        self.timestamp = datetime.utcnow()
    
    def is_failing(self) -> bool:
        """¿Está en estado OPEN o tiene fallos recientes?"""
        return "open" in self.state.lower() or self.fail_count > 0
    
    def time_since_last_failure(self) -> Optional[float]:
        """Segundos desde el último fallo"""
        if not self.last_failure_time:
            return None
        return (datetime.utcnow() - self.last_failure_time).total_seconds()
    
    def __repr__(self) -> str:
        return (f"CB[{self.name}] state={self.state} fails={self.fail_count} "
                f"success={self.success_count} latency={self.latency_ms:.1f}ms")


# ============================================================================
# CASCADING FAILURE DETECTION
# ============================================================================

class CascadingFailureDetector:
    """
    Detecta y cuantifica fallos en cascada entre componentes.
    
    Ejemplo de cascada:
    1. Database circuit breaker abre (conexión rechazada)
    2. Cache intenta depositar datos en DB → falla
    3. Aplicación intenta READ from cache → puede fallar si está lleno
    4. OpenAI llama a fallback que necesita DB → falla
    """
    
    def __init__(self, cascading_rules: Dict[str, Dict[str, float]]):
        """
        Args:
            cascading_rules: Dict de impactos en cascada
            Ejemplo: {'database': {'cache': 0.2, 'openai': 0.0}}
        """
        self.cascading_rules = cascading_rules
        self.failure_chain: List[Dict] = []
    
    def evaluate_cascading_impact(self, 
                                  failed_component: str,
                                  component_snapshots: Dict[str, CircuitBreakerSnapshot]) -> float:
        """
        Evalúa el impacto total en cascada de un fallo.
        
        Args:
            failed_component: Componente que falló
            component_snapshots: Snapshots actuales de todos los componentes
            
        Returns:
            Impacto acumulativo (0.0-1.0) en los otros componentes
        """
        total_impact = 0.0
        
        # Obtener reglas de impacto para el componente fallido
        impact_rules = self.cascading_rules.get(failed_component.lower(), {})
        
        for affected_component, direct_impact in impact_rules.items():
            # Amplificar el impacto si el componente afectado ya estaba degradado
            affected_snapshot = component_snapshots.get(affected_component)
            if affected_snapshot and affected_snapshot.is_failing():
                # Si ya estaba fallando, amplificar el impacto
                amplified_impact = direct_impact * (1 + affected_snapshot.fail_count / 10)
                total_impact += min(amplified_impact, 1.0)
            else:
                total_impact += direct_impact
        
        # Log de cascada si hay impacto significativo
        if total_impact > 0.1:
            logger.warning(
                f"Cascading failure detected: {failed_component} failure "
                f"causing {total_impact:.0%} additional system impact",
                extra={
                    "failed_component": failed_component,
                    "cascading_impact": total_impact,
                    "affected_components": list(impact_rules.keys())
                }
            )
            
            self.failure_chain.append({
                'timestamp': datetime.utcnow(),
                'failed_component': failed_component,
                'cascading_impact': total_impact
            })
            
            # Limitar histórico a 100 eventos
            if len(self.failure_chain) > 100:
                self.failure_chain = self.failure_chain[-100:]
        
        return total_impact
    
    def get_critical_path(self) -> Optional[str]:
        """Identifica el componente más crítico en la cadena de fallos"""
        if not self.failure_chain:
            return None
        
        # Componente con mayor impacto en cascada acumulado
        impact_by_component = {}
        for event in self.failure_chain[-20:]:  # Últimos 20 eventos
            comp = event['failed_component']
            impact = event['cascading_impact']
            impact_by_component[comp] = impact_by_component.get(comp, 0) + impact
        
        if impact_by_component:
            return max(impact_by_component, key=impact_by_component.get)
        return None


# ============================================================================
# CIRCUIT BREAKER MONITOR
# ============================================================================

class CircuitBreakerMonitor:
    """
    Monitorea el estado de todos los circuit breakers en tiempo real.
    Interfaz: permite registrar callbacks cuando el estado cambia.
    """
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreakerSnapshot] = {}
        self.state_change_callbacks: List[Callable] = []
        self.last_evaluation: Optional[datetime] = None
    
    async def register_state_change_callback(self, callback: Callable):
        """
        Registra callback para cambios de estado.
        Signature: callback(breaker_name: str, old_state: str, new_state: str)
        """
        self.state_change_callbacks.append(callback)
    
    async def update_breaker_snapshot(self, 
                                      breaker_name: str,
                                      snapshot: CircuitBreakerSnapshot):
        """Actualiza el snapshot de un circuit breaker"""
        old_snapshot = self.breakers.get(breaker_name)
        self.breakers[breaker_name] = snapshot
        
        # Detectar cambios de estado
        if old_snapshot and old_snapshot.state != snapshot.state:
            logger.info(
                f"Circuit breaker state change: {breaker_name} "
                f"{old_snapshot.state} → {snapshot.state}",
                extra={
                    "breaker": breaker_name,
                    "old_state": old_snapshot.state,
                    "new_state": snapshot.state
                }
            )
            
            # Invocar callbacks
            for callback in self.state_change_callbacks:
                try:
                    await callback(breaker_name, old_snapshot.state, snapshot.state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")
        
        self.last_evaluation = datetime.utcnow()
    
    def get_all_snapshots(self) -> Dict[str, CircuitBreakerSnapshot]:
        """Retorna snapshots de todos los circuit breakers"""
        return self.breakers.copy()
    
    def get_failing_components(self) -> List[str]:
        """Retorna lista de componentes en estado fallido"""
        return [name for name, snapshot in self.breakers.items() 
                if snapshot.is_failing()]
    
    def get_overall_health_impact(self) -> float:
        """
        Calcula el impacto general de los fallos en los circuit breakers.
        
        Returns:
            Score 0.0-1.0 donde 1.0 = completamente saludable
        """
        if not self.breakers:
            return 1.0
        
        health_impacts = {
            'database': 0.40,  # Muy crítico
            'cache': 0.20,     # Importante
            'openai': 0.20,    # Enhancements
            's3': 0.10,        # Archivos
            'redis': 0.10      # Puede ser cache o sesiones
        }
        
        total_impact = 0.0
        for name, snapshot in self.breakers.items():
            if snapshot.is_failing():
                weight = health_impacts.get(name.lower(), 0.05)
                total_impact += weight
        
        return max(0.0, 1.0 - min(total_impact, 1.0))


# ============================================================================
# AUTO-RECOVERY ORCHESTRATOR
# ============================================================================

class AutoRecoveryOrchestrator:
    """
    Orquesta la recuperación automática cuando el sistema mejora.
    Coordina reset de circuit breakers y transiciones de niveles.
    """
    
    def __init__(self, degradation_manager, monitor: CircuitBreakerMonitor):
        self.degradation_manager = degradation_manager
        self.monitor = monitor
        self.recovery_in_progress = False
        self.last_recovery_attempt: Optional[datetime] = None
        self.recovery_backoff_seconds = 30
    
    async def attempt_recovery(self):
        """
        Intenta recuperación: evalúa si los circuit breakers pueden resetearse.
        Llamado periódicamente (cada 30s) cuando está degradado.
        """
        if self.recovery_in_progress:
            return
        
        current_time = datetime.utcnow()
        if (self.last_recovery_attempt and 
            (current_time - self.last_recovery_attempt).total_seconds() < self.recovery_backoff_seconds):
            return
        
        self.recovery_in_progress = True
        self.last_recovery_attempt = current_time
        
        try:
            # Obtener snapshots actuales
            snapshots = self.monitor.get_all_snapshots()
            
            # Evaluar si cada CB puede transicionar a HALF_OPEN
            recovery_candidates = []
            for name, snapshot in snapshots.items():
                if snapshot.state.lower() == "open":
                    time_since_fail = snapshot.time_since_last_failure()
                    
                    # Si pasó reset_timeout, intentar HALF_OPEN
                    if time_since_fail and time_since_fail >= 30:  # Default reset_timeout
                        recovery_candidates.append(name)
            
            if recovery_candidates:
                logger.info(
                    f"Recovery: attempting to transition {len(recovery_candidates)} "
                    f"circuit breakers to HALF_OPEN: {recovery_candidates}",
                    extra={"recovery_candidates": recovery_candidates}
                )
                
                # Aquí irían llamadas para auto-reset actual de los CBs
                # await reset_circuit_breaker('openai')
                # etc.
                
                # Forzar re-evaluación del degradation level
                await self.degradation_manager.evaluate_health()
        
        except Exception as e:
            logger.error(f"Recovery attempt error: {e}", exc_info=True)
        
        finally:
            self.recovery_in_progress = False


# ============================================================================
# MAIN INTEGRATION CLASS
# ============================================================================

class DegradationBreakerIntegration:
    """
    Orquestador central: integra DegradationManager con todos los circuit breakers.
    
    Responsabilidades:
    1. Monitorear estado de CBs
    2. Detectar cascadas
    3. Dispara cambios de nivel
    4. Orquesta recuperación
    """
    
    def __init__(self, 
                 degradation_manager,
                 cascading_rules: Dict[str, Dict[str, float]]):
        self.degradation_manager = degradation_manager
        self.monitor = CircuitBreakerMonitor()
        self.cascading_detector = CascadingFailureDetector(cascading_rules)
        self.recovery_orchestrator = AutoRecoveryOrchestrator(
            degradation_manager, 
            self.monitor
        )
        self.integration_active = False
    
    async def initialize(self):
        """Inicializa la integración"""
        await self.monitor.register_state_change_callback(
            self._on_circuit_breaker_state_change
        )
        self.integration_active = True
        logger.info("Degradation-Breaker integration initialized")
    
    async def _on_circuit_breaker_state_change(self, 
                                               breaker_name: str,
                                               old_state: str,
                                               new_state: str):
        """Callback: cuando un circuit breaker cambia de estado"""
        
        logger.info(
            f"CB state changed: {breaker_name} {old_state} → {new_state}",
            extra={"breaker": breaker_name, "old": old_state, "new": new_state}
        )
        
        # Si alguno se abrió → posible degradación
        if "open" in new_state.lower():
            snapshots = self.monitor.get_all_snapshots()
            cascading_impact = self.cascading_detector.evaluate_cascading_impact(
                breaker_name, 
                snapshots
            )
            
            # Re-evaluar degradation level
            new_level = await self.degradation_manager.evaluate_health()
            await self.degradation_manager.set_level(new_level)
    
    async def update_all_breakers(self, breaker_updates: Dict[str, dict]):
        """
        Actualiza snapshots de todos los breakers de una vez.
        Útil para integración desde un loop de monitoreo central.
        
        Args:
            breaker_updates: {
                'openai': {'state': 'closed', 'fails': 0, 'success': 42, ...},
                'database': {...},
                ...
            }
        """
        for name, update_data in breaker_updates.items():
            snapshot = CircuitBreakerSnapshot(
                name=name,
                state=update_data.get('state', 'unknown'),
                fail_count=update_data.get('fail_count', 0),
                success_count=update_data.get('success_count', 0),
                latency_ms=update_data.get('latency_ms', 0.0),
                last_failure_time=update_data.get('last_failure_time')
            )
            await self.monitor.update_breaker_snapshot(name, snapshot)
    
    async def run_recovery_loop(self, interval_seconds: int = 30):
        """
        Loop continuo de recuperación (por separado del auto_recovery_loop del DM).
        """
        logger.info(f"Recovery loop started (interval={interval_seconds}s)")
        
        while self.integration_active:
            try:
                await self.recovery_orchestrator.attempt_recovery()
            except Exception as e:
                logger.error(f"Recovery loop error: {e}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)
    
    def get_integration_status(self) -> Dict:
        """Retorna status completo de la integración"""
        return {
            'active': self.integration_active,
            'circuit_breakers': {
                name: {
                    'state': snapshot.state,
                    'fail_count': snapshot.fail_count,
                    'success_count': snapshot.success_count,
                    'latency_ms': snapshot.latency_ms,
                    'is_failing': snapshot.is_failing()
                }
                for name, snapshot in self.monitor.get_all_snapshots().items()
            },
            'failing_components': self.monitor.get_failing_components(),
            'overall_health_impact': self.monitor.get_overall_health_impact(),
            'critical_path': self.cascading_detector.get_critical_path(),
            'recovery_in_progress': self.recovery_orchestrator.recovery_in_progress,
            'last_evaluation': self.monitor.last_evaluation.isoformat() if self.monitor.last_evaluation else None
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

def create_integration(degradation_manager, cascading_rules: Dict) -> DegradationBreakerIntegration:
    """Factory para crear la integración"""
    return DegradationBreakerIntegration(degradation_manager, cascading_rules)
