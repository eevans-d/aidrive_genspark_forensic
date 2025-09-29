# CONFIGURACIONES DE PRODUCCIÓN - SISTEMA INVENTARIO RETAIL
## Resultado de aplicar PROMPT 3 con GitHub Copilot Pro

---

## 1. VARIABLES DE ENTORNO COMPLETAS

### Lista Exhaustiva de ENV Vars Necesarias

#### Variables Base del Sistema
```bash
# === CONFIGURACIÓN GENERAL ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=tu-secret-key-256-bits-muy-seguro-aqui
PYTHONPATH=/app

# === INFORMACIÓN DE LA EMPRESA ===
COMPANY_NAME="Mi Empresa SRL"
COMPANY_CUIT=20123456789
COMPANY_ADDRESS="Av. Corrientes 1234, CABA, Argentina"
COMPANY_PHONE="+54-11-4444-5555"
```

#### Base de Datos y Cache
```bash
# === POSTGRESQL ===
DATABASE_URL=postgresql://username:password@localhost:5432/inventario_retail_prod
POSTGRES_DB=inventario_retail_prod
POSTGRES_USER=inventario_user
POSTGRES_PASSWORD=postgres-super-secure-password-2024
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# === REDIS ===
REDIS_URL=redis://:redis-password@localhost:6379/0
REDIS_PASSWORD=redis-super-secure-password-2024
REDIS_HOST=localhost  
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_TTL=3600
REDIS_SESSION_TTL=86400
```

#### Servicios Multi-Agente
```bash
# === PUERTOS DE SERVICIOS ===
AGENTE_NEGOCIO_PORT=8001
AGENTE_DEPOSITO_PORT=8002
ML_SERVICE_PORT=8003
DASHBOARD_PORT=5000

# === URLS INTERNAS (para comunicación entre servicios) ===
AGENTE_NEGOCIO_URL=http://localhost:8001
AGENTE_DEPOSITO_URL=http://localhost:8002
ML_SERVICE_URL=http://localhost:8003
DASHBOARD_URL=http://localhost:5000

# === URLS EXTERNAS (para clientes) ===
PUBLIC_AGENTE_NEGOCIO_URL=https://agente-negocio.tu-dominio.com.ar
PUBLIC_AGENTE_DEPOSITO_URL=https://agente-deposito.tu-dominio.com.ar
PUBLIC_ML_SERVICE_URL=https://ml-service.tu-dominio.com.ar
PUBLIC_DASHBOARD_URL=https://dashboard.tu-dominio.com.ar
```

#### APIs Externas y Servicios de IA
```bash
# === OPENAI ===
OPENAI_API_KEY=sk-tu-clave-openai-aqui-muy-larga
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1
OPENAI_TIMEOUT=30
OPENAI_MAX_RETRIES=3

# === TELEGRAM NOTIFICATIONS ===
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-123456789
TELEGRAM_ALERTAS_ENABLED=true
TELEGRAM_NOTIFICATIONS_ENABLED=true
TELEGRAM_ERROR_NOTIFICATIONS=true
```

#### AFIP y Compliance Argentina
```bash
# === AFIP INTEGRATION ===
AFIP_ENVIRONMENT=production
AFIP_CUIT=20123456789
AFIP_CERT_PATH=/app/certs/afip_prod.crt
AFIP_KEY_PATH=/app/certs/afip_prod.key
AFIP_WSDL_URL=https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL
AFIP_CACHE_DIR=/app/cache/afip
AFIP_TIMEOUT=30

# === CONTEXTO ARGENTINO ===
TIMEZONE=America/Argentina/Buenos_Aires
LOCALE=es_AR.UTF-8
CURRENCY=ARS
INFLACION_MENSUAL=4.5
TEMPORADA=verano
IVA_RATE=21.0
```

#### Seguridad y Autenticación
```bash
# === JWT CONFIGURATION ===
JWT_SECRET_KEY=jwt-super-secret-key-256-bits-para-firmar-tokens
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=30
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# === ADMIN CREDENTIALS ===
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-password-super-seguro-2024
ADMIN_EMAIL=admin@empresa.com.ar

# === API SECURITY ===
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://dashboard.tu-dominio.com.ar,https://app.tu-dominio.com.ar
ALLOWED_HOSTS=dashboard.tu-dominio.com.ar,app.tu-dominio.com.ar,localhost
```

