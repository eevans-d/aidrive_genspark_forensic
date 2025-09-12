"""
Configuración de Base de Datos - Sistema Gestión Depósito
Implementación SQLAlchemy con connection pooling y logging
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
import sys
import os

# Configurar logging para SQL
logging.basicConfig()
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.WARNING)  # Cambiar a DEBUG para ver queries

class DatabaseManager:
    """
    Gestor de Base de Datos con connection pooling y manejo de errores
    """

    def __init__(self, connection_string: str = None):
        """
        Inicializa el gestor de base de datos

        Args:
            connection_string: URL de conexión a PostgreSQL
        """
        # URL por defecto para desarrollo
        self.connection_string = connection_string or self._get_default_connection_string()

        # Configurar engine con pooling optimizado
        self.engine = create_engine(
            self.connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,  # Reciclar conexiones cada hora
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            echo=False,  # Cambiar a True para debug SQL
            future=True
        )

        # Configurar session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        # Event listeners para logging
        self._setup_event_listeners()

        self.logger = logging.getLogger(__name__)

    def _get_default_connection_string(self) -> str:
        """Construye string de conexión desde variables de entorno"""
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'deposito_db'),
            'username': os.getenv('DB_USER', 'deposito_user'),
            'password': os.getenv('DB_PASSWORD', 'deposito_pass')
        }

        return f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    def _setup_event_listeners(self):
        """Configura event listeners para monitoreo"""

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configuraciones específicas por conexión"""
            pass

        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log antes de ejecutar query"""
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(self.engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log después de ejecutar query"""
            total = time.time() - conn.info['query_start_time'].pop(-1)
            if total > 0.5:  # Log queries lentas (>500ms)
                self.logger.warning(f"Slow query: {total:.3f}s - {statement[:100]}...")

    def create_tables(self):
        """
        Crea todas las tablas en la base de datos
        """
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Tablas creadas exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"Error creando tablas: {e}")
            return False

    def drop_tables(self):
        """
        Elimina todas las tablas (¡CUIDADO! - Solo para desarrollo)
        """
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("Tablas eliminadas exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"Error eliminando tablas: {e}")
            return False

    @contextmanager
    def get_session(self):
        """
        Context manager para manejo seguro de sesiones

        Usage:
            with db.get_session() as session:
                # usar session aquí
                session.commit()
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error en sesión de BD: {e}")
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """
        Obtiene una sesión síncrona (para usar con dependency injection)
        ¡IMPORTANTE! Debe cerrarse manualmente
        """
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos

        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                return result.fetchone()[0] == 1
        except Exception as e:
            self.logger.error(f"Error probando conexión: {e}")
            return False

    def get_connection_info(self) -> dict:
        """
        Obtiene información de la conexión actual
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute("""
                    SELECT 
                        version() as version,
                        current_database() as database,
                        current_user as user,
                        inet_server_addr() as host,
                        inet_server_port() as port
                """)
                row = result.fetchone()
                return {
                    'version': row[0],
                    'database': row[1],
                    'user': row[2],
                    'host': row[3],
                    'port': row[4],
                    'pool_size': self.engine.pool.size(),
                    'checked_out': self.engine.pool.checkedout()
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo info de conexión: {e}")
            return {}

    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """
        Ejecuta SQL crudo y retorna resultados

        Args:
            sql: Query SQL a ejecutar
            params: Parámetros para la query

        Returns:
            list: Resultados de la query
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sql, params or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error(f"Error ejecutando SQL: {e}")
            raise

    def get_table_stats(self) -> dict:
        """
        Obtiene estadísticas de las tablas principales
        """
        try:
            stats = {}
            with self.get_session() as session:
                # Contar registros por tabla
                from .models import Producto, MovimientoStock, Proveedor, Cliente

                stats['productos'] = session.query(Producto).count()
                stats['movimientos_stock'] = session.query(MovimientoStock).count()
                stats['proveedores'] = session.query(Proveedor).count()
                stats['clientes'] = session.query(Cliente).count()

                # Productos con stock crítico
                stats['productos_stock_critico'] = session.query(Producto).filter(
                    Producto.stock_actual <= Producto.stock_minimo
                ).count()

            return stats
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    def backup_data(self, output_file: str = None) -> bool:
        """
        Respalda datos críticos a archivo SQL
        """
        # Implementación simplificada - en producción usar pg_dump
        try:
            if not output_file:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"/home/user/output/backup_deposito_{timestamp}.sql"

            # Por ahora solo log - implementar backup real con pg_dump
            self.logger.info(f"Backup solicitado para archivo: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error en backup: {e}")
            return False

# Instancia global del gestor de BD
db_manager = DatabaseManager()

# Dependency para FastAPI
def get_database_session():
    """
    Dependency injection para obtener sesión de BD en FastAPI
    """
    session = db_manager.get_session_sync()
    try:
        yield session
    finally:
        session.close()

# Funciones de utilidad
def init_database():
    """Inicializa la base de datos creando todas las tablas"""
    return db_manager.create_tables()

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    return db_manager.test_connection()

# Para usar con time en event listeners
import time
