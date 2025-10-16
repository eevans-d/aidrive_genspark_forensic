# 🚀 Sistema Inventario Multi-Agente - Guía de Deployment

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes (ETAPA 3 - Actualizado)

```
┌─────────────────────────────────────────────────────────────────┐
│                          Users/Clients                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                        ┌──────▼──────┐
                        │   NGINX     │ Port 80/443
                        │  TLS Ready  │
                        └──────┬──────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
    ┌───▼───┐            ┌────▼────┐           ┌────▼────┐
    │Agente │   Port 8001│Dashboard │ Port 8080│ Metrics │
    │Depósito            │          │          │Prometheus
    └───┬───┘            └────┬────┘          └────┬────┘
        │                     │                     │
    JWT │                 API Key                   │
    Auth│              Authorization           X-API-Key
        │                     │                     │
        └──────────┬──────────┴──────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
  ┌───▼────────────┐     ┌──────▼────┐
  │  PostgreSQL    │     │   Redis   │
  │  Cifrado en    │     │   Cache   │
  │  Reposo (AES)  │     │           │
  │  + Auditoría   │     └───────────┘
  └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Observability Stack                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Prometheus (9090)  ──TLS──▶ Alertmanager (9093)                │
│     │                          │                                 │
│     │                      Slack/Email                           │
│  Scrape Metrics              Alerts                              │
│     │                                                             │
│  ◀──┴──────────────▶ Grafana (3000)                             │
│     │                                                             │
│     └──────▶ Loki (3100) ──▶ Logs                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Security Layer                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TLS Certificates    PostgreSQL Encryption    API Keys          │
│  (Mutual Auth)       (AES-256-CBC)            (Dashboard)       │
│                      pgcrypto + Audit         X-API-Key Header  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Seguro

```
1. CLIENTE REQUEST (HTTPS - TLS 1.2+)
   Client ─TLS─▶ Nginx ─JWT─▶ Dashboard ─API Key─▶ Backend

2. BACKEND COMMUNICATION (MUTUAL TLS)
   Prometheus ─mTLS─▶ Alertmanager
   (certificado cliente + servidor validados)

3. BASE DE DATOS (CIFRADO EN REPOSO)
   Dashboard/Agentes ─SQL─▶ PostgreSQL
   Datos sensibles: decrypt_data() con clave maestra
   Acceso registrado: encrypted_data_access_log

