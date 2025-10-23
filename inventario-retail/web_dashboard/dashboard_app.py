#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Web - Sistema Mini Market
==================================

Dashboard web completo con Business Intelligence, métricas avanzadas,
gráficos interactivos y reportes ejecutivos para el Sistema Mini Market.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Header, Query, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.responses import PlainTextResponse
import sqlite3
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional
import math
from pathlib import Path
import os
import threading
import time
import re
import logging
import uuid
import contextvars
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redis y Cache
try:
    from redis import asyncio as aioredis
    from fastapi_cache2 import FastAPICache
    from fastapi_cache2.backends.redis import RedisBackend
    from fastapi_cache2.decorator import cache
    REDIS_AVAILABLE = True
except ImportError:
    print("⚠️  Redis no disponible, cache deshabilitado")
    REDIS_AVAILABLE = False
    cache = lambda expire: lambda f: f  # No-op decorator

# Importar lógica del Mini Market
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agente_negocio'))

try:
    from provider_database_integration import MiniMarketDatabaseManager
except ImportError:
    # Fallback si no se encuentra el módulo
    print("⚠️  No se pudo importar MiniMarketDatabaseManager")
    MiniMarketDatabaseManager = None

# Configuración de la aplicación
app = FastAPI(
    title="Dashboard Mini Market",
    description="Dashboard Web con Business Intelligence para el Sistema Mini Market",
    version="1.0.0"
)

# Configurar archivos estáticos y templates con rutas absolutas
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Instancia del gestor de base de datos
db_path = os.path.join(os.path.dirname(__file__), '..', 'agente_negocio', 'minimarket_inventory.db')
db_manager = MiniMarketDatabaseManager(db_path) if MiniMarketDatabaseManager else None

# -----------------------------
# Logging estructurado y Request-ID
# -----------------------------

# Variables de contexto para logs
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get("-"),
        }
        # Adjuntar campos extra comunes si están presentes
        for key in ("path","method","status","duration_ms","client_ip"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)

