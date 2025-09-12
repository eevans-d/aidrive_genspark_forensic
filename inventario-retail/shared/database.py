"""
Configuración de base de datos SQLAlchemy 2.0 + SQLite WAL
Optimizada para concurrencia y contexto retail argentino
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Base para modelos SQLAlchemy
Base = declarative_base()

# Engine SQLAlchemy con configuración WAL
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,  # Reciclar conexiones cada 5 min
    connect_args={
        "check_same_thread": False,  # Permitir threads múltiples
        "timeout": 20,  # Timeout conexión 20s
    }
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Configura SQLite para máximo rendimiento y concurrencia
    WAL mode permite lecturas concurrentes
    """
    with dbapi_connection.cursor() as cursor:
        # WAL mode para concurrencia
        cursor.execute("PRAGMA journal_mode=WAL")

        # Optimizaciones performance
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance seguridad/speed
        cursor.execute("PRAGMA cache_size=10000")    # 10MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")   # Temp en RAM
        cursor.execute("PRAGMA mmap_size=268435456") # 256MB memory map

        # Timeouts para evitar locks
        cursor.execute("PRAGMA busy_timeout=30000")  # 30s timeout

        # Foreign keys habilitadas
        cursor.execute("PRAGMA foreign_keys=ON")

        # Checkpoint automático WAL
        cursor.execute("PRAGMA wal_autocheckpoint=1000")

        logger.debug("SQLite configurado con WAL mode y optimizaciones")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que provee sesiones de BD
    Con manejo automático de transacciones
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión BD: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """
    Inicializa la base de datos creando todas las tablas
    y configuraciones necesarias para el sistema
    """
    try:
        # Importar todos los modelos para que SQLAlchemy los registre
        from .models import Producto, MovimientoStock

        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)

        # Verificar que WAL mode está activo
        with SessionLocal() as session:
            result = session.execute(text("PRAGMA journal_mode")).fetchone()
            if result and result[0] == "wal":
                logger.info("✅ Base de datos inicializada con WAL mode")
            else:
                logger.warning("⚠️ WAL mode no configurado correctamente")

        logger.info("✅ Base de datos inicializada correctamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        raise


def health_check_db() -> dict:
    """
    Health check de la base de datos
    Retorna métricas de estado y performance
    """
    try:
        with SessionLocal() as session:
            # Test básico de conexión
            session.execute(text("SELECT 1")).fetchone()

            # Verificar WAL mode
            wal_mode = session.execute(text("PRAGMA journal_mode")).fetchone()[0]

            # Estadísticas WAL
            wal_stats = session.execute(text("PRAGMA wal_checkpoint(PASSIVE)")).fetchone()

            # Tamaño BD
            page_count = session.execute(text("PRAGMA page_count")).fetchone()[0]
            page_size = session.execute(text("PRAGMA page_size")).fetchone()[0] 
            db_size_mb = (page_count * page_size) / (1024 * 1024)

            # Cache hits
            cache_stats = session.execute(text("PRAGMA cache_size")).fetchone()[0]

            return {
                "status": "healthy",
                "wal_mode": wal_mode,
                "db_size_mb": round(db_size_mb, 2),
                "page_count": page_count,
                "cache_size": cache_stats,
                "wal_frames": wal_stats[1] if wal_stats else 0,
                "connection_pool": {
                    "size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                    "checked_in": engine.pool.checkedin()
                }
            }

    except Exception as e:
        logger.error(f"Health check BD falló: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e)
        }


def optimize_database():
    """
    Operaciones de optimización y mantenimiento BD
    Ejecutar periódicamente para mantener performance
    """
    try:
        with SessionLocal() as session:
            # VACUUM incremental para recuperar espacio
            session.execute(text("PRAGMA incremental_vacuum"))

            # Analizar estadísticas para optimizar queries
            session.execute(text("ANALYZE"))

            # WAL checkpoint para consolidar cambios
            session.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))

            # Verificar integridad
            integrity = session.execute(text("PRAGMA integrity_check")).fetchall()

            if len(integrity) == 1 and integrity[0][0] == "ok":
                logger.info("✅ Optimización BD completada - Integridad OK")
                return True
            else:
                logger.error(f"❌ Problemas de integridad: {integrity}")
                return False

    except Exception as e:
        logger.error(f"Error en optimización BD: {e}")
        return False


class DatabaseManager:
    """
    Manager para operaciones avanzadas de BD
    Incluye backup, restore y estadísticas
    """

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def backup_database(self, backup_path: str) -> bool:
        """Crea backup completo de la BD"""
        try:
            import shutil
            import sqlite3

            # Extraer path real de la BD desde URL
            db_path = settings.DATABASE_URL.replace("sqlite:///", "").split("?")[0]

            # WAL checkpoint antes del backup
            with sqlite3.connect(db_path) as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            # Copiar archivo BD
            shutil.copy2(db_path, backup_path)

            logger.info(f"✅ Backup creado: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en backup: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restaura BD desde backup"""
        try:
            import shutil

            # Cerrar todas las conexiones
            engine.dispose()

            # Extraer path real de la BD
            db_path = settings.DATABASE_URL.replace("sqlite:///", "").split("?")[0]

            # Restaurar archivo
            shutil.copy2(backup_path, db_path)

            # Recrear engine
            global engine
            engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                poolclass=StaticPool,
                pool_pre_ping=True,
                connect_args={"check_same_thread": False}
            )

            logger.info(f"✅ BD restaurada desde: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en restore: {e}")
            return False

    def get_statistics(self) -> dict:
        """Obtiene estadísticas detalladas de la BD"""
        try:
            with SessionLocal() as session:
                # Importar modelos para contar registros
                from .models import Producto, MovimientoStock

                stats = {
                    "productos_total": session.query(Producto).count(),
                    "productos_stock_critico": session.query(Producto).filter(
                        Producto.stock_actual <= Producto.stock_minimo
                    ).count(),
                    "movimientos_total": session.query(MovimientoStock).count(),
                    "movimientos_hoy": session.execute(text("""
                        SELECT COUNT(*) FROM movimientos_stock 
                        WHERE DATE(timestamp) = DATE('now')
                    """)).scalar(),
                }

                # Agregar health check
                stats.update(health_check_db())

                return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}


# Instancia global del manager
db_manager = DatabaseManager()