#### OCR y Machine Learning
```bash
# === OCR CONFIGURATION ===
OCR_ENGINE=easyocr
OCR_LANGUAGES=es,en
OCR_CONFIDENCE_THRESHOLD=0.8
TESSERACT_PATH=/usr/bin/tesseract
TESSERACT_CONFIG=--oem 3 --psm 6

# === ML MODELS ===
ML_MODEL_PATH=/app/models
ML_DEMAND_MODEL=demand_forecasting_v2.pkl
ML_PRICE_MODEL=price_optimization_v1.pkl
ML_RECOMMENDATION_MODEL=recommendation_engine_v1.pkl
ML_MODEL_CACHE_TTL=3600
ML_PREDICTION_BATCH_SIZE=100
```

#### Performance y Monitoreo
```bash
# === PERFORMANCE ===
WORKERS_COUNT=4
MAX_CONNECTIONS=100
KEEP_ALIVE_TIMEOUT=65
GRACEFUL_TIMEOUT=30
WORKER_TIMEOUT=120

# === MONITORING ===
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_ENABLED=true
HEALTH_CHECK_TIMEOUT=10
LOG_RETENTION_DAYS=30

# === CACHING ===
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=1000
CACHE_STRATEGY=lru
```

### Template .env.production
```bash
# =================================================================
# SISTEMA INVENTARIO RETAIL - CONFIGURACIÓN PRODUCCIÓN
# =================================================================
# Archivo: .env.production
# Descripción: Variables de entorno para deployment en producción
# Última actualización: $(date +%Y-%m-%d)
# =================================================================

# === CONFIGURACIÓN GENERAL ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=CAMBIAR-POR-SECRET-KEY-SEGURO-256-BITS
PYTHONPATH=/app

# === BASE DE DATOS ===
DATABASE_URL=postgresql://USUARIO:PASSWORD@HOST:5432/inventario_retail_prod
REDIS_URL=redis://:PASSWORD@HOST:6379/0

# === PUERTOS DE SERVICIOS ===
AGENTE_NEGOCIO_PORT=8001
AGENTE_DEPOSITO_PORT=8002
ML_SERVICE_PORT=8003
DASHBOARD_PORT=5000

# === APIs EXTERNAS (COMPLETAR CON VALORES REALES) ===
OPENAI_API_KEY=sk-COMPLETAR-CON-TU-CLAVE-OPENAI
TELEGRAM_BOT_TOKEN=COMPLETAR-CON-TOKEN-BOT
TELEGRAM_CHAT_ID=COMPLETAR-CON-CHAT-ID

# === AFIP (COMPLETAR CON DATOS REALES) ===
AFIP_ENVIRONMENT=production
AFIP_CUIT=COMPLETAR-CON-TU-CUIT
AFIP_CERT_PATH=/app/certs/afip_prod.crt
AFIP_KEY_PATH=/app/certs/afip_prod.key

# === SEGURIDAD (GENERAR VALORES SEGUROS) ===
JWT_SECRET_KEY=GENERAR-JWT-SECRET-KEY-SEGURO
ADMIN_PASSWORD=GENERAR-PASSWORD-ADMIN-SEGURO

# === URLS PÚBLICAS (COMPLETAR CON TUS DOMINIOS) ===
PUBLIC_DASHBOARD_URL=https://dashboard.tu-dominio.com.ar
CORS_ORIGINS=https://dashboard.tu-dominio.com.ar

# === CONTEXTO ARGENTINO ===
TIMEZONE=America/Argentina/Buenos_Aires
CURRENCY=ARS
INFLACION_MENSUAL=4.5
IVA_RATE=21.0

# =================================================================
# INSTRUCCIONES:
# 1. Copiar este archivo como .env.production
# 2. Completar TODOS los valores marcados con COMPLETAR/GENERAR
# 3. Nunca commitear este archivo con valores reales
# 4. Usar herramientas como openssl para generar secrets seguros
# =================================================================
```