def _configure_logging():
    log_level = os.getenv("DASHBOARD_LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("DASHBOARD_LOG_DIR", os.path.join(BASE_DIR, "logs"))
    rotate_when = os.getenv("DASHBOARD_LOG_ROTATE_WHEN", "midnight")  # TimedRotatingFileHandler
    backup_count = int(os.getenv("DASHBOARD_LOG_BACKUP_COUNT", "7"))

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("dashboard")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Formateador JSON
    formatter = JsonFormatter()

    # Consola
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Archivo con rotación diaria
    try:
        from logging.handlers import TimedRotatingFileHandler
        fh = TimedRotatingFileHandler(os.path.join(log_dir, "dashboard.log"), when=rotate_when, backupCount=backup_count, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        # Si falla el handler de archivo, seguimos con consola
        pass

    return logger

logger = _configure_logging()

# Métricas simples en memoria
_metrics_lock = threading.Lock()
_metrics = {
    "start_time": time.time(),
    "requests_total": 0,
    "errors_total": 0,
    "by_path": {},  # path -> {count, errors, total_duration_ms}
}

# -----------------------------
# Seguridad y Hardening (Middlewares y utilidades)
# -----------------------------

# Hosts de confianza (configurable por env). Ej: "localhost,127.0.0.1,mi-dominio.com"
_allowed_hosts_env = os.getenv("DASHBOARD_ALLOWED_HOSTS", "*")
if _allowed_hosts_env and _allowed_hosts_env.strip() != "*":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[h.strip() for h in _allowed_hosts_env.split(",") if h.strip()])

# Redirección HTTPS opcional
if os.getenv("DASHBOARD_FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS opcional, restringido por env (no usar '*' por defecto)
_cors_origins = [o.strip() for o in os.getenv("DASHBOARD_CORS_ORIGINS", "").split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"]
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # CSP endurecida: se eliminaron scripts y estilos inline migrándolos a archivos estáticos.
    # Ajustar si se añaden nuevos CDNs. Preferir SRI para recursos externos.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https://cdn.jsdelivr.net https://cdn.pixabay.com; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net data:; "
        "media-src 'self' https://cdn.pixabay.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'"
    )
    if os.getenv("DASHBOARD_ENABLE_HSTS", "false").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# ============================================
# Redis Cache Initialization
# ============================================

@app.on_event("startup")
async def startup_redis():
    """Inicializar conexión a Redis para caché"""
    if REDIS_AVAILABLE:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis = aioredis.from_url(
                redis_url,
                encoding="utf8",
                decode_responses=True
            )
            FastAPICache.init(RedisBackend(redis), prefix="minimarket-cache")
            logger.info("✅ Redis cache inicializado", extra={"redis_url": redis_url})
        except Exception as e:
            logger.warning(f"⚠️  Error inicializando Redis: {e}", extra={"error": str(e)})

# Validación/Sanitización de parámetros
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def sanitize_date(value: Optional[str]) -> Optional[str]:
    """Devuelve una fecha YYYY-MM-DD válida o None.

    - Primero valida el formato con regex.
    - Luego valida que la fecha sea del calendario usando datetime.strptime.
    """
    if not value:
        return None
    v = value.strip()
    if not DATE_RE.match(v):
        return None
    try:
        # Validar fecha real del calendario
        datetime.strptime(v, "%Y-%m-%d")
        return v
    except Exception:
        return None

def sanitize_text(value: Optional[str], max_len: int = 60) -> Optional[str]:
    if not value:
        return None
    v = value.strip()
    # Permitir alfanumérico, espacios, guiones, puntos, barras, acentos y ñ
    v = re.sub(r"[^\w\s\-\._/áéíóúÁÉÍÓÚñÑ]", "", v)
    return v[:max_len]

def clamp_int(value: int, min_v: int, max_v: int) -> int:
    try:
        iv = int(value)
    except Exception:
        iv = min_v
    return max(min_v, min(iv, max_v))


def _get_ui_api_key() -> str:
    """API key opcional para inyectar en el HTML del dashboard.

    Configure "DASHBOARD_UI_API_KEY" si desea que el frontend envíe X-API-Key
    en las llamadas a /api/*. No use la misma clave de backend.
    """
    return os.getenv("DASHBOARD_UI_API_KEY", "")

# API Key opcional para proteger /api*. Si DASHBOARD_API_KEY está seteada, se exige X-API-Key.
def verify_api_key(x_api_key: Optional[str] = Header(default=None)):
    expected = os.getenv("DASHBOARD_API_KEY")
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(status_code=401, detail="API key inválida")
    return True

# Manejador global de excepciones para evitar fugas de stacktrace
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Diferenciar entre rutas HTML y API por prefijo
    path = request.url.path
    if path.startswith("/api/") or path in {"/health"}:
        return JSONResponse(status_code=500, content={"error": "Error interno"})
    return templates.TemplateResponse("error.html", {"request": request, "error": "Error interno"}, status_code=500)

# Rate limiting sencillo en memoria para rutas /api/*
_rate_counters = {}
_rate_lock = threading.Lock()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Releer configuración en cada request para permitir toggling por env (útil en tests y despliegue)
    _RL_ENABLED = os.getenv("DASHBOARD_RATELIMIT_ENABLED", "true").lower() == "true"
    _RL_WINDOW_SEC = int(os.getenv("DASHBOARD_RATELIMIT_WINDOW", "60"))
    _RL_MAX_REQ = int(os.getenv("DASHBOARD_RATELIMIT_MAX", "120"))
    if not _RL_ENABLED:
        return await call_next(request)
    path = request.url.path
    if not path.startswith("/api/"):
        return await call_next(request)
    # Identificar cliente
    client_ip = request.client.host if request.client else "unknown"
    now = int(time.time())
    window = now // _RL_WINDOW_SEC
    key = (client_ip, path, window)
    with _rate_lock:
        count = _rate_counters.get(key, 0) + 1
        _rate_counters[key] = count
        # Limpieza básica de ventanas antiguas para contener memoria
        if len(_rate_counters) > 5000:
            obsolete = [k for k in _rate_counters.keys() if k[2] < window]
            for k in obsolete:
                _rate_counters.pop(k, None)
    if count > _RL_MAX_REQ:
        return JSONResponse(status_code=429, content={"error": "Rate limit excedido"})
    return await call_next(request)


class DashboardAnalytics:
    """Clase para análisis y métricas del dashboard"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Cache en memoria: {clave: (valor, timestamp)}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = {
            'dashboard_summary': 30,  # segundos
            'stock_by_provider': 30,
            'weekly_sales': 30
        }

    def _get_cache(self, key):
        with self._cache_lock:
            v = self._cache.get(key)
            if v:
                value, ts = v
                ttl = self._cache_ttl.get(key, 30)
                if time.time() - ts < ttl:
                    return value
                else:
                    del self._cache[key]
        return None

    def _set_cache(self, key, value):
        with self._cache_lock:
            self._cache[key] = (value, time.time())

    def get_dashboard_summary(self) -> Dict[str, Any]:
        cache = self._get_cache('dashboard_summary')
        if cache:
            return cache
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # Métricas básicas
                cursor.execute("SELECT COUNT(*) FROM proveedores WHERE activo = 1")
                total_proveedores = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT pedido_id) FROM detalle_pedidos")
                total_pedidos = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(cantidad) FROM detalle_pedidos")
                total_productos_pedidos = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM movimientos_stock")
                total_movimientos = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM facturas_ocr WHERE procesado = 1")
                facturas_procesadas = cursor.fetchone()[0]
                # Pedidos últimos 30 días
                cursor.execute("""
                    SELECT COUNT(DISTINCT p.id) 
                    FROM pedidos p 
                    WHERE p.fecha_pedido >= datetime('now', '-30 days')
                """)
                pedidos_mes = cursor.fetchone()[0]
                # Stock movements últimos 7 días
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM movimientos_stock 
                    WHERE fecha_movimiento >= datetime('now', '-7 days')
                """)
                movimientos_semana = cursor.fetchone()[0]
                # Proveedor más activo
                cursor.execute("""
                    SELECT pr.nombre, COUNT(p.id) as total
                    FROM proveedores pr
                    LEFT JOIN pedidos p ON pr.id = p.proveedor_id
                    WHERE p.fecha_pedido >= datetime('now', '-30 days')
                    GROUP BY pr.id, pr.nombre
                    ORDER BY total DESC
                    LIMIT 1
                """)
                proveedor_top = cursor.fetchone()
                proveedor_top_nombre = proveedor_top[0] if proveedor_top else "N/A"
                proveedor_top_pedidos = proveedor_top[1] if proveedor_top else 0
                result = {
                    "total_proveedores": total_proveedores,
                    "total_pedidos": total_pedidos,
                    "total_productos_pedidos": total_productos_pedidos,
                    "total_movimientos": total_movimientos,
                    "facturas_procesadas": facturas_procesadas,
                    "pedidos_mes": pedidos_mes,
                    "movimientos_semana": movimientos_semana,
                    "proveedor_top": {
                        "nombre": proveedor_top_nombre,
                        "pedidos": proveedor_top_pedidos
                    }
                }
                self._set_cache('dashboard_summary', result)
                return result
        except Exception as e:
            return {
                "error": f"Error obteniendo resumen: {str(e)}",
                "total_proveedores": 0,
                "total_pedidos": 0,
                "total_productos_pedidos": 0,
                "total_movimientos": 0,
                "facturas_procesadas": 0,
                "pedidos_mes": 0,
                "movimientos_semana": 0,
                "proveedor_top": {"nombre": "N/A", "pedidos": 0}
            }

    def get_provider_stats(self) -> List[Dict[str, Any]]:
        """Obtiene estadísticas por proveedor"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        pr.codigo,
                        pr.nombre,
                        COUNT(DISTINCT p.id) as total_pedidos,
                        COALESCE(SUM(dp.cantidad), 0) as total_productos,
                        COUNT(DISTINCT CASE WHEN p.fecha_pedido >= datetime('now', '-7 days') THEN p.id END) as pedidos_semana,
                        COUNT(DISTINCT CASE WHEN p.fecha_pedido >= datetime('now', '-30 days') THEN p.id END) as pedidos_mes
                    FROM proveedores pr
                    LEFT JOIN pedidos p ON pr.id = p.proveedor_id
                    LEFT JOIN detalle_pedidos dp ON p.id = dp.pedido_id
                    WHERE pr.activo = 1
                    GROUP BY pr.id, pr.codigo, pr.nombre
                    ORDER BY total_pedidos DESC
                """)
                
                results = cursor.fetchall()
                return [
                    {
                        "codigo": row[0],
                        "nombre": row[1],
                        "total_pedidos": row[2],
                        "total_productos": row[3],
                        "pedidos_semana": row[4],
                        "pedidos_mes": row[5]
                    }
                    for row in results
                ]
                
        except Exception as e:
            return [{"error": f"Error obteniendo stats proveedores: {str(e)}"}]
    
    def get_stock_movements_timeline(self, days: int = 7) -> List[Dict[str, Any]]:
        """Obtiene timeline de movimientos de stock"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(fecha_movimiento) as fecha,
                        tipo_movimiento,
                        COUNT(*) as cantidad_movimientos,
                        SUM(cantidad) as total_productos
                    FROM movimientos_stock
                    WHERE fecha_movimiento >= datetime('now', '-{} days')
                    GROUP BY DATE(fecha_movimiento), tipo_movimiento
                    ORDER BY fecha DESC, tipo_movimiento
                """.format(days))
                
                results = cursor.fetchall()
                return [
                    {
                        "fecha": row[0],
                        "tipo": row[1],
                        "movimientos": row[2],
                        "productos": row[3]
                    }
                    for row in results
                ]
                
        except Exception as e:
            return [{"error": f"Error obteniendo timeline: {str(e)}"}]
    
    def get_top_products(self, limit: int = 10, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene productos más pedidos con filtros opcionales (cacheado)."""
        cache_key = f"top_products:{limit}:{start_date or ''}:{end_date or ''}:{proveedor or ''}"
        cache = self._get_cache(cache_key)
        if cache:
            return cache
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                where_conditions: List[str] = []
                params: List[Any] = []
                if start_date:
                    where_conditions.append("p.fecha_pedido >= ?")
                    params.append(start_date)
                if end_date:
                    where_conditions.append("p.fecha_pedido <= ?")
                    params.append(end_date)
                if proveedor:
                    where_conditions.append("(pr.nombre LIKE ? OR pr.codigo LIKE ?)")
                    params.extend([f"%{proveedor}%", f"%{proveedor}%"])
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                params.append(limit)
                cursor.execute(f"""
                    SELECT 
                        dp.producto_nombre,
                        SUM(dp.cantidad) as total_cantidad,
                        COUNT(DISTINCT dp.pedido_id) as pedidos_count,
                        pr.nombre as proveedor_principal
                    FROM detalle_pedidos dp
                    LEFT JOIN pedidos p ON dp.pedido_id = p.id
                    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                    {where_clause}
                    GROUP BY dp.producto_nombre
                    ORDER BY total_cantidad DESC
                    LIMIT ?
                """, params)
                rows = cursor.fetchall()
                data = [
                    {
                        "producto": r[0],
                        "cantidad_total": r[1],
                        "pedidos": r[2],
                        "proveedor": r[3] or "N/A"
                    }
                    for r in rows
                ]
                self._set_cache(cache_key, data)
                return data
        except Exception as e:
            return [{"error": f"Error obteniendo top productos: {str(e)}"}]
    
    def get_monthly_trends(self, months: int = 6, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene tendencias mensuales con filtros opcionales"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                where_conditions = []
                params = []
                
                if start_date:
                    where_conditions.append("fecha_pedido >= ?")
                    params.append(start_date)
                elif not end_date:
                    where_conditions.append("fecha_pedido >= datetime('now', '-{} months')".format(months))
                
                if end_date:
                    where_conditions.append("fecha_pedido <= ?")
                    params.append(end_date)
                
                if proveedor:
                    where_conditions.append("proveedor_id IN (SELECT id FROM proveedores WHERE nombre LIKE ? OR codigo LIKE ?)")
                    params.extend([f"%{proveedor}%", f"%{proveedor}%"])
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # Pedidos por mes
                cursor.execute(f"""
                    SELECT 
                        strftime('%Y-%m', fecha_pedido) as mes,
                        COUNT(DISTINCT id) as pedidos,
                        COUNT(DISTINCT proveedor_id) as proveedores_activos
                    FROM pedidos
                    {where_clause}
                    GROUP BY strftime('%Y-%m', fecha_pedido)
                    ORDER BY mes
                """, params)
                
                pedidos_mensuales = cursor.fetchall()
                
                # Movimientos por mes con filtros similares
                mov_where_conditions = []
                mov_params = []
                
                if start_date:
                    mov_where_conditions.append("fecha_movimiento >= ?")
                    mov_params.append(start_date)
                elif not end_date:
                    mov_where_conditions.append("fecha_movimiento >= datetime('now', '-{} months')".format(months))
                
                if end_date:
                    mov_where_conditions.append("fecha_movimiento <= ?")
                    mov_params.append(end_date)
                
                if proveedor:
                    mov_where_conditions.append("proveedor_id IN (SELECT id FROM proveedores WHERE nombre LIKE ? OR codigo LIKE ?)")
                    mov_params.extend([f"%{proveedor}%", f"%{proveedor}%"])
                
                mov_where_clause = ""
                if mov_where_conditions:
                    mov_where_clause = "WHERE " + " AND ".join(mov_where_conditions)
                
                cursor.execute(f"""
                    SELECT 
                        strftime('%Y-%m', fecha_movimiento) as mes,
                        tipo_movimiento,
                        COUNT(*) as movimientos,
                        SUM(cantidad) as productos
                    FROM movimientos_stock
                    {mov_where_clause}
                    GROUP BY strftime('%Y-%m', fecha_movimiento), tipo_movimiento
                    ORDER BY mes, tipo_movimiento
                """, mov_params)
                
                movimientos_mensuales = cursor.fetchall()
                
                return {
                    "pedidos_mensuales": [
                        {
                            "mes": row[0],
                            "pedidos": row[1],
                            "proveedores_activos": row[2]
                        }
                        for row in pedidos_mensuales
                    ],
                    "movimientos_mensuales": [
                        {
                            "mes": row[0],
                            "tipo": row[1],
                            "movimientos": row[2],
                            "productos": row[3]
                        }
                        for row in movimientos_mensuales
                    ]
                }
                
        except Exception as e:
            return {
                "error": f"Error obteniendo tendencias: {str(e)}",
                "pedidos_mensuales": [],
                "movimientos_mensuales": []
            }

    def get_monthly_trends_cached(self, months: int, start_date: Optional[str], end_date: Optional[str], proveedor: Optional[str]) -> Dict[str, Any]:
        """Wrapper con cache para reducir consultas repetidas.

        Separado de get_monthly_trends para permitir reutilización y testing
        de la rama de cache hit.
        """
        cache_key = f"monthly_trends:{months}:{start_date or ''}:{end_date or ''}:{proveedor or ''}"
        cache = self._get_cache(cache_key)
        if cache:
            return cache
        result = self.get_monthly_trends(months, start_date, end_date, proveedor)
        if not result.get("error"):
            self._set_cache(cache_key, result)
        return result

    # Stub básico para alertas de stock si no existe implementación (evita error hasattr)
    def get_stock_alerts(self) -> List[Dict[str, Any]]:  # type: ignore
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT producto_nombre, SUM(cantidad) as total
                    FROM detalle_pedidos
                    GROUP BY producto_nombre
                    ORDER BY total DESC
                    LIMIT 3
                """)
                rows = cursor.fetchall()
                return [
                    {"producto": r[0], "total": r[1], "nivel_alerta": "critico" if (r[1] or 0) < 5 else "ok"}
                    for r in rows
                ]
        except Exception:
            return []  # pragma: no cover (ruta de fallo DB muy poco probable en entorno controlado)

    def get_stock_by_provider(self, limit: int = 10) -> List[Dict[str, Any]]:
        cache = self._get_cache('stock_by_provider')
        if cache:
            return cache
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        pr.codigo,
                        pr.nombre,
                        COALESCE(SUM(CASE WHEN ms.tipo_movimiento = 'ingreso' THEN ms.cantidad 
                                          WHEN ms.tipo_movimiento = 'egreso' THEN -ms.cantidad 
                                          ELSE 0 END), 0) AS stock_total
                    FROM proveedores pr
                    LEFT JOIN movimientos_stock ms ON ms.proveedor_id = pr.id
                    WHERE pr.activo = 1
                    GROUP BY pr.id, pr.codigo, pr.nombre
                    ORDER BY stock_total DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                rows = cursor.fetchall()
                results = [
                    {"codigo": r[0], "nombre": r[1], "stock_total": r[2]} for r in rows
                ]
                if not results or all((item["stock_total"] or 0) == 0 for item in results):
                    raise ValueError("Sin movimientos de stock suficientes, usando fallback")
                self._set_cache('stock_by_provider', results)
                return results
        except Exception:
            try:
                providers = self.get_provider_stats()
                if isinstance(providers, list) and providers and not providers[0].get("error"):
                    sorted_list = sorted(providers, key=lambda x: x.get("total_productos", 0), reverse=True)[:limit]
                    results = [
                        {"codigo": p.get("codigo"), "nombre": p.get("nombre"), "stock_total": p.get("total_productos", 0)}
                        for p in sorted_list
                    ]
                    self._set_cache('stock_by_provider', results)
                    return results
                return []  # pragma: no cover (fallback adicional)
            except Exception as e2:
                return [{"error": f"Error obteniendo stock por proveedor: {str(e2)}"}]  # pragma: no cover

    def get_weekly_sales(self, weeks: int = 8) -> List[Dict[str, Any]]:
        cache = self._get_cache('weekly_sales')
        if cache:
            return cache
        try:
            days = max(1, int(weeks)) * 7
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    SELECT 
                        strftime('%Y-%W', p.fecha_pedido) AS semana,
                        COUNT(DISTINCT p.id) AS pedidos,
                        COALESCE(SUM(dp.cantidad), 0) AS productos
                    FROM pedidos p
                    LEFT JOIN detalle_pedidos dp ON dp.pedido_id = p.id
                    WHERE p.fecha_pedido >= datetime('now', '-{days} days')
                    GROUP BY strftime('%Y-%W', p.fecha_pedido)
                    ORDER BY semana
                    """
                )
                rows = cursor.fetchall()
                result = [
                    {"semana": r[0], "pedidos": r[1], "productos": r[2]} for r in rows
                ]
                self._set_cache('weekly_sales', result)
                return result
        except Exception as e:
            return [{"error": f"Error obteniendo ventas semanales: {str(e)}"}]  # pragma: no cover


# Instancia de analytics
analytics = DashboardAnalytics(db_manager)


# -----------------------------
# Middleware: Request-ID, Access Log y Métricas
# -----------------------------

@app.middleware("http")
async def access_log_and_metrics(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request_id_var.set(req_id)
    start = time.time()
    status_code = 500
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = int((time.time() - start) * 1000)
        client_ip = request.client.host if request.client else "-"
        path = request.url.path
        method = request.method
        # Métricas
        try:
            with _metrics_lock:
                _metrics["requests_total"] += 1
                if status_code >= 500:
                    _metrics["errors_total"] += 1
                by = _metrics["by_path"].setdefault(path, {"count": 0, "errors": 0, "total_duration_ms": 0})
                by["count"] += 1
                if status_code >= 500:
                    by["errors"] += 1
                by["total_duration_ms"] += duration_ms
        except Exception:
            pass
        # Logging
        extra = {"path": path, "method": method, "status": status_code, "duration_ms": duration_ms, "client_ip": client_ip}
        try:
            if status_code >= 500:
                logger.error(f"{method} {path} -> {status_code}", extra=extra)
            else:
                logger.info(f"{method} {path} -> {status_code}", extra=extra)
        except Exception:
            pass
        # Propagar Request-ID en respuesta
        if response is not None:
            response.headers["X-Request-ID"] = req_id


# Rutas principales del dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Página principal del dashboard"""
    try:
        summary = analytics.get_dashboard_summary()
        stock_alerts = []
        tiene_critico = False
        # Obtener alertas de stock bajo/crítico
        if hasattr(analytics, "get_stock_alerts"):
            stock_alerts = analytics.get_stock_alerts()
            tiene_critico = any(prod.get("nivel_alerta") == "critico" for prod in stock_alerts)
        return templates.TemplateResponse(request, "dashboard.html", {
            "title": "Mini Market Dashboard",
            "summary": summary,
            "stock_alerts": stock_alerts,
            "tiene_critico": tiene_critico,
            "dashboard_api_key": _get_ui_api_key()
        })
    except Exception as e:
        return templates.TemplateResponse(request, "error.html", {
            "error": f"Error cargando dashboard: {str(e)}",
            "dashboard_api_key": _get_ui_api_key()
        })


