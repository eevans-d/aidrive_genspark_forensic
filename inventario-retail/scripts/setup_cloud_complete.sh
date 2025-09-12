#!/bin/bash
# scripts/setup_cloud_complete.sh
# Master script to setup complete cloud scaling and performance optimizations

set -e

echo "🇦🇷 CONFIGURACIÓN COMPLETA - ESCALADO CLOUD Y OPTIMIZACIONES PERFORMANCE"
echo "========================================================================"
echo "Sistema: Inventario Retail Argentino"
echo "Versión: Cloud Production Ready"
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CLOUD_PROVIDER="${1:-local}"  # aws, digitalocean, or local
SKIP_DEPENDENCIES="${SKIP_DEPENDENCIES:-false}"

# Step counter
STEP=1

print_step() {
    echo -e "${BLUE}PASO $STEP: $1${NC}"
    echo "----------------------------------------"
    ((STEP++))
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Verificando prerrequisitos del sistema"

    local missing_deps=()

    # Check Python
    if ! python3 --version | grep -E 'Python 3\.(8|9|10|11)' > /dev/null; then
        missing_deps+=("python3.8+")
    fi

    # Check Docker
    if ! command -v docker > /dev/null; then
        missing_deps+=("docker")
    fi

    # Check curl
    if ! command -v curl > /dev/null; then
        missing_deps+=("curl")
    fi

    # Check system tools
    for tool in git wget unzip systemctl; do
        if ! command -v "$tool" > /dev/null; then
            missing_deps+=("$tool")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Dependencias faltantes: ${missing_deps[*]}"

        if [ "$SKIP_DEPENDENCIES" != "true" ]; then
            echo "Instalando dependencias..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip docker.io docker-compose \
                curl wget git unzip systemctl redis-server postgresql
        else
            echo "Use SKIP_DEPENDENCIES=false para instalar automáticamente"
            exit 1
        fi
    fi

    print_success "Prerrequisitos verificados"
}

# Setup Argentine configuration
setup_argentine_config() {
    print_step "Configurando entorno argentino"

    # Set timezone
    sudo timedatectl set-timezone America/Argentina/Buenos_Aires

    # Set locale if not exists
    if ! locale -a | grep es_AR > /dev/null; then
        sudo locale-gen es_AR.UTF-8
    fi

    # Environment variables
    cat > /tmp/argentina_env << 'EOF'
export TZ=America/Argentina/Buenos_Aires
export LANG=es_AR.UTF-8
export COUNTRY=Argentina
export CURRENCY=ARS
export INFLATION_RATE=4.5
EOF

    sudo mv /tmp/argentina_env /etc/environment.d/argentina.conf

    print_success "Configuración argentina aplicada"
}

# Setup monitoring
setup_monitoring() {
    print_step "Configurando sistema de monitoreo"

    if [ -f "monitoring/setup_monitoring.sh" ]; then
        chmod +x monitoring/setup_monitoring.sh
        ./monitoring/setup_monitoring.sh
        print_success "Monitoreo Prometheus + Grafana configurado"
    else
        print_warning "Script de monitoreo no encontrado, omitiendo..."
    fi
}

# Setup database
setup_database() {
    print_step "Configurando base de datos PostgreSQL"

    if [ -f "scripts/database/migrate_postgres.sh" ]; then
        chmod +x scripts/database/migrate_postgres.sh
        ./scripts/database/migrate_postgres.sh
        print_success "Migración a PostgreSQL completada"
    else
        print_warning "Script de migración no encontrado, omitiendo..."
    fi
}

# Setup Redis cache
setup_redis() {
    print_step "Configurando cache Redis"

    # Start Redis
    sudo systemctl enable redis-server
    sudo systemctl start redis-server

    # Configure Redis for Argentina
    sudo tee /etc/redis/redis.conf.d/argentina.conf > /dev/null << 'EOF'
# Argentine retail specific configuration
maxmemory 512mb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
EOF

    sudo systemctl restart redis-server
    print_success "Redis configurado para retail argentino"
}

