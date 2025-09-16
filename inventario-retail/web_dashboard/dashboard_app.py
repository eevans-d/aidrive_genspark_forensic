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

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.responses import PlainTextResponse
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math
from pathlib import Path
import os
import threading
import time

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
    
    def get_top_products(self, limit: int = 10, start_date: str = None, end_date: str = None, proveedor: str = None) -> List[Dict[str, Any]]:
        """Obtiene productos más pedidos con filtros opcionales"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                where_conditions = []
                params = []
                
                if start_date:
                    where_conditions.append("p.fecha_pedido >= ?")
                    params.append(start_date)
                
                if end_date:
                    where_conditions.append("p.fecha_pedido <= ?")
                    params.append(end_date)
                
                if proveedor:
                    where_conditions.append("(pr.nombre LIKE ? OR pr.codigo LIKE ?)")
                    params.extend([f"%{proveedor}%", f"%{proveedor}%"])
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
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
                
                results = cursor.fetchall()
                return [
                    {
                        "producto": row[0],
                        "cantidad_total": row[1],
                        "pedidos": row[2],
                        "proveedor": row[3] or "N/A"
                    }
                    for row in results
                ]
                
        except Exception as e:
            return [{"error": f"Error obteniendo top productos: {str(e)}"}]
        def get_top_products(self, limit: int = 10, start_date: str = None, end_date: str = None, proveedor: str = None) -> List[Dict[str, Any]]:
            """Obtiene productos más pedidos con filtros opcionales y cachea el resultado"""
            cache_key = f"top_products:{limit}:{start_date or ''}:{end_date or ''}:{proveedor or ''}"
            cache = self._get_cache(cache_key)
            if cache:
                return cache
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    where_conditions = []
                    params = []
                    if start_date:
                        where_conditions.append("p.fecha_pedido >= ?")
                        params.append(start_date)
                    if end_date:
                        where_conditions.append("p.fecha_pedido <= ?")
                        params.append(end_date)
                    if proveedor:
                        where_conditions.append("(pr.nombre LIKE ? OR pr.codigo LIKE ?)")
                        params.extend([f"%{proveedor}%", f"%{proveedor}%"])
                    where_clause = ""
                    if where_conditions:
                        where_clause = "WHERE " + " AND ".join(where_conditions)
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
                    results = cursor.fetchall()
                    data = [
                        {
                            "producto": row[0],
                            "cantidad_total": row[1],
                            "pedidos": row[2],
                            "proveedor": row[3] or "N/A"
                        }
                        for row in results
                    ]
                    self._set_cache(cache_key, data)
                    return data
            except Exception as e:
                return [{"error": f"Error obteniendo top productos: {str(e)}"}]
    
    def get_monthly_trends(self, months: int = 6, start_date: str = None, end_date: str = None, proveedor: str = None) -> Dict[str, Any]:
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
        def get_monthly_trends(self, months: int = 6, start_date: str = None, end_date: str = None, proveedor: str = None) -> Dict[str, Any]:
            """Obtiene tendencias mensuales con filtros opcionales y cachea el resultado"""
            cache_key = f"monthly_trends:{months}:{start_date or ''}:{end_date or ''}:{proveedor or ''}"
            cache = self._get_cache(cache_key)
            if cache:
                return cache
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
                    result = {
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
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                return {
                    "error": f"Error obteniendo tendencias: {str(e)}",
                    "pedidos_mensuales": [],
                    "movimientos_mensuales": []
                }

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
                return []
            except Exception as e2:
                return [{"error": f"Error obteniendo stock por proveedor: {str(e2)}"}]

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
            return [{"error": f"Error obteniendo ventas semanales: {str(e)}"}]


# Instancia de analytics
analytics = DashboardAnalytics(db_manager)


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
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "Mini Market Dashboard",
            "summary": summary,
            "stock_alerts": stock_alerts,
            "tiene_critico": tiene_critico
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando dashboard: {str(e)}"
        })


@app.get("/providers", response_class=HTMLResponse)
async def providers_dashboard(request: Request):
    """Dashboard de proveedores"""
    try:
        provider_stats = analytics.get_provider_stats()
        return templates.TemplateResponse("providers.html", {
            "request": request,
            "title": "Proveedores - Mini Market Dashboard",
            "providers": provider_stats
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando proveedores: {str(e)}"
        })


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request, start_date: str = None, end_date: str = None, proveedor: str = None):
    """Dashboard de analytics avanzado con filtros"""
    try:
        trends = analytics.get_monthly_trends(6, start_date, end_date, proveedor)
        top_products = analytics.get_top_products(10, start_date, end_date, proveedor)
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "title": "Analytics - Mini Market Dashboard",
            "trends": trends,
            "top_products": top_products
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando analytics: {str(e)}"
        })


# API endpoints para datos JSON
@app.get("/api/summary")
async def api_summary():
    """API: Resumen general"""
    return analytics.get_dashboard_summary()


@app.get("/api/providers")
async def api_providers():
    """API: Estadísticas de proveedores"""
    return analytics.get_provider_stats()


@app.get("/api/stock-timeline")
async def api_stock_timeline(days: int = 7):
    """API: Timeline de movimientos de stock"""
    return analytics.get_stock_movements_timeline(days)


@app.get("/api/top-products")
async def api_top_products(limit: int = 10, start_date: str = None, end_date: str = None, proveedor: str = None):
    """API: Productos más pedidos con filtros opcionales"""
    return analytics.get_top_products(limit, start_date, end_date, proveedor)


@app.get("/api/trends")
async def api_trends(months: int = 6, start_date: str = None, end_date: str = None, proveedor: str = None):
    """API: Tendencias mensuales con filtros opcionales"""
    return analytics.get_monthly_trends(months, start_date, end_date, proveedor)


@app.get("/api/stock-by-provider")
async def api_stock_by_provider(limit: int = 10):
    """API: Stock (o volumen aproximado) por proveedor"""
    return analytics.get_stock_by_provider(limit)


@app.get("/api/weekly-sales")
async def api_weekly_sales(weeks: int = 8):
    """API: Evolución semanal de ventas/pedidos de las últimas N semanas"""
    return analytics.get_weekly_sales(weeks)


# Export endpoints (CSV)
@app.get("/api/export/summary.csv")
async def api_export_summary_csv():
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
async def api_export_providers_csv():
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
async def api_export_top_products_csv(limit: int = 10, start_date: str = None, end_date: str = None, proveedor: str = None):
    """Exporta el ranking de productos más pedidos a CSV con filtros."""
    data = analytics.get_top_products(limit, start_date, end_date, proveedor)
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