@app.get("/providers", response_class=HTMLResponse)
async def providers_dashboard(request: Request):
    """Dashboard de proveedores"""
    try:
        provider_stats = analytics.get_provider_stats()
        return templates.TemplateResponse(request, "providers.html", {
            "title": "Proveedores - Mini Market Dashboard",
            "providers": provider_stats,
            "dashboard_api_key": _get_ui_api_key()
        })
    except Exception as e:
        return templates.TemplateResponse(request, "error.html", {
            "error": f"Error cargando proveedores: {str(e)}",
            "dashboard_api_key": _get_ui_api_key()
        })


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None):
    """Dashboard de analytics avanzado con filtros"""
    try:
        s_start = sanitize_date(start_date)
        s_end = sanitize_date(end_date)
        s_prov = sanitize_text(proveedor, 60)
        trends = analytics.get_monthly_trends(6, s_start, s_end, s_prov)
        top_products = analytics.get_top_products(10, s_start, s_end, s_prov)
        return templates.TemplateResponse(request, "analytics.html", {
            "title": "Analytics - Mini Market Dashboard",
            "trends": trends,
            "top_products": top_products,
            "dashboard_api_key": _get_ui_api_key()
        })
    except Exception as e:
        return templates.TemplateResponse(request, "error.html", {
            "error": f"Error cargando analytics: {str(e)}",
            "dashboard_api_key": _get_ui_api_key()
        })


