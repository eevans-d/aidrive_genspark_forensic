"""
Degradation Manager - Sistema de Degradación por Niveles

Este módulo implementa un sistema de degradación graceful que permite al sistema
mantener funcionalidad reducida cuando las dependencias fallan.

Niveles de Degradación:
    NIVEL 1 (OPTIMAL):     100% funcionalidad - Todos los servicios operativos
    NIVEL 2 (DEGRADED):    85% funcionalidad - Cache down, bypass a DB
    NIVEL 3 (LIMITED):     60% funcionalidad - OpenAI down, features AI disabled
    NIVEL 4 (MINIMAL):     30% funcionalidad - DB read-only, solo consultas críticas
    NIVEL 5 (EMERGENCY):   10% funcionalidad - Status page only

Uso:
    from shared.degradation_manager import degradation_manager, DegradationLevel
    
    current_level = degradation_manager.current_level
    if current_level >= DegradationLevel.LIMITED:
        # Usar funcionalidad básica
        pass

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation (Resilience Hardening)
"""

from enum import Enum
from typing import Dict, Callable, Optional, Any
import asyncio
import logging
from datetime import datetime
from prometheus_client import Gauge, Counter

logger = logging.getLogger(__name__)


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

degradation_level_gauge = Gauge(
    'degradation_level',
    'Current system degradation level (1=optimal, 5=emergency)',
    ['level_name']
)

degradation_transitions_counter = Counter(
    'degradation_transitions_total',
    'Total degradation level transitions',
    ['from_level', 'to_level']
)


# ============================================================================
# DEGRADATION LEVELS ENUM
# ============================================================================

class DegradationLevel(Enum):
    """
    Niveles de degradación del sistema.
    Valores más altos = mayor degradación
    """
    OPTIMAL = 1      # 100% funcionalidad
    DEGRADED = 2     # 85% funcionalidad (cache down)
    LIMITED = 3      # 60% funcionalidad (OpenAI down)
    MINIMAL = 4      # 30% funcionalidad (DB problemas)
    EMERGENCY = 5    # 10% funcionalidad (múltiples fallos)
    
    def __lt__(self, other):
        if isinstance(other, DegradationLevel):
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, DegradationLevel):
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, DegradationLevel):
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if isinstance(other, DegradationLevel):
            return self.value >= other.value
        return NotImplemented


# ============================================================================
# DEGRADATION MANAGER CLASS
# ============================================================================

