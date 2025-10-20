# PLAN DE DESPLIEGUE PERSONALIZADO - SISTEMA INVENTARIO RETAIL
## Resultado de aplicar PROMPT 2 con GitHub Copilot Pro

---

## 1. PREPARACIÓN PRE-DESPLIEGUE

### Checklist Completo de Verificación de Código
```bash
# Verificación de dependencias y ambiente
- [ ] Python 3.11+ instalado y configurado
- [ ] Todas las dependencias en requirements_final.txt disponibles
- [ ] Variables de entorno configuradas correctamente
- [ ] Base de datos PostgreSQL accesible
- [ ] Redis server funcional
- [ ] Tesseract OCR instalado (para OCR de facturas AFIP)
- [ ] OpenCV dependencies disponibles

# Tests y validación
- [ ] Tests unitarios pasando: python -m pytest tests/
- [ ] Tests de integración: python -m pytest tests/integration/
- [ ] Health checks funcionando en todos los servicios
- [ ] OCR de facturas AFIP funcionando correctamente
- [ ] ML models cargando sin errores
- [ ] Conectividad con APIs externas (OpenAI, AFIP, Telegram)

# Seguridad y compliance
- [ ] Secrets y API keys no hardcodeadas
- [ ] JWT secrets generados securely
- [ ] CORS configurado correctamente
- [ ] Rate limiting implementado
- [ ] AFIP compliance validado
```

### Configuraciones Específicas para Producción
```bash
# Archivos de configuración críticos
cp .env.production.template .env.production
cp docker-compose.production.yml docker-compose.yml

# Variables críticas para producción
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=generate-strong-256-bit-key-here
DATABASE_URL=postgresql://user:password@host:5432/inventario_retail
REDIS_URL=redis://:password@host:6379/0

# AFIP Production settings
AFIP_ENVIRONMENT=production
AFIP_CUIT=20123456789
CUIT_EMPRESA=tu-cuit-real

# Performance settings
WORKERS_COUNT=4
MAX_CONNECTIONS=100
CACHE_TTL=3600
```

### Scripts de Build Optimizados para Deployment
```bash
#!/bin/bash
# build-production.sh
set -e

echo "🚀 Building Sistema Inventario Retail for Production..."

# Build optimized Python environment
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_final.txt --no-cache-dir

# Compile Python files
python -m compileall agente_deposito/ agente_negocio/ ml/ shared/

# Optimize ML models
python scripts/optimize_models.py

# Build static assets
echo "Optimizing static assets..."
cd web_dashboard/static
# Minify CSS/JS if needed

echo "✅ Build completed successfully"
```

### Archivos que Deben ser Excluidos (.gitignore, .dockerignore)
```gitignore
# .dockerignore adicional para producción
**/__pycache__
**/*.pyc
**/*.pyo
**/*.pyd
**/.Python
**/env
**/venv
**/ENV
**/.venv
**/env.bak
**/venv.bak

# Development files
.env.development
.env.local
**/tests/
**/test_*
**/*_test.py
**/pytest_cache/
**/.coverage
**/htmlcov/

# Documentation and examples
**/docs/
**/examples/
**/*.md
!README.md

# Logs and temporary files
**/logs/
**/tmp/
**/.tmp/
**/temp/
**/*.log

# IDE files
**/.vscode/
**/.idea/
**/*.swp
**/*.swo

# OS files
**/.DS_Store
**/Thumbs.db
```

---

## 2. ESTRATEGIA DE HOSTING PARA ARGENTINA

### Recomendación Específica: Railway
**Plataforma elegida**: Railway (railway.app)

### Justificación Técnica
```
✅ Ventajas para Argentina:
- Latencia baja desde Sudamérica (AWS us-east-1)
- Deploy automático desde GitHub
- PostgreSQL y Redis managed incluidos
- Scaling horizontal automático
- SSL certificates automáticos
- $5/mes plan starter suficiente para MVP

✅ Específico para sistemas multi-agente:
- Support para múltiples servicios en un proyecto
- Network interno entre servicios
- Environment variables por servicio
- Health checks automáticos
- Logs centralizados

✅ Para sistemas con IA/ML:
- Support para Python 3.11
- Memoria suficiente para ML models
- Storage persistente para models y cache
- Timeout configurables para APIs IA
```

### Configuración Paso a Paso para Railway