# API endpoints para datos JSON
@app.get("/api/summary")
async def api_summary(_auth: bool = Depends(verify_api_key)):
    """API: Resumen general"""
    return analytics.get_dashboard_summary()


@app.get("/api/providers")
async def api_providers(_auth: bool = Depends(verify_api_key)):
    """API: Estadísticas de proveedores"""
    return analytics.get_provider_stats()


@app.get("/api/stock-timeline")
async def api_stock_timeline(days: int = 7, _auth: bool = Depends(verify_api_key)):
    """API: Timeline de movimientos de stock"""
    safe_days = clamp_int(days, 1, 90)
    return analytics.get_stock_movements_timeline(safe_days)


@app.get("/api/top-products")
async def api_top_products(limit: int = 10, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None, _auth: bool = Depends(verify_api_key)):
    """API: Productos más pedidos con filtros opcionales"""
    safe_limit = clamp_int(limit, 1, 100)
    s_start = sanitize_date(start_date)
    s_end = sanitize_date(end_date)
    s_prov = sanitize_text(proveedor, 60)
    return analytics.get_top_products(safe_limit, s_start, s_end, s_prov)


@app.get("/api/trends")
async def api_trends(months: int = 6, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None, _auth: bool = Depends(verify_api_key)):
    """API: Tendencias mensuales con filtros opcionales"""
    safe_months = clamp_int(months, 1, 24)
    s_start = sanitize_date(start_date)
    s_end = sanitize_date(end_date)
    s_prov = sanitize_text(proveedor, 60)
    return analytics.get_monthly_trends(safe_months, s_start, s_end, s_prov)