4. OBSERVABILIDAD (SECURE SCRAPING)
   Prometheus ─API Key─▶ Dashboard /metrics
   Grafana ─datasource─▶ Prometheus (http://prometheus:9090)
   Logs: Promtail ─push─▶ Loki ─query─▶ Grafana
```

---

## 📋 Componentes del Sistema

### Servicios Principales
- **AgenteDepósito** (Puerto 8001) - Gestión ACID de stock y productos
- **AgenteNegocio** (Puerto 8002) - OCR, pricing y reglas de negocio  
- **ML Service** (Puerto 8003) - Predicciones y machine learning
- **Dashboard Web** (Puerto 8080) - Interfaz de usuario principal
- **Nginx** (Puerto 80/443) - Reverse proxy y load balancer

### Infraestructura
- **PostgreSQL** (Puerto 5432) - Base de datos principal
- **Redis** (Puerto 6379) - Cache y sessions

---

## 🛠️ Instalación y Deployment

### Prerrequisitos
```bash
# Docker & Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker-compose --version
```

### Deployment Rápido

1. **Clonar y configurar**:
```bash
git clone <repo-url>
cd inventario-retail

# Configurar environment
cp .env.production.template .env.production
nano .env.production  # Editar valores reales
```

2. **Desplegar sistema completo**:
```bash
./scripts/deploy.sh --up
```

3. **Verificar estado**:
```bash
./scripts/deploy.sh --status
```

### URLs del Sistema
- Dashboard Principal: http://localhost
- API Depósito: http://localhost/api/deposito/
- API Negocio: http://localhost/api/negocio/  
- API ML: http://localhost/api/ml/

---

## 🔧 Gestión del Sistema

### Comandos Principales
```bash
# Verificar prerrequisitos
./scripts/deploy.sh --check

# Construir imágenes
./scripts/deploy.sh --build

# Levantar servicios
./scripts/deploy.sh --up

# Ver logs en tiempo real
./scripts/deploy.sh --logs

# Ver estado de servicios
./scripts/deploy.sh --status

# Reiniciar servicios
./scripts/deploy.sh --restart

# Detener servicios
./scripts/deploy.sh --down

# Backup de base de datos
./scripts/deploy.sh --backup

# Restaurar backup
./scripts/deploy.sh --restore backup_file.sql
```

### Monitoreo
```bash
# Ver logs específicos
docker-compose -f docker-compose.production.yml logs -f agente-deposito
docker-compose -f docker-compose.production.yml logs -f dashboard

# Acceder a contenedores
docker exec -it agente_deposito bash
docker exec -it inventario_retail_db psql -U postgres inventario_retail

# Ver métricas de recursos
docker stats
```

---

## ⚙️ Configuración de Producción

### Variables de Entorno Críticas
```bash
# Seguridad
JWT_SECRET_KEY=<256-bit-random-key>
POSTGRES_PASSWORD=<secure-password>
DASHBOARD_API_KEY=<api-key>

# CORS (restrictivo en producción)
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Base de datos
DATABASE_URL=postgresql://user:pass@postgres:5432/inventario_retail
```

### SSL/HTTPS (Producción)
```bash
# Obtener certificados SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# El nginx.conf ya incluye configuración HTTPS
```

---

## 🛡️ Seguridad

### Autenticación JWT
- Todos los endpoints API están protegidos con JWT
- Roles: `admin`, `deposito`, `negocio`, `ml_service`
- Tokens expiran en 8 horas (configurable)

### API Keys
- Dashboard API protegido con `DASHBOARD_API_KEY`
- Header requerido: `X-API-Key: <your-key>`

### CORS
- Configurado restrictivamente en producción
- Solo orígenes autorizados en `CORS_ORIGINS`

---

## 📊 Monitoreo y Observabilidad

### Health Checks
```bash
# Verificar salud de todos los servicios
curl http://localhost/health
curl http://localhost:8001/health  # Agente Depósito
curl http://localhost:8002/health  # Agente Negocio
curl http://localhost:8003/health  # ML Service
curl http://localhost:8080/health  # Dashboard
```

### Logs
- Logs centralizados en `./logs/`
- Rotación automática diaria
- Formato JSON para parsing automático

### Métricas
- Métricas Prometheus en endpoints `/metrics`
- Grafana dashboard configurado (opcional)

---

## � Observability Stack (ETAPA 3)

### Componentes del Stack

El sistema incluye un stack completo de observabilidad con:

- **Prometheus** (Puerto 9090) - Recolección y almacenamiento de métricas
- **Grafana** (Puerto 3000) - Visualización de métricas y logs
- **Loki** (Puerto 3100) - Agregación de logs
- **Promtail** (Puerto 9080) - Recolector de logs Docker
- **Alertmanager** (Puerto 9093) - Gestión de alertas
- **Node Exporter** (Puerto 9100) - Métricas del sistema host
- **Postgres Exporter** (Puerto 9187) - Métricas de PostgreSQL
- **Redis Exporter** (Puerto 9121) - Métricas de Redis

### Deployment del Stack de Observability

**1. Verificar que servicios principales están corriendo:**
```bash
# Los servicios principales deben estar UP antes de desplegar observability
docker-compose -f docker-compose.production.yml ps
```

**2. Desplegar stack de observability:**
```bash
cd inventario-retail/observability

# Levantar todos los componentes
docker-compose -f docker-compose.observability.yml up -d

# Verificar que todos están UP
docker-compose -f docker-compose.observability.yml ps
```

**3. Verificar conectividad:**
```bash
# Verificar que Prometheus puede alcanzar targets
curl http://localhost:9090/-/healthy
# Esperado: "Prometheus is Healthy."

# Verificar Grafana está UP
curl http://localhost:3000/api/health
# Esperado: {"database":"ok"}

# Verificar Loki está listo
curl http://localhost:3100/ready
# Esperado: "ready"
```

### Acceso a Interfaces Web

**Grafana (Principal):**
- URL: http://localhost:3000
- Usuario: `admin`
- Password: `admin` (cambiar en primer acceso)
- Datasources: Pre-configuradas automáticamente (Prometheus, Loki)

**Prometheus UI:**
- URL: http://localhost:9090
- Verificar targets: http://localhost:9090/targets
- Verificar alertas: http://localhost:9090/alerts

**Alertmanager:**
- URL: http://localhost:9093
- Ver alertas activas: http://localhost:9093/#/alerts

### Dashboards de Grafana

El sistema incluye 4 dashboards pre-configurados:

**1. System Overview** (`minimarket-system-overview`)
- Salud de los 4 servicios (UP/DOWN)
- Request rate por servicio
- Error rate % con thresholds
- P95 latency en milisegundos
- Uptime % de última semana

**2. Business KPIs** (`minimarket-business-kpis`)
- Productos depositados por hora
- Alertas de stock crítico
- Órdenes de compra generadas
- Inflación calculada vs baseline
- Revenue proyectado vs real
- Distribución de productos por categoría
- Trending de órdenes (hourly)

**3. Performance** (`minimarket-performance`)
- CPU usage % por contenedor
- Memory usage % por contenedor
- Disk I/O (read/write) en Bps
- Network I/O (RX/TX) en Bps
- PostgreSQL connections activas vs max
- Redis cache hit rate %
- Redis clients y keys activos

**4. ML Service Monitor** (`minimarket-ml-service`)
- OCR processing time (P50/P95/P99)
- OCR timeout events por hora
- Price prediction accuracy %
- ML model drift score
- CPU/Memory del servicio ML
- Predictions & cache performance
- Distribución de modelos en uso
- ML/OCR errors por minuto

**Acceso a dashboards:**
```bash
# Abrir Grafana: http://localhost:3000
# Login: admin/admin
# Navegar a: Dashboards > Browse
# Folder: "MiniMarket"
# Seleccionar dashboard deseado
```

### Configuración de Alertmanager y Slack

**1. Configurar webhook de Slack:**
```bash
# Editar observability/alertmanager/alertmanager.yml
nano inventario-retail/observability/alertmanager/alertmanager.yml

# Reemplazar placeholder con webhook real:
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#minimarket-alerts'
        username: 'Prometheus AlertManager'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**2. Aplicar cambios:**
```bash
# Reiniciar Alertmanager
docker-compose -f docker-compose.observability.yml restart alertmanager

# Verificar configuración
curl http://localhost:9093/api/v2/status
```

**3. Probar alertas manualmente:**
```bash
# Enviar alerta de prueba
curl -XPOST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert from Mini Market",
      "description": "This is a test alert to verify Slack integration"
    }
  }
]'

# Verificar que llegó a Slack en #minimarket-alerts
```

### Alertas Configuradas

El sistema incluye 15 alertas pre-configuradas:

**CRITICAL (5 alertas):**
- `ServiceDown` - Servicio no responde >2 minutos
- `HighErrorRate` - Tasa de errores >5% durante 5 minutos
- `DatabaseDown` - PostgreSQL no responde >1 minuto
- `DiskSpaceCritical` - Espacio en disco <10% durante 5 minutos
- `RedisDown` - Redis no responde >2 minutos

**HIGH (5 alertas):**
- `HighLatency` - P95 latency >300ms durante 10 minutos
- `MemoryPressure` - Uso de memoria >80% durante 10 minutos
- `CPUHigh` - CPU >70% durante 15 minutos
- `StockCritico` - >50 productos en stock crítico durante 15 minutos
- `OCRTimeoutSpike` - >10 timeouts de OCR por hora durante 10 minutos
- `CacheHitRateLow` - Redis cache hit rate <70% durante 15 minutos

**MEDIUM (5 alertas):**
- `SlowRequests` - P50 latency >200ms durante 20 minutos
- `InflacionAnomaly` - Inflación difiere >5% del baseline durante 30 minutos
- `MLModelDrift` - Model drift score >0.15 durante 1 hora
- `LogVolumeSpike` - Volumen de logs aumenta >200% durante 15 minutos
- `DeploymentIssue` - Servicio reiniciado >3 veces en 10 minutos

**Ver alertas activas:**
```bash
# En Prometheus UI
http://localhost:9090/alerts

# O vía API
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alert: .labels.alertname, state: .state}'
```

### Testing del Stack de Observability

**1. Verificar Prometheus targets:**
```bash
# Abrir http://localhost:9090/targets
# Todos deben estar en estado "UP" (verde)

# Targets esperados:
# - agente_deposito (8001)
# - agente_negocio (8002)
# - ml_service (8003)
# - dashboard (8080)
# - node_exporter (9100)
# - postgres_exporter (9187)
# - redis_exporter (9121)
# - prometheus (9090)
```

**2. Verificar métricas en Prometheus:**
```bash
# Queries de ejemplo en http://localhost:9090/graph

# Ver servicios UP
up{job=~"agente_.*|ml_service|dashboard"}

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_errors_total[5m])

# CPU usage
rate(container_cpu_usage_seconds_total[5m])
```

**3. Verificar dashboards en Grafana:**
```bash
# Abrir http://localhost:3000
# Login: admin/admin
# Ir a Dashboards > Browse > MiniMarket folder
# Abrir "System Overview"
# Debe mostrar datos en todos los panels (si servicios están corriendo)
```

**4. Verificar logs en Loki:**
```bash
# En Grafana, ir a Explore (ícono de brújula)
# Seleccionar datasource "Loki"
# Query de ejemplo: {job="agente_deposito"}
# Debe mostrar logs recientes del servicio
```

**5. Smoke test completo:**
```bash
# Script automatizado para verificar todo el stack
cd inventario-retail/observability

# Ejecutar smoke test
bash ../scripts/check_metrics_dashboard.sh http://localhost:9090 http://localhost:3000

# Esperado: todos los checks en verde
```

### Monitoreo de Métricas Clave

**KPIs del Sistema (Targets ETAPA 3):**
- ✅ **Uptime:** >99.9%
- ✅ **P95 Latency:** <300ms
- ✅ **Error Rate:** <0.5%
- ✅ **Cache Hit Rate:** >70%
- ✅ **OCR Timeout Rate:** <10/hora
- ✅ **ML Prediction Accuracy:** >90%

**Verificar KPIs actuales:**
```bash
# Request en Prometheus o ver en Dashboard "System Overview"

# Uptime últimos 7 días
100 * (1 - (rate(up[7d] == 0) / rate(up[7d])))

# P95 Latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000

# Error Rate
100 * (rate(http_errors_total[5m]) / rate(http_requests_total[5m]))

# Cache Hit Rate
100 * (rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])))
```

### Runbooks de Operaciones

Consultar runbooks detallados para troubleshooting:

**1. Respuesta a Alertas:**
```bash
# Ver procedimientos para cada alerta
cat inventario-retail/observability/runbooks/RESPONDING_TO_ALERTS.md

# Incluye diagnóstico y resolución paso a paso para:
# - ServiceDown, HighErrorRate, DatabaseDown
# - HighLatency, MemoryPressure, CPUHigh
# - StockCritico, OCRTimeoutSpike, MLModelDrift
# - Y todas las demás alertas configuradas
```

**2. Troubleshooting de Dashboards:**
```bash
# Ver guía de problemas comunes
cat inventario-retail/observability/runbooks/DASHBOARD_TROUBLESHOOTING.md

# Incluye soluciones para:
# - Dashboard no muestra datos
# - Queries muy lentas
# - Grafana no carga
# - Datasource no conecta
# - Métricas desactualizadas
```

### Mantenimiento del Stack

**Limpieza de datos antiguos:**
```bash
# Prometheus retention configurado: 30 días
# Loki retention configurado: 30 días
# Ambos limpian automáticamente datos antiguos

# Ver tamaño actual de datos
docker exec prometheus du -sh /prometheus
docker exec loki du -sh /loki

# Si es necesario, ajustar retention en configs:
# - observability/prometheus/prometheus.yml (--storage.tsdb.retention.time)
# - observability/loki/loki-config.yml (retention_period: 720h)
```

**Backup de configuraciones:**
```bash
# Backup de dashboards de Grafana
docker exec grafana tar czf /tmp/grafana-dashboards.tar.gz /etc/grafana/provisioning
docker cp grafana:/tmp/grafana-dashboards.tar.gz ./backups/

# Backup de configuraciones de Prometheus
docker exec prometheus tar czf /tmp/prometheus-config.tar.gz /etc/prometheus
docker cp prometheus:/tmp/prometheus-config.tar.gz ./backups/

# Los configs también están en Git en inventario-retail/observability/
```

**Actualización del stack:**
```bash
# Actualizar a versiones más recientes
cd inventario-retail/observability

# Editar docker-compose.observability.yml con nuevas versiones
# Ejemplo: prom/prometheus:v2.45.0 -> prom/prometheus:v2.47.0

# Pull de nuevas imágenes
docker-compose -f docker-compose.observability.yml pull

# Aplicar actualizaciones (con mínimo downtime)
docker-compose -f docker-compose.observability.yml up -d

# Verificar que todo funciona
docker-compose -f docker-compose.observability.yml ps
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### Detener Stack de Observability

```bash
cd inventario-retail/observability

# Detener todos los componentes (mantiene volúmenes con datos)
docker-compose -f docker-compose.observability.yml down

# Detener y eliminar volúmenes (CUIDADO: borra todos los datos históricos)
docker-compose -f docker-compose.observability.yml down -v
```

### Troubleshooting Común

**Prometheus no scrape targets:**
```bash
# Verificar que servicios están en la misma red Docker
docker network inspect inventario-retail_default | grep -E "(prometheus|agente)"

# Si no, agregar prometheus a la red correcta
docker network connect inventario-retail_default prometheus

# Reiniciar Prometheus
docker-compose -f docker-compose.observability.yml restart prometheus
```

**Grafana muestra "No data":**
```bash
# Verificar datasource Prometheus
# En Grafana: Configuration > Data Sources > Prometheus
# URL debe ser: http://prometheus:9090 (nombre del contenedor, no localhost)
# Click en "Save & Test" - debe mostrar "Data source is working"

# Si falla, verificar que Grafana y Prometheus están en la misma red
docker network connect inventario-retail_default grafana
docker-compose -f docker-compose.observability.yml restart grafana
```

**Alertas no llegan a Slack:**
```bash
# Verificar webhook URL en alertmanager.yml
docker exec alertmanager cat /etc/alertmanager/alertmanager.yml | grep api_url

# Verificar logs de Alertmanager
docker logs alertmanager | grep -i "slack\|error"

# Test manual de notificación (ver sección "Configuración de Alertmanager")
```

**Para más detalles, consultar:**
- `observability/runbooks/RESPONDING_TO_ALERTS.md`
- `observability/runbooks/DASHBOARD_TROUBLESHOOTING.md`

---

## 🔒 Seguridad - TLS y Comunicaciones Seguras

### Configuración de TLS para Prometheus y Alertmanager

A partir de ETAPA 3, se implementó comunicación segura entre Prometheus y Alertmanager usando TLS con autenticación mutua.

**Certificados:**
```bash
# Los certificados se encuentran en:
inventario-retail/observability/prometheus/tls/
├── ca.crt                    # Certificate Authority
├── ca.key                    # Private key del CA
├── prometheus.crt            # Certificado de cliente (Prometheus)
├── prometheus.key            # Private key de Prometheus
├── alertmanager.crt          # Certificado de servidor (Alertmanager)
└── alertmanager.key          # Private key de Alertmanager

# Validez: 365 días desde la generación
# Generados con: OpenSSL 3.0+ | RSA 4096-bit | TLS 1.2+
```

**Generación de nuevos certificados:**
```bash
# Regenerar certificados (útil para renovación antes de expirar)
cd inventario-retail/observability/prometheus/tls

# Hacer backup de certificados actuales
mv ca.crt ca.crt.bak
mv ca.key ca.key.bak
mv prometheus.* prometheus.bak/
mv alertmanager.* alertmanager.bak/

# Ejecutar script de generación
./generate_certs.sh

# Verificar nuevos certificados
openssl x509 -in prometheus.crt -text -noout | grep "Not Before\|Not After"
```

**Verificación de conectividad TLS:**
```bash
# Verificar que Prometheus puede conectar a Alertmanager con TLS
docker exec prometheus curl --cacert /etc/prometheus/tls/ca.crt \
  --cert /etc/prometheus/tls/prometheus.crt \
  --key /etc/prometheus/tls/prometheus.key \
  https://alertmanager:9093/api/v2/status

# Esperado: JSON con status de Alertmanager
```

**Documentación completa:**
```bash
# Ver guía detallada de TLS setup
cat security/TLS_SETUP.md

# Incluye:
# - Arquitectura de seguridad
# - Procedimientos de renovación
# - Troubleshooting de certificados
# - Mejores prácticas
```

---

## 🔐 Encriptación de Datos - Datos en Reposo

### Cifrado de Datos Sensibles en PostgreSQL

A partir de ETAPA 3, se implementó cifrado AES-256-CBC para datos sensibles usando la extensión pgcrypto de PostgreSQL.

**Datos cifrados:**
```sql
-- Tabla: system_config
- api_key_encrypted
- jwt_secret_encrypted
- slack_webhook_encrypted

-- Tabla: productos
- costo_adquisicion_encrypted
- precio_sugerido_encrypted
```

**Aplicar migración de cifrado:**
```bash
# La migración 004_add_encryption.sql debe ser aplicada una sola vez
# Verificar si ya fue aplicada:

docker exec inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='pgcrypto')"
# Resultado: t (true) = ya aplicada | f (false) = no aplicada

