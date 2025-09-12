"""
Cliente MercadoLibre API para sincronización de stock y precios
Implementación completa para e-commerce argentino
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

@dataclass
class MLCredentials:
    """Credenciales MercadoLibre"""
    app_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    user_id: str
    environment: str = "production"  # "sandbox" o "production"

    @property
    def base_url(self) -> str:
        if self.environment == "sandbox":
            return "https://api.mercadolibre.com"
        return "https://api.mercadolibre.com"

@dataclass
class MLProduct:
    """Producto MercadoLibre"""
    id: str
    title: str
    price: float
    available_quantity: int
    condition: str = "new"
    category_id: str = ""
    pictures: List[str] = None
    attributes: List[Dict] = None

    def __post_init__(self):
        if self.pictures is None:
            self.pictures = []
        if self.attributes is None:
            self.attributes = []

class MLRateLimiter:
    """Rate limiter para API MercadoLibre (3000 req/hour)"""

    def __init__(self, max_requests: int = 3000, window_hours: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_hours * 3600
        self.requests_made = []

    def can_make_request(self) -> bool:
        """Verificar si podemos hacer request"""
        now = time.time()
        # Limpiar requests antiguos
        self.requests_made = [
            req_time for req_time in self.requests_made 
            if now - req_time < self.window_seconds
        ]

        return len(self.requests_made) < self.max_requests

    def wait_if_needed(self):
        """Esperar si es necesario para respetar rate limit"""
        if not self.can_make_request():
            oldest_request = min(self.requests_made)
            sleep_time = self.window_seconds - (time.time() - oldest_request) + 1
            logger.info(f"Rate limit alcanzado, esperando {sleep_time:.1f} segundos")
            time.sleep(sleep_time)

    def record_request(self):
        """Registrar que hicimos un request"""
        self.requests_made.append(time.time())

class MercadoLibreClient:
    """Cliente MercadoLibre API para gestión de inventario"""

    def __init__(self, credentials: MLCredentials):
        self.credentials = credentials
        self.rate_limiter = MLRateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {credentials.access_token}',
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Hacer request con rate limiting y retry"""
        self.rate_limiter.wait_if_needed()

        url = f"{self.credentials.base_url}{endpoint}"

        for attempt in range(3):  # 3 intentos
            try:
                self.rate_limiter.record_request()
                response = self.session.request(method, url, **kwargs)

                if response.status_code == 401:
                    # Token expirado, intentar refresh
                    if self._refresh_token():
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.credentials.access_token}'
                        })
                        continue
                    else:
                        raise Exception("No se pudo renovar el token de acceso")

                if response.status_code == 429:
                    # Rate limit excedido
                    wait_time = int(response.headers.get('X-RateLimit-Reset', 60))
                    logger.warning(f"Rate limit excedido, esperando {wait_time}s")
                    time.sleep(wait_time)
                    continue

                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"Error en request (intento {attempt + 1}): {e}")
                if attempt == 2:  # último intento
                    raise
                time.sleep(2 ** attempt)  # backoff exponencial

        raise Exception("Max intentos alcanzados")

    def _refresh_token(self) -> bool:
        """Renovar access token usando refresh token"""
        try:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.credentials.app_id,
                'client_secret': self.credentials.client_secret,
                'refresh_token': self.credentials.refresh_token
            }

            response = requests.post(
                f"{self.credentials.base_url}/oauth/token",
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.credentials.access_token = token_data['access_token']
                if 'refresh_token' in token_data:
                    self.credentials.refresh_token = token_data['refresh_token']

                logger.info("Token MercadoLibre renovado exitosamente")
                return True

            logger.error(f"Error renovando token: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Excepción renovando token: {e}")
            return False

    def get_user_info(self) -> Dict:
        """Obtener información del usuario"""
        response = self._make_request('GET', f'/users/{self.credentials.user_id}')

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo info usuario: {response.status_code}")

    def get_user_items(self, status: str = "active", limit: int = 50, offset: int = 0) -> Dict:
        """Obtener publicaciones del usuario"""
        params = {
            'status': status,
            'limit': limit,
            'offset': offset
        }

        response = self._make_request(
            'GET', 
            f'/users/{self.credentials.user_id}/items/search',
            params=params
        )

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo items: {response.status_code}")

    def get_item_details(self, item_id: str) -> Dict:
        """Obtener detalles de una publicación"""
        response = self._make_request('GET', f'/items/{item_id}')

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo item {item_id}: {response.status_code}")

    def update_item_stock(self, item_id: str, available_quantity: int) -> Dict:
        """Actualizar stock de una publicación"""
        data = {
            'available_quantity': available_quantity
        }

        response = self._make_request(
            'PUT',
            f'/items/{item_id}',
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Stock actualizado para {item_id}: {available_quantity}")
            return result

        raise Exception(f"Error actualizando stock {item_id}: {response.status_code}")

    def update_item_price(self, item_id: str, price: float) -> Dict:
        """Actualizar precio de una publicación"""
        data = {
            'price': price
        }

        response = self._make_request(
            'PUT',
            f'/items/{item_id}',
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Precio actualizado para {item_id}: ${price}")
            return result

        raise Exception(f"Error actualizando precio {item_id}: {response.status_code}")

    def pause_item(self, item_id: str) -> Dict:
        """Pausar publicación (stock = 0)"""
        data = {
            'status': 'paused'
        }

        response = self._make_request(
            'PUT',
            f'/items/{item_id}',
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Item pausado: {item_id}")
            return result

        raise Exception(f"Error pausando item {item_id}: {response.status_code}")

    def reactivate_item(self, item_id: str) -> Dict:
        """Reactivar publicación pausada"""
        data = {
            'status': 'active'
        }

        response = self._make_request(
            'PUT',
            f'/items/{item_id}',
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Item reactivado: {item_id}")
            return result

        raise Exception(f"Error reactivando item {item_id}: {response.status_code}")

    def get_orders(self, seller_id: str = None, status: str = None, limit: int = 50) -> Dict:
        """Obtener órdenes de venta"""
        if seller_id is None:
            seller_id = self.credentials.user_id

        params = {
            'seller': seller_id,
            'limit': limit
        }

        if status:
            params['order.status'] = status

        response = self._make_request(
            'GET',
            '/orders/search',
            params=params
        )

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo órdenes: {response.status_code}")

    def get_order_details(self, order_id: str) -> Dict:
        """Obtener detalles de una orden"""
        response = self._make_request('GET', f'/orders/{order_id}')

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo orden {order_id}: {response.status_code}")

    def bulk_update_stock(self, updates: List[Dict[str, Any]]) -> List[Dict]:
        """Actualizar stock en lote (más eficiente)"""
        results = []

        for update in updates:
            try:
                item_id = update['item_id']
                quantity = update['available_quantity']

                result = self.update_item_stock(item_id, quantity)
                results.append({
                    'item_id': item_id,
                    'success': True,
                    'result': result
                })

            except Exception as e:
                logger.error(f"Error actualizando {update.get('item_id')}: {e}")
                results.append({
                    'item_id': update.get('item_id'),
                    'success': False,
                    'error': str(e)
                })

        return results

    def bulk_update_prices(self, updates: List[Dict[str, Any]]) -> List[Dict]:
        """Actualizar precios en lote"""
        results = []

        for update in updates:
            try:
                item_id = update['item_id']
                price = update['price']

                result = self.update_item_price(item_id, price)
                results.append({
                    'item_id': item_id,
                    'success': True,
                    'result': result
                })

            except Exception as e:
                logger.error(f"Error actualizando precio {update.get('item_id')}: {e}")
                results.append({
                    'item_id': update.get('item_id'),
                    'success': False,
                    'error': str(e)
                })

        return results

    def get_categories(self, category_id: str = None) -> List[Dict]:
        """Obtener categorías disponibles"""
        if category_id:
            response = self._make_request('GET', f'/categories/{category_id}')
        else:
            response = self._make_request('GET', '/sites/MLA/categories')

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error obteniendo categorías: {response.status_code}")

    def search_items(self, query: str, category: str = None, limit: int = 50) -> Dict:
        """Buscar items en MercadoLibre"""
        params = {
            'site_id': 'MLA',  # Argentina
            'q': query,
            'limit': limit
        }

        if category:
            params['category'] = category

        response = self._make_request(
            'GET',
            '/sites/MLA/search',
            params=params
        )

        if response.status_code == 200:
            return response.json()

        raise Exception(f"Error buscando items: {response.status_code}")

# Funciones de utilidad
def crear_mapping_productos_ml(productos_locales: List[Dict], ml_items: List[Dict]) -> Dict[str, str]:
    """Crear mapping entre productos locales y items MercadoLibre"""
    mapping = {}

    for producto in productos_locales:
        codigo = producto.get('codigo', '')
        nombre = producto.get('nombre', '')

        # Buscar match por nombre similar
        for ml_item in ml_items:
            ml_title = ml_item.get('title', '').lower()

            if (codigo.lower() in ml_title or 
                any(word in ml_title for word in nombre.lower().split() if len(word) > 3)):
                mapping[codigo] = ml_item['id']
                break

    return mapping

def calcular_precio_ml_con_comision(precio_base: float, comision_ml: float = 0.11) -> float:
    """Calcular precio MercadoLibre incluyendo comisión"""
    # Precio final = precio_base / (1 - comision_ml)
    precio_ml = precio_base / (1 - comision_ml)
    return round(precio_ml, 2)

if __name__ == "__main__":
    # Ejemplo de uso (requiere credenciales válidas)
    credentials = MLCredentials(
        app_id="your_app_id",
        client_secret="your_client_secret",
        access_token="your_access_token",
        refresh_token="your_refresh_token",
        user_id="your_user_id",
        environment="sandbox"
    )

    client = MercadoLibreClient(credentials)

    try:
        # Obtener info usuario
        user_info = client.get_user_info()
        print(f"Usuario: {user_info.get('nickname')}")

        # Obtener items
        items = client.get_user_items()
        print(f"Items activos: {items.get('paging', {}).get('total', 0)}")

        # Actualizar stock de ejemplo
        if items.get('results'):
            first_item = items['results'][0]
            result = client.update_item_stock(first_item['id'], 10)
            print(f"Stock actualizado: {result.get('available_quantity')}")

    except Exception as e:
        print(f"Error: {e}")
