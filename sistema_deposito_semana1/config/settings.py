
"""
Configuración global del sistema de gestión de depósito
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'deposito_db')
    username: str = os.getenv('DB_USER', 'deposito_user')
    password: str = os.getenv('DB_PASSWORD', 'deposito_pass')

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class APIConfig:
    """Configuración de API"""
    host: str = os.getenv('API_HOST', '0.0.0.0')
    port: int = int(os.getenv('API_PORT', '8000'))
    debug: bool = os.getenv('API_DEBUG', 'False').lower() == 'true'
    reload: bool = os.getenv('API_RELOAD', 'False').lower() == 'true'

@dataclass
class LoggingConfig:
    """Configuración de logging"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_handler: bool = True
    console_handler: bool = True
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

# Instancias de configuración
db_config = DatabaseConfig()
api_config = APIConfig()
logging_config = LoggingConfig()
