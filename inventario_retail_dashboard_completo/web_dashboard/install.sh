#!/bin/bash
# Script instalación rápida Dashboard Web Interactivo
# Sistema Inventario Retail Argentino

echo "🚀 Instalando Dashboard Web Interactivo..."

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorio uploads
mkdir -p uploads

# Configurar variables de entorno
export FLASK_APP=app.py
export FLASK_ENV=development

echo "✅ Instalación completada!"
echo ""
echo "Para ejecutar el dashboard:"
echo "1. source venv/bin/activate"
echo "2. python app.py"
echo "3. Abrir http://localhost:5000"
echo ""
echo "Para ejecutar con Docker:"
echo "docker-compose up -d"