#### Paso 1: Preparar Repositorio
```bash
# Crear railway.json en raíz del proyecto
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "./scripts/start-production.sh",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30
  }
}

# Crear Procfile para definir servicios
web-agente-negocio: cd agente_negocio && uvicorn main:app --host 0.0.0.0 --port $PORT
web-agente-deposito: cd agente_deposito && uvicorn main:app --host 0.0.0.0 --port $PORT  
web-ml-service: cd ml && uvicorn main_ml_service:app --host 0.0.0.0 --port $PORT
web-dashboard: cd web_dashboard && python dashboard_api.py
```

#### Paso 2: Deploy en Railway
```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login y conectar repo
railway login
railway link

# 3. Crear servicios
railway service create agente-negocio
railway service create agente-deposito  
railway service create ml-service
railway service create dashboard

# 4. Deploy todos los servicios
railway up --service agente-negocio
railway up --service agente-deposito
railway up --service ml-service
railway up --service dashboard
```

#### Paso 3: Configurar Base de Datos
```bash
# Agregar PostgreSQL
railway add postgresql

# Agregar Redis
railway add redis

# Las variables DATABASE_URL y REDIS_URL se configuran automáticamente
```

### Costos Estimados Mensuales (USD)
```
💰 Plan Starter ($5/mes):
- 4 servicios activos
- PostgreSQL shared
- Redis shared  
- 1GB RAM por servicio
- 1GB storage
- 100GB bandwidth

💰 Upgrade a Developer ($20/mes) cuando:
- Más de 1000 usuarios activos
- >1GB storage necesario
- >100GB bandwidth/mes
- Multiple environments (staging/prod)

💰 Costos adicionales estimados:
- Domain personalizado: $0 (Railway provee subdomain gratuito)
- SSL: $0 (incluido)
- Monitoring básico: $0 (Railway dashboard incluido)
- Backup automático: $10/mes (servicio externo)

Total estimado inicial: $15-25/mes
```

### Límites del Plan Gratuito y Cuándo Upgrader
```
🔴 Límites plan gratuito:
- Solo 1 servicio activo
- 512MB RAM
- 1GB storage
- Hibernation después 30min inactividad

🟡 Señales para upgrade a Starter ($5/mes):
- Necesitas >1 servicio (multi-agente)
- >512MB RAM (modelos ML)
- Sin hibernation (sistema 24/7)

🟢 Señales para upgrade a Developer ($20/mes):
- >100 usuarios concurrentes
- >1GB storage (datos históricos)
- Multiple environments
- Custom domains
```

---

## 3. PROCESO DE DESPLIEGUE DETALLADO

### Comandos Git Exactos para Preparar el Deploy
```bash
# 1. Preparar rama de producción
git checkout main
git pull origin main
git checkout -b production-deploy-$(date +%Y%m%d-%H%M)

# 2. Configurar archivos de producción
cp .env.production.template .env.production
# Editar .env.production con valores reales

# 3. Validar configuración
python scripts/validate_config.py --env production

# 4. Ejecutar tests completos
python -m pytest tests/ -v --tb=short

# 5. Commit configuración final
git add .env.production railway.json Procfile
git commit -m "feat: production configuration for deployment"

# 6. Push a Railway
git push origin production-deploy-$(date +%Y%m%d-%H%M)
railway up --detach
```

### Configuración de Repositorio para Auto-Deploy
```yaml
# .github/workflows/railway-deploy.yml
name: Deploy to Railway
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r requirements_final.txt
      
      - name: Run tests
        run: |
          python -m pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      
      - name: Deploy to Railway
        run: |
          railway up --service agente-negocio --detach
          railway up --service agente-deposito --detach
          railway up --service ml-service --detach
          railway up --service dashboard --detach
```

### Pasos Manuales Necesarios
```bash
# 1. Configurar variables de entorno en Railway dashboard
- OPENAI_API_KEY=sk-tu-clave-openai
- TELEGRAM_BOT_TOKEN=tu-bot-token
- AFIP_CUIT=tu-cuit-empresa
- JWT_SECRET_KEY=clave-segura-256-bits

# 2. Configurar dominios personalizados (opcional)
- railway domain add inventario-retail.tu-dominio.com.ar

# 3. Configurar SSL certificates (automático en Railway)

# 4. Setup initial data
railway run python scripts/setup_initial_data.py

# 5. Verificar servicios
railway logs --service agente-negocio
railway logs --service agente-deposito
```