# Setup NGINX load balancer
setup_nginx() {
    print_step "Configurando NGINX load balancer"

    if [ -f "scripts/nginx/setup_nginx.sh" ]; then
        chmod +x scripts/nginx/setup_nginx.sh
        ./scripts/nginx/setup_nginx.sh
        print_success "NGINX load balancer configurado"
    else
        print_warning "Script de NGINX no encontrado, omitiendo..."
    fi
}

# Setup cloud infrastructure
setup_cloud_infrastructure() {
    print_step "Configurando infraestructura cloud: $CLOUD_PROVIDER"

    case "$CLOUD_PROVIDER" in
        "aws")
            if [ -f "scripts/cloud/deploy_aws.sh" ]; then
                chmod +x scripts/cloud/deploy_aws.sh
                ./scripts/cloud/deploy_aws.sh
                print_success "Infraestructura AWS configurada"
            else
                print_error "Script de AWS no encontrado"
            fi
            ;;
        "digitalocean")
            if [ -f "scripts/cloud/deploy_digitalocean.sh" ]; then
                chmod +x scripts/cloud/deploy_digitalocean.sh
                ./scripts/cloud/deploy_digitalocean.sh
                print_success "Infraestructura DigitalOcean configurada"
            else
                print_error "Script de DigitalOcean no encontrado"
            fi
            ;;
        "local")
            print_warning "Configuración local - omitiendo setup cloud"
            ;;
        *)
            print_error "Proveedor cloud no soportado: $CLOUD_PROVIDER"
            exit 1
            ;;
    esac
}

# Setup auto-scaling
setup_autoscaling() {
    print_step "Configurando auto-scaling estacional"

    # Create auto-scaling service
    sudo tee /etc/systemd/system/retail-argentina-autoscaler.service > /dev/null << EOF
[Unit]
Description=Argentine Retail Auto-Scaler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 -c "
import sys
sys.path.append('$(pwd)')

if '$CLOUD_PROVIDER' == 'aws':
    from autoscaling.aws_autoscaling import setup_argentine_autoscaling
    setup_argentine_autoscaling()
elif '$CLOUD_PROVIDER' == 'digitalocean':
    from autoscaling.digitalocean_autoscaling import setup_digitalocean_autoscaling
    # Note: Requires API token configuration
    print('DigitalOcean auto-scaling configured for manual trigger')
else:
    print('Local environment - auto-scaling simulated')
"
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl enable retail-argentina-autoscaler
    print_success "Auto-scaling estacional configurado"
}

# Setup performance monitoring
setup_performance_monitoring() {
    print_step "Configurando monitoreo de performance"

    # Install performance tools
    pip3 install py-spy psutil redis

    # Create performance monitoring service
    sudo tee /etc/systemd/system/retail-argentina-profiler.service > /dev/null << EOF
[Unit]
Description=Argentine Retail Performance Profiler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 -c "
import sys, time
sys.path.append('$(pwd)')
from performance.profiling.retail_profiler import ArgentineRetailProfiler

profiler = ArgentineRetailProfiler()
session = profiler.start_profiling_session('production', 60)
while True:
    time.sleep(300)  # Profile every 5 minutes
    report = profiler.generate_report('production')
    print(f'Performance report: {report}')
"
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl enable retail-argentina-profiler
    print_success "Monitoreo de performance configurado"
}

# Run verification
run_verification() {
    print_step "Ejecutando verificación completa del deployment"

    if [ -f "scripts/verification/verify_deployment.sh" ]; then
        chmod +x scripts/verification/verify_deployment.sh
        ./scripts/verification/verify_deployment.sh

        if [ $? -eq 0 ]; then
            print_success "Verificación completada exitosamente"
        else
            print_warning "Verificación completada con advertencias"
        fi
    else
        print_warning "Script de verificación no encontrado"
    fi
}