class DegradationManager:
    """
    Gestiona el nivel de degradación del sistema basado en health de dependencias.
    """
    
    def __init__(self):
        self.current_level = DegradationLevel.OPTIMAL
        self.health_checks: Dict[str, Callable] = {}
        self.level_transitions: Dict[DegradationLevel, Callable] = {}
        self._last_check_time: Optional[datetime] = None
        self._check_interval = 30  # segundos
        self._transition_history = []
        
    async def register_health_check(self, name: str, check_func: Callable):
        """
        Registra una función de health check.
        
        Args:
            name: Nombre del componente (redis, db, openai, etc.)
            check_func: Función async que retorna bool (True = healthy)
        """
        self.health_checks[name] = check_func
        logger.info(f"Health check registrado: {name}")
    
    async def register_transition_handler(
        self, 
        level: DegradationLevel, 
        handler: Callable
    ):
        """
        Registra un handler que se ejecuta al transicionar a un nivel.
        
        Args:
            level: Nivel de degradación
            handler: Función async a ejecutar en la transición
        """
        self.level_transitions[level] = handler
        logger.info(f"Transition handler registrado para nivel: {level.name}")
    
    async def _check_redis(self) -> bool:
        """Health check para Redis"""
        try:
            # TODO DÍA 3: Implementar check real
            # from shared.cache import get_redis_client
            # redis = await get_redis_client()
            # await redis.ping()
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def _check_database(self) -> bool:
        """Health check para PostgreSQL"""
        try:
            # TODO DÍA 3: Implementar check real
            # from shared.database import get_db_session
            # async with get_db_session() as session:
            #     await session.execute("SELECT 1")
            return True  # Placeholder
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _check_openai(self) -> bool:
        """Health check para OpenAI API"""
        try:
            # TODO DÍA 3: Implementar check real
            # Puede verificar circuit breaker state
            from shared.circuit_breakers import openai_breaker
            return openai_breaker.current_state != 'open'
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    async def evaluate_health(self) -> DegradationLevel:
        """
        Evalúa el health del sistema y determina el nivel de degradación apropiado.
        
        Returns:
            Nivel de degradación apropiado basado en health checks
        """
        health_status = {}
        
        # Ejecutar health checks registrados
        for name, check_func in self.health_checks.items():
            try:
                health_status[name] = await check_func()
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")
                health_status[name] = False
        
        # Checks por defecto si no hay registrados
        if not health_status:
            health_status = {
                'redis': await self._check_redis(),
                'database': await self._check_database(),
                'openai': await self._check_openai()
            }
        
        # Determinar nivel basado en health
        return self._calculate_degradation_level(health_status)
    
    def _calculate_degradation_level(
        self, 
        health_status: Dict[str, bool]
    ) -> DegradationLevel:
        """
        Calcula el nivel de degradación basado en el status de los componentes.
        
        Args:
            health_status: Dict con status de cada componente
            
        Returns:
            Nivel de degradación calculado
        """
        redis_ok = health_status.get('redis', True)
        db_ok = health_status.get('database', True)
        openai_ok = health_status.get('openai', True)
        
        # Lógica de decisión
        if all(health_status.values()):
            return DegradationLevel.OPTIMAL
        
        elif not redis_ok and db_ok and openai_ok:
            # Solo cache down → DEGRADED
            return DegradationLevel.DEGRADED
        
        elif not openai_ok and db_ok:
            # OpenAI down, DB ok → LIMITED
            return DegradationLevel.LIMITED
        
        elif not db_ok:
            # DB problemas → MINIMAL o EMERGENCY
            if redis_ok or openai_ok:
                return DegradationLevel.MINIMAL
            else:
                return DegradationLevel.EMERGENCY
        
        else:
            # Múltiples problemas → LIMITED
            return DegradationLevel.LIMITED
    
    async def set_level(self, new_level: DegradationLevel):
        """
        Transiciona a un nuevo nivel de degradación.
        
        Args:
            new_level: Nuevo nivel de degradación
        """
        if new_level == self.current_level:
            return
        
        old_level = self.current_level
        
        logger.warning(
            f"Degradation level change: {old_level.name} → {new_level.name}",
            extra={
                "old_level": old_level.value,
                "old_level_name": old_level.name,
                "new_level": new_level.value,
                "new_level_name": new_level.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Ejecutar transition handler si existe
        if new_level in self.level_transitions:
            try:
                await self.level_transitions[new_level]()
            except Exception as e:
                logger.error(f"Transition handler error for {new_level.name}: {e}")
        
        # Actualizar nivel actual
        self.current_level = new_level
        
        # Guardar en historial
        self._transition_history.append({
            'timestamp': datetime.utcnow(),
            'from_level': old_level,
            'to_level': new_level
        })
        
        # Limitar historial a últimas 100 transiciones
        if len(self._transition_history) > 100:
            self._transition_history = self._transition_history[-100:]
        
        # Update metrics
        degradation_level_gauge.labels(level_name=new_level.name).set(new_level.value)
        degradation_transitions_counter.labels(
            from_level=old_level.name,
            to_level=new_level.name
        ).inc()
    
    async def auto_recovery_loop(self):
        """
        Loop continuo que evalúa health y ajusta nivel automáticamente.
        Debe ejecutarse como background task en el startup de la app.
        """
        logger.info("Auto-recovery loop iniciado")
        
        while True:
            try:
                # Evaluar health actual
                new_level = await self.evaluate_health()
                
                # Auto-upgrade si el health mejoró
                if new_level.value < self.current_level.value:
                    logger.info(
                        f"Auto-recovery: upgrading from {self.current_level.name} "
                        f"to {new_level.name}"
                    )
                    await self.set_level(new_level)
                
                # Auto-downgrade si el health empeoró
                elif new_level.value > self.current_level.value:
                    logger.warning(
                        f"Auto-degradation: downgrading from {self.current_level.name} "
                        f"to {new_level.name}"
                    )
                    await self.set_level(new_level)
                
                self._last_check_time = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Auto-recovery loop error: {e}", exc_info=True)
            
            # Esperar intervalo configurado
            await asyncio.sleep(self._check_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status completo del degradation manager.
        
        Returns:
            Dict con nivel actual, historial, last check time
        """
        return {
            'current_level': self.current_level.value,
            'current_level_name': self.current_level.name,
            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
            'check_interval_seconds': self._check_interval,
            'transition_history': [
                {
                    'timestamp': t['timestamp'].isoformat(),
                    'from_level': t['from_level'].name,
                    'to_level': t['to_level'].name
                }
                for t in self._transition_history[-10:]  # Últimas 10
            ],
            'health_checks_registered': list(self.health_checks.keys())
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

degradation_manager = DegradationManager()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_feature_available(feature: str) -> bool:
    """
    Verifica si una feature está disponible en el nivel actual de degradación.
    
    Args:
        feature: Nombre de la feature a verificar
        
    Returns:
        True si la feature está disponible, False si no
    """
    current_level = degradation_manager.current_level
    
    # Feature availability matrix
    feature_matrix = {
        'cache': DegradationLevel.OPTIMAL,
        'openai_api': DegradationLevel.LIMITED,
        'write_operations': DegradationLevel.MINIMAL,
        'complex_queries': DegradationLevel.MINIMAL,
        'ai_enhancement': DegradationLevel.LIMITED,
        'recommendations': DegradationLevel.LIMITED,
    }
    
    required_level = feature_matrix.get(feature, DegradationLevel.OPTIMAL)
    return current_level < required_level


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

"""
EJEMPLO 1: Verificar nivel en un endpoint

from shared.degradation_manager import degradation_manager, DegradationLevel

@app.get("/api/inventory/{item_id}")
async def get_inventory(item_id: str):
    current_level = degradation_manager.current_level
    
    if current_level == DegradationLevel.OPTIMAL:
        # Full pipeline: cache → AI enhancement → DB
        return await get_inventory_optimal(item_id)
    
    elif current_level == DegradationLevel.DEGRADED:
        # Bypass cache, direct DB
        return await get_inventory_from_db(item_id)
    
    elif current_level >= DegradationLevel.LIMITED:
        # Basic read-only
        return await get_inventory_basic(item_id)


EJEMPLO 2: Registrar health check custom

async def check_external_api():
    try:
        response = await httpx.get("https://api.example.com/health")
        return response.status_code == 200
    except:
        return False

await degradation_manager.register_health_check(
    'external_api',
    check_external_api
)


EJEMPLO 3: Iniciar auto-recovery loop en FastAPI

from shared.degradation_manager import degradation_manager

@app.on_event("startup")
async def start_auto_recovery():
    asyncio.create_task(degradation_manager.auto_recovery_loop())


EJEMPLO 4: Endpoint de status

@app.get("/health/degradation")
async def degradation_status():
    return degradation_manager.get_status()
"""

# ============================================================================
# TODO: IMPLEMENTACIÓN DÍA 3-5
# ============================================================================

"""
DÍA 3: Degradation Manager + Levels 1-2
  [ ] Crear este módulo (degradation_manager.py)
  [ ] Implementar DegradationManager class
  [ ] Implementar health checks básicos
  [ ] Implementar NIVEL 1 (OPTIMAL) logic
  [ ] Implementar NIVEL 2 (DEGRADED) logic
  [ ] Tests unitarios
  [ ] Métricas Prometheus

DÍA 4: Levels 3-4 + Auto-Recovery
  [ ] Implementar NIVEL 3 (LIMITED) logic
  [ ] Implementar NIVEL 4 (MINIMAL) logic
  [ ] Implementar auto_recovery_loop()
  [ ] Integration tests con circuit breakers
  [ ] Dashboard Grafana para degradation levels
  [ ] Alertas para degradation events

DÍA 5: Integration + Deployment
  [ ] End-to-end testing
  [ ] Deploy to staging
  [ ] Smoke tests
  [ ] Documentation completa
"""
