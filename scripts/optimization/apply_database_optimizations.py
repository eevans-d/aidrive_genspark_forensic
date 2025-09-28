#!/usr/bin/env python3
"""
Script para aplicar optimizaciones de base de datos específicas por submódulo
Ejecuta automáticamente las configuraciones SQL creadas
"""
import os
import sys
import logging
import sqlite3
import psycopg2
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Aplicar optimizaciones de base de datos por submódulo"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "config" / "database"
        
    def apply_sqlite_optimizations(self, db_path: str) -> bool:
        """
        Aplicar optimizaciones SQLite para inventario-retail
        """
        sqlite_config = self.config_path / "inventario_sqlite_pragmas.sql"
        
        if not sqlite_config.exists():
            logger.error(f"SQLite config not found: {sqlite_config}")
            return False
            
        try:
            # Verificar que la base de datos existe
            if not os.path.exists(db_path):
                logger.warning(f"SQLite database not found: {db_path}")
                logger.info("Skipping SQLite optimizations - database will be created when needed")
                return True
            
            logger.info(f"Applying SQLite optimizations to: {db_path}")
            
            with sqlite3.connect(db_path) as conn:
                # Leer y ejecutar el archivo de configuración
                with open(sqlite_config, 'r') as f:
                    sql_content = f.read()
                
                # Ejecutar comandos uno por uno
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            conn.execute(statement)
                            logger.debug(f"Executed: {statement[:50]}...")
                        except sqlite3.Error as e:
                            logger.warning(f"SQLite warning: {e} for statement: {statement[:50]}")
                
                conn.commit()
                
            # Verificar optimizaciones aplicadas
            stats = self._verify_sqlite_optimizations(db_path)
            logger.info(f"SQLite optimizations applied successfully: {stats}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying SQLite optimizations: {e}")
            return False
    
    def apply_postgresql_optimizations(self, connection_params: Dict[str, str]) -> bool:
        """
        Aplicar optimizaciones PostgreSQL para BI orchestrator
        """
        pg_config = self.config_path / "bi_postgresql_indices.sql"
        
        if not pg_config.exists():
            logger.error(f"PostgreSQL config not found: {pg_config}")
            return False
            
        try:
            logger.info(f"Applying PostgreSQL optimizations to: {connection_params.get('host', 'localhost')}")
            
            # Construir string de conexión
            conn_string = (
                f"host={connection_params.get('host', 'localhost')} "
                f"port={connection_params.get('port', '5432')} "
                f"dbname={connection_params.get('database', 'business_intelligence')} "
                f"user={connection_params.get('user', 'bi_user')} "
                f"password={connection_params.get('password', 'password')}"
            )
            
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Leer archivo de configuración
                    with open(pg_config, 'r') as f:
                        sql_content = f.read()
                    
                    # Ejecutar comandos
                    for statement in sql_content.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                cursor.execute(statement)
                                logger.debug(f"Executed: {statement[:50]}...")
                            except psycopg2.Error as e:
                                logger.warning(f"PostgreSQL warning: {e} for statement: {statement[:50]}")
                
                conn.commit()
                
            # Verificar optimizaciones
            stats = self._verify_postgresql_optimizations(connection_params)
            logger.info(f"PostgreSQL optimizations applied successfully: {stats}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying PostgreSQL optimizations: {e}")
            return False
    
    def _verify_sqlite_optimizations(self, db_path: str) -> Dict[str, str]:
        """Verificar que las optimizaciones SQLite fueron aplicadas"""
        stats = {}
        
        try:
            with sqlite3.connect(db_path) as conn:
                # Verificar WAL mode
                cursor = conn.execute("PRAGMA journal_mode")
                stats['journal_mode'] = cursor.fetchone()[0]
                
                # Verificar cache size
                cursor = conn.execute("PRAGMA cache_size")
                stats['cache_size'] = str(cursor.fetchone()[0])
                
                # Verificar foreign keys
                cursor = conn.execute("PRAGMA foreign_keys")
                stats['foreign_keys'] = str(cursor.fetchone()[0])
                
                # Contar índices creados
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
                )
                stats['custom_indexes'] = str(cursor.fetchone()[0])
                
        except Exception as e:
            logger.error(f"Error verifying SQLite optimizations: {e}")
            stats['error'] = str(e)
            
        return stats
    
    def _verify_postgresql_optimizations(self, connection_params: Dict[str, str]) -> Dict[str, str]:
        """Verificar que las optimizaciones PostgreSQL fueron aplicadas"""
        stats = {}
        
        try:
            conn_string = (
                f"host={connection_params.get('host', 'localhost')} "
                f"port={connection_params.get('port', '5432')} "
                f"dbname={connection_params.get('database', 'business_intelligence')} "
                f"user={connection_params.get('user', 'bi_user')} "
                f"password={connection_params.get('password', 'password')}"
            )
            
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Contar índices concurrentes creados
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM pg_indexes 
                        WHERE indexname LIKE 'idx_%'
                    """)
                    stats['custom_indexes'] = str(cursor.fetchone()[0])
                    
                    # Verificar extensiones
                    cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname IN ('pg_trgm', 'pg_stat_statements')")
                    stats['extensions'] = str(cursor.fetchone()[0])
                    
                    # Verificar estadísticas actualizadas
                    cursor.execute("SELECT schemaname, tablename FROM pg_stat_user_tables LIMIT 5")
                    stats['analyzed_tables'] = str(len(cursor.fetchall()))
                    
        except Exception as e:
            logger.error(f"Error verifying PostgreSQL optimizations: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def optimize_all_databases(self, config: Dict[str, Dict[str, str]]) -> bool:
        """
        Aplicar optimizaciones a todas las bases de datos configuradas
        """
        success = True
        
        # 1. Optimizar SQLite para inventario-retail
        if 'sqlite' in config:
            sqlite_config = config['sqlite']
            db_path = sqlite_config.get('database_path', 'inventario-retail/data/inventario.db')
            full_db_path = self.project_root / db_path
            
            if not self.apply_sqlite_optimizations(str(full_db_path)):
                success = False
        
        # 2. Optimizar PostgreSQL para BI orchestrator
        if 'postgresql' in config:
            pg_config = config['postgresql']
            if not self.apply_postgresql_optimizations(pg_config):
                success = False
        
        # 3. Optimizar PostgreSQL para sistema_deposito
        if 'postgresql_deposito' in config:
            deposito_config = config['postgresql_deposito']
            if not self.apply_postgresql_optimizations(deposito_config):
                success = False
        
        return success


def load_database_config() -> Dict[str, Dict[str, str]]:
    """
    Cargar configuración de bases de datos desde variables de entorno
    """
    config = {}
    
    # SQLite para inventario-retail
    config['sqlite'] = {
        'database_path': os.getenv('SQLITE_DB_PATH', 'inventario-retail/data/inventario.db')
    }
    
    # PostgreSQL para BI orchestrator
    config['postgresql'] = {
        'host': os.getenv('BI_PG_HOST', 'localhost'),
        'port': os.getenv('BI_PG_PORT', '5432'),
        'database': os.getenv('BI_PG_DATABASE', 'business_intelligence'),
        'user': os.getenv('BI_PG_USER', 'bi_user'),
        'password': os.getenv('BI_PG_PASSWORD', 'password')
    }
    
    # PostgreSQL para sistema_deposito
    config['postgresql_deposito'] = {
        'host': os.getenv('DEPOSITO_PG_HOST', 'localhost'),
        'port': os.getenv('DEPOSITO_PG_PORT', '5432'),
        'database': os.getenv('DEPOSITO_PG_DATABASE', 'deposito_db'),
        'user': os.getenv('DEPOSITO_PG_USER', 'deposito_user'),
        'password': os.getenv('DEPOSITO_PG_PASSWORD', 'deposito_pass')
    }
    
    return config


def main():
    """Función principal del script"""
    if len(sys.argv) < 2:
        print("Uso: python apply_database_optimizations.py <project_root_path>")
        print("Ejemplo: python apply_database_optimizations.py /path/to/aidrive_genspark_forensic")
        sys.exit(1)
    
    project_root = sys.argv[1]
    
    if not os.path.exists(project_root):
        logger.error(f"Project root not found: {project_root}")
        sys.exit(1)
    
    logger.info(f"Starting database optimizations for project: {project_root}")
    
    # Cargar configuración
    config = load_database_config()
    logger.info(f"Loaded configuration for databases: {list(config.keys())}")
    
    # Aplicar optimizaciones
    optimizer = DatabaseOptimizer(project_root)
    
    if optimizer.optimize_all_databases(config):
        logger.info("✅ All database optimizations applied successfully")
        sys.exit(0)
    else:
        logger.error("❌ Some database optimizations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()