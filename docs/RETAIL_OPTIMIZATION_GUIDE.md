# Guía de Optimización Retail - AIDRIVE_GENSPARK_FORENSIC

## 🎯 Resumen Ejecutivo

Esta guía documenta las optimizaciones implementadas específicamente para el sistema multi-agente retail argentino. Las optimizaciones están diseñadas para los 3 submódulos principales identificados en el proyecto.

## 📋 Submódulos Optimizados

### 1. **inventario-retail/**
- **Base de datos**: SQLite (con migration path a PostgreSQL)
- **Optimizaciones**: WAL mode, índices de stock, cache 64MB
- **Servicios**: Stock atómico, validaciones EAN-13, OCR con circuit breakers

### 2. **business-intelligence-orchestrator-v3.1/**
- **Base de datos**: PostgreSQL
- **Optimizaciones**: Índices concurrentes, taxonomías, legal compliance
- **Servicios**: Web automático, competitive monitoring

### 3. **sistema_deposito_semana1/**
- **Base de datos**: PostgreSQL
- **Optimizaciones**: Connection pooling, transacciones ACID
- **Servicios**: Gestión depósitos, transferencias inter-almacén

## 🚀 Implementación de Optimizaciones

### Paso 1: Aplicar Configuraciones de Base de Datos

```bash
# Ejecutar script de optimización automática
python scripts/optimization/apply_database_optimizations.py /path/to/project

# O aplicar manualmente por submódulo:
# Para SQLite (inventario-retail)
sqlite3 inventario-retail/data/inventario.db < config/database/inventario_sqlite_pragmas.sql

# Para PostgreSQL (BI orchestrator) 
psql -d business_intelligence -f config/database/bi_postgresql_indices.sql
```

### Paso 2: Integrar Validaciones Retail

```python
from app.retail import MovimientoStock, ProductoRetail, StockService

# Ejemplo de uso en FastAPI endpoints
@app.post("/api/stock/movimiento")
async def crear_movimiento(movimiento: MovimientoStock):
    service = StockService(db_session_factory)
    
    # Operación atómica con retry logic
    result = await service.registrar_movimiento_stock(movimiento)
    return result

# Validación de productos argentinos
@app.post("/api/productos")
async def crear_producto(producto: ProductoRetail):
    # Automáticamente valida EAN-13, precios, IVA
    return {"success": True, "producto_id": producto.id}
```

### Paso 3: Configurar Métricas y Monitoreo

```python
from app.retail import setup_metrics_server, retail_metrics

# Inicializar servidor de métricas
setup_metrics_server(port=9090)

# Usar métricas en operaciones críticas
retail_metrics.record_stock_operation(
    operation_type="ENTRADA",
    deposito_id=1,
    result="success",
    categoria="Bebidas"
)
```

### Paso 4: Implementar OCR Optimizado

```python
from app.retail import ocr_service

# OCR con circuit breaker y cache
result = await ocr_service.process_image_with_fallbacks(
    image="path/to/producto.jpg",
    timeout=10.0,
    min_confidence=0.8
)

# Reconocimiento de códigos de barras
barcode_result = await ocr_service.recognize_barcode(
    image="path/to/barcode.jpg"
)
```

## 📊 Monitoreo y Alertas

### Dashboard Grafana

Importar el dashboard desde `monitoring/dashboards/retail_dashboard.json`:

- **Stock Operations Overview**: Rate de operaciones por tipo
- **OCR Performance**: P95 y P50 de tiempos de procesamiento  
- **Critical Stock Items**: Productos con stock bajo/agotado
- **Database Performance**: Tiempos de query y error rates

### Métricas Clave

```prometheus
# Operaciones de stock por tipo y resultado
retail_stock_operations_total{operation_type="ENTRADA",result="success"}

# Tiempo de procesamiento OCR
histogram_quantile(0.95, retail_ocr_processing_seconds)

# Valor total del inventario por categoría  
retail_stock_value_total{categoria="Bebidas"}

# Items con stock crítico
retail_low_stock_items_count{criticality="AGOTADO"}
```

