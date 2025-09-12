#!/bin/bash
# ==========================================
# Script de Inicialización Sistema Multi-Agente Retail Argentino
# Ejecutar desde el directorio raíz del proyecto
# ==========================================

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    error "No se encontró requirements.txt. Ejecutar desde el directorio raíz del proyecto."
    exit 1
fi

log "🚀 Inicializando Sistema Multi-Agente Retail Argentino..."

# ==========================================
# 1. VERIFICAR PYTHON Y DEPENDENCIAS DEL SISTEMA
# ==========================================

log "📋 Verificando dependencias del sistema..."

# Verificar Python 3.11+
if ! python3 --version | grep -E "3\.(11|12)" > /dev/null; then
    error "Se requiere Python 3.11 o superior"
    info "Instalar con: sudo apt update && sudo apt install python3.11 python3.11-venv"
    exit 1
fi

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    error "pip3 no está instalado"
    info "Instalar con: sudo apt install python3-pip"
    exit 1
fi

log "✅ Python $(python3 --version) encontrado"

# ==========================================
# 2. CREAR ENTORNO VIRTUAL
# ==========================================

log "🐍 Configurando entorno virtual..."

if [ ! -d "venv" ]; then
    log "Creando entorno virtual..."
    python3 -m venv venv
else
    log "Entorno virtual ya existe"
fi

# Activar entorno virtual
source venv/bin/activate
log "✅ Entorno virtual activado"

# Actualizar pip
log "Actualizando pip..."
pip install --upgrade pip setuptools wheel

# ==========================================
# 3. INSTALAR DEPENDENCIAS PYTHON
# ==========================================

log "📦 Instalando dependencias Python..."

# Instalar dependencias principales
pip install -r requirements.txt

log "✅ Dependencias Python instaladas"

# ==========================================
# 4. VERIFICAR DEPENDENCIAS DEL SISTEMA
# ==========================================

log "🔍 Verificando dependencias del sistema..."

# Lista de paquetes requeridos
SYSTEM_DEPS=(
    "libgl1-mesa-glx"      # OpenCV
    "libglib2.0-0"         # OpenCV
    "tesseract-ocr"        # OCR backup
    "tesseract-ocr-spa"    # OCR español
)

# Función para verificar si un paquete está instalado
check_package() {
    if dpkg -l | grep -q "^ii  $1 "; then
        return 0
    else
        return 1
    fi
}

missing_packages=()
for package in "${SYSTEM_DEPS[@]}"; do
    if ! check_package "$package"; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    warn "Paquetes del sistema faltantes: ${missing_packages[*]}"
    info "Instalar con: sudo apt update && sudo apt install ${missing_packages[*]}"

    read -p "¿Instalar ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install "${missing_packages[@]}"
        log "✅ Paquetes del sistema instalados"
    else
        warn "Continuar sin instalar paquetes. Algunas funciones pueden no trabajar correctamente."
    fi
else
    log "✅ Todas las dependencias del sistema están instaladas"
fi

# ==========================================
# 5. CONFIGURAR ARCHIVO DE ENTORNO
# ==========================================

log "⚙️ Configurando archivo de entorno..."

if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        log "Copiando .env.template a .env..."
        cp .env.template .env

        # Generar JWT secret aleatorio
        JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

        # Reemplazar en .env
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
        else
            # Linux
            sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
        fi

        log "✅ Archivo .env creado con JWT secret aleatorio"
        warn "Revisar y ajustar configuración en .env según necesidades"
    else
        error "No se encontró .env.template"
        exit 1
    fi
else
    log "Archivo .env ya existe"
fi

# ==========================================
# 6. CREAR DIRECTORIOS NECESARIOS
# ==========================================

log "📁 Creando estructura de directorios..."

