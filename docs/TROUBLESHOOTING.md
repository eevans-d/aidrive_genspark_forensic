# TROUBLESHOOTING Y MANTENIMIENTO - SISTEMA INVENTARIO RETAIL
## Resultado de aplicar PROMPT 4 con GitHub Copilot Pro

---

## 1. PROBLEMAS COMUNES DE DESPLIEGUE

### Top 5 Errores Más Probables Durante Deployment

#### Error #1: Fallo de Conexión a Base de Datos PostgreSQL
**Síntomas:**
```bash
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
FATAL: password authentication failed for user "postgres"
could not connect to server: Connection refused
```

**Diagnóstico Específico:**
```bash
# 1. Verificar conectividad básica
pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER

# 2. Test conexión manual
psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"

# 3. Verificar logs PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log

# 4. Validar formato DATABASE_URL
echo $DATABASE_URL | grep -E "^postgresql://[^:]+:[^@]+@[^:]+:[0-9]+/[^?]+(\?.*)?"
```

**Solución Paso a Paso:**
```bash
#!/bin/bash
# fix-database-connection.sh

# Verificar y corregir configuración
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL no configurada"
    echo "Configure: export DATABASE_URL='postgresql://user:pass@host:5432/db'"
    exit 1
fi

# Verificar disponibilidad del servidor
if ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT; then
    echo "❌ PostgreSQL server no disponible"
    echo "Verificar que PostgreSQL esté ejecutándose"
    exit 1
fi

# Crear base de datos si no existe
createdb -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB 2>/dev/null || true

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
cd /app && alembic upgrade head

echo "✅ Base de datos configurada correctamente"
```

---

#### Error #2: API OpenAI Rate Limit o Quota Exceeded
**Síntomas:**
```bash
openai.error.RateLimitError: You exceeded your current quota
openai.error.AuthenticationError: Incorrect API key provided
HTTP 429: Too Many Requests
```

**Diagnóstico Específico:**
```bash
# 1. Verificar formato API key
echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]{48}$" && echo "✅ Format OK" || echo "❌ Invalid format"

# 2. Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models | jq '.data[0].id' || echo "❌ API call failed"

# 3. Verificar usage y billing
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/usage \
  -G -d "date=$(date -d '30 days ago' '+%Y-%m-%d')" | jq '.total_usage'
```

**Solución Paso a Paso:**
```bash
#!/bin/bash
# fix-openai-issues.sh

# Configurar fallback a EasyOCR cuando OpenAI falla
cat > /app/agente_negocio/ocr/fallback_config.py << 'EOF'
FALLBACK_CONFIG = {
    'ocr_fallback_enabled': True,
    'primary_engine': 'openai',
    'fallback_engines': ['easyocr', 'tesseract'],
    'circuit_breaker': {
        'failure_threshold': 3,
        'recovery_timeout': 300,
        'half_open_max_calls': 5
    }
}
EOF

# Implementar circuit breaker para OpenAI
echo "Habilitando circuit breaker para OpenAI..."
export OCR_FALLBACK_ENABLED=true
export OPENAI_CIRCUIT_BREAKER_ENABLED=true

echo "✅ Fallback de OCR configurado"
```

---

#### Error #3: Redis Connection Timeout o Memory Issues
**Síntomas:**
```bash
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'
redis.exceptions.TimeoutError: Timeout reading from socket
```

**Diagnóstico Específico:**
```bash
# 1. Test conectividad Redis
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" ping

# 2. Verificar memoria disponible
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" info memory | grep used_memory_human

# 3. Verificar configuración maxmemory
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" config get maxmemory

# 4. Test pool connections
python -c "
import redis
pool = redis.ConnectionPool.from_url('$REDIS_URL', max_connections=20)
r = redis.Redis(connection_pool=pool)
print('✅ Redis pool OK:', r.ping())
"
```

**Solución Paso a Paso:**
```bash
#!/bin/bash
# fix-redis-issues.sh

# Optimizar configuración Redis para producción
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" config set maxmemory 256mb
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" config set maxmemory-policy allkeys-lru

# Limpiar keys antiguas si es necesario
echo "Limpiando cache antiguo..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" eval "
local keys = redis.call('KEYS', 'retail:cache:*')
local deleted = 0
for i=1,#keys do
    local ttl = redis.call('TTL', keys[i])
    if ttl == -1 then
        redis.call('EXPIRE', keys[i], 3600)
        deleted = deleted + 1
    end
end
return deleted
" 0

echo "✅ Redis optimizado para producción"
```

---

## 2. COMANDOS DE MANTENIMIENTO ESENCIALES

