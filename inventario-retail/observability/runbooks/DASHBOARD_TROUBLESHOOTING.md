# Runbook: Dashboard Troubleshooting Guide

**Última actualización:** 4 de octubre de 2025  
**Versión:** 1.0  
**Autor:** DevOps Team - ETAPA 3 Phase 1

---

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [Problemas Comunes](#problemas-comunes)
  - [Dashboard no muestra datos](#dashboard-no-muestra-datos)
  - [Queries muy lentas](#queries-muy-lentas)
  - [Grafana no carga](#grafana-no-carga)
  - [Datasource no conecta](#datasource-no-conecta)
  - [Panels muestran "N/A" o vacíos](#panels-muestran-na-o-vacíos)
  - [Métricas desactualizadas](#métricas-desactualizadas)
- [Optimización de Queries](#optimización-de-queries)
- [Troubleshooting Avanzado](#troubleshooting-avanzado)
- [Mantenimiento Preventivo](#mantenimiento-preventivo)
- [Referencias](#referencias)

---

## Introducción

Esta guía cubre los problemas más comunes con los dashboards de Grafana y sus soluciones. Los 4 dashboards implementados son:

1. **System Overview** - Monitoreo general de salud de servicios
2. **Business KPIs** - Métricas de negocio
3. **Performance** - Recursos de infraestructura
4. **ML Service Monitor** - Métricas específicas de ML/OCR

**Acceso rápido:**
- Grafana UI: http://localhost:3000
- Prometheus UI: http://localhost:9090
- Loki UI: http://localhost:3100 (vía Grafana Explore)

**Credenciales por defecto:**
- Usuario: `admin`
- Password: `admin` (cambiar en primer acceso)

---

## Problemas Comunes

### Dashboard no muestra datos

**Síntomas:**
- Todos los panels muestran "No data"
- Gráficos vacíos
- Mensaje "No data points" en tooltips

#### Diagnóstico Paso a Paso

**1. Verificar que Prometheus está UP:**
```bash
# Verificar contenedor Prometheus
docker ps | grep prometheus

# Verificar logs
docker logs prometheus | tail -20

# Probar API de Prometheus
curl http://localhost:9090/-/healthy
# Esperado: HTTP 200 "Prometheus is Healthy."
```

**2. Verificar que servicios tienen métricas:**
```bash
# Probar endpoints /metrics de cada servicio
curl http://localhost:8001/metrics | head -20  # agente_deposito
curl http://localhost:8002/metrics | head -20  # agente_negocio
curl http://localhost:8003/metrics | head -20  # ml_service
curl http://localhost:8080/metrics | head -20  # dashboard

# Cada uno debe retornar métricas en formato Prometheus
# Ejemplo esperado:
# # HELP http_requests_total Total HTTP requests
# # TYPE http_requests_total counter
# http_requests_total{job="agente_deposito"} 1234
```

**3. Verificar targets en Prometheus:**
```bash
# Abrir http://localhost:9090/targets
# Todos los targets deben estar en verde (UP)
# Si aparecen en rojo (DOWN), ver causas abajo
```

**4. Verificar rango de tiempo en Grafana:**
- En la esquina superior derecha del dashboard
- Verificar que el rango seleccionado es apropiado (ej: "Last 6 hours")
- Si el sistema es nuevo, puede no haber datos históricos

#### Resoluciones por Causa

**Causa 1: Prometheus no puede scrape los servicios**

Síntoma en `/targets`: Targets en rojo con error "context deadline exceeded" o "connection refused"

```bash
# Verificar conectividad de red Docker
docker network ls
docker network inspect <network_name>

# Verificar que servicios están en la misma red
docker inspect agente-deposito | grep NetworkMode
docker inspect prometheus | grep NetworkMode

# Si están en redes diferentes, agregar prometheus a la red correcta
docker network connect <network_name> prometheus

# Reiniciar Prometheus
docker-compose -f docker-compose.observability.yml restart prometheus
```

**Causa 2: Configuración incorrecta en prometheus.yml**

```bash
# Verificar configuración
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Debe contener scrape_configs para los 4 servicios:
# - job_name: 'agente_deposito'
#   static_configs:
#     - targets: ['agente-deposito:8001']

# Si falta alguno, editar el archivo y recargar config
docker exec prometheus kill -HUP 1

# O reiniciar Prometheus
docker-compose -f docker-compose.observability.yml restart prometheus
```

**Causa 3: Servicios no están exponiendo métricas**

```bash
# Si curl a /metrics retorna 404, el servicio no tiene el endpoint
# Verificar que el código incluye prometheus_client

# Ejemplo para agente_deposito:
docker exec agente-deposito python -c "import prometheus_client; print('OK')"

# Si falta la biblioteca, agregarla a requirements.txt y rebuild
pip install prometheus-client

# Verificar que el endpoint está registrado en main.py
docker exec agente-deposito grep -n "/metrics" /app/main.py
```

**Causa 4: Firewall o puerto bloqueado**

```bash
# Verificar que puertos están abiertos
sudo iptables -L -n | grep -E "(8001|8002|8003|8080|9090)"

# Verificar con telnet
telnet localhost 8001
telnet localhost 9090

# Si falla, abrir puertos en firewall
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 8003/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 9090/tcp
```

**Causa 5: Grafana datasource mal configurado**

```bash
# En Grafana UI, ir a Configuration > Data Sources > Prometheus
# URL debe ser: http://prometheus:9090 (nombre del contenedor)
# Si es http://localhost:9090, cambiar a nombre del contenedor

# Hacer click en "Save & Test"
# Debe mostrar "Data source is working"

# Si falla, verificar que Grafana está en la misma red Docker que Prometheus
docker network inspect <network_name> | grep -E "(grafana|prometheus)"
```

---

### Queries muy lentas

**Síntomas:**
- Dashboards tardan >10 segundos en cargar
- Mensaje "Query timeout" en panels
- Grafana se congela al navegar entre dashboards

#### Diagnóstico

**1. Verificar carga de Prometheus:**
```bash
# Ver métricas de performance de Prometheus
curl http://localhost:9090/metrics | grep prometheus_engine

# Métricas importantes:
# - prometheus_engine_queries (queries activas)
# - prometheus_engine_query_duration_seconds (latencia)
# - prometheus_tsdb_head_samples (muestras en memoria)
```

**2. Identificar queries lentas:**
```bash
# En Grafana, abrir un panel lento
# Click en título del panel > Edit
# Click en "Query Inspector" (ícono de lupa)
# Ver "Request duration" - si es >5s, la query es lenta
```

**3. Ejecutar query directamente en Prometheus:**
```bash
# Copiar la query PromQL del panel
# Ir a http://localhost:9090/graph
# Pegar query y ejecutar
# Verificar tiempo de ejecución en la UI
```

#### Resoluciones

**Optimización 1: Reducir cardinality**

Queries con alta cardinality (muchas series) son lentas. Ejemplo problemático:
```promql
# MAL - Alta cardinality (una serie por cada combinación de labels)
rate(http_requests_total[5m])

# BIEN - Agregado, menor cardinality
sum(rate(http_requests_total[5m])) by (job)
```

**Cómo aplicar:**
```bash
# En Grafana, editar panel con query lenta
# Agregar aggregation a la query:
# - sum(...) by (job)
# - avg(...) by (instance)
# - max(...) by (service)

# Guardar y verificar mejora de performance
```

**Optimización 2: Reducir rango de tiempo**

```bash
# En la query PromQL, usar rangos más cortos:
# Antes: rate(metric[1h])
# Después: rate(metric[5m])

# Esto reduce el número de samples a procesar
```

**Optimización 3: Aumentar recursos de Prometheus**

```yaml
# Editar docker-compose.observability.yml
prometheus:
  deploy:
    resources:
      limits:
        memory: 2G  # Aumentar de 1G a 2G
        cpus: '2.0'  # Aumentar de 1.0 a 2.0

# Aplicar cambios
docker-compose -f docker-compose.observability.yml up -d prometheus
```

**Optimización 4: Configurar retention de datos**

```bash
# Editar prometheus.yml, agregar flag de retention
docker run -d \
  --name prometheus \
  -v prometheus-data:/prometheus \
  prom/prometheus:latest \
  --storage.tsdb.retention.time=15d  # Reducir de 30d a 15d si es necesario

# Esto reduce el tamaño de la base de datos
```

**Optimización 5: Pre-agregación con recording rules**

Si una query es muy compleja y se usa frecuentemente, crear recording rule:

```yaml
# Editar prometheus/alerts.yml, agregar sección de recording rules
groups:
  - name: recording_rules
    interval: 30s
    rules:
      # Pre-calcular P95 latency cada 30s
      - record: http_request_duration_p95
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

Luego en Grafana, usar la métrica pre-calculada:
```promql
# En vez de:
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Usar:
http_request_duration_p95
```

---

### Grafana no carga

**Síntomas:**
- http://localhost:3000 no responde
- Error "Connection refused" o "ERR_CONNECTION_REFUSED"
- Página en blanco

#### Diagnóstico

**1. Verificar contenedor Grafana:**
```bash
docker ps -a | grep grafana

# Si está "Exited" o no aparece, está down
docker logs grafana | tail -50
```

**2. Verificar puerto:**
```bash
netstat -tlnp | grep 3000

# Si no aparece, el puerto no está escuchando
```

**3. Verificar permisos de volúmenes:**
```bash
ls -la /var/lib/docker/volumes/ | grep grafana

# Verificar ownership
docker exec grafana ls -la /var/lib/grafana
```

#### Resoluciones

**Causa 1: Contenedor crasheado**
```bash
# Ver error en logs
docker logs grafana | grep -i "error\|fatal"

# Reiniciar Grafana
docker-compose -f docker-compose.observability.yml restart grafana

# Si falla, ver causa específica en logs
```

**Causa 2: Puerto ocupado**
```bash
# Verificar qué proceso usa puerto 3000
sudo lsof -i :3000

# Detener proceso conflictivo o cambiar puerto de Grafana
# Editar docker-compose.observability.yml:
grafana:
  ports:
    - "3001:3000"  # Cambiar puerto externo

docker-compose -f docker-compose.observability.yml up -d grafana
```

**Causa 3: Permisos de volumen incorrectos**
```bash
# Grafana corre como usuario ID 472
# Verificar ownership del volumen
docker volume inspect grafana-data

# Arreglar permisos
docker run --rm -v grafana-data:/data alpine chown -R 472:472 /data

# Reiniciar Grafana
docker-compose -f docker-compose.observability.yml restart grafana
```

**Causa 4: Configuración corrupta**
```bash
# Renombrar configuración actual
docker exec grafana mv /etc/grafana/grafana.ini /etc/grafana/grafana.ini.bak

# Recrear con defaults
docker-compose -f docker-compose.observability.yml up -d --force-recreate grafana
```

---

### Datasource no conecta

**Síntomas:**
- Al hacer "Save & Test" en datasource, aparece error
- Mensaje "HTTP Error Bad Gateway" o "Timeout"
- Dashboards muestran "Datasource not found"

#### Diagnóstico

**1. Verificar configuración de datasource:**
```bash
# En Grafana UI: Configuration > Data Sources > Prometheus
# Verificar URL: debe ser http://prometheus:9090 (nombre del container, no localhost)

# Verificar Access: debe ser "Server (default)" no "Browser"
```

**2. Verificar conectividad desde Grafana:**
```bash
# Entrar al contenedor de Grafana
docker exec -it grafana sh

# Probar conectividad a Prometheus
wget -O- http://prometheus:9090/-/healthy

# Si falla, hay problema de red
exit
```

**3. Verificar red Docker:**
```bash
docker network inspect <network_name> | grep -A 10 "grafana"
docker network inspect <network_name> | grep -A 10 "prometheus"

# Ambos deben estar en la misma red
```

#### Resoluciones

**Causa 1: URL incorrecta en datasource**
```bash
# En Grafana UI: Configuration > Data Sources > Prometheus
# Cambiar URL:
# ❌ http://localhost:9090
# ✅ http://prometheus:9090

# Usar el nombre del contenedor, no localhost ni IP

# Save & Test
```

**Causa 2: Contenedores en diferentes redes**
```bash
# Agregar Grafana a la red de Prometheus
docker network connect <network_name> grafana

# O viceversa
docker network connect <network_name> prometheus

# Reiniciar ambos contenedores
docker-compose -f docker-compose.observability.yml restart grafana prometheus
```

**Causa 3: Provisioning no aplicado**
```bash
# Verificar que datasource.yml existe
docker exec grafana cat /etc/grafana/provisioning/datasources/datasource.yml

# Si falta, copiar desde repo
docker cp inventario-retail/observability/grafana/provisioning/datasources/datasource.yml grafana:/etc/grafana/provisioning/datasources/

# Reiniciar Grafana
docker-compose -f docker-compose.observability.yml restart grafana
```

**Causa 4: Prometheus no responde**
```bash
# Verificar que Prometheus está UP y responde
curl http://localhost:9090/-/healthy

# Si falla, resolver problema de Prometheus primero
# (ver sección "Prometheus no responde" abajo)
```

---

### Panels muestran "N/A" o vacíos

**Síntomas:**
- Panel muestra "N/A" en vez de valor numérico
- Gauge o Stat panel vacío
- Tabla sin filas

#### Diagnóstico

**1. Verificar query retorna datos:**
```bash
# En Grafana, editar panel
# Click en "Query Inspector"
# Ver "Data" tab - debe mostrar series con valores

# Si "Data" está vacío, la query no retorna datos
```

**2. Ejecutar query en Prometheus UI:**
```bash
# Copiar query PromQL del panel
# Ir a http://localhost:9090/graph
# Pegar y ejecutar
# Verificar que retorna valores
```

**3. Verificar rango de tiempo:**
```bash
# En dashboard, verificar time range (esquina superior derecha)
# Cambiar a "Last 24 hours" para ver si hay datos históricos

# Si es sistema nuevo (<6 horas de antigüedad), no habrá datos históricos
```

#### Resoluciones

**Causa 1: Métrica no existe aún**
```bash
# Algunas métricas solo se exponen después de eventos:
# - ml_predictions_total: Solo después de primera predicción
# - http_errors_total: Solo después de primer error
# - ocr_timeout_events_total: Solo después de primer timeout

# Solución: Esperar a que ocurra el evento, o triggerearlo manualmente
curl http://localhost:8003/api/predict -d '{"data": "test"}'

# La métrica aparecerá en Prometheus después del primer scrape (15-30s)
```

**Causa 2: Query incorrecta**
```promql
# Revisar sintaxis de la query
# Errores comunes:

# ❌ rate(http_requests_total)  # Falta rango
# ✅ rate(http_requests_total[5m])

# ❌ histogram_quantile(0.95, http_request_duration_seconds_bucket)  # Falta rate()
# ✅ histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# ❌ sum(rate(metric[5m]) by (job))  # Paréntesis mal colocado
# ✅ sum(rate(metric[5m])) by (job)
```

**Causa 3: Aggregation elimina todos los datos**
```promql
# Si usas aggregation con label que no existe:
sum(rate(http_requests_total[5m])) by (nonexistent_label)
# Retorna vacío

# Verificar labels disponibles:
# En Prometheus UI: http_requests_total
# Ver qué labels existen realmente

# Usar labels correctos:
sum(rate(http_requests_total[5m])) by (job, status)
```

**Causa 4: Panel visualization mal configurado**
```bash
# En Grafana, editar panel
# Ir a tab "Panel options"
# Verificar:
# - "Value" field mapping correcto
# - "Calculation" apropiado (Last, Mean, Sum, etc.)
# - "Unit" correcto (si está en "short" pero son bytes, cambiar a "bytes")

# Para Gauge panels:
# - Verificar "Min" y "Max" no están invertidos
# - Verificar thresholds configurados

# Para Stat panels:
# - Verificar "Reduce" function es apropiada (Last not null, Mean, etc.)
```

---

### Métricas desactualizadas

**Síntomas:**
- Valores en dashboard no cambian
- Última actualización es antigua (>5 minutos)
- Gráficos "congelados"

#### Diagnóstico

**1. Verificar refresh interval:**
```bash
# En dashboard, ver esquina superior derecha
# Debe mostrar auto-refresh activo (ej: "Refreshing every 30s")

# Si muestra ícono de pause, el auto-refresh está detenido
```

**2. Verificar scrape interval de Prometheus:**
```bash
# Ver configuración
docker exec prometheus cat /etc/prometheus/prometheus.yml | grep scrape_interval

# Debe ser 15s o 30s
# Si es muy alto (ej: 5m), las métricas se actualizan lentamente
```

**3. Verificar última vez que Prometheus scrapeó:**
```bash
# Ir a http://localhost:9090/targets
# Ver columna "Last Scrape" - debe ser <1 minuto

# Si es >5 minutos, Prometheus no está scraping
```

#### Resoluciones

**Causa 1: Auto-refresh desactivado**
```bash
# En dashboard Grafana, esquina superior derecha
# Click en dropdown de refresh
# Seleccionar "30s" o "1m"
# El dashboard comenzará a actualizarse automáticamente
```

**Causa 2: Prometheus no está scraping**
```bash
# Ver logs de Prometheus
docker logs prometheus | grep -i "scrape\|error"

# Si aparece error de conectividad, resolver problema de red
# (ver sección "Dashboard no muestra datos")

# Reiniciar Prometheus
docker-compose -f docker-compose.observability.yml restart prometheus
```

**Causa 3: Cache agresivo en browser**
```bash
# Hacer hard refresh en browser:
# - Chrome/Firefox: Ctrl+Shift+R (Linux/Windows) o Cmd+Shift+R (Mac)
# - O abrir DevTools (F12) > Network tab > Disable cache

# Recargar dashboard
```

**Causa 4: Query con función de agregación incorrecta**
```promql
# Si usas rate() sin by(), puede dar valores extraños:
# ❌ rate(http_requests_total[1h])  # Promedio de última hora, cambia lentamente
# ✅ rate(http_requests_total[5m])  # Promedio de últimos 5 min, más responsivo

# En dashboard, editar queries para usar rangos más cortos
```

---

## Optimización de Queries

### Mejores Prácticas

**1. Usar rangos apropiados:**
```promql
# Para dashboards en tiempo real: 5m
rate(metric[5m])

# Para análisis de tendencias: 1h
rate(metric[1h])

# Para alertas: alineado con "for" del alert
rate(metric[5m])  # Si alerta es "for: 5m"
```

**2. Agregar siempre con by():**
```promql
# ❌ Sin agregación: alta cardinality
rate(http_requests_total[5m])

# ✅ Con agregación: baja cardinality
sum(rate(http_requests_total[5m])) by (job)
```

**3. Evitar regex innecesarios:**
```promql
# ❌ Regex cuando no es necesario
rate(http_requests_total{job=~"agente_.*"}[5m])

# ✅ Label exacto cuando es posible
rate(http_requests_total{job="agente_deposito"}[5m])
```

**4. Usar recording rules para queries complejas:**
```yaml
# En prometheus/alerts.yml
- record: http_request_duration_p95
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Luego en dashboard usar:
http_request_duration_p95
```

**5. Limitar series retornadas:**
```promql
# ❌ Retorna todas las series (puede ser miles)
http_requests_total

# ✅ Filtrar a servicios relevantes
http_requests_total{job=~"agente_deposito|agente_negocio"}

# ✅ O usar topk para limitar
topk(10, rate(http_requests_total[5m]))
```

### Queries de Ejemplo Optimizadas

**Latencia P95 (optimizada):**
```promql
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)
) * 1000
```

**Tasa de errores (optimizada):**
```promql
100 * (
  sum(rate(http_errors_total[5m])) by (job)
  /
  sum(rate(http_requests_total[5m])) by (job)
)
```

**Uso de CPU (optimizada):**
```promql
100 * (
  rate(container_cpu_usage_seconds_total{name=~".*agente.*"}[5m])
  /
  container_spec_cpu_quota{name=~".*agente.*"}
)
```

**Cache hit rate (optimizada):**
```promql
100 * (
  rate(redis_keyspace_hits_total[5m])
  /
  (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
)
```

---

## Troubleshooting Avanzado

### Prometheus no responde

**Síntomas:**
- http://localhost:9090 timeout
- Todos los dashboards sin datos
- Target page no carga

**Diagnóstico:**
```bash
# Verificar contenedor
docker ps -a | grep prometheus

# Ver logs
docker logs prometheus | tail -100

# Ver recursos
docker stats prometheus --no-stream
```

**Resoluciones:**

**Crash por falta de memoria:**
```bash
# Ver en logs: "out of memory" o "SIGKILL"
docker logs prometheus | grep -i "memory\|sigkill"

# Aumentar límite de memoria
# Editar docker-compose.observability.yml:
prometheus:
  deploy:
    resources:
      limits:
        memory: 2G

docker-compose -f docker-compose.observability.yml up -d prometheus
```

**Base de datos corrupta:**
```bash
# Ver en logs: "corruption" o "block corrupted"
docker logs prometheus | grep -i "corrupt"

# Detener Prometheus
docker-compose -f docker-compose.observability.yml stop prometheus

# Hacer backup del volumen
docker run --rm -v prometheus-data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Eliminar data corrupta
docker volume rm prometheus-data

# Recrear volumen y reiniciar
docker volume create prometheus-data
docker-compose -f docker-compose.observability.yml up -d prometheus
```

**Configuración inválida:**
```bash
# Ver en logs: "error loading config"
docker logs prometheus | grep -i "config"

# Validar prometheus.yml
docker run --rm -v $(pwd)/inventario-retail/observability/prometheus:/etc/prometheus prom/prometheus:latest \
  promtool check config /etc/prometheus/prometheus.yml

# Si tiene errores, corregir y reiniciar
docker-compose -f docker-compose.observability.yml restart prometheus
```

---

### Loki logs no aparecen en Grafana

**Síntomas:**
- Explore > Loki no muestra logs
- Query retorna "No logs found"

**Diagnóstico:**
```bash
# Verificar Loki está UP
docker ps | grep loki
curl http://localhost:3100/ready

# Verificar Promtail está enviando logs
docker logs promtail | grep -i "sent\|push"

# Verificar datasource Loki en Grafana
# Configuration > Data Sources > Loki
# URL debe ser: http://loki:3100
```

**Resoluciones:**

**Promtail no recolecta logs:**
```bash
# Verificar config de Promtail
docker exec promtail cat /etc/promtail/config.yml

# Debe tener scrape_configs para Docker logs
# Ver inventario-retail/observability/promtail/config.yml

# Reiniciar Promtail
docker-compose -f docker-compose.observability.yml restart promtail
```

**Loki datasource mal configurado:**
```bash
# En Grafana: Configuration > Data Sources > Loki
# URL: http://loki:3100 (nombre del contenedor)
# Access: Server (default)

# Derived fields para correlacionar con traces (opcional):
# - Name: traceID
# - Regex: "trace_id":"([^"]+)"
# - URL: ${__value.raw}

# Save & Test
```

---

### Alertas no se envían a Slack

**Síntomas:**
- Alertas firing en Prometheus pero no llegan a Slack
- Alertmanager muestra alertas pero sin notificaciones

**Diagnóstico:**
```bash
# Verificar Alertmanager está UP
docker ps | grep alertmanager
curl http://localhost:9093/-/healthy

# Ver alertas activas
curl http://localhost:9093/api/v2/alerts

# Ver logs de Alertmanager
docker logs alertmanager | grep -i "slack\|error\|notification"
```

**Resoluciones:**

**Webhook URL incorrecta:**
```bash
# Editar alertmanager/alertmanager.yml
# Verificar slack_api_url es correcto:
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#minimarket-alerts'

# Reiniciar Alertmanager
docker-compose -f docker-compose.observability.yml restart alertmanager
```

**Alerta no matchea route:**
```bash
# Ver configuración de routes en alertmanager.yml
# Verificar que labels de alerta matchean con routes

# Ejemplo: si alerta tiene label severity=critical
# Route debe tener:
routes:
  - receiver: 'slack'
    match:
      severity: critical

# Reiniciar Alertmanager después de cambios
```

**Test manual de notificación:**
```bash
# Enviar alerta test a Alertmanager
curl -XPOST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Test alert for troubleshooting"
    }
  }
]'

# Verificar en Slack si llega notificación
# Ver logs de Alertmanager para errores
docker logs alertmanager | tail -20
```

---

## Mantenimiento Preventivo

### Tareas Diarias

**1. Verificar salud de stack de observability:**
```bash
# Script automatizado
docker ps --filter name=prometheus --filter name=grafana --filter name=loki --format "{{.Names}}: {{.Status}}"

# Esperado: todos "Up" y healthy
```

**2. Revisar espacio en disco:**
```bash
du -sh /var/lib/docker/volumes/prometheus-data
du -sh /var/lib/docker/volumes/loki-data
du -sh /var/lib/docker/volumes/grafana-data

# Si alguno >50GB, considerar aumentar retention
```

### Tareas Semanales

**1. Backup de configuraciones:**
```bash
# Backup de dashboards
docker exec grafana tar czf /tmp/grafana-dashboards.tar.gz /etc/grafana/provisioning/dashboards
docker cp grafana:/tmp/grafana-dashboards.tar.gz ./backups/

# Backup de Prometheus config
docker exec prometheus tar czf /tmp/prometheus-config.tar.gz /etc/prometheus
docker cp prometheus:/tmp/prometheus-config.tar.gz ./backups/

# Subir a repositorio Git
git add backups/
git commit -m "backup: weekly observability configs"
git push
```

**2. Revisar queries lentas:**
```bash
# Top 10 queries más lentas en Prometheus
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=topk(10, prometheus_engine_query_duration_seconds{quantile="0.9"})'

# Identificar y optimizar (ver sección Optimización de Queries)
```

**3. Limpiar métricas no usadas:**
```bash
# Listar todas las métricas activas
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data[]'

# Identificar métricas que no se usan en dashboards ni alertas
# Eliminar del código de servicios para reducir cardinality
```

### Tareas Mensuales

**1. Revisar y actualizar dashboards:**
```bash
# Revisar dashboards con métricas obsoletas
# Agregar nuevos panels según necesidades del negocio
# Eliminar panels que nadie usa
```

**2. Tune Prometheus retention:**
```bash
# Analizar crecimiento de data
docker exec prometheus du -sh /prometheus

# Ajustar retention según espacio disponible
# Editar prometheus flags en docker-compose.yml:
command:
  - '--storage.tsdb.retention.time=30d'  # Ajustar según necesidad
```

**3. Actualizar runbooks:**
```bash
# Revisar este documento y RESPONDING_TO_ALERTS.md
# Agregar nuevos problemas encontrados
# Actualizar procedimientos según cambios en sistema
```

---

## Referencias

**Documentación de Grafana:**
- [Query Troubleshooting](https://grafana.com/docs/grafana/latest/troubleshooting/query-troubleshooting/)
- [Panel configuration](https://grafana.com/docs/grafana/latest/panels/)
- [Provisioning dashboards](https://grafana.com/docs/grafana/latest/administration/provisioning/)

**Documentación de Prometheus:**
- [Query basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Query functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Troubleshooting](https://prometheus.io/docs/prometheus/latest/troubleshooting/)

**Documentación de Loki:**
- [LogQL query language](https://grafana.com/docs/loki/latest/logql/)
- [Troubleshooting](https://grafana.com/docs/loki/latest/operations/troubleshooting/)

**Documentación interna:**
- `RESPONDING_TO_ALERTS.md` - Runbook de respuesta a alertas
- `DEPLOYMENT_GUIDE.md` - Guía de deployment (incluye sección de observability)
- Dashboards: `inventario-retail/observability/grafana/dashboards/*.json`
- Prometheus config: `inventario-retail/observability/prometheus/prometheus.yml`
- Alertas: `inventario-retail/observability/prometheus/alerts.yml`

**Herramientas útiles:**
- [Prometheus query visualizer](https://www.percona.com/blog/2020/12/23/using-the-prometheus-query-visualizer/)
- [PromQL cheat sheet](https://promlabs.com/promql-cheat-sheet/)
- [Grafana dashboard best practices](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)

---

**Última actualización:** 4 de octubre de 2025  
**Mantenido por:** DevOps Team - Mini Market Project  
**Versión:** 1.0  
**Feedback:** Reportar problemas o mejoras en #devops-feedback (Slack)
