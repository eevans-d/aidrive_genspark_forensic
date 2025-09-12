"""
Configuración compartida del sistema multi-agente
Usa Pydantic Settings para cargar configuración desde .env
Contexto: Retail argentino con inflación y temporadas
"""
from functools import lru_cache
from typing import Literal
from pydantic import BaseSettings, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Configuración global del sistema multi-agente"""

    # Base de datos
    DATABASE_URL: str = "sqlite:///./data/inventario.db?check_same_thread=false"
    DATABASE_ECHO: bool = False

    # JWT y Seguridad
    JWT_SECRET: str = "inventario-retail-jwt-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Puertos de servicios
    AGENTE_NEGOCIO_PORT: int = 8001
    AGENTE_DEPOSITO_PORT: int = 8002
    MONITOR_PORT: int = 8003

    # URLs de servicios
    AGENTE_NEGOCIO_URL: str = "http://localhost:8001"
    AGENTE_DEPOSITO_URL: str = "http://localhost:8002"

    # Contexto Argentino - Inflación
    INFLACION_MENSUAL: float = 4.5  # Porcentaje mensual
    INFLACION_ANUAL_MAX: float = 150.0  # Límite alerta

    # Contexto Argentino - Temporadas
    TEMPORADA: Literal["verano", "invierno", "otoño", "primavera"] = "verano"

    # Factores estacionales para stock mínimo
    FACTOR_STOCK_VERANO: float = 1.3  # +30% stock en verano
    FACTOR_STOCK_INVIERNO: float = 0.8  # -20% stock en invierno
    FACTOR_STOCK_OTOÑO: float = 1.0    # Stock normal
    FACTOR_STOCK_PRIMAVERA: float = 1.1  # +10% stock

    # OCR y Procesamiento
    OCR_CONFIDENCE_MIN: float = 0.6
    OCR_CACHE_TTL_HOURS: int = 24
    OCR_MAX_IMAGE_SIZE_MB: int = 10

    # AFIP - Tipos de factura válidos
    TIPOS_FACTURA_AFIP: list = ["A", "B", "C", "E", "M"]

    # Resiliencia
    HTTP_TIMEOUT_SECONDS: int = 30
    HTTP_RETRY_MAX: int = 3
    HTTP_RETRY_BACKOFF: float = 1.5
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = 60

    # Outbox Pattern
    OUTBOX_WORKER_INTERVAL_SECONDS: int = 30
    OUTBOX_MAX_RETRIES: int = 5
    OUTBOX_RETENTION_DAYS: int = 7

    # Monitoring y Alertas
    HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    HEALTH_CHECK_TIMEOUT_SECONDS: int = 90

    # Telegram Bot (opcional)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_ALERTAS_ENABLED: bool = False

    # Backup
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "./backups"
    BACKUP_SCHEDULE_CRON: str = "0 2 * * *"  # 2 AM diario

    # Logs
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json o text
    LOG_ROTATION_SIZE: str = "100MB"
    LOG_RETENTION_DAYS: int = 30

    # Performance
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_CONCURRENT_REQUESTS: int = 50

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Asegurar que el directorio de la BD existe"""
        if v.startswith("sqlite:"):
            # Extraer path del archivo SQLite
            db_path = v.split("///")[1].split("?")[0]
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        return v

    @validator("INFLACION_MENSUAL")
    def validate_inflacion(cls, v):
        """Validar inflación en rango razonable"""
        if not 0 <= v <= 50:
            raise ValueError("Inflación mensual debe estar entre 0% y 50%")
        return v

    @validator("TEMPORADA")
    def validate_temporada(cls, v):
        """Validar temporada argentina"""
        temporadas_validas = ["verano", "invierno", "otoño", "primavera"]
        if v not in temporadas_validas:
            raise ValueError(f"Temporada debe ser una de: {temporadas_validas}")
        return v

    def get_factor_stock_actual(self) -> float:
        """Obtiene factor de stock para temporada actual"""
        factores = {
            "verano": self.FACTOR_STOCK_VERANO,
            "invierno": self.FACTOR_STOCK_INVIERNO, 
            "otoño": self.FACTOR_STOCK_OTOÑO,
            "primavera": self.FACTOR_STOCK_PRIMAVERA
        }
        return factores.get(self.TEMPORADA, 1.0)

    def get_inflacion_diaria(self) -> float:
        """Calcula inflación diaria desde mensual"""
        # Fórmula: (1 + inflacion_mensual/100)^(1/30.44) - 1
        return (1 + self.INFLACION_MENSUAL/100)**(1/30.44) - 1

    def is_alertas_enabled(self) -> bool:
        """Verifica si las alertas Telegram están configuradas"""
        return (self.TELEGRAM_ALERTAS_ENABLED and 
                self.TELEGRAM_BOT_TOKEN and 
                self.TELEGRAM_CHAT_ID)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Factory function para settings con cache LRU"""
    return Settings()


# Configuración de logging estructurado
def setup_logging():
    """Configura logging para el sistema"""
    import logging
    import logging.handlers
    import json
    from datetime import datetime

    settings = get_settings()

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno
            }

            if hasattr(record, "extra_data"):
                log_entry.update(record.extra_data)

            return json.dumps(log_entry, ensure_ascii=False)

    # Crear logger root
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Handler para archivo con rotación
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/inventario-retail.log",
        maxBytes=100*1024*1024,  # 100MB
        backupCount=5
    )

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    logger.addHandler(handler)

    # Handler para consola (desarrollo)
    if settings.LOG_LEVEL == "DEBUG":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(console_handler)

    return logger


# Instancia global de settings para import directo
settings = get_settings()
