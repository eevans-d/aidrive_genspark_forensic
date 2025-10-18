"""
Circuit Breakers Module - Implementación de Circuit Breakers para Resiliencia

Este módulo implementa circuit breakers para proteger el sistema contra cascading
failures cuando las dependencias externas fallan.

Uso:
    from shared.circuit_breakers import openai_breaker, db_breaker, redis_breaker
    
    @openai_breaker
    async def call_openai_api(prompt: str):
        # Tu código aquí
        pass

Author: Operations Team
Date: October 18, 2025
Part of: OPCIÓN C Implementation (Resilience Hardening)
"""

from pybreaker import CircuitBreaker
import logging
from typing import Callable, Any
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['breaker_name']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total failures detected by circuit breaker',
    ['breaker_name']
)

circuit_breaker_fallback_calls = Counter(
    'circuit_breaker_fallback_calls_total',
    'Total fallback calls when circuit is open',
    ['breaker_name']
)


# ============================================================================
# CIRCUIT BREAKER LISTENER
# ============================================================================

def circuit_breaker_listener(breaker: CircuitBreaker, state_change: str):
    """
    Listener para capturar cambios de estado del circuit breaker.
    
    Args:
        breaker: Instancia del circuit breaker
        state_change: Nuevo estado ('open', 'half-open', 'closed')
    """
    logger.warning(
        f"Circuit breaker '{breaker.name}' state change → {state_change}",
        extra={
            "breaker_name": breaker.name,
            "new_state": state_change,
            "fail_counter": breaker.fail_counter,
            "fail_max": breaker.fail_max
        }
    )
    
    # Update Prometheus metric
    state_map = {
        'closed': 0,
        'open': 1,
        'half-open': 2
    }
    circuit_breaker_state.labels(breaker_name=breaker.name).set(
        state_map.get(state_change, 0)
    )


# ============================================================================
# OPENAI API CIRCUIT BREAKER
# ============================================================================

openai_breaker = CircuitBreaker(
    fail_max=5,              # 5 fallos consecutivos para abrir
    reset_timeout=60,        # 60 segundos antes de intentar half-open (recuperación)
    name="openai_api",
    listeners=[circuit_breaker_listener]
)


# ============================================================================
# POSTGRESQL CIRCUIT BREAKER
# ============================================================================

db_breaker = CircuitBreaker(
    fail_max=3,              # 3 fallos → crítico (DB es más crítico)
    reset_timeout=30,        # 30 segundos recovery
    name="postgresql",
    listeners=[circuit_breaker_listener]
)


# ============================================================================
# REDIS CIRCUIT BREAKER
# ============================================================================

redis_breaker = CircuitBreaker(
    fail_max=5,              # 5 fallos para abrir
    reset_timeout=20,        # Redis recovery rápido
    name="redis_cache",
    listeners=[circuit_breaker_listener]
)


# ============================================================================
# S3 STORAGE CIRCUIT BREAKER
# ============================================================================

s3_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="s3_storage",
    listeners=[circuit_breaker_listener]
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_breakers() -> dict[str, CircuitBreaker]:
    """
    Retorna diccionario con todos los circuit breakers configurados.
    
    Returns:
        Dict con nombre → instancia de circuit breaker
    """
    return {
        'openai_api': openai_breaker,
        'postgresql': db_breaker,
        'redis_cache': redis_breaker,
        's3_storage': s3_breaker
    }


def get_breaker_status() -> dict[str, dict[str, Any]]:
    """
    Obtiene status de todos los circuit breakers.
    
    Returns:
        Dict con status detallado de cada breaker
    """
    breakers = get_all_breakers()
    status = {}
    
    for name, breaker in breakers.items():
        status[name] = {
            'state': breaker.current_state,
            'fail_counter': breaker.fail_counter,
            'fail_max': breaker.fail_max,
            'timeout_duration': breaker.timeout_duration,
            'opened_at': getattr(breaker, '_opened_at', None)
        }
    
    return status


def reset_all_breakers():
    """
    Reset manual de todos los circuit breakers.
    Usar solo en emergencias o después de fixes.
    """
    breakers = get_all_breakers()
    for name, breaker in breakers.items():
        try:
            breaker.call(lambda: None)  # Reset internal state
            logger.info(f"Circuit breaker '{name}' reset exitosamente")
        except Exception as e:
            logger.error(f"Error resetting breaker '{name}': {e}")


# ============================================================================
# DECORATOR HELPER
# ============================================================================

def with_fallback(fallback_func: Callable):
    """
    Decorator helper para agregar fallback automático a funciones.
    
    Uso:
        @openai_breaker
        @with_fallback(lambda *args, **kwargs: {"status": "fallback"})
        async def my_function():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Función {func.__name__} falló, usando fallback",
                    extra={"error": str(e)}
                )
                circuit_breaker_fallback_calls.labels(
                    breaker_name=func.__name__
                ).inc()
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

"""
EJEMPLO 1: Proteger llamada a OpenAI API

from shared.circuit_breakers import openai_breaker

@openai_breaker
async def call_openai_api(prompt: str):
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        timeout=120
    )
    return response.choices[0].message.content


EJEMPLO 2: Con fallback automático

@openai_breaker
@with_fallback(lambda prompt: {"response": "Sistema degradado", "status": "fallback"})
async def call_openai_with_fallback(prompt: str):
    # ... código
    pass


EJEMPLO 3: Proteger queries a DB

from shared.circuit_breakers import db_breaker

@db_breaker
async def get_inventory_from_db(item_id: str):
    async with get_db_session() as session:
        result = await session.execute(
            select(Item).where(Item.id == item_id)
        )
        return result.scalar_one_or_none()


EJEMPLO 4: Verificar status de breakers

from shared.circuit_breakers import get_breaker_status

@app.get("/health/breakers")
async def breakers_health():
    return get_breaker_status()
"""

# ============================================================================
# TODO: IMPLEMENTACIÓN DÍA 1-2
# ============================================================================

"""
DÍA 1: Setup + OpenAI + DB
  [x] Instalar pybreaker: pip install pybreaker==1.0.1
  [ ] Crear este módulo (circuit_breakers.py)
  [ ] Implementar OpenAI breaker en agente_negocio/services/openai_service.py
  [ ] Implementar DB breaker en shared/database.py
  [ ] Tests unitarios en tests/test_circuit_breakers.py
  [ ] Configurar métricas Prometheus

DÍA 2: Redis + S3 + Integration
  [ ] Implementar Redis breaker en shared/cache.py
  [ ] Implementar S3 breaker (si aplicable)
  [ ] Integration tests
  [ ] Deploy to staging
  [ ] Smoke tests con breakers activos
  [ ] Documentation en docs/CIRCUIT_BREAKERS.md
"""
