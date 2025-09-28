"""
Métricas específicas del dominio retail para sistema multi-agente argentino
Integración con Prometheus para monitoreo en producción
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Fallback si prometheus_client no está disponible
    PROMETHEUS_AVAILABLE = False
    
    class MockMetric:
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    Counter = Histogram = Gauge = Info = lambda *args, **kwargs: MockMetric()


logger = logging.getLogger(__name__)


# Métricas técnicas específicas del retail
stock_operations = Counter(
    'retail_stock_operations_total',
    'Total stock operations by type and result',
    ['operation_type', 'deposito_id', 'result', 'categoria']
)

ocr_processing_time = Histogram(
    'retail_ocr_processing_seconds',
    'OCR processing time distribution',
    ['ocr_type', 'success', 'product_category'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')]
)

stock_validation_errors = Counter(
    'retail_stock_validation_errors_total',
    'Stock validation errors by type',
    ['error_type', 'producto_id', 'deposito_id']
)

database_query_time = Histogram(
    'retail_database_query_seconds',
    'Database query execution time',
    ['query_type', 'table', 'success'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, float('inf')]
)

# Métricas de negocio retail específicas
current_stock_value = Gauge(
    'retail_stock_value_total',
    'Total inventory value by depot and category',
    ['deposito_id', 'categoria']
)

low_stock_items = Gauge(
    'retail_low_stock_items_count',
    'Number of items with low stock by category and criticality',
    ['categoria', 'criticality', 'deposito_id']
)

daily_sales_volume = Gauge(
    'retail_daily_sales_volume',
    'Daily sales volume by category',
    ['categoria', 'deposito_id', 'date']
)

product_turnover_rate = Gauge(
    'retail_product_turnover_rate',
    'Product turnover rate (sales/average_inventory)',
    ['producto_id', 'categoria', 'period_days']
)

pricing_alerts = Counter(
    'retail_pricing_alerts_total',
    'Pricing alerts from competitive monitoring',
    ['alert_type', 'competitor', 'product_category']
)

# Métricas del sistema OCR específicas
ocr_accuracy_rate = Gauge(
    'retail_ocr_accuracy_rate',
    'OCR accuracy rate by document type',
    ['document_type', 'ocr_engine']
)

barcode_recognition_success = Counter(
    'retail_barcode_recognition_total',
    'Barcode recognition attempts and success',
    ['barcode_type', 'success', 'quality']
)


class RetailMetricsCollector:
    """Collector de métricas específicas para el negocio retail"""
    
    def __init__(self, db_session_factory=None):
        self.db_session_factory = db_session_factory
        self.last_calculation = {}
        self.calculation_interval = 300  # 5 minutos
        
    def record_stock_operation(self, operation_type: str, deposito_id: int, 
                             result: str, categoria: str = "unknown"):
        """Registrar operación de stock"""
        if PROMETHEUS_AVAILABLE:
            stock_operations.labels(
                operation_type=operation_type,
                deposito_id=str(deposito_id),
                result=result,
                categoria=categoria
            ).inc()
        
        logger.debug(f"Stock operation recorded: {operation_type}/{result} in depot {deposito_id}")

    def record_ocr_processing(self, processing_time: float, ocr_type: str, 
                            success: bool, product_category: str = "unknown"):
        """Registrar tiempo de procesamiento OCR"""
        if PROMETHEUS_AVAILABLE:
            ocr_processing_time.labels(
                ocr_type=ocr_type,
                success=str(success),
                product_category=product_category
            ).observe(processing_time)
        
        logger.debug(f"OCR processing recorded: {processing_time:.2f}s, type={ocr_type}, success={success}")

    def record_stock_validation_error(self, error_type: str, producto_id: int, 
                                    deposito_id: int):
        """Registrar error de validación de stock"""
        if PROMETHEUS_AVAILABLE:
            stock_validation_errors.labels(
                error_type=error_type,
                producto_id=str(producto_id),
                deposito_id=str(deposito_id)
            ).inc()

    def record_database_query(self, query_time: float, query_type: str, 
                            table: str, success: bool = True):
        """Registrar tiempo de consulta a base de datos"""
        if PROMETHEUS_AVAILABLE:
            database_query_time.labels(
                query_type=query_type,
                table=table,
                success=str(success)
            ).observe(query_time)

    def record_barcode_recognition(self, barcode_type: str, success: bool, quality: str):
        """Registrar reconocimiento de código de barras"""
        if PROMETHEUS_AVAILABLE:
            barcode_recognition_success.labels(
                barcode_type=barcode_type,
                success=str(success),
                quality=quality
            ).inc()

    def calculate_retail_metrics(self) -> Dict[str, Any]:
        """
        Calcular métricas específicas del negocio retail
        """
        if not self.db_session_factory:
            logger.warning("No database session factory available for metrics calculation")
            return {}
        
        # Verificar si es momento de recalcular
        now = time.time()
        if now - self.last_calculation.get('business_metrics', 0) < self.calculation_interval:
            return self.last_calculation.get('results', {})
        
        session = self.db_session_factory()
        try:
            metrics = {}
            
            # 1. Valor total del inventario por depósito y categoría
            inventory_value_query = """
            SELECT 
                COALESCE(deposito_id, 0) as deposito_id,
                categoria,
                SUM(stock_actual * precio_venta) as valor_total
            FROM productos 
            WHERE active = true AND stock_actual > 0
            GROUP BY deposito_id, categoria
            """
            
            inventory_results = session.execute(inventory_value_query).fetchall()
            for row in inventory_results:
                deposito_id, categoria, valor_total = row
                if PROMETHEUS_AVAILABLE:
                    current_stock_value.labels(
                        deposito_id=str(deposito_id),
                        categoria=categoria or "sin_categoria"
                    ).set(float(valor_total or 0))
            
            # 2. Items con stock bajo por criticidad
            low_stock_query = """
            SELECT 
                COALESCE(deposito_id, 0) as deposito_id,
                categoria,
                CASE 
                    WHEN stock_actual = 0 THEN 'AGOTADO'
                    WHEN stock_actual <= stock_minimo * 0.5 THEN 'CRITICO'
                    ELSE 'BAJO'
                END as criticidad,
                COUNT(*) as cantidad
            FROM productos
            WHERE active = true AND stock_actual <= stock_minimo
            GROUP BY deposito_id, categoria, criticidad
            """
            
            low_stock_results = session.execute(low_stock_query).fetchall()
            for row in low_stock_results:
                deposito_id, categoria, criticidad, cantidad = row
                if PROMETHEUS_AVAILABLE:
                    low_stock_items.labels(
                        categoria=categoria or "sin_categoria",
                        criticality=criticidad,
                        deposito_id=str(deposito_id)
                    ).set(cantidad)
            
            # 3. Tasa de rotación de productos (últimos 30 días)
            turnover_query = """
            SELECT 
                ms.producto_id,
                p.categoria,
                COUNT(CASE WHEN ms.tipo_movimiento = 'SALIDA' THEN 1 END) as ventas,
                AVG(p.stock_actual) as stock_promedio
            FROM movimientos_stock ms
            JOIN productos p ON ms.producto_id = p.id
            WHERE ms.created_at >= datetime('now', '-30 days')
                AND p.active = true
            GROUP BY ms.producto_id, p.categoria
            HAVING stock_promedio > 0
            """
            
            turnover_results = session.execute(turnover_query).fetchall()
            for row in turnover_results:
                producto_id, categoria, ventas, stock_promedio = row
                turnover_rate = (ventas or 0) / (stock_promedio or 1)
                
                if PROMETHEUS_AVAILABLE:
                    product_turnover_rate.labels(
                        producto_id=str(producto_id),
                        categoria=categoria or "sin_categoria",
                        period_days="30"
                    ).set(turnover_rate)
            
            # 4. Resumen para logs y dashboard
            total_products = session.execute(
                "SELECT COUNT(*) FROM productos WHERE active = true"
            ).scalar()
            
            total_inventory_value = session.execute(
                "SELECT SUM(stock_actual * precio_venta) FROM productos WHERE active = true"
            ).scalar() or 0
            
            critical_stock_items = session.execute(
                "SELECT COUNT(*) FROM productos WHERE active = true AND stock_actual = 0"
            ).scalar()
            
            metrics = {
                'total_products': total_products,
                'total_inventory_value': float(total_inventory_value),
                'critical_stock_items': critical_stock_items,
                'low_stock_items_total': len(low_stock_results),
                'calculation_time': datetime.now().isoformat(),
                'turnover_products': len(turnover_results)
            }
            
            # Cachear resultados
            self.last_calculation = {
                'business_metrics': now,
                'results': metrics
            }
            
            logger.info(f"Retail metrics calculated: {len(inventory_results)} inventory items, "
                       f"{critical_stock_items} critical items, total value: ${total_inventory_value:,.2f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating retail metrics: {e}")
            return {}
            
        finally:
            session.close()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas de performance"""
        return {
            'prometheus_available': PROMETHEUS_AVAILABLE,
            'metrics_enabled': True,
            'last_calculation': self.last_calculation.get('business_metrics'),
            'calculation_interval_seconds': self.calculation_interval
        }