# Si no está aplicada:
docker exec inventario_retail_db psql -U postgres inventario_retail \
  -f /docker-entrypoint-initdb.d/004_add_encryption.sql

# Verificar funciones de cifrado
docker exec inventario_retail_db psql -U postgres inventario_retail -c \
  "\df encrypt_data"
```

**Configuración de la clave maestra:**
```bash
# En .env.production, establecer clave de 32 bytes (64 caracteres hex)
DATABASE_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# IMPORTANTE:
# - Usar clave fuerte y aleatoria
# - NO compartir esta clave en repositorio
# - Guardar copia segura en bóveda de secretos
# - Rotar cada 90 días (ver procedimiento abajo)
```

**Uso de funciones de cifrado:**
```sql
-- Cifrar datos
UPDATE system_config SET 
  api_key_encrypted = encrypt_data(api_key, current_setting('DATABASE_ENCRYPTION_KEY'))
WHERE id = 1;

-- Descifrar datos
SELECT decrypt_data(api_key_encrypted, current_setting('DATABASE_ENCRYPTION_KEY'))
FROM system_config WHERE id = 1;

-- Auditoría de acceso
SELECT * FROM encrypted_data_access_log 
ORDER BY accessed_at DESC 
LIMIT 10;
```

**Rotación de claves de cifrado (Procedimiento):**
```bash
# 1. Generar nueva clave maestra
NEW_KEY=<generar-nueva-clave-32-bytes>

