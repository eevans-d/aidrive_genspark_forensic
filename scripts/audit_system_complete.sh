#!/bin/bash
# scripts/audit_system_complete.sh - Alineado al repositorio real
set -euo pipefail

OUTPUT_DIR="docs/audit_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUTPUT_DIR"

echo "🔍 AUDITORÍA ALINEADA AL REPOSITORIO REAL"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Verificar comandos necesarios
has_cmd() { command -v "$1" >/dev/null 2>&1; }

# 1. VALIDACIÓN DE ESTRUCTURA CRÍTICA
{
    echo "# VALIDACIÓN DE ESTRUCTURA Y CONVENCIONES"
    echo "Generado: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
    
    # Verificar directorios clave
    [ -d "inventario-retail" ] && echo "✅ inventario-retail/ (con guión)" || echo "❌ CRÍTICO: inventario-retail/ no encontrado"
    [ -d "inventario-retail/web_dashboard" ] && echo "✅ web_dashboard/" || echo "❌ web_dashboard/ no encontrado"
    [ -d "shared" ] && echo "✅ shared/ (configuración)" || echo "⚠️ shared/ no encontrado"
    [ -f ".github/workflows/ci.yml" ] && echo "✅ CI/CD workflow" || echo "❌ ci.yml no encontrado"
    
    echo ""
    echo "## Métricas Prometheus Existentes"
    if grep -r "dashboard_request_duration_ms_p95" inventario-retail/ --include="*.py" > /dev/null 2>&1; then
        echo "✅ Métrica dashboard_request_duration_ms_p95 encontrada"
        grep -r -n "dashboard_request_duration_ms_p95" inventario-retail/ --include="*.py" | head -3
    else
        echo "❌ CRÍTICO: Métrica dashboard_request_duration_ms_p95 no encontrada"
        echo "Buscando métricas alternativas..."
        grep -r "dashboard_request_duration" inventario-retail/ --include="*.py" | head -5 || echo "Ninguna métrica de duración encontrada"
    fi
    
    echo ""
    echo "## Convenciones de Importación"
    if grep -r "sys\.path\.insert" inventario-retail/ --include="*.py" > /dev/null 2>&1; then
        echo "✅ Patrones sys.path.insert detectados"
        grep -r "sys\.path\.insert" inventario-retail/ --include="*.py" | head -3
    else
        echo "⚠️ No se detectaron patrones sys.path.insert"
    fi
    
} > "$OUTPUT_DIR/structure_validation_$TIMESTAMP.md"

# 2. AUDITORÍA DASHBOARD
{
    echo "# AUDITORÍA DASHBOARD EXISTENTE"
    echo "Generado: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
    
    if [ -d "inventario-retail/web_dashboard" ]; then
        echo "## Archivos Python"
        find inventario-retail/web_dashboard -name "*.py" -type f | sed 's/^/ - /'
        
        echo ""
        echo "## Endpoints FastAPI"
        grep -rn "@app\.\|@router\." inventario-retail/web_dashboard/ --include="*.py" || echo "No endpoints encontrados"
        
        echo ""
        echo "## Middleware Existente"
        grep -rn "Middleware" inventario-retail/web_dashboard/ --include="*.py" || echo "No middleware encontrado"
        
        echo ""
        echo "## Requirements"
        cat inventario-retail/web_dashboard/requirements.txt 2>/dev/null || echo "requirements.txt no encontrado"
    else
        echo "❌ Directorio web_dashboard no encontrado"
    fi
    
} > "$OUTPUT_DIR/dashboard_audit_$TIMESTAMP.md"

# 3. COBERTURA BASELINE
{
    echo "# COBERTURA DE TESTS BASELINE"
    echo "Generado: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
    
    if has_cmd pytest; then
        echo "## Pytest Collection"
        (cd inventario-retail && pytest --collect-only 2>&1) || echo "Pytest collection falló"
        
        echo ""
        echo "## Cobertura Dashboard"
        (cd inventario-retail && pytest --cov=web_dashboard --cov-report=term-missing 2>&1) || echo "Cobertura falló"
    else
        echo "❌ pytest no disponible"
    fi
    
} > "$OUTPUT_DIR/coverage_baseline_$TIMESTAMP.md"

# 4. ANÁLISIS DE CONFIGURACIÓN
{
    echo "# ANÁLISIS DE CONFIGURACIÓN"
    echo "Generado: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
    
    echo "## Docker Compose Files"
    ls -1 docker-compose*.yml 2>/dev/null | sed 's/^/ - /' || echo "No docker-compose files found"
    
    echo ""
    echo "## GitHub Workflows"
    find .github/workflows -name "*.yml" -type f 2>/dev/null | sed 's/^/ - /' || echo "No workflows found"
    
    echo ""
    echo "## Prometheus Configuration"
    find inventario-retail -name "prometheus*.yml" -type f 2>/dev/null | sed 's/^/ - /' || echo "No prometheus config found"
    
} > "$OUTPUT_DIR/config_analysis_$TIMESTAMP.md"

# 5. DEPENDENCIAS
{
    echo "# ANÁLISIS DE DEPENDENCIAS"
    echo "Generado: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo ""
    
    echo "## Requirements Files"
    find . -name "requirements*.txt" -type f | while read req; do
        echo ""
        echo "### $req"
        cat "$req"
    done
    
} > "$OUTPUT_DIR/dependencies_$TIMESTAMP.md"

echo ""
echo "✅ Auditoría completada en: $OUTPUT_DIR/"
echo ""
echo "Reportes generados:"
ls -lah "$OUTPUT_DIR/"*_$TIMESTAMP.md
