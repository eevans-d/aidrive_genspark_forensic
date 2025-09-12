#!/bin/bash
# Deploy completo a producción
set -e

echo "🚀 Iniciando deploy a producción..."

# Instalar nginx y systemd
sudo apt install -y nginx supervisor
sudo systemctl enable nginx

# Copiar archivos de configuración
sudo cp systemd/*.service /etc/systemd/system/
sudo cp nginx/inventario-retail.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/inventario-retail.conf /etc/nginx/sites-enabled/

# Recargar systemd y nginx
sudo systemctl daemon-reload
sudo nginx -t && sudo systemctl reload nginx

# Instalar certificados SSL (opcional)
if [ -n "$SSL_EMAIL" ]; then
    sudo certbot --nginx -d $SERVER_NAME --email $SSL_EMAIL --agree-tos --non-interactive
fi

echo "✅ Deploy a producción completado"