### Alertas Recomendadas

```yaml
# Prometheus alerting rules
groups:
- name: retail_alerts
  rules:
  - alert: StockAgotado
    expr: retail_low_stock_items_count{criticality="AGOTADO"} > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Productos agotados detectados"
      
  - alert: OCRPerformanceDegradation
    expr: histogram_quantile(0.95, retail_ocr_processing_seconds) > 2.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Performance de OCR degradada"
```

## 🧪 Testing y Validación

### Ejecutar Tests de Validaciones

```bash
# Tests completos del módulo retail
python -m pytest tests/retail/ -v

# Tests específicos de validaciones
python -m pytest tests/retail/test_retail_validations.py::TestMovimientoStock -v

# Con coverage
python -m pytest tests/retail/ --cov=app.retail --cov-report=html
```

### Performance Testing

```bash
# Test de carga para operaciones de stock
python -c "
from app.retail import StockService
import asyncio
import time

async def test_stock_operations():
    service = StockService(db_session_factory)
    
    start = time.time()
    for i in range(100):
        # Simular operaciones concurrentes
        pass
    
    print(f'100 operations in {time.time() - start:.2f}s')
"
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```env
# Base de datos
SQLITE_DB_PATH=inventario-retail/data/inventario.db
BI_PG_HOST=localhost
BI_PG_DATABASE=business_intelligence
DEPOSITO_PG_HOST=localhost
DEPOSITO_PG_DATABASE=deposito_db

# Redis para cache
REDIS_URL=redis://localhost:6379/1

# Métricas
PROMETHEUS_PORT=9090
METRICS_INTERVAL=300

# OCR
OCR_TIMEOUT=10.0
OCR_CIRCUIT_BREAKER_THRESHOLD=3
OCR_CACHE_TTL=3600
```

### Configuración por Ambiente

```python
# config/environments.py
import os

ENVIRONMENTS = {
    "development": {
        "database": {
            "sqlite_path": "data/dev_inventario.db",
            "pg_host": "localhost"
        },
        "ocr": {
            "timeout": 30.0,  # Más permisivo en dev
            "circuit_breaker_threshold": 5
        }
    },
    "production": {
        "database": {
            "sqlite_path": "/var/lib/inventario/inventario.db", 
            "pg_host": os.getenv("PG_HOST", "postgres.internal")
        },
        "ocr": {
            "timeout": 10.0,  # Estricto en prod
            "circuit_breaker_threshold": 3
        }
    }
}
```

## 🎯 Criterios de Éxito

### Performance Targets

- ✅ **Stock Operations**: P95 < 150ms
- ✅ **OCR Processing**: P95 < 2000ms  
- ✅ **Database Queries**: P95 < 500ms
- ✅ **API Error Rate**: < 0.5%

### Business Metrics

- ✅ **Stock Accuracy**: 99.9% (cero stock negativo)
- ✅ **OCR Accuracy**: > 90% para productos argentinos
- ✅ **Cache Hit Rate**: > 80% para precios/OCR
- ✅ **Alert Response**: < 1min para stock crítico

## 🛠️ Troubleshooting

### Problemas Comunes

1. **SQLite Database Locked**
   ```python
   # El retry logic automático maneja esto
   # Ajustar busy_timeout si es necesario
   PRAGMA busy_timeout=15000;
   ```

2. **Circuit Breaker Open**
   ```python
   # Verificar estado del OCR service
   stats = ocr_service.get_service_stats()
   print(f"Circuit breaker: {stats['circuit_breaker_state']}")
   ```

3. **Métricas No Aparecen**
   ```bash
   # Verificar servidor de métricas
   curl http://localhost:9090/metrics | grep retail_
   ```

### Logs de Debug

```python
import logging
logging.getLogger('app.retail').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 📚 Referencias

- [Documentación Pydantic v2](https://docs.pydantic.dev/latest/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [SQLite Performance Tips](https://www.sqlite.org/opt.html)
- [PostgreSQL Index Tuning](https://www.postgresql.org/docs/current/indexes.html)