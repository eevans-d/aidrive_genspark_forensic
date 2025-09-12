"""
Procesador de facturas E2E
"""
import json
from typing import Dict
from fastapi import UploadFile
from .ocr.processor import OCRProcessor
from .integrations.deposito_client import DepositoClient
import logging

logger = logging.getLogger(__name__)

class InvoiceProcessor:
    def __init__(self):
        self.ocr = OCRProcessor()
        self.deposito = DepositoClient()

    async def process_invoice_e2e(self, file: UploadFile, proveedor_cuit: str) -> Dict:
        """Procesar factura completo E2E"""
        try:
            # 1. OCR de la factura
            file_bytes = await file.read()
            ocr_result = await self.ocr.process_image(file_bytes)

            # 2. Simular extracción de items (en MVP real aquí iría lógica más compleja)
            items_encontrados = [
                {"codigo": "ALM000001", "cantidad": 10, "precio": 850.0},
                {"codigo": "BEB000001", "cantidad": 5, "precio": 1200.0}
            ]

            # 3. Actualizar stock para cada item
            movimientos = []
            for item in items_encontrados:
                # Buscar o crear producto en depósito
                producto = await self.deposito.buscar_o_crear_producto(item)

                # Actualizar stock
                resultado_stock = await self.deposito.actualizar_stock({
                    "producto_id": producto["id"],
                    "tipo_movimiento": "entrada",
                    "cantidad": item["cantidad"],
                    "motivo": f"Factura proveedor {proveedor_cuit}",
                    "precio_unitario": item["precio"],
                    "idempotency_key": f"factura_{proveedor_cuit}_{item['codigo']}"
                })

                movimientos.append(resultado_stock)

            return {
                "factura_id": f"PROC_{proveedor_cuit}_{len(movimientos)}",
                "ocr_data": ocr_result["datos_extraidos"],
                "items_procesados": len(movimientos),
                "movimientos": movimientos,
                "status": "completado"
            }

        except Exception as e:
            logger.error(f"Error en procesamiento E2E: {e}")
            raise