# 2. En production, ejecutar:
docker exec inventario_retail_db psql -U postgres inventario_retail << EOF
BEGIN;

-- Re-cifrar todos los datos con nueva clave
UPDATE system_config SET
  api_key_encrypted = encrypt_data(
    decrypt_data(api_key_encrypted, current_setting('old_key')), 
    '$NEW_KEY'
  );

COMMIT;
EOF

# 3. Actualizar DATABASE_ENCRYPTION_KEY en .env.production
# 4. Reiniciar servicios que usan la BD
```

**Verificación de integridad:**
```bash
# Verificar que todos los datos se pueden descifrar
docker exec inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT COUNT(*) FROM system_config WHERE decrypt_data(api_key_encrypted, current_setting('DATABASE_ENCRYPTION_KEY')) IS NULL"
# Esperado: 0 (ninguno nulo)
```

**Rollback (en caso de necesidad):**
```bash
# Si necesitas revertir la migración de cifrado:
docker exec inventario_retail_db psql -U postgres inventario_retail \
  -f /docker-entrypoint-initdb.d/004_add_encryption_rollback.sql

# ADVERTENCIA: esto elimina las columnas cifradas y las funciones
# Ejecutar solo si es absolutamente necesario
```

**Documentación completa:**
```bash
# Ver guía detallada de encriptación
cat security/DATA_ENCRYPTION.md