### Setup de Base de Datos en Producción
```bash
# 1. Ejecutar migraciones
railway run --service agente-deposito python -c "
from shared.database import engine, Base
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"

# 2. Setup data inicial
railway run --service agente-deposito python scripts/seed_initial_data.py

# 3. Verificar conectividad
railway run --service agente-deposito python -c "
from shared.database import test_connection
test_connection()
print('✅ Database connection successful')
"
```

---

## 4. VERIFICACIÓN POST-DESPLIEGUE

### URLs y Endpoints para Testear
```bash
# URLs principales (reemplazar con tus dominios reales)
AGENTE_NEGOCIO_URL=https://agente-negocio-production.up.railway.app
AGENTE_DEPOSITO_URL=https://agente-deposito-production.up.railway.app
ML_SERVICE_URL=https://ml-service-production.up.railway.app
DASHBOARD_URL=https://dashboard-production.up.railway.app

# Health checks
curl $AGENTE_NEGOCIO_URL/health
curl $AGENTE_DEPOSITO_URL/health
curl $ML_SERVICE_URL/health
curl $DASHBOARD_URL/health

# API endpoints críticos
curl $AGENTE_NEGOCIO_URL/api/v1/ocr/health
curl $AGENTE_DEPOSITO_URL/api/v1/inventory/stats
curl $ML_SERVICE_URL/api/v1/predictions/health
curl $DASHBOARD_URL/api/dashboard/status
```

### Comandos para Verificar que Todo Funciona
```bash
#!/bin/bash
# post-deploy-verification.sh

echo "🔍 Verificando deployment del Sistema Inventario Retail..."

# 1. Health checks básicos
echo "Verificando health checks..."
for service in agente-negocio agente-deposito ml-service dashboard; do
  URL="https://$service-production.up.railway.app/health"
  if curl -f -s $URL > /dev/null; then
    echo "✅ $service: HEALTHY"
  else
    echo "❌ $service: UNHEALTHY"
  fi
done

# 2. Test conectividad base de datos
echo "Verificando base de datos..."
railway run --service agente-deposito python -c "
from shared.database import engine
try:
    engine.execute('SELECT 1')
    print('✅ Database: CONNECTED')
except Exception as e:
    print(f'❌ Database: ERROR - {e}')
"

# 3. Test OCR functionality
echo "Verificando OCR de facturas..."
curl -X POST $AGENTE_NEGOCIO_URL/api/v1/ocr/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}' | grep -q "success" && echo "✅ OCR: WORKING" || echo "❌ OCR: ERROR"

# 4. Test ML service
echo "Verificando ML predictions..."
curl -X POST $ML_SERVICE_URL/api/v1/predictions/test \
  -H "Content-Type: application/json" \
  -d '{"test_data": [1,2,3]}' | grep -q "prediction" && echo "✅ ML: WORKING" || echo "❌ ML: ERROR"

echo "🎯 Verificación completada"
```

### Logs Críticos a Revisar
```bash
# Logs por servicio en Railway
railway logs --service agente-negocio --tail
railway logs --service agente-deposito --tail  
railway logs --service ml-service --tail
railway logs --service dashboard --tail

# Buscar errores específicos
railway logs --service agente-negocio | grep -i "error\|exception\|failed"

# Verificar startup logs
railway logs --service agente-negocio --since 1h | head -50

# Monitor performance logs
railway logs --service ml-service | grep -i "slow\|timeout\|memory"
```

