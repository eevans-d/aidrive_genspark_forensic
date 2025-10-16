# Load Testing - Dashboard Mini Market

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Herramientas](#herramientas)
3. [Scripts de Testing](#scripts-de-testing)
4. [Umbrales de Performance](#umbrales-de-performance)
5. [Cómo Ejecutar](#cómo-ejecutar)
6. [Análisis de Resultados](#análisis-de-resultados)
7. [Integración CI/CD](#integración-cicd)
8. [Troubleshooting](#troubleshooting)
9. [Mejores Prácticas](#mejores-prácticas)

---

## Descripción General

Este directorio contiene la suite completa de load testing para el Dashboard del Mini Market. Los tests están diseñados para:

- **Validar performance** bajo diferentes cargas de trabajo
- **Identificar bottlenecks** antes de deployment
- **Establecer baselines** de performance
- **Verificar SLOs** (Service Level Objectives)
- **Simular tráfico real** de usuarios y Prometheus

### Arquitectura de Testing

```
load_testing/
├── test-health.js              # Baseline: health check endpoint
├── test-inventory-read.js      # Lectura de inventario (GET)
├── test-inventory-write.js     # Escritura de inventario (POST)
├── test-metrics.js             # Scraping de métricas Prometheus
├── run-all.sh                  # Orquestador de tests
├── results/                    # Resultados de ejecuciones
│   ├── *.json                  # Datos raw de k6
│   ├── *.txt                   # Summaries legibles
│   └── *.log                   # Logs de ejecución
└── LOAD_TESTING.md             # Esta documentación
```

---

## Herramientas

### k6 - Modern Load Testing

**¿Por qué k6?**
- Escrito en Go, altamente performante
- Scripts en JavaScript ES6+
- CLI simple y poderosa
- Métricas detalladas y custom
- Integración con CI/CD
- Open source y bien documentado

**Instalación:**

```bash
# Ubuntu/Debian
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# macOS
brew install k6

# Windows
choco install k6

# Docker
docker pull grafana/k6:latest
```

**Verificar instalación:**

```bash
k6 version
# Ejemplo output: k6 v0.47.0 (2023-11-29T10:48:49+0000/v0.47.0-0-gd8c1f07, go1.21.4, linux/amd64)
```

---

## Scripts de Testing

### 1. test-health.js - Baseline Performance

**Propósito:** Validar que el health check endpoint responde correctamente bajo carga.

**Escenario:**
```
Usuarios: 0 → 50 (30s) → 50 (1m) → 100 (30s) → 100 (1m) → 0 (30s)
Duración total: 3.5 minutos
```

**Umbrales:**
- ✅ P95 latency < 100ms
- ✅ Error rate < 0.1%
- ✅ Throughput > 200 req/s

**Ejemplo de ejecución:**

```bash
k6 run test-health.js

# Con variables de entorno
k6 run -e BASE_URL=https://staging.example.com test-health.js
```

**Métricas clave:**
- `http_req_duration`: Tiempo de respuesta total
- `http_req_waiting`: Tiempo esperando respuesta del servidor
- `http_reqs`: Total de requests realizados
- `health_check_duration`: Métrica custom para este endpoint

---

### 2. test-inventory-read.js - Read Operations

**Propósito:** Medir performance de operaciones de lectura (GET) sobre el inventario.

**Escenario:**
```
Usuarios: 0 → 30 (1m) → 30 (2m) → 60 (1m) → 60 (2m) → 0 (1m)
Duración total: 7 minutos
```

**Endpoints testeados:**
- `GET /api/inventory` - Listar todos los productos
- `GET /api/inventory/:sku` - Obtener producto por SKU
- `GET /api/inventory?filters` - Búsquedas con filtros

**Umbrales:**
- ✅ P95 latency < 300ms
- ✅ Error rate < 0.5%
- ✅ Throughput > 100 req/s
- ✅ Auth errors < 10

**Ejemplo de ejecución:**

```bash
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=your-api-key-here \
       test-inventory-read.js
```

**Checks realizados:**
- Status code 200
- Response time dentro de SLO
- Estructura de respuesta válida (array de productos)
- Datos no vacíos
- Autenticación exitosa

---

### 3. test-inventory-write.js - Write Operations

**Propósito:** Validar performance de operaciones de escritura (POST) sobre el inventario.

⚠️ **ADVERTENCIA:** Este test crea datos de prueba en el sistema. Usar solo en ambientes de testing.

**Escenario:**
```
Usuarios: 0 → 10 (30s) → 10 (1m) → 25 (30s) → 25 (1m) → 50 (30s) → 50 (1m) → 0 (30s)
Duración total: 5.5 minutos
```

**Endpoints testeados:**
- `POST /api/inventory` - Crear nuevo producto
- `POST /api/inventory/update-stock` - Actualizar stock
- `POST /api/inventory/bulk-update` - Actualización masiva

**Umbrales:**
- ✅ P95 latency < 500ms (writes son más lentas)
- ✅ Error rate < 1%
- ✅ Throughput > 50 req/s
- ✅ Successful writes > 1000

**Ejemplo de ejecución:**

```bash
# Solo en ambientes de testing
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=test-api-key-dev \
       test-inventory-write.js
```

**Datos generados:**
- SKUs con formato `TEST-SKU-{timestamp}-{random}`
- Productos en categorías: lácteos, bebidas, panadería, carnes, verduras, limpieza
- Proveedores ficticios: SUPPLIER-A, SUPPLIER-B, etc.

**Limpieza post-test:**
```sql
-- Eliminar productos de prueba
DELETE FROM productos WHERE sku LIKE 'TEST-SKU-%';
```

---

### 4. test-metrics.js - Prometheus Scraping

**Propósito:** Simular scraping de Prometheus y validar que no impacta el servicio.

**Escenario:**
```
Usuarios: 0 → 20 (30s) → 20 (2m) → 50 (30s) → 50 (1m) → 0 (30s)
Duración total: 4.5 minutos
Sleep entre requests: 0.5s (simular intervalo de Prometheus)
```

**Umbrales:**
- ✅ P95 latency < 200ms
- ✅ Error rate < 0.1%
- ✅ Throughput > 50 req/s
- ✅ Formato Prometheus válido

**Ejemplo de ejecución:**

```bash
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=your-metrics-key \
       test-metrics.js
```

**Validaciones:**
- Response contiene `# HELP` y `# TYPE` (formato Prometheus)
- Métricas del dashboard presentes:
  - `dashboard_requests_total`
  - `dashboard_errors_total`
  - `dashboard_request_duration_ms_p95`
- Tamaño de respuesta razonable

---

## Umbrales de Performance

### Service Level Objectives (SLOs)

| Métrica | Target | Crítico | Endpoint |
|---------|--------|---------|----------|
| Availability | 99.9% | 99.5% | Todos |
| P95 Latency | < 300ms | < 500ms | API |
| P99 Latency | < 500ms | < 1000ms | API |
| Error Rate | < 0.5% | < 1% | API |
| Throughput | > 100 req/s | > 50 req/s | API |

### Por Endpoint

#### GET /health
- **P95:** < 100ms
- **Error rate:** < 0.1%
- **Throughput:** > 200 req/s
- **Availability:** 99.99%

#### GET /api/inventory
- **P95:** < 300ms
- **Error rate:** < 0.5%
- **Throughput:** > 100 req/s
- **Availability:** 99.9%

#### POST /api/inventory
- **P95:** < 500ms
- **Error rate:** < 1%
- **Throughput:** > 50 req/s
- **Availability:** 99.9%

#### GET /metrics
- **P95:** < 200ms
- **Error rate:** < 0.1%
- **Throughput:** > 50 req/s
- **Availability:** 99.95%

### Interpretación de Resultados

**✅ PASS:** Todos los umbrales cumplidos
**⚠️ WARNING:** 1-2 umbrales no cumplidos
**❌ FAIL:** 3+ umbrales no cumplidos o error rate > 5%

---

## Cómo Ejecutar

### Ejecución Individual

**Test específico:**
```bash
cd inventario-retail/scripts/load_testing

# Health check
k6 run test-health.js

# Inventory read (requiere API key)
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=test-api-key-dev \
       test-inventory-read.js

# Metrics
k6 run -e BASE_URL=http://localhost:8080 \
       -e API_KEY=test-api-key-dev \
       test-metrics.js
```

**Con opciones avanzadas:**
```bash
# Salida JSON
k6 run --out json=results/output.json test-health.js

# Con más usuarios virtuales
k6 run --vus 100 --duration 5m test-health.js

# Modo silencioso
k6 run --quiet test-health.js

# Con tags
k6 run --tag environment=staging test-health.js
```

### Ejecución de Suite Completa

**Script de orquestación:**
```bash
cd inventario-retail/scripts/load_testing

# Ejecución básica
./run-all.sh

# Con variables personalizadas
BASE_URL=https://staging.example.com \
API_KEY=staging-key \
./run-all.sh

# Omitir tests de escritura
SKIP_WRITE_TESTS=true ./run-all.sh

# Continuar aunque fallen tests
CONTINUE_ON_FAILURE=true ./run-all.sh
```

**Opciones del script:**
- `BASE_URL`: URL del servicio (default: http://localhost:8080)
- `API_KEY`: API key para autenticación (default: test-api-key-dev)
- `SKIP_WRITE_TESTS`: Omitir tests de escritura (default: false)
- `CONTINUE_ON_FAILURE`: Continuar si un test falla (default: false)

### Ejecución en Docker

```bash
# Health check
docker run --rm -i grafana/k6:latest run - < test-health.js

# Con network host (acceder a localhost)
docker run --rm --network="host" -i grafana/k6:latest run \
    -e BASE_URL=http://localhost:8080 \
    - < test-inventory-read.js

# Con volumen para resultados
docker run --rm \
    -v $(pwd)/results:/results \
    -e BASE_URL=http://host.docker.internal:8080 \
    grafana/k6:latest run \
    --out json=/results/output.json \
    /scripts/test-health.js
```

### Ejecución Programada (Cron)

```bash
# Agregar a crontab
crontab -e

# Ejecutar daily a las 2 AM
0 2 * * * cd /path/to/load_testing && SKIP_WRITE_TESTS=true ./run-all.sh >> /var/log/load-tests.log 2>&1
```

---

## Análisis de Resultados

### Estructura de Resultados

```
results/
├── test-health-20231016_143022.log
├── test-inventory-read-20231016_143525.log
├── test-metrics-20231016_144030.log
├── consolidated-report-20231016_144530.txt
├── health-check-summary.json
├── inventory-read-summary.json
└── metrics-summary.json
```

### Leer Summary en Terminal

```bash
# Summary de k6 (al final del output)
cat results/test-health-20231016_143022.log | tail -n 50

# JSON summary
cat results/health-check-summary.json | jq '.metrics.http_req_duration'

# Reporte consolidado
cat results/consolidated-report-20231016_144530.txt
```

### Métricas Clave

**http_req_duration:**
```
avg=120.45ms min=45.12ms med=98.33ms max=456.78ms
p(90)=180.23ms p(95)=220.15ms p(99)=380.44ms
```

**Interpretación:**
- `avg`: Promedio (útil pero no suficiente)
- `med`: Mediana (50% de requests)
- `p(90)`: 90% de requests debajo de este valor
- `p(95)`: **Métrica principal para SLO**
- `p(99)`: Detectar outliers

**http_reqs:**
```
count=12450 rate=207.5/s
```

**Interpretación:**
- `count`: Total de requests realizados
- `rate`: Throughput en req/s

**http_req_failed:**
```
passes=45 fails=12405 (0.36%)
```

**Interpretación:**
- `passes`: Requests exitosos
- `fails`: Requests fallidos
- Error rate = fails / (passes + fails)

### Análisis con jq

```bash
# Top 5 métricas por duración
cat results/health-check-summary.json | \
    jq '.metrics | to_entries | sort_by(.value.values.avg) | reverse | .[:5]'

# Error rate
cat results/health-check-summary.json | \
    jq '.metrics.http_req_failed.values.rate * 100' 

# Throughput
cat results/health-check-summary.json | \
    jq '.metrics.http_reqs.values.rate'

# Check success rate
cat results/health-check-summary.json | \
    jq '.root_group.checks[] | {name: .name, rate: .passes / (.passes + .fails)}'
```

### Visualización con Grafana

k6 puede exportar métricas a diversos backends:

```bash
# A InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 test-health.js

# A Prometheus (con extensión)
k6 run --out prometheus test-health.js

# A JSON
k6 run --out json=output.json test-health.js
```

---

## Integración CI/CD

### GitHub Actions Workflow

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to test'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Run load tests
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
          API_KEY: ${{ secrets.STAGING_DASHBOARD_API_KEY }}
        run: |
          cd inventario-retail/scripts/load_testing
          SKIP_WRITE_TESTS=true ./run-all.sh
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: inventario-retail/scripts/load_testing/results/
          retention-days: 30
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('inventario-retail/scripts/load_testing/results/consolidated-report-*.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 📊 Load Test Results\n\`\`\`\n${report}\n\`\`\``
            });
```

### Pre-Deployment Gate

```yaml
# En workflow de deployment
- name: Performance baseline check
  run: |
    cd inventario-retail/scripts/load_testing
    k6 run --quiet test-health.js
    if [ $? -ne 0 ]; then
      echo "❌ Performance baseline not met. Aborting deployment."
      exit 1
    fi
```

### Umbral Dinámico en CI

```javascript
// En script k6
export const options = {
  thresholds: {
    http_req_duration: [
      // Si es PR: umbrales más estrictos
      __ENV.CI_CONTEXT === 'pull_request' ? 'p(95)<250' : 'p(95)<300'
    ],
  },
};
```

---

## Troubleshooting

### Error: "k6 no encontrado"

**Problema:** k6 no está instalado o no está en PATH.

**Solución:**
```bash
# Verificar instalación
which k6

# Reinstalar
sudo apt-get update && sudo apt-get install k6

# Verificar versión
k6 version
```

---

### Error: "Connection refused"

**Problema:** El servicio no está disponible en la URL especificada.

**Solución:**
```bash
# Verificar que el servicio esté corriendo
curl http://localhost:8080/health

# Verificar puerto correcto
netstat -tuln | grep 8080

# Verificar variable BASE_URL
echo $BASE_URL
```

---

### Error: "401 Unauthorized"

**Problema:** API key inválida o ausente.

**Solución:**
```bash
# Verificar que API_KEY esté configurada
echo $API_KEY

# Probar manualmente con curl
curl -H "X-API-Key: test-api-key-dev" http://localhost:8080/api/inventory

# Verificar en dashboard_app.py cuál es la key esperada
grep -r "DASHBOARD_API_KEY" inventario-retail/web_dashboard/
```

---

### Umbrales no cumplidos

**Problema:** Tests fallan porque no cumplen umbrales de performance.

**Diagnóstico:**
```bash
# Ver métricas detalladas
cat results/*.json | jq '.metrics.http_req_duration'

# Identificar requests lentos
cat results/*.json | jq '.metrics.http_req_duration.values | {max, "p(99)", "p(95)"}'
```

**Causas comunes:**
1. **Base de datos lenta:** Revisar queries, agregar índices
2. **CPU/memoria limitada:** Escalar recursos
3. **Network latency:** Usar misma región/AZ
4. **Cold start:** Ejecutar warmup antes del test
5. **Logging excesivo:** Reducir nivel de log en producción

**Soluciones:**
```bash
# Warmup antes del test real
k6 run --vus 10 --duration 30s test-health.js

# Reducir carga del test
k6 run --vus 25 --duration 2m test-inventory-read.js

# Ajustar umbrales temporalmente (solo para diagnóstico)
# Editar test-*.js y cambiar thresholds
```

---

### OOM (Out of Memory)

**Problema:** k6 consume mucha memoria y es killed por el sistema.

**Solución:**
```bash
# Reducir VUs y duración
k6 run --vus 50 --duration 3m test-health.js

# Usar modo distribuido (k6 Cloud o k6-operator)
k6 cloud test-health.js

# Aumentar límite de memoria del sistema
ulimit -v unlimited
```

---

## Mejores Prácticas

### 1. Empezar Simple

✅ **DO:**
```bash
# Test pequeño primero
k6 run --vus 10 --duration 1m test-health.js
```

❌ **DON'T:**
```bash
# No empezar con carga masiva
k6 run --vus 1000 --duration 30m test-health.js
```

---

### 2. Usar Ramp-Up Gradual

✅ **DO:**
```javascript
stages: [
  { duration: '1m', target: 50 },   // Gradual
  { duration: '3m', target: 50 },   // Sostener
  { duration: '1m', target: 0 },    // Ramp-down
]
```

❌ **DON'T:**
```javascript
stages: [
  { duration: '5s', target: 500 },  // Spike inmediato
]
```

---

### 3. Validar Respuestas

✅ **DO:**
```javascript
check(response, {
  'status is 200': (r) => r.status === 200,
  'has expected structure': (r) => r.json('products') !== undefined,
  'data is not empty': (r) => r.json('products').length > 0,
});
```

❌ **DON'T:**
```javascript
// Solo verificar status code
check(response, {
  'status is 200': (r) => r.status === 200,
});
```

---

### 4. Simular Comportamiento Real

✅ **DO:**
```javascript
export default function () {
  http.get('/api/inventory');
  sleep(Math.random() * 2 + 1);  // 1-3 segundos
  
  http.get('/api/inventory/SKU001');
  sleep(Math.random() * 3 + 2);  // 2-5 segundos
}
```

❌ **DON'T:**
```javascript
export default function () {
  http.get('/api/inventory');
  http.get('/api/inventory');
  http.get('/api/inventory');
  // Sin pauses, comportamiento irreal
}
```

---

### 5. No Testear en Producción (Sin Planificación)

⚠️ **WARNING:** Load testing en producción puede causar:
- Degradación del servicio
- Aumento de costos (tráfico, compute)
- Alertas falsas
- Impacto en usuarios reales

**Si debes testear en producción:**
1. Hacerlo en horario de bajo tráfico
2. Empezar con carga mínima
3. Tener plan de rollback
4. Notificar al equipo
5. Monitorear en tiempo real

---

### 6. Limpiar Datos de Prueba

✅ **DO:**
```bash
# Después de test-inventory-write.js
psql -d minimarket -c "DELETE FROM productos WHERE sku LIKE 'TEST-SKU-%';"
```

---

### 7. Versionado de Tests

✅ **DO:**
- Commitear scripts de load testing al repo
- Versionar junto con código de aplicación
- Actualizar tests cuando cambien endpoints

---

### 8. Documentar Baselines

```markdown
## Baseline Performance (2023-10-16)

### Environment
- Instance: t3.medium (2 vCPU, 4GB RAM)
- Database: PostgreSQL 14 (db.t3.small)
- Region: us-east-1

### Results
- GET /api/inventory: P95 = 245ms, Throughput = 120 req/s
- POST /api/inventory: P95 = 420ms, Throughput = 65 req/s
```

---

## Referencias

### Documentación Oficial

- **k6:** https://k6.io/docs/
- **k6 Cloud:** https://k6.io/cloud/
- **Grafana k6:** https://grafana.com/docs/k6/

### Tutoriales y Guías

- [k6 Getting Started](https://k6.io/docs/getting-started/running-k6/)
- [k6 Test Types](https://k6.io/docs/test-types/introduction/)
- [k6 Metrics](https://k6.io/docs/using-k6/metrics/)
- [k6 Thresholds](https://k6.io/docs/using-k6/thresholds/)

### Comunidad

- GitHub: https://github.com/grafana/k6
- Slack: https://k6.io/slack
- Forum: https://community.k6.io/

---

## Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2023-10-16 | Creación inicial de suite de load testing |

---

**Mantenido por:** Equipo Mini Market  
**Última actualización:** 16 de octubre de 2023  
**Contacto:** [GitHub Issues](https://github.com/your-org/your-repo/issues)