# Incluye:
# - Estrategia de encriptación
# - Ejemplos de uso (SQL y Python)
# - Análisis de performance
# - Gestión de claves
# - Compliance y auditoría
```

---

## 📊 Performance - Load Testing

### Suite de Load Testing con k6

A partir de ETAPA 3, se implementó suite completa de load testing automatizado con k6 para validar performance de todos los endpoints críticos.

**Ubicación de scripts:**
```bash
inventario-retail/scripts/load_testing/
├── test-health.js           # Baseline: health check (P95<100ms)
├── test-inventory-read.js   # Lectura: GET operations (P95<300ms)
├── test-inventory-write.js  # Escritura: POST operations (P95<500ms)
├── test-metrics.js          # Métricas: Prometheus scraping (P95<200ms)
├── run-all.sh               # Orquestador de suite completa
└── results/                 # Directorio de resultados
```

**Requisitos previos:**
```bash
# Instalar k6
sudo apt install k6

# Verificar instalación
k6 version
```

**Ejecutar tests individuales:**
```bash
cd inventario-retail/scripts/load_testing

# Test de health check
k6 run test-health.js

# Test de lectura (requiere API key)
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=your-api-key \
       test-inventory-read.js

# Test de escritura (CUIDADO: crea datos de prueba)
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=your-api-key \
       test-inventory-write.js

