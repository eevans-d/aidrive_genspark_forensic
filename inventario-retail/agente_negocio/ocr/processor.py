"""
OCR Processor para facturas AFIP argentinas
EasyOCR + validaciones específicas
"""
import easyocr
import cv2
import numpy as np
from PIL import Image
import re
import logging
from typing import Dict, List, Optional
from shared.utils import validar_cuit, validar_numero_factura_afip

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        """Inicializar EasyOCR con español"""
        try:
            self.reader = easyocr.Reader(['es', 'en'])  # Español e inglés
            logger.info("✅ EasyOCR inicializado")
        except Exception as e:
            logger.error(f"Error inicializando OCR: {e}")
            self.reader = None

    async def process_image(self, image_bytes: bytes) -> Dict:
        """Procesar imagen con OCR y extraer datos AFIP"""
        if not self.reader:
            raise Exception("OCR no inicializado")

        try:
            # Convertir bytes a imagen
            image = Image.open(image_bytes)
            image_array = np.array(image)

            # Preprocesamiento básico
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array

            # OCR con EasyOCR
            results = self.reader.readtext(gray, paragraph=True)

            # Combinar texto
            full_text = " ".join([result[1] for result in results])

            # Extraer datos AFIP
            extracted_data = self._extract_afip_data(full_text)

            return {
                "texto_completo": full_text,
                "datos_extraidos": extracted_data,
                "confianza_promedio": np.mean([result[2] for result in results])
            }

        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            raise

    def _extract_afip_data(self, text: str) -> Dict:
        """Extraer datos específicos de factura AFIP"""
        data = {}

        # Buscar CUIT (XX-XXXXXXXX-X)
        cuit_pattern = r"(\d{2}-?\d{8}-?\d{1})"
        cuit_match = re.search(cuit_pattern, text)
        if cuit_match:
            cuit = cuit_match.group(1)
            is_valid, _ = validar_cuit(cuit)
            if is_valid:
                data["cuit"] = cuit

        # Buscar número de factura
        factura_patterns = [
            r"N°?\s*(\d{4,5}-\d{8})",
            r"Factura\s*N°?\s*(\d{4,5}-\d{8})",
            r"FC\s*(\d{4,5}-\d{8})"
        ]

        for pattern in factura_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["numero_factura"] = match.group(1)
                break

        # Buscar total (formato argentino)
        total_patterns = [
            r"Total\s*\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
            r"TOTAL\s*\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
            r"\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})"
        ]

        for pattern in total_patterns:
            match = re.search(pattern, text)
            if match:
                data["total"] = match.group(1)
                break

        return data
