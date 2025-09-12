"""
Sistema de backup automático con verificación
"""
import shutil
import os
import tarfile
import hashlib
from datetime import datetime
from shared.database import db_manager
from shared.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class BackupManager:
    def __init__(self):
        self.backup_dir = settings.BACKUP_PATH
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, backup_type: str = "full") -> str:
        """Crear backup completo del sistema"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Crear backup BD
            db_backup_path = f"{self.backup_dir}/db_backup_{timestamp}.db"
            if db_manager.backup_database(db_backup_path):
                logger.info(f"✅ Backup BD creado: {db_backup_path}")

            # Crear archivo tar.gz completo
            with tarfile.open(backup_path, "w:gz") as tar:
                # Agregar BD
                if os.path.exists(db_backup_path):
                    tar.add(db_backup_path, arcname="inventario.db")

                # Agregar configuración
                if os.path.exists(".env"):
                    tar.add(".env", arcname="config.env")

                # Agregar logs recientes
                if os.path.exists("logs"):
                    tar.add("logs", arcname="logs")

            # Limpiar backup temporal BD
            if os.path.exists(db_backup_path):
                os.remove(db_backup_path)

            # Verificar integridad
            if self.verify_backup(backup_path):
                logger.info(f"✅ Backup completo creado y verificado: {backup_name}")

                # Limpiar backups antiguos
                self._cleanup_old_backups()

                return backup_path
            else:
                logger.error(f"❌ Backup falló verificación: {backup_name}")
                return None

        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return None

    def verify_backup(self, backup_path: str) -> bool:
        """Verificar integridad del backup"""
        try:
            # Verificar que el archivo existe y no está vacío
            if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
                return False

            # Verificar que se puede abrir como tar.gz
            with tarfile.open(backup_path, "r:gz") as tar:
                # Verificar que contiene archivos esperados
                files = tar.getnames()
                required_files = ["inventario.db"]

                for required in required_files:
                    if required not in files:
                        logger.warning(f"Archivo requerido no encontrado en backup: {required}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error verificando backup: {e}")
            return False

    def _cleanup_old_backups(self):
        """Limpiar backups antiguos según retención"""
        try:
            retention_days = settings.BACKUP_RETENTION_DAYS
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)

            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".tar.gz"):
                    file_path = os.path.join(self.backup_dir, filename)
                    if os.path.getctime(file_path) < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"🗑️ Backup antiguo eliminado: {filename}")

        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {e}")
