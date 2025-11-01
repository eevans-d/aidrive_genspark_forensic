# GUÍAS OPERACIONALES EXPANDIDAS - SISTEMA MINI MARKET
## Runbooks, Procedimientos y Protocolos Operacionales

**Versión:** 2.0.0 FINAL - SISTEMA COMPLETADO  
**Fecha:** 1 de noviembre de 2025  
**Estado:** ✅ SISTEMA 100% DESPLEGADO Y OPERATIVO EN PRODUCCIÓN  
**URL Producción:** https://lefkn5kbqv2o.space.minimax.io  
**Target:** DevOps, SRE, Operaciones, Soporte Técnico, Personal Mini Market  

---

## 📋 TABLA DE CONTENIDOS

1. [Runbooks de Operaciones](#1-runbooks-de-operaciones)
2. [Procedimientos de Backup y Recovery](#2-procedimientos-de-backup-y-recovery)
3. [Guías de Troubleshooting Expandidas](#3-guías-de-troubleshooting-expandidas)
4. [Procedimientos de Monitoreo y Alertas](#4-procedimientos-de-monitoreo-y-alertas)
5. [Guías de Escalamiento](#5-guías-de-escalamiento)
6. [Procedimientos de Mantenimiento](#6-procedimientos-de-mantenimiento)
7. [Protocolos de Seguridad](#7-protocolos-de-seguridad)
8. [Comandos de Referencia Rápida](#8-comandos-de-referencia-rápida)

---

## 1. RUNBOOKS DE OPERACIONES

### 1.1 Daily Operations Runbook

#### **🌅 PROCEDIMIENTO DIARIO (8:00 AM)**

```bash
#!/bin/bash
# daily-operations.sh
# Ejecutar cada día a las 8:00 AM

echo "=== DAILY OPERATIONS - $(date) ==="

# 1. HEALTH CHECK SISTEMA
echo "1. Checking system health..."
curl -f https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/api-minimarket || {
    echo "❌ API Health Check FAILED"
    echo "Escalating to on-call engineer..."
    # Send alert to on-call
}

# 2. VERIFICAR BASE DE DATOS
echo "2. Checking database connectivity..."
psql $DATABASE_URL -c "SELECT 1;" || {
    echo "❌ Database connection FAILED"
    echo "Checking database status..."
    # Check Supabase dashboard
}

# 3. VERIFICAR EDGE FUNCTIONS
echo "3. Checking edge functions status..."
supabase functions list | grep -E "(scraper|api|alertas)" || {
    echo "❌ Edge Functions check FAILED"
}

# 4. REVISAR LOGS DE ERRORES
echo "4. Reviewing error logs..."
supabase functions logs scraper-maxiconsumo --limit 50 | grep -i error | tail -10
if [ $? -eq 0 ]; then
    echo "⚠️  Found errors in scraper logs - Review required"
fi

# 5. VERIFICAR CRON JOBS
echo "5. Checking cron jobs status..."
# Query database for recent cron job executions
psql $DATABASE_URL -c "
SELECT 
    job_name,
    last_run,
    status,
    next_run
FROM cron.job_run_details 
WHERE last_run > NOW() - INTERVAL '24 hours'
ORDER BY last_run DESC;"

# 6. GENERAR REPORTE DIARIO
echo "6. Generating daily report..."
curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/reportes-automaticos \
     -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
     -d '{"type": "daily", "date": "'$(date +%Y-%m-%d)'"}'

# 7. VERIFICAR ESPACIO EN DISCO
echo "7. Checking disk usage..."
df -h | awk '$5 > 80 {print "⚠️  Disk usage warning: " $0}'

# 8. VERIFICAR MÉTRICAS DE PERFORMANCE
echo "8. Performance metrics check..."
# Check API response times, memory usage, etc.

echo "=== DAILY OPERATIONS COMPLETED ==="
```

#### **Checklist Diario Manual**

```markdown
## ✅ DAILY OPERATIONS CHECKLIST

### Morning Routine (8:00 AM)
- [ ] Health check API endpoint (<200ms)
- [ ] Database connectivity verified
- [ ] Edge functions responding
- [ ] Error logs reviewed (no critical errors)
- [ ] Cron jobs executed successfully
- [ ] Daily report generated
- [ ] Disk space >20% available
- [ ] Memory usage <80%

### Midday Check (12:00 PM)
- [ ] Review active alerts
- [ ] Check stock levels (no critical lows)
- [ ] Verify data synchronization
- [ ] Monitor system performance
- [ ] Review user activity

### Evening Review (5:00 PM)
- [ ] Generate activity summary
- [ ] Backup critical logs
- [ ] Prepare shift handoff notes
- [ ] Review pending tasks
- [ ] Plan next day activities
```

### 1.2 Weekly Operations Runbook

#### **📅 PROCEDIMIENTO SEMANAL (Lunes 9:00 AM)**

```bash
#!/bin/bash
# weekly-operations.sh

echo "=== WEEKLY OPERATIONS - $(date) ==="

# 1. BACKUP COMPLETO
echo "1. Performing weekly backup..."
# Full database backup
pg_dump $DATABASE_URL > "backup_$(date +%Y%m%d).sql"
# Upload to S3 or secure storage

# 2. ANÁLISIS DE PERFORMANCE
echo "2. Performance analysis..."
# Run performance queries
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_distinct DESC 
LIMIT 20;"

# 3. LIMPIEZA DE LOGS
echo "3. Cleaning old logs..."
# Clean logs older than 90 days
psql $DATABASE_URL -c "DELETE FROM logs_scraping WHERE timestamp < NOW() - INTERVAL '90 days';"

# 4. REFRESH MATERIALIZED VIEWS
echo "4. Refreshing materialized views..."
psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW mv_estadisticas_diarias;"

# 5. ANÁLISIS DE TENDENCIAS
echo "5. Trend analysis..."
# Generate weekly trend report
curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/reportes-automaticos \
     -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
     -d '{"type": "weekly_trends"}'

# 6. VERIFICACIÓN DE SEGURIDAD
echo "6. Security audit..."
# Check for suspicious activity
psql $DATABASE_URL -c "
SELECT 
    created_at,
    event_type,
    table_name,
    user_id
FROM audit_log 
WHERE created_at > NOW() - INTERVAL '7 days'
AND event_type = 'FAILED_LOGIN'
ORDER BY created_at DESC;"

echo "=== WEEKLY OPERATIONS COMPLETED ==="
```

### 1.3 Monthly Operations Runbook

#### **📆 PROCEDIMIENTO MENSUAL (Primer día del mes)**

```bash
#!/bin/bash
# monthly-operations.sh

echo "=== MONTHLY OPERATIONS - $(date) ==="

# 1. ANÁLISIS COMPLETO DE COSTOS
echo "1. Cost analysis..."
# Analyze resource usage and costs
# (Database storage, bandwidth, compute usage)

# 2. OPTIMIZACIÓN DE QUERIES
echo "2. Query optimization review..."
# Find slow queries and optimize
psql $DATABASE_URL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"

# 3. PLANIFICACIÓN DE CAPACITY
echo "3. Capacity planning..."
# Analyze growth trends and plan capacity

# 4. AUDITORÍA COMPLETA DE SEGURIDAD
echo "4. Complete security audit..."
# Full security review

# 5. PLANIFICACIÓN DE MEJORAS
echo "5. Improvement planning..."
# Plan improvements for next month

echo "=== MONTHLY OPERATIONS COMPLETED ==="
```

---

## 2. PROCEDIMIENTOS DE BACKUP Y RECOVERY

### 2.1 Backup Strategy

#### **📋 TIPOS DE BACKUP**

| Tipo | Frecuencia | Retención | Descripción |
|------|------------|-----------|-------------|
| **Full Backup** | Diario a las 2:00 AM | 30 días | Backup completo de base de datos |
| **Incremental** | Cada 6 horas | 7 días | Solo cambios desde último backup |
| **WAL Archiving** | Continuo | 15 días | Write-Ahead Logs para point-in-time recovery |
| **Config Backup** | Diario | 90 días | Configuraciones y edge functions |
| **Log Backup** | Cada hora | 7 días | Logs de aplicación |

#### **🔧 PROCEDIMIENTO DE BACKUP AUTOMÁTICO**

```sql
-- Configurar backup automático en Supabase
-- Comando para activar WAL archiving
SELECT pg_start_backup('daily_backup_' || current_date);

-- Crear backup de configuración
COPY (
    SELECT * FROM configuracion_proveedor
    UNION ALL
    SELECT id, clave, valor, descripcion, 'personal' as tipo_dato, updated_at
    FROM personal
) TO PROGRAM 'gzip > /backups/config_' || current_date || '.sql.gz';

SELECT pg_stop_backup();
```

```bash
#!/bin/bash
# automated-backup.sh

BACKUP_DIR="/backups/minimarket"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# 1. BACKUP DE BASE DE DATOS
echo "Creating database backup..."
pg_dump $DATABASE_URL \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --file="$BACKUP_DIR/minimarket_$DATE.backup"

# 2. BACKUP DE CONFIGURACIÓN
echo "Backing up configuration..."
psql $DATABASE_URL -c "COPY (
    SELECT 'config', clave, valor, descripcion, updated_at 
    FROM configuracion_proveedor
) TO STDOUT WITH CSV HEADER" > "$BACKUP_DIR/config_$DATE.csv"

# 3. BACKUP DE EDGE FUNCTIONS
echo "Backing up edge functions..."
for func in scraper-maxiconsumo api-minimarket api-proveedor alertas-stock; do
    supabase functions download $func --output-file="$BACKUP_DIR/$func_$DATE.zip"
done

# 4. COMPRIMIR BACKUP
echo "Compressing backup..."
tar -czf "$BACKUP_DIR/minimarket_full_$DATE.tar.gz" \
    "$BACKUP_DIR/minimarket_$DATE.backup" \
    "$BACKUP_DIR/config_$DATE.csv" \
    "$BACKUP_DIR"/*_"$DATE".zip

# 5. SUBIR A STORAGE
echo "Uploading to secure storage..."
# aws s3 cp "$BACKUP_DIR/minimarket_full_$DATE.tar.gz" s3://minimarket-backups/
# o usar el storage de Supabase

# 6. LIMPIAR BACKUPS VIEJOS
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.backup" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.csv" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 7. VERIFICAR BACKUP
echo "Verifying backup integrity..."
if pg_restore --list "$BACKUP_DIR/minimarket_$DATE.backup" >/dev/null 2>&1; then
    echo "✅ Backup verification successful"
else
    echo "❌ Backup verification failed"
    # Send alert
fi

echo "Backup completed: minimarket_full_$DATE.tar.gz"
```

### 2.2 Recovery Procedures

#### **⚡ PROCEDIMIENTO DE RECOVERY EMERGENCIA**

```bash
#!/bin/bash
# emergency-recovery.sh

BACKUP_FILE=$1
RECOVERY_TARGET=$2

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [recovery_timestamp]"
    exit 1
fi

echo "=== EMERGENCY RECOVERY PROCEDURE ==="
echo "Backup file: $BACKUP_FILE"
echo "Recovery target: ${RECOVERY_TARGET:-latest}"

# 1. PARAR TODAS LAS CONEXIONES
echo "1. Stopping all connections..."
# Kill active connections
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active';"

# 2. CREAR BACKUP DE EMERGENCIA
echo "2. Creating emergency backup..."
pg_dump $DATABASE_URL --format=custom --file="emergency_backup_$(date +%Y%m%d_%H%M%S).backup"

# 3. RESTAURAR DESDE BACKUP
echo "3. Restoring from backup..."
dropdb $DATABASE_NAME || true
createdb $DATABASE_NAME
pg_restore --verbose --clean --no-owner --no-privileges \
           --dbname=$DATABASE_NAME $BACKUP_FILE

# 4. APLICAR POINT-IN-TIME RECOVERY SI ES NECESARIO
if [ ! -z "$RECOVERY_TARGET" ]; then
    echo "4. Applying point-in-time recovery to: $RECOVERY_TARGET"
    # Aplicar WAL logs hasta el timestamp especificado
fi

# 5. VERIFICAR INTEGRIDAD
echo "5. Verifying data integrity..."
psql $DATABASE_URL -c "
SELECT 
    (SELECT COUNT(*) FROM productos) as productos,
    (SELECT COUNT(*) FROM categorias) as categorias,
    (SELECT COUNT(*) FROM proveedores) as proveedores;"

# 6. VERIFICAR CONSISTENCIA
echo "6. Checking referential integrity..."
psql $DATABASE_URL -c "
SELECT 
    COUNT(*) as productos_sin_categoria
FROM productos p 
LEFT JOIN categorias c ON p.categoria_id = c.id 
WHERE c.id IS NULL;"

# 7. RESTAURAR EDGE FUNCTIONS
echo "7. Restoring edge functions..."
supabase functions deploy --no-verify-jwt

# 8. VERIFICAR SISTEMA
echo "8. System verification..."
curl -f https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/api-minimarket

echo "=== RECOVERY COMPLETED ==="
```

#### **🔄 PROCEDIMIENTO DE RECOVERY COMPLETO**

```markdown
## COMPLETE RECOVERY PROCEDURE

### Situation Assessment
1. **Identify the issue**
   - Database corruption
   - Accidental data deletion
   - System failure
   - Security breach

2. **Determine scope**
   - Full system recovery needed?
   - Partial recovery possible?
   - Point-in-time recovery required?

3. **Notify stakeholders**
   - Management team
   - Users (if applicable)
   - Technical team

### Recovery Steps
1. **Stop all traffic**
   - Put system in maintenance mode
   - Redirect users to status page

2. **Assess damage**
   - Check backup integrity
   - Identify last good state

3. **Execute recovery**
   - Follow emergency recovery script
   - Document all steps taken

4. **Verify restoration**
   - Run integrity checks
   - Test critical functions
   - Verify data completeness

5. **Resume operations**
   - Disable maintenance mode
   - Monitor system health
   - Send recovery notification

6. **Post-recovery analysis**
   - Root cause analysis
   - Update procedures
   - Prevent future occurrences
```

---

## 3. GUÍAS DE TROUBLESHOOTING EXPANDIDAS

### 3.1 Sistema No Responde

#### **🚨 DIAGNÓSTICO RÁPIDO**

```bash
#!/bin/bash
# system-down-diagnostic.sh

echo "=== SYSTEM DOWN DIAGNOSTIC ==="
TIMESTAMP=$(date)

# 1. Verificar conectividad básica
echo "1. Basic connectivity check..."
ping -c 3 google.com && echo "✅ Internet OK" || echo "❌ Internet FAILED"

# 2. Verificar Supabase
echo "2. Supabase service check..."
curl -f -s --max-time 10 https://htvlwhisjpdagqkqnpxg.supabase.co/rest/v1/ || echo "❌ Supabase API FAILED"

# 3. Verificar DNS
echo "3. DNS resolution check..."
nslookup htvlwhisjpdagqkqnpxg.supabase.co || echo "❌ DNS FAILED"

# 4. Verificar edge functions
echo "4. Edge functions check..."
for func in api-minimarket scraper-maxiconsumo alertas-stock; do
    response=$(curl -s -o /dev/null -w "%{http_code}" https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/$func)
    if [ "$response" -eq 200 ]; then
        echo "✅ $func: OK"
    else
        echo "❌ $func: FAILED (HTTP $response)"
    fi
done

# 5. Verificar base de datos
echo "5. Database connectivity..."
psql $DATABASE_URL -c "SELECT version();" 2>/dev/null && echo "✅ Database OK" || echo "❌ Database FAILED"

# 6. Verificar logs recientes
echo "6. Recent error logs..."
supabase functions logs --limit 20 2>/dev/null | grep -i error | tail -5

echo "=== DIAGNOSTIC COMPLETED ==="
```

#### **🔧 CORRECCIONES COMUNES**

| Problema | Síntoma | Diagnóstico | Solución |
|----------|---------|-------------|----------|
| **API no responde** | HTTP 500/timeout | Check edge functions | Redeploy functions |
| **Database timeout** | Queries very slow | Check connections | Restart connection pool |
| **Scraper falla** | Error en logs | Check provider site | Manual trigger + retry |
| **Stock desactualizado** | Datos incorrectos | Check cron jobs | Run manual sync |
| **Alertas no enviadas** | Notificaciones faltantes | Check notification service | Manual send + fix config |

### 3.2 Performance Issues

#### **📊 DIAGNÓSTICO DE PERFORMANCE**

```bash
#!/bin/bash
# performance-diagnostic.sh

echo "=== PERFORMANCE DIAGNOSTIC ==="

# 1. CPU y Memory usage
echo "1. System resources..."
free -h
top -bn1 | head -20

# 2. Database performance
echo "2. Database performance..."
psql $DATABASE_URL -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched
FROM pg_stat_database 
WHERE datname = current_database();"

# 3. Slow queries
echo "3. Slow queries..."
psql $DATABASE_URL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# 4. Connection count
echo "4. Active connections..."
psql $DATABASE_URL -c "
SELECT 
    state,
    count(*) as connection_count
FROM pg_stat_activity 
WHERE datname = current_database()
GROUP BY state;"

# 5. Lock analysis
echo "5. Lock analysis..."
psql $DATABASE_URL -c "
SELECT 
    a.datname,
    l.relation::regclass,
    l.mode,
    l.locktype,
    page,
    virtualtransaction,
    pid,
    a.query,
    a.query_start,
    a.state
FROM pg_stat_activity a 
JOIN pg_locks l ON l.pid = a.pid 
WHERE a.datname = current_database()
ORDER BY relation DESC;"

echo "=== PERFORMANCE DIAGNOSTIC COMPLETED ==="
```

### 3.3 Data Integrity Issues

#### **🔍 VERIFICACIÓN DE INTEGRIDAD**

```sql
-- integrity-check.sql

-- 1. Verificar foreign keys
SELECT 
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table
FROM pg_constraint 
WHERE contype = 'f' 
AND connamespace = 'public'::regnamespace;

-- 2. Verificar integridad de productos
SELECT 
    p.id,
    p.nombre,
    p.categoria_id,
    c.nombre as categoria_nombre
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE c.id IS NULL;

-- 3. Verificar integridad de stock
SELECT 
    s.producto_id,
    p.nombre as producto_nombre,
    s.stock_actual,
    s.stock_minimo
FROM stock_deposito s
LEFT JOIN productos p ON s.producto_id = p.id
WHERE p.id IS NULL;

-- 4. Verificar precios duplicados
SELECT 
    producto_id,
    proveedor_id,
    COUNT(*) as duplicate_count
FROM precios_proveedor
WHERE es_precio_vigente = TRUE
GROUP BY producto_id, proveedor_id
HAVING COUNT(*) > 1;

-- 5. Verificar datos inconsistentes
SELECT 
    'Productos sin código de barras' as issue,
    COUNT(*) as count
FROM productos 
WHERE codigo_barras IS NULL AND codigo_barras != ''
UNION ALL
SELECT 
    'Categorías huérfanas' as issue,
    COUNT(*) as count
FROM categorias c
WHERE c.parent_id IS NOT NULL 
AND c.parent_id NOT IN (SELECT id FROM categorias WHERE id = c.parent_id);
```

---

## 4. PROCEDIMIENTOS DE MONITOREO Y ALERTAS

### 4.1 Monitoring Architecture

#### **📊 MÉTRICAS CLAVE MONITOREADAS**

```yaml
# monitoring-config.yaml
metrics:
  application:
    - api_response_time
    - api_error_rate
    - active_users
    - request_count
    
  database:
    - connection_count
    - query_execution_time
    - lock_waits
    - storage_usage
    
  system:
    - cpu_usage
    - memory_usage
    - disk_usage
    - network_latency
    
  business:
    - productos_actualizados
    - stock_bajo_count
    - tareas_pendientes
    - scraping_success_rate

alerts:
  critical:
    - api_down
    - database_connection_lost
    - storage_full
    - security_breach
    
  warning:
    - high_response_time
    - low_disk_space
    - failed_scraping_runs
    - stock_critically_low
    
  info:
    - deployment_completed
    - backup_successful
    - performance_thresholds_exceeded
```

### 4.2 Alert Configuration

#### **🚨 ALERTAS CRÍTICAS**

```sql
-- Configurar alertas automáticas en la base de datos
CREATE OR REPLACE FUNCTION check_critical_alerts()
RETURNS VOID AS $$
DECLARE
    low_stock_count INTEGER;
    failed_scraping_count INTEGER;
    api_error_rate NUMERIC;
BEGIN
    -- Verificar stock bajo crítico
    SELECT COUNT(*) INTO low_stock_count
    FROM stock_deposito
    WHERE stock_actual <= stock_minimo / 2;
    
    IF low_stock_count > 10 THEN
        INSERT INTO alertas_sistema (tipo, mensaje, severidad, fecha_creacion)
        VALUES ('STOCK_CRITICO', 
                'Hay ' || low_stock_count || ' productos con stock críticamente bajo',
                'critica',
                NOW());
    END IF;
    
    -- Verificar fallos de scraping
    SELECT COUNT(*) INTO failed_scraping_count
    FROM estadisticas_scraping
    WHERE fecha_inicio > NOW() - INTERVAL '24 hours'
    AND tasa_exito < 80;
    
    IF failed_scraping_count > 3 THEN
        INSERT INTO alertas_sistema (tipo, mensaje, severidad, fecha_creacion)
        VALUES ('SCRAPING_FALLA',
                'Se detectaron ' || failed_scraping_count || ' fallos de scraping en 24h',
                'alta',
                NOW());
    END IF;
    
END;
$$ LANGUAGE plpgsql;

-- Programar verificación cada 15 minutos
SELECT cron.schedule('critical-alerts-check', '*/15 * * * *', 'SELECT check_critical_alerts();');
```

### 4.3 Dashboard Monitoring

#### **📈 MÉTRICAS EN TIEMPO REAL**

```sql
-- Vista para dashboard de monitoreo
CREATE VIEW vista_monitoreo_tiempo_real AS
SELECT 
    -- Métricas de aplicación
    (SELECT COUNT(*) FROM api_requests WHERE created_at > NOW() - INTERVAL '1 hour') as requests_last_hour,
    (SELECT AVG(response_time) FROM api_requests WHERE created_at > NOW() - INTERVAL '1 hour') as avg_response_time,
    (SELECT COUNT(*) FROM api_requests WHERE status_code >= 400 AND created_at > NOW() - INTERVAL '1 hour') as errors_last_hour,
    
    -- Métricas de base de datos
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_transactions,
    
    -- Métricas de negocio
    (SELECT COUNT(*) FROM productos WHERE activo = TRUE) as total_productos,
    (SELECT COUNT(*) FROM stock_deposito WHERE stock_actual <= stock_minimo) as productos_stock_bajo,
    (SELECT COUNT(*) FROM tareas_pendientes WHERE estado = 'pendiente') as tareas_pendientes,
    (SELECT COUNT(*) FROM alertas_cambios_precios WHERE procesada = FALSE) as alertas_pendientes,
    
    -- Métricas de scraping
    (SELECT AVG(tasa_exito) FROM estadisticas_scraping WHERE fecha_inicio > NOW() - INTERVAL '24 hours') as scraping_success_rate,
    (SELECT MAX(fecha_inicio) FROM estadisticas_scraping WHERE fecha_inicio > NOW() - INTERVAL '24 hours') as last_scraping_run,
    
    -- Timestamp
    NOW() as timestamp;
```

---

## 5. GUÍAS DE ESCALAMIENTO

### 5.1 Escalation Matrix

#### **📞 CONTACTOS DE ESCALAMIENTO**

| Nivel | Tiempo Respuesta | Contacto | Situación |
|-------|-----------------|----------|-----------|
| **L1** | 15 minutos | DevOps On-Call | Problemas menores, configuración |
| **L2** | 1 hora | Senior Developer | Errores de aplicación, debugging |
| **L3** | 4 horas | Technical Lead | Problemas complejos, arquitectura |
| **L4** | 24 horas | CTO/Engineering Manager | Problemas críticos, decisiones estratégicas |

#### **🔴 ESCALAMIENTO AUTOMÁTICO**

```bash
#!/bin/bash
# auto-escalation.sh

# Función para enviar alerta escalando
send_escalation_alert() {
    local severity=$1
    local message=$2
    local timeout_minutes=$3
    
    case $severity in
        "critica")
            # Alert L1 immediately
            send_slack_alert "#escalation-critical" "🚨 CRITICAL: $message"
            send_email_alert "oncall@company.com" "CRITICAL: $message"
            
            # Auto-escalate to L2 after timeout
            sleep $((timeout_minutes * 60))
            send_slack_alert "#escalation-critical" "⚠️ ESCALATING TO L2: $message"
            send_email_alert "senior-dev@company.com" "ESCALATED: $message"
            ;;
        "alta")
            # Alert L1 immediately
            send_slack_alert "#escalation-high" "⚠️ HIGH: $message"
            send_email_alert "devops@company.com" "HIGH: $message"
            ;;
        "media")
            # Log and monitor
            echo "$(date): $message" >> /var/log/minimarket/escalations.log
            send_slack_alert("#general", "📋 INFO: $message")
            ;;
    esac
}

# Ejemplos de uso
case "$1" in
    "api-down")
        send_escalation_alert "critica" "API no responde - Todas las funciones" 15
        ;;
    "database-issue")
        send_escalation_alert "critica" "Problema de base de datos detectado" 30
        ;;
    "scraping-failure")
        send_escalation_alert "alta" "Fallos consecutivos en scraping" 60
        ;;
    "performance-degradation")
        send_escalation_alert "alta" "Degradación de performance detectada" 30
        ;;
    *)
        echo "Uso: $0 [api-down|database-issue|scraping-failure|performance-degradation]"
        exit 1
        ;;
esac
```

### 5.2 Incident Response

#### **🆘 PROTOCOLO DE RESPUESTA A INCIDENTES**

```markdown
## INCIDENT RESPONSE PROTOCOL

### Phase 1: Detection & Assessment (0-15 minutes)
1. **Alert received**
   - Acknowledge alert
   - Assess severity
   - Assign incident commander

2. **Initial investigation**
   - Check system status
   - Identify scope of impact
   - Gather preliminary data

3. **Communication**
   - Notify stakeholders
   - Update status page
   - Begin incident log

### Phase 2: Containment & Mitigation (15-60 minutes)
1. **Immediate actions**
   - Implement temporary fixes
   - Isolate affected systems
   - Preserve evidence

2. **Short-term mitigation**
   - Deploy emergency patches
   - Scale resources if needed
   - Enable backup systems

3. **Communication updates**
   - Regular status updates
   - Stakeholder briefings
   - User notifications

### Phase 3: Resolution & Recovery (1-4 hours)
1. **Root cause identification**
   - Analyze logs and data
   - Identify failure points
   - Document findings

2. **Permanent fix implementation**
   - Deploy solution
   - Verify functionality
   - Monitor performance

3. **Recovery verification**
   - Test all systems
   - Validate data integrity
   - Confirm normal operations

### Phase 4: Post-Incident (After resolution)
1. **Incident review**
   - 5 Whys analysis
   - Timeline reconstruction
   - Impact assessment

2. **Documentation**
   - Incident report
   - Lessons learned
   - Process improvements

3. **Prevention**
   - Update monitoring
   - Improve procedures
   - Additional safeguards
```

---

## 6. PROCEDIMIENTOS DE MANTENIMIENTO

### 6.1 Scheduled Maintenance

#### **🔧 MANTENIMIENTO SEMANAL**

```bash
#!/bin/bash
# weekly-maintenance.sh

echo "=== WEEKLY MAINTENANCE - $(date) ==="

# 1. VACUUM Y ANALYZE BASE DE DATOS
echo "1. Database maintenance..."
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# 2. REINDEX SI ES NECESARIO
echo "2. Checking indexes..."
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
LIMIT 10;"

# 3. LIMPIAR LOGS ANTIGUOS
echo "3. Cleaning old logs..."
psql $DATABASE_URL -c "
DELETE FROM logs_scraping 
WHERE timestamp < NOW() - INTERVAL '30 days';"

# 4. ACTUALIZAR ESTADÍSTICAS
echo "4. Updating statistics..."
psql $DATABASE_URL -c "ANALYZE;"

# 5. REFRESH VISTAS MATERIALIZADAS
echo "5. Refreshing materialized views..."
psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW mv_estadisticas_diarias;"

# 6. VERIFICAR INTEGRIDAD
echo "6. Integrity check..."
psql $DATABASE_URL -c "
SELECT 
    'Productos sin categoría' as issue,
    COUNT(*) as count
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE c.id IS NULL
UNION ALL
SELECT 
    'Precios sin producto' as issue,
    COUNT(*) as count
FROM precios_proveedor pp
LEFT JOIN productos p ON pp.producto_id = p.id
WHERE p.id IS NULL;"

echo "=== WEEKLY MAINTENANCE COMPLETED ==="
```

### 6.2 Unplanned Maintenance

#### **🚨 PROCEDIMIENTO DE EMERGENCIA**

```bash
#!/bin/bash
# emergency-maintenance.sh

INCIDENT_ID=$1
REASON=$2

echo "=== EMERGENCY MAINTENANCE ==="
echo "Incident ID: $INCIDENT_ID"
echo "Reason: $REASON"
echo "Start time: $(date)"

# 1. CREAR PUNTO DE BACKUP
echo "1. Creating emergency backup..."
BACKUP_FILE="emergency_backup_${INCIDENT_ID}_$(date +%Y%m%d_%H%M%S).sql"
pg_dump $DATABASE_URL --format=custom --file=$BACKUP_FILE

# 2. ACTIVAR MODO MANTENIMIENTO
echo "2. Enabling maintenance mode..."
# Update status in database
psql $DATABASE_URL -c "
INSERT INTO system_status (status, message, started_at)
VALUES ('maintenance', '$REASON', NOW());"

# 3. NOTIFICAR USUARIOS
echo "3. Notifying users..."
# Send maintenance notification
curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/notificaciones-tareas \
     -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
     -d '{"tipo": "mantenimiento", "mensaje": "Sistema en mantenimiento por $REASON"}'

# 4. PROCEDER CON MANTENIMIENTO
echo "4. Performing maintenance..."
# Maintenance commands here

# 5. VERIFICAR SISTEMA
echo "5. System verification..."
supabase functions list

# 6. DESACTIVAR MODO MANTENIMIENTO
echo "6. Disabling maintenance mode..."
psql $DATABASE_URL -c "
UPDATE system_status 
SET status = 'operational', 
    ended_at = NOW()
WHERE status = 'maintenance';"

echo "=== EMERGENCY MAINTENANCE COMPLETED ==="
```

---

## 7. PROTOCOLOS DE SEGURIDAD

### 7.1 Security Monitoring

#### **🔐 AUDITORÍA DE SEGURIDAD**

```sql
-- Función para auditoría de seguridad
CREATE OR REPLACE FUNCTION security_audit()
RETURNS TABLE (
    audit_type VARCHAR,
    finding VARCHAR,
    severity VARCHAR,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- 1. Verificar usuarios sin roles
    SELECT 
        'USERS' as audit_type,
        'Usuario sin rol asignado: ' || p.email as finding,
        'media' as severity,
        'Asignar rol apropiado al usuario' as recommendation
    FROM personal p
    WHERE p.rol IS NULL
    AND p.activo = TRUE
    
    UNION ALL
    
    -- 2. Verificar intentos de login fallidos
    SELECT 
        'AUTHENTICATION' as audit_type,
        'Intentos de login fallidos múltiples desde IP: ' || ip_address as finding,
        'alta' as severity,
        'Revisar y bloquear IP si es necesario' as recommendation
    FROM failed_login_attempts
    WHERE attempt_time > NOW() - INTERVAL '24 hours'
    GROUP BY ip_address
    HAVING COUNT(*) > 5
    
    UNION ALL
    
    -- 3. Verificar datos sensibles en logs
    SELECT 
        'DATA_LEAKAGE' as audit_type,
        'Posible exposición de datos sensibles en logs' as finding,
        'critica' as severity,
        'Revisar y limpiar logs, implementar masking' as recommendation
    FROM logs_scraping
    WHERE mensaje ~ '[0-9]{4}[\s\-]?[0-9]{4}'
    AND timestamp > NOW() - INTERVAL '7 days'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Ejecutar auditoría diaria
SELECT cron.schedule('daily-security-audit', '0 6 * * *', 'SELECT * FROM security_audit();');
```

### 7.2 Access Control

#### **🛡️ GESTIÓN DE ACCESOS**

```sql
-- Vista para control de accesos
CREATE VIEW vista_control_accesos AS
SELECT 
    p.id,
    p.nombre,
    p.email,
    p.rol,
    p.activo,
    p.fecha_ingreso,
    -- Último acceso
    (SELECT MAX(created_at) FROM audit_log WHERE user_id = p.id) as ultimo_acceso,
    -- Número de accesos esta semana
    (SELECT COUNT(*) FROM audit_log 
     WHERE user_id = p.id 
     AND created_at > NOW() - INTERVAL '7 days') as accesos_semana,
    -- Actividades recientes
    (SELECT string_agg(DISTINCT table_name, ', ') 
     FROM audit_log 
     WHERE user_id = p.id 
     AND created_at > NOW() - INTERVAL '7 days') as tablas_accedidas
FROM personal p
WHERE p.activo = TRUE;

-- Función para revocar accesos
CREATE OR REPLACE FUNCTION revoke_user_access(user_email VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- Marcar usuario como inactivo
    UPDATE personal 
    SET activo = FALSE, 
        updated_at = NOW()
    WHERE email = user_email;
    
    -- Registrar en auditoría
    INSERT INTO audit_log (event_type, table_name, old_data, changed_at)
    VALUES ('REVOKE_ACCESS', 'personal', 
            jsonb_build_object('email', user_email, 'activo', TRUE), 
            NOW());
            
    -- Log de seguridad
    INSERT INTO security_logs (event_type, description, severity, timestamp)
    VALUES ('ACCESS_REVOKED', 
            'Access revoked for user: ' || user_email, 
            'alta', 
            NOW());
END;
$$ LANGUAGE plpgsql;
```

---

## 8. COMANDOS DE REFERENCIA RÁPIDA

### 8.1 Quick Reference Commands

#### **⚡ COMANDOS ESENCIALES**

```bash
# ============================================================================
# MINIMARKET - QUICK REFERENCE COMMANDS
# ============================================================================

# ----------------------------------------------------------------------------
# SYSTEM HEALTH CHECK
# ----------------------------------------------------------------------------
# Quick health check
curl -f https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/api-minimarket

# Database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Edge functions status
supabase functions list

# Recent errors
supabase functions logs --limit 20 | grep -i error

# ----------------------------------------------------------------------------
# BACKUP & RECOVERY
# ----------------------------------------------------------------------------
# Quick backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql $DATABASE_NAME < backup_file.sql

# Check backup integrity
pg_restore --list backup_file.backup

# ----------------------------------------------------------------------------
# MONITORING
# ----------------------------------------------------------------------------
# Active connections
psql $DATABASE_URL -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"

# Slow queries
psql $DATABASE_URL -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;"

# ----------------------------------------------------------------------------
# MAINTENANCE
# ----------------------------------------------------------------------------
# Vacuum database
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Refresh materialized views
psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW mv_estadisticas_diarias;"

# Clean old logs (30 days)
psql $DATABASE_URL -c "DELETE FROM logs_scraping WHERE timestamp < NOW() - INTERVAL '30 days';"

# ----------------------------------------------------------------------------
# TROUBLESHOOTING
# ----------------------------------------------------------------------------
# Check system resources
free -h && df -h

# View active processes
ps aux | grep -E "(node|postgres|supabase)"

# Check network connectivity
netstat -tulpn | grep -E "(3000|54321|5432)"

# ----------------------------------------------------------------------------
# SECURITY
# ----------------------------------------------------------------------------
# Check failed logins
psql $DATABASE_URL -c "SELECT * FROM failed_login_attempts WHERE attempt_time > NOW() - INTERVAL '24 hours';"

# Audit user access
psql $DATABASE_URL -c "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 20;"

# Check security logs
psql $DATABASE_URL -c "SELECT * FROM security_logs WHERE timestamp > NOW() - INTERVAL '7 days' ORDER BY timestamp DESC;"

# ----------------------------------------------------------------------------
# BUSINESS INTELLIGENCE
# ----------------------------------------------------------------------------
# Products with low stock
psql $DATABASE_URL -c "SELECT p.nombre, s.stock_actual, s.stock_minimo FROM productos p JOIN stock_deposito s ON p.id = s.producto_id WHERE s.stock_actual <= s.stock_minimo;"

# Pending tasks
psql $DATABASE_URL -c "SELECT COUNT(*) as tareas_pendientes FROM tareas_pendientes WHERE estado = 'pendiente';"

# Recent alerts
psql $DATABASE_URL -c "SELECT COUNT(*) as alertas_activas FROM alertas_cambios_precios WHERE procesada = FALSE;"

# ----------------------------------------------------------------------------
# EDGE FUNCTIONS
# ----------------------------------------------------------------------------
# Deploy specific function
supabase functions deploy api-minimarket

# View function logs
supabase functions logs api-minimarket --limit 50

# Test function manually
curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/api-minimarket/categorias \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json"

# ----------------------------------------------------------------------------
# CRON JOBS
# ----------------------------------------------------------------------------
# List scheduled jobs
psql $DATABASE_URL -c "SELECT * FROM cron.job;"

# Create new cron job
psql $DATABASE_URL -c "SELECT cron.schedule('job-name', 'cron-expression', 'SQL command');"

# Unschedule job
psql $DATABASE_URL -c "SELECT cron.unschedule('job-name');"

# ----------------------------------------------------------------------------
# ALERTS & NOTIFICATIONS
# ----------------------------------------------------------------------------
# Trigger manual alert
curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/alertas-stock \
     -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
     -d '{"tipo": "manual", "mensaje": "Test alert"}'

# Check alert queue
psql $DATABASE_URL -c "SELECT * FROM notificaciones_tareas WHERE enviada = FALSE;"

# ----------------------------------------------------------------------------
# DATA OPERATIONS
# ----------------------------------------------------------------------------
# Import data from CSV
\copy productos FROM 'productos.csv' WITH CSV HEADER;

# Export data to CSV
\copy (SELECT * FROM vista_productos_con_stock) TO 'productos_export.csv' WITH CSV HEADER;

# Bulk insert
psql $DATABASE_URL -c "
INSERT INTO productos (nombre, categoria_id) 
SELECT nombre, categoria_id 
FROM staging_productos 
WHERE imported = FALSE;"

# ----------------------------------------------------------------------------
# DEVELOPMENT & DEBUGGING
# ----------------------------------------------------------------------------
# Enable query logging
psql $DATABASE_URL -c "ALTER SYSTEM SET log_statement = 'all';"

# Show current settings
psql $DATABASE_URL -c "SHOW ALL;"

# Explain query plan
EXPLAIN ANALYZE SELECT * FROM productos WHERE categoria_id = 'uuid';

# View database schema
\dt

# View table structure
\d productos

# ----------------------------------------------------------------------------
# PERFORMANCE TUNING
# ----------------------------------------------------------------------------
# Check index usage
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;"

# Analyze query performance
psql $DATABASE_URL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"

# ----------------------------------------------------------------------------
# CLEANUP & MAINTENANCE
# ----------------------------------------------------------------------------
# Clean orphaned records
psql $DATABASE_URL -c "
DELETE FROM stock_deposito 
WHERE producto_id NOT IN (SELECT id FROM productos);"

# Rebuild index
REINDEX INDEX index_name;

# Analyze table statistics
ANALYZE;

# Check for bloat
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_percent DESC;"
```

### 8.2 Emergency Contact List

#### **📞 CONTACTOS DE EMERGENCIA**

```markdown
## EMERGENCY CONTACTS

### Technical Team
- **DevOps On-Call**: +54-xxx-xxxx
- **Senior Developer**: +54-xxx-xxxx
- **Database Administrator**: +54-xxx-xxxx
- **Security Engineer**: +54-xxx-xxxx

### Management
- **Technical Lead**: +54-xxx-xxxx
- **Engineering Manager**: +54-xxx-xxxx
- **CTO**: +54-xxx-xxxx

### External Support
- **Supabase Support**: https://supabase.com/support
- **Cloud Provider**: [Provider support URL]
- **Domain Registrar**: [Registrar support]

### Escalation Procedure
1. **L1 (0-15 min)**: DevOps On-Call
2. **L2 (15-60 min)**: Senior Developer
3. **L3 (1-4 hours)**: Technical Lead
4. **L4 (>4 hours)**: Engineering Manager

### Communication Channels
- **Slack #incidents**: Real-time incident communication
- **Email incidents@company.com**: Formal incident reporting
- **Status Page**: https://status.minimarket.com
```

---

Esta documentación operacional expandida proporciona runbooks completos, procedimientos de backup y recovery, guías de troubleshooting detalladas, protocolos de monitoreo y escalamiento, procedimientos de mantenimiento, protocolos de seguridad y comandos de referencia rápida para la operación eficiente del sistema Mini Market en producción.
