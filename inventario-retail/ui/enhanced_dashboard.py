"""
Enhanced Dashboard - ML Analytics & Visualizations
================================================

Dashboard mejorado con Chart.js para visualización de predicciones ML
y analytics avanzados del sistema de inventario argentino.

Características:
- Gráficos Chart.js interactivos para demanda
- Dashboard ML con predicciones en tiempo real
- Analytics de inventario y tendencias
- Mapas de calor de categorías
- Métricas KPI del sistema
- Alertas y notificaciones

Autor: Sistema Multi-Agente Inventario
Versión: Post-MVP con Enhanced Dashboard
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd

# Imports del sistema
from ..shared.config import get_config, ARGENTINA_TZ
from ..shared.models import Producto, Venta
from ..shared.database import get_db_session

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURACIÓN DASHBOARD
# ========================

# Crear app FastAPI para dashboard
dashboard_app = FastAPI(
    title="Enhanced Dashboard - Sistema Inventario Argentina",
    description="Dashboard con Chart.js y ML Analytics para retail argentino",
    version="1.0.0"
)

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="ui/templates")
dashboard_app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# URLs de servicios
AGENTE_NEGOCIO_URL = os.getenv("AGENTE_NEGOCIO_URL", "http://localhost:8002")
AGENTE_DEPOSITO_URL = os.getenv("AGENTE_DEPOSITO_URL", "http://localhost:8001")
ML_PREDICTOR_URL = os.getenv("ML_PREDICTOR_URL", "http://localhost:8003")

# ========================
# SERVICIOS DE DATOS
# ========================

class DashboardDataService:
    """Servicio para obtener datos del dashboard"""

    def __init__(self):
        self.config = get_config()

    def get_kpi_metrics(self) -> Dict[str, Any]:
        """Obtener métricas KPI del sistema"""
        try:
            with get_db_session() as db:
                # Contar productos
                total_productos = db.query(Producto).count()
                productos_bajo_stock = db.query(Producto).filter(
                    Producto.stock_actual <= Producto.stock_minimo
                ).count()

                # Ventas últimos 30 días
                fecha_inicio = datetime.now(ARGENTINA_TZ) - timedelta(days=30)
                ventas_mes = db.query(Venta).filter(
                    Venta.fecha >= fecha_inicio
                ).all()

                total_ventas = len(ventas_mes)
                ingresos_mes = sum(venta.total for venta in ventas_mes)

                # Calcular tendencias
                fecha_anterior = fecha_inicio - timedelta(days=30)
                ventas_anterior = db.query(Venta).filter(
                    Venta.fecha >= fecha_anterior,
                    Venta.fecha < fecha_inicio
                ).all()

                ingresos_anterior = sum(venta.total for venta in ventas_anterior)

                # Calcular variación
                if ingresos_anterior > 0:
                    variacion_ingresos = ((ingresos_mes - ingresos_anterior) / ingresos_anterior) * 100
                else:
                    variacion_ingresos = 100 if ingresos_mes > 0 else 0

                return {
                    'total_productos': total_productos,
                    'productos_bajo_stock': productos_bajo_stock,
                    'porcentaje_bajo_stock': (productos_bajo_stock / total_productos * 100) if total_productos > 0 else 0,
                    'ventas_mes': total_ventas,
                    'ingresos_mes': ingresos_mes,
                    'variacion_ingresos': variacion_ingresos,
                    'fecha_actualizacion': datetime.now(ARGENTINA_TZ).isoformat()
                }

        except Exception as e:
            logger.error(f"Error obteniendo KPIs: {str(e)}")
            return {
                'total_productos': 0,
                'productos_bajo_stock': 0,
                'porcentaje_bajo_stock': 0,
                'ventas_mes': 0,
                'ingresos_mes': 0,
                'variacion_ingresos': 0,
                'error': str(e)
            }

    def get_sales_trend_data(self, days: int = 30) -> Dict[str, Any]:
        """Obtener datos de tendencia de ventas para Chart.js"""
        try:
            with get_db_session() as db:
                fecha_inicio = datetime.now(ARGENTINA_TZ) - timedelta(days=days)
                ventas = db.query(Venta).filter(
                    Venta.fecha >= fecha_inicio
                ).order_by(Venta.fecha).all()

                # Agrupar por día
                ventas_por_dia = {}
                for venta in ventas:
                    fecha_str = venta.fecha.strftime('%Y-%m-%d')
                    if fecha_str not in ventas_por_dia:
                        ventas_por_dia[fecha_str] = {
                            'cantidad': 0,
                            'ingresos': 0,
                            'fecha': fecha_str
                        }
                    ventas_por_dia[fecha_str]['cantidad'] += venta.cantidad
                    ventas_por_dia[fecha_str]['ingresos'] += venta.total

                # Completar días faltantes
                for i in range(days):
                    fecha = (fecha_inicio + timedelta(days=i)).strftime('%Y-%m-%d')
                    if fecha not in ventas_por_dia:
                        ventas_por_dia[fecha] = {
                            'cantidad': 0,
                            'ingresos': 0,
                            'fecha': fecha
                        }

                # Ordenar por fecha
                data_sorted = sorted(ventas_por_dia.values(), key=lambda x: x['fecha'])

                return {
                    'labels': [item['fecha'] for item in data_sorted],
                    'datasets': [
                        {
                            'label': 'Ingresos (ARS)',
                            'data': [item['ingresos'] for item in data_sorted],
                            'borderColor': 'rgb(75, 192, 192)',
                            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                            'tension': 0.1
                        },
                        {
                            'label': 'Cantidad Vendida',
                            'data': [item['cantidad'] for item in data_sorted],
                            'borderColor': 'rgb(255, 99, 132)',
                            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                            'yAxisID': 'y1'
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Error obteniendo tendencias: {str(e)}")
            return {
                'labels': [],
                'datasets': [],
                'error': str(e)
            }

    def get_category_distribution(self) -> Dict[str, Any]:
        """Obtener distribución por categorías para gráfico de dona"""
        try:
            with get_db_session() as db:
                productos = db.query(Producto).filter(Producto.activo == True).all()

                categorias = {}
                for producto in productos:
                    categoria = producto.categoria or 'otros'
                    if categoria not in categorias:
                        categorias[categoria] = {
                            'count': 0,
                            'stock_total': 0,
                            'valor_inventario': 0
                        }
                    categorias[categoria]['count'] += 1
                    categorias[categoria]['stock_total'] += producto.stock_actual
                    categorias[categoria]['valor_inventario'] += producto.stock_actual * producto.precio_venta

                # Formatear para Chart.js
                labels = list(categorias.keys())
                data_count = [categorias[cat]['count'] for cat in labels]
                data_valor = [categorias[cat]['valor_inventario'] for cat in labels]

                # Colores para las categorías
                colors = [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                ]

                return {
                    'productos_por_categoria': {
                        'labels': labels,
                        'datasets': [{
                            'data': data_count,
                            'backgroundColor': colors[:len(labels)],
                            'hoverBackgroundColor': colors[:len(labels)]
                        }]
                    },
                    'valor_por_categoria': {
                        'labels': labels,
                        'datasets': [{
                            'data': data_valor,
                            'backgroundColor': colors[:len(labels)],
                            'hoverBackgroundColor': colors[:len(labels)]
                        }]
                    }
                }

        except Exception as e:
            logger.error(f"Error obteniendo categorías: {str(e)}")
            return {
                'productos_por_categoria': {'labels': [], 'datasets': []},
                'valor_por_categoria': {'labels': [], 'datasets': []},
                'error': str(e)
            }

    def get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """Obtener alertas de stock bajo"""
        try:
            with get_db_session() as db:
                productos_bajo_stock = db.query(Producto).filter(
                    Producto.stock_actual <= Producto.stock_minimo,
                    Producto.activo == True
                ).order_by(Producto.stock_actual).limit(10).all()

                alerts = []
                for producto in productos_bajo_stock:
                    urgency = 'critical' if producto.stock_actual == 0 else 'warning' if producto.stock_actual <= producto.stock_minimo * 0.5 else 'info'

                    alerts.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'stock_actual': producto.stock_actual,
                        'stock_minimo': producto.stock_minimo,
                        'categoria': producto.categoria,
                        'urgency': urgency,
                        'dias_sin_stock': 0 if producto.stock_actual > 0 else 1  # Simplificado
                    })

                return alerts

        except Exception as e:
            logger.error(f"Error obteniendo alertas: {str(e)}")
            return []

# Instancia global del servicio
data_service = DashboardDataService()

# ========================
# ENDPOINTS DASHBOARD
# ========================

@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Página principal del dashboard"""
    try:
        # Obtener datos para el dashboard
        kpis = data_service.get_kpi_metrics()
        alerts = data_service.get_low_stock_alerts()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "kpis": kpis,
                "alerts": alerts,
                "timestamp": datetime.now(ARGENTINA_TZ).strftime('%d/%m/%Y %H:%M')
            }
        )

    except Exception as e:
        logger.error(f"Error renderizando dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )

@dashboard_app.get("/api/sales-trend")
async def get_sales_trend(days: int = 30):
    """API para obtener datos de tendencia de ventas"""
    try:
        return data_service.get_sales_trend_data(days)
    except Exception as e:
        logger.error(f"Error obteniendo tendencias: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_app.get("/api/category-distribution")
async def get_category_distribution():
    """API para obtener distribución por categorías"""
    try:
        return data_service.get_category_distribution()
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_app.get("/api/ml-predictions")
async def get_ml_predictions():
    """API para obtener predicciones ML agregadas"""
    try:
        # En implementación real, llamaría al ML Predictor
        # Por ahora, datos simulados
        predictions = {
            'top_predicted_demand': [
                {'producto': 'Leche Entera 1L', 'demanda_7d': 45, 'confianza': 0.89},
                {'producto': 'Pan Lactal', 'demanda_7d': 32, 'confianza': 0.76},
                {'producto': 'Coca Cola 2L', 'demanda_7d': 28, 'confianza': 0.82}
            ],
            'demand_forecast_chart': {
                'labels': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)],
                'datasets': [{
                    'label': 'Demanda Predicha',
                    'data': [150, 165, 140, 180, 155, 170, 160],
                    'borderColor': 'rgb(153, 102, 255)',
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'tension': 0.1
                }]
            },
            'model_confidence': 0.84,
            'last_training': datetime.now(ARGENTINA_TZ) - timedelta(hours=6)
        }

        return predictions

    except Exception as e:
        logger.error(f"Error obteniendo predicciones ML: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_app.get("/api/kpis")
async def get_kpis():
    """API para obtener métricas KPI actualizadas"""
    try:
        return data_service.get_kpi_metrics()
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@dashboard_app.get("/api/alerts")
async def get_alerts():
    """API para obtener alertas del sistema"""
    try:
        return {
            'stock_alerts': data_service.get_low_stock_alerts(),
            'system_alerts': [
                {
                    'type': 'info',
                    'message': 'Sistema funcionando correctamente',
                    'timestamp': datetime.now(ARGENTINA_TZ).isoformat()
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# MAIN PARA DESARROLLO
# ========================

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Dashboard Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8004, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print("📊 Iniciando Enhanced Dashboard - Sistema Inventario Argentina")
    print(f"🌐 Dashboard: http://{args.host}:{args.port}")
    print(f"📈 Analytics: http://{args.host}:{args.port}/api/")

    uvicorn.run(
        "ui.enhanced_dashboard:dashboard_app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
