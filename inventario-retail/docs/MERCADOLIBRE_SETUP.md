# Guía de Configuración MercadoLibre - Sistema de Inventario Argentino

## Introducción

Esta guía te ayudará a configurar la integración con MercadoLibre para sincronización automática de stock, precios, órdenes y respuestas a preguntas. La integración permite mantener tu catálogo actualizado y procesar ventas automáticamente.

## Prerrequisitos

### 1. Requisitos MercadoLibre
- Cuenta de vendedor en MercadoLibre Argentina
- Publicaciones activas en MercadoLibre
- Acceso a MercadoLibre Developers

### 2. Requisitos Técnicos
- Python 3.8 o superior
- Acceso a internet para API de MercadoLibre
- Servidor con IP pública (para webhooks, opcional)

## Paso 1: Crear Aplicación en MercadoLibre

### 1.1 Acceder a Developers
1. Ve a [MercadoLibre Developers](https://developers.mercadolibre.com.ar)
2. Inicia sesión con tu cuenta de MercadoLibre
3. Ve a "Mis aplicaciones"

### 1.2 Crear Nueva Aplicación
1. Haz clic en "Crear aplicación"
2. Completa los datos:
   - **Nombre**: Sistema de Inventario
   - **Descripción**: Integración para gestión de inventario
   - **URL de la aplicación**: https://tudominio.com
   - **Callback URL**: https://tudominio.com/ml/callback
   - **Scopes necesarios**:
     - `read` - Leer información básica
     - `write` - Escribir información
     - `offline_access` - Acceso offline

3. Guarda **App ID** y **Client Secret**

### 1.3 Configurar Redirect URI
```bash
# Si no tienes dominio, puedes usar localhost para testing
Redirect URI: http://localhost:8080/ml/callback
```

## Paso 2: Obtener Tokens de Acceso

### 2.1 Autorización Inicial
```python
# Script para obtener tokens iniciales
import requests
from urllib.parse import urlencode

# Configuración de tu aplicación
APP_ID = "tu_app_id"
CLIENT_SECRET = "tu_client_secret"
REDIRECT_URI = "http://localhost:8080/ml/callback"

# URL de autorización
auth_url = f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}"

print("1. Ve a esta URL para autorizar la aplicación:")
print(auth_url)
print("\n2. Después de autorizar, copia el código de la URL de respuesta")
print("3. El código estará en: http://localhost:8080/ml/callback?code=TG-XXXXXXXX")

code = input("Ingresa el código obtenido: ")

# Intercambiar código por tokens
token_url = "https://api.mercadolibre.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": APP_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "redirect_uri": REDIRECT_URI
}

response = requests.post(token_url, data=data)
tokens = response.json()

print("\n✅ Tokens obtenidos:")
print(f"Access Token: {tokens['access_token']}")
print(f"Refresh Token: {tokens['refresh_token']}")
print(f"Expira en: {tokens['expires_in']} segundos")
```

### 2.2 Renovación Automática de Tokens
```python
# Función para renovar tokens automáticamente
async def renovar_token(refresh_token: str):
    data = {
        "grant_type": "refresh_token",
        "client_id": APP_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token
    }

    response = requests.post("https://api.mercadolibre.com/oauth/token", data=data)
    return response.json()
```

## Paso 3: Configurar el Sistema

### 3.1 Editar Configuración
Edita el archivo `.env.integrations`:

```bash
# Credenciales MercadoLibre
ML_APP_ID=1234567890123456
ML_CLIENT_SECRET=AbCdEfGhIjKlMnOpQrStUvWxYz
ML_REDIRECT_URI=http://localhost:8080/ml/callback

# Tokens (obtenidos en el paso anterior)
ML_ACCESS_TOKEN=APP_USR-1234567890123456-abcdef-ghijklmnopqrstuvwxyz123456-987654321
ML_REFRESH_TOKEN=TG-abcdef1234567890abcdef1234567890abcdef12

# ID del vendedor (tu user ID en MercadoLibre)
ML_SELLER_ID=123456789

# Configuración de sincronización
ML_SYNC_STOCK_ACTIVO=true
ML_SYNC_PRECIOS_ACTIVO=true
ML_SYNC_ORDENES_ACTIVO=true
ML_SYNC_PREGUNTAS_ACTIVO=true
```

### 3.2 Obtener Seller ID
```python
# Script para obtener tu Seller ID
import requests

access_token = "tu_access_token"
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get("https://api.mercadolibre.com/users/me", headers=headers)
user_info = response.json()

print(f"Seller ID: {user_info['id']}")
print(f"Nickname: {user_info['nickname']}")
print(f"Sitio: {user_info['site_id']}")
```

## Paso 4: Mapear Productos con Publicaciones

### 4.1 Obtener Publicaciones Existentes
```python
from integrations.ecommerce.mercadolibre_client import MercadoLibreClient, MLCredentials

# Configurar cliente
credentials = MLCredentials(
    app_id="tu_app_id",
    client_secret="tu_client_secret",
    access_token="tu_access_token",
    refresh_token="tu_refresh_token"
)

client = MercadoLibreClient(credentials)

# Obtener publicaciones
publicaciones = await client.obtener_publicaciones_activas()

print("Publicaciones encontradas:")
for pub in publicaciones:
    print(f"- {pub['id']}: {pub['title']} (Stock: {pub['available_quantity']})")
```

### 4.2 Mapear en Base de Datos
```sql
-- Crear tabla de mapeo producto-publicación
CREATE TABLE producto_ml_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id VARCHAR(50) NOT NULL,
    ml_item_id VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE(producto_id, ml_item_id)
);

-- Insertar mapeos
INSERT INTO producto_ml_mapping (producto_id, ml_item_id) VALUES
('PROD001', 'MLA123456789'),
('PROD002', 'MLA987654321');
```

## Paso 5: Configurar Webhooks (Opcional)

### 5.1 Crear Webhook
```python
# Script para configurar webhook
import requests

access_token = "tu_access_token"
headers = {"Authorization": f"Bearer {access_token}"}

webhook_data = {
    "topic": "orders",
    "callback_url": "https://tudominio.com/webhook/ml/orders",
    "secret": "tu_secreto_webhook"
}

response = requests.post(
    "https://api.mercadolibre.com/applications/{app_id}/notifications",
    headers=headers,
    json=webhook_data
)

print("Webhook creado:", response.json())
```

### 5.2 Manejar Webhooks
```python
# Endpoint para recibir webhooks
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/ml/orders', methods=['POST'])
def handle_ml_webhook():
    # Verificar firma (opcional pero recomendado)
    signature = request.headers.get('X-Hub-Signature')
    if signature:
        expected = hmac.new(
            webhook_secret.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, f"sha256={expected}"):
            return "Invalid signature", 401

    # Procesar webhook
    data = request.json

    if data.get('topic') == 'orders':
        order_id = data.get('resource')
        # Procesar nueva orden
        asyncio.create_task(procesar_nueva_orden(order_id))

    return jsonify({"status": "ok"})
```

## Paso 6: Testing y Validación

### 6.1 Test de Conexión
```python
# Test básico de conexión
async def test_mercadolibre():
    from integrations.ecommerce.mercadolibre_client import MercadoLibreClient, MLCredentials

    credentials = MLCredentials(
        app_id="tu_app_id",
        client_secret="tu_client_secret", 
        access_token="tu_access_token",
        refresh_token="tu_refresh_token"
    )

    client = MercadoLibreClient(credentials)

    try:
        # Test obtener publicaciones
        publicaciones = await client.obtener_publicaciones_activas()
        print(f"✅ Conexión exitosa: {len(publicaciones)} publicaciones")

        # Test actualizar stock
        if publicaciones:
            item_id = publicaciones[0]['id']
            resultado = await client.update_item_stock(item_id, 99)
            print(f"✅ Update stock: {resultado}")

        # Test obtener órdenes
        ordenes = await client.obtener_ordenes_pendientes()
        print(f"✅ Órdenes pendientes: {len(ordenes)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Ejecutar test
import asyncio
asyncio.run(test_mercadolibre())
```

### 6.2 Test de Sincronización
```python
# Test completo de sincronización
from schedulers.ecommerce_scheduler import crear_ecommerce_sync_scheduler

# Crear scheduler
ml_client = MercadoLibreClient(credentials)
scheduler = criar_ecommerce_sync_scheduler(ml_client)

# Ejecutar sync manual
resultado = await scheduler.ejecutar_sync_manual(
    TipoSyncEcommerce.SYNC_STOCK
)

print("Resultado sync:", resultado)
```

## Paso 7: Configuración para Producción

### 7.1 Configurar Rate Limiting
```bash
# En .env.integrations
ML_RATE_LIMIT_REQUESTS=3000
ML_RATE_LIMIT_PERIOD=3600
```

### 7.2 Configurar Monitoreo
```python
# Script de monitoreo MercadoLibre
from schedulers.ecommerce_scheduler import crear_ecommerce_sync_scheduler

scheduler = crear_ecommerce_sync_scheduler(ml_client)
estado = scheduler.obtener_estado_syncs()

print("Estado sincronizaciones ML:")
for sync in estado:
    print(f"- {sync['descripcion']}: {'✅' if sync['activa'] else '❌'}")
```

### 7.3 Configurar Alertas
```bash
# Configurar alertas por email/Slack
EMAIL_ENABLED=true
EMAIL_TO_ERRORS=admin@tuempresa.com

SLACK_ENABLED=true
SLACK_CANAL_ECOMMERCE_SYNC=#ecommerce-sync
```

## Troubleshooting

### Error: "Invalid grant"
- Verificar que el código no haya expirado (duran 10 minutos)
- Comprobar que el redirect_uri coincida exactamente
- Verificar App ID y Client Secret

### Error: "Forbidden" (403)
- Verificar que el access token no haya expirado
- Comprobar scopes de la aplicación
- Renovar tokens usando refresh token

### Error: "Rate limit exceeded"
- Verificar límites de API (3000 req/hora)
- Implementar backoff exponencial
- Distribuir requests en el tiempo

### Error: "Item not found"
- Verificar que el item_id exista y sea tuyo
- Comprobar que la publicación no esté eliminada
- Verificar permisos sobre la publicación

## Funcionalidades Avanzadas

### 7.1 Respuestas Automáticas
```python
# Configurar respuestas automáticas a preguntas
respuestas_automaticas = {
    "envío": "¡Hola! Los envíos se realizan dentro de las 24hs hábiles.",
    "factura": "¡Hola! Sí, emitimos factura A y B según corresponda.",
    "stock": "¡Hola! Tenemos stock disponible."
}
```

### 7.2 Gestión de Precios Dinámicos
```python
# Actualizar precios según reglas de negocio
def calcular_precio_ml(precio_base, margen_ml=0.15):
    return precio_base * (1 + margen_ml)
```

### 7.3 Análisis de Performance
```python
# Obtener métricas de rendimiento
metricas = await client.obtener_metricas()
print(f"Nivel vendedor: {metricas['nivel_vendedor']}")
print(f"Calificación: {metricas['reputacion']['calificaciones']['positivas']}%")
```

## Mantenimiento

### Renovación de Tokens
- Los access tokens expiran cada 6 horas
- Los refresh tokens expiran cada 6 meses
- Implementar renovación automática

### Monitoreo de Salud
- Verificar conexión API cada 5 minutos
- Monitorear rate limits
- Alertar sobre errores críticos

### Backup de Configuración
```bash
# Backup de configuración ML
tar -czf ml_backup_$(date +%Y%m%d).tar.gz .env.integrations logs/ecommerce_integration.log
```

## Contacto y Soporte

### MercadoLibre
- **Developers**: https://developers.mercadolibre.com.ar
- **Centro de Ayuda**: https://ayuda.mercadolibre.com.ar
- **API Status**: https://developers.mercadolibre.com.ar/status

### Sistema  
- Revisar logs en `logs/ecommerce_integration.log`
- Usar mocks para testing sin afectar produción
- Consultar documentación de API MercadoLibre

---

**⚠️ Importante**: Mantener tokens seguros, respetar rate limits y probar en sandbox antes de producción.
