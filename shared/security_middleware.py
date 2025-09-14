
"""
Middleware de seguridad centralizado para todos los servicios.
Incluye rate limiting, logging y headers de seguridad.
"""

import os
import time
import logging
import redis
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Inicialización de cliente Redis para rate limiting
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'), 
        port=int(os.getenv('REDIS_PORT', '6379')), 
        db=int(os.getenv('REDIS_DB', '1')), 
        decode_responses=True
    )
    redis_client.ping()  # Test conexión
except Exception:
    redis_client = None
    logger.warning("Redis no disponible - rate limiting deshabilitado")


class SecurityMiddleware:
    """
    Middleware de seguridad centralizado.
    Incluye rate limiting por IP y headers de seguridad.
    """
    def __init__(self):
        self.rate_limit_requests = 100  # requests por minuto
        self.rate_limit_window = 60     # segundos

    async def rate_limit_check(self, request: Request) -> bool:
        """
        Verifica el rate limiting por IP usando Redis.
        Permite la request si Redis no está disponible o ante error.
        """
        if not redis_client:
            return True

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        try:
            current_requests = redis_client.get(key)
            if current_requests is None:
                redis_client.setex(key, self.rate_limit_window, 1)
                return True
            if int(current_requests) >= self.rate_limit_requests:
                return False
            redis_client.incr(key)
            return True
        except Exception as e:
            logger.error(f"Error en rate limiting: {e}")
            return True

    async def security_headers(self, response) -> None:
        """
        Agrega headers de seguridad a la respuesta.
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

async def security_middleware(request: Request, call_next):
    """Middleware principal de seguridad"""
    middleware = SecurityMiddleware()
    
    # Rate limiting
    if not await middleware.rate_limit_check(request):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"}
        )
    
    # Procesar request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Agregar headers de seguridad
    await middleware.security_headers(response)
    
    # Header de tiempo de proceso
    response.headers["X-Process-Time"] = str(process_time)
    
    return response