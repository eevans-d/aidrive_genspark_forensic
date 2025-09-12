"""
Dashboard Web Interactivo - Sistema Inventario Retail Argentino
Aplicación Flask principal con funcionalidades completas para retail
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import json
import redis
import psycopg2
from datetime import datetime, timedelta
import pandas as pd
import io
import base64
from PIL import Image
import plotly.graph_objs as go
import plotly.utils

# Configuración aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'inventario_retail_argentina_2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Configuración SocketIO para updates tiempo real
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración Redis Cache
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis conectado exitosamente")
except:
    REDIS_AVAILABLE = False
    print("⚠️ Redis no disponible - funcionando sin cache")

# Configuración PostgreSQL
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'inventario_retail',
    'user': 'postgres',
    'password': 'password'
}

def get_db_connection():
    """Conexión base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conexión BD: {e}")
        return None

def cache_get(key):
    """Obtener dato del cache Redis"""
    if REDIS_AVAILABLE:
        try:
            return redis_client.get(key)
        except:
            pass
    return None

def cache_set(key, value, ttl=300):
    """Guardar dato en cache Redis"""
    if REDIS_AVAILABLE:
        try:
            redis_client.setex(key, ttl, json.dumps(value) if isinstance(value, (dict, list)) else value)
        except:
            pass

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def dashboard():
    """Dashboard principal con métricas tiempo real"""
    try:
        # Intentar obtener datos del cache
        cached_data = cache_get('dashboard_data')
        if cached_data:
            dashboard_data = json.loads(cached_data)
        else:
            # Generar datos dashboard
            dashboard_data = generate_dashboard_data()
            cache_set('dashboard_data', dashboard_data, 60)  # Cache 1 minuto

        return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        flash(f'Error cargando dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', data={})

@app.route('/productos')
def productos():
    """Gestión productos con filtros y búsqueda"""
    try:
        page = int(request.args.get('page', 1))
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')

        productos_data = get_productos_filtered(search, category, status, page)

        return render_template('productos.html', 
                             productos=productos_data['productos'],
                             pagination=productos_data['pagination'],
                             filters={'search': search, 'category': category, 'status': status})
    except Exception as e:
        flash(f'Error cargando productos: {str(e)}', 'error')
        return render_template('productos.html', productos=[], pagination={})

@app.route('/ocr')
def ocr_interface():
    """Interface OCR para procesamiento facturas"""
    return render_template('ocr.html')

@app.route('/reportes')
def reportes():
    """Generación reportes y exports"""
    return render_template('reportes.html')

@app.route('/compras')
def recomendaciones_compras():
    """Recomendaciones compra diarias"""
    try:
        cached_compras = cache_get('recomendaciones_compras')
        if cached_compras:
            compras_data = json.loads(cached_compras)
        else:
            compras_data = generate_purchase_recommendations()
            cache_set('recomendaciones_compras', compras_data, 300)  # Cache 5 minutos

        return render_template('compras.html', data=compras_data)
    except Exception as e:
        flash(f'Error cargando recomendaciones: {str(e)}', 'error')
        return render_template('compras.html', data={})

