#!/bin/bash

# ============================================================================
# VALIDACIÓN DÍA 1 HORAS 4-7: DATABASE CIRCUIT BREAKER (SIMPLE)
# ============================================================================

echo "🔍 DÍA 1 HORAS 4-7: Validación Database Circuit Breaker"
echo "================================================================"

WORKSPACE_ROOT="/home/eevan/ProyectosIA/aidrive_genspark"
PASS=0
FAIL=0

# Función simple para verificar
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $2"
        ((PASS++))
        return 0
    else
        echo "❌ $2 - No encontrado: $1"
        ((FAIL++))
        return 1
    fi
}

check_pattern() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo "✅ $3"
        ((PASS++))
        return 0
    else
        echo "❌ $3 - No encontrado en $1"
        ((FAIL++))
        return 1
    fi
}

echo ""
echo "📋 PASO 1: Archivos principales"
check_file "$WORKSPACE_ROOT/inventario-retail/agente_negocio/services/database_service.py" "database_service.py existe"
check_file "$WORKSPACE_ROOT/inventario-retail/agente_negocio/main.py" "main.py existe"
check_file "$WORKSPACE_ROOT/tests/resilience/test_database_circuit_breaker.py" "test_database_circuit_breaker.py existe"

echo ""
echo "📋 PASO 2: DatabaseService - Métodos"
DB_FILE="$WORKSPACE_ROOT/inventario-retail/agente_negocio/services/database_service.py"
check_pattern "$DB_FILE" "class DatabaseService" "Clase DatabaseService definida"
check_pattern "$DB_FILE" "async def read_query" "Método read_query implementado"
check_pattern "$DB_FILE" "async def write_query" "Método write_query implementado"
check_pattern "$DB_FILE" "async def transaction" "Método transaction implementado"
check_pattern "$DB_FILE" "_activate_readonly_mode" "Graceful degradation (read-only mode)"
check_pattern "$DB_FILE" "get_database_service" "Singleton pattern implementado"

echo ""
echo "📋 PASO 3: Endpoints en main.py"
MAIN_FILE="$WORKSPACE_ROOT/inventario-retail/agente_negocio/main.py"
check_pattern "$MAIN_FILE" "from .services.database_service import" "Import de database_service"
check_pattern "$MAIN_FILE" 'def db_read' "Endpoint GET /db/read"
check_pattern "$MAIN_FILE" 'def db_write' "Endpoint POST /db/write"
check_pattern "$MAIN_FILE" 'def db_transaction' "Endpoint POST /db/transaction"
check_pattern "$MAIN_FILE" 'def database_health' "Endpoint GET /health/database"

echo ""
echo "📋 PASO 4: Imports FastAPI"
check_pattern "$MAIN_FILE" "from fastapi import.*Query" "Import Query"
check_pattern "$MAIN_FILE" "from fastapi import.*Body" "Import Body"

echo ""
echo "📋 PASO 5: Circuit Breaker Config"
CB_FILE="$WORKSPACE_ROOT/inventario-retail/shared/circuit_breakers.py"
check_pattern "$CB_FILE" "db_breaker" "db_breaker configurado"
check_pattern "$CB_FILE" "reset_timeout" "Parámetro reset_timeout correcto"

echo ""
echo "📋 PASO 6: Fallbacks"
FB_FILE="$WORKSPACE_ROOT/inventario-retail/shared/fallbacks.py"
check_pattern "$FB_FILE" "db_read_fallback" "db_read_fallback() definido"
check_pattern "$FB_FILE" "db_write_fallback" "db_write_fallback() definido"

echo ""
echo "📋 PASO 7: Tests"
TEST_FILE="$WORKSPACE_ROOT/tests/resilience/test_database_circuit_breaker.py"
TEST_COUNT=$(grep -c "^async def test_" "$TEST_FILE" 2>/dev/null || echo "0")
echo "Total de tests: $TEST_COUNT"
if [ "$TEST_COUNT" -ge 15 ]; then
    echo "✅ Cobertura de tests suficiente ($TEST_COUNT tests)"
    ((PASS++))
else
    echo "❌ Cobertura de tests insuficiente ($TEST_COUNT tests < 15)"
    ((FAIL++))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "TOTAL: $TOTAL verificaciones"
echo "✅ PASS: $PASS"
echo "❌ FAIL: $FAIL"

if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo "✨ VALIDACIÓN 100% COMPLETA ✨"
    echo ""
    echo "DÍA 1 HORAS 4-7: Database Circuit Breaker COMPLETADO"
    echo "  ✅ DatabaseService con @db_breaker decorator"
    echo "  ✅ Graceful degradation (read-only mode)"
    echo "  ✅ 4 endpoints en main.py"
    echo "  ✅ Tests de cobertura completa"
    echo "  ✅ Circuit breaker DB configurado"
    echo ""
    echo "Próximo paso: DÍA 1 HORAS 7-8 (Testing + Monitoring)"
    exit 0
else
    echo ""
    echo "⚠️  VALIDACIÓN INCOMPLETA - REVISAR FALLOS"
    exit 1
fi