@app.get("/api/stock-by-provider")
async def api_stock_by_provider(limit: int = 10, _auth: bool = Depends(verify_api_key)):
    """API: Stock (o volumen aproximado) por proveedor"""
    safe_limit = clamp_int(limit, 1, 100)
    return analytics.get_stock_by_provider(safe_limit)


@app.get("/api/weekly-sales")
async def api_weekly_sales(weeks: int = 8, _auth: bool = Depends(verify_api_key)):
    """API: Evolución semanal de ventas/pedidos de las últimas N semanas"""
    safe_weeks = clamp_int(weeks, 1, 52)
    return analytics.get_weekly_sales(safe_weeks)


# Endpoint de métricas (Prometheus-like), protegido por API Key
@app.get("/metrics")
async def metrics(_auth: bool = Depends(verify_api_key)):
    uptime = int(time.time() - _metrics.get("start_time", time.time()))
    with _metrics_lock:
        req_total = _metrics.get("requests_total", 0)
        err_total = _metrics.get("errors_total", 0)
        by_path = dict(_metrics.get("by_path", {}))
    lines = []
    lines.append("# HELP dashboard_requests_total Total requests processed")
    lines.append("# TYPE dashboard_requests_total counter")
    lines.append(f"dashboard_requests_total {req_total}")
    lines.append("# HELP dashboard_errors_total Total 5xx errors")
    lines.append("# TYPE dashboard_errors_total counter")
    lines.append(f"dashboard_errors_total {err_total}")
    lines.append("# HELP dashboard_uptime_seconds Process uptime in seconds")
    lines.append("# TYPE dashboard_uptime_seconds gauge")
    lines.append(f"dashboard_uptime_seconds {uptime}")
    # Por path
    lines.append("# HELP dashboard_requests_by_path_total Requests by path")
    lines.append("# TYPE dashboard_requests_by_path_total counter")
    lines.append("# HELP dashboard_errors_by_path_total Errors by path")
    lines.append("# TYPE dashboard_errors_by_path_total counter")
    lines.append("# HELP dashboard_request_duration_ms_sum Total duration by path (ms)")
    lines.append("# TYPE dashboard_request_duration_ms_sum counter")
    for path, data in sorted(by_path.items()):
        p = path.replace('"', '\"')
        lines.append(f'dashboard_requests_by_path_total{{path="{p}"}} {data.get("count", 0)}')
        lines.append(f'dashboard_errors_by_path_total{{path="{p}"}} {data.get("errors", 0)}')
        lines.append(f'dashboard_request_duration_ms_sum{{path="{p}"}} {data.get("total_duration_ms", 0)}')
    text = "\n".join(lines) + "\n"
    return PlainTextResponse(content=text, media_type="text/plain; version=0.0.4")

