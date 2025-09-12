"""
Módulo compartido del sistema multi-agente retail argentino
"""
__version__ = "1.0.0"
__author__ = "Sistema Multi-Agente Retail"

from .config import get_settings, settings, setup_logging
from .database import get_db, init_database, health_check_db, db_manager
from .models import Producto, MovimientoStock, OutboxMessage
from .utils import (
    validar_cuit, formatear_cuit, formatear_precio_argentino,
    parsear_precio_argentino, calcular_precio_con_inflacion,
    obtener_factor_estacional, obtener_temporada_actual,
    formateador, FormateadorArgentino
)

__all__ = [
    "get_settings", "settings", "setup_logging",
    "get_db", "init_database", "health_check_db", "db_manager",
    "Producto", "MovimientoStock", "OutboxMessage",
    "validar_cuit", "formatear_cuit", "formatear_precio_argentino",
    "parsear_precio_argentino", "calcular_precio_con_inflacion",
    "obtener_factor_estacional", "obtener_temporada_actual",
    "formateador", "FormateadorArgentino"
]
