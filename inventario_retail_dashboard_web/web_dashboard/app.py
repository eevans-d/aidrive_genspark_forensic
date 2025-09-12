#!/usr/bin/env python3
"""
Dashboard Web Interactivo - Sistema Inventario Retail Argentino
Aplicación Flask principal con integración completa ML, OCR, Cache
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_socketio import SocketIO, emit
import os
import json
import redis
import pandas as pd
from datetime import datetime, timedelta
import logging
from werkzeug.utils import secure_filename
import io
import base64
from PIL import Image

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventario-retail-argentino-2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Socket.IO para updates tiempo real
socketio = SocketIO(app, cors_allowed_origins="*")

# Redis para cache y sesiones
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Redis conectado correctamente")
except:
    redis_client = None
    print("⚠️ Redis no disponible, usando fallback")

# Importar componentes del sistema (simulamos las importaciones)
class MockMLEngine:
    def get_dashboard_data(self):
        return {
            'kpis': {
                'productos_stock': 127,
                'valor_inventario': '$629,067.77',
                'disponibilidad': '98%',
                'cobertura_dias': '12.5'
            },
            'alertas_criticas': [
                {'producto': 'Coca Cola 2L', 'stock': 5, 'dias_restantes': 1.2, 'urgencia': 'crítica'},
                {'producto': 'Arroz 1kg', 'stock': 12, 'dias_restantes': 2.8, 'urgencia': 'alta'},
                {'producto': 'Aceite Girasol', 'stock': 45, 'dias_restantes': 52, 'urgencia': 'sobrestocado'}
            ],
            'recomendaciones_compra': [
                {'producto': 'Coca Cola 2L', 'cantidad': 24, 'costo': 28800, 'prioridad': 1},
                {'producto': 'Arroz 1kg', 'cantidad': 50, 'costo': 15000, 'prioridad': 2},
                {'producto': 'Yerba Mate 1kg', 'cantidad': 15, 'costo': 9750, 'prioridad': 3}
            ]
        }

ml_engine = MockMLEngine()

# Rutas principales
@app.route('/')
def index():
    """Dashboard principal"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard principal con métricas en tiempo real"""
    try:
        dashboard_data = ml_engine.get_dashboard_data()
        return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return render_template('error.html', error="Error cargando dashboard")

@app.route('/productos')
def productos():
    """Gestión de productos y stock"""
    return render_template('productos.html')

@app.route('/ocr')
def ocr():
    """Interface OCR para facturas"""
    return render_template('ocr.html')

@app.route('/reportes')
def reportes():
    """Generación de reportes"""
    return render_template('reportes.html')

# API Endpoints
@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API datos dashboard tiempo real"""
    try:
        data = ml_engine.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productos')
def api_productos():
    """API listado productos"""
    try:
        # Datos mock productos
        productos = [
            {
                'id': 1, 'codigo': 'CC2L001', 'nombre': 'Coca Cola 2L',
                'categoria': 'Bebidas', 'stock': 5, 'precio': 1200,
                'prediccion_7d': 18, 'estado': 'crítico'
            },
            {
                'id': 2, 'codigo': 'ARZ1K001', 'nombre': 'Arroz 1kg',
                'categoria': 'Alimentos', 'stock': 12, 'precio': 300,
                'prediccion_7d': 25, 'estado': 'bajo'
            },
            {
                'id': 3, 'codigo': 'ACG1L001', 'nombre': 'Aceite Girasol 1L',
                'categoria': 'Alimentos', 'stock': 45, 'precio': 800,
                'prediccion_7d': 8, 'estado': 'sobrestocado'
            }
        ]
        return jsonify(productos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-factura', methods=['POST'])
def api_upload_factura():
    """API upload y procesamiento facturas OCR"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file:
            filename = secure_filename(file.filename)
            # Procesar con OCR (simulado)
            ocr_result = {
                'success': True,
                'filename': filename,
                'datos_extraidos': {
                    'emisor': 'Distribuidora San Martín S.A.',
                    'cuit': '20-12345678-9',
                    'fecha': '22/08/2025',
                    'numero': '0001-00001234',
                    'productos': [
                        {'codigo': 'CC2L001', 'descripcion': 'Coca Cola 2L', 'cantidad': 24, 'precio_unitario': 1100, 'total': 26400},
                        {'codigo': 'ARZ1K001', 'descripcion': 'Arroz Largo Fino 1kg', 'cantidad': 50, 'precio_unitario': 280, 'total': 14000}
                    ],
                    'subtotal': 40400,
                    'iva': 8484,
                    'total': 48884
                },
                'confidence_scores': {
                    'emisor': 0.95,
                    'cuit': 0.92,
                    'fecha': 0.98,
                    'productos': 0.89,
                    'totales': 0.94
                }
            }
            return jsonify(ocr_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generar-reporte', methods=['POST'])
def api_generar_reporte():
    """API generación reportes"""
    try:
        params = request.json
        tipo = params.get('tipo', 'stock')
        formato = params.get('formato', 'pdf')

        # Generar reporte mock
        reporte_data = {
            'tipo': tipo,
            'formato': formato,
            'generado': datetime.now().isoformat(),
            'url_descarga': f'/downloads/reporte_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{formato}',
            'preview': {
                'total_productos': 127,
                'valor_total': 629067.77,
                'alertas_criticas': 3,
                'recomendaciones': 8
            }
        }

        return jsonify(reporte_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket para updates tiempo real
@socketio.on('connect')
def handle_connect():
    """Cliente conectado via WebSocket"""
    logger.info('Cliente conectado via WebSocket')
    emit('connected', {'data': 'Conectado al dashboard'})

@socketio.on('request_update')
def handle_request_update():
    """Cliente solicita actualización datos"""
    try:
        data = ml_engine.get_dashboard_data()
        emit('dashboard_update', data)
    except Exception as e:
        emit('error', {'message': str(e)})

# Función para updates automáticos
def background_updates():
    """Updates automáticos cada 30 segundos"""
    import threading
    import time

    def update_loop():
        while True:
            try:
                time.sleep(30)  # Update cada 30 segundos
                data = ml_engine.get_dashboard_data()
                socketio.emit('dashboard_update', data, broadcast=True)
            except Exception as e:
                logger.error(f"Error en background update: {e}")

    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Error interno del servidor"), 500

if __name__ == '__main__':
    # Crear directorio uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Iniciar updates en background
    background_updates()

    # Ejecutar aplicación
    print("🚀 Iniciando Dashboard Web - Sistema Inventario Retail Argentino")
    print("📊 Dashboard disponible en: http://localhost:5000")

    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5000,
                allow_unsafe_werkzeug=True)