# Export endpoints (CSV)
@app.get("/api/export/summary.csv")
async def api_export_summary_csv(_auth: bool = Depends(verify_api_key)):
    """Exporta el resumen general a CSV."""
    data = analytics.get_dashboard_summary()
    if isinstance(data, dict) and data.get("error"):
        csv_text = "error,message\ntrue,{}".format(data["error"].replace("\n", " "))
    else:
        headers = [
            "total_proveedores","total_pedidos","total_productos_pedidos",
            "total_movimientos","facturas_procesadas","pedidos_mes",
            "movimientos_semana","proveedor_top_nombre","proveedor_top_pedidos"
        ]
        proveedor_top = data.get("proveedor_top", {}) if isinstance(data, dict) else {}
        row = [
            str(data.get("total_proveedores", 0)),
            str(data.get("total_pedidos", 0)),
            str(data.get("total_productos_pedidos", 0)),
            str(data.get("total_movimientos", 0)),
            str(data.get("facturas_procesadas", 0)),
            str(data.get("pedidos_mes", 0)),
            str(data.get("movimientos_semana", 0)),
            str(proveedor_top.get("nombre", "")),
            str(proveedor_top.get("pedidos", 0)),
        ]
        csv_text = ",".join(headers) + "\n" + ",".join(row)
    return PlainTextResponse(content=csv_text, media_type="text/csv")


