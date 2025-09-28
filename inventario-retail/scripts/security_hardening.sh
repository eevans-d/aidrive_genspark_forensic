#!/bin/bash
# =================================================================
# SECURITY HARDENING SCRIPT - SISTEMA INVENTARIO RETAIL
# =================================================================
# Script para aplicar configuraciones de seguridad para producción

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}🔒 $1${NC}"
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

# Generar JWT secret seguro
generate_jwt_secret() {
    log_info "Generando JWT secret seguro..."
    
    # Generar clave de 256 bits (32 bytes)
    JWT_SECRET=$(openssl rand -hex 32)
    
    if [[ -f "$ENV_FILE" ]]; then
        # Actualizar archivo existente
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|" "$ENV_FILE"
    else
        echo "JWT_SECRET_KEY=${JWT_SECRET}" >> "$ENV_FILE"
    fi
    
    log_success "JWT secret generado y configurado"
}

# Generar API keys seguros
generate_api_keys() {
    log_info "Generando API keys seguros..."
    
    DASHBOARD_API_KEY=$(openssl rand -hex 24)
    DASHBOARD_UI_API_KEY=$(openssl rand -hex 24)
    
    if [[ -f "$ENV_FILE" ]]; then
        sed -i "s|DASHBOARD_API_KEY=.*|DASHBOARD_API_KEY=${DASHBOARD_API_KEY}|" "$ENV_FILE"
        sed -i "s|DASHBOARD_UI_API_KEY=.*|DASHBOARD_UI_API_KEY=${DASHBOARD_UI_API_KEY}|" "$ENV_FILE"
    else
        echo "DASHBOARD_API_KEY=${DASHBOARD_API_KEY}" >> "$ENV_FILE"
        echo "DASHBOARD_UI_API_KEY=${DASHBOARD_UI_API_KEY}" >> "$ENV_FILE"
    fi
    
    log_success "API keys generados y configurados"
}

# Configurar password seguro para PostgreSQL
generate_postgres_password() {
    log_info "Generando password seguro para PostgreSQL..."
    
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    if [[ -f "$ENV_FILE" ]]; then
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" "$ENV_FILE"
        # Actualizar DATABASE_URL también
        sed -i "s|DATABASE_URL=postgresql://retail_user:.*@|DATABASE_URL=postgresql://retail_user:${POSTGRES_PASSWORD}@|" "$ENV_FILE"
    else
        echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> "$ENV_FILE"
    fi
    
    log_success "Password de PostgreSQL generado"
}