# Test de métricas
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=your-api-key \
       test-metrics.js
```

**Ejecutar suite completa:**
```bash
cd inventario-retail/scripts/load_testing

# Ejecución básica (omite write tests por defecto)
./run-all.sh

# Con parámetros personalizados
BASE_URL=https://staging.yourdomain.com \
API_KEY=staging-key \
SKIP_WRITE_TESTS=true \
./run-all.sh

# Continuar aunque fallen algunos tests
CONTINUE_ON_FAILURE=true ./run-all.sh
```

**Umbrales de Performance (SLOs):**

| Endpoint | Métrica | Target | Crítico |
|----------|---------|--------|---------|
| `/health` | P95 Latency | <100ms | <200ms |
| `/health` | Error Rate | <0.1% | <1% |
| `/api/inventory` | P95 Latency | <300ms | <500ms |
| `/api/inventory` | Error Rate | <0.5% | <2% |
| `/metrics` | P95 Latency | <200ms | <400ms |
| `/metrics` | Error Rate | <0.1% | <1% |

**Análisis de resultados:**
```bash
# Ver resultados más recientes
cat results/consolidated-report-*.txt

# Análisis JSON
cat results/health-check-summary.json | jq '.metrics.http_req_duration'

# Latencia por percentil
cat results/health-check-summary.json | jq '.metrics.http_req_duration.values | {min, med, "p(95)", "p(99)", max}'
```

**Pre-deployment gate:**
```bash
# Ejecutar como verificación antes de deploy
SKIP_WRITE_TESTS=true ./run-all.sh