---

## 2. CONFIGURACIÓN DE BASE DE DATOS

### Connection Strings para Producción
```python
# shared/database_config.py
import os
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Production database configuration
DATABASE_CONFIG = {
    'production': {
        'url': os.getenv('DATABASE_URL'),
        'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 30)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'echo': False  # Never log SQL in production
    }
}

def create_production_engine():
    """Create optimized database engine for production"""
    config = DATABASE_CONFIG['production']
    
    engine = create_engine(
        config['url'],
        poolclass=QueuePool,
        pool_size=config['pool_size'],
        max_overflow=config['max_overflow'],
        pool_timeout=config['pool_timeout'],
        pool_recycle=config['pool_recycle'],
        pool_pre_ping=config['pool_pre_ping'],
        echo=config['echo']
    )
    
    return engine

# Session factory
ProductionSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=create_production_engine()
)
```

### Configuración de Connection Pooling
```python
# shared/database.py - Production optimizations
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries in production"""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")  
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries and metrics"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log queries slower than 1 second
    if total > 1.0:
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    # Store metrics for monitoring
    if hasattr(context, 'compiled'):
        context.compiled.query_time = total

# Redis connection pool
import redis
from redis.connection import ConnectionPool

redis_pool = ConnectionPool(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    db=int(os.getenv('REDIS_DB', 0)),
    max_connections=20,
    retry_on_timeout=True,
    socket_keepalive=True,
    socket_keepalive_options={}
)

redis_client = redis.Redis(connection_pool=redis_pool)
```

### Migrations para Producción
```bash
#!/bin/bash
# scripts/run-production-migrations.sh
set -e

echo "🔄 Running production database migrations..."

# Check database connectivity
python -c "
from shared.database import engine
try:
    engine.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

# Create backup before migrations
echo "📦 Creating database backup..."
pg_dump $DATABASE_URL > "backups/pre-migration-$(date +%Y%m%d-%H%M).sql"

# Run alembic migrations
echo "🔄 Running Alembic migrations..."
alembic upgrade head

# Verify migrations
echo "✅ Verifying migrations..."
python -c "
from sqlalchemy import inspect
from shared.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables in database: {len(tables)}')
for table in tables:
    columns = inspector.get_columns(table)
    print(f'  {table}: {len(columns)} columns')

print('✅ Migration verification completed')
"

echo "🎯 Production migrations completed successfully"
```

### Seeds y Data Inicial
```python
# scripts/seed_production_data.py
import os
from shared.database import ProductionSessionLocal
from agente_deposito.models import Product, Category, Supplier
from agente_negocio.models import User, Role
from shared.security import get_password_hash

def seed_production_data():
    """Seed essential data for production environment"""
    db = ProductionSessionLocal()
    
    try:
        print("🌱 Seeding production data...")
        
        # Create admin user
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username=os.getenv('ADMIN_USERNAME', 'admin'),
                email=os.getenv('ADMIN_EMAIL', 'admin@empresa.com.ar'),
                hashed_password=get_password_hash(os.getenv('ADMIN_PASSWORD')),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            print("✅ Admin user created")
        
        # Create default categories
        default_categories = [
            {"name": "Almacén", "description": "Productos de almacén general"},
            {"name": "Bebidas", "description": "Bebidas y refrescos"},
            {"name": "Limpieza", "description": "Productos de limpieza"},
            {"name": "Higiene", "description": "Productos de higiene personal"}
        ]
        
        for cat_data in default_categories:
            if not db.query(Category).filter(Category.name == cat_data["name"]).first():
                category = Category(**cat_data)
                db.add(category)
        
        print("✅ Default categories created")
        
        # Create default supplier
        if not db.query(Supplier).filter(Supplier.name == "Proveedor Inicial").first():
            supplier = Supplier(
                name="Proveedor Inicial",
                contact_email="proveedor@email.com",
                phone="+54-11-1234-5678",
                address="Buenos Aires, Argentina"
            )
            db.add(supplier)
            print("✅ Default supplier created")
        
        db.commit()
        print("🎯 Production data seeding completed")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_production_data()
```