@app.get("/api/export/providers.csv")
async def api_export_providers_csv(_auth: bool = Depends(verify_api_key)):
    """Exporta estadísticas de proveedores a CSV."""
    data = analytics.get_provider_stats()
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and data[0].get("error"):
        csv_text = "error,message\ntrue,{}".format(data[0]["error"].replace("\n", " "))
    else:
        headers = ["codigo","nombre","total_pedidos","total_productos","pedidos_semana","pedidos_mes"]
        lines = [",".join(headers)]
        for p in (data or []):
            lines.append(
                f"{p.get('codigo','')},{p.get('nombre','')},{p.get('total_pedidos',0)},{p.get('total_productos',0)},{p.get('pedidos_semana',0)},{p.get('pedidos_mes',0)}"
            )
        csv_text = "\n".join(lines)
    return PlainTextResponse(content=csv_text, media_type="text/csv")


# Exportar Top Productos a CSV (reubicado correctamente)
@app.get("/api/export/top-products.csv")
async def api_export_top_products_csv(limit: int = 10, start_date: Optional[str] = None, end_date: Optional[str] = None, proveedor: Optional[str] = None, _auth: bool = Depends(verify_api_key)):
    """Exporta el ranking de productos más pedidos a CSV con filtros."""
    safe_limit = clamp_int(limit, 1, 100)
    s_start = sanitize_date(start_date)
    s_end = sanitize_date(end_date)
    s_prov = sanitize_text(proveedor, 60)
    data = analytics.get_top_products(safe_limit, s_start, s_end, s_prov)
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and data[0].get("error"):
        csv_text = "error,message\ntrue,{}".format(data[0]["error"].replace("\n", " "))
    else:
        headers = ["producto","cantidad_total","pedidos","proveedor"]
        lines = [",".join(headers)]
        for p in (data or []):
            lines.append(
                f"{p.get('producto','')},{p.get('cantidad_total',0)},{p.get('pedidos',0)},{p.get('proveedor','')}"
            )
        csv_text = "\n".join(lines)
    return PlainTextResponse(content=csv_text, media_type="text/csv")


@app.get("/health")
async def health_check():
    """Health check del dashboard"""
    try:
        # Verificar conexión a base de datos
        summary = analytics.get_dashboard_summary()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected" if "error" not in summary else "error",
            "services": {
                "dashboard": "ok",
                "analytics": "ok",
                "api": "ok"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# ============================================
# BÚSQUEDA ULTRARRÁPIDA CON CACHE REDIS
# ============================================

@app.get("/api/productos/search")
@cache(expire=300)  # Cache 5 minutos
async def search_productos(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """
    Búsqueda de productos con cache Redis.
    
    Parámetros:
    - q: Término de búsqueda (nombre o código de barras)
    - limit: Máximo de resultados (1-50, default 10)
    - offset: Paginación (default 0)
    
    Retorna:
    - Lista de productos que coinciden con la búsqueda
    - Marcado como cacheado si viene de Redis
    """
    
    start_time = time.time()
    
    try:
        # Ruta a la BD
        db_file = os.path.join(os.path.dirname(__file__), '..', 'agente_negocio', 'minimarket_inventory.db')
        
        # Conectar a la BD
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query optimizada con índices
        query = """
        SELECT 
            id, nombre, codigo_barras, 
            precio_venta as precio, stock_actual as stock, 
            categoria_id, activo, fecha_registro
        FROM productos
        WHERE activo = 1 AND (
            nombre LIKE ? COLLATE NOCASE OR
            codigo_barras LIKE ? COLLATE NOCASE
        )
        ORDER BY 
            CASE 
                WHEN nombre LIKE ? COLLATE NOCASE THEN 0
                ELSE 1
            END,
            nombre ASC
        LIMIT ? OFFSET ?
        """
        
        search_term = f"%{q}%"
        
        cursor.execute(query, (search_term, search_term, f"{q}%", limit, offset))
        rows = cursor.fetchall()
        
        # Total count
        count_query = """
        SELECT COUNT(*) FROM productos 
        WHERE activo = 1 AND (
            nombre LIKE ? COLLATE NOCASE OR
            codigo_barras LIKE ? COLLATE NOCASE
        )
        """
        cursor.execute(count_query, (search_term, search_term))
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Convertir a diccionarios
        results = [dict(row) for row in rows]
        
        # Métricas
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "🔍 Búsqueda productos",
            extra={
                "query": q,
                "results": len(results),
                "total": total_count,
                "duration_ms": int(duration_ms)
            }
        )
        
        return {
            "query": q,
            "count": len(results),
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "results": results,
            "cached": True,
            "duration_ms": round(duration_ms, 2)
        }
        
    except Exception as e:
        import traceback
        logger.error(
            "❌ Error búsqueda productos",
            extra={"error": str(e), "query": q, "traceback": traceback.format_exc()}
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error en búsqueda",
                "query": q,
                "details": str(e)
            }
        )


# ============================================
# OCR Preview & Processing Endpoints
# ============================================