# Configurar CORS restrictivo
configure_cors() {
    log_info "Configurando CORS restrictivo..."
    
    echo ""
    echo "🌐 Configuración de CORS para producción"
    echo "Ingrese los dominios permitidos (separados por coma):"
    echo "Ejemplo: https://yourdomain.com,https://api.yourdomain.com"
    read -p "Dominios CORS: " cors_domains
    
    if [[ -n "$cors_domains" && "$cors_domains" != "*" ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=${cors_domains}|" "$ENV_FILE"
            sed -i "s|DASHBOARD_CORS_ORIGINS=.*|DASHBOARD_CORS_ORIGINS=${cors_domains}|" "$ENV_FILE"
        else
            echo "CORS_ORIGINS=${cors_domains}" >> "$ENV_FILE"
            echo "DASHBOARD_CORS_ORIGINS=${cors_domains}" >> "$ENV_FILE"
        fi
        log_success "CORS configurado con dominios específicos"
    else
        log_warning "CORS no configurado - usando configuración restrictiva por defecto"
    fi
}

# Configurar hosts permitidos
configure_allowed_hosts() {
    log_info "Configurando hosts permitidos..."
    
    echo ""
    echo "🏠 Configuración de hosts de confianza"
    echo "Ingrese los hosts permitidos (separados por coma):"
    echo "Ejemplo: yourdomain.com,www.yourdomain.com,api.yourdomain.com"
    read -p "Hosts permitidos: " allowed_hosts
    
    if [[ -n "$allowed_hosts" && "$allowed_hosts" != "*" ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            sed -i "s|DASHBOARD_ALLOWED_HOSTS=.*|DASHBOARD_ALLOWED_HOSTS=${allowed_hosts}|" "$ENV_FILE"
        else
            echo "DASHBOARD_ALLOWED_HOSTS=${allowed_hosts}" >> "$ENV_FILE"
        fi
        log_success "Hosts permitidos configurados"
    else
        log_warning "Hosts permitidos no configurados"
    fi
}

# Habilitar HTTPS forzado
enable_https() {
    log_info "Configurando HTTPS..."
    
    echo ""
    echo "🔐 ¿Habilitar redirección HTTPS forzada? (y/N)"
    read -p "HTTPS forzado: " enable_https_input
    
    if [[ "$enable_https_input" =~ ^[Yy]$ ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            sed -i "s|DASHBOARD_FORCE_HTTPS=.*|DASHBOARD_FORCE_HTTPS=true|" "$ENV_FILE"
        else
            echo "DASHBOARD_FORCE_HTTPS=true" >> "$ENV_FILE"
        fi
        log_success "HTTPS forzado habilitado"
    else
        log_warning "HTTPS forzado no habilitado"
    fi
}

# Configurar logging de seguridad
configure_security_logging() {
    log_info "Configurando logging de seguridad..."
    
    if [[ -f "$ENV_FILE" ]]; then
        # Configurar logging detallado para seguridad
        sed -i "s|LOG_LEVEL=.*|LOG_LEVEL=INFO|" "$ENV_FILE"
    else
        echo "LOG_LEVEL=INFO" >> "$ENV_FILE"
    fi
    
    # Crear directorio de logs si no existe
    mkdir -p "${PROJECT_DIR}/logs"
    chmod 755 "${PROJECT_DIR}/logs"
    
    log_success "Logging de seguridad configurado"
}

# Verificar configuración final
verify_security_config() {
    log_info "Verificando configuración de seguridad..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Archivo .env.production no encontrado"
        return 1
    fi
    
    # Verificar variables críticas
    local required_vars=(
        "JWT_SECRET_KEY"
        "POSTGRES_PASSWORD"
        "DASHBOARD_API_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Variables faltantes: ${missing_vars[*]}"
        return 1
    fi
    
    # Verificar que no hay valores por defecto inseguros
    if grep -q "CHANGE_ME" "$ENV_FILE"; then
        log_warning "Encontrados valores CHANGE_ME - revisar configuración"
    fi
    
    if grep -q "allow_origins.*\*" "${PROJECT_DIR}"/*/main*.py 2>/dev/null; then
        log_warning "Encontrados CORS wildcard en código - verificar configuración"
    fi
    
    log_success "Configuración de seguridad verificada"
}

# Eliminar servicios legacy inseguros
remove_legacy_services() {
    log_info "Verificando servicios legacy..."
    
    local legacy_files=(
        "${PROJECT_DIR}/../inventario_retail_cache"
        "${PROJECT_DIR}/web_dashboard/dashboard_app_backup.py"
    )
    
    for file in "${legacy_files[@]}"; do
        if [[ -e "$file" ]]; then
            log_warning "Servicio legacy encontrado: $file"
            echo "¿Eliminar? (y/N)"
            read -p "Eliminar $file: " remove_legacy
            if [[ "$remove_legacy" =~ ^[Yy]$ ]]; then
                rm -rf "$file"
                log_success "Servicio legacy eliminado: $file"
            fi
        fi
    done
}

# Función principal
main() {
    echo ""
    log_info "=== INICIANDO HARDENING DE SEGURIDAD ==="
    echo ""
    
    # Verificar prerrequisitos
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL no está instalado"
        exit 1
    fi
    
    # Crear archivo .env.production si no existe
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Archivo .env.production no encontrado"
        if [[ -f "${PROJECT_DIR}/.env.production.template" ]]; then
            cp "${PROJECT_DIR}/.env.production.template" "$ENV_FILE"
            log_success "Archivo .env.production creado desde template"
        else
            touch "$ENV_FILE"
            log_warning "Archivo .env.production vacío creado"
        fi
    fi
    
    # Ejecutar hardening
    generate_jwt_secret
    generate_api_keys
    generate_postgres_password
    configure_cors
    configure_allowed_hosts
    enable_https
    configure_security_logging
    remove_legacy_services
    verify_security_config
    
    echo ""
    log_success "=== HARDENING DE SEGURIDAD COMPLETADO ==="
    echo ""
    log_info "Siguiente paso: ./scripts/deploy.sh --up"
    echo ""
    log_warning "⚠️  IMPORTANTE: Guardar las credenciales generadas en un lugar seguro"
    log_warning "⚠️  Archivo de configuración: $ENV_FILE"
    echo ""
}

# Mostrar ayuda
show_help() {
    cat << EOF
🔒 Script de Hardening de Seguridad - Sistema Inventario Retail

Uso: $0 [OPCIÓN]

OPCIONES:
    -h, --help          Mostrar esta ayuda
    --jwt-only          Solo generar JWT secret
    --keys-only         Solo generar API keys
    --postgres-only     Solo generar password PostgreSQL
    --verify            Solo verificar configuración actual

Este script configura:
- JWT secret seguro (256-bit)
- API keys aleatorios
- Password seguro para PostgreSQL  
- CORS restrictivo para producción
- Hosts de confianza
- HTTPS forzado (opcional)
- Logging de seguridad

EOF
}

# Parsing de argumentos
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    --jwt-only)
        generate_jwt_secret
        ;;
    --keys-only)
        generate_api_keys
        ;;
    --postgres-only)
        generate_postgres_password
        ;;
    --verify)
        verify_security_config
        ;;
    "")
        main
        ;;
    *)
        log_error "Opción desconocida: $1"
        show_help
        exit 1
        ;;
esac