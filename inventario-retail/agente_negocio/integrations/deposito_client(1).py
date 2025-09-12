"""
AgenteNegocio - Deposito Integration Client
Cliente HTTP robusto para integración con sistemas de depósito
"""

import logging
import asyncio
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import aiohttp
import requests
from urllib.parse import urljoin, urlencode
import time
from pathlib import Path

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestMethod(Enum):
    """Métodos HTTP soportados"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class AuthType(Enum):
    """Tipos de autenticación soportados"""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"

class RetryStrategy(Enum):
    """Estrategias de reintento"""
    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"

@dataclass
class RequestConfig:
    """Configuración para requests HTTP"""
    timeout: int = 30
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retry_delay: float = 1.0
    backoff_factor: float = 2.0

    # Headers por defecto
    default_headers: Dict[str, str] = field(default_factory=lambda: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'AgenteNegocio/1.0'
    })

    # Configuración SSL
    verify_ssl: bool = True
    ssl_cert_path: Optional[str] = None

    # Rate limiting
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_window: int = 60     # seconds

@dataclass
class AuthConfig:
    """Configuración de autenticación"""
    auth_type: AuthType = AuthType.NONE

    # Bearer token
    bearer_token: Optional[str] = None
    token_expiry: Optional[datetime] = None

    # Basic auth
    username: Optional[str] = None
    password: Optional[str] = None

    # API Key
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"

    # OAuth2
    oauth2_token_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None

@dataclass
class Response:
    """Respuesta HTTP estructurada"""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]] = None

    # Metadata de la request
    url: str = ""
    method: str = ""
    request_time: float = 0.0
    attempts: int = 1

    @property
    def is_success(self) -> bool:
        """Verifica si la respuesta fue exitosa"""
        return 200 <= self.status_code < 300

    @property
    def is_client_error(self) -> bool:
        """Verifica si es error del cliente (4xx)"""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Verifica si es error del servidor (5xx)"""
        return 500 <= self.status_code < 600

    def json(self) -> Dict[str, Any]:
        """Obtiene contenido JSON de la respuesta"""
        if self.json_data is None:
            try:
                self.json_data = json.loads(self.text)
            except json.JSONDecodeError:
                raise ValueError(f"Response is not valid JSON: {self.text[:200]}...")
        return self.json_data

class RateLimiter:
    """Limitador de velocidad para requests"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Espera hasta que se pueda hacer una request"""
        async with self._lock:
            now = time.time()

            # Remover requests antiguas
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]

            # Si hemos alcanzado el límite, esperar
            if len(self.requests) >= self.max_requests:
                oldest_request = min(self.requests)
                wait_time = self.window_seconds - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)

            # Registrar esta request
            self.requests.append(now)