---

## 3. CONFIGURACIÓN DE SEGURIDAD

### CORS Setup Específico
```python
# shared/security.py - Production CORS configuration
from fastapi.middleware.cors import CORSMiddleware
import os

def configure_cors(app):
    """Configure CORS for production environment"""
    
    # Get allowed origins from environment
    cors_origins = os.getenv('CORS_ORIGINS', '').split(',')
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    
    # Production CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # Specific domains only
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type", 
            "X-Requested-With",
            "X-API-Key",
            "X-CSRFToken"
        ],
        expose_headers=["X-Total-Count", "X-Request-ID"],
        max_age=3600  # Cache preflight requests
    )
    
    return app
```

### Rate Limiting Adecuado
```python
# shared/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
import os

# Production rate limits
RATE_LIMITS = {
    'default': os.getenv('API_RATE_LIMIT', '100/minute'),
    'auth': '5/minute',  # Login attempts
    'ocr': '10/minute',  # OCR processing
    'ml': '30/minute',   # ML predictions
    'upload': '20/minute' # File uploads
}

limiter = Limiter(key_func=get_remote_address)

def create_rate_limiter():
    """Create production-ready rate limiter"""
    return limiter

# Custom rate limit exceeded handler
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom response for rate limit exceeded"""
    response = Response(
        content=f"""{{
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after": {exc.retry_after}
        }}""",
        status_code=429,
        media_type="application/json"
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    return response

# Apply to FastAPI app
def configure_rate_limiting(app):
    """Configure rate limiting for production"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    return app
```

### Headers de Seguridad
```python
# shared/security_headers.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import secrets

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Generate nonce for CSP
        nonce = secrets.token_urlsafe(16)
        
        # Security headers for production
        headers = {
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Content Type Options
            "X-Content-Type-Options": "nosniff",
            
            # Frame Options
            "X-Frame-Options": "DENY",
            
            # Content Security Policy
            "Content-Security-Policy": f"""
                default-src 'self';
                script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net;
                style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
                img-src 'self' data: https:;
                font-src 'self' https://fonts.gstatic.com;
                connect-src 'self' https://api.openai.com;
                frame-ancestors 'none';
                base-uri 'self';
                form-action 'self';
            """.replace('\n', '').replace('  ', ' '),
            
            # HSTS (only in production with HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Request ID for tracking
            "X-Request-ID": secrets.token_hex(8)
        }
        
        for header, value in headers.items():
            response.headers[header] = value
            
        return response
```

---

## 4. OPTIMIZACIÓN DE PERFORMANCE

### Configuración de Caching
```python
# shared/cache.py - Production caching strategy
import redis
import json
import pickle
from functools import wraps
from typing import Optional, Any
import hashlib
import os

class ProductionCache:
    """Production-ready caching system"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL'),
            decode_responses=False,  # For binary data
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        self.default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', 3600))
    
    def get_key(self, namespace: str, identifier: str) -> str:
        """Generate cache key with namespace"""
        return f"retail:{namespace}:{identifier}"
    
    def cache_result(self, ttl: int = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = self.get_key(
                    "func_cache", 
                    hashlib.md5(key_data.encode()).hexdigest()
                )
                
                # Try to get from cache
                try:
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        return pickle.loads(cached)
                except Exception:
                    pass  # Cache miss or error, continue
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                
                try:
                    self.redis_client.setex(
                        cache_key,
                        ttl or self.default_ttl,
                        pickle.dumps(result)
                    )
                except Exception:
                    pass  # Cache write error, ignore
                
                return result
            return wrapper
        return decorator

# Global cache instance
cache = ProductionCache()

# Cache decorators for common use cases
inventory_cache = cache.cache_result(ttl=300)  # 5 minutes
ml_prediction_cache = cache.cache_result(ttl=1800)  # 30 minutes
user_session_cache = cache.cache_result(ttl=3600)  # 1 hour
```

