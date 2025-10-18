"""
OpenAI Service - Servicio de IA con Circuit Breaker

Módulo que encapsula todas las llamadas a OpenAI con protección mediante
circuit breaker para evitar cascading failures cuando OpenAI está caído.

Features:
- Circuit breaker con fallback automático
- Prometheus metrics para monitoreo
- Structured logging con request_id
- Graceful degradation en caso de fallos

Author: Operations Team
Date: October 18, 2025
Part of: DÍA 1 Implementation (OPCIÓN C - Resilience Hardening)
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.circuit_breakers import openai_breaker
from shared.fallbacks import openai_fallback, openai_pricing_fallback, openai_ocr_enhancement_fallback
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

openai_api_calls = Counter(
    'agente_negocio_openai_calls_total',
    'Total OpenAI API calls',
    ['operation', 'status']  # status: success, fallback, error
)

openai_api_latency = Histogram(
    'agente_negocio_openai_latency_seconds',
    'OpenAI API call latency',
    ['operation']
)

openai_breaker_state = Gauge(
    'agente_negocio_openai_breaker_state',
    'OpenAI circuit breaker state (0=closed, 1=open, 2=half-open)'
)


# ============================================================================
# OPENAI SERVICE CLASS
# ============================================================================

class OpenAIService:
    """
    Servicio centralizado para todas las operaciones de OpenAI.
    
    Características:
    - Protección con circuit breaker
    - Fallbacks automáticos
    - Prometheus metrics
    - Logging estructurado
    
    Ejemplo:
        service = OpenAIService()
        result = await service.enhance_ocr_text(raw_text)
        if result['success']:
            enhanced_text = result['data']
        else:
            # Usar fallback
            enhanced_text = result['fallback']
    """
    
    def __init__(self):
        """Inicializar el servicio OpenAI"""
        self.api_key = os.getenv('OPENAI_API_KEY', 'test-key')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.timeout = int(os.getenv('OPENAI_TIMEOUT', '30'))
        
    async def enhance_ocr_text(
        self,
        raw_ocr_text: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mejorar texto OCR usando OpenAI.
        
        Args:
            raw_ocr_text: Texto crudo del OCR
            request_id: ID de request para logging
            
        Returns:
            Dict con 'success', 'data' (enhanced text o fallback), y 'breaker_state'
        """
        operation = "enhance_ocr"
        start_time = datetime.now()
        
        try:
            logger.info(
                f"[{operation}] Iniciando enhancement de OCR",
                extra={"request_id": request_id, "text_length": len(raw_ocr_text)}
            )
            
            # Update breaker state metric
            self._update_breaker_state()
            
            # Llamar a OpenAI con circuit breaker
            result = await self._call_openai_with_breaker(
                operation=operation,
                prompt=self._build_ocr_enhancement_prompt(raw_ocr_text),
                request_id=request_id
            )
            
            latency = (datetime.now() - start_time).total_seconds()
            openai_api_latency.labels(operation=operation).observe(latency)
            openai_api_calls.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Enhancement exitoso",
                extra={
                    "request_id": request_id,
                    "latency": latency,
                    "result_length": len(result.get('content', ''))
                }
            )
            
            return {
                'success': True,
                'data': result.get('content', ''),
                'breaker_state': openai_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            # Circuit breaker abierto o error → usar fallback
            latency = (datetime.now() - start_time).total_seconds()
            fallback_result = openai_ocr_enhancement_fallback(raw_ocr_text)
            
            logger.warning(
                f"[{operation}] Usando fallback - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency,
                    "breaker_state": openai_breaker.current_state
                }
            )
            
            openai_api_calls.labels(operation=operation, status="fallback").inc()
            
            return {
                'success': False,
                'data': fallback_result,
                'fallback': True,
                'breaker_state': openai_breaker.current_state,
                'latency': latency,
                'error': str(e)
            }
    
    async def generate_pricing(
        self,
        item_data: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generar pricing usando OpenAI para análisis inteligente.
        
        Args:
            item_data: Datos del item (name, cost, category, etc.)
            request_id: ID de request para logging
            
        Returns:
            Dict con 'success', 'pricing' (o fallback), y 'breaker_state'
        """
        operation = "generate_pricing"
        start_time = datetime.now()
        
        try:
            logger.info(
                f"[{operation}] Iniciando generación de pricing",
                extra={"request_id": request_id, "item_id": item_data.get('id')}
            )
            
            self._update_breaker_state()
            
            # Llamar a OpenAI con circuit breaker
            result = await self._call_openai_with_breaker(
                operation=operation,
                prompt=self._build_pricing_prompt(item_data),
                request_id=request_id
            )
            
            # Parse resultado
            pricing = self._parse_pricing_response(result.get('content', ''))
            
            latency = (datetime.now() - start_time).total_seconds()
            openai_api_latency.labels(operation=operation).observe(latency)
            openai_api_calls.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Pricing generado",
                extra={
                    "request_id": request_id,
                    "latency": latency,
                    "suggested_price": pricing.get('price')
                }
            )
            
            return {
                'success': True,
                'pricing': pricing,
                'breaker_state': openai_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            # Circuit breaker abierto o error → usar fallback
            latency = (datetime.now() - start_time).total_seconds()
            fallback_pricing = openai_pricing_fallback(item_data)
            
            logger.warning(
                f"[{operation}] Usando fallback pricing - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency,
                    "breaker_state": openai_breaker.current_state
                }
            )
            
            openai_api_calls.labels(operation=operation, status="fallback").inc()
            
            return {
                'success': False,
                'pricing': fallback_pricing,
                'fallback': True,
                'breaker_state': openai_breaker.current_state,
                'latency': latency,
                'error': str(e)
            }
    
    async def analyze_invoice(
        self,
        invoice_text: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizar factura usando OpenAI para extracción de datos.
        
        Args:
            invoice_text: Texto de la factura
            request_id: ID de request para logging
            
        Returns:
            Dict con 'success', 'analysis' (o fallback), y 'breaker_state'
        """
        operation = "analyze_invoice"
        start_time = datetime.now()
        
        try:
            logger.info(
                f"[{operation}] Iniciando análisis de factura",
                extra={"request_id": request_id, "text_length": len(invoice_text)}
            )
            
            self._update_breaker_state()
            
            # Llamar a OpenAI con circuit breaker
            result = await self._call_openai_with_breaker(
                operation=operation,
                prompt=self._build_invoice_analysis_prompt(invoice_text),
                request_id=request_id
            )
            
            analysis = self._parse_invoice_analysis(result.get('content', ''))
            
            latency = (datetime.now() - start_time).total_seconds()
            openai_api_latency.labels(operation=operation).observe(latency)
            openai_api_calls.labels(operation=operation, status="success").inc()
            
            logger.info(
                f"[{operation}] Análisis completado",
                extra={
                    "request_id": request_id,
                    "latency": latency,
                    "items_extracted": len(analysis.get('items', []))
                }
            )
            
            return {
                'success': True,
                'analysis': analysis,
                'breaker_state': openai_breaker.current_state,
                'latency': latency
            }
            
        except Exception as e:
            # Circuit breaker abierto o error → usar fallback
            latency = (datetime.now() - start_time).total_seconds()
            
            logger.warning(
                f"[{operation}] Usando fallback analysis - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "latency": latency,
                    "breaker_state": openai_breaker.current_state
                }
            )
            
            openai_api_calls.labels(operation=operation, status="fallback").inc()
            
            return {
                'success': False,
                'analysis': self._get_fallback_analysis(),
                'fallback': True,
                'breaker_state': openai_breaker.current_state,
                'latency': latency,
                'error': str(e)
            }
    
    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================
    
    @openai_breaker
    async def _call_openai_with_breaker(
        self,
        operation: str,
        prompt: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Llamada a OpenAI protegida con circuit breaker.
        
        El decorador @openai_breaker:
        - Monitorea fallos
        - Abre si hay 5 fallos en 60 segundos
        - Intenta recuperarse después de 60 segundos
        
        Args:
            operation: Nombre de la operación
            prompt: Prompt para OpenAI
            request_id: ID de request
            
        Returns:
            Response de OpenAI o lanza excepción
        """
        # TODO: DÍA 1 - PASO 2
        # Aquí iría la llamada real a OpenAI API
        # Por ahora, simulamos la respuesta
        
        logger.debug(
            f"[Circuit Breaker] Llamando OpenAI - Operation: {operation}",
            extra={"request_id": request_id}
        )
        
        # Simular API call (reemplazar con llamada real)
        return {
            'content': f"OpenAI response for {operation}",
            'tokens_used': 150,
            'model': self.model
        }
    
    def _update_breaker_state(self):
        """Actualizar métrica de estado del circuit breaker"""
        state_map = {
            'closed': 0,
            'open': 1,
            'half-open': 2
        }
        current = openai_breaker.current_state
        openai_breaker_state.set(state_map.get(current, 0))
    
    @staticmethod
    def _build_ocr_enhancement_prompt(raw_text: str) -> str:
        """Construir prompt para enhancement de OCR"""
        return f"""Mejora el siguiente texto OCR de mala calidad. Corrige errores de ortografía y espacios:

Texto original:
{raw_text}

Proporciona solo el texto mejorado sin explicaciones."""
    
    @staticmethod
    def _build_pricing_prompt(item_data: Dict[str, Any]) -> str:
        """Construir prompt para generación de pricing"""
        return f"""Basado en los siguientes datos del item:
- Nombre: {item_data.get('name', 'N/A')}
- Categoría: {item_data.get('category', 'N/A')}
- Costo: {item_data.get('cost', 'N/A')}
- Margen objetivo: {item_data.get('target_margin', '30%')}

Sugiere un precio de venta óptimo considerando el mercado. Responde solo con un JSON."""
    
    @staticmethod
    def _build_invoice_analysis_prompt(invoice_text: str) -> str:
        """Construir prompt para análisis de factura"""
        return f"""Analiza la siguiente factura y extrae la información clave:

Factura:
{invoice_text}

Responde con un JSON con: fecha, proveedor, total, items (lista de nombre, cantidad, precio)."""
    
    @staticmethod
    def _parse_pricing_response(response: str) -> Dict[str, Any]:
        """Parsear respuesta de pricing desde OpenAI"""
        # En producción, parsear JSON desde la respuesta
        return {
            'price': 100.0,
            'recommended': True,
            'reasoning': response
        }
    
    @staticmethod
    def _parse_invoice_analysis(response: str) -> Dict[str, Any]:
        """Parsear análisis de factura desde OpenAI"""
        # En producción, parsear JSON desde la respuesta
        return {
            'date': '2025-10-18',
            'provider': 'N/A',
            'total': 0.0,
            'items': []
        }
    
    @staticmethod
    def _get_fallback_analysis() -> Dict[str, Any]:
        """Análisis fallback cuando OpenAI no disponible"""
        return {
            'date': None,
            'provider': 'N/A',
            'total': 0.0,
            'items': [],
            'note': 'Analysis unavailable, manual review required'
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_openai_service_instance = None

def get_openai_service() -> OpenAIService:
    """
    Obtener instancia singleton del servicio OpenAI.
    
    Uso en FastAPI:
        from .services.openai_service import get_openai_service
        
        @app.post("/enhance-ocr")
        async def enhance_ocr(text: str):
            service = get_openai_service()
            result = await service.enhance_ocr_text(text)
            return result
    """
    global _openai_service_instance
    if _openai_service_instance is None:
        _openai_service_instance = OpenAIService()
    return _openai_service_instance


# ============================================================================
# HEALTH CHECK
# ============================================================================

async def check_openai_health() -> Dict[str, Any]:
    """
    Health check para OpenAI service.
    
    Retorna estado del circuit breaker sin hacer llamadas reales.
    """
    service = get_openai_service()
    
    return {
        'service': 'openai',
        'status': 'healthy' if openai_breaker.current_state != 'open' else 'degraded',
        'breaker_state': openai_breaker.current_state,
        'fail_counter': openai_breaker.fail_counter,
        'fail_max': openai_breaker.fail_max,
        'last_failure': openai_breaker.last_failure_time if hasattr(openai_breaker, 'last_failure_time') else None
    }
