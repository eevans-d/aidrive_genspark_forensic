#!/bin/bash
# =================================================================
# SCRIPT DE DEPLOYMENT - SISTEMA INVENTARIO RETAIL
# =================================================================
# Script para deployment automatizado del sistema completo

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.production"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.production.yml"

# Función de ayuda
show_help() {
    cat << EOF
🚀 Script de Deployment - Sistema Inventario Retail

Uso: $0 [OPCIÓN]

OPCIONES:
    -h, --help          Mostrar esta ayuda
    -c, --check         Verificar prerrequisitos
    -b, --build         Solo construir imágenes
    -u, --up            Levantar servicios
    -d, --down          Detener servicios
    -r, --restart       Reiniciar servicios
    -l, --logs          Mostrar logs
    -s, --status        Mostrar estado de servicios
    --backup            Realizar backup de base de datos
    --restore [FILE]    Restaurar backup de base de datos

EJEMPLOS:
    $0 --check          # Verificar que todo esté listo
    $0 --build          # Construir imágenes Docker
    $0 --up             # Desplegar sistema completo
    $0 --logs           # Ver logs en tiempo real
    $0 --backup         # Crear backup de DB

EOF
}

# Verificar prerrequisitos
check_prerequisites() {
    log_info "Verificando prerrequisitos..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    log_success "Docker instalado: $(docker --version)"
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi
    log_success "Docker Compose instalado: $(docker-compose --version)"
    
    # Archivo de entorno
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Archivo .env.production no encontrado"
        log_info "Copiando template..."
        cp "${PROJECT_DIR}/.env.production.template" "$ENV_FILE"
        log_warning "⚠️  IMPORTANTE: Editar $ENV_FILE con valores reales antes de continuar"
        exit 1
    fi
    log_success "Archivo de entorno encontrado"
    
    # Docker Compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Archivo docker-compose.production.yml no encontrado"
        exit 1
    fi
    log_success "Docker Compose file encontrado"
    
    # Crear directorios necesarios
    mkdir -p "${PROJECT_DIR}/logs"
    mkdir -p "${PROJECT_DIR}/models"
    mkdir -p "${PROJECT_DIR}/data"
    mkdir -p "${PROJECT_DIR}/backups"
    log_success "Directorios creados"
    
    log_success "Todos los prerrequisitos están cumplidos"
}

# Construir imágenes
build_images() {
    log_info "Construyendo imágenes Docker..."
    cd "$PROJECT_DIR"
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    
    log_success "Imágenes construidas exitosamente"
}

# Levantar servicios
deploy_up() {
    log_info "Desplegando servicios..."
    cd "$PROJECT_DIR"
    
    # Verificar que no haya servicios corriendo
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_warning "Hay servicios corriendo. Deteniendo primero..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    fi
    
    # Levantar servicios
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Esperar a que los servicios estén listos
    log_info "Esperando a que los servicios estén disponibles..."
    sleep 30
    
    # Verificar health checks
    check_health
    
    log_success "Deployment completado"
    show_urls
}

# Verificar salud de servicios
check_health() {
    log_info "Verificando salud de servicios..."
    
    local services=(
        "http://localhost:8001/health:Agente Depósito"
        "http://localhost:8002/health:Agente Negocio"
        "http://localhost:8003/health:ML Service"
        "http://localhost:8080/health:Dashboard"
        "http://localhost/health:Nginx"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        if curl -sf "$url" > /dev/null; then
            log_success "$name está saludable"
        else
            log_error "$name no responde en $url"
        fi
    done
}

# Mostrar URLs del sistema
show_urls() {
    log_info "Sistema desplegado exitosamente!"
    echo ""
    echo "🌐 URLs disponibles:"
    echo "   Dashboard Principal: http://localhost"
    echo "   Agente Depósito API: http://localhost/api/deposito/"
    echo "   Agente Negocio API:  http://localhost/api/negocio/"
    echo "   ML Service API:      http://localhost/api/ml/"
    echo ""
    echo "🔧 URLs directas (para debugging):"
    echo "   Dashboard:      http://localhost:8080"
    echo "   Agente Depósito: http://localhost:8001"
    echo "   Agente Negocio:  http://localhost:8002"
    echo "   ML Service:      http://localhost:8003"
    echo ""
}

# Detener servicios
deploy_down() {
    log_info "Deteniendo servicios..."
    cd "$PROJECT_DIR"
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    log_success "Servicios detenidos"
}

# Reiniciar servicios
restart_services() {
    log_info "Reiniciando servicios..."
    deploy_down
    sleep 5
    deploy_up
}

# Mostrar logs
show_logs() {
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
}

# Mostrar estado
show_status() {
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo ""
    check_health
}

# Backup de base de datos
backup_database() {
    log_info "Realizando backup de base de datos..."
    
    local backup_file="${PROJECT_DIR}/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker exec inventario_retail_db pg_dump -U postgres inventario_retail > "$backup_file"
    
    log_success "Backup guardado en: $backup_file"
}

# Restaurar backup
restore_database() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Archivo de backup no encontrado: $backup_file"
        exit 1
    fi
    
    log_info "Restaurando backup: $backup_file"
    log_warning "⚠️  Esto sobrescribirá la base de datos actual"
    
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operación cancelada"
        exit 0
    fi
    
    docker exec -i inventario_retail_db psql -U postgres inventario_retail < "$backup_file"
    
    log_success "Backup restaurado exitosamente"
}

# Parsing de argumentos
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    -c|--check)
        check_prerequisites
        ;;
    -b|--build)
        check_prerequisites
        build_images
        ;;
    -u|--up)
        check_prerequisites
        build_images
        deploy_up
        ;;
    -d|--down)
        deploy_down
        ;;
    -r|--restart)
        restart_services
        ;;
    -l|--logs)
        show_logs
        ;;
    -s|--status)
        show_status
        ;;
    --backup)
        backup_database
        ;;
    --restore)
        if [[ -z "${2:-}" ]]; then
            log_error "Se requiere especificar el archivo de backup"
            show_help
            exit 1
        fi
        restore_database "$2"
        ;;
    "")
        log_error "Se requiere una opción"
        show_help
        exit 1
        ;;
    *)
        log_error "Opción desconocida: $1"
        show_help
        exit 1
        ;;
esac