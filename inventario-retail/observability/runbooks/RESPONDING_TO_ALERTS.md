# Runbook: Responding to Alerts - Mini Market Observability

**Última actualización:** 4 de octubre de 2025  
**Versión:** 1.0  
**Autor:** DevOps Team - ETAPA 3 Phase 1

---

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Alertas CRITICAL](#alertas-critical)
  - [ServiceDown](#servicedown)
  - [HighErrorRate](#higherrorrate)
  - [DatabaseDown](#databasedown)
  - [DiskSpaceCritical](#diskspacecritical)
- [Alertas HIGH](#alertas-high)
  - [HighLatency](#highlatency)
  - [MemoryPressure](#memorypressure)
  - [CPUHigh](#cpuhigh)
  - [StockCritico](#stockcritico)
  - [OCRTimeoutSpike](#ocrtimeoutspike)
  - [CacheHitRateLow](#cachehitratelow)
- [Alertas MEDIUM](#alertas-medium)
  - [SlowRequests](#slowrequests)
  - [InflacionAnomaly](#inflacionanomaly)
  - [MLModelDrift](#mlmodeldrift)
  - [LogVolumeSpike](#logvolumespike)
  - [DeploymentIssue](#deploymentissue)
- [Procedimientos Generales](#procedimientos-generales)
- [Escalación](#escalación)
- [Referencias](#referencias)

---

## Introducción

Este runbook describe los procedimientos de respuesta para todas las alertas configuradas en Prometheus Alertmanager para el sistema Multi-Agente Mini Market. Las alertas se clasifican por severidad:

- **CRITICAL** 🔴: Requiere respuesta inmediata (5 min), impacta disponibilidad del sistema
- **HIGH** 🟠: Requiere respuesta urgente (15 min), impacta calidad del servicio
- **MEDIUM** 🟡: Requiere atención (30 min), puede escalar si no se resuelve

**Canales de notificación:**
- Slack: `#minimarket-alerts` (todas las severidades)
- PagerDuty: Solo alertas CRITICAL (configurar en producción)

**Dashboards de referencia:**
- System Overview: `http://<grafana>:3000/d/minimarket-system-overview`
- Business KPIs: `http://<grafana>:3000/d/minimarket-business-kpis`
- Performance: `http://<grafana>:3000/d/minimarket-performance`
- ML Service: `http://<grafana>:3000/d/minimarket-ml-service`

---

## Alertas CRITICAL

### ServiceDown

**Descripción:** Un servicio crítico no responde (down > 2 minutos)

**Query:** `up{job=~"agente_deposito|agente_negocio|ml_service|dashboard"} == 0`

**Umbral:** `for: 2m`

**Impacto:**
- 🔴 Sistema parcial o totalmente inoperativo
- 🔴 Pérdida de funcionalidad crítica
- 🔴 Usuarios no pueden acceder al dashboard o funcionalidades

#### Diagnóstico

1. **Verificar estado del servicio:**
   ```bash
   docker ps -a | grep -E "(agente_deposito|agente_negocio|ml-service|dashboard)"
   ```

2. **Revisar logs del contenedor:**
   ```bash
   docker logs --tail 100 <container_name>
   ```

3. **Verificar salud del servicio:**
   ```bash
   curl -f http://localhost:<port>/health
   # Puertos: deposito:8001, negocio:8002, ml:8003, dashboard:8080
   ```

4. **Revisar Grafana System Overview:**
   - Panel "Service Health Status" mostrará el servicio en rojo

#### Resolución

**Causa 1: Contenedor crasheado**
```bash
# Reiniciar el contenedor específico
docker-compose restart <service_name>

# Verificar que levanta correctamente
docker logs -f <container_name>
```

**Causa 2: OOMKilled (Out of Memory)**
```bash
# Verificar evento OOM en logs del sistema
dmesg | grep -i "oom"

# Aumentar límite de memoria en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G  # Aumentar de 512M a 1G

# Aplicar cambios
docker-compose up -d <service_name>
```

**Causa 3: Puerto bloqueado o conflicto**
```bash
# Verificar puertos en uso
netstat -tlnp | grep -E "(8001|8002|8003|8080)"

# Si hay conflicto, detener proceso conflictivo o cambiar puerto en docker-compose.yml
```

**Causa 4: Error de configuración o dependencias**
```bash
# Revisar variables de entorno
docker exec <container_name> env | grep -E "(DATABASE|REDIS|ML)"

# Verificar conectividad a dependencias
docker exec <container_name> ping -c 3 postgres
docker exec <container_name> ping -c 3 redis

# Reconstruir imagen si hay cambios de código
docker-compose build <service_name>
docker-compose up -d <service_name>
```

#### Verificación

```bash
# 1. Servicio responde en health endpoint
curl http://localhost:<port>/health
# Esperado: HTTP 200 {"status": "healthy"}

# 2. Métricas disponibles
curl http://localhost:<port>/metrics
# Esperado: HTTP 200 con métricas Prometheus

# 3. Prometheus target UP
# Visitar http://localhost:9090/targets
# Verificar que el target aparece en verde
```

#### Escalación

- **No resuelto en 10 min:** Notificar a Lead DevOps + On-Call Engineer
- **Múltiples servicios down:** Escalar a CTO inmediatamente
- **Impacto en producción:** Activar War Room

---

### HighErrorRate

**Descripción:** Tasa de errores HTTP >5% durante 5 minutos

**Query:** `(rate(http_errors_total[5m]) / rate(http_requests_total[5m]) * 100) > 5`

**Umbral:** `for: 5m`

**Impacto:**
- 🔴 Degradación severa de calidad de servicio
- 🔴 Usuarios experimentan errores frecuentes
- 🔴 Pérdida potencial de datos o transacciones

#### Diagnóstico

1. **Identificar servicio afectado:**
   ```bash
   # Revisar Dashboard System Overview, panel "Error Rate %"
   # O consultar Prometheus directamente:
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=rate(http_errors_total[5m]) by (job)'
   ```

2. **Analizar logs de errores:**
   ```bash
   # Via Loki (recomendado)
   # Abrir Grafana > Explore > Loki
   # Query: {job="<service>"} |= "ERROR" | json
   
   # Via Docker logs
   docker logs --tail 200 <container_name> | grep -i error
   ```

3. **Verificar códigos de estado HTTP:**
   ```bash
   # Consultar distribución de códigos de error
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m]) by (status, job)'
   ```

4. **Revisar recursos del sistema:**
   ```bash
   # CPU y memoria del contenedor
   docker stats --no-stream <container_name>
   ```

#### Resolución

**Causa 1: Error de base de datos (5xx errors)**
```bash
# Verificar conectividad a PostgreSQL
docker exec <container_name> pg_isready -h postgres -U minimarket

# Revisar logs de PostgreSQL
docker logs postgres | tail -50

# Verificar conexiones activas
docker exec postgres psql -U minimarket -c "SELECT count(*) FROM pg_stat_activity;"

# Si PostgreSQL está sobrecargado, reiniciar pool de conexiones
docker-compose restart <service_name>
```

**Causa 2: Timeout a servicios externos (ML, APIs)**
```bash
# Verificar latencia de ML service
curl -w "@-" -s http://localhost:8003/health <<< '
time_namelookup:  %{time_namelookup}
time_connect:  %{time_connect}
time_starttransfer:  %{time_starttransfer}
time_total:  %{time_total}
'

# Si ML service está lento, revisar OCR timeouts
# Ver panel "OCR Timeout Events" en ML Service Monitor dashboard

# Reiniciar ML service si es necesario
docker-compose restart ml-service
```

**Causa 3: Bug en código desplegado recientemente**
```bash
# Revisar último commit desplegado
git log -1 --oneline

# Rollback a versión anterior
git checkout <previous_commit_sha>
docker-compose build <service_name>
docker-compose up -d <service_name>

# O usar imagen previa en GHCR
docker pull ghcr.io/<owner>/<repo>:<previous_tag>
# Editar docker-compose.yml para usar tag anterior
docker-compose up -d <service_name>
```

**Causa 4: Validación de datos falla (4xx errors)**
```bash
# Revisar ejemplos de requests que fallan
docker logs <container_name> | grep "422\|400" | tail -20

# Si es error de validación masivo, podría ser cambio en API
# Notificar a equipo de desarrollo para fix urgente
```

#### Verificación

```bash
# 1. Tasa de error vuelve a <0.5%
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=(rate(http_errors_total[5m])/rate(http_requests_total[5m])*100)'
# Esperado: < 0.5

# 2. No hay nuevos errores en logs
docker logs --since 5m <container_name> | grep -i error | wc -l
# Esperado: 0 o muy pocos

# 3. Dashboard System Overview muestra verde en "Error Rate %"
```

#### Escalación

- **No resuelto en 15 min:** Notificar a Development Team Lead
- **Requiere rollback:** Coordinar con Tech Lead y QA
- **Bug crítico identificado:** Crear incident report y post-mortem

---

### DatabaseDown

**Descripción:** PostgreSQL no responde durante >1 minuto

**Query:** `pg_up == 0`

**Umbral:** `for: 1m`

**Impacto:**
- 🔴 **CRÍTICO** - Todos los servicios pierden persistencia
- 🔴 Sistema completamente inoperativo
- 🔴 Riesgo de pérdida de datos si no se resuelve rápido

#### Diagnóstico

1. **Verificar contenedor PostgreSQL:**
   ```bash
   docker ps -a | grep postgres
   docker logs --tail 50 postgres
   ```

2. **Intentar conexión manual:**
   ```bash
   docker exec -it postgres psql -U minimarket -d minimarket -c "\l"
   ```

3. **Revisar espacio en disco:**
   ```bash
   df -h
   docker exec postgres df -h /var/lib/postgresql/data
   ```

4. **Verificar estado del proceso:**
   ```bash
   docker exec postgres pg_isready -U minimarket
   ```

#### Resolución

**Causa 1: Contenedor PostgreSQL detenido**
```bash
# Reiniciar PostgreSQL
docker-compose restart postgres

# Verificar que levanta
docker logs -f postgres | grep "ready to accept connections"
```

**Causa 2: Corrupción de datos o crash**
```bash
# Revisar logs para detectar corrupción
docker logs postgres | grep -i "corrupt\|panic\|fatal"

# Si hay corrupción, intentar recovery
docker exec postgres pg_resetwal /var/lib/postgresql/data

# Si falla, restaurar desde último backup
# (Ver BACKUP_RESTORE_RUNBOOK.md)
```

**Causa 3: Disco lleno**
```bash
# Liberar espacio eliminando logs antiguos
docker exec postgres sh -c "find /var/lib/postgresql/data/log -name '*.log' -mtime +7 -delete"

# Vacuum para recuperar espacio
docker exec postgres psql -U minimarket -d minimarket -c "VACUUM FULL;"

# Si es crítico, aumentar volumen en producción
```

**Causa 4: Conexiones máximas alcanzadas**
```bash
# Ver conexiones activas
docker exec postgres psql -U minimarket -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Terminar conexiones idle
docker exec postgres psql -U minimarket -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';
"

# Aumentar max_connections en postgresql.conf si es recurrente
```

#### Verificación

```bash
# 1. PostgreSQL responde
docker exec postgres pg_isready -U minimarket
# Esperado: "accepting connections"

# 2. Servicios pueden conectar
docker exec agente-deposito python -c "import psycopg2; psycopg2.connect('host=postgres user=minimarket password=<pass> dbname=minimarket')"

# 3. Prometheus target "postgres-exporter" UP
# http://localhost:9090/targets

# 4. Dashboard Performance muestra conexiones normales
```

#### Escalación

- **No resuelve en 5 min:** Escalar a DBA + Lead DevOps inmediatamente
- **Requiere restauración de backup:** Notificar CTO y activar DR plan
- **Pérdida de datos confirmada:** Activar incident response team completo

---

### DiskSpaceCritical

**Descripción:** Espacio en disco <10% durante >5 minutos

**Query:** `(node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10`

**Umbral:** `for: 5m`

**Impacto:**
- 🔴 Riesgo inminente de crash de servicios
- 🔴 PostgreSQL puede corrupcionar datos
- 🔴 Logs se detienen, pérdida de observabilidad

#### Diagnóstico

1. **Verificar espacio en disco:**
   ```bash
   df -h
   ```

2. **Identificar directorios grandes:**
   ```bash
   du -sh /var/lib/docker/* | sort -rh | head -10
   ```

3. **Revisar logs de Docker:**
   ```bash
   du -sh /var/lib/docker/containers/*
   ```

4. **Verificar volúmenes de Docker:**
   ```bash
   docker system df -v
   ```

#### Resolución

**Acción inmediata: Liberar espacio rápido**
```bash
# 1. Limpiar logs de contenedores viejos
docker system prune -f

# 2. Eliminar imágenes no usadas
docker image prune -a -f

# 3. Limpiar volúmenes huérfanos
docker volume prune -f

# 4. Truncar logs grandes de contenedores
find /var/lib/docker/containers/ -name "*-json.log" -size +100M -exec truncate -s 50M {} \;
```

**Solución permanente:**
```bash
# 1. Configurar rotación de logs en docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "3"

# 2. Configurar Loki retention (ya está en 30d)
# Ver inventario-retail/observability/loki/loki-config.yml

# 3. Configurar backup y limpieza de PostgreSQL
# Agregar cron job para vacuum y limpieza de WAL logs

# 4. Monitorear tendencia de crecimiento
# Panel en Dashboard Performance muestra "Disk I/O"
```

**Si el espacio sigue crítico:**
```bash
# Aumentar volumen en producción (AWS EBS, Azure Disk, etc.)
# Procedimiento específico según cloud provider
# Documentar en INFRASTRUCTURE_SCALING.md
```

#### Verificación

```bash
# 1. Espacio recuperado >20%
df -h | grep -E "/$|/var"
# Esperado: >20% available

# 2. Servicios operando normalmente
docker ps | grep -E "(Up|healthy)"

# 3. PostgreSQL sin errores de I/O
docker logs postgres | tail -20 | grep -i "space\|disk"

# 4. Dashboard Performance muestra Disk I/O normal
```

#### Escalación

- **No se puede liberar suficiente espacio:** Notificar Infrastructure Team para provisionar más storage
- **Corrupción detectada post-cleanup:** Escalar a DBA + incident response
- **Requiere migración de datos:** Coordinar con Architecture Team

---

## Alertas HIGH

### HighLatency

**Descripción:** P95 latency >300ms durante 10 minutos

**Query:** `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.3`

**Umbral:** `for: 10m`

**Impacto:**
- 🟠 Experiencia de usuario degradada
- 🟠 Posible timeout en integraciones
- 🟠 Puede escalar a ServiceDown si empeora

#### Diagnóstico

1. **Identificar servicio con alta latencia:**
   ```bash
   # Dashboard System Overview > "P95 Latency" panel
   # O consultar Prometheus:
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (job)'
   ```

2. **Revisar carga del sistema:**
   ```bash
   docker stats --no-stream
   ```

3. **Verificar queries lentas en PostgreSQL:**
   ```bash
   docker exec postgres psql -U minimarket -d minimarket -c "
     SELECT query, mean_exec_time, calls 
     FROM pg_stat_statements 
     ORDER BY mean_exec_time DESC 
     LIMIT 10;
   "
   ```

4. **Revisar cache hit rate de Redis:**
   ```bash
   # Dashboard Performance > "Redis Cache Hit Rate %" panel
   ```

#### Resolución

**Causa 1: Alta carga en PostgreSQL**
```bash
# Identificar queries lentas
docker exec postgres psql -U minimarket -c "
  SELECT pid, query, state, query_start 
  FROM pg_stat_activity 
  WHERE state != 'idle' AND query_start < NOW() - INTERVAL '30 seconds';
"

# Terminar query problemática si es necesaria
docker exec postgres psql -U minimarket -c "SELECT pg_terminate_backend(<pid>);"

# Aplicar índices si faltan (coordinar con dev team)
# Ejecutar ANALYZE para actualizar stats
docker exec postgres psql -U minimarket -c "ANALYZE;"
```

**Causa 2: Cache hit rate bajo en Redis**
```bash
# Verificar tasa de cache hits
docker exec redis redis-cli INFO stats | grep keyspace

# Aumentar memoria de Redis si es necesario
# Editar docker-compose.yml:
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

# Reiniciar Redis
docker-compose restart redis
```

**Causa 3: ML Service OCR lento**
```bash
# Revisar Dashboard ML Service Monitor > "OCR Processing Time"
# Si P95 >5s, es probable que OCR está saturado

# Verificar timeout events
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(ocr_timeout_events_total[5m])'

# Escalar workers de ML (si es aplicable) o reducir carga
```

**Causa 4: CPU throttling**
```bash
# Revisar Dashboard Performance > "CPU Usage %" panel
# Si >85%, aumentar límites de CPU en docker-compose.yml

deploy:
  resources:
    limits:
      cpus: '2.0'  # Aumentar de 1.0 a 2.0

docker-compose up -d <service_name>
```

#### Verificación

```bash
# 1. P95 latency <300ms
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
# Esperado: <0.3 (300ms)

# 2. CPU usage normal (<70%)
docker stats --no-stream | awk '{print $3}'

# 3. Dashboard System Overview muestra latencia verde
```

#### Escalación

- **Latency >1s persistente:** Escalar a Performance Engineering Team
- **Requiere cambios de código:** Coordinar con Development Team
- **Requiere scaling horizontal:** Notificar Infrastructure Team

---

### MemoryPressure

**Descripción:** Uso de memoria >80% durante 10 minutos

**Query:** `(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 80`

**Umbral:** `for: 10m`

**Impacto:**
- 🟠 Riesgo de OOMKill inminente
- 🟠 Posible degradación de performance
- 🟠 Puede llevar a ServiceDown

#### Diagnóstico

1. **Identificar contenedor con alta memoria:**
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" | sort -k3 -rh
   ```

2. **Revisar Dashboard Performance > "Memory Usage %" panel**

3. **Analizar memoria del proceso:**
   ```bash
   docker exec <container_name> ps aux --sort=-%mem | head -10
   ```

#### Resolución

**Acción inmediata:**
```bash
# Reiniciar servicio para liberar memoria
docker-compose restart <service_name>

# Monitorear si el problema persiste
docker stats <container_name>
```

**Solución permanente:**
```bash
# Aumentar límite de memoria en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G  # Aumentar según necesidad
    reservations:
      memory: 512M

# Aplicar cambios
docker-compose up -d <service_name>
```

**Si es memory leak:**
```bash
# Identificar memory leak con profiling (coordinar con dev team)
# Implementar fix en código y desplegar

# Workaround temporal: restart periódico
# Agregar health check con restart policy en docker-compose.yml
```

#### Verificación

```bash
# Uso de memoria <75%
docker stats --no-stream <container_name> | awk '{print $7}'
```

#### Escalación

- **OOMKill recurrente:** Escalar a Development Team para investigar leak
- **Requiere más recursos:** Notificar Infrastructure Team

---

### CPUHigh

**Descripción:** CPU >70% durante 15 minutos

**Query:** `(rate(container_cpu_usage_seconds_total[5m]) / container_spec_cpu_quota) * 100 > 70`

**Umbral:** `for: 15m`

**Impacto:**
- 🟠 Performance degradada
- 🟠 Alta latencia probable
- 🟠 Puede llevar a throttling

#### Diagnóstico

1. **Identificar contenedor:**
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | sort -k2 -rh
   ```

2. **Revisar Dashboard Performance > "CPU Usage %" panel**

3. **Verificar procesos dentro del contenedor:**
   ```bash
   docker exec <container_name> top -bn1 | head -20
   ```

#### Resolución

**Si es carga legítima:**
```bash
# Aumentar CPU quota en docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'

docker-compose up -d <service_name>
```

**Si es runaway process:**
```bash
# Reiniciar servicio
docker-compose restart <service_name>

# Investigar causa (coordinar con dev team)
```

#### Verificación

```bash
# CPU <70%
docker stats --no-stream <container_name>
```

#### Escalación

- **CPU crítico >90%:** Escalar inmediatamente a Infrastructure Team

---

### StockCritico

**Descripción:** >50 productos en stock crítico durante 15 minutos

**Query:** `negocio_stock_critico_productos > 50`

**Umbral:** `for: 15m`

**Impacto:**
- 🟠 **BUSINESS** - Riesgo de quiebre de stock
- 🟠 Pérdida potencial de ventas
- 🟠 Requiere acción de negocio

#### Diagnóstico

1. **Revisar Dashboard Business KPIs > "Stock Crítico Alerts" panel**

2. **Consultar productos en stock crítico:**
   ```bash
   docker exec agente-negocio python -c "
   import psycopg2
   conn = psycopg2.connect('host=postgres user=minimarket password=<pass> dbname=minimarket')
   cur = conn.cursor()
   cur.execute('SELECT nombre, stock_actual, stock_minimo FROM productos WHERE stock_actual <= stock_minimo ORDER BY stock_actual LIMIT 20')
   for row in cur.fetchall():
       print(row)
   "
   ```

3. **Verificar órdenes de compra generadas:**
   ```bash
   # Dashboard Business KPIs > "Órdenes de Compra" panel
   ```

#### Resolución

**Este es un evento de negocio, no técnico:**

1. **Notificar a Business Team / Gerente de Operaciones**
   - Enviar lista de productos críticos
   - Incluir proyección de quiebre de stock

2. **Verificar que agente_negocio está generando órdenes:**
   ```bash
   docker logs agente-negocio | grep "orden_compra" | tail -20
   ```

3. **Si el agente no está generando órdenes:**
   ```bash
   # Verificar logs de errores
   docker logs agente-negocio | grep -i error

   # Reiniciar agente_negocio
   docker-compose restart agente-negocio
   ```

4. **Acelerar procesamiento manual si es urgente:**
   ```bash
   # Trigger manual de generación de órdenes (si endpoint existe)
   curl -X POST http://localhost:8002/api/generar_ordenes -H "Content-Type: application/json"
   ```

#### Verificación

```bash
# Stock crítico disminuye
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=negocio_stock_critico_productos'
# Esperado: Número decreciente con el tiempo

# Órdenes generadas recientemente
docker logs agente-negocio | grep "orden_compra_generada" | tail -10
```

#### Escalación

- **Stock crítico no disminuye en 2 horas:** Escalar a Operations Manager
- **Agente_negocio con errores:** Escalar a Development Team
- **Requiere intervención manual:** Coordinar con Procurement Team

---

### OCRTimeoutSpike

**Descripción:** >10 timeouts de OCR por hora durante 10 minutos

**Query:** `rate(ocr_timeout_events_total[1h]) * 3600 > 10`

**Umbral:** `for: 10m`

**Impacto:**
- 🟠 Degradación de servicio ML
- 🟠 Productos no son procesados correctamente
- 🟠 Puede afectar cálculos de inflación

#### Diagnóstico

1. **Revisar Dashboard ML Service Monitor > "OCR Timeout Events" panel**

2. **Verificar latencia de OCR:**
   ```bash
   # Dashboard ML Service Monitor > "OCR Processing Time" panel
   # Si P95 >10s, OCR está muy lento
   ```

3. **Revisar logs de ML service:**
   ```bash
   docker logs ml-service | grep -i "timeout\|ocr" | tail -50
   ```

4. **Verificar carga de CPU/Memory de ML service:**
   ```bash
   docker stats ml-service --no-stream
   ```

#### Resolución

**Causa 1: Imágenes de mala calidad o muy grandes**
```bash
# Revisar ejemplos de imágenes que fallan
docker logs ml-service | grep "ocr_timeout" -A 5 -B 5

# Implementar preprocessing más agresivo (coordinar con dev team)
# Workaround: Aumentar timeout en configuración
```

**Causa 2: ML Service sobrecargado**
```bash
# Verificar requests/sec
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(ml_predictions_total[5m])'

# Si es alto, considerar:
# 1. Aumentar recursos de ML service
# 2. Implementar rate limiting
# 3. Escalar horizontalmente (múltiples instancias)
```

**Causa 3: Biblioteca OCR con problemas**
```bash
# Reiniciar ML service
docker-compose restart ml-service

# Si persiste, verificar versión de Tesseract/EasyOCR
docker exec ml-service python -c "import pytesseract; print(pytesseract.get_tesseract_version())"

# Considerar actualizar imagen o biblioteca OCR
```

#### Verificación

```bash
# Timeouts vuelven a <5/hora
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(ocr_timeout_events_total[1h])*3600'
# Esperado: <5

# P95 OCR processing time <5s
# Verificar en Dashboard ML Service Monitor
```

#### Escalación

- **Timeouts persisten >1 hora:** Escalar a ML Engineering Team
- **Requiere cambios en modelo:** Coordinar con Data Science Team
- **Impacta cálculos críticos:** Notificar Business Team del impacto

---

### CacheHitRateLow

**Descripción:** Redis cache hit rate <70% durante 15 minutos

**Query:** `(redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100 < 70`

**Umbral:** `for: 15m`

**Impacto:**
- 🟠 Performance degradada
- 🟠 Mayor carga en PostgreSQL
- 🟠 Alta latencia probable

#### Diagnóstico

1. **Revisar Dashboard Performance > "Redis Cache Hit Rate %" panel**

2. **Verificar estadísticas de Redis:**
   ```bash
   docker exec redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
   ```

3. **Revisar memoria de Redis:**
   ```bash
   docker exec redis redis-cli INFO memory
   ```

4. **Verificar eviction policy:**
   ```bash
   docker exec redis redis-cli CONFIG GET maxmemory-policy
   ```

#### Resolución

**Causa 1: Memoria de Redis insuficiente**
```bash
# Verificar keys evicted
docker exec redis redis-cli INFO stats | grep evicted

# Aumentar memoria de Redis en docker-compose.yml
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru

docker-compose up -d redis
```

**Causa 2: TTL muy corto o flush reciente**
```bash
# Verificar si hubo flush reciente
docker logs redis | grep -i "flush\|flushdb"

# Ajustar TTL en código si es necesario (coordinar con dev team)
```

**Causa 3: Patrón de acceso cambió (nuevos queries)**
```bash
# Warm up cache con queries comunes
# Ejecutar script de precarga si existe

# Monitorear mejora de hit rate
watch -n 5 'docker exec redis redis-cli INFO stats | grep keyspace'
```

#### Verificación

```bash
# Hit rate >80%
docker exec redis redis-cli INFO stats | grep keyspace_hits | awk -F: '{hit=$2} END {getline; miss=$2; print (hit/(hit+miss)*100)}'
# Esperado: >80
```

#### Escalación

- **Hit rate no mejora:** Escalar a Backend Team para revisar caching strategy
- **Requiere Redis Cluster:** Coordinar con Infrastructure Team

---

## Alertas MEDIUM

### SlowRequests

**Descripción:** P50 latency >200ms durante 20 minutos

**Query:** `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m])) > 0.2`

**Umbral:** `for: 20m`

**Impacto:**
- 🟡 Performance subóptima pero aceptable
- 🟡 Puede escalar a HighLatency

#### Diagnóstico y Resolución

Similar a **HighLatency** pero con menor urgencia. Seguir mismo procedimiento pero con timeline más relajado.

---

### InflacionAnomaly

**Descripción:** Inflación calculada difiere >5% del baseline durante 30 minutos

**Query:** `abs(ml_inflacion_calculada_percent - ml_inflacion_baseline_percent) > 5`

**Umbral:** `for: 30m`

**Impacto:**
- 🟡 **BUSINESS** - Posible anomalía en cálculos
- 🟡 Requiere revisión de modelo ML

#### Diagnóstico

1. **Revisar Dashboard Business KPIs > "Inflación Calculada %" panel**

2. **Verificar drift del modelo:**
   ```bash
   # Dashboard ML Service Monitor > "ML Model Drift Score" panel
   ```

3. **Consultar datos de entrada:**
   ```bash
   docker exec agente-deposito python -c "
   import psycopg2
   conn = psycopg2.connect('host=postgres user=minimarket password=<pass> dbname=minimarket')
   cur = conn.cursor()
   cur.execute('SELECT COUNT(*), AVG(precio) FROM productos WHERE fecha_actualizacion > NOW() - INTERVAL \\'1 day\\'')
   print(cur.fetchone())
   "
   ```

#### Resolución

**Este es mayormente un evento de negocio/ML:**

1. **Notificar a Data Science Team** para revisar modelo

2. **Verificar calidad de datos de entrada:**
   - Revisar si hay productos con precios anómalos
   - Verificar que OCR está funcionando correctamente

3. **Si es anomalía real del mercado:**
   - Documentar evento
   - Actualizar baseline si es sostenido

4. **Si es bug en modelo:**
   - Revertir a versión anterior del modelo
   - Coordinar fix con ML team

#### Verificación

```bash
# Anomalía se corrige
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=abs(ml_inflacion_calculada_percent - ml_inflacion_baseline_percent)'
# Esperado: <5
```

#### Escalación

- **Anomalía persiste >4 horas:** Escalar a Data Science Lead
- **Impacto en decisiones de negocio:** Notificar CFO/Operations Manager

---

### MLModelDrift

**Descripción:** Model drift score >0.15 durante 1 hora

**Query:** `ml_model_drift_score > 0.15`

**Umbral:** `for: 1h`

**Impacto:**
- 🟡 **ML** - Modelo perdiendo precisión
- 🟡 Predicciones menos confiables
- 🟡 Requiere reentrenamiento

#### Diagnóstico

1. **Revisar Dashboard ML Service Monitor > "ML Model Drift Score" panel**

2. **Verificar accuracy actual:**
   ```bash
   # Dashboard ML Service Monitor > "ML Price Prediction Accuracy %" panel
   ```

3. **Revisar distribución de datos:**
   ```bash
   # Consultar cambios recientes en productos
   docker exec postgres psql -U minimarket -c "
     SELECT categoria, COUNT(*), AVG(precio) 
     FROM productos 
     WHERE fecha_actualizacion > NOW() - INTERVAL '7 days'
     GROUP BY categoria;
   "
   ```

#### Resolución

**Acción de ML Team:**

1. **Evaluar si requiere reentrenamiento:**
   - Recolectar datos recientes
   - Evaluar performance en test set
   - Decidir si hacer retraining o ajuste

2. **Workaround temporal:**
   ```bash
   # Aumentar umbral de confianza para predicciones
   # (requiere cambio en código, coordinar con dev team)
   ```

3. **Reentrenar modelo:**
   ```bash
   # Ejecutar pipeline de retraining
   # (procedimiento específico del equipo ML)
   
   # Desplegar nuevo modelo
   # Actualizar docker image con nuevo modelo weights
   ```

4. **Monitorear mejora post-deployment:**
   ```bash
   # Verificar que drift score baja
   # Dashboard ML Service Monitor
   ```

#### Verificación

```bash
# Drift score <0.10
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=ml_model_drift_score'
# Esperado: <0.10

# Accuracy mejora
# Verificar en Dashboard ML Service Monitor > "ML Price Prediction Accuracy %"
```

#### Escalación

- **Drift persiste post-retraining:** Escalar a ML Engineering Lead
- **Accuracy crítica <80%:** Considerar rollback a modelo anterior

---

### LogVolumeSpike

**Descripción:** Volumen de logs aumenta >200% durante 15 minutos

**Query:** `rate(loki_distributor_lines_received_total[5m]) > 200`

**Umbral:** `for: 15m`

**Impacto:**
- 🟡 Posible error en loop causando spam
- 🟡 Riesgo de llenar disco
- 🟡 Degradación de Loki

#### Diagnóstico

1. **Identificar servicio con logs excesivos:**
   ```bash
   # Grafana > Explore > Loki
   # Query: rate({job=~".+"} [5m]) | unwrap bytes | sum by (job)
   ```

2. **Revisar logs del servicio:**
   ```bash
   docker logs --tail 100 <container_name>
   ```

#### Resolución

**Causa 1: Error loop**
```bash
# Identificar mensaje repetitivo
docker logs <container_name> | sort | uniq -c | sort -rn | head

# Reiniciar servicio para detener loop
docker-compose restart <container_name>

# Fix en código (coordinar con dev team)
```

**Causa 2: Debug logging activado en producción**
```bash
# Verificar nivel de log
docker exec <container_name> env | grep LOG_LEVEL

# Cambiar a INFO/WARNING
# Editar docker-compose.yml o variable de entorno
LOG_LEVEL: "INFO"

docker-compose up -d <container_name>
```

#### Verificación

```bash
# Volumen de logs vuelve a normal
# Grafana > Explore > Loki
# Query: rate({job="<service>"} [5m])
```

#### Escalación

- **Log spam persiste:** Escalar a Development Team
- **Disco llenándose rápido:** Trigger DiskSpaceCritical procedure

---

### DeploymentIssue

**Descripción:** Servicio reiniciado >3 veces en 10 minutos

**Query:** `changes(container_last_seen[10m]) > 3`

**Umbral:** `for: 10m`

**Impacto:**
- 🟡 Inestabilidad del servicio
- 🟡 Posible CrashLoopBackOff
- 🟡 Puede escalar a ServiceDown

#### Diagnóstico

1. **Verificar restarts:**
   ```bash
   docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "Restart|Restarting"
   ```

2. **Revisar logs de crashes:**
   ```bash
   docker logs --tail 200 <container_name> | grep -i "error\|fatal\|panic"
   ```

3. **Verificar health checks:**
   ```bash
   docker inspect <container_name> | jq '.[0].State.Health'
   ```

#### Resolución

**Causa 1: Health check demasiado estricto**
```bash
# Ajustar health check en docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 60s  # Aumentar start_period

docker-compose up -d <service_name>
```

**Causa 2: Bug en código reciente**
```bash
# Rollback a versión anterior
git log --oneline -10
git checkout <previous_commit>
docker-compose build <service_name>
docker-compose up -d <service_name>
```

**Causa 3: Dependencia no disponible**
```bash
# Verificar que PostgreSQL/Redis están UP
docker ps | grep -E "postgres|redis"

# Ajustar depends_on con healthcheck en docker-compose.yml
```

#### Verificación

```bash
# No más restarts en 15 minutos
docker ps --filter name=<service_name> --format "{{.Status}}"
# Esperado: "Up X minutes" sin "Restart"
```

#### Escalación

- **CrashLoopBackOff persiste:** Escalar a Development Team Lead
- **Requiere hotfix urgente:** Activar emergency deployment procedure

---

## Procedimientos Generales

### Post-Incident Checklist

Después de resolver cualquier alerta CRITICAL o HIGH:

1. ✅ **Documentar resolución:**
   - Causa raíz identificada
   - Pasos tomados para resolver
   - Duración del incidente
   - Impacto en usuarios/negocio

2. ✅ **Verificar métricas normalizadas:**
   - Revisar los 4 dashboards de Grafana
   - Confirmar que todas las métricas están en verde

3. ✅ **Comunicar resolución:**
   - Actualizar canal de Slack #minimarket-alerts
   - Notificar a stakeholders afectados

4. ✅ **Crear ticket de seguimiento:**
   - Si requiere fix permanente
   - Si requiere cambios de infraestructura
   - Si requiere actualización de runbooks

5. ✅ **Post-mortem (solo para CRITICAL):**
   - Agendar sesión de post-mortem
   - Documentar lecciones aprendidas
   - Crear action items para prevenir recurrencia

### Herramientas Útiles

**Comandos Docker esenciales:**
```bash
# Ver todos los contenedores (incluidos stopped)
docker ps -a

# Logs con timestamps
docker logs --timestamps <container_name>

# Logs desde hace X tiempo
docker logs --since 1h <container_name>

# Seguir logs en tiempo real
docker logs -f <container_name>

# Stats de todos los contenedores
docker stats --no-stream

# Inspeccionar configuración completa
docker inspect <container_name>

# Ejecutar comando dentro del contenedor
docker exec -it <container_name> bash
```

**Consultas Prometheus útiles:**
```promql
# Top 5 endpoints más lentos
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (endpoint))

# Servicios down en las últimas 24h
changes(up[24h]) > 0

# Errores por servicio
sum(rate(http_errors_total[5m])) by (job)

# Memoria disponible
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100
```

**Accesos rápidos:**
```bash
# Prometheus UI
http://localhost:9090

# Grafana
http://localhost:3000 (admin/admin)

# Alertmanager
http://localhost:9093

# Loki logs (via Grafana Explore)
http://localhost:3000/explore
```

---

## Escalación

### Matriz de Escalación

| Severidad | Tiempo sin resolver | Escalar a |
|-----------|---------------------|-----------|
| CRITICAL | 10 minutos | Lead DevOps + On-Call Engineer |
| CRITICAL | 30 minutos | CTO + Incident Response Team |
| HIGH | 30 minutos | Development Team Lead |
| HIGH | 2 horas | Operations Manager |
| MEDIUM | 4 horas | Team Lead correspondiente |

### Contactos de Escalación

**DevOps Team:**
- Lead DevOps: `@lead-devops` (Slack) / +54-XXX (On-Call)
- DevOps Engineer 1: `@devops1` (Slack)
- DevOps Engineer 2: `@devops2` (Slack)

**Development Team:**
- Tech Lead: `@tech-lead` (Slack)
- Backend Lead: `@backend-lead` (Slack)
- ML Engineer: `@ml-engineer` (Slack)

**Operations:**
- Operations Manager: `@ops-manager` (Slack)
- DBA: `@dba` (Slack)

**Executive:**
- CTO: `@cto` (Slack) / Solo para CRITICAL

### Protocolo de War Room

**Activar War Room cuando:**
- Múltiples servicios CRITICAL down
- Pérdida de datos confirmada
- Incidente afecta producción >30 minutos
- Impacto financiero significativo

**Procedimiento:**
1. Crear canal Slack `#war-room-YYYY-MM-DD-HHmm`
2. Invitar: CTO, Lead DevOps, Tech Lead, Operations Manager, DBA
3. Designar Incident Commander
4. Status updates cada 15 minutos
5. Documentación en tiempo real
6. Post-mortem obligatorio

---

## Referencias

**Documentación relacionada:**
- `DEPLOYMENT_GUIDE.md` - Procedimientos de deployment
- `DASHBOARD_TROUBLESHOOTING.md` - Troubleshooting de Grafana
- `BACKUP_RESTORE_RUNBOOK.md` - Procedimientos de backup/restore (TBD)
- `INFRASTRUCTURE_SCALING.md` - Scaling de infraestructura (TBD)

**Dashboards de Grafana:**
- System Overview: http://localhost:3000/d/minimarket-system-overview
- Business KPIs: http://localhost:3000/d/minimarket-business-kpis
- Performance: http://localhost:3000/d/minimarket-performance
- ML Service: http://localhost:3000/d/minimarket-ml-service

**Prometheus:**
- UI: http://localhost:9090
- Targets: http://localhost:9090/targets
- Alerts: http://localhost:9090/alerts
- Rules: http://localhost:9090/rules

**Loki Logs:**
- Via Grafana Explore: http://localhost:3000/explore

**Repositorio:**
- Observability configs: `inventario-retail/observability/`
- Alert rules: `inventario-retail/observability/prometheus/alerts.yml`
- Docker compose: `inventario-retail/observability/docker-compose.observability.yml`

---

**Última actualización:** 4 de octubre de 2025  
**Mantenido por:** DevOps Team - Mini Market Project  
**Versión:** 1.0
