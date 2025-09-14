"""
Cliente MercadoLibre API con rate limiting y token refresh
"""
import asyncio
import aiohttp
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter para API de MercadoLibre"""

    def __init__(self, max_requests: int = 5000, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

    async def acquire(self) -> bool:
        """Adquiere permiso para hacer request"""
        now = time.time()

        # Limpiar requests antiguos
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()

        self.requests.append(now)
        return True

class MercadoLibreClient:
    """Cliente para API de MercadoLibre con circuit breaker"""

    def __init__(self, client_id: str, client_secret: str, access_token: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.mercadolibre.com"

        # Rate limiter
        self.rate_limiter = RateLimiter()

        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        self.circuit_breaker_max_failures = int(os.getenv('ML_CIRCUIT_BREAKER_MAX_FAILURES', '5'))
        self.circuit_breaker_reset_timeout = int(os.getenv('ML_CIRCUIT_BREAKER_RESET_TIMEOUT', '300'))  # 5 minutes

        # Session HTTP
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_my_items(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Obtiene items del usuario con circuit breaker protection"""
        # Check circuit breaker
        if not self._is_circuit_breaker_closed():
            logger.warning("Circuit breaker open, skipping ML API call")
            return {
                "success": False,
                "error": "Circuit breaker open - too many recent failures"
            }
            
        try:
            await self.rate_limiter.acquire()

            # Timeout protection
            timeout_seconds = int(os.getenv('ML_API_TIMEOUT', '30'))
            result = await asyncio.wait_for(
                self._get_my_items_internal(limit, offset),
                timeout=timeout_seconds
            )
            
            # Reset circuit breaker on success
            self.circuit_breaker_failures = 0
            return result

        except asyncio.TimeoutError:
            self._record_circuit_breaker_failure()
            logger.error(f"ML API timeout after {timeout_seconds} seconds", exc_info=True, extra={
                "limit": limit,
                "offset": offset,
                "context": "ml_api_timeout"
            })
            return {
                "success": False,
                "error": f"API timeout after {timeout_seconds} seconds"
            }
        except Exception as e:
            self._record_circuit_breaker_failure()
            logger.error(f"Error obteniendo items ML: {e}", exc_info=True, extra={
                "limit": limit,
                "offset": offset,
                "context": "ml_get_items_error"
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_my_items_internal(self, limit: int, offset: int) -> Dict[str, Any]:
        """Internal implementation for getting items"""
        # Mock implementation
        items = [
            {
                "id": f"MLA{123456789 + i}",
                "title": f"Producto Test {i+1}",
                "price": 1500.0 + (i * 100),
                "available_quantity": 50 - i,
                "status": "active",
                "seller_custom_field": f"PROD{i+1:03d}"
            }
            for i in range(min(limit, 10))
        ]

        return {
            "success": True,
            "items": items,
            "paging": {
                "total": 100,
                "limit": limit,
                "offset": offset
            }
        }
    
    def _is_circuit_breaker_closed(self) -> bool:
        """Check if circuit breaker is closed (allowing requests)"""
        if self.circuit_breaker_failures < self.circuit_breaker_max_failures:
            return True
            
        # Check if timeout has passed to reset circuit breaker
        if self.circuit_breaker_last_failure:
            elapsed = (datetime.now() - self.circuit_breaker_last_failure).total_seconds()
            if elapsed > self.circuit_breaker_reset_timeout:
                self.circuit_breaker_failures = 0
                self.circuit_breaker_last_failure = None
                logger.info("Circuit breaker reset after timeout")
                return True
                
        return False
    
    def _record_circuit_breaker_failure(self):
        """Record a circuit breaker failure"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = datetime.now()
        
        if self.circuit_breaker_failures >= self.circuit_breaker_max_failures:
            logger.warning(f"Circuit breaker opened after {self.circuit_breaker_failures} failures")

    async def update_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un item específico"""
        try:
            await self.rate_limiter.acquire()

            # Mock successful update
            return {
                "success": True,
                "item_id": item_id,
                "updated_fields": list(data.keys()),
                "updated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self._record_circuit_breaker_failure()
            logger.error(f"Error actualizando item {item_id}: {e}", exc_info=True, extra={
                "item_id": item_id,
                "updated_fields": list(data.keys()) if data else [],
                "context": "ml_update_item_error"
            })
            return {
                "success": False,
                "error": str(e)
            }

    async def update_multiple_items(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Actualiza múltiples items por lotes"""
        results = []
        errors = []

        for update in updates:
            try:
                result = await self.update_item(update['item_id'], update['data'])
                if result['success']:
                    results.append(result)
                else:
                    errors.append({
                        "item_id": update['item_id'],
                        "error": result['error']
                    })
            except Exception as e:
                errors.append({
                    "item_id": update['item_id'],
                    "error": str(e)
                })

        return {
            "success": len(errors) == 0,
            "updated_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors
        }