### Compression y Minification
```python
# shared/compression.py
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import gzip
import mimetypes

class CompressionMiddleware(BaseHTTPMiddleware):
    """Advanced compression middleware for production"""
    
    def __init__(self, app, minimum_size: int = 500):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = {
            'application/json',
            'application/javascript', 
            'text/css',
            'text/html',
            'text/plain',
            'text/xml',
            'application/xml'
        }
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Check if compression should be applied
        if not self._should_compress(request, response):
            return response
        
        # Compress response body
        return await self._compress_response(response)
    
    def _should_compress(self, request, response) -> bool:
        """Determine if response should be compressed"""
        # Check accept-encoding header
        accept_encoding = request.headers.get('accept-encoding', '')
        if 'gzip' not in accept_encoding:
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return False
        
        # Check response size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def _compress_response(self, response):
        """Compress response body with gzip"""
        # Get response body
        body = b''
        async for chunk in response.body_iterator:
            body += chunk
        
        # Compress if large enough
        if len(body) >= self.minimum_size:
            compressed_body = gzip.compress(body)
            
            # Only use compression if it actually reduces size
            if len(compressed_body) < len(body):
                response.headers['content-encoding'] = 'gzip' 
                response.headers['content-length'] = str(len(compressed_body))
                response.body_iterator = iter([compressed_body])
        
        return response
```

---

## 5. ARCHIVOS DE CONFIGURACIÓN COMPLETOS

### Dockerfile Optimizado
```dockerfile
# Dockerfile.production
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements_final.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_final.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-spa \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash retail && \
    mkdir -p /app /app/logs /app/models /app/cache /app/certs && \
    chown -R retail:retail /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=retail:retail . .

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Switch to non-root user
USER retail

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port (will be set by Railway)
EXPOSE $PORT

# Start script
CMD ["./scripts/start-production.sh"]
```

### Docker Compose para Producción
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: inventario_retail_db_prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST_AUTH_METHOD: md5
    ports:
      - "5432:5432"
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
      - ./backups:/backups
    networks:
      - retail_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: retail_redis_prod
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_prod_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - retail_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  # Agente Negocio
  agente-negocio:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: agente_negocio_prod
    environment:
      - ENVIRONMENT=production
      - SERVICE_NAME=agente-negocio
      - PORT=8001
    ports:
      - "8001:8001"
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models:ro
      - ./certs:/app/certs:ro
    networks:
      - retail_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # Agente Depósito
  agente-deposito:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: agente_deposito_prod
    environment:
      - ENVIRONMENT=production
      - SERVICE_NAME=agente-deposito
      - PORT=8002
    ports:
      - "8002:8002"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - retail_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  # ML Service
  ml-service:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: ml_service_prod
    environment:
      - ENVIRONMENT=production
      - SERVICE_NAME=ml-service
      - PORT=8003
    ports:
      - "8003:8003"
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
    networks:
      - retail_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      agente-deposito:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Dashboard Web
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: dashboard_prod
    environment:
      - ENVIRONMENT=production
      - SERVICE_NAME=dashboard
      - PORT=5000
    ports:
      - "5000:5000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data:ro
    networks:
      - retail_network
    depends_on:
      agente-negocio:
        condition: service_healthy
      agente-deposito:
        condition: service_healthy
      ml-service:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx_proxy_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    networks:
      - retail_network
    depends_on:
      - agente-negocio
      - agente-deposito
      - ml-service
      - dashboard
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.1'

volumes:
  postgres_prod_data:
    driver: local
  redis_prod_data:
    driver: local

networks:
  retail_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Script de Inicio para Producción
