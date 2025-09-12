#!/bin/bash
"""
Script de Instalación OCR Avanzado
=================================

Script para instalar y configurar el sistema OCR avanzado
con todas las dependencias necesarias.

Autor: Sistema Inventario Retail Argentino
Fecha: 2025-08-22
"""

echo "🚀 Instalando Sistema OCR Avanzado para Inventario Retail Argentino"
echo "=================================================================="

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt-get update -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
sudo apt-get install -y libsm6 libxext6 libxrender-dev
sudo apt-get install -y libgtk-3-dev
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa
sudo apt-get install -y libgstreamer1.0-0 gstreamer1.0-plugins-base
sudo apt-get install -y redis-server

# Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip3 install --upgrade pip

# OCR engines
pip3 install easyocr
pip3 install pytesseract
pip3 install paddlepaddle paddleocr

# Computer vision
pip3 install opencv-python
pip3 install pillow

# ML y data processing
pip3 install numpy pandas scikit-learn
pip3 install matplotlib seaborn

# Web framework
pip3 install fastapi uvicorn
pip3 install python-multipart

# Cache y async
pip3 install redis aioredis hiredis
pip3 install asyncio aiofiles

# Utils
pip3 install python-dateutil
pip3 install pydantic

echo "✅ Dependencias instaladas correctamente"

# Configurar Redis
echo "🗄️ Configurando Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p /tmp/facturas_upload
mkdir -p /home/user/output/ocr_testing
mkdir -p /var/log/ocr_system

# Configurar permisos
chmod 755 /tmp/facturas_upload
chmod 755 /home/user/output/ocr_testing

echo "🎯 Instalación completada"
echo ""
echo "Para ejecutar el sistema:"
echo "cd inventario-retail/ocr_advanced"
echo "python agente_negocio_ocr_advanced.py"
echo ""
echo "Para testing:"
echo "python ocr_testing_framework.py"
