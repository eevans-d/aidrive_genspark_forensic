"""
Dependencies - FastAPI Dependency Injection
Versión: 2.0 - Production Ready

Dependencies para:
- Gestión de sesiones de base de datos
- Manejo de errores centralizado
- Validaciones automáticas
- Logging y auditoria
- Authentication (preparado para futuro)
"""

import logging
from typing import Generator, Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from .services import ServiceError, ValidationError, NotFoundError
from datetime import datetime
from .stock_manager_complete import StockManagerError, InsufficientStockError, ProductNotFoundError, ConcurrencyError

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de base de datos (en producción usar variables de entorno)
DATABASE_URL = "sqlite:///./agente_deposito.db"  # Cambiar por PostgreSQL en producción

# Crear engine y session
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # True para debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas
Base.metadata.create_all(bind=engine)


# === DATABASE SESSION DEPENDENCY ===

def get_database() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos con manejo automático
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# === ERROR HANDLERS ===

class ErrorHandler:
    """
    Manejador centralizado de errores
    """

    @staticmethod
    def handle_service_error(error: Exception) -> HTTPException:
        """
        Convierte errores de servicio en HTTPException apropiadas
        """
        error_mappings = {
            NotFoundError: (status.HTTP_404_NOT_FOUND, "Recurso no encontrado"),
            ValidationError: (status.HTTP_400_BAD_REQUEST, "Error de validación"),
            InsufficientStockError: (status.HTTP_400_BAD_REQUEST, "Stock insuficiente"),
            ProductNotFoundError: (status.HTTP_404_NOT_FOUND, "Producto no encontrado"),
            ConcurrencyError: (status.HTTP_409_CONFLICT, "Conflicto de concurrencia"),
            StockManagerError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Error en gestión de stock"),
            ServiceError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Error interno del servicio"),
            SQLAlchemyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Error de base de datos")
        }

        for error_type, (status_code, default_message) in error_mappings.items():
            if isinstance(error, error_type):
                return HTTPException(
                    status_code=status_code,
                    detail={
                        "error": default_message,
                        "message": str(error),
                        "type": error_type.__name__
                    }
                )

        # Error genérico
        logger.error(f"Error no manejado: {type(error).__name__}: {str(error)}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error interno del servidor",
                "message": "Ha ocurrido un error inesperado",
                "type": "InternalServerError"
            }
        )


def get_error_handler() -> ErrorHandler:
    """
    Dependency para obtener el manejador de errores
    """
    return ErrorHandler()


# === VALIDATION DEPENDENCIES ===

def validate_positive_int(value: int, field_name: str = "valor") -> int:
    """
    Valida que un entero sea positivo
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} debe ser un número positivo"
        )
    return value


def validate_non_negative_int(value: int, field_name: str = "valor") -> int:
    """
    Valida que un entero sea no negativo
    """
    if value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} no puede ser negativo"
        )
    return value


def validate_pagination_params(page: int = 1, size: int = 20) -> dict:
    """
    Valida parámetros de paginación
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La página debe ser mayor que 0"
        )

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tamaño de página debe estar entre 1 y 100"
        )

    return {"page": page, "size": size}


# === LOGGING DEPENDENCIES ===

class RequestLogger:
    """
    Logger para requests con contexto
    """

    def __init__(self, request: Request):
        self.request = request
        self.start_time = None

    def log_request_start(self):
        """
        Log del inicio de request
        """
        import time
        self.start_time = time.time()

        logger.info(
            f"REQUEST START: {self.request.method} {self.request.url.path} "
            f"- Client: {self.request.client.host if self.request.client else 'unknown'}"
        )

    def log_request_end(self, status_code: int):
        """
        Log del final de request
        """
        import time
        duration = time.time() - self.start_time if self.start_time else 0

        logger.info(
            f"REQUEST END: {self.request.method} {self.request.url.path} "
            f"- Status: {status_code} - Duration: {duration:.3f}s"
        )


def get_request_logger(request: Request) -> RequestLogger:
    """
    Dependency para obtener logger de request
    """
    return RequestLogger(request)


# === AUTHENTICATION DEPENDENCIES (PREPARADO PARA FUTURO) ===

class AuthenticationManager:
    """
    Gestor de autenticación (preparado para implementación futura)
    """

    def __init__(self):
        self.current_user = "SYSTEM"  # Por ahora usuario por defecto

    def get_current_user(self) -> str:
        """
        Obtiene el usuario actual (placeholder)
        """
        return self.current_user

    def validate_permissions(self, action: str) -> bool:
        """
        Valida permisos (placeholder)
        """
        return True  # Por ahora todo permitido


def get_current_user(auth_manager: AuthenticationManager = Depends()) -> str:
    """
    Dependency para obtener usuario actual
    """
    return auth_manager.get_current_user()


def get_auth_manager() -> AuthenticationManager:
    """
    Dependency para obtener gestor de autenticación
    """
    return AuthenticationManager()


# === DECORATOR PARA MANEJO DE ERRORES ===

def handle_errors(func):
    """
    Decorator para manejo automático de errores en endpoints
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            error_handler = ErrorHandler()
            raise error_handler.handle_service_error(e)

    return wrapper


# === CONTEXT MANAGERS ===

@contextmanager
def database_transaction(db: Session):
    """
    Context manager para transacciones de base de datos
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rollback debido a error: {str(e)}")
        raise


# === UTILITY DEPENDENCIES ===

def get_request_id(request: Request) -> str:
    """
    Genera un ID único para el request para tracking
    """
    import uuid
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    return request_id


async def log_slow_requests(request: Request, call_next):
    """
    Middleware para detectar requests lentos
    """
    import time
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    if process_time > 1.0:  # Requests que toman más de 1 segundo
        logger.warning(
            f"SLOW REQUEST: {request.method} {request.url.path} "
            f"took {process_time:.3f}s"
        )

    response.headers["X-Process-Time"] = str(process_time)
    return response


# === HEALTH CHECK DEPENDENCIES ===

def check_database_health(db: Session = Depends(get_database)) -> dict:
    """
    Verifica el estado de salud de la base de datos
    """
    try:
        # Ejecutar query simple para verificar conexión
        db.execute("SELECT 1")
        return {"database": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"database": "unhealthy", "error": str(e)}


def get_system_health() -> dict:
    """
    Obtiene el estado general del sistema
    """
    import psutil
    import time

    return {
        "timestamp": time.time(),
        "uptime": time.time() - psutil.boot_time(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }


# === RESPONSE HELPERS ===

class ResponseBuilder:
    """
    Constructor de respuestas estandarizadas
    """

    @staticmethod
    def success(data: Any = None, message: str = "Operación exitosa") -> dict:
        """
        Construye respuesta de éxito
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        if data is not None:
            response["data"] = data

        return response

    @staticmethod
    def error(message: str, details: Any = None) -> dict:
        """
        Construye respuesta de error
        """
        response = {
            "success": False,
            "error": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        if details is not None:
            response["details"] = details

        return response


def get_response_builder() -> ResponseBuilder:
    """
    Dependency para obtener constructor de respuestas
    """
    return ResponseBuilder()
