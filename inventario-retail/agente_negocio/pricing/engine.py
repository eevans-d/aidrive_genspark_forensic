"""
Motor de precios con inflación automática argentina
"""
from shared.config import get_settings
from shared.utils import calcular_precio_con_inflacion
from shared.database import get_db
from shared.models import Producto
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class PricingEngine:
    async def calcular_precio_inflacion(self, codigo: str, dias_transcurridos: int) -> float:
        """Calcular precio con inflación aplicada"""
        db = next(get_db())

        try:
            # Buscar producto
            producto = db.query(Producto).filter(Producto.codigo == codigo).first()
            if not producto:
                raise Exception(f"Producto {codigo} no encontrado")

            # Aplicar inflación
            precio_actualizado = calcular_precio_con_inflacion(
                producto.precio_compra,
                dias_transcurridos,
                settings.INFLACION_MENSUAL
            )

            logger.info(f"Precio actualizado - {codigo}: ${precio_actualizado:.2f}")
            return precio_actualizado

        finally:
            db.close()