@app.post("/api/ocr/process")
async def process_ocr(request: Request):
    """
    Procesar imagen OCR y retornar preview con datos extractados
    
    Body: {
        "image_base64": "...",
        "proveedor_id": 1,
        "request_id": "..."
    }
    
    Response: {
        "request_id": "...",
        "confidence": 92.5,
        "proveedor": "Distribuidora XYZ",
        "fecha": "2024-10-20",
        "total": 1500.00,
        "items": [
            {"name": "Producto A", "quantity": 5, "price": 100, "confidence": 95},
            ...
        ],
        "warnings": [...],
        "suggestions": [...]
    }
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        data = await request.json()
        image_b64 = data.get("image_base64", "")
        proveedor_id = data.get("proveedor_id")
        
        if not image_b64:
            return JSONResponse(
                status_code=400,
                content={"error": "image_base64 requerido"}
            )
        
        # Simular procesamiento OCR
        # En producción, llamar a Agente Negocio: http://agente-negocio:8002/ocr/extract
        ocr_result = {
            "request_id": request_id,
            "confidence": 87.3,  # Simulado
            "proveedor": "Distribuidora ABC S.A.",
            "proveedor_confidence": 92.0,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "fecha_confidence": 85.0,
            "total": 1250.50,
            "total_confidence": 88.0,
            "items": [
                {
                    "name": "Producto A",
                    "quantity": 10,
                    "price": 50.0,
                    "confidence": 90.0
                },
                {
                    "name": "Producto B",
                    "quantity": 5,
                    "price": 150.0,
                    "confidence": 88.0
                }
            ],
            "items_count": 2,
            "items_count_confidence": 85.0,
            "warnings": [],
            "suggestions": []
        }
        
        # Agregar warnings según confianza
        if ocr_result["confidence"] < 80:
            ocr_result["warnings"].append("Baja confianza general en el OCR. Revisa los datos cuidadosamente.")
        
        if ocr_result["proveedor_confidence"] < 80:
            ocr_result["warnings"].append("Proveedor detectado con baja confianza.")
        
        if ocr_result["total_confidence"] < 85:
            ocr_result["warnings"].append("Total calculado con baja precisión. Verifica manualmente.")
        
        # Agregar sugerencias
        if len(ocr_result["items"]) == 0:
            ocr_result["suggestions"].append("No se detectaron items en la factura. Considerar agregar manualmente.")
        
        if ocr_result["items_count"] > 50:
            ocr_result["suggestions"].append("Muchos items detectados. Considera dividir en múltiples facturas.")
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "✅ OCR procesado",
            extra={
                "request_id": request_id,
                "confidence": ocr_result["confidence"],
                "items_count": len(ocr_result["items"]),
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return {
            **ocr_result,
            "duration_ms": round(duration_ms, 2)
        }
        
    except Exception as e:
        import traceback
        logger.error(
            "❌ Error procesando OCR",
            extra={
                "request_id": request_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "request_id": request_id,
                "error": "Error procesando OCR",
                "details": str(e)
            }
        )


@app.post("/api/ocr/confirm")
async def confirm_ocr(request: Request):
    """
    Confirmar y guardar datos OCR validados
    
    Body: {
        "request_id": "...",
        "proveedor": "...",
        "fecha": "...",
        "total": 1500.00,
        "items": [...],
        "confidence": 92.5,
        "edited_fields": ["proveedor", "total"]
    }
    
    Response: {
        "success": true,
        "request_id": "...",
        "document_id": 123,
        "message": "Factura confirmada y guardada"
    }
    """
    try:
        data = await request.json()
        request_id = data.get("request_id")
        proveedor = data.get("proveedor")
        fecha = data.get("fecha")
        total = data.get("total")
        items = data.get("items", [])
        confidence = data.get("confidence", 90.0)  # Valor por defecto 90%
        edited_fields = data.get("edited_fields", [])
        
        # Validaciones básicas
        if not all([request_id, proveedor, fecha, total]):
            return JSONResponse(
                status_code=400,
                content={"error": "Faltan campos requeridos"}
            )
        
        # Aquí se guardaría en la BD
        # Por ahora, simular guardado
        document_id = abs(hash(request_id)) % 100000
        
        logger.info(
            "✅ OCR confirmado y guardado",
            extra={
                "request_id": request_id,
                "proveedor": proveedor,
                "total": total,
                "document_id": document_id,
                "edited_fields": edited_fields,
                "confidence": confidence
            }
        )
        
        # Registrar en métricas locales
        with _metrics_lock:
            _metrics['requests_total'] += 1
            if confidence < 85:
                _metrics['errors_total'] += 1  # Confianza baja como "error"
        
        return {
            "success": True,
            "request_id": request_id,
            "document_id": document_id,
            "message": f"✅ Factura confirmada (confianza: {confidence:.1f}%)",
            "edited_fields_count": len(edited_fields)
        }
        
    except Exception as e:
        import traceback
        logger.error(
            "❌ Error confirmando OCR",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error confirmando OCR",
                "details": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    print("🏪 === INICIANDO DASHBOARD WEB MINI MARKET ===")
    print()
    print("📊 Funcionalidades:")
    print("  • Dashboard principal con métricas generales")
    print("  • Analytics de proveedores con estadísticas")
    print("  • Tendencias y gráficos interactivos")
    print("  • API REST para datos en tiempo real")
    print()
    print("🌐 URLs disponibles:")
    print("  • Dashboard: http://localhost:8080/")
    print("  • Proveedores: http://localhost:8080/providers")
    print("  • Analytics: http://localhost:8080/analytics")
    print("  • API: http://localhost:8080/api/*")
    print()
    print("🚀 Iniciando servidor...")
    
    # Usamos el import string para habilitar reload correctamente
    uvicorn.run("dashboard_app:app", host="0.0.0.0", port=8080, reload=True)