class DepositoClient:
    """
    Cliente HTTP robusto para integraciones con sistemas de depósito
    Soporta autenticación, reintentos, rate limiting y manejo de errores
    """

    def __init__(self, 
                 base_url: str,
                 auth_config: Optional[AuthConfig] = None,
                 request_config: Optional[RequestConfig] = None):
        """
        Inicializa el cliente

        Args:
            base_url: URL base del API
            auth_config: Configuración de autenticación
            request_config: Configuración de requests
        """
        self.base_url = base_url.rstrip('/')
        self.auth_config = auth_config or AuthConfig()
        self.request_config = request_config or RequestConfig()

        # Rate limiter
        self.rate_limiter = RateLimiter(
            self.request_config.rate_limit_requests,
            self.request_config.rate_limit_window
        )

        # Session para requests síncronos
        self._sync_session = None

        # Métricas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_retries': 0,
            'avg_response_time': 0.0
        }

        logger.info(f"DepositoClient inicializado - Base URL: {self.base_url}")

    def _get_sync_session(self) -> requests.Session:
        """Obtiene o crea session síncrona"""
        if self._sync_session is None:
            self._sync_session = requests.Session()
            self._sync_session.headers.update(self.request_config.default_headers)
        return self._sync_session

    def _prepare_auth_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Prepara headers de autenticación"""
        auth_headers = headers.copy()

        if self.auth_config.auth_type == AuthType.BEARER:
            if self.auth_config.bearer_token:
                auth_headers['Authorization'] = f"Bearer {self.auth_config.bearer_token}"

        elif self.auth_config.auth_type == AuthType.API_KEY:
            if self.auth_config.api_key:
                auth_headers[self.auth_config.api_key_header] = self.auth_config.api_key

        return auth_headers

    def _prepare_auth(self, session: requests.Session):
        """Prepara autenticación para session síncrona"""
        if self.auth_config.auth_type == AuthType.BASIC:
            if self.auth_config.username and self.auth_config.password:
                session.auth = (self.auth_config.username, self.auth_config.password)

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calcula delay para reintento"""
        if self.request_config.retry_strategy == RetryStrategy.FIXED:
            return self.request_config.retry_delay

        elif self.request_config.retry_strategy == RetryStrategy.EXPONENTIAL:
            return self.request_config.retry_delay * (self.request_config.backoff_factor ** (attempt - 1))

        elif self.request_config.retry_strategy == RetryStrategy.LINEAR:
            return self.request_config.retry_delay * attempt

        return 0.0

    def _should_retry(self, response: Response, attempt: int) -> bool:
        """Determina si se debe reintentar la request"""
        if attempt >= self.request_config.max_retries:
            return False

        # Reintentar en errores de servidor o timeouts
        if response.is_server_error:
            return True

        # Reintentar en ciertos errores específicos
        if response.status_code in [408, 429, 502, 503, 504]:
            return True

        return False

    async def request_async(self, 
                          method: RequestMethod,
                          endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None,
                          files: Optional[Dict[str, Any]] = None) -> Response:
        """
        Realiza request HTTP asíncrona

        Args:
            method: Método HTTP
            endpoint: Endpoint relativo
            data: Datos para el body
            params: Parámetros de query
            headers: Headers adicionales
            files: Archivos para upload

        Returns:
            Response: Respuesta estructurada
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Preparar headers
        request_headers = self.request_config.default_headers.copy()
        if headers:
            request_headers.update(headers)
        request_headers = self._prepare_auth_headers(request_headers)

        # Rate limiting
        await self.rate_limiter.acquire()

        # Preparar datos
        json_data = None
        if data and not files:
            json_data = data

        # Realizar request con reintentos
        last_response = None
        for attempt in range(1, self.request_config.max_retries + 2):
            try:
                start_time = time.time()

                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.request_config.timeout),
                    connector=aiohttp.TCPConnector(verify_ssl=self.request_config.verify_ssl)
                ) as session:

                    async with session.request(
                        method.value,
                        url,
                        json=json_data,
                        data=data if files else None,
                        params=params,
                        headers=request_headers
                    ) as resp:

                        content = await resp.read()
                        text = content.decode('utf-8', errors='ignore')

                        response = Response(
                            status_code=resp.status,
                            headers=dict(resp.headers),
                            content=content,
                            text=text,
                            url=str(resp.url),
                            method=method.value,
                            request_time=time.time() - start_time,
                            attempts=attempt
                        )

                # Actualizar estadísticas
                self.stats['total_requests'] += 1
                if response.is_success:
                    self.stats['successful_requests'] += 1
                else:
                    self.stats['failed_requests'] += 1

                # Si es exitosa, retornar
                if response.is_success:
                    return response

                last_response = response

                # Verificar si debe reintentar
                if not self._should_retry(response, attempt):
                    break

                # Esperar antes del reintento
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Request failed (attempt {attempt}), retrying in {delay}s. "
                                 f"Status: {response.status_code}, URL: {url}")
                    await asyncio.sleep(delay)
                    self.stats['total_retries'] += 1

            except asyncio.TimeoutError:
                logger.error(f"Request timeout (attempt {attempt}): {url}")
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    self.stats['total_retries'] += 1
                else:
                    raise

            except Exception as e:
                logger.error(f"Request error (attempt {attempt}): {url} - {str(e)}")
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    self.stats['total_retries'] += 1
                else:
                    raise

        # Si llegamos aquí, todos los reintentos fallaron
        if last_response:
            logger.error(f"All retry attempts failed for {url}. Last status: {last_response.status_code}")
            return last_response
        else:
            raise RuntimeError(f"All retry attempts failed for {url}")

    def request_sync(self, 
                    method: RequestMethod,
                    endpoint: str,
                    data: Optional[Dict[str, Any]] = None,
                    params: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None,
                    files: Optional[Dict[str, Any]] = None) -> Response:
        """
        Realiza request HTTP síncrona

        Args:
            method: Método HTTP
            endpoint: Endpoint relativo
            data: Datos para el body
            params: Parámetros de query
            headers: Headers adicionales
            files: Archivos para upload

        Returns:
            Response: Respuesta estructurada
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        session = self._get_sync_session()

        # Preparar headers
        request_headers = self.request_config.default_headers.copy()
        if headers:
            request_headers.update(headers)
        request_headers = self._prepare_auth_headers(request_headers)

        # Preparar autenticación
        self._prepare_auth(session)

        # Realizar request con reintentos
        last_response = None
        for attempt in range(1, self.request_config.max_retries + 2):
            try:
                start_time = time.time()

                # Preparar argumentos
                kwargs = {
                    'timeout': self.request_config.timeout,
                    'headers': request_headers,
                    'verify': self.request_config.verify_ssl
                }

                if params:
                    kwargs['params'] = params

                if files:
                    kwargs['files'] = files
                    if data:
                        kwargs['data'] = data
                elif data:
                    kwargs['json'] = data

                resp = session.request(method.value, url, **kwargs)

                response = Response(
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    content=resp.content,
                    text=resp.text,
                    url=resp.url,
                    method=method.value,
                    request_time=time.time() - start_time,
                    attempts=attempt
                )

                # Actualizar estadísticas
                self.stats['total_requests'] += 1
                if response.is_success:
                    self.stats['successful_requests'] += 1
                else:
                    self.stats['failed_requests'] += 1

                # Si es exitosa, retornar
                if response.is_success:
                    return response

                last_response = response

                # Verificar si debe reintentar
                if not self._should_retry(response, attempt):
                    break

                # Esperar antes del reintento
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(f"Request failed (attempt {attempt}), retrying in {delay}s. "
                                 f"Status: {response.status_code}, URL: {url}")
                    time.sleep(delay)
                    self.stats['total_retries'] += 1

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout (attempt {attempt}): {url}")
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    time.sleep(delay)
                    self.stats['total_retries'] += 1
                else:
                    raise

            except Exception as e:
                logger.error(f"Request error (attempt {attempt}): {url} - {str(e)}")
                if attempt <= self.request_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    time.sleep(delay)
                    self.stats['total_retries'] += 1
                else:
                    raise

        # Si llegamos aquí, todos los reintentos fallaron
        if last_response:
            logger.error(f"All retry attempts failed for {url}. Last status: {last_response.status_code}")
            return last_response
        else:
            raise RuntimeError(f"All retry attempts failed for {url}")

    # Métodos convenientes
    async def get_async(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                       headers: Optional[Dict[str, str]] = None) -> Response:
        """GET asíncrono"""
        return await self.request_async(RequestMethod.GET, endpoint, params=params, headers=headers)

    async def post_async(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None) -> Response:
        """POST asíncrono"""
        return await self.request_async(RequestMethod.POST, endpoint, data=data, headers=headers)

    async def put_async(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                       headers: Optional[Dict[str, str]] = None) -> Response:
        """PUT asíncrono"""
        return await self.request_async(RequestMethod.PUT, endpoint, data=data, headers=headers)

    async def delete_async(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Response:
        """DELETE asíncrono"""
        return await self.request_async(RequestMethod.DELETE, endpoint, headers=headers)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
           headers: Optional[Dict[str, str]] = None) -> Response:
        """GET síncrono"""
        return self.request_sync(RequestMethod.GET, endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Response:
        """POST síncrono"""
        return self.request_sync(RequestMethod.POST, endpoint, data=data, headers=headers)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
           headers: Optional[Dict[str, str]] = None) -> Response:
        """PUT síncrono"""
        return self.request_sync(RequestMethod.PUT, endpoint, data=data, headers=headers)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Response:
        """DELETE síncrono"""
        return self.request_sync(RequestMethod.DELETE, endpoint, headers=headers)

    def refresh_token(self) -> bool:
        """
        Refresca el token OAuth2 si es necesario

        Returns:
            bool: True si se refrescó exitosamente
        """
        if (self.auth_config.auth_type != AuthType.OAUTH2 or 
            not self.auth_config.oauth2_token_url or
            not self.auth_config.refresh_token):
            return False

        try:
            # Preparar datos para refresh
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.auth_config.refresh_token,
                'client_id': self.auth_config.client_id,
                'client_secret': self.auth_config.client_secret
            }

            # Hacer request de refresh
            resp = requests.post(
                self.auth_config.oauth2_token_url,
                data=refresh_data,
                timeout=self.request_config.timeout
            )

            if resp.status_code == 200:
                token_data = resp.json()
                self.auth_config.bearer_token = token_data.get('access_token')

                # Calcular expiración
                expires_in = token_data.get('expires_in', 3600)
                self.auth_config.token_expiry = datetime.now() + timedelta(seconds=expires_in)

                # Actualizar refresh token si viene
                if 'refresh_token' in token_data:
                    self.auth_config.refresh_token = token_data['refresh_token']

                logger.info("Token OAuth2 refrescado exitosamente")
                return True
            else:
                logger.error(f"Error refrescando token: {resp.status_code} - {resp.text}")
                return False

        except Exception as e:
            logger.error(f"Error refrescando token OAuth2: {str(e)}")
            return False

    def is_token_expired(self) -> bool:
        """Verifica si el token está expirado"""
        if not self.auth_config.token_expiry:
            return False

        # Considerar expirado si queda menos de 5 minutos
        return datetime.now() + timedelta(minutes=5) >= self.auth_config.token_expiry

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cliente"""
        total_requests = self.stats['total_requests']
        if total_requests > 0:
            success_rate = (self.stats['successful_requests'] / total_requests) * 100
            avg_retries = self.stats['total_retries'] / total_requests
        else:
            success_rate = 0.0
            avg_retries = 0.0

        return {
            'total_requests': total_requests,
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate_percent': round(success_rate, 2),
            'total_retries': self.stats['total_retries'],
            'average_retries_per_request': round(avg_retries, 2),
            'average_response_time_ms': round(self.stats['avg_response_time'] * 1000, 2)
        }

    def reset_stats(self):
        """Resetea las estadísticas"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_retries': 0,
            'avg_response_time': 0.0
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._sync_session:
            self._sync_session.close()

