"""
Cache Manager para ML Service
Gestión de cache con Redis y configuración de tipos.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheType(str, Enum):
    PREDICTION = "prediction"
    MODEL = "model"
    DATA = "data"

class CacheConfig:
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size

class MLCacheManager:
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.cache = {}  # Simple dict cache for now
        self.logger = logger

    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache."""
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Establece valor en cache."""
        self.cache[key] = value

    def delete(self, key: str) -> None:
        """Elimina clave del cache."""
        self.cache.pop(key, None)

    def clear(self) -> None:
        """Limpia todo el cache."""
        self.cache.clear()