```bash
#!/bin/bash
# scripts/start-production.sh
set -e

echo "🚀 Starting Sistema Inventario Retail - Production Mode"

# Validate environment
if [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ ENVIRONMENT must be set to 'production'"
    exit 1
fi

# Validate required environment variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL" 
    "SECRET_KEY"
    "JWT_SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment validation passed"

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import time
import sys
from shared.database import engine
from sqlalchemy import text

max_retries = 30
for i in range(max_retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f'❌ Database connection failed after {max_retries} retries: {e}')
            sys.exit(1)
        print(f'⏳ Database not ready, retrying... ({i+1}/{max_retries})')
        time.sleep(2)
"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Start the appropriate service based on SERVICE_NAME
case $SERVICE_NAME in
    "agente-negocio")
        echo "🚀 Starting Agente Negocio..."
        cd agente_negocio
        exec gunicorn main:app \
            --bind 0.0.0.0:$PORT \
            --workers $WORKERS_COUNT \
            --worker-class uvicorn.workers.UvicornWorker \
            --worker-timeout $WORKER_TIMEOUT \
            --keep-alive $KEEP_ALIVE_TIMEOUT \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --preload \
            --access-logfile - \
            --error-logfile -
        ;;
    
    "agente-deposito")
        echo "🚀 Starting Agente Depósito..."
        cd agente_deposito
        exec gunicorn main:app \
            --bind 0.0.0.0:$PORT \
            --workers $WORKERS_COUNT \
            --worker-class uvicorn.workers.UvicornWorker \
            --worker-timeout $WORKER_TIMEOUT \
            --keep-alive $KEEP_ALIVE_TIMEOUT \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --preload \
            --access-logfile - \
            --error-logfile -
        ;;
    
    "ml-service")
        echo "🚀 Starting ML Service..."
        cd ml
        exec gunicorn main_ml_service:app \
            --bind 0.0.0.0:$PORT \
            --workers 2 \
            --worker-class uvicorn.workers.UvicornWorker \
            --worker-timeout 180 \
            --keep-alive $KEEP_ALIVE_TIMEOUT \
            --max-requests 500 \
            --max-requests-jitter 25 \
            --preload \
            --access-logfile - \
            --error-logfile -
        ;;
    
    "dashboard")
        echo "🚀 Starting Dashboard..."
        cd web_dashboard
        exec gunicorn dashboard_api:app \
            --bind 0.0.0.0:$PORT \
            --workers $WORKERS_COUNT \
            --worker-timeout $WORKER_TIMEOUT \
            --keep-alive $KEEP_ALIVE_TIMEOUT \
            --max-requests 1000 \
            --max-requests-jitter 50 \
            --access-logfile - \
            --error-logfile -
        ;;
    
    *)
        echo "❌ Unknown SERVICE_NAME: $SERVICE_NAME"
        exit 1
        ;;
esac
```

---

## 6. CONFIGURACIÓN ESPECÍFICA DE IA/AGENTES

### Variables de Entorno para APIs de IA
```bash
# === OPENAI CONFIGURATION ===
OPENAI_API_KEY=sk-tu-clave-openai-super-larga-aqui
OPENAI_ORG_ID=org-tu-organizacion-id
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1
OPENAI_TOP_P=1.0
OPENAI_FREQUENCY_PENALTY=0.0
OPENAI_PRESENCE_PENALTY=0.0

# === OPENAI TIMEOUTS AND LIMITS ===
OPENAI_TIMEOUT=30
OPENAI_MAX_RETRIES=3
OPENAI_BACKOFF_FACTOR=2
OPENAI_RATE_LIMIT_PER_MINUTE=60
OPENAI_DAILY_BUDGET_USD=50

# === MULTI-AGENT COORDINATION ===
AGENT_COMMUNICATION_TIMEOUT=10
AGENT_HEARTBEAT_INTERVAL=30
AGENT_DISCOVERY_ENABLED=true
AGENT_CIRCUIT_BREAKER_THRESHOLD=5
AGENT_CIRCUIT_BREAKER_TIMEOUT=60
```