### Tests de Funcionalidad Básicos
```python
# test_post_deployment.py
import requests
import json
import pytest

BASE_URLS = {
    'negocio': 'https://agente-negocio-production.up.railway.app',
    'deposito': 'https://agente-deposito-production.up.railway.app',
    'ml': 'https://ml-service-production.up.railway.app',
    'dashboard': 'https://dashboard-production.up.railway.app'
}

def test_health_endpoints():
    """Test all health endpoints are responding"""
    for service, url in BASE_URLS.items():
        response = requests.get(f"{url}/health")
        assert response.status_code == 200
        assert response.json().get('status') == 'healthy'

def test_authentication():
    """Test JWT authentication is working"""
    # Test login
    response = requests.post(
        f"{BASE_URLS['negocio']}/api/v1/auth/login",
        json={"username": "admin", "password": "test_password"}
    )
    assert response.status_code == 200
    assert 'access_token' in response.json()

def test_database_connectivity():
    """Test database operations are working"""
    response = requests.get(f"{BASE_URLS['deposito']}/api/v1/inventory/stats")
    assert response.status_code == 200
    assert 'total_products' in response.json()

def test_ml_predictions():
    """Test ML service is generating predictions"""
    test_data = {"products": [{"id": 1, "sales": [10, 15, 12]}]}
    response = requests.post(
        f"{BASE_URLS['ml']}/api/v1/predictions/demand",
        json=test_data
    )
    assert response.status_code == 200
    assert 'predictions' in response.json()

# Ejecutar: python -m pytest test_post_deployment.py -v
```

---

## 5. ROLLBACK Y RECOVERY

### Cómo Hacer Rollback Si Algo Falla
```bash
#!/bin/bash
# rollback-production.sh

echo "🚨 Iniciando rollback del Sistema Inventario Retail..."

# 1. Identificar último deploy exitoso
LAST_GOOD_COMMIT=$(git log --oneline --grep="production deploy" -n 2 | tail -1 | cut -d' ' -f1)
echo "Rollback to commit: $LAST_GOOD_COMMIT"

# 2. Rollback en Railway
railway rollback --service agente-negocio
railway rollback --service agente-deposito  
railway rollback --service ml-service
railway rollback --service dashboard

# 3. Verificar rollback exitoso
sleep 30
./scripts/post-deploy-verification.sh

# 4. Restaurar configuración anterior si es necesario
if [ -f ".env.production.backup" ]; then
    cp .env.production.backup .env.production
    echo "✅ Configuration restored from backup"
fi

# 5. Notificar equipo
echo "📢 Rollback completed. System restored to previous stable state."
```

### Backup de Configuraciones
```bash
#!/bin/bash
# backup-configs.sh

BACKUP_DIR="backups/$(date +%Y%m%d-%H%M)"
mkdir -p $BACKUP_DIR

echo "📦 Creating configuration backup..."

# Backup environment files
cp .env.production $BACKUP_DIR/
cp railway.json $BACKUP_DIR/
cp Procfile $BACKUP_DIR/

# Backup database schema
railway run --service agente-deposito pg_dump $DATABASE_URL > $BACKUP_DIR/schema_backup.sql

# Backup critical data
railway run --service agente-deposito python scripts/export_critical_data.py > $BACKUP_DIR/critical_data.json

# Create restore script
cat > $BACKUP_DIR/restore.sh << 'EOF'
#!/bin/bash
echo "Restoring from backup..."
cp .env.production ../
cp railway.json ../
cp Procfile ../
echo "Configuration restored. Manual database restore may be needed."
EOF

chmod +x $BACKUP_DIR/restore.sh
echo "✅ Backup created in $BACKUP_DIR"
```

### Recovery Plan Básico
```bash
# recovery-plan.md

## Escenarios de Recovery

### 1. Servicio Individual Caído
- Verificar logs: railway logs --service [service-name] --tail
- Restart servicio: railway restart --service [service-name]  
- Si persiste: railway rollback --service [service-name]

### 2. Base de Datos Corrupta
- Parar todos los servicios
- Restaurar desde backup más reciente
- Ejecutar migraciones si es necesario
- Restart todos los servicios

### 3. Deploy Completo Fallido
- Ejecutar rollback-production.sh
- Verificar con post-deploy-verification.sh
- Investigar logs para identificar causa
- Fix issues y re-deploy

### 4. Pérdida de Configuración
- Restaurar desde backups/latest/
- Reconfigurar variables de entorno en Railway
- Re-deploy si es necesario

## Contactos de Emergencia
- DevOps Lead: +54-xxx-xxx-xxxx
- Database Admin: +54-xxx-xxx-xxxx  
- Sistema crítico: disponible 24/7

## SLA Recovery Times
- Servicio individual: < 15 minutos
- Deploy rollback: < 30 minutos
- Database restore: < 2 horas
- Sistema completo: < 4 horas
```

---

Este plan de despliegue personalizado proporciona una guía completa y específica para deployar el Sistema Inventario Retail Multi-Agente en producción con Railway, optimizado para el contexto argentino y las necesidades específicas del sistema.