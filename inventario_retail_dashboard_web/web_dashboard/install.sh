#!/bin/bash
# Script de instalación automática - Dashboard Web Sistema Inventario

echo "🚀 Instalando Dashboard Web Sistema Inventario Retail Argentino"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instalar Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instalar Docker Compose primero."
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p uploads
mkdir -p ssl
mkdir -p backups

# Generar certificados SSL autofirmados (desarrollo)
echo "🔐 Generando certificados SSL para desarrollo..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/nginx.key \
    -out ssl/nginx.crt \
    -subj "/C=AR/ST=BuenosAires/L=CABA/O=InventarioRetail/CN=localhost"

# Configurar permisos
chmod 600 ssl/nginx.key
chmod 644 ssl/nginx.crt

# Construir y levantar servicios
echo "🏗️ Construyendo contenedores..."
docker-compose build

echo "▶️ Iniciando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando servicios..."
sleep 10

# Verificar estado
echo "🔍 Verificando estado de servicios..."
docker-compose ps

# Mostrar logs iniciales
echo "📋 Logs iniciales del dashboard:"
docker-compose logs dashboard --tail=20

echo ""
echo "✅ Instalación completada!"
echo ""
echo "🌐 Dashboard disponible en:"
echo "   - HTTP:  http://localhost"
echo "   - HTTPS: https://localhost (certificado autofirmado)"
echo "   - Directo: http://localhost:5000"
echo ""
echo "🗄️ Base de datos PostgreSQL:"
echo "   - Host: localhost:5432"
echo "   - Base: inventario_retail"
echo "   - Usuario: inventario"
echo ""
echo "📦 Redis Cache:"
echo "   - Host: localhost:6379"
echo ""
echo "🛠️ Comandos útiles:"
echo "   - Ver logs: docker-compose logs -f"
echo "   - Parar servicios: docker-compose down"
echo "   - Reiniciar: docker-compose restart"
echo "   - Backup DB: docker-compose exec postgres pg_dump -U inventario inventario_retail > backup.sql"
echo ""