### Configuración de Timeouts y Rate Limits
```python
# shared/ai_config.py - Production AI settings
import os
import openai
from typing import Optional
import asyncio
from functools import wraps
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AIRateLimiter:
    """Production-ready rate limiter for AI APIs"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.daily_budget = float(os.getenv('OPENAI_DAILY_BUDGET_USD', 50))
        self.daily_spent = 0.0
        self.reset_time = time.time() + 86400  # 24 hours
    
    def can_make_request(self, service: str = 'openai') -> bool:
        """Check if request can be made within rate limits"""
        now = time.time()
        
        # Reset daily budget if needed
        if now > self.reset_time:
            self.daily_spent = 0.0
            self.reset_time = now + 86400
        
        # Check daily budget
        if self.daily_spent >= self.daily_budget:
            logger.warning(f"Daily AI budget exceeded: ${self.daily_spent:.2f}")
            return False
        
        # Check rate limits
        rate_limit = int(os.getenv('OPENAI_RATE_LIMIT_PER_MINUTE', 60))
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[service] = [
            req_time for req_time in self.requests[service] 
            if req_time > minute_ago
        ]
        
        return len(self.requests[service]) < rate_limit
    
    def record_request(self, service: str, cost: float = 0.0):
        """Record a request and its cost"""
        self.requests[service].append(time.time())
        self.daily_spent += cost

# Global rate limiter
ai_rate_limiter = AIRateLimiter()

def with_ai_retry(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator for AI API calls with retry logic"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Check rate limits
                    if not ai_rate_limiter.can_make_request():
                        raise Exception("Rate limit exceeded")
                    
                    # Make the API call
                    result = await func(*args, **kwargs)
                    
                    # Record successful request
                    ai_rate_limiter.record_request('openai', 0.002)  # Estimate cost
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"AI API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"AI API call failed after {max_retries} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator

# Production OpenAI client configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.organization = os.getenv('OPENAI_ORG_ID')

# Production settings
OPENAI_CONFIG = {
    'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
    'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', 4000)),
    'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.1)),
    'top_p': float(os.getenv('OPENAI_TOP_P', 1.0)),
    'frequency_penalty': float(os.getenv('OPENAI_FREQUENCY_PENALTY', 0.0)),
    'presence_penalty': float(os.getenv('OPENAI_PRESENCE_PENALTY', 0.0)),
    'timeout': int(os.getenv('OPENAI_TIMEOUT', 30))
}
```

### Manejo de Errores de APIs Externas
```python
# shared/ai_error_handling.py
import asyncio
import logging
from enum import Enum
from typing import Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AIErrorType(Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    INVALID_RESPONSE = "invalid_response"
    NETWORK_ERROR = "network_error"

@dataclass
class AIError:
    error_type: AIErrorType
    message: str
    retry_after: Optional[int] = None
    cost: float = 0.0

class AIErrorHandler:
    """Production error handling for AI services"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.circuit_breaker_threshold = int(os.getenv('AGENT_CIRCUIT_BREAKER_THRESHOLD', 5))
        self.circuit_breaker_timeout = int(os.getenv('AGENT_CIRCUIT_BREAKER_TIMEOUT', 60))
        self.circuit_breaker_reset_time = {}
    
    def is_circuit_open(self, service: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if service not in self.circuit_breaker_reset_time:
            return False
        
        if time.time() > self.circuit_breaker_reset_time[service]:
            # Reset circuit breaker
            self.error_counts[service] = 0
            del self.circuit_breaker_reset_time[service]
            return False
        
        return True
    
    def record_error(self, service: str, error: AIError):
        """Record an error and potentially trip circuit breaker"""
        self.error_counts[service] += 1
        
        if self.error_counts[service] >= self.circuit_breaker_threshold:
            self.circuit_breaker_reset_time[service] = time.time() + self.circuit_breaker_timeout
            logger.error(f"Circuit breaker tripped for {service} after {self.error_counts[service]} errors")
    
    def handle_error(self, service: str, exception: Exception) -> AIError:
        """Convert exception to AIError and handle appropriately"""
        
        if "rate limit" in str(exception).lower():
            error = AIError(
                error_type=AIErrorType.RATE_LIMIT,
                message="API rate limit exceeded",
                retry_after=60
            )
        elif "timeout" in str(exception).lower():
            error = AIError(
                error_type=AIErrorType.TIMEOUT,
                message="API request timeout",
                retry_after=30
            )
        elif "budget" in str(exception).lower():
            error = AIError(
                error_type=AIErrorType.BUDGET_EXCEEDED,
                message="Daily budget exceeded"
            )
        else:
            error = AIError(
                error_type=AIErrorType.API_ERROR,
                message=str(exception)
            )
        
        self.record_error(service, error)
        return error

# Global error handler
ai_error_handler = AIErrorHandler()
```

