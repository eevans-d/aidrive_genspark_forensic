# Configuración de Cron Jobs - Mini Market Sprint 6

## Cron Jobs Configurados

### 1. Job Diario de Actualización de Precios
- **Archivo**: `job_daily_price_update.json`
- **ID**: 5
- **Cron Expression**: `0 2 * * *` (02:00 AM diario)
- **Función Edge**: `cron-jobs-maxiconsumo`
- **Parámetros**:
  - `job_type`: "daily-price-update"
  - `scraping_mode`: "full_catalog"
  - `price_change_threshold`: 2%
  - `notifications_enabled`: true
- **Descripción**: Realiza scraping completo del catálogo Maxiconsumo y actualiza precios con cambios > 2%

### 2. Job Semanal de Análisis de Tendencias
- **Archivo**: `job_weekly_trend_analysis.json`
- **ID**: 6
- **Cron Expression**: `0 3 * * 0` (Domingos 03:00 AM)
- **Función Edge**: `cron-jobs-maxiconsumo`
- **Parámetros**:
  - `job_type`: "weekly-trend-analysis"
  - `analysis_period`: "weekly"
  - `ml_predictions`: true
  - `seasonal_patterns`: true
  - `generate_reports`: true
- **Descripción**: Análisis completo de tendencias con ML básico y predicciones de precios

### 3. Job de Alertas Tiempo Real
- **Archivo**: `job_realtime_alerts.json`
- **ID**: 7
- **Cron Expression**: `*/15 * * * *` (cada 15 minutos)
- **Función Edge**: `cron-jobs-maxiconsumo`
- **Parámetros**:
  - `job_type`: "realtime-alerts"
  - `alert_threshold`: 15%
  - `check_frequency`: 15 minutos
  - `critical_products_only`: true
  - `instant_notifications`: true
  - `escalation_enabled`: true
- **Descripción**: Monitoreo continuo con alertas instantáneas para cambios > 15%

## Implementación en Supabase

### Paso 1: Crear el Job en la Base de Datos
```sql
-- Ejecutar el raw_sql de cada archivo JSON en Supabase SQL Editor
-- El raw_sql contiene la creación del procedimiento y el schedule
```

### Paso 2: Verificar el Estado de los Jobs
```sql
-- Ver jobs activos
SELECT * FROM cron.job;

-- Ver próximas ejecuciones
SELECT * FROM cron.job_run_details 
WHERE jobname IN ('daily_price_update', 'weekly_trend_analysis', 'realtime_alerts')
ORDER BY run_time DESC;
```

### Paso 3: Monitorear Ejecuciones
```sql
-- Ver logs de ejecución
SELECT * FROM cron.job_run_details 
WHERE jobname = 'daily_price_update'
ORDER BY run_time DESC 
LIMIT 10;
```

## Configuración de la Función Edge

La función `cron-jobs-maxiconsumo` debe estar desplegada en Supabase con las siguientes rutas:

- `POST /functions/v1/cron-jobs-maxiconsumo` - Ejecutar jobs
- `GET /functions/v1/cron-jobs-maxiconsumo?action=status` - Estado de jobs
- `GET /functions/v1/cron-jobs-maxiconsumo?action=health` - Health check

## Variables de Entorno Requeridas

```bash
SUPABASE_URL=https://htvlwhisjpdagqkqnpxg.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
SENDGRID_API_KEY=<sendgrid_key>
TWILIO_ACCOUNT_SID=<twilio_sid>
TWILIO_AUTH_TOKEN=<twilio_token>
```

## Gestión de Jobs

### Activar Job
```sql
SELECT cron.unschedule('daily_price_update');
SELECT cron.schedule('daily_price_update', '0 2 * * *', 'CALL daily_price_update_9f7c2a8b()');
```

### Desactivar Job
```sql
SELECT cron.unschedule('daily_price_update');
```

### Modificar Cron Expression
```sql
SELECT cron.unschedule('daily_price_update');
-- Modificar cron_expression en el JSON y ejecutar el nuevo raw_sql
```

## Alertas y Notificaciones

- **Email**: Para jobs completados/fallidos y cambios significativos
- **SMS**: Solo para alertas críticas (>15% cambio de precio)
- **Dashboard**: Monitoreo en tiempo real en `/workspace/docs/CRON_JOBS_COMPLETOS.md`

## Resolución de Problemas

### Job No Se Ejecuta
1. Verificar que pg_cron esté habilitado: `SELECT extname FROM pg_extension WHERE extname = 'pg_cron';`
2. Verificar que el job esté scheduleado: `SELECT * FROM cron.job WHERE jobname = 'daily_price_update';`
3. Revisar logs: `SELECT * FROM cron.job_run_details WHERE jobname = 'daily_price_update';`

### Función Edge Falla
1. Verificar que la función esté desplegada
2. Revisar logs de la función edge en Supabase Dashboard
3. Verificar variables de entorno

### Notificaciones No Funcionan
1. Verificar API keys de SendGrid/Twilio
2. Revisar configuración de destinatarios
3. Verificar templates de email

## Métricas de Rendimiento

- **Tiempo de ejecución por job**
- **Tasa de éxito/fallo**
- **Volumen de productos procesados**
- **Cambios de precios detectados**
- **Alertas enviadas**

## Backup y Recuperación

Los logs de ejecución se mantienen en `cron_jobs_execution_log` con retención de 30 días por defecto.

Para backup completo:
```sql
-- Backup de configuración
COPY cron.job TO '/backup/cron_jobs.csv' CSV HEADER;

-- Backup de logs
COPY cron.job_run_details TO '/backup/cron_run_details.csv' CSV HEADER;
```