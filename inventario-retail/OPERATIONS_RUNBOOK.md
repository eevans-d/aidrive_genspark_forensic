# 🔧 Operations Runbook - Mini Market Dashboard

## 📋 Tabla de Contenidos

1. [Procedimientos de Emergencia](#procedimientos-de-emergencia)
2. [Playbooks por Incidente](#playbooks-por-incidente)
3. [Escalamiento y Contactos](#escalamiento-y-contactos)
4. [Checklists Operacionales](#checklists-operacionales)
5. [Recuperación de Desastres](#recuperación-de-desastres)

---

## 🚨 Procedimientos de Emergencia

### P1: Dashboard No Responde (Service Down)

**Tiempo de respuesta:** < 5 minutos
**Impacto:** Crítico - Sistema completamente inaccesible

#### Diagnóstico (1-2 minutos)

```bash
# 1. Verificar que endpoint responde
curl -v http://localhost:8080/health

# 2. Si no responde, ver status de contenedores
docker-compose -f docker-compose.production.yml ps

# 3. Ver logs recientes
docker-compose -f docker-compose.production.yml logs --tail=50 dashboard

# 4. Verificar recursos (CPU, memoria, disco)
docker stats dashboard
df -h /
```

#### Acciones Inmediatas (2-3 minutos)

**Opción 1: Reinicio Simple (resolver 70% de los casos)**
```bash
# Reiniciar solo dashboard
docker-compose -f docker-compose.production.yml restart dashboard

# Esperar 10 segundos y verificar
sleep 10
curl http://localhost:8080/health

# Si recupera → Registrar incidente y continuar monitoreando
# Si no → Ir a Opción 2
```

**Opción 2: Reinicio Completo del Stack**
```bash
# Detener todo
docker-compose -f docker-compose.production.yml down

# Esperar 5 segundos
sleep 5

# Reiniciar todo
docker-compose -f docker-compose.production.yml up -d

# Verificar status
sleep 15
docker-compose -f docker-compose.production.yml ps

# Verificar endpoints críticos
curl http://localhost:8080/health
curl http://localhost/api/inventory
```

**Opción 3: Revisar Logs para Errores Críticos**
```bash
# Si servicios están corriendo pero no responden:
docker logs dashboard | grep -i "error\|exception\|fatal" | tail -20

# Buscar problemas de conexión a BD
docker logs dashboard | grep -i "database\|postgresql\|connection" | tail -10

# Buscar problemas de puerto/bind
docker logs dashboard | grep -i "bind\|port\|address already in use" | tail -10
```

#### Escalación (si no se recupera)

- **2 minutos sin respuesta:** Iniciar troubleshooting avanzado (P2)
- **5 minutos sin respuesta:** Contactar on-call engineer (ver sección de contactos)

---

### P2: Base de Datos No Conecta (Database Down)

**Tiempo de respuesta:** < 3 minutos
**Impacto:** Crítico - Pérdida de funcionalidad de datos

#### Diagnóstico

```bash
# 1. Verificar que PostgreSQL está corriendo
docker-compose -f docker-compose.production.yml ps | grep postgres

# 2. Verificar conectividad
docker exec -it inventario_retail_db pg_isready -U postgres

# 3. Ver logs de error
docker logs inventario_retail_db | grep -i "error\|fatal" | tail -20

# 4. Verificar espacio en disco
docker exec inventario_retail_db du -sh /var/lib/postgresql/data

# 5. Verificar puertos
sudo netstat -tulpn | grep 5432
```

#### Acciones Inmediatas

**Paso 1: Reintentar Conexión**
```bash
# Reiniciar PostgreSQL
docker-compose -f docker-compose.production.yml restart postgres

# Esperar a que esté listo
docker exec inventario_retail_db pg_isready -U postgres
# Esperado: "accepting connections"

# Verificar desde dashboard
curl http://localhost:8080/health
```

**Paso 2: Si Sigue Sin Conectar**
```bash
# Verificar integridad de datos
docker exec -it inventario_retail_db psql -U postgres -c "SELECT datname FROM pg_database;"

# Intentar repair (últimas opciones)
docker exec -it inventario_retail_db reindex

# Si la BD está corrupta: ver sección "Recuperación de Desastres"
```

---

### P3: Observability Stack Caído (No Hay Métricas/Alertas)

**Tiempo de respuesta:** < 10 minutos
**Impacto:** Alto - Sin observabilidad, pero servicios siguen funcionando

#### Diagnóstico

```bash
# 1. Verificar stack de observability
cd inventario-retail/observability
docker-compose -f docker-compose.observability.yml ps

# 2. Verificar endpoints
curl http://localhost:9090/-/healthy      # Prometheus
curl http://localhost:3000/api/health     # Grafana
curl http://localhost:3100/ready          # Loki
curl http://localhost:9093/api/v2/status  # Alertmanager

# 3. Ver logs
docker-compose -f docker-compose.observability.yml logs --tail=50
```

#### Acciones Inmediatas

```bash
# Reiniciar stack completo
docker-compose -f docker-compose.observability.yml down
sleep 5
docker-compose -f docker-compose.observability.yml up -d

# Esperar a que levante
sleep 20

# Verificar status
docker-compose -f docker-compose.observability.yml ps

# Verificar datos en Prometheus
curl http://localhost:9090/api/v1/query?query=up
```

---

## 📋 Playbooks por Incidente

### PB1: Tasa de Errores Muy Alta (>5%)

**Síntoma:** Alerta "HighErrorRate" activada

#### Diagnóstico

```bash
# 1. Ver qué endpoints están fallando
curl -s http://localhost:9090/api/v1/query?query='rate(http_requests_total%5B5m%5D)' | jq .

# 2. Ver logs de dashboard
docker logs dashboard | grep -i "error\|exception" | tail -50

# 3. Revisar base de datos
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT COUNT(*) FROM pg_stat_activity WHERE state != 'idle';"

# 4. Revisar conexiones abiertas
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

#### Acciones Correctivas

**Causa 1: Base de Datos Lenta**
```bash
# Analizar queries lentas
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Agregar índices faltantes
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "CREATE INDEX idx_productos_sku ON productos(sku);"

# Vacuum full si hay fragmentación
docker exec -it inventario_retail_db vacuum full;
```

**Causa 2: API Timeout o Sobrecarga**
```bash
# Ver uso de recursos
docker stats dashboard

# Si CPU está al 100%:
# - Revisar si hay queries N+1 en código
# - Aumentar recursos Docker (memory limit)
# - Escalar horizontalmente

# Restart graceful
docker-compose -f docker-compose.production.yml restart dashboard

# Monitorear durante 5 minutos
docker stats dashboard --no-stream=false
```

**Causa 3: Problema de Conectividad**
```bash
# Verificar que servicios pueden comunicarse
docker exec dashboard curl -v http://agente-deposito:8001/health
docker exec dashboard curl -v http://agente-negocio:8002/health
docker exec dashboard curl -v postgres:5432  # Esto fallará pero verifica conectividad

# Ver DNS
docker exec dashboard nslookup postgres
```

#### Escalación

- Si error rate no baja en 5 minutos → Contactar al arquitecto
- Si error rate > 25% → Considerar rollback de última versión

---

### PB2: Latencia Alta (P95 > 300ms)

**Síntoma:** Alerta "HighLatency" activada

#### Diagnóstico

```bash
# 1. Ver latencias actuales
curl -s http://localhost:9090/api/v1/query?query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket%5B5m%5D))' | jq .

# 2. Identificar endpoint más lento
curl -s http://localhost:9090/api/v1/query?query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint=~"%2Fapi%2F.*"}%5B5m%5D)) by (endpoint)' | jq .

# 3. Ver si es I/O o CPU
docker stats dashboard --no-stream

# 4. Ver conexiones a BD
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"
```

#### Acciones Correctivas

**Causa 1: BD Lenta**
```bash
# Analizar plan de ejecución de query lenta
QUERY="SELECT * FROM productos WHERE sku = 'ABC123';"
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c "EXPLAIN ANALYZE $QUERY;"

# Si hay sequential scans sin índice → Agregar índice
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "CREATE INDEX CONCURRENTLY idx_sku ON productos(sku);"
```

**Causa 2: Cache Inefectivo**
```bash
# Ver hit rate de Redis
docker exec redis redis-cli INFO stats | grep keyspace_hits

# Si hit rate < 50%:
# - Revisar TTL de claves
# - Aumentar Redis memory limit
# - Optimizar estrategia de caching

docker exec redis redis-cli CONFIG GET maxmemory
docker exec redis redis-cli DBSIZE
```

**Causa 3: Red Congestionada**
```bash
# Verificar que servicios están en la misma red Docker
docker network inspect inventario-retail_default

# Si hay latencia entre contenedores:
# - Verificar si host tiene problemas de red
# - Ver si Docker está usando overlay drivers lentos
```

---

### PB3: Uso de Memoria Alto (>80%)

**Síntoma:** Alerta "MemoryPressure" activada

#### Diagnóstico

```bash
# 1. Ver uso de memoria actual
docker stats

# 2. Identificar contenedor que consume más
docker stats --no-stream

# 3. Ver límites configurados
docker inspect dashboard | grep -A5 Memory

# 4. Ver si hay memory leaks (aumento gradual)
docker stats dashboard --no-stream=false | tee memory.log
# Observar por 5 minutos
```

#### Acciones Correctivas

**Opción 1: Reiniciar Servicios**
```bash
# Reiniciar dashboard (libera memoria)
docker-compose -f docker-compose.production.yml restart dashboard

# Esperar y verificar
sleep 30
docker stats dashboard --no-stream
```

**Opción 2: Ajustar Límites de Memoria**
```bash
# En docker-compose.production.yml, aumentar limits:
# services:
#   dashboard:
#     deploy:
#       resources:
#         limits:
#           memory: 1G  # Aumentar de 512M a 1G

# Aplicar cambios
docker-compose -f docker-compose.production.yml up -d
```

**Opción 3: Revisar Memory Leaks en Código**
```bash
# Si memoria sigue creciendo después de restart:
# - Revisar logs de aplicación
# - Buscar conexiones no cerradas
# - Revisar caché sin límite de tamaño

docker logs dashboard | grep -i "memory\|leak" | tail -20
```

---

### PB4: Certificados TLS Expirados

**Síntoma:** Errores de certificado en Prometheus → Alertmanager

#### Diagnóstico

```bash
# 1. Ver fecha de expiración
openssl x509 -in inventario-retail/observability/prometheus/tls/prometheus.crt \
  -text -noout | grep "Not After"

# 2. Si están a punto de expirar (< 30 días)
EXPIRY=$(openssl x509 -in inventario-retail/observability/prometheus/tls/prometheus.crt \
  -noout -dates | grep "notAfter" | cut -d= -f2)
echo "Expira en: $EXPIRY"
```

#### Acciones Correctivas

```bash
# 1. Ir al directorio de certificados
cd inventario-retail/observability/prometheus/tls

# 2. Backup de certificados actuales
mkdir backup_$(date +%Y%m%d)
cp ca.* prometheus.* alertmanager.* backup_*/

# 3. Generar nuevos certificados
./generate_certs.sh

# 4. Verificar
openssl x509 -in prometheus.crt -text -noout | grep "Not After"

# 5. Reiniciar servicios
docker-compose -f ../docker-compose.observability.yml restart prometheus alertmanager

# 6. Verificar conectividad TLS
docker exec prometheus curl --cacert /etc/prometheus/tls/ca.crt \
  --cert /etc/prometheus/tls/prometheus.crt \
  --key /etc/prometheus/tls/prometheus.key \
  https://alertmanager:9093/api/v2/status
```

---

### PB5: Alertas de Datos Cifrados Inaccesibles

**Síntoma:** Errores "decrypt_data failed" en logs

#### Diagnóstico

```bash
# 1. Verificar que clave está seteada
echo $DATABASE_ENCRYPTION_KEY

# 2. Verificar que clave es válida (64 caracteres hex)
echo $DATABASE_ENCRYPTION_KEY | wc -c  # Debe ser 65 (64 + newline)

# 3. Intentar descifrar dato
docker exec -it inventario_retail_db psql -U postgres inventario_retail << EOF
SET DATABASE_ENCRYPTION_KEY = '${DATABASE_ENCRYPTION_KEY}';
SELECT decrypt_data(api_key_encrypted, current_setting('DATABASE_ENCRYPTION_KEY'))
FROM system_config LIMIT 1;
EOF
```

#### Acciones Correctivas

**Causa 1: Clave Incorrecta o Cambió**
```bash
# Si la clave fue cambiad y datos están cifrados con antigua:
# → NO hay recuperación posible (por diseño)
# → Contactar arquitecto para evaluación de opciones

# Soluciones últimas:
# 1. Restaurar BD desde backup pre-cifrado
# 2. Usar clave anterior si está documentada
# 3. Regenerar datos si es posible
```

**Causa 2: Clave No Está en Env**
```bash
# Agregar a .env.production
echo "DATABASE_ENCRYPTION_KEY=<clave-correcta>" >> .env.production

# Recargar env (reiniciar servicios)
docker-compose -f docker-compose.production.yml restart dashboard agente-deposito agente-negocio

# Verificar
docker exec dashboard env | grep DATABASE_ENCRYPTION_KEY
```

---

## 📞 Escalamiento y Contactos

### Matriz de Escalamiento

| Severidad | Tiempo Respuesta | Acción | Contacto |
|-----------|------------------|--------|----------|
| P1 (Crítico) | < 5 min | Equipos en standby | On-call Engineer |
| P2 (Alto) | < 15 min | Revisar playbook, escalar si no resuelve | Team Lead |
| P3 (Medio) | < 1 hora | Investigar y documentar | Senior Engineer |
| P4 (Bajo) | < 8 horas | Planificar para siguiente sprint | Backlog |

### On-Call Contacts

```
MODO GUERRA (P1):
- Slack: #minimarket-emergencies
- Engineer On-Call: @semanal-on-call (canal Slack)
- Escalación: Lead Técnico (en contactos organizacionales)

EMERGENCIA FUERA DE HORARIO:
- PagerDuty: https://pagerduty.company.com
- Teléfono de emergencia: +54 9 (ver contactos organizacionales)
```

### Procedimiento de Handoff

```bash
# Al terminar turno on-call:

# 1. Documentar incidentes en Slack
# - Qué pasó
# - Cómo se resolvió
# - Lecciones aprendidas

# 2. Pasar runbooks y contexto
# - Ver últimos logs
# - Avisar de problemas recurrentes

# 3. Verificar que no hay alertas activas
curl http://localhost:9093/api/v2/alerts

# 4. Crear tickets para seguimiento
# - Issues en GitHub si requiere código
# - Tareas de infrastructure si requiere infra
```

---

## ✅ Checklists Operacionales

### Daily Health Check (Realizar cada mañana)

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check ==="
echo ""

# 1. Servicios UP
echo "✓ Servicios principales..."
docker-compose -f docker-compose.production.yml ps | grep -E "(dashboard|agente-deposito|agente-negocio|postgres|redis)"

# 2. Endpoints responden
echo ""
echo "✓ Endpoints..."
curl -s http://localhost:8080/health | jq . && echo "  Dashboard: OK" || echo "  Dashboard: FAIL"
curl -s http://localhost/api/inventory -H "X-API-Key: dev" > /dev/null && echo "  API: OK" || echo "  API: FAIL"

# 3. Base de datos
echo ""
echo "✓ Base de datos..."
docker exec inventario_retail_db pg_isready -U postgres > /dev/null && echo "  PostgreSQL: OK" || echo "  PostgreSQL: FAIL"

# 4. Observability
echo ""
echo "✓ Observability..."
curl -s http://localhost:9090/-/healthy > /dev/null && echo "  Prometheus: OK" || echo "  Prometheus: FAIL"
curl -s http://localhost:3000/api/health > /dev/null && echo "  Grafana: OK" || echo "  Grafana: FAIL"

# 5. Alertas activas
echo ""
echo "✓ Alertas activas..."
ACTIVE_ALERTS=$(curl -s http://localhost:9093/api/v2/alerts | jq length)
echo "  Total: $ACTIVE_ALERTS"

# 6. Espacio en disco
echo ""
echo "✓ Espacio en disco..."
df -h / | tail -1

echo ""
echo "=== Health Check Complete ==="
```

### Pre-Deployment Checklist

- [ ] Todos los tests pasando en CI/CD
- [ ] Load tests con baseline cumplidos
- [ ] Backup de BD realizado
- [ ] Documentación actualizada
- [ ] Cambios de seguridad revisados
- [ ] Variables de entorno verificadas
- [ ] Certificados TLS válidos (> 30 días)
- [ ] Runway de espacio en disco > 20%

---

## 🔄 Recuperación de Desastres

### RTO/RPO Targets

| Escenario | RTO | RPO |
|-----------|-----|-----|
| Pérdida de datos (backup restaurable) | 2 horas | 24 horas |
| Contenedor corrompido | 15 minutos | 0 (sin estado) |
| Servidor entero caído | 4 horas | 24 horas |
| Región/AZ entera (si fuera distribuido) | 1 día | 24 horas |

### Procedimiento de Backup

```bash
#!/bin/bash
# backup_procedure.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting backup: $TIMESTAMP"

# 1. Backup de BD
docker-compose -f docker-compose.production.yml exec -T postgres \
  pg_dump -U postgres inventario_retail > \
  $BACKUP_DIR/inventario_retail_$TIMESTAMP.sql

# 2. Backup de configs
tar czf $BACKUP_DIR/configs_$TIMESTAMP.tar.gz \
  .env.production \
  observability/prometheus/tls/ \
  observability/prometheus/prometheus.yml \
  observability/alertmanager/alertmanager.yml

# 3. Backup de volúmenes
docker run --rm \
  -v inventario_retail_postgres_data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  busybox tar czf /backup/postgres_data_$TIMESTAMP.tar.gz /data

# 4. Copiar a storage remoto
aws s3 cp $BACKUP_DIR/ s3://minimarket-backups/$TIMESTAMP/ --recursive

echo "Backup complete: $TIMESTAMP"
```

### Procedimiento de Restore

```bash
#!/bin/bash
# restore_procedure.sh

BACKUP_FILE=$1  # Pasar como: ./backups/inventario_retail_20231016_120000.sql

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

echo "WARNING: Este procedimiento restaurará la BD desde backup"
echo "Archivo: $BACKUP_FILE"
read -p "¿Continuar? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelado"
  exit 1
fi

# 1. Detener servicios que acceden BD
docker-compose -f docker-compose.production.yml stop dashboard agente-deposito agente-negocio

# 2. Dropear BD actual (PUNTO DE NO RETORNO)
docker exec -it inventario_retail_db psql -U postgres -c \
  "DROP DATABASE inventario_retail;"

# 3. Crear BD vacía
docker exec -it inventario_retail_db psql -U postgres -c \
  "CREATE DATABASE inventario_retail;"

# 4. Restaurar desde backup
docker exec -i inventario_retail_db psql -U postgres inventario_retail < $BACKUP_FILE

# 5. Verificar restauración
docker exec -it inventario_retail_db psql -U postgres inventario_retail -c \
  "SELECT COUNT(*) FROM productos;"

# 6. Reiniciar servicios
docker-compose -f docker-compose.production.yml up -d

echo "Restore complete"
```

---

## 📝 Documentación Adicional

### Guías Relacionadas

- **Troubleshooting Específico:** Ver `inventario-retail/observability/runbooks/`
- **Respuesta a Alertas:** Ver `RESPONDING_TO_ALERTS.md`
- **TLS Setup Completo:** Ver `security/TLS_SETUP.md`
- **Data Encryption:** Ver `security/DATA_ENCRYPTION.md`
- **Load Testing:** Ver `scripts/load_testing/LOAD_TESTING.md`

### Logs Importantes

```bash
# Logs de aplicación
docker logs dashboard -f --tail=100

# Logs de base de datos
docker logs inventario_retail_db -f --tail=100

# Logs de Prometheus/Alertmanager
docker logs prometheus -f --tail=100
docker logs alertmanager -f --tail=100

# Logs centralizados (si hay ELK/Loki)
# Ver en Grafana → Explore → Loki
```

---

**Última actualización:** 16 de octubre de 2025  
**Versión:** 1.0.0 (ETAPA 3)  
**Mantenedor:** Equipo de Operaciones  
**Contacto:** #minimarket-ops en Slack