### Configuración de Fallbacks
```python
# shared/ai_fallbacks.py
from typing import Any, Optional, List, Callable
import logging

logger = logging.getLogger(__name__)

class AIFallbackSystem:
    """Production fallback system for AI services"""
    
    def __init__(self):
        self.fallback_chains = {
            'ocr': [
                self._ocr_easyocr_fallback,
                self._ocr_tesseract_fallback,
                self._ocr_manual_fallback
            ],
            'text_analysis': [
                self._openai_gpt4_analysis,
                self._openai_gpt35_analysis,
                self._local_analysis_fallback
            ],
            'price_prediction': [
                self._ml_price_prediction,
                self._rule_based_pricing,
                self._static_price_fallback
            ]
        }
    
    async def execute_with_fallback(self, service: str, primary_func: Callable, *args, **kwargs) -> Any:
        """Execute function with fallback chain"""
        
        # Try primary function first
        try:
            if not ai_error_handler.is_circuit_open(service):
                result = await primary_func(*args, **kwargs)
                logger.info(f"Primary function succeeded for {service}")
                return result
        except Exception as e:
            logger.warning(f"Primary function failed for {service}: {e}")
            ai_error_handler.handle_error(service, e)
        
        # Try fallback chain
        if service in self.fallback_chains:
            for i, fallback_func in enumerate(self.fallback_chains[service]):
                try:
                    result = await fallback_func(*args, **kwargs)
                    logger.info(f"Fallback {i+1} succeeded for {service}")
                    return result
                except Exception as e:
                    logger.warning(f"Fallback {i+1} failed for {service}: {e}")
        
        # If all fallbacks fail, return safe default
        logger.error(f"All fallbacks failed for {service}, returning safe default")
        return self._get_safe_default(service)
    
    def _get_safe_default(self, service: str) -> Any:
        """Return safe default values when all systems fail"""
        defaults = {
            'ocr': {"text": "OCR temporalmente no disponible", "confidence": 0.0},
            'text_analysis': {"analysis": "Análisis no disponible", "confidence": 0.0},
            'price_prediction': {"price": 0.0, "confidence": 0.0, "method": "fallback"}
        }
        return defaults.get(service, {"error": "Service temporarily unavailable"})
    
    # Fallback implementations
    async def _ocr_easyocr_fallback(self, image_path: str) -> dict:
        """EasyOCR fallback for OCR"""
        import easyocr
        reader = easyocr.Reader(['es', 'en'])
        results = reader.readtext(image_path)
        return {
            "text": " ".join([result[1] for result in results]),
            "confidence": sum([result[2] for result in results]) / len(results) if results else 0.0,
            "method": "easyocr"
        }
    
    async def _ocr_tesseract_fallback(self, image_path: str) -> dict:
        """Tesseract fallback for OCR"""
        import pytesseract
        from PIL import Image
        
        text = pytesseract.image_to_string(Image.open(image_path), lang='spa+eng')
        return {
            "text": text.strip(),
            "confidence": 0.8,  # Tesseract doesn't provide confidence
            "method": "tesseract"
        }
    
    async def _rule_based_pricing(self, product_data: dict) -> dict:
        """Rule-based pricing fallback"""
        base_price = product_data.get('cost', 0) * 1.3  # 30% markup
        inflation_factor = 1 + (float(os.getenv('INFLACION_MENSUAL', 4.5)) / 100)
        
        return {
            "price": base_price * inflation_factor,
            "confidence": 0.7,
            "method": "rule_based"
        }

# Global fallback system
ai_fallback_system = AIFallbackSystem()
```

---

Este archivo de configuraciones de producción proporciona una base sólida, segura y optimizada para deployar el Sistema Inventario Retail Multi-Agente en un entorno de producción, con todas las consideraciones necesarias para un sistema enterprise en Argentina.