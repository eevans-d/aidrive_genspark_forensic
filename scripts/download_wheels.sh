#!/bin/bash
# Script para pre-descargar wheels y evitar timeouts en deployment
# Task T1.1.3 - ETAPA 3 Fase 1 Semana 1

set -e

WHEELS_DIR="$(dirname "$0")/../inventario-retail/wheels"
mkdir -p "$WHEELS_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  📦 Descargando wheels para deployment offline                ║"
echo "║  Directorio: $WHEELS_DIR                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Paquetes críticos más pesados (los que causan timeout)
CRITICAL_PACKAGES=(
    "easyocr==1.7.0"           # ~500MB con dependencias (torch, etc)
    "torch==2.1.0"             # ~888MB
    "scikit-learn==1.3.2"      # ~30MB
    "opencv-python==4.8.1.78"  # ~90MB
    "pandas==2.1.4"            # ~50MB
    "numpy==1.26.4"            # ~50MB
    "pillow==10.1.0"           # ~10MB
    "streamlit==1.28.2"        # ~20MB
    "plotly==5.17.0"           # ~30MB
)

echo "🔍 Paquetes críticos a descargar:"
for pkg in "${CRITICAL_PACKAGES[@]}"; do
    echo "  - $pkg"
done
echo ""

# Descargar cada paquete con sus dependencias
for pkg in "${CRITICAL_PACKAGES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📥 Descargando: $pkg"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    pip download \
        --dest "$WHEELS_DIR" \
        --timeout 600 \
        --retries 5 \
        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        "$pkg" || {
            echo "⚠️  WARNING: Failed to download $pkg, continuando..."
        }
    
    echo ""
done

# Descargar el requirements completo (esto atrapará dependencias faltantes)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Descargando requirements.txt completo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pip download \
    --dest "$WHEELS_DIR" \
    --timeout 600 \
    --retries 5 \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r "$(dirname "$0")/../inventario-retail/requirements.txt" || {
        echo "⚠️  WARNING: Some packages failed, pero ya tenemos las críticas"
    }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DESCARGA COMPLETADA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Resumen
WHEEL_COUNT=$(find "$WHEELS_DIR" -name "*.whl" | wc -l)
WHEEL_SIZE=$(du -sh "$WHEELS_DIR" | cut -f1)

echo "📊 RESUMEN:"
echo "  - Wheels descargadas: $WHEEL_COUNT archivos"
echo "  - Tamaño total: $WHEEL_SIZE"
echo "  - Ubicación: $WHEELS_DIR"
echo ""
echo "🚀 Próximo paso: Modificar Dockerfiles para usar wheels locales"
echo "   Ver: T1.1.3 en CHECKLIST_FASE1_ETAPA3.md"
echo ""
