"""
Cliente HTTP para comunicación con AgenteDepósito
"""
import httpx
import logging
from typing import Dict, Optional
from shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DepositoClient:
    def __init__(self):
        self.base_url = settings.AGENTE_DEPOSITO_URL
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    async def health_check(self) -> bool:
        """Verificar conectividad con AgenteDepósito"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

    async def buscar_o_crear_producto(self, item: Dict) -> Dict:
        """Buscar producto o crear si no existe"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Simular búsqueda/creación
                producto_data = {
                    "codigo": item["codigo"],
                    "nombre": f"Producto {item['codigo']}",
                    "categoria": "Importado",
                    "precio_compra": item["precio"],
                    "stock_actual": 0,
                    "stock_minimo": 5
                }

                # Intentar crear producto
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
                    productos = search_response.json()["productos"]
                    return productos[0] if productos else None

        except Exception as e:
            logger.error(f"Error buscando/creando producto: {e}")
            raise

    async def actualizar_stock(self, stock_data: Dict) -> Dict:
        """Actualizar stock en AgenteDepósito"""
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
