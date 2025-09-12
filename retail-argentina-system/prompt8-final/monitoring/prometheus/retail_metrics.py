"""
Métricas custom para sistema inventario retail argentino
Integración con Prometheus para monitoring avanzado
"""
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from typing import Dict, List, Optional
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class RetailMetrics:
    """Métricas específicas del sistema retail argentino"""

    def __init__(self):
        # Métricas de facturas
        self.facturas_procesadas = Counter(
            'retail_facturas_procesadas_total',
            'Total facturas procesadas',
            ['tipo_factura', 'estado', 'proveedor']
        )

        self.tiempo_procesamiento_factura = Histogram(
            'retail_factura_procesamiento_segundos', 
            'Tiempo procesamiento facturas',
            ['tipo_procesamiento'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        # Métricas de stock
        self.stock_actual = Gauge(
            'retail_stock_actual_unidades',
            'Stock actual por producto',
            ['producto_codigo', 'categoria', 'proveedor']
        )

        self.stock_critico = Gauge(
            'retail_stock_critico_total',
            'Productos en stock crítico'
        )

        self.movimientos_stock = Counter(
            'retail_movimientos_stock_total',
            'Movimientos de stock',
            ['tipo_movimiento', 'categoria']
        )

        # Métricas financieras
        self.ventas_pesos = Counter(
            'retail_ventas_pesos_total',
            'Ventas totales en pesos argentinos',
            ['categoria', 'canal']
        )

        self.inflacion_aplicada = Gauge(
            'retail_inflacion_mensual_porcentaje',
            'Tasa de inflación mensual aplicada'
        )

        self.precios_ajustados = Counter(
            'retail_precios_ajustados_total',
            'Precios ajustados por inflación',
            ['categoria']
        )

        # Métricas ML
        self.predicciones_demanda = Counter(
            'retail_predicciones_demanda_total',
            'Predicciones de demanda generadas',
            ['modelo', 'accuracy_range']
        )

        self.modelo_accuracy = Gauge(
            'retail_modelo_accuracy_porcentaje',
            'Accuracy del modelo ML',
            ['modelo']
        )

        # Métricas integración AFIP
        self.validaciones_afip = Counter(
            'retail_validaciones_afip_total',
            'Validaciones AFIP realizadas',
            ['tipo_validacion', 'resultado']
        )

        self.tiempo_respuesta_afip = Histogram(
            'retail_afip_respuesta_segundos',
            'Tiempo respuesta servicios AFIP',
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        # Métricas e-commerce
        self.sync_ecommerce = Counter(
            'retail_sync_ecommerce_total',
            'Sincronizaciones e-commerce',
            ['plataforma', 'estado']
        )

        # Métricas sistema
        self.uptime_servicios = Gauge(
            'retail_uptime_segundos',
            'Uptime de servicios',
            ['servicio']
        )

        self.errores_sistema = Counter(
            'retail_errores_total',
            'Errores del sistema',
            ['servicio', 'tipo_error', 'severidad']
        )

        # Info del sistema
        self.info_sistema = Info(
            'retail_sistema_info',
            'Información del sistema'
        )

        # Inicializar info
        self.info_sistema.info({
            'version': '1.0.0',
            'region': 'argentina',
            'moneda': 'ARS',
            'ambiente': 'production'
        })

    def record_factura_procesada(self, tipo: str, estado: str, proveedor: str, tiempo_segundos: float):
        """Registrar factura procesada"""
        self.facturas_procesadas.labels(
            tipo_factura=tipo,
            estado=estado, 
            proveedor=proveedor
        ).inc()

        self.tiempo_procesamiento_factura.labels(
            tipo_procesamiento='ocr' if tipo == 'automatico' else 'manual'
        ).observe(tiempo_segundos)

    def update_stock_metrics(self, productos_stock: List[Dict]):
        """Actualizar métricas de stock"""
        stock_critico_count = 0

        for producto in productos_stock:
            # Stock actual por producto
            self.stock_actual.labels(
                producto_codigo=producto['codigo'],
                categoria=producto['categoria'],
                proveedor=producto.get('proveedor', 'unknown')
            ).set(producto['stock_actual'])

            # Contar stock crítico
            if producto['stock_actual'] <= producto['stock_minimo']:
                stock_critico_count += 1

        self.stock_critico.set(stock_critico_count)

    def record_movimiento_stock(self, tipo: str, categoria: str):
        """Registrar movimiento de stock"""
        self.movimientos_stock.labels(
            tipo_movimiento=tipo,
            categoria=categoria
        ).inc()

    def record_venta(self, monto_pesos: float, categoria: str, canal: str = 'retail'):
        """Registrar venta"""
        self.ventas_pesos.labels(
            categoria=categoria,
            canal=canal
        ).inc(monto_pesos)

    def update_inflacion(self, tasa_mensual: float):
        """Actualizar tasa de inflación"""
        self.inflacion_aplicada.set(tasa_mensual)

    def record_precio_ajustado(self, categoria: str):
        """Registrar precio ajustado por inflación"""
        self.precios_ajustados.labels(categoria=categoria).inc()

    def record_prediccion_ml(self, modelo: str, accuracy: float):
        """Registrar predicción ML"""
        # Categorizar accuracy
        if accuracy >= 0.9:
            accuracy_range = 'excellent'
        elif accuracy >= 0.8:
            accuracy_range = 'good'
        elif accuracy >= 0.7:
            accuracy_range = 'acceptable'
        else:
            accuracy_range = 'poor'

        self.predicciones_demanda.labels(
            modelo=modelo,
            accuracy_range=accuracy_range
        ).inc()

        self.modelo_accuracy.labels(modelo=modelo).set(accuracy * 100)

    def record_validacion_afip(self, tipo: str, resultado: str, tiempo_segundos: float):
        """Registrar validación AFIP"""
        self.validaciones_afip.labels(
            tipo_validacion=tipo,
            resultado=resultado
        ).inc()

        self.tiempo_respuesta_afip.observe(tiempo_segundos)

    def record_sync_ecommerce(self, plataforma: str, estado: str):
        """Registrar sincronización e-commerce"""
        self.sync_ecommerce.labels(
            plataforma=plataforma,
            estado=estado
        ).inc()

    def record_error(self, servicio: str, tipo_error: str, severidad: str = 'error'):
        """Registrar error del sistema"""
        self.errores_sistema.labels(
            servicio=servicio,
            tipo_error=tipo_error,
            severidad=severidad
        ).inc()

    def update_uptime(self, servicio: str, uptime_segundos: float):
        """Actualizar uptime de servicio"""
        self.uptime_servicios.labels(servicio=servicio).set(uptime_segundos)

# Instancia global de métricas
retail_metrics = RetailMetrics()

class MetricsCollector:
    """Collector de métricas para el sistema retail"""

    def __init__(self, db_session_factory, redis_client=None):
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client
        self.start_time = time.time()

    async def collect_business_metrics(self):
        """Recolectar métricas de negocio"""
        try:
            with self.db_session_factory() as session:
                # Métricas de stock
                from shared.models import Producto, MovimientoStock
                productos = session.query(Producto).all()

                productos_data = [
                    {
                        'codigo': p.codigo,
                        'categoria': p.categoria or 'sin_categoria',
                        'proveedor': p.proveedor or 'sin_proveedor',
                        'stock_actual': p.stock_actual,
                        'stock_minimo': p.stock_minimo
                    }
                    for p in productos
                ]

                retail_metrics.update_stock_metrics(productos_data)

                # Métricas de movimientos recientes (última hora)
                hora_atras = datetime.now() - timedelta(hours=1)
                movimientos_recientes = session.query(MovimientoStock).filter(
                    MovimientoStock.created_at >= hora_atras
                ).all()

                for mov in movimientos_recientes:
                    categoria = mov.producto.categoria if mov.producto else 'sin_categoria'
                    retail_metrics.record_movimiento_stock(mov.tipo, categoria)

        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            retail_metrics.record_error('metrics_collector', 'database_error')

    async def collect_system_metrics(self):
        """Recolectar métricas del sistema"""
        try:
            # Uptime de servicios
            current_time = time.time()
            uptime = current_time - self.start_time

            servicios = [
                'agente_negocio', 'agente_deposito', 
                'ml_predictor', 'dashboard', 'streamlit_ui'
            ]

            for servicio in servicios:
                retail_metrics.update_uptime(servicio, uptime)

            # Métricas de cache Redis si disponible
            if self.redis_client:
                try:
                    info = self.redis_client.info()
                    # Podríamos agregar métricas específicas de Redis aquí
                except Exception as e:
                    retail_metrics.record_error('redis', 'connection_error')

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            retail_metrics.record_error('metrics_collector', 'system_error')

    async def start_collection_loop(self, interval_seconds: int = 60):
        """Iniciar loop de recolección de métricas"""
        logger.info(f"Starting metrics collection loop (interval: {interval_seconds}s)")

        while True:
            try:
                await self.collect_business_metrics()
                await self.collect_system_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(10)  # Retry en 10 segundos

def start_metrics_server(port: int = 9090):
    """Iniciar servidor de métricas Prometheus"""
    logger.info(f"Starting Prometheus metrics server on port {port}")
    start_http_server(port)

if __name__ == "__main__":
    # Demo de métricas
    print("🎯 Demo métricas retail argentino")

    # Simular métricas
    retail_metrics.record_factura_procesada('A', 'procesada', 'Proveedor Test', 2.5)
    retail_metrics.update_inflacion(4.5)
    retail_metrics.record_prediccion_ml('RandomForest', 0.87)
    retail_metrics.record_validacion_afip('CAE', 'success', 1.2)

    print("✅ Métricas demo registradas")
    print("🚀 Iniciando servidor en puerto 9090...")

    start_metrics_server(9090)

    # Mantener vivo
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("👋 Cerrando servidor de métricas")