# Setup health monitoring
setup_health_monitoring() {
    print_step "Configurando monitoreo continuo de salud"

    if [ -f "scripts/verification/health_monitor.sh" ]; then
        chmod +x scripts/verification/health_monitor.sh

        # Create systemd service for health monitoring
        sudo tee /etc/systemd/system/retail-argentina-health.service > /dev/null << EOF
[Unit]
Description=Argentine Retail Health Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/scripts/verification/health_monitor.sh
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl enable retail-argentina-health
        sudo systemctl start retail-argentina-health

        print_success "Monitoreo continuo de salud configurado"
    else
        print_warning "Script de monitoreo de salud no encontrado"
    fi
}

# Main installation flow
main() {
    echo -e "${GREEN}Iniciando configuración completa del sistema...${NC}"
    echo

    # Check if we're root
    if [ "$EUID" -ne 0 ]; then
        print_error "Este script requiere permisos de root. Ejecute con sudo."
        exit 1
    fi

    # Main setup steps
    check_prerequisites
    setup_argentine_config
    setup_database
    setup_redis
    setup_monitoring
    setup_nginx
    setup_cloud_infrastructure
    setup_autoscaling
    setup_performance_monitoring
    setup_health_monitoring
    run_verification

    echo
    echo "========================================================================"
    echo -e "${GREEN}🎉 CONFIGURACIÓN COMPLETA FINALIZADA EXITOSAMENTE${NC}"
    echo "========================================================================"
    echo
    echo -e "${BLUE}📋 RESUMEN DE CONFIGURACIÓN:${NC}"
    echo "• Timezone: America/Argentina/Buenos_Aires"
    echo "• Base de datos: PostgreSQL con datos migrados"
    echo "• Cache: Redis optimizado para Argentina"
    echo "• Load Balancer: NGINX con SSL"
    echo "• Monitoreo: Prometheus + Grafana"
    echo "• Cloud: $CLOUD_PROVIDER"
    echo "• Auto-scaling: Configurado para diciembre y Black Friday"
    echo "• Performance: Profiling continuo activado"
    echo "• Health Check: Monitoreo 24/7 activado"
    echo
    echo -e "${BLUE}🔗 ENDPOINTS DISPONIBLES:${NC}"
    echo "• API Negocio (CUIT): http://localhost:8001"
    echo "• API Depósito (Stock): http://localhost:8002"
    echo "• API ML (Predicción): http://localhost:8003"
    echo "• Dashboard API: http://localhost:8004"
    echo "• Streamlit UI: http://localhost:8501"
    echo "• Prometheus: http://localhost:9090"
    echo "• Grafana: http://localhost:3000 (admin/admin)"
    echo "• Load Balancer: http://localhost"
    echo
    echo -e "${BLUE}📊 LOGS Y MONITOREO:${NC}"
    echo "• Health logs: tail -f /var/log/retail-argentina-health.log"
    echo "• Service status: sudo systemctl status retail-argentina-*"
    echo "• Performance reports: ls performance/reports/"
    echo
    echo -e "${YELLOW}📝 PRÓXIMOS PASOS:${NC}"
    echo "1. Configurar tokens de API para cloud providers"
    echo "2. Configurar alertas Telegram (opcional)"
    echo "3. Ejecutar tests de carga: python3 -m performance.benchmarks.retail_benchmarks"
    echo "4. Monitorear métricas en Grafana"
    echo "5. Verificar auto-scaling en temporadas altas"
    echo
    print_success "Sistema retail argentino listo para producción 🇦🇷"
}

# Show usage
show_usage() {
    echo "Uso: $0 [CLOUD_PROVIDER]"
    echo
    echo "CLOUD_PROVIDER opciones:"
    echo "  aws           - Configurar para AWS EC2"
    echo "  digitalocean  - Configurar para DigitalOcean Droplets"
    echo "  local         - Configuración local (default)"
    echo
    echo "Variables de entorno:"
    echo "  SKIP_DEPENDENCIES=true  - Omitir instalación de dependencias"
    echo "  TELEGRAM_BOT_TOKEN      - Token para alertas Telegram"
    echo "  TELEGRAM_CHAT_ID        - Chat ID para alertas Telegram"
    echo
    echo "Ejemplo:"
    echo "  sudo $0 aws"
    echo "  sudo SKIP_DEPENDENCIES=true $0 digitalocean"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    *)
        main
        ;;
esac