### Health Check Completo del Sistema
```bash
#!/bin/bash
# health-check-complete.sh - Sistema Inventario Retail

echo "🔍 HEALTH CHECK COMPLETO - Sistema Inventario Retail"
echo "======================================================"

# Arrays para tracking
SERVICES=("agente-negocio:8001" "agente-deposito:8002" "ml-service:8003" "dashboard:5000")
FAILED_SERVICES=()
WARNINGS=()

# 1. Verificar servicios core
echo "📊 Verificando servicios principales..."
for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    
    if curl -f -s -m 10 "http://localhost:$port/health" >/dev/null 2>&1; then
        response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://localhost:$port/health")
        if (( $(echo "$response_time > 2.0" | bc -l) )); then
            echo "⚠️  $service_name: SLOW (${response_time}s)"
            WARNINGS+=("$service_name response time: ${response_time}s")
        else
            echo "✅ $service_name: HEALTHY"
        fi
    else
        echo "❌ $service_name: UNHEALTHY"
        FAILED_SERVICES+=("$service_name")
    fi
done

# 2. Verificar base de datos
echo "🗄️ Verificando PostgreSQL..."
python -c "
from shared.database import engine
from sqlalchemy import text
import sys

try:
    connection = engine.connect()
    result = connection.execute(text('SELECT COUNT(*) FROM products')).fetchone()
    active_connections = connection.execute(text('''
        SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
    ''')).fetchone()
    
    print(f'✅ PostgreSQL: CONNECTED')
    print(f'   Products: {result[0]}')
    print(f'   Active connections: {active_connections[0]}')
    
    connection.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ PostgreSQL: ERROR - {str(e)}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    FAILED_SERVICES+=("postgresql")
fi

# 3. Verificar Redis
echo "💾 Verificando Redis..."
if redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" ping >/dev/null 2>&1; then
    MEMORY_INFO=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" info memory | grep used_memory_human)
    CONNECTED_CLIENTS=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a "$REDIS_PASSWORD" info clients | grep connected_clients)
    echo "✅ Redis: CONNECTED"
    echo "   $MEMORY_INFO"
    echo "   $CONNECTED_CLIENTS"
else
    echo "❌ Redis: DISCONNECTED"
    FAILED_SERVICES+=("redis")
fi

# 4. Verificar APIs externas críticas
echo "🌐 Verificando APIs externas..."

# OpenAI API
if [ -n "$OPENAI_API_KEY" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1}' \
        "https://api.openai.com/v1/chat/completions")
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "✅ OpenAI API: ACCESSIBLE"
    else
        echo "⚠️ OpenAI API: ERROR (HTTP $HTTP_CODE)"
        WARNINGS+=("OpenAI API HTTP $HTTP_CODE")
    fi
else
    echo "⚠️ OpenAI API: NOT CONFIGURED"
fi

# 5. Verificar recursos del sistema
echo "⚡ Verificando recursos del sistema..."
if command -v free >/dev/null; then
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "📊 Memoria utilizada: ${MEMORY_USAGE}%"
    if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
        WARNINGS+=("High memory usage: ${MEMORY_USAGE}%")
    fi
fi

if command -v df >/dev/null; then
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo "💿 Disco utilizado: ${DISK_USAGE}%"
    if [ "$DISK_USAGE" -gt 85 ]; then
        WARNINGS+=("High disk usage: ${DISK_USAGE}%")
    fi
fi

# 6. Resumen final
echo "======================================================"
if [ ${#FAILED_SERVICES[@]} -eq 0 ] && [ ${#WARNINGS[@]} -eq 0 ]; then
    echo "🎯 RESULTADO: SISTEMA COMPLETAMENTE SALUDABLE"
    exit 0
elif [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo "⚠️  RESULTADO: SISTEMA FUNCIONAL CON ADVERTENCIAS"
    printf '%s\n' "${WARNINGS[@]}"
    exit 1
else
    echo "🚨 RESULTADO: PROBLEMAS CRÍTICOS DETECTADOS"
    echo "Servicios fallidos: ${FAILED_SERVICES[*]}"
    printf 'Advertencias: %s\n' "${WARNINGS[@]}"
    exit 2
fi
```

