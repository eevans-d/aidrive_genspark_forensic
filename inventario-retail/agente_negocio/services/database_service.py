"""
Database Service - Servicio de BD con Circuit Breaker

Módulo que encapsula todas las operaciones de base de datos con protección
mediante circuit breaker para evitar cascading failures cuando la DB está
caída o sobrecargada.

Features:
- Circuit breaker con fallback automático
- Prometheus metrics para monitoreo
- Structured logging con request_id
- Graceful degradation (read-only mode)
- Connection pooling protection

Author: Operations Team
Date: October 19, 2025
Part of: DÍA 1 Implementation (OPCIÓN C - Resilience Hardening)
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.circuit_breakers import db_breaker
from shared.fallbacks import db_read_fallback, db_write_fallback
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

db_queries = Counter(
    'agente_negocio_db_queries_total',
    'Total database queries',
    ['operation', 'status']  # status: success, fallback, error
)

db_query_latency = Histogram(
    'agente_negocio_db_query_latency_seconds',
    'Database query latency',
    ['operation']
)

db_connection_pool_size = Gauge(
    'agente_negocio_db_pool_size',
    'Current database connection pool size'
)

db_breaker_state = Gauge(
    'agente_negocio_db_breaker_state',
    'Database circuit breaker state (0=closed, 1=open, 2=half-open)'
)

db_write_mode = Gauge(
    'agente_negocio_db_write_mode_enabled',
    'Database write mode enabled (1) or read-only (0)'
)


# ============================================================================
# DATABASE SERVICE CLASS
# ============================================================================

class DatabaseService:
    """
    Servicio centralizado para operaciones de base de datos.
    
    Características:
    - Protección con circuit breaker (3 fallos → abre)
    - Fallbacks automáticos para read/write
    - Metricas de Prometheus
    - Logging estructurado
    - Read-only mode cuando la DB tiene problemas
    
    Ejemplo:
        service = DatabaseService()
        result = await service.read_query(
            "SELECT * FROM items WHERE id = %s",
            (item_id,)
        )
        if result['success']:
            items = result['data']
        else:
            # Usar fallback (cache o mensaje)
            items = result['fallback']
    """
    
    def __init__(self, db_connection=None):
        """
        Inicializar el servicio de base de datos.
        
        Args:
            db_connection: Conexión a BD (inyectable para testing)
        """
        self.db_connection = db_connection
        self.write_mode_enabled = True  # True = writes allowed, False = read-only
        self.readonly_reason = None
        
    @db_breaker
    async def read_query(
        self,
        query: str,
        params: tuple = (),
        request_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Ejecutar query READ con protección de circuit breaker.
        
        Args:
            query: SQL query con placeholders %s
            params: Tupla de parámetros
            request_id: ID de request para logging
            timeout: Timeout en segundos
            
        Returns:
            Dict con 'success', 'data' (resultados), 'breaker_state', 'latency'
        """
        operation = "read_query"
        start_time = datetime.now()
        
        try:
            logger.debug(
                f"[{operation}] Ejecutando: {query[:50]}...",
                extra={"request_id": request_id}
            )
            
            # Update breaker state metric
            self._update_breaker_state()
            
            # Ejecutar query
            # TODO: DÍA 1 - PASO 2: Implementar llamada real a BD
            # En producción, usar: cursor = self.db_connection.cursor()
            
            results = [
                {'id': 1, 'name': 'Product 1', 'price': 100.0},
                {'id': 2, 'name': 'Product 2', 'price': 200.0},
            ]
            
            latency = (datetime.now() - start_time).total_seconds()
            db_query_latency.labels(operation=operation).observe(latency)
            db_queries.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Query exitosa",
                extra={
                    "request_id": request_id,
                    "latency": latency,
                    "rows": len(results)
                }
            )
            
            return {
                'success': True,
                'data': results,
                'breaker_state': db_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            # Circuit breaker abierto o error → usar fallback
            latency = (datetime.now() - start_time).total_seconds()
            fallback_result = db_read_fallback(query, params)
            
            logger.warning(
                f"[{operation}] Usando fallback - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency,
                    "breaker_state": db_breaker.current_state
                }
            )
            
            db_queries.labels(operation=operation, status="fallback").inc()
            
            return {
                'success': False,
                'data': fallback_result,
                'fallback': True,
                'breaker_state': db_breaker.current_state,
                'latency': latency,
                'error': str(e)
            }
    
    @db_breaker
    async def write_query(
        self,
        query: str,
        params: tuple = (),
        request_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Ejecutar query WRITE (INSERT/UPDATE/DELETE) con protección.
        
        Características:
        - Verifica si write_mode está habilitado
        - Bloquea writes si la BD tiene problemas (graceful degradation)
        - Fallback bloquea la operación (no ejecuta fallback)
        
        Args:
            query: SQL query con placeholders %s
            params: Tupla de parámetros
            request_id: ID de request para logging
            timeout: Timeout en segundos
            
        Returns:
            Dict con 'success', 'rows_affected', 'breaker_state', 'latency'
        """
        operation = "write_query"
        start_time = datetime.now()
        
        # Verificar si write_mode está habilitado
        if not self.write_mode_enabled:
            logger.warning(
                f"[{operation}] Escriba bloqueada - BD en read-only mode",
                extra={
                    "request_id": request_id,
                    "reason": self.readonly_reason,
                    "query": query[:50]
                }
            )
            
            return {
                'success': False,
                'error': 'Database in read-only mode',
                'reason': self.readonly_reason,
                'breaker_state': db_breaker.current_state,
                'fallback': True
            }
        
        try:
            logger.debug(
                f"[{operation}] Ejecutando: {query[:50]}...",
                extra={"request_id": request_id}
            )
            
            self._update_breaker_state()
            
            # Ejecutar query
            # TODO: DÍA 1 - PASO 2: Implementar llamada real a BD
            
            rows_affected = 1
            
            latency = (datetime.now() - start_time).total_seconds()
            db_query_latency.labels(operation=operation).observe(latency)
            db_queries.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Escriba exitosa",
                extra={
                    "request_id": request_id,
                    "latency": latency,
                    "rows_affected": rows_affected
                }
            )
            
            return {
                'success': True,
                'rows_affected': rows_affected,
                'breaker_state': db_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            # Escriba falló → bloquear futuras escritas
            latency = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"[{operation}] Escriba falló - activando read-only mode",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency,
                    "breaker_state": db_breaker.current_state
                }
            )
            
            # Activar read-only mode
            self._activate_readonly_mode(str(e))
            
            db_queries.labels(operation=operation, status="error").inc()
            
            return {
                'success': False,
                'error': str(e),
                'breaker_state': db_breaker.current_state,
                'latency': latency,
                'readonly_mode_activated': True
            }
    
    async def transaction(
        self,
        operations: List[Dict[str, Any]],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecutar transacción (múltiples queries atómicas).
        
        Args:
            operations: Lista de dicts con {'query': str, 'params': tuple}
            request_id: ID de request para logging
            
        Returns:
            Dict con 'success', 'results', 'breaker_state'
        """
        operation = "transaction"
        start_time = datetime.now()
        
        if not self.write_mode_enabled:
            logger.warning(
                f"[{operation}] Transacción bloqueada - BD en read-only",
                extra={"request_id": request_id}
            )
            
            return {
                'success': False,
                'error': 'Database in read-only mode',
                'fallback': True
            }
        
        try:
            logger.info(
                f"[{operation}] Iniciando transacción con {len(operations)} operaciones",
                extra={"request_id": request_id}
            )
            
            results = []
            for op in operations:
                # Ejecutar cada operación
                result = await self.write_query(
                    op['query'],
                    op.get('params', ()),
                    request_id
                )
                if not result['success']:
                    # Si alguna falla, rollback
                    raise Exception(f"Operation failed: {op['query']}")
                results.append(result)
            
            latency = (datetime.now() - start_time).total_seconds()
            db_query_latency.labels(operation=operation).observe(latency)
            db_queries.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Transacción completada",
                extra={
                    "request_id": request_id,
                    "operations": len(results),
                    "latency": latency
                }
            )
            
            return {
                'success': True,
                'results': results,
                'breaker_state': db_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"[{operation}] Transacción falló",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency
                }
            )
            
            self._activate_readonly_mode(str(e))
            
            db_queries.labels(operation=operation, status="error").inc()
            
            return {
                'success': False,
                'error': str(e),
                'breaker_state': db_breaker.current_state,
                'latency': latency,
                'readonly_mode_activated': True
            }
    
    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================
    
    def _update_breaker_state(self):
        """Actualizar métrica de estado del circuit breaker"""
        state_map = {
            'closed': 0,
            'open': 1,
            'half-open': 2
        }
        current = db_breaker.current_state
        db_breaker_state.set(state_map.get(current, 0))
    
    def _activate_readonly_mode(self, reason: str):
        """Activar modo read-only en caso de fallos de escritura"""
        self.write_mode_enabled = False
        self.readonly_reason = reason
        db_write_mode.set(0)
        
        logger.error(
            f"🔴 DATABASE EN READ-ONLY MODE - Razón: {reason}",
            extra={"timestamp": datetime.now().isoformat()}
        )
    
    def _deactivate_readonly_mode(self):
        """Desactivar modo read-only cuando la BD se recupera"""
        self.write_mode_enabled = True
        self.readonly_reason = None
        db_write_mode.set(1)
        
        logger.info(
            f"🟢 DATABASE RECOVERED - Escribas habilitadas",
            extra={"timestamp": datetime.now().isoformat()}
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado del servicio de BD.
        
        Returns:
            Dict con breaker state, write mode, connection pool, etc.
        """
        return {
            'breaker_state': db_breaker.current_state,
            'fail_counter': db_breaker.fail_counter,
            'fail_max': db_breaker.fail_max,
            'write_mode_enabled': self.write_mode_enabled,
            'readonly_reason': self.readonly_reason
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_db_service_instance = None

def get_database_service(db_connection=None) -> DatabaseService:
    """
    Obtener instancia singleton del servicio de BD.
    
    Uso en FastAPI:
        from .services.database_service import get_database_service
        
        @app.get("/items")
        async def get_items(request_id: str):
            service = get_database_service()
            result = await service.read_query(
                "SELECT * FROM items",
                request_id=request_id
            )
            return result
    """
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DatabaseService(db_connection)
    return _db_service_instance


# ============================================================================
# HEALTH CHECK
# ============================================================================

async def check_database_health() -> Dict[str, Any]:
    """
    Health check para Database service.
    
    Retorna estado del circuit breaker sin hacer queries reales.
    """
    service = get_database_service()
    
    return {
        'service': 'database',
        'status': 'healthy' if db_breaker.current_state != 'open' else 'degraded',
        'breaker_state': db_breaker.current_state,
        'write_mode': 'enabled' if service.write_mode_enabled else 'disabled',
        'readonly_reason': service.readonly_reason,
        'fail_counter': db_breaker.fail_counter,
        'fail_max': db_breaker.fail_max
    }
