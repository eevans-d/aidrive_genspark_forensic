#!/bin/bash
# Script para build secuencial de servicios Docker
# Evita saturación de red construyendo uno a uno
# Task T1.1.4 - ETAPA 3 Fase 1 Semana 1

set -e

COMPOSE_FILE="${1:-docker-compose.production.yml}"
SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../inventario-retail" && pwd)"

cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔨 Build Secuencial de Servicios Docker                      ║"
echo "║  Compose: $COMPOSE_FILE                                        ║"
echo "║  Directory: $PROJECT_DIR                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Servicios que requieren build (en orden de dependencias)
services=("agente-deposito" "agente-negocio" "ml-service" "dashboard")

echo "🎯 Servicios a construir:"
for service in "${services[@]}"; do
    echo "  - $service"
done
echo ""

# Timestamp inicio
START_TIME=$(date +%s)

# Build cada servicio secuencialmente
for service in "${services[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 Building: $service"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    SERVICE_START=$(date +%s)
    
    if docker-compose -f "$COMPOSE_FILE" build --no-cache "$service"; then
        SERVICE_END=$(date +%s)
        SERVICE_DURATION=$((SERVICE_END - SERVICE_START))
        echo ""
        echo "✅ $service built successfully in ${SERVICE_DURATION}s"
        echo ""
    else
        echo ""
        echo "❌ ERROR: $service build failed"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check Dockerfile syntax: inventario-retail/$service/Dockerfile"
        echo "  2. Verify network connectivity"
        echo "  3. Check docker-compose.yml service definition"
        echo "  4. Review build logs above"
        echo ""
        exit 1
    fi
    
    # Cooldown de 5 segundos entre builds para evitar saturación
    if [ "$service" != "${services[-1]}" ]; then
        echo "⏳ Cooldown 5s antes del siguiente build..."
        sleep 5
        echo ""
    fi
done

# Timestamp fin
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BUILD COMPLETO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 RESUMEN:"
echo "  - Servicios construidos: ${#services[@]}"
echo "  - Tiempo total: ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60))m $(($TOTAL_DURATION % 60))s)"
echo "  - Compose file: $COMPOSE_FILE"
echo ""
echo "🚀 Próximo paso: Deploy con docker-compose up"
echo "   Ver: T1.1.5 en CHECKLIST_FASE1_ETAPA3.md"
echo ""
echo "Comando para deploy:"
echo "  cd $PROJECT_DIR"
echo "  docker-compose -f $COMPOSE_FILE up -d"
echo ""
