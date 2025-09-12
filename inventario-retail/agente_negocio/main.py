"""
AgenteNegocio - FastAPI App para OCR facturas AFIP y pricing inflación
Puerto 8001 con integración completa al AgenteDepósito
"""
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings, setup_logging
from .ocr.processor import OCRProcessor
from .pricing.engine import PricingEngine
from .invoice.processor import InvoiceProcessor
from .integrations.deposito_client import DepositoClient

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="AgenteNegocio - OCR & Pricing", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Inicializar componentes
ocr_processor = OCRProcessor()
pricing_engine = PricingEngine()
invoice_processor = InvoiceProcessor()
deposito_client = DepositoClient()

@app.get("/health")
async def health():
    """Health check con conectividad AgenteDepósito"""
    try:
        deposito_status = await deposito_client.health_check()
        return {
            "status": "healthy",
            "service": "agente_negocio",
            "timestamp": datetime.utcnow().isoformat(),
            "deposito_status": "connected" if deposito_status else "disconnected"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/precios/consultar")
async def consultar_precio(codigo: str, dias_desde_compra: int = 0):
    """Consultar precio con inflación aplicada"""
    try:
        precio = await pricing_engine.calcular_precio_inflacion(codigo, dias_desde_compra)
        return {
            "codigo": codigo,
            "precio_actualizado": precio,
            "dias_transcurridos": dias_desde_compra,
            "inflacion_aplicada": settings.INFLACION_MENSUAL
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/facturas/procesar")
async def procesar_factura(file: UploadFile = File(...), proveedor_cuit: str = Form(...)):
    """Procesar factura E2E: OCR → Pricing → Stock Update"""
    try:
        logger.info(f"Procesando factura de proveedor CUIT: {proveedor_cuit}")

        # Procesar factura completa
        resultado = await invoice_processor.process_invoice_e2e(file, proveedor_cuit)

        logger.info(f"Factura procesada exitosamente: {resultado['factura_id']}")
        return resultado

    except Exception as e:
        logger.error(f"Error procesando factura: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup():
    logger.info("🧠 AgenteNegocio iniciado - Puerto 8001")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.AGENTE_NEGOCIO_PORT, reload=True)