# Clientes especializados para diferentes sistemas
class DepositoAPIClient(DepositoClient):
    """Cliente especializado para API de depósito"""

    def __init__(self, base_url: str, api_key: str):
        auth_config = AuthConfig(
            auth_type=AuthType.API_KEY,
            api_key=api_key,
            api_key_header="X-Deposito-API-Key"
        )

        request_config = RequestConfig(
            timeout=45,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL
        )

        super().__init__(base_url, auth_config, request_config)

    async def get_products_async(self, category: Optional[str] = None, 
                               limit: int = 100) -> Response:
        """Obtiene productos del depósito"""
        params = {'limit': limit}
        if category:
            params['category'] = category

        return await self.get_async('products', params=params)

    async def create_order_async(self, order_data: Dict[str, Any]) -> Response:
        """Crea una orden en el depósito"""
        return await self.post_async('orders', data=order_data)

    async def get_order_status_async(self, order_id: str) -> Response:
        """Obtiene el estado de una orden"""
        return await self.get_async(f'orders/{order_id}')

    async def update_inventory_async(self, product_id: str, 
                                   quantity: int) -> Response:
        """Actualiza inventario de un producto"""
        data = {'quantity': quantity}
        return await self.put_async(f'products/{product_id}/inventory', data=data)

    def get_products(self, category: Optional[str] = None, limit: int = 100) -> Response:
        """Versión síncrona de get_products_async"""
        params = {'limit': limit}
        if category:
            params['category'] = category

        return self.get('products', params=params)

    def create_order(self, order_data: Dict[str, Any]) -> Response:
        """Versión síncrona de create_order_async"""
        return self.post('orders', data=order_data)

