"""
Auto-Recovery Loop Module - DÍA 2 HORAS 4-6

Sistema de recuperación automática que:
  1. Ejecuta heartbeat de 30 segundos
  2. Evalúa si los componentes pueden recuperarse
  3. Detecta patrones de fallos en cascada
  4. Predice mejoras antes de ocurran
  5. Aplica backoff exponencial para retry

Flujo:
  30s interval → evaluate_health() → detect_cascading_failures()
  → can_attempt_recovery() → trigger_recovery()

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation - DÍA 2 HORAS 4-6
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, field
import statistics

logger = logging.getLogger(__name__)


# ============================================================================
# RECOVERY CHECKPOINT
# ============================================================================

@dataclass
class RecoveryCheckpoint:
    """Punto de control en el proceso de recuperación"""
    component_name: str
    failed_at: datetime
    last_check_at: datetime
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    backoff_multiplier: float = 2.0
    next_retry_at: Optional[datetime] = None
    
    def should_retry(self) -> bool:
        """¿Debería intentar recuperar este componente?"""
        if self.recovery_attempts >= self.max_recovery_attempts:
            return False
        
        if not self.next_retry_at:
            return True
        
        return datetime.utcnow() >= self.next_retry_at
    
    def record_attempt(self, success: bool):
        """Registra un intento de recuperación"""
        self.recovery_attempts += 1
        self.last_check_at = datetime.utcnow()
        
        if not success:
            # Calcular próximo retry con backoff exponencial
            backoff_seconds = 2 ** self.recovery_attempts * 5  # 10, 20, 40, ...
            self.next_retry_at = self.last_check_at + timedelta(seconds=backoff_seconds)
            logger.info(
                f"Recovery failed for {self.component_name}, retry in {backoff_seconds}s",
                extra={
                    "component": self.component_name,
                    "attempts": self.recovery_attempts,
                    "backoff_seconds": backoff_seconds
                }
            )
        else:
            self.next_retry_at = None
            logger.info(f"Recovery successful for {self.component_name}")


# ============================================================================
# CASCADING FAILURE PATTERN DETECTOR
# ============================================================================

class CascadingFailurePatternDetector:
    """
    Detecta patrones de fallos en cascada:
    - Fallos simultáneos de múltiples componentes
    - Fallos secuenciales (A falla → B falla → C falla)
    - Fallos que se repiten cíclicamente
    """
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.failure_history: List[Tuple[datetime, str]] = []
    
    def record_failure(self, component_name: str):
        """Registra un fallo"""
        self.failure_history.append((datetime.utcnow(), component_name))
        # Mantener solo últimos N eventos
        if len(self.failure_history) > self.window_size:
            self.failure_history = self.failure_history[-self.window_size:]
    
    def detect_simultaneous_failures(self, time_window_seconds: int = 10) -> Dict[str, int]:
        """
        Detecta fallos que ocurrieron simultáneamente.
        
        Returns:
            Dict con componentes y su frecuencia en ventanas de tiempo
        """
        if not self.failure_history:
            return {}
        
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window_seconds)
        
        simultaneous = {}
        for timestamp, component in self.failure_history:
            if timestamp > cutoff:
                simultaneous[component] = simultaneous.get(component, 0) + 1
        
        return simultaneous
    
    def detect_sequential_pattern(self) -> Optional[List[str]]:
        """
        Detecta si hay un patrón secuencial: A→B→C→A→...
        
        Returns:
            Patrón detectado o None
        """
        if len(self.failure_history) < 4:
            return None
        
        # Extraer componentes en orden
        recent = [c for _, c in self.failure_history[-10:]]
        
        # Buscar patrón repetido (e.g., [A, B, C, A, B, C])
        for pattern_length in range(1, 6):
            pattern = recent[:pattern_length]
            if len(recent) >= pattern_length * 2:
                # Verificar si el patrón se repite
                repeats = 0
                for i in range(pattern_length, len(recent), pattern_length):
                    chunk = recent[i:i+pattern_length]
                    if chunk == pattern:
                        repeats += 1
                
                if repeats >= 2:
                    logger.warning(
                        f"Cyclic failure pattern detected: {pattern}",
                        extra={"pattern": pattern, "repeats": repeats}
                    )
                    return pattern
        
        return None
    
    def get_critical_component(self) -> Optional[str]:
        """Identifica el componente que falla más frecuentemente"""
        if not self.failure_history:
            return None
        
        failure_counts = {}
        for _, component in self.failure_history:
            failure_counts[component] = failure_counts.get(component, 0) + 1
        
        return max(failure_counts, key=failure_counts.get) if failure_counts else None


# ============================================================================
# RECOVERY PREDICTOR
# ============================================================================

class RecoveryPredictor:
    """
    Predice si una recuperación será exitosa basándose en:
    - Tiempo desde el último fallo
    - Patrones históricos
    - Mejoras en métricas intermedias
    """
    
    def __init__(self):
        self.recovery_history: List[Dict] = []
    
    def record_recovery_attempt(self,
                               component: str,
                               was_successful: bool,
                               recovery_duration_seconds: float,
                               health_score_before: float,
                               health_score_after: float):
        """Registra un intento de recuperación para aprender"""
        self.recovery_history.append({
            'timestamp': datetime.utcnow(),
            'component': component,
            'was_successful': was_successful,
            'duration_seconds': recovery_duration_seconds,
            'health_before': health_score_before,
            'health_after': health_score_after
        })
        
        # Limitar histórico
        if len(self.recovery_history) > 100:
            self.recovery_history = self.recovery_history[-100:]
    
    def predict_recovery_success(self, 
                                component: str,
                                time_since_failure_seconds: float,
                                current_health_score: float) -> float:
        """
        Predice la probabilidad de éxito de recuperación (0.0-1.0).
        
        Args:
            component: Nombre del componente
            time_since_failure_seconds: Tiempo desde el último fallo
            current_health_score: Health score actual del componente
            
        Returns:
            Probabilidad de éxito (0.0-1.0)
        """
        # Factores base
        confidence = 0.0
        
        # Factor 1: Tiempo suficiente desde fallo
        if time_since_failure_seconds > 30:
            confidence += 0.3
        elif time_since_failure_seconds > 10:
            confidence += 0.15
        
        # Factor 2: Health score mejorado
        if current_health_score > 50:
            confidence += 0.3
        elif current_health_score > 30:
            confidence += 0.15
        
        # Factor 3: Histórico de recuperaciones exitosas
        successful_count = sum(
            1 for h in self.recovery_history[-10:]
            if h['component'].lower() == component.lower() and h['was_successful']
        )
        
        if successful_count >= 2:
            confidence += 0.2
        elif successful_count == 1:
            confidence += 0.1
        
        # Factor 4: Penalizar si hay intentos fallidos recientes
        failed_count = sum(
            1 for h in self.recovery_history[-5:]
            if h['component'].lower() == component.lower() and not h['was_successful']
        )
        
        confidence -= failed_count * 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_recovery_statistics(self, component: str) -> Dict:
        """Estadísticas de recuperación para un componente"""
        component_history = [
            h for h in self.recovery_history
            if h['component'].lower() == component.lower()
        ]
        
        if not component_history:
            return {'total_attempts': 0}
        
        successful = [h for h in component_history if h['was_successful']]
        durations = [h['duration_seconds'] for h in component_history]
        
        return {
            'total_attempts': len(component_history),
            'successful': len(successful),
            'failed': len(component_history) - len(successful),
            'success_rate': len(successful) / len(component_history) if component_history else 0,
            'avg_recovery_duration': statistics.mean(durations) if durations else 0,
            'min_recovery_duration': min(durations) if durations else 0,
            'max_recovery_duration': max(durations) if durations else 0
        }


# ============================================================================
# AUTO-RECOVERY LOOP ORCHESTRATOR
# ============================================================================

class AutoRecoveryLoop:
    """
    Orquesta todo el proceso de recuperación automática.
    Ejecuta en background con intervalo de 30 segundos.
    """
    
    def __init__(self, degradation_manager, health_aggregator):
        self.degradation_manager = degradation_manager
        self.health_aggregator = health_aggregator
        self.pattern_detector = CascadingFailurePatternDetector()
        self.recovery_predictor = RecoveryPredictor()
        self.recovery_checkpoints: Dict[str, RecoveryCheckpoint] = {}
        self.loop_running = False
        self.loop_iterations = 0
        self.last_evaluation_time: Optional[datetime] = None
        self.evaluation_interval_seconds = 30
    
    async def run(self):
        """Loop principal de recuperación (30s interval)"""
        logger.info("Auto-recovery loop started (30s interval)")
        self.loop_running = True
        
        while self.loop_running:
            try:
                await self._execute_recovery_cycle()
                self.last_evaluation_time = datetime.utcnow()
                self.loop_iterations += 1
            except Exception as e:
                logger.error(f"Recovery cycle error: {e}", exc_info=True)
            
            await asyncio.sleep(self.evaluation_interval_seconds)
    
    async def _execute_recovery_cycle(self):
        """Una iteración completa del ciclo de recuperación"""
        
        # Paso 1: Evaluar health actual
        current_level = await self.degradation_manager.evaluate_health()
        current_score = self.degradation_manager.calculate_overall_health_score()
        
        # Paso 2: Si está degradado, intentar recuperación
        if current_level.value > 1:  # No es OPTIMAL
            await self._attempt_recovery_for_degraded_level(current_level, current_score)
        
        # Paso 3: Detectar patrones de cascada
        simultaneous = self.pattern_detector.detect_simultaneous_failures()
        cyclic = self.pattern_detector.detect_sequential_pattern()
        
        if cyclic:
            logger.warning(f"Cyclic failure pattern: {cyclic}")
        
        if simultaneous and len(simultaneous) > 1:
            logger.warning(
                f"Multiple simultaneous failures: {simultaneous}",
                extra={"simultaneous_failures": simultaneous}
            )
    
    async def _attempt_recovery_for_degraded_level(self, current_level, current_score: float):
        """Intenta recuperar componentes específicos basados en el nivel"""
        
        # Identificar componentes en fallo
        failing_components = self.health_aggregator.get_failing_components()
        
        for component in failing_components:
            # Obtener o crear checkpoint
            if component not in self.recovery_checkpoints:
                self.recovery_checkpoints[component] = RecoveryCheckpoint(
                    component_name=component,
                    failed_at=datetime.utcnow(),
                    last_check_at=datetime.utcnow()
                )
            
            checkpoint = self.recovery_checkpoints[component]
            
            # Verificar si debería reintentar
            if not checkpoint.should_retry():
                continue
            
            # Predecir probabilidad de éxito
            time_since_fail = (datetime.utcnow() - checkpoint.failed_at).total_seconds()
            success_prob = self.recovery_predictor.predict_recovery_success(
                component,
                time_since_fail,
                current_score
            )
            
            if success_prob > 0.5:  # Solo reintentar si hay buenas chances
                logger.info(
                    f"Attempting recovery for {component} (success_prob={success_prob:.0%})",
                    extra={
                        "component": component,
                        "success_probability": success_prob,
                        "time_since_failure": time_since_fail
                    }
                )
                
                start_time = datetime.utcnow()
                was_successful = await self._trigger_component_recovery(component)
                recovery_duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Registrar resultado
                checkpoint.record_attempt(was_successful)
                self.recovery_predictor.record_recovery_attempt(
                    component,
                    was_successful,
                    recovery_duration,
                    current_score,
                    self.degradation_manager.calculate_overall_health_score()
                )
                
                # Si se recuperó, remover checkpoint
                if was_successful:
                    del self.recovery_checkpoints[component]
    
    async def _trigger_component_recovery(self, component_name: str) -> bool:
        """
        Intenta recuperar un componente específico.
        En implementación real, aquí se resetearían circuit breakers.
        """
        # Placeholder: simular intento de recuperación
        # En DÍA 3 se integraría con los CBs reales
        logger.debug(f"Triggering recovery for {component_name}")
        return True
    
    def stop(self):
        """Detiene el loop"""
        self.loop_running = False
        logger.info("Auto-recovery loop stopped")
    
    def get_status(self) -> Dict:
        """Retorna status del loop"""
        return {
            'running': self.loop_running,
            'iterations': self.loop_iterations,
            'last_evaluation': self.last_evaluation_time.isoformat() if self.last_evaluation_time else None,
            'active_recovery_checkpoints': len(self.recovery_checkpoints),
            'checkpoints': {
                name: {
                    'failed_at': cp.failed_at.isoformat(),
                    'recovery_attempts': cp.recovery_attempts,
                    'next_retry': cp.next_retry_at.isoformat() if cp.next_retry_at else None
                }
                for name, cp in self.recovery_checkpoints.items()
            },
            'cyclic_pattern': self.pattern_detector.detect_sequential_pattern(),
            'critical_component': self.pattern_detector.get_critical_component()
        }