DIRECTORIES=(
    "data"
    "logs"
    "backups"
    "uploads"
    "temp"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log "Directorio $dir creado"
    fi
done

# Configurar permisos
chmod 755 data logs backups
chmod 777 uploads temp  # Para uploads de usuarios

log "✅ Estructura de directorios creada"

# ==========================================
# 7. INICIALIZAR BASE DE DATOS
# ==========================================

log "🗄️ Inicializando base de datos..."

# Ejecutar inicialización de BD
python3 -c "
import sys
sys.path.insert(0, '.')
from shared.database import init_database
from shared.config import setup_logging

# Configurar logging
setup_logging()

try:
    init_database()
    print('✅ Base de datos inicializada correctamente')
except Exception as e:
    print(f'❌ Error inicializando BD: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    log "✅ Base de datos inicializada"
else
    error "Falló la inicialización de la base de datos"
    exit 1
fi

# ==========================================
# 8. VERIFICAR CONFIGURACIÓN
# ==========================================

log "🔧 Verificando configuración..."

# Test de configuración
python3 -c "
import sys
sys.path.insert(0, '.')
from shared.config import get_settings

try:
    settings = get_settings()
    print(f'✅ Configuración cargada:')
    print(f'   - Puerto AgenteNegocio: {settings.AGENTE_NEGOCIO_PORT}')
    print(f'   - Puerto AgenteDepósito: {settings.AGENTE_DEPOSITO_PORT}')
    print(f'   - Inflación mensual: {settings.INFLACION_MENSUAL}%')
    print(f'   - Temporada: {settings.TEMPORADA}')
    print(f'   - Base de datos: {settings.DATABASE_URL}')
except Exception as e:
    print(f'❌ Error en configuración: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    error "Error en verificación de configuración"
    exit 1
fi

# ==========================================
# 9. CREAR SCRIPTS DE UTILIDAD
# ==========================================

log "📜 Creando scripts de utilidad..."

# Script para activar entorno
cat > activate.sh << 'EOF'
#!/bin/bash
# Script para activar entorno virtual
source venv/bin/activate
echo "🐍 Entorno virtual activado"
echo "Para desactivar: deactivate"
EOF

chmod +x activate.sh

# Script para ejecutar tests
cat > run_tests.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "🧪 Ejecutando tests..."
pytest tests/ -v --cov=shared --cov=agente_negocio --cov=agente_deposito
EOF

chmod +x run_tests.sh

# Script para iniciar servicios
cat > start_services.sh << 'EOF'
#!/bin/bash
source venv/bin/activate

echo "🚀 Iniciando servicios..."

# Terminal 1: AgenteDepósito
gnome-terminal -- bash -c "
    source venv/bin/activate; 
    echo '🏭 Iniciando AgenteDepósito en puerto 8002...'; 
    cd agente_deposito; 
    uvicorn main:app --host 0.0.0.0 --port 8002 --reload;
    exec bash"

sleep 2

# Terminal 2: AgenteNegocio  
gnome-terminal -- bash -c "
    source venv/bin/activate; 
    echo '🧠 Iniciando AgenteNegocio en puerto 8001...'; 
    cd agente_negocio; 
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload;
    exec bash"

echo "✅ Servicios iniciados en terminales separadas"
echo "   - AgenteDepósito: http://localhost:8002"
echo "   - AgenteNegocio: http://localhost:8001"
EOF

chmod +x start_services.sh

log "✅ Scripts de utilidad creados"

# ==========================================
# 10. RESUMEN Y PRÓXIMOS PASOS
# ==========================================

log "🎉 ¡Inicialización completada exitosamente!"

echo
info "=== RESUMEN ==="
info "✅ Entorno virtual creado y configurado"
info "✅ Dependencias Python instaladas"  
info "✅ Base de datos inicializada"
info "✅ Configuración verificada"
info "✅ Directorios creados"
info "✅ Scripts de utilidad listos"

echo
info "=== PRÓXIMOS PASOS ==="
info "1. Revisar configuración en .env"
info "2. Ejecutar tests: ./run_tests.sh"
info "3. Iniciar servicios: ./start_services.sh"
info "4. Verificar health checks:"
info "   curl http://localhost:8001/health"
info "   curl http://localhost:8002/health"

echo
warn "=== NOTAS IMPORTANTES ==="
warn "- Configurar alertas Telegram en .env (opcional)"
warn "- Ajustar inflación mensual según contexto actual"  
warn "- Configurar backup automático para producción"
warn "- Revisar logs en directorio logs/"

echo
log "🚀 Sistema listo para usar. ¡A codear se ha dicho!"
