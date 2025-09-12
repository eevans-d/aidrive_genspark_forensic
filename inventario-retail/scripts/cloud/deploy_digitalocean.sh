#!/bin/bash
# Deploy DigitalOcean Droplet para Sistema Inventario Retail Argentino
# Uso: ./deploy_digitalocean.sh [size] [region] 

set -e
set -u

# Configuración por defecto
DROPLET_SIZE="${1:-s-2vcpu-2gb}"    # 2 vCPU, 2GB RAM, $18/mes
REGION="${2:-nyc3}"                 # Cercano a Argentina
DROPLET_NAME="inventario-retail-$(date +%Y%m%d)"
IMAGE="ubuntu-22-04-x64"
SSH_KEY_NAME="inventario-retail-key"

echo "🚀 Desplegando Sistema Inventario Retail en DigitalOcean"
echo "   Droplet: $DROPLET_SIZE"
echo "   Región: $REGION"  
echo "   Costo estimado: $18/mes"

# Validar doctl CLI
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl no instalado. Instalando..."

    # Detectar OS para descargar binario correcto
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
        tar xf doctl-1.94.0-linux-amd64.tar.gz
        sudo mv doctl /usr/local/bin
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install doctl
    else
        echo "❌ OS no soportado para instalación automática. Instalar doctl manualmente."
        exit 1
    fi
fi

# Verificar autenticación
if ! doctl auth list &>/dev/null; then
    echo "❌ No autenticado con DigitalOcean."
    echo "Ejecutar: doctl auth init"
    exit 1
fi

# Crear o verificar SSH key
if ! doctl compute ssh-key list | grep -q "$SSH_KEY_NAME"; then
    echo "🔑 Creando SSH Key..."

    # Generar key si no existe
    if [ ! -f "$HOME/.ssh/${SSH_KEY_NAME}" ]; then
        ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/${SSH_KEY_NAME}" -N "" -C "inventario-retail"
    fi

    # Subir key a DigitalOcean
    doctl compute ssh-key import $SSH_KEY_NAME         --public-key-file "$HOME/.ssh/${SSH_KEY_NAME}.pub"
fi

# Obtener ID de SSH key
SSH_KEY_ID=$(doctl compute ssh-key list | grep "$SSH_KEY_NAME" | awk '{print $1}')

# Cloud-init script para inicialización automática
CLOUD_INIT_SCRIPT='#!/bin/bash
set -e

# Log de inicialización
exec > >(tee /var/log/cloud-init-inventario.log)
exec 2>&1

echo "🚀 Iniciando configuración DigitalOcean Droplet..."

# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias optimizadas
apt install -y python3.11 python3.11-venv python3-pip nginx redis-server postgresql postgresql-contrib \
    git curl wget unzip htop tree jq fail2ban ufw \
    build-essential libssl-dev libffi-dev python3.11-dev \
    supervisor certbot python3-certbot-nginx

# Configurar timezone Argentina
timedatectl set-timezone America/Argentina/Buenos_Aires

# Configurar firewall optimizado
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow "Nginx Full"
ufw allow 8001:8004/tcp
ufw allow 8501/tcp
ufw --force enable

# Configurar fail2ban con reglas argentinas
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
EOF

systemctl restart fail2ban

# Crear usuario aplicación
useradd -m -s /bin/bash inventario
usermod -aG sudo inventario
echo "inventario ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/inventario

# Configurar Redis optimizado para Argentina
cat > /etc/redis/redis.conf.custom << EOF
# Configuración optimizada para inventario retail argentino
maxmemory 512mb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
save 900 1
save 300 10
save 60 10000
EOF

cat /etc/redis/redis.conf.custom >> /etc/redis/redis.conf
systemctl restart redis-server

# Configurar PostgreSQL con encoding argentino
sudo -u postgres psql -c "CREATE USER inventario WITH PASSWORD '''inventario123''' SUPERUSER;"
sudo -u postgres createdb inventario_retail -O inventario -E UTF8 -T template0 --lc-collate='''es_AR.UTF-8''' --lc-ctype='''es_AR.UTF-8'''

# Optimizaciones PostgreSQL para small instance
sudo -u postgres psql -c "ALTER SYSTEM SET shared_buffers = '''128MB''';"
sudo -u postgres psql -c "ALTER SYSTEM SET effective_cache_size = '''1GB''';"  
sudo -u postgres psql -c "ALTER SYSTEM SET maintenance_work_mem = '''64MB''';"
sudo -u postgres psql -c "SELECT pg_reload_conf();"

# Configurar directorio aplicación
mkdir -p /opt/inventario-retail
chown inventario:inventario /opt/inventario-retail

# Instalar Python dependencies globales para performance
pip3 install --upgrade pip setuptools wheel
pip3 install gunicorn uvicorn[standard] redis psycopg2-binary

# Configurar logs centralizados
mkdir -p /var/log/inventario-retail
chown inventario:inventario /var/log/inventario-retail

# Configurar NGINX básico
cat > /etc/nginx/sites-available/inventario-retail << EOF
server {
    listen 80;
    server_name _;

    # Rate limiting básico
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /streamlit/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

ln -sf /etc/nginx/sites-available/inventario-retail /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "✅ Droplet inicializado correctamente - $(date)" | tee /tmp/init-complete
'

# Crear Droplet
echo "🚀 Creando Droplet..."
DROPLET_ID=$(doctl compute droplet create $DROPLET_NAME     --size $DROPLET_SIZE     --image $IMAGE     --region $REGION     --ssh-keys $SSH_KEY_ID     --user-data "$CLOUD_INIT_SCRIPT"     --tag-name inventario-retail     --wait     --format ID     --no-header)

# Obtener IP pública
sleep 30  # Esperar que se asigne IP
DROPLET_IP=$(doctl compute droplet get $DROPLET_ID --format PublicIPv4 --no-header)

echo ""
echo "🎉 ¡Droplet DigitalOcean creado exitosamente!"
echo "   Droplet ID: $DROPLET_ID"
echo "   IP Pública: $DROPLET_IP"
echo "   Costo: $18/mes"
echo "   Región: $REGION"
echo ""
echo "📋 Próximos pasos:"
echo "1. Esperar 3-5 minutos para inicialización completa"
echo "2. Conectar: ssh -i ~/.ssh/${SSH_KEY_NAME} root@${DROPLET_IP}"
echo "3. Cambiar a usuario: sudo su - inventario"
echo "4. Clonar repo en: /opt/inventario-retail"
echo "5. Ejecutar: ./scripts/cloud/provision_server.sh"
echo ""
echo "🔗 URLs de acceso:"
echo "   Dashboard: http://${DROPLET_IP}"
echo "   Streamlit: http://${DROPLET_IP}/streamlit/"
echo "   APIs directas: http://${DROPLET_IP}:8001-8004"
echo ""
echo "💡 Para SSL automático:"
echo "   certbot --nginx -d tu-dominio.com"
