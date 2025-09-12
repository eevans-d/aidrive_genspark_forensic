#!/bin/bash
# Script de Deployment - Dashboard Web Inventario Retail Argentino

echo "🚀 Iniciando deployment Dashboard Web Inventario Retail ARG..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Instalando..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Instalando..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p uploads logs facturas ssl

# Variables de entorno
echo "⚙️ Configurando variables de entorno..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Dashboard Web Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/inventario_retail
REDIS_URL=redis://redis:6379/0

# API URLs
API_DEPOSITO_URL=http://agente-deposito:8000
API_NEGOCIO_URL=http://agente-negocio:8001
API_ML_URL=http://ml-predictor:8002

# Configuración Argentina
TIMEZONE=America/Argentina/Buenos_Aires
CURRENCY=ARS
INFLACION_MENSUAL=0.045
EOF
    echo "✅ Archivo .env creado"
else
    echo "✅ Archivo .env ya existe"
fi

# Build y deploy
echo "🔨 Construyendo imágenes Docker..."
docker-compose build --no-cache

echo "🚀 Iniciando servicios..."
docker-compose up -d

# Verificar servicios
echo "🔍 Verificando servicios..."
sleep 10

services=("postgres" "redis" "dashboard-web")
for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service: OK"
    else
        echo "❌ $service: ERROR"
    fi
done

# Test endpoints
echo "🧪 Probando endpoints..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Dashboard Web: OK"
else
    echo "❌ Dashboard Web: ERROR"
fi

echo ""
echo "🎉 ¡Deployment completado!"
echo ""
echo "📊 Dashboard Web: http://localhost:5000"
echo "🔒 Login: admin / admin123"
echo "📱 Mobile-friendly: ✅"
echo "⚡ WebSockets: ✅"
echo "🧠 ML Integration: ✅"
echo ""
echo "Para ver logs: docker-compose logs -f dashboard-web"
echo "Para parar: docker-compose down"
echo ""
echo "¡Sistema Inventario Retail Argentino funcionando! 🇦🇷"