# Si algún threshold falla, abortar deployment
if [ $? -ne 0 ]; then
  echo "❌ Performance baseline no cumplido. Abortando deployment."
  exit 1
fi
```

**Documentación completa:**
```bash
# Ver guía detallada de load testing
cat scripts/load_testing/LOAD_TESTING.md

# Incluye:
# - Instalación de k6
# - Descripción de cada test
# - Integración CI/CD
# - Troubleshooting
# - Mejores prácticas
```

---

## 🔄 Backup y Restore

### Backup Automático
```bash
# Backup manual
./scripts/deploy.sh --backup

# Programar backup diario (cron)
0 2 * * * /path/to/inventario-retail/scripts/deploy.sh --backup
```

### Restore
```bash
# Restaurar desde backup
./scripts/deploy.sh --restore backups/backup_20250101_020000.sql
```

---

## 🚨 Troubleshooting

### Problemas Comunes

**Servicios no inician**:
```bash
# Ver logs de error
docker-compose -f docker-compose.production.yml logs

# Verificar puertos ocupados
sudo netstat -tulpn | grep :8001
```

**Base de datos no conecta**:
```bash
# Verificar PostgreSQL
docker exec -it inventario_retail_db pg_isready -U postgres

# Ver logs de DB
docker logs inventario_retail_db
```

**JWT tokens inválidos**:
```bash
# Verificar JWT_SECRET_KEY en .env.production
# Regenerar tokens con nuevo secret
```

### Problemas de TLS/Certificados

**Certificados expirados:**
```bash
# Verificar validez de certificados
openssl x509 -in observability/prometheus/tls/prometheus.crt -text -noout | grep "Not After"

# Si están a punto de expirar (< 30 días):
cd observability/prometheus/tls
./generate_certs.sh  # Generar nuevos certificados

# Reiniciar servicios
docker-compose -f ../docker-compose.observability.yml restart prometheus alertmanager
```

**Error de certificado en Prometheus:**
```bash
# Verificar que Prometheus puede conectar a Alertmanager con TLS
docker exec prometheus curl --cacert /etc/prometheus/tls/ca.crt \
  --cert /etc/prometheus/tls/prometheus.crt \
  --key /etc/prometheus/tls/prometheus.key \
  https://alertmanager:9093/api/v2/status

# Si falla verificar:
# 1. Archivos de certificados están en lugar correcto
# 2. Permisos de archivos (.key en 600)
# 3. Nombres de hosts en configuración coinciden con CN en certificados

docker exec prometheus ls -la /etc/prometheus/tls/
```

**Error: "certificate verify failed":**
```bash
# Verificar que CA.crt es válido y accesible
docker exec prometheus openssl verify -CAfile /etc/prometheus/tls/ca.crt \
  /etc/prometheus/tls/prometheus.crt

# Esperado: "OK"
# Si falla, regenerar certificados:
cd observability/prometheus/tls && ./generate_certs.sh
```

### Problemas de Encriptación

**Error: "column does not exist api_key_encrypted":**
```bash
# La migración de cifrado no ha sido aplicada
# Verificar si existe la extensión pgcrypto:
docker exec inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='pgcrypto')"