# Instancia global del collector
retail_metrics = RetailMetricsCollector()


def setup_metrics_server(port: int = 9090):
    """
    Configurar servidor de métricas Prometheus
    """
    if PROMETHEUS_AVAILABLE:
        try:
            start_http_server(port)
            logger.info(f"Metrics server started on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            return False
    else:
        logger.warning("Prometheus client not available, metrics server not started")
        return False


def record_api_request_time(endpoint: str, method: str, status_code: int, 
                          processing_time: float):
    """Decorator/función para registrar tiempo de respuesta de APIs"""
    retail_metrics.record_database_query(
        query_time=processing_time,
        query_type=f"api_{method.lower()}",
        table=endpoint.replace('/', '_'),
        success=200 <= status_code < 400
    )


# Context manager para medición automática de tiempo
class MetricsTimer:
    """Context manager para medir tiempo automáticamente"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str]):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Registrar según el tipo de métrica
            if self.metric_name == 'ocr_processing':
                retail_metrics.record_ocr_processing(
                    processing_time=duration,
                    ocr_type=self.labels.get('type', 'unknown'),
                    success=exc_type is None,
                    product_category=self.labels.get('category', 'unknown')
                )
            elif self.metric_name == 'database_query':
                retail_metrics.record_database_query(
                    query_time=duration,
                    query_type=self.labels.get('type', 'unknown'),
                    table=self.labels.get('table', 'unknown'),
                    success=exc_type is None
                )


# Función de utilidad para obtener métricas de forma síncrona
def get_current_retail_metrics() -> Dict[str, Any]:
    """Obtener métricas actuales del retail"""
    return retail_metrics.calculate_retail_metrics()