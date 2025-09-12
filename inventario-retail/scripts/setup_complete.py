#!/usr/bin/env python3
"""
Sistema Bancario - Setup Completo Automático
Inicializa todo el sistema con configuración, base de datos, y verificaciones
"""

import os
import sys
import time
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.required_dirs = [
            'data/postgres', 'data/redis', 'logs/app', 'logs/nginx', 
            'logs/postgres', 'uploads', 'models/ocr', 'models/ml',
            'reports', 'backups', 'nginx/ssl', 'scripts'
        ]
        self.services = {
            'agente-deposito': 8001,
            'agente-negocio': 8002,
            'ml-service': 8003
        }
        self.database_ready = False
        self.redis_ready = False

    def print_banner(self):
        """Mostrar banner de inicio"""
        banner = '''
╔══════════════════════════════════════════════════════════════╗
║                   SISTEMA BANCARIO                           ║
║              Setup Completo Automático                      ║
║                                                              ║
║  🏦 Agente Depósito  📊 ML Service   💼 Agente Negocio     ║
║  🗄️  PostgreSQL      🔄 Redis       📈 Schedulers           ║
╚══════════════════════════════════════════════════════════════╝
        '''
        print(banner)

    def check_dependencies(self) -> bool:
        """Verificar dependencias del sistema"""
        logger.info("🔍 Verificando dependencias del sistema...")

        dependencies = {
            'docker': ['docker', '--version'],
            'docker-compose': ['docker-compose', '--version'],
            'python': ['python', '--version'],
            'pip': ['pip', '--version']
        }

        missing = []
        for name, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✅ {name}: {result.stdout.strip()}")
                else:
                    missing.append(name)
            except FileNotFoundError:
                missing.append(name)

        if missing:
            logger.error(f"❌ Dependencias faltantes: {\', \'.join(missing)}")
            return False

        logger.info("✅ Todas las dependencias están disponibles")
        return True

    def create_directories(self):
        """Crear estructura de directorios"""
        logger.info("📁 Creando estructura de directorios...")

        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ {dir_path}")

        # Configurar permisos apropiados
        os.chmod(self.project_root / 'data', 0o755)
        os.chmod(self.project_root / 'logs', 0o755)
        os.chmod(self.project_root / 'uploads', 0o777)

        logger.info("✅ Estructura de directorios creada")

    def create_env_file(self):
        """Crear archivo de configuración .env"""
        logger.info("⚙️ Creando archivo de configuración...")

        env_content = \'\'\'# Sistema Bancario - Configuración de Desarrollo
# Generado automáticamente por setup_complete.py

# Base de Datos
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/sistema_bancario
POSTGRES_DB=sistema_bancario
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Aplicación
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=sistema-bancario-secret-key-development-2024
API_VERSION=v1
DEBUG=true

# OCR
OCR_MODEL_PATH=/app/models/ocr
OCR_CONFIDENCE_THRESHOLD=0.8
UPLOAD_MAX_SIZE=10485760
UPLOAD_DIR=/app/uploads

# Machine Learning
ML_MODEL_PATH=/app/models/ml
RISK_THRESHOLD=0.7
MODEL_UPDATE_INTERVAL=3600
TRAINING_DATA_PATH=/app/data/training

# Negocio
MAX_LOAN_AMOUNT=1000000
INTEREST_RATE_MIN=0.05
INTEREST_RATE_MAX=0.25
APPROVAL_THRESHOLD=0.6

# Scheduler
DAILY_REPORT_TIME=02:00
WEEKLY_REPORT_DAY=monday
MONTHLY_REPORT_DAY=1
BACKUP_TIME=03:00
CLEANUP_RETENTION_DAYS=30

# Nginx
DOMAIN_NAME=localhost
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
HEALTH_CHECK_INTERVAL=30

# Logging
LOG_FILE_PATH=/app/logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
\'\'\'

        env_path = self.project_root / '.env'
        with open(env_path, 'w') as f:
            f.write(env_content)

        logger.info("✅ Archivo .env creado")

    def generate_status_report(self):
        """Generar reporte de estado del sistema"""
        logger.info("📊 Generando reporte de estado...")

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system': {
                'database': self.database_ready,
                'redis': self.redis_ready
            },
            'services': {},
            'directories': {},
            'files': {}
        }

        # Verificar servicios
        for service, port in self.services.items():
            try:
                response = requests.get(f'http://localhost:{port}/health', timeout=5)
                report['services'][service] = {
                    'status': 'running' if response.status_code == 200 else 'error',
                    'port': port,
                    'response_time': response.elapsed.total_seconds()
                }
            except:
                report['services'][service] = {
                    'status': 'down',
                    'port': port
                }

        # Verificar directorios
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            report['directories'][dir_path] = full_path.exists()

        # Verificar archivos importantes
        important_files = [
            '.env', 'docker-compose.development.yml', 
            'requirements_final.txt', 'nginx/nginx.conf',
            'scripts/init_db.sql'
        ]

        for file_path in important_files:
            full_path = self.project_root / file_path
            report['files'][file_path] = full_path.exists()

        # Guardar reporte
        report_path = self.project_root / 'setup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📊 Reporte guardado en: {report_path}")
        return report

def main():
    """Función principal"""
    setup = SystemSetup()

    try:
        setup.print_banner()

        # Verificaciones previas
        if not setup.check_dependencies():
            sys.exit(1)

        # Crear estructura y configuración
        setup.create_directories()
        setup.create_env_file()

        # Generar reporte final
        report = setup.generate_status_report()

        logger.info("🎉 Setup completado exitosamente!")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Setup interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error durante el setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
