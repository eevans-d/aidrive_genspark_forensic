#!/bin/bash
# Deploy completo AWS EC2 para Sistema Inventario Retail Argentino
# Uso: ./deploy_aws.sh [instance-type] [region] [key-name]

set -e
set -u

# Configuración por defecto
INSTANCE_TYPE="${1:-t3.small}"  # 2 vCPU, 2GB RAM, <$20/mes
REGION="${2:-us-east-1}"        # Latencia ok para Argentina
KEY_NAME="${3:-inventario-key}"
AMI_ID="ami-0c02fb55956c7d316"  # Ubuntu 22.04 LTS
SECURITY_GROUP="inventario-retail-sg"

echo "🚀 Desplegando Sistema Inventario Retail en AWS EC2"
echo "   Instancia: $INSTANCE_TYPE"  
echo "   Región: $REGION"
echo "   Costo estimado: <$20/mes"

# Validar AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI no instalado. Instalando..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

# Configurar región
aws configure set default.region $REGION

# Crear Security Group si no existe  
if ! aws ec2 describe-security-groups --group-names $SECURITY_GROUP &>/dev/null; then
    echo "📋 Creando Security Group..."
    SECURITY_GROUP_ID=$(aws ec2 create-security-group         --group-name $SECURITY_GROUP         --description "Security group para Inventario Retail Argentino"         --query 'GroupId' --output text)

    # Reglas de firewall optimizadas
    aws ec2 authorize-security-group-ingress         --group-id $SECURITY_GROUP_ID         --protocol tcp --port 22 --cidr 0.0.0.0/0  # SSH

    aws ec2 authorize-security-group-ingress         --group-id $SECURITY_GROUP_ID         --protocol tcp --port 80 --cidr 0.0.0.0/0  # HTTP

    aws ec2 authorize-security-group-ingress         --group-id $SECURITY_GROUP_ID         --protocol tcp --port 443 --cidr 0.0.0.0/0  # HTTPS

    aws ec2 authorize-security-group-ingress         --group-id $SECURITY_GROUP_ID         --protocol tcp --port 8001-8004 --cidr 0.0.0.0/0  # APIs

    aws ec2 authorize-security-group-ingress         --group-id $SECURITY_GROUP_ID         --protocol tcp --port 8501 --cidr 0.0.0.0/0  # Streamlit
else
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups         --group-names $SECURITY_GROUP         --query 'SecurityGroups[0].GroupId' --output text)
fi

# Crear o verificar Key Pair
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME &>/dev/null; then
    echo "🔑 Creando Key Pair..."
    aws ec2 create-key-pair --key-name $KEY_NAME         --query 'KeyMaterial' --output text > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "✅ Key guardada en: ${KEY_NAME}.pem"
fi

# User Data Script para inicialización automática
USER_DATA=$(base64 -w 0 << 'EOF'
#!/bin/bash
set -e

# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias básicas
apt install -y python3.11 python3.11-venv python3-pip nginx redis-server postgresql postgresql-contrib     git curl wget unzip htop tree jq fail2ban ufw

# Configurar firewall básico
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 8001:8004/tcp
ufw allow 8501/tcp
ufw --force enable

# Configurar fail2ban para SSH
systemctl enable fail2ban
systemctl start fail2ban

# Crear usuario para aplicación
useradd -m -s /bin/bash inventario
usermod -aG sudo inventario

# Configurar directorio aplicación
mkdir -p /opt/inventario-retail
chown inventario:inventario /opt/inventario-retail

# Configurar Redis (cache performance)
sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server

# Configurar PostgreSQL básico
sudo -u postgres createuser --superuser inventario || true
sudo -u postgres createdb inventario_retail || true

# Mensaje de éxito
echo "✅ Servidor inicializado correctamente" > /tmp/init-complete
EOF
)

# Lanzar instancia EC2
echo "🚀 Lanzando instancia EC2..."
INSTANCE_ID=$(aws ec2 run-instances     --image-id $AMI_ID     --count 1     --instance-type $INSTANCE_TYPE     --key-name $KEY_NAME     --security-group-ids $SECURITY_GROUP_ID     --user-data "$USER_DATA"     --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=inventario-retail},{Key=Project,Value=InventarioArgentino}]"     --query 'Instances[0].InstanceId' --output text)

echo "⏳ Esperando que la instancia esté running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Obtener IP pública
PUBLIC_IP=$(aws ec2 describe-instances     --instance-ids $INSTANCE_ID     --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "🎉 ¡Instancia AWS EC2 creada exitosamente!"
echo "   Instance ID: $INSTANCE_ID"
echo "   IP Pública: $PUBLIC_IP"
echo "   Costo: ~$15-20/mes"
echo ""
echo "📋 Próximos pasos:"
echo "1. Esperar 2-3 minutos para inicialización completa"
echo "2. Conectar: ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo "3. Clonar repo: git clone <tu-repo> /opt/inventario-retail"
echo "4. Ejecutar: ./scripts/cloud/provision_server.sh"
echo ""
echo "🔗 URLs de acceso (después de deployment):"
echo "   Dashboard: http://${PUBLIC_IP}"
echo "   Streamlit: http://${PUBLIC_IP}:8501"
echo "   APIs: http://${PUBLIC_IP}:8001-8004"
