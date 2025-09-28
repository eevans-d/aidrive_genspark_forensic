"""
Módulo retail optimizado para sistema multi-agente argentino
Incluye validaciones, servicios y métricas específicas del dominio
"""

from .validation import (
    MovimientoStock,
    ProductoRetail,
    ValidacionStock,
    AlertaStock,
    validar_codigo_barras_argentino,
    validar_precio_argentino
)

from .stock_service import StockService

from .metrics import (
    retail_metrics,
    setup_metrics_server,
    get_current_retail_metrics,
    MetricsTimer
)

from .ocr_service import (
    ocr_service,
    OCRResult,
    OCRStatus
)

__version__ = "1.0.0"
__author__ = "AIDRIVE_GENSPARK_FORENSIC Team"

# Configuración por defecto
DEFAULT_CONFIG = {
    "stock_service": {
        "max_retries": 3,
        "base_delay": 0.1
    },
    "ocr_service": {
        "default_timeout": 10.0,
        "circuit_breaker_threshold": 3,
        "cache_ttl": 3600
    },
    "metrics": {
        "prometheus_port": 9090,
        "calculation_interval": 300
    }
}

__all__ = [
    # Validaciones
    "MovimientoStock",
    "ProductoRetail", 
    "ValidacionStock",
    "AlertaStock",
    "validar_codigo_barras_argentino",
    "validar_precio_argentino",
    
    # Servicios
    "StockService",
    "ocr_service",
    
    # Métricas
    "retail_metrics",
    "setup_metrics_server",
    "get_current_retail_metrics",
    "MetricsTimer",
    
    # Tipos y enums
    "OCRResult",
    "OCRStatus",
    
    # Configuración
    "DEFAULT_CONFIG"
]