### Restart Inteligente de Servicios
```bash
#!/bin/bash
# restart-services.sh - Sistema Inventario Retail

SERVICE_NAME=${1:-"all"}

restart_service() {
    local service=$1
    local port=$2
    local max_wait=${3:-30}
    
    echo "🔄 Reiniciando $service..."
    
    if command -v docker-compose >/dev/null && [ -f "docker-compose.production.yml" ]; then
        # Docker Compose deployment
        docker-compose -f docker-compose.production.yml restart $service
        
        # Wait for service to be ready
        local count=0
        while [ $count -lt $max_wait ]; do
            if curl -f -s "http://localhost:$port/health" >/dev/null 2>&1; then
                echo "✅ $service reiniciado exitosamente"
                return 0
            fi
            sleep 2
            ((count += 2))
        done
        
        echo "❌ $service no respondió después de ${max_wait}s"
        docker-compose -f docker-compose.production.yml logs --tail=20 $service
        return 1
        
    elif command -v systemctl >/dev/null; then
        # Systemd deployment
        sudo systemctl restart "inventario-$service"
        sleep 5
        
        if systemctl is-active --quiet "inventario-$service"; then
            echo "✅ $service reiniciado exitosamente"
            return 0
        else
            echo "❌ $service falló al reiniciar"
            sudo systemctl status "inventario-$service"
            return 1
        fi
    else
        echo "❌ No se pudo determinar método de restart para $service"
        return 1
    fi
}

case $SERVICE_NAME in
    "agente-negocio")
        restart_service "agente-negocio" 8001
        ;;
    "agente-deposito")
        restart_service "agente-deposito" 8002
        ;;
    "ml-service")
        restart_service "ml-service" 8003
        ;;
    "dashboard")
        restart_service "dashboard" 5000
        ;;
    "all")
        echo "🔄 Reiniciando todos los servicios del Sistema Inventario Retail..."
        restart_service "agente-deposito" 8002 60  # Base first
        sleep 5
        restart_service "agente-negocio" 8001 60   # Business logic
        sleep 5
        restart_service "ml-service" 8003 90       # ML takes longer
        sleep 5
        restart_service "dashboard" 5000 30        # Dashboard last
        echo "🎯 Reinicio completo finalizado"
        ;;
    *)
        echo "❌ Servicio desconocido: $SERVICE_NAME"
        echo "Servicios disponibles: agente-negocio, agente-deposito, ml-service, dashboard, all"
        exit 1
        ;;
esac
```

---

## 3. SCRIPTS DE AUTOMATIZACIÓN

### Deployment Completo Automatizado
```bash
#!/bin/bash
# deploy-complete.sh - Sistema Inventario Retail

set -euo pipefail

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.production"
BACKUP_DIR="${PROJECT_DIR}/backups/$(date +%Y%m%d-%H%M)"

# Logging functions
log_info() { echo -e "\033[34mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }
log_error() { echo -e "\033[31m❌ $1\033[0m"; }

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Ejecutando verificaciones pre-deployment..."
    
    # Check required files
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Archivo .env.production no encontrado"
        exit 1
    fi
    
    # Check required environment variables
    source "$ENV_FILE"
    required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Variable requerida $var no está configurada"
            exit 1
        fi
    done
    
    # Check database connectivity
    if ! pg_isready -d "$DATABASE_URL" -t 10; then
        log_error "No se puede conectar a la base de datos"
        exit 1
    fi
    
    # Check Redis connectivity
    if ! redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
        log_error "No se puede conectar a Redis"
        exit 1
    fi
    
    log_success "Todas las verificaciones pre-deployment pasaron"
}

# Create backup
create_backup() {
    log_info "Creando backup del sistema actual..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/database_backup.sql"
    
    # Backup configuration
    cp "$ENV_FILE" "$BACKUP_DIR/"
    
    # Backup current codebase
    git rev-parse HEAD > "$BACKUP_DIR/git_commit.txt"
    
    log_success "Backup creado en: $BACKUP_DIR"
}

# Deploy application
deploy_application() {
    log_info "Desplegando aplicación..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest changes
    git pull origin main
    
    # Update dependencies
    pip install -r requirements_final.txt --no-cache-dir
    
    # Run database migrations
    alembic upgrade head
    
    # Restart services
    if command -v docker-compose >/dev/null; then
        docker-compose -f docker-compose.production.yml up -d --build
    elif command -v systemctl >/dev/null; then
        sudo systemctl restart inventario-agente-deposito
        sudo systemctl restart inventario-agente-negocio
        sudo systemctl restart inventario-ml-service
        sudo systemctl restart inventario-dashboard
    fi
    
    log_success "Aplicación desplegada exitosamente"
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Ejecutando verificación post-deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Run health checks
    if ./scripts/health-check-complete.sh; then
        log_success "Verificación post-deployment exitosa"
    else
        log_error "Verificación post-deployment falló"
        log_warning "Considere ejecutar rollback: ./scripts/rollback.sh $BACKUP_DIR"
        exit 1
    fi
}

# Main deployment process
main() {
    log_info "🚀 Iniciando deployment completo del Sistema Inventario Retail"
    
    pre_deployment_checks
    create_backup
    deploy_application
    post_deployment_verification
    
    log_success "🎯 Deployment completo exitoso!"
    log_info "Backup disponible en: $BACKUP_DIR"
}

# Execute main function
main "$@"
```

Este sistema de troubleshooting proporciona herramientas completas y específicas para mantener el Sistema Inventario Retail funcionando óptimamente en producción, con énfasis en problemas reales de sistemas multi-agente con IA.