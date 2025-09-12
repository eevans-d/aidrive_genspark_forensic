# Sistema Bancario - Guía de Deployment

## 📋 Tabla de Contenidos
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación Rápida](#instalación-rápida)
- [Configuración Detallada](#configuración-detallada)
- [Base de Datos](#base-de-datos)
- [Variables de Entorno](#variables-de-entorno)
- [Comandos de Deployment](#comandos-de-deployment)
- [Verificación del Sistema](#verificación-del-sistema)
- [Monitoreo y Logs](#monitoreo-y-logs)
- [Troubleshooting](#troubleshooting)
- [Mantenimiento](#mantenimiento)

## 🖥️ Requisitos del Sistema

### Hardware Mínimo
- **CPU**: 4 cores, 2.0 GHz
- **RAM**: 8 GB (16 GB recomendado)
- **Disco**: 50 GB SSD (100 GB recomendado)
- **Red**: 100 Mbps

### Software
- **Docker**: v20.10.0+
- **Docker Compose**: v2.0.0+
- **Python**: 3.9+ (para desarrollo local)
- **Git**: v2.30.0+

### Puertos Requeridos
```
80     - Nginx (HTTP)
443    - Nginx (HTTPS)
3000   - Web Interface
5432   - PostgreSQL
6379   - Redis
8001   - Agente Depósito
8002   - Agente Negocio
8003   - ML Service
```

## 🚀 Instalación Rápida

### 1. Clonación del Repositorio
```bash
git clone https://github.com/tu-usuario/sistema-bancario.git
cd sistema-bancario
```

### 2. Setup Automático
```bash
# Ejecutar script de setup completo
python scripts/setup_complete.py

# O manualmente:
chmod +x scripts/quick_setup.sh
./scripts/quick_setup.sh
```

### 3. Levantar Servicios
```bash
# Desarrollo completo
docker-compose -f docker-compose.development.yml up -d

# Solo servicios core
docker-compose -f docker-compose.development.yml up -d postgres redis agente-deposito agente-negocio
```

## ⚙️ Configuración Detallada

### Estructura de Directorios
```
sistema-bancario/
├── data/
│   ├── postgres/          # Datos PostgreSQL
│   └── redis/            # Datos Redis
├── logs/
│   ├── app/              # Logs aplicación
│   ├── nginx/            # Logs Nginx
│   └── postgres/         # Logs PostgreSQL
├── uploads/              # Archivos subidos
├── models/
│   ├── ocr/              # Modelos OCR
│   └── ml/               # Modelos ML
├── reports/              # Reportes generados
├── backups/              # Backups automáticos
├── nginx/
│   ├── nginx.conf        # Configuración Nginx
│   └── ssl/              # Certificados SSL
└── scripts/
    ├── init_db.sql       # Inicialización BD
    ├── setup_complete.py # Setup automático
    └── backup.sh         # Script backup
```

### Crear Estructura
```bash
mkdir -p {data/{postgres,redis},logs/{app,nginx,postgres},uploads,models/{ocr,ml},reports,backups,nginx/ssl}
```

## 🗄️ Base de Datos

### Inicialización PostgreSQL
```bash
# Crear usuario y base de datos
docker exec -it sistema_bancario_db psql -U postgres -c "
CREATE DATABASE sistema_bancario;
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE sistema_bancario TO app_user;
"

# Ejecutar migraciones
docker exec -it agente_deposito_service alembic upgrade head
```

### Script de Inicialización (scripts/init_db.sql)
```sql
-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Crear schemas
CREATE SCHEMA IF NOT EXISTS deposits;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS reports;

-- Configuración inicial
INSERT INTO system_config (key, value) VALUES 
('ocr.confidence_threshold', '0.8'),
('ml.risk_threshold', '0.7'),
('business.max_loan_amount', '1000000');
```

## 🔐 Variables de Entorno

### Archivo .env (Desarrollo)
```env
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
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
API_VERSION=v1

# OCR
OCR_MODEL_PATH=/app/models/ocr
OCR_CONFIDENCE_THRESHOLD=0.8
UPLOAD_MAX_SIZE=10485760  # 10MB

# Machine Learning
ML_MODEL_PATH=/app/models/ml
RISK_THRESHOLD=0.7
MODEL_UPDATE_INTERVAL=3600
TRAINING_DATA_PATH=/app/data/training

# Negocio
MAX_LOAN_AMOUNT=1000000
INTEREST_RATE_MIN=0.05
INTEREST_RATE_MAX=0.25

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
```

### Archivo .env.production
```env
# Base de Datos
DATABASE_URL=postgresql://app_user:${DB_PASSWORD}@postgres:5432/sistema_bancario
POSTGRES_PASSWORD=${DB_PASSWORD}

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# Aplicación
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=${SECRET_KEY}

# SSL
SSL_ENABLED=true
FORCE_HTTPS=true

# Seguridad
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

## 🐳 Comandos de Deployment

### Desarrollo Local
```bash
# Iniciar todo el stack
docker-compose -f docker-compose.development.yml up -d

# Ver logs en tiempo real
docker-compose -f docker-compose.development.yml logs -f

# Reiniciar un servicio específico
docker-compose -f docker-compose.development.yml restart agente-deposito

# Parar todo
docker-compose -f docker-compose.development.yml down

# Limpiar volúmenes (¡CUIDADO! Borra datos)
docker-compose -f docker-compose.development.yml down -v
```

### Producción
```bash
# Build y deploy
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# Rolling update (sin downtime)
docker-compose -f docker-compose.production.yml up -d --no-deps agente-deposito
```

### Comandos Útiles
```bash
# Backup base de datos
docker exec sistema_bancario_db pg_dump -U postgres sistema_bancario > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker exec -i sistema_bancario_db psql -U postgres sistema_bancario < backup_20231201.sql

# Verificar salud de servicios
docker-compose -f docker-compose.development.yml ps

# Ver recursos utilizados
docker stats

# Limpiar contenedores y imágenes no utilizadas
docker system prune -a
```

## ✅ Verificación del Sistema

### Health Checks Automáticos
```bash
# Verificar todos los servicios
curl http://localhost:8001/health  # Agente Depósito
curl http://localhost:8002/health  # Agente Negocio
curl http://localhost:8003/health  # ML Service

# Verificar base de datos
docker exec sistema_bancario_db pg_isready -U postgres

# Verificar Redis
docker exec sistema_bancario_redis redis-cli ping
```

### Script de Verificación
```bash
#!/bin/bash
# scripts/verify_deployment.sh

echo "🔍 Verificando Sistema Bancario..."

# Verificar servicios
services=("agente-deposito:8001" "agente-negocio:8002" "ml-service:8003")
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "✅ $name: OK"
    else
        echo "❌ $name: FAIL"
    fi
done

# Verificar base de datos
if docker exec sistema_bancario_db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL: OK"
else
    echo "❌ PostgreSQL: FAIL"
fi

# Verificar Redis
if docker exec sistema_bancario_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAIL"
fi

echo "🏁 Verificación completada"
```

## 📊 Monitoreo y Logs

### Logs Centralizados
```bash
# Ver logs de todos los servicios
docker-compose -f docker-compose.development.yml logs -f

# Logs de un servicio específico
docker-compose -f docker-compose.development.yml logs -f agente-deposito

# Logs con filtro de tiempo
docker-compose -f docker-compose.development.yml logs --since="1h" agente-deposito

# Buscar errores específicos
docker-compose -f docker-compose.development.yml logs | grep ERROR
```

### Configuración de Logging
```python
# config/logging.py
import logging
from loguru import logger

# Configuración Loguru
logger.add(
    "/app/logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
```

### Métricas con Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sistema-bancario'
    static_configs:
      - targets: ['agente-deposito:8001', 'agente-negocio:8002', 'ml-service:8003']
    metrics_path: '/metrics'
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Servicio no inicia
```bash
# Verificar logs
docker-compose logs nombre-servicio

# Verificar configuración
docker-compose config

# Verificar puertos
netstat -tulpn | grep :8001
```

#### 2. Error de conexión a PostgreSQL
```bash
# Verificar estado
docker exec sistema_bancario_db pg_isready -U postgres

# Verificar logs
docker logs sistema_bancario_db

# Reiniciar servicio
docker-compose restart postgres
```

#### 3. Redis no responde
```bash
# Verificar conexión
docker exec sistema_bancario_redis redis-cli ping

# Ver configuración
docker exec sistema_bancario_redis redis-cli CONFIG GET "*"

# Limpiar cache si es necesario
docker exec sistema_bancario_redis redis-cli FLUSHALL
```

#### 4. Problemas de permisos
```bash
# Ajustar permisos de directorios
sudo chown -R $USER:$USER data/ logs/ uploads/
chmod -R 755 data/ logs/ uploads/
```

#### 5. Memoria insuficiente
```bash
# Verificar uso de memoria
docker stats --no-stream

# Ajustar límites en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

### Comandos de Diagnóstico
```bash
# Estado general del sistema
docker system df
docker system events

# Información detallada de contenedores
docker inspect nombre-contenedor

# Procesos internos del contenedor
docker exec nombre-contenedor ps aux

# Uso de recursos
docker exec nombre-contenedor top
```

## 🔄 Mantenimiento

### Backups Automáticos
```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/app/backups"

# Backup PostgreSQL
docker exec sistema_bancario_db pg_dump -U postgres sistema_bancario > "$BACKUP_DIR/db_backup_$DATE.sql"

# Backup archivos importantes
tar -czf "$BACKUP_DIR/files_backup_$DATE.tar.gz" uploads/ models/

# Limpiar backups antiguos (mantener 7 días)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

### Actualizaciones
```bash
# Actualizar imágenes
docker-compose pull

# Rebuild servicios
docker-compose build --no-cache

# Rolling update sin downtime
docker-compose up -d --no-deps servicio-a-actualizar
```

### Monitoreo de Salud
```bash
# Script de monitoreo (cron cada 5 minutos)
#!/bin/bash
# scripts/health_monitor.sh

SERVICES=("agente-deposito:8001" "agente-negocio:8002" "ml-service:8003")

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"

    if ! curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "❌ $name down - restarting..."
        docker-compose restart "$name"

        # Enviar alerta (opcional)
        # curl -X POST "webhook-url" -d "Service $name is down"
    fi
done
```

### Limpieza Periódica
```bash
# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete

# Limpiar archivos temporales
find uploads/ -name "temp_*" -mtime +1 -delete

# Limpiar imágenes Docker no utilizadas
docker image prune -a -f

# Limpiar volúmenes huérfanos
docker volume prune -f
```

## 📞 Soporte

### Información de Sistema
```bash
# Generar reporte de sistema
scripts/system_report.sh > system_report_$(date +%Y%m%d).txt
```

### Contactos
- **Desarrollo**: equipo-dev@empresa.com
- **DevOps**: devops@empresa.com
- **Soporte**: soporte@empresa.com

### Enlaces Útiles
- [Documentación API](http://localhost:8001/docs)
- [Dashboard Grafana](http://localhost:3001)
- [Métricas Prometheus](http://localhost:9090)
- [Logs Kibana](http://localhost:5601)

---
*Última actualización: 2024-01-01*
*Versión: 1.0.0*