# Funciones de utilidad
def create_deposito_client(base_url: str, api_key: str) -> DepositoAPIClient:
    """Crea cliente especializado para depósito"""
    return DepositoAPIClient(base_url, api_key)

def create_oauth2_client(base_url: str, client_id: str, client_secret: str,
                        token_url: str) -> DepositoClient:
    """Crea cliente con autenticación OAuth2"""
    auth_config = AuthConfig(
        auth_type=AuthType.OAUTH2,
        client_id=client_id,
        client_secret=client_secret,
        oauth2_token_url=token_url
    )

    return DepositoClient(base_url, auth_config)

async def health_check_async(client: DepositoClient, 
                           endpoint: str = 'health') -> Dict[str, Any]:
    """
    Realiza health check asíncrono

    Args:
        client: Cliente HTTP
        endpoint: Endpoint de health check

    Returns:
        Dict: Resultado del health check
    """
    try:
        start_time = time.time()
        response = await client.get_async(endpoint)
        end_time = time.time()

        return {
            'status': 'healthy' if response.is_success else 'unhealthy',
            'status_code': response.status_code,
            'response_time_ms': round((end_time - start_time) * 1000, 2),
            'url': response.url,
            'attempts': response.attempts
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'response_time_ms': -1
        }

def health_check(client: DepositoClient, endpoint: str = 'health') -> Dict[str, Any]:
    """Versión síncrona del health check"""
    try:
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()

        return {
            'status': 'healthy' if response.is_success else 'unhealthy',
            'status_code': response.status_code,
            'response_time_ms': round((end_time - start_time) * 1000, 2),
            'url': response.url,
            'attempts': response.attempts
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'response_time_ms': -1
        }