# Si false (f), aplicar migración:
docker exec inventario_retail_db psql -U postgres inventario_retail \
  -f /docker-entrypoint-initdb.d/004_add_encryption.sql

# Reiniciar servicios que usan BD
docker-compose -f docker-compose.production.yml restart agente-deposito agente-negocio
```

**Error: "Failed to decrypt data":**
```bash
# La clave DATABASE_ENCRYPTION_KEY en .env es incorrecta
# Causas:
# 1. Clave no seteada (verificar: echo $DATABASE_ENCRYPTION_KEY)
# 2. Clave con formato incorrecto (debe ser 64 caracteres hex)
# 3. Clave cambió después de cifrar datos (imposible recuperar)

# Verificar que está bien seteada:
docker exec -e DATABASE_ENCRYPTION_KEY=$DATABASE_ENCRYPTION_KEY \
  inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT decrypt_data(api_key_encrypted, current_setting('DATABASE_ENCRYPTION_KEY')) FROM system_config LIMIT 1"

# Si devuelve NULL, la clave es incorrecta
```

**Overhead de performance por cifrado:**
```bash
# Encriptación tiene overhead ~60-66%
# Si performance degrada mucho:

# Opción 1: Reducir datos cifrados (cifrar solo lo crítico)
# Opción 2: Agregar índices en columnas buscadas
# Opción 3: Cache más agresivo en Redis

# Ver análisis detallado:
cat security/DATA_ENCRYPTION.md
```

### Problemas de Load Testing

**Error: "k6 no encontrado":**
```bash
# Instalar k6
sudo apt update && sudo apt install k6

# Verificar
k6 version
```

**Error: "Connection refused":**
```bash
# Servicio no está respondiendo
# Verificar que está up:
curl http://localhost:8080/health

# Si no responde:
docker-compose -f docker-compose.production.yml ps

# Reiniciar si es necesario:
docker-compose -f docker-compose.production.yml restart dashboard
```

**Error: "401 Unauthorized" en tests:**
```bash
# API key inválida o no seteada
# Verificar que se pasa correctamente:
k6 run -e API_KEY=your-api-key-here test-health.js

# Verificar que API key es correcta:
grep DASHBOARD_API_KEY .env.production
echo $DASHBOARD_API_KEY
```

**Tests fallan por umbrales de performance:**
```bash
# Los SLOs no se cumplen (ej: P95 > 300ms)

# Causas comunes:
# 1. Base de datos lenta: revisar queries, agregar índices
# 2. CPU/memoria limitada: escalar recursos
# 3. Network latency: usar misma región/AZ
# 4. Logging excesivo: reducir nivel de log

# Soluciones:
# - Analizar resultados JSON:
cat results/health-check-summary.json | jq '.metrics.http_req_duration'

# - Reducir carga del test temporalmente:
k6 run --vus 25 --duration 2m test-health.js

# - Revisar logs mientras corre test:
docker-compose -f docker-compose.production.yml logs -f dashboard &
k6 run test-health.js
```

**Datos de prueba acumulándose:**
```bash
# El test test-inventory-write.js crea productos ficticios
# Limpiar después de tests:
docker exec -it inventario_retail_db psql -U postgres inventario_retail << EOF
DELETE FROM productos WHERE sku LIKE 'TEST-SKU-%';
COMMIT;
EOF
```

### Logs de Debug
```bash
# Habilitar debug logs
echo "LOG_LEVEL=DEBUG" >> .env.production
./scripts/deploy.sh --restart
```

---

## 📈 Escalado

### Horizontal Scaling
```bash
# Escalar servicios específicos
docker-compose -f docker-compose.production.yml up -d --scale agente-deposito=3
docker-compose -f docker-compose.production.yml up -d --scale agente-negocio=2
```

### Load Balancer
- Nginx configurado untuk load balancing automático
- Health checks y failover incluidos

---

## 🆙 Actualizaciones

### Rolling Updates
```bash
# Actualizar imagen específica
docker-compose -f docker-compose.production.yml pull agente-deposito
docker-compose -f docker-compose.production.yml up -d --no-deps agente-deposito

# Actualización completa
git pull
./scripts/deploy.sh --build
./scripts/deploy.sh --restart
```

---

## 📞 Contacto y Soporte

- **Documentación técnica**: Ver archivos en `/docs/`
- **APIs**: Swagger UI disponible en `/docs` de cada servicio
- **Logs**: Revisar `./logs/` para troubleshooting

**Estado del sistema**: ✅ Listo para producción