# ==================== API ENDPOINTS ====================

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API datos dashboard tiempo real"""
    try:
        data = generate_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productos/search')
def api_productos_search():
    """API búsqueda productos autocomplete"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT codigo, nombre, precio_venta, stock_actual 
                FROM productos 
                WHERE nombre ILIKE %s OR codigo ILIKE %s 
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))

            productos = []
            for row in cursor.fetchall():
                productos.append({
                    'codigo': row[0],
                    'nombre': row[1],
                    'precio': f"${row[2]:,.2f}",
                    'stock': row[3]
                })

            cursor.close()
            conn.close()
            return jsonify(productos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify([])

@app.route('/api/upload-factura', methods=['POST'])
def api_upload_factura():
    """API upload y procesamiento facturas OCR"""
    if 'factura' not in request.files:
        return jsonify({'error': 'No se seleccionó archivo'}), 400

    file = request.files['factura']
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Procesar OCR (simulación - integrar con sistema OCR real)
            ocr_result = process_factura_ocr(filepath)

            return jsonify({
                'success': True,
                'filename': filename,
                'ocr_result': ocr_result
            })
        except Exception as e:
            return jsonify({'error': f'Error procesando factura: {str(e)}'}), 500

    return jsonify({'error': 'Tipo archivo no permitido'}), 400

@app.route('/api/alertas')
def api_alertas():
    """API alertas stock crítico y recomendaciones"""
    try:
        alertas = generate_alertas()
        return jsonify(alertas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/demanda')
def api_charts_demanda():
    """API datos gráficos demanda predicciones"""
    try:
        producto_id = request.args.get('producto_id')
        days = int(request.args.get('days', 30))

        chart_data = generate_demand_chart_data(producto_id, days)
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== WEBSOCKETS TIEMPO REAL ====================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado - enviar datos iniciales"""
    emit('dashboard_update', generate_dashboard_data())

@socketio.on('request_update')
def handle_update_request():
    """Cliente solicita actualización datos"""
    emit('dashboard_update', generate_dashboard_data())

# ==================== FUNCIONES AUXILIARES ====================

def generate_dashboard_data():
    """Generar datos dashboard principal"""
    try:
        conn = get_db_connection()
        if not conn:
            return generate_mock_dashboard_data()

        cursor = conn.cursor()

        # KPIs principales
        cursor.execute("SELECT COUNT(*) FROM productos")
        total_productos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_actual > 0")
        productos_stock = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(stock_actual * precio_costo) FROM productos")
        valor_inventario = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_actual <= stock_minimo")
        productos_criticos = cursor.fetchone()[0]

        # Productos top ventas (simulación)
        top_productos = [
            {'nombre': 'Coca Cola 2L', 'ventas': 234, 'tendencia': '+12%'},
            {'nombre': 'Arroz 1kg', 'ventas': 189, 'tendencia': '+8%'},
            {'nombre': 'Aceite Girasol', 'ventas': 156, 'tendencia': '-3%'},
            {'nombre': 'Yerba Mate', 'ventas': 145, 'tendencia': '+15%'},
            {'nombre': 'Pan Lactal', 'ventas': 123, 'tendencia': '+5%'}
        ]

        cursor.close()
        conn.close()

        return {
            'kpis': {
                'total_productos': total_productos,
                'productos_stock': productos_stock,
                'disponibilidad': round((productos_stock / total_productos) * 100, 1) if total_productos > 0 else 0,
                'valor_inventario': valor_inventario,
                'productos_criticos': productos_criticos,
                'inflacion_diaria': valor_inventario * 0.0015  # 0.15% diario (4.5% mensual)
            },
            'top_productos': top_productos,
            'alertas': generate_alertas_summary(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error generando dashboard data: {e}")
        return generate_mock_dashboard_data()

def generate_mock_dashboard_data():
    """Datos mock para pruebas"""
    return {
        'kpis': {
            'total_productos': 847,
            'productos_stock': 831,
            'disponibilidad': 98.1,
            'valor_inventario': 629067.77,
            'productos_criticos': 12,
            'inflacion_diaria': 943.60
        },
        'top_productos': [
            {'nombre': 'Coca Cola 2L', 'ventas': 234, 'tendencia': '+12%'},
            {'nombre': 'Arroz 1kg', 'ventas': 189, 'tendencia': '+8%'},
            {'nombre': 'Aceite Girasol', 'ventas': 156, 'tendencia': '-3%'},
            {'nombre': 'Yerba Mate', 'ventas': 145, 'tendencia': '+15%'},
            {'nombre': 'Pan Lactal', 'ventas': 123, 'tendencia': '+5%'}
        ],
        'alertas': {
            'criticas': 3,
            'advertencias': 8,
            'info': 15
        },
        'timestamp': datetime.now().isoformat()
    }

def generate_alertas_summary():
    """Generar resumen alertas"""
    return {
        'criticas': 3,
        'advertencias': 8,
        'info': 15
    }

def generate_alertas():
    """Generar alertas detalladas"""
    return {
        'criticas': [
            {'tipo': 'stock_critico', 'producto': 'Azúcar 1kg', 'mensaje': 'Stock para 1.2 días', 'accion': 'Comprar urgente 50 unidades'},
            {'tipo': 'agotado', 'producto': 'Sal fina', 'mensaje': 'Producto agotado', 'accion': 'Restock inmediato'},
            {'tipo': 'vencimiento', 'producto': 'Yogur', 'mensaje': 'Vence en 2 días', 'accion': 'Liquidar con descuento'}
        ],
        'advertencias': [
            {'tipo': 'stock_bajo', 'producto': 'Arroz 1kg', 'mensaje': 'Stock para 4 días', 'accion': 'Programar pedido'},
            {'tipo': 'sobrestockeado', 'producto': 'Conservas', 'mensaje': '45 días cobertura', 'accion': 'Reducir pedidos'},
            {'tipo': 'sin_movimiento', 'producto': 'Leche polvo', 'mensaje': '30 días sin venta', 'accion': 'Promocionar producto'}
        ],
        'info': [
            {'tipo': 'precio_actualizado', 'producto': 'Aceite girasol', 'mensaje': 'Precio ajustado por inflación', 'accion': 'Revisar márgenes'},
            {'tipo': 'nueva_prediccion', 'producto': 'Bebidas', 'mensaje': 'Aumento demanda previsto +20%', 'accion': 'Aumentar stock'}
        ]
    }

def get_productos_filtered(search, category, status, page):
    """Obtener productos con filtros"""
    # Simulación - integrar con BD real
    productos_mock = []
    for i in range(20):
        productos_mock.append({
            'id': i + 1,
            'codigo': f'PROD{i+1:03d}',
            'nombre': f'Producto {i+1}',
            'categoria': 'Bebidas' if i % 3 == 0 else 'Alimentos',
            'precio_costo': 100 + (i * 10),
            'precio_venta': 150 + (i * 15),
            'stock_actual': 50 - (i * 2),
            'stock_minimo': 10,
            'estado': 'normal' if i % 4 != 0 else 'critico'
        })

    return {
        'productos': productos_mock,
        'pagination': {
            'current_page': page,
            'total_pages': 3,
            'total_items': 50
        }
    }

def generate_purchase_recommendations():
    """Generar recomendaciones compra"""
    return {
        'urgentes': [
            {'producto': 'Coca Cola 2L', 'cantidad': 24, 'costo': 28800, 'prioridad': 'CRÍTICO', 'dias_stock': 1.2},
            {'producto': 'Arroz 1kg', 'cantidad': 50, 'costo': 15000, 'prioridad': 'URGENTE', 'dias_stock': 2.8},
            {'producto': 'Aceite Girasol', 'cantidad': 12, 'costo': 9600, 'prioridad': 'NORMAL', 'dias_stock': 4.5}
        ],
        'resumen': {
            'total_productos': 3,
            'inversion_total': 53400,
            'roi_estimado': 15.4,
            'productos_criticos': 1
        }
    }

def allowed_file(filename):
    """Verificar tipo archivo permitido"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_factura_ocr(filepath):
    """Procesar factura con OCR (simulación)"""
    # Simulación - integrar con sistema OCR real
    return {
        'cuit_emisor': '20-12345678-9',
        'fecha': '22/08/2025',
        'numero_factura': '00001-00000123',
        'total': 15420.50,
        'productos': [
            {'descripcion': 'Coca Cola 2L', 'cantidad': 12, 'precio_unitario': 450.00, 'subtotal': 5400.00},
            {'descripcion': 'Arroz 1kg', 'cantidad': 20, 'precio_unitario': 350.00, 'subtotal': 7000.00},
            {'descripcion': 'Aceite Girasol', 'cantidad': 6, 'precio_unitario': 520.00, 'subtotal': 3120.00}
        ],
        'confidence': 0.94
    }

def generate_demand_chart_data(producto_id, days):
    """Generar datos gráfico demanda"""
    # Simulación - integrar con sistema ML real
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
    ventas_reales = [abs(int(50 + 20 * (0.5 - hash(date) % 100 / 100))) for date in dates]
    predicciones = [abs(int(48 + 22 * (0.5 - hash(date + 'pred') % 100 / 100))) for date in dates]

    return {
        'dates': dates,
        'ventas_reales': ventas_reales,
        'predicciones': predicciones
    }

if __name__ == '__main__':
    # Crear carpeta uploads
    os.makedirs('uploads', exist_ok=True)

    # Ejecutar aplicación
    print("🚀 Iniciando Dashboard Web Interactivo...")
    print("📱 Acceder en: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
