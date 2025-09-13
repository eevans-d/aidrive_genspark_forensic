
"""
Cliente para integración con Agente Depósito.
Provee métodos para verificar conectividad y operaciones remotas: búsqueda/creación de productos, consulta y actualización de stock.
"""

# Imports principales
import httpx
import logging
from typing import Dict, Optional
from shared.config import get_settings

# Inicialización de logger y settings
logger = logging.getLogger(__name__)
settings = get_settings()


class DepositoClient:
    def __init__(self):
        """
        Inicializa el cliente con el endpoint y timeout configurados.
        """
        self.base_url = settings.AGENTE_DEPOSITO_URL
        self.timeout = settings.HTTP_TIMEOUT_SECONDS


    async def health_check(self) -> bool:
        """
        Verifica la conectividad con el Agente Depósito.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error health_check: {e}")
            return False


    async def buscar_o_crear_producto(self, item: Dict) -> Dict:
        """
        Busca un producto por código o lo crea si no existe.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                producto_data = {
                    "codigo": item["codigo"],
                    "nombre": f"Producto {item['codigo']}",
                    "categoria": "Importado",
                    "precio_compra": item["precio"],
                    "stock_actual": 0,
                    "stock_minimo": 5
                }
                response = await client.post(
                    f"{self.base_url}/productos",
                    json=producto_data
                )
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    # Si ya existe, buscar por código
                    search_response = await client.get(
                        f"{self.base_url}/productos",
                        params={"codigo": item["codigo"]}
                    )
                    productos = search_response.json().get("productos", [])
                    return productos[0] if productos else None
        except Exception as e:
            logger.error(f"Error buscando/creando producto: {e}")
            raise


    async def get_producto_by_codigo(self, codigo: str) -> Optional[Dict]:
        """
        Obtiene un producto específico por código para PricingEngine.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/productos",
                    params={"codigo": codigo}
                )
                if response.status_code == 200:
                    productos = response.json().get("productos", [])
                    return productos[0] if productos else None
                return None
        except Exception as e:
            logger.error(f"Error obteniendo producto {codigo}: {e}")
            return None


    async def actualizar_stock(self, stock_data: Dict) -> Dict:
        """
        Actualiza el stock en Agente Depósito.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/stock/update",
                    json=stock_data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error actualizando stock: {e}")
            raise
