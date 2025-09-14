 
"""
Dashboard Web Interactivo - Sistema Inventario Retail Argentino
Aplicación Flask principal con integración completa ML, OCR, Cache
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
from shared.security_headers import apply_flask_security
from shared.config import validate_env_vars
import redis
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import logging

# Importar autenticación JWT para comunicación con APIs
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.auth import auth_manager, ADMIN_ROLE

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración Flask
app = Flask(__name__)

# Métricas Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
REQUEST_COUNT = Counter('dashboard_requests_total', 'Total de requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('dashboard_request_latency_seconds', 'Latencia de requests', ['endpoint'])

# Middleware para logging y métricas
@app.before_request
def before_request_metrics():
    request._start_time = datetime.now()

@app.after_request
def after_request_metrics(response):
    process_time = (datetime.now() - getattr(request, '_start_time', datetime.now())).total_seconds()
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.path).observe(process_time)
    return response

# Endpoint /metrics Prometheus
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
validate_env_vars(["DASHBOARD_SECRET_KEY", "CORS_ORIGINS"])  # fail-fast
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# SocketIO para updates tiempo real
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
socketio = SocketIO(app, cors_allowed_origins=_cors_origins or None)
# Security headers
apply_flask_security(app)

# Redis client for real-time data
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'), 
    port=int(os.getenv('REDIS_PORT', '6379')), 
    db=int(os.getenv('REDIS_DB', '0')), 
    decode_responses=True
)

# Service URLs - Production-ready configuration
SERVICE_URLS = {
    'deposito': os.getenv('DEPOSITO_SERVICE_URL', 'http://localhost:8000'),
    'negocio': os.getenv('NEGOCIO_SERVICE_URL', 'http://localhost:8001'), 
    'ml': os.getenv('ML_SERVICE_URL', 'http://localhost:8002'),
    'scheduler': os.getenv('SCHEDULER_SERVICE_URL', 'http://localhost:8003')
}

# Simple user storage (replace with proper DB in production)
users = {
    'admin': generate_password_hash(os.getenv('ADMIN_PASSWORD', 'changeme-admin-password'))
}

def check_auth():
    """Verificar autenticación usuario"""
    return 'user' in session

def get_dashboard_token():
    """Generar token JWT para comunicación con APIs backend"""
    if 'user' in session:
        user_role = 'admin' if session['user'] == 'admin' else 'empleado'
        return auth_manager.create_access_token({
            'sub': session['user'],
            'role': user_role
        })
    return None

def get_api_data(endpoint, api='deposito'):
    """Wrapper para llamadas API GET con autenticación JWT"""
    try:
        token = get_dashboard_token()
        if not token:
            logger.error("No hay token JWT disponible")
            return None
            
        url = f"{SERVICE_URLS[api]}{endpoint}"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error GET API {api}{endpoint}: {e}")
        return None

def post_api_data(endpoint, data, api='deposito'):
    """Wrapper para llamadas API POST con autenticación JWT"""
    try:
        token = get_dashboard_token()
        if not token:
            logger.error("No hay token JWT disponible")
            return None
            
        url = f"{SERVICE_URLS[api]}{endpoint}"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error POST API {api}{endpoint}: {e}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login empleados"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            session['login_time'] = datetime.now().isoformat()
            flash(f'Bienvenido {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout usuario"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Redirigir a dashboard"""
    if not check_auth():
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard principal con métricas tiempo real"""
    if not check_auth():
        return redirect(url_for('login'))

    # Obtener datos dashboard de APIs ML
    try:
        # KPIs principales
        kpis = get_api_data('/kpis-negocio', 'ml')

        # Alertas críticas
        alertas = get_api_data('/alertas-criticas', 'ml')

        # Productos stock bajo
        stock_bajo = get_api_data('/productos/stock-bajo', 'deposito')

        # Recomendaciones compra HOY
        compras_hoy = get_api_data('/compras-urgentes', 'ml')

        # Predicciones semana
        predicciones = get_api_data('/predicciones-semana', 'ml')

        dashboard_data = {
            'kpis': kpis or {},
            'alertas': alertas or [],
            'stock_bajo': stock_bajo or [],
            'compras_hoy': compras_hoy or [],
            'predicciones': predicciones or [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error dashboard: {e}")
        return render_template('dashboard.html', data={}, error="Error cargando datos")

@app.route('/productos')
def productos():
    """Gestión productos con búsqueda y filtros"""
    if not check_auth():
        return redirect(url_for('login'))

    # Parámetros búsqueda/filtros
    search = request.args.get('search', '')
    categoria = request.args.get('categoria', '')
    estado = request.args.get('estado', '')  # stock_bajo, sobrestockeado, normal

    params = {
        'search': search,
        'categoria': categoria,
        'estado': estado
    }

    # Obtener productos con filtros
    productos_data = get_api_data('/productos', 'deposito', params)
    categorias = get_api_data('/categorias', 'deposito')

    return render_template('productos.html', 
                         productos=productos_data or [],
                         categorias=categorias or [],
                         filtros=params)

@app.route('/ocr')
def ocr():
    """Interface OCR para facturas"""
    if not check_auth():
        return redirect(url_for('login'))

    # Historial facturas procesadas
    historial = get_api_data('/ocr/historial', 'negocio')

    return render_template('ocr.html', historial=historial or [])

@app.route('/upload-factura', methods=['POST'])
def upload_factura():
    """Upload y procesamiento factura OCR"""
    if not check_auth():
        return jsonify({'error': 'No autorizado'}), 401

    if 'factura' not in request.files:
        return jsonify({'error': 'No se seleccionó archivo'}), 400

    file = request.files['factura']
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    if file:
        # Guardar archivo temporal
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        # Procesar con OCR avanzado
        with open(filepath, 'rb') as f:
            files = {'factura': f}
            try:
                response = requests.post(f"{SERVICE_URLS['negocio']}/procesar-factura-avanzado",
                                       files=files, timeout=30)
                if response.status_code == 200:
                    resultado = response.json()

                    # Emitir update WebSocket
                    socketio.emit('factura_procesada', {
                        'filename': filename,
                        'resultado': resultado,
                        'timestamp': datetime.now().isoformat()
                    })

                    return jsonify({
                        'success': True,
                        'resultado': resultado,
                        'filename': filename
                    })
                else:
                    return jsonify({'error': 'Error procesando factura'}), 500

            except Exception as e:
                logger.error(f"Error OCR: {e}")
                return jsonify({'error': f'Error OCR: {str(e)}'}), 500
            finally:
                # Limpiar archivo temporal
                if os.path.exists(filepath):
                    os.remove(filepath)

@app.route('/reportes')
def reportes():
    """Generación reportes PDF/Excel"""
    if not check_auth():
        return redirect(url_for('login'))

    return render_template('reportes.html')

@app.route('/generar-reporte', methods=['POST'])
def generar_reporte():
    """Generar reporte personalizado"""
    if not check_auth():
        return jsonify({'error': 'No autorizado'}), 401

    tipo_reporte = request.json.get('tipo')
    formato = request.json.get('formato', 'pdf')
    fecha_desde = request.json.get('fecha_desde')
    fecha_hasta = request.json.get('fecha_hasta')

    # Llamar API generación reporte
    data = {
        'tipo': tipo_reporte,
        'formato': formato,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta
    }

    resultado = post_api_data('/generar-reporte', data, 'negocio')

    if resultado:
        return jsonify({'success': True, 'url_descarga': resultado.get('url')})
    else:
        return jsonify({'error': 'Error generando reporte'}), 500

# API Endpoints para AJAX/JavaScript
@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API data dashboard tiempo real"""
    if not check_auth():
        return jsonify({'error': 'No autorizado'}), 401

    # Cache Redis 30 segundos
    cache_key = 'dashboard_data'
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    # Obtener datos frescos
    data = {
        'kpis': get_api_data('/kpis-negocio', 'ml') or {},
        'alertas': get_api_data('/alertas-criticas', 'ml') or [],
        'compras_urgentes': get_api_data('/compras-urgentes', 'ml') or [],
        'timestamp': datetime.now().isoformat()
    }

    # Cache 30 segundos
    redis_client.setex(cache_key, 30, json.dumps(data))

    return jsonify(data)

@app.route('/api/productos-autocomplete')
def api_productos_autocomplete():
    """Autocomplete productos para búsqueda"""
    if not check_auth():
        return jsonify([])

    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    productos = get_api_data(f'/productos/search?q={query}', 'deposito')

    if productos:
        suggestions = [
            {'id': p['id'], 'text': f"{p['nombre']} - {p['codigo']}"}
            for p in productos[:10]
        ]
        return jsonify(suggestions)

    return jsonify([])

# WebSocket Events
@socketio.on('connect')
def on_connect():
    """Cliente conectado WebSocket"""
    if not check_auth():
        return False

    logger.info(f"Cliente conectado: {session['user']}")
    emit('connected', {'status': 'Conectado al dashboard tiempo real'})

@socketio.on('request_dashboard_update')
def on_request_update():
    """Cliente solicita update dashboard"""
    if not check_auth():
        return

    # Enviar datos actualizados
    data = {
        'kpis': get_api_data('/kpis-negocio', 'ml') or {},
        'alertas': get_api_data('/alertas-criticas', 'ml') or [],
        'timestamp': datetime.now().isoformat()
    }

    emit('dashboard_update', data)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Crear directorio uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Ejecutar aplicación
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=int(os.getenv('FLASK_PORT', '5000')))
