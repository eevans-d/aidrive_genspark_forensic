#!/bin/bash

###############################################################################
# Script de Orquestación de Load Testing
# Ejecuta todos los tests k6 en secuencia y genera reporte consolidado
###############################################################################

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${RESULTS_DIR}/consolidated-report-${TIMESTAMP}.txt"

# Variables de entorno (pueden ser sobrescritas)
BASE_URL="${BASE_URL:-http://localhost:8080}"
API_KEY="${API_KEY:-test-api-key-dev}"

# Bandera para continuar en caso de fallo
CONTINUE_ON_FAILURE="${CONTINUE_ON_FAILURE:-false}"

###############################################################################
# Funciones
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_header "Verificando Dependencias"
    
    # Verificar k6
    if ! command -v k6 &> /dev/null; then
        print_error "k6 no está instalado"
        print_info "Instalar con: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    
    print_success "k6 instalado: $(k6 version)"
    
    # Verificar servicio disponible
    if ! curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" | grep -q "200\|401"; then
        print_error "Servicio no disponible en ${BASE_URL}"
        exit 1
    fi
    
    print_success "Servicio disponible en ${BASE_URL}"
}

create_results_dir() {
    if [ ! -d "${RESULTS_DIR}" ]; then
        mkdir -p "${RESULTS_DIR}"
        print_info "Directorio de resultados creado: ${RESULTS_DIR}"
    fi
}

run_test() {
    local test_name=$1
    local test_file=$2
    local description=$3
    
    print_header "${test_name}"
    print_info "${description}"
    print_info "Ejecutando: ${test_file}"
    
    # Ejecutar test con timeout de 10 minutos
    if timeout 600 k6 run \
        -e BASE_URL="${BASE_URL}" \
        -e API_KEY="${API_KEY}" \
        "${SCRIPT_DIR}/${test_file}" 2>&1 | tee "${RESULTS_DIR}/${test_name}-${TIMESTAMP}.log"; then
        
        print_success "${test_name} completado exitosamente"
        echo "✅ ${test_name} - PASSED" >> "${REPORT_FILE}"
        return 0
    else
        print_error "${test_name} falló"
        echo "❌ ${test_name} - FAILED" >> "${REPORT_FILE}"
        
        if [ "${CONTINUE_ON_FAILURE}" != "true" ]; then
            print_error "Abortando suite de tests"
            exit 1
        fi
        
        return 1
    fi
}

generate_consolidated_report() {
    print_header "Generando Reporte Consolidado"
    
    {
        echo "=========================================="
        echo "Load Testing - Reporte Consolidado"
        echo "=========================================="
        echo ""
        echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Base URL: ${BASE_URL}"
        echo "Timestamp: ${TIMESTAMP}"
        echo ""
        echo "=========================================="
        echo "Resultados de Tests"
        echo "=========================================="
        echo ""
    } > "${REPORT_FILE}"
    
    print_success "Reporte consolidado: ${REPORT_FILE}"
}

run_all_tests() {
    print_header "Iniciando Suite de Load Testing"
    print_info "Base URL: ${BASE_URL}"
    print_info "API Key: ${API_KEY:0:10}..."
    print_info "Continue on Failure: ${CONTINUE_ON_FAILURE}"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Test 1: Health Check
    total_tests=$((total_tests + 1))
    if run_test "test-health" "test-health.js" "Baseline performance test del endpoint /health"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    sleep 5  # Pausa entre tests
    
    # Test 2: Inventory Read
    total_tests=$((total_tests + 1))
    if run_test "test-inventory-read" "test-inventory-read.js" "Performance de operaciones de lectura GET /api/inventory"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    sleep 5
    
    # Test 3: Inventory Write (opcional, comentar si no se desea crear datos)
    if [ "${SKIP_WRITE_TESTS}" != "true" ]; then
        total_tests=$((total_tests + 1))
        if run_test "test-inventory-write" "test-inventory-write.js" "Performance de operaciones de escritura POST /api/inventory"; then
            passed_tests=$((passed_tests + 1))
        else
            failed_tests=$((failed_tests + 1))
        fi
        
        sleep 5
    else
        print_warning "Write tests omitidos (SKIP_WRITE_TESTS=true)"
    fi
    
    # Test 4: Metrics
    total_tests=$((total_tests + 1))
    if run_test "test-metrics" "test-metrics.js" "Performance del endpoint /metrics para Prometheus"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Resumen final
    print_header "Resumen Final"
    echo "Total Tests: ${total_tests}"
    echo "Passed: ${passed_tests}"
    echo "Failed: ${failed_tests}"
    
    {
        echo ""
        echo "=========================================="
        echo "Resumen"
        echo "=========================================="
        echo "Total Tests: ${total_tests}"
        echo "Passed: ${passed_tests}"
        echo "Failed: ${failed_tests}"
        echo "Success Rate: $(awk "BEGIN {printf \"%.2f%%\", (${passed_tests}/${total_tests})*100}")"
    } >> "${REPORT_FILE}"
    
    if [ ${failed_tests} -eq 0 ]; then
        print_success "Todos los tests pasaron exitosamente"
        return 0
    else
        print_error "Algunos tests fallaron"
        return 1
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    print_header "Load Testing Suite - Mini Market Dashboard"
    
    check_dependencies
    create_results_dir
    generate_consolidated_report
    
    if run_all_tests; then
        print_success "Suite de load testing completada exitosamente"
        print_info "Resultados en: ${RESULTS_DIR}"
        print_info "Reporte consolidado: ${REPORT_FILE}"
        exit 0
    else
        print_error "Suite de load testing completada con errores"
        print_info "Revisar logs en: ${RESULTS_DIR}"
        exit 1
    fi
}

# Mostrar ayuda
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    cat << EOF
Uso: $0 [opciones]

Script de orquestación para ejecutar suite de load testing con k6.

Variables de entorno:
    BASE_URL                URL base del servicio (default: http://localhost:8080)
    API_KEY                 API key para autenticación (default: test-api-key-dev)
    CONTINUE_ON_FAILURE     Continuar si un test falla (default: false)
    SKIP_WRITE_TESTS        Omitir tests de escritura (default: false)

Ejemplos:
    # Ejecutar todos los tests contra localhost
    $0

    # Ejecutar contra staging
    BASE_URL=https://staging.example.com API_KEY=staging-key $0

    # Omitir tests de escritura
    SKIP_WRITE_TESTS=true $0

    # Continuar aunque fallen tests
    CONTINUE_ON_FAILURE=true $0

EOF
    exit 0
fi

# Ejecutar main
main
