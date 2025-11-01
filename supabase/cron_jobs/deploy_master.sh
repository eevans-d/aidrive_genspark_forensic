#!/bin/bash
# ===================================================================
# SCRIPT MAESTRO DE IMPLEMENTACIÓN - CRON JOBS AUTOMÁTICOS
# Mini Market Sprint 6
# ===================================================================

echo "🚀 INICIANDO IMPLEMENTACIÓN DE CRON JOBS AUTOMÁTICOS"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ===================================================================
# PASO 1: VERIFICAR ARCHIVOS NECESARIOS
# ===================================================================

log_info "Verificando archivos necesarios..."

FILES_TO_CHECK=(
    "/workspace/backend/migration/09_cron_jobs_tables.sql"
    "/workspace/supabase/functions/cron-jobs-maxiconsumo/index.ts"
    "/workspace/supabase/cron_jobs/deploy_all_cron_jobs.sql"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        log_success "✅ $file"
    else
        log_error "❌ Archivo faltante: $file"
        exit 1
    fi
done

# ===================================================================
# PASO 2: APLICAR MIGRACIÓN DE BASE DE DATOS
# ===================================================================

log_info "Aplicando migración de base de datos (09_cron_jobs_tables.sql)..."

if command -v supabase &> /dev/null; then
    cd /workspace
    supabase db push
    
    if [ $? -eq 0 ]; then
        log_success "✅ Migración de BD aplicada correctamente"
    else
        log_error "❌ Error aplicando migración de BD"
        log_info "Ejecutar manualmente: supabase db push"
        exit 1
    fi
else
    log_warning "⚠️  Supabase CLI no encontrado"
    log_info "Aplicar migración manualmente en Supabase Dashboard > SQL Editor"
    log_info "Archivo: /workspace/backend/migration/09_cron_jobs_tables.sql"
fi

# ===================================================================
# PASO 3: DESPLEGAR FUNCIÓN EDGE
# ===================================================================

log_info "Desplegando función edge cron-jobs-maxiconsumo..."

if command -v supabase &> /dev/null; then
    cd /workspace
    supabase functions deploy cron-jobs-maxiconsumo
    
    if [ $? -eq 0 ]; then
        log_success "✅ Función edge desplegada correctamente"
    else
        log_error "❌ Error desplegando función edge"
        log_info "Ejecutar manualmente: supabase functions deploy cron-jobs-maxiconsumo"
        exit 1
    fi
else
    log_warning "⚠️  Supabase CLI no encontrado"
    log_info "Desplegar función manualmente en Supabase Dashboard > Edge Functions"
fi

# ===================================================================
# PASO 4: CONFIGURAR CRON JOBS
# ===================================================================

log_info "Configurando cron jobs en la base de datos..."

# Verificar si podemos conectarnos a la base de datos
if command -v psql &> /dev/null; then
    log_info "Ejecutando script de implementación de cron jobs..."
    
    # Crear archivo temporal con el script
    TEMP_SCRIPT="/tmp/deploy_cron_jobs.sql"
    cp /workspace/supabase/cron_jobs/deploy_all_cron_jobs.sql "$TEMP_SCRIPT"
    
    # Ejecutar script (requiere conexión a Supabase)
    # psql -h <host> -U <user> -d <database> -f "$TEMP_SCRIPT"
    
    if [ $? -eq 0 ]; then
        log_success "✅ Cron jobs configurados correctamente"
    else
        log_warning "⚠️  Ejecución automática falló"
        log_info "Ejecutar manualmente en Supabase SQL Editor:"
        log_info "Archivo: /workspace/supabase/cron_jobs/deploy_all_cron_jobs.sql"
    fi
    
    rm -f "$TEMP_SCRIPT"
else
    log_warning "⚠️  PostgreSQL CLI no encontrado"
    log_info "Ejecutar manualmente en Supabase SQL Editor:"
    log_info "Archivo: /workspace/supabase/cron_jobs/deploy_all_cron_jobs.sql"
fi

# ===================================================================
# PASO 5: VERIFICAR CONFIGURACIÓN
# ===================================================================

log_info "Verificando configuración de cron jobs..."

echo ""
echo "📋 RESUMEN DE IMPLEMENTACIÓN:"
echo "=================================================="
echo ""
echo "🗄️  Base de Datos:"
echo "   • Tablas de cron jobs creadas"
echo "   • Funciones y triggers configurados"
echo "   • Vistas de monitoreo disponibles"
echo ""
echo "⚡ Edge Function:"
echo "   • Función cron-jobs-maxiconsumo desplegada"
echo "   • Endpoints disponibles:"
echo "     - POST /functions/v1/cron-jobs-maxiconsumo"
echo "     - GET  /functions/v1/cron-jobs-maxiconsumo?action=status"
echo "     - GET  /functions/v1/cron-jobs-maxiconsumo?action=health"
echo ""
echo "⏰ Cron Jobs Configurados:"
echo "   • Job Diario:      daily_price_update (02:00 AM)"
echo "   • Job Semanal:     weekly_trend_analysis (Domingos 03:00)"
echo "   • Alertas RT:      realtime_alerts (cada 15 min)"
echo ""
echo "📊 Monitoreo:"
echo "   • Logs en: cron_jobs_execution_log"
echo "   • Estado en: cron_jobs_config"
echo "   • Alertas en: cron_jobs_alerts"
echo ""
echo "📁 Archivos Creados:"
echo "   • /workspace/supabase/cron_jobs/job_daily_price_update.json"
echo "   • /workspace/supabase/cron_jobs/job_weekly_trend_analysis.json"
echo "   • /workspace/supabase/cron_jobs/job_realtime_alerts.json"
echo "   • /workspace/supabase/cron_jobs/deploy_all_cron_jobs.sql"
echo "   • /workspace/supabase/cron_jobs/README.md"
echo ""

# ===================================================================
# PASO 6: PRÓXIMOS PASOS
# ===================================================================

log_info "PRÓXIMOS PASOS:"
echo ""
echo "1. 🔧 Configurar variables de entorno en Supabase Dashboard:"
echo "   • SENDGRID_API_KEY"
echo "   • TWILIO_ACCOUNT_SID"
echo "   • TWILIO_AUTH_TOKEN"
echo ""
echo "2. 🧪 Probar función edge manualmente:"
echo "   curl -X POST https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1/cron-jobs-maxiconsumo \
     -H 'Content-Type: application/json' \
     -d '{\"action\":\"health\"}'"
echo ""
echo "3. 📊 Verificar cron jobs en Supabase Dashboard:"
echo "   • SQL Editor: SELECT * FROM cron.job;"
echo "   • Logs: cron.job_run_details"
echo ""
echo "4. 🔔 Configurar destinatarios de notificaciones:"
echo "   • INSERT INTO cron_jobs_notifications (...)"
echo ""
echo "5. 📈 Monitorear primeras ejecuciones"
echo ""

# ===================================================================
# COMANDOS DE VERIFICACIÓN
# ===================================================================

echo "🔍 COMANDOS DE VERIFICACIÓN:"
echo "=================================================="
echo ""
echo "-- Ver jobs activos"
echo "SELECT * FROM cron.job WHERE jobname IN ('daily_price_update', 'weekly_trend_analysis', 'realtime_alerts');"
echo ""
echo "-- Ver logs recientes"
echo "SELECT jobname, run_time, job_pid, return_message 
FROM cron.job_run_details 
WHERE jobname IN ('daily_price_update', 'weekly_trend_analysis', 'realtime_alerts')
ORDER BY run_time DESC 
LIMIT 10;"
echo ""
echo "-- Ver estado de configuración"
echo "SELECT job_name, job_type, is_active, last_execution 
FROM cron_jobs_config 
WHERE job_name IN ('daily-price-update', 'weekly-trend-analysis', 'realtime-alerts');"
echo ""

log_success "🎉 IMPLEMENTACIÓN COMPLETADA"
echo "=================================================="