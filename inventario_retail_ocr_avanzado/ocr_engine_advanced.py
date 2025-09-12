"""
OCR Engine Avanzado para Facturas Argentinas
============================================

Motor OCR multi-engine con voting system y optimizaciones específicas
para facturas argentinas. Combina EasyOCR, Tesseract y PaddleOCR para
máxima accuracy en documentos retail argentinos.

Autor: Sistema Inventario Retail Argentino
Fecha: 2025-08-22
"""

import cv2
import numpy as np
import easyocr
import pytesseract
import paddleocr
from typing import Dict, List, Tuple, Optional
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import re
import time
from concurrent.futures import ThreadPoolExecutor

@dataclass
class OCRResult:
    """Resultado de OCR con confidence score y metadatos"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    engine: str
    processing_time: float

class FacturaType(Enum):
    """Tipos de factura argentina"""
    FACTURA_A = "A"
    FACTURA_B = "B" 
    FACTURA_C = "C"
    NOTA_CREDITO = "NC"
    NOTA_DEBITO = "ND"
    REMITO = "R"
    UNKNOWN = "UNKNOWN"

class OCREngineAdvanced:
    """OCR Engine avanzado con múltiples motores y voting system"""

    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)

        # Configurar OCR engines
        self._setup_ocr_engines()

        # Estadísticas performance
        self.stats = {
            "total_processed": 0,
            "easyocr_accuracy": [],
            "tesseract_accuracy": [], 
            "paddleocr_accuracy": [],
            "voting_accuracy": [],
            "avg_processing_time": 0
        }

    def _setup_ocr_engines(self):
        """Inicializar y configurar OCR engines"""
        try:
            # EasyOCR - Excelente para texto en imágenes naturales
            self.easyocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
            self.logger.info("EasyOCR iniciado correctamente")
        except Exception as e:
            self.logger.warning(f"Error iniciando EasyOCR: {e}")
            self.easyocr_reader = None

        try:
            # PaddleOCR - Muy bueno para documentos estructurados
            self.paddleocr_reader = paddleocr.PaddleOCR(lang='es', use_angle_cls=True, show_log=False)
            self.logger.info("PaddleOCR iniciado correctamente")
        except Exception as e:
            self.logger.warning(f"Error iniciando PaddleOCR: {e}")
            self.paddleocr_reader = None

        # Tesseract - Configurable y bueno para texto limpio
        self.tesseract_config = '--oem 3 --psm 6 -l spa+eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$.,: '

    async def process_factura(self, image_path: str, factura_type: Optional[FacturaType] = None) -> Dict:
        """
        Procesar factura con OCR avanzado

        Args:
            image_path: Ruta a la imagen de la factura
            factura_type: Tipo de factura si se conoce

        Returns:
            Dict con resultados OCR y metadatos
        """
        start_time = time.time()

        # Verificar cache
        cache_key = f"ocr_advanced:{hash(image_path)}:{factura_type}"
        if self.cache_manager:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                return cached_result

        try:
            # Cargar y preprocessar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar imagen: {image_path}")

            # Detectar tipo de factura si no se especificó
            if not factura_type:
                factura_type = self._detect_factura_type(image)

            # Ejecutar OCR con múltiples engines en paralelo
            ocr_results = await self._run_multi_ocr(image, factura_type)

            # Aplicar voting system para mejor accuracy
            final_result = self._apply_voting_system(ocr_results)

            # Postprocesamiento específico para facturas argentinas
            processed_result = self._postprocess_argentina(final_result, factura_type)

            # Calcular métricas
            processing_time = time.time() - start_time
            processed_result['processing_time'] = processing_time
            processed_result['factura_type'] = factura_type.value
            processed_result['engines_used'] = len(ocr_results)

            # Guardar en cache
            if self.cache_manager:
                await self.cache_manager.set(cache_key, processed_result, ttl=86400)  # 24h

            # Actualizar estadísticas
            self._update_stats(processing_time, final_result.confidence)

            return processed_result

        except Exception as e:
            self.logger.error(f"Error procesando factura {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _run_multi_ocr(self, image: np.ndarray, factura_type: FacturaType) -> List[OCRResult]:
        """Ejecutar OCR con múltiples engines en paralelo"""
        results = []

        # Ejecutar engines en paralelo
        with ThreadPoolExecutor(max_workers=3) as executor:
            tasks = []

            if self.easyocr_reader:
                tasks.append(executor.submit(self._run_easyocr, image))

            if self.paddleocr_reader:
                tasks.append(executor.submit(self._run_paddleocr, image))

            tasks.append(executor.submit(self._run_tesseract, image, factura_type))

            # Esperar resultados
            for future in tasks:
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Error en OCR engine: {e}")

        return results

    def _run_easyocr(self, image: np.ndarray) -> Optional[OCRResult]:
        """Ejecutar EasyOCR"""
        if not self.easyocr_reader:
            return None

        try:
            start_time = time.time()
            results = self.easyocr_reader.readtext(image)

            # Combinar texto de todos los resultados
            text_parts = []
            total_confidence = 0
            bbox_combined = [float('inf'), float('inf'), 0, 0]

            for bbox, text, confidence in results:
                if confidence > 0.3:  # Filtrar resultados de baja confianza
                    text_parts.append(text)
                    total_confidence += confidence

                    # Actualizar bounding box combinado
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                    bbox_combined[0] = min(bbox_combined[0], min(x_coords))
                    bbox_combined[1] = min(bbox_combined[1], min(y_coords))
                    bbox_combined[2] = max(bbox_combined[2], max(x_coords))
                    bbox_combined[3] = max(bbox_combined[3], max(y_coords))

            if text_parts:
                avg_confidence = total_confidence / len(text_parts)
                combined_text = " ".join(text_parts)

                return OCRResult(
                    text=combined_text,
                    confidence=avg_confidence,
                    bbox=tuple(map(int, bbox_combined)),
                    engine="EasyOCR",
                    processing_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.warning(f"Error en EasyOCR: {e}")

        return None

    def _run_paddleocr(self, image: np.ndarray) -> Optional[OCRResult]:
        """Ejecutar PaddleOCR"""
        if not self.paddleocr_reader:
            return None

        try:
            start_time = time.time()
            results = self.paddleocr_reader.ocr(image, cls=True)

            if results and results[0]:
                text_parts = []
                total_confidence = 0
                bbox_combined = [float('inf'), float('inf'), 0, 0]

                for line in results[0]:
                    if len(line) >= 2 and len(line[1]) >= 2:
                        bbox, (text, confidence) = line[0], line[1]

                        if confidence > 0.3:
                            text_parts.append(text)
                            total_confidence += confidence

                            # Actualizar bounding box
                            x_coords = [p[0] for p in bbox]
                            y_coords = [p[1] for p in bbox]
                            bbox_combined[0] = min(bbox_combined[0], min(x_coords))
                            bbox_combined[1] = min(bbox_combined[1], min(y_coords))
                            bbox_combined[2] = max(bbox_combined[2], max(x_coords))
                            bbox_combined[3] = max(bbox_combined[3], max(y_coords))

                if text_parts:
                    avg_confidence = total_confidence / len(text_parts)
                    combined_text = " ".join(text_parts)

                    return OCRResult(
                        text=combined_text,
                        confidence=avg_confidence,
                        bbox=tuple(map(int, bbox_combined)),
                        engine="PaddleOCR",
                        processing_time=time.time() - start_time
                    )

        except Exception as e:
            self.logger.warning(f"Error en PaddleOCR: {e}")

        return None

    def _run_tesseract(self, image: np.ndarray, factura_type: FacturaType) -> Optional[OCRResult]:
        """Ejecutar Tesseract con configuración optimizada"""
        try:
            start_time = time.time()

            # Configuración específica según tipo de factura
            config = self.tesseract_config
            if factura_type in [FacturaType.FACTURA_A, FacturaType.FACTURA_B]:
                config += " -c tessedit_enable_dict_correction=1"

            # OCR con Tesseract
            text = pytesseract.image_to_string(image, config=config)

            # Obtener datos adicionales para confidence score
            try:
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                confidences = [int(c) for c in data['conf'] if int(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
            except:
                avg_confidence = 0.5  # Confidence por defecto

            if text.strip():
                return OCRResult(
                    text=text.strip(),
                    confidence=avg_confidence,
                    bbox=(0, 0, image.shape[1], image.shape[0]),  # Bbox completa
                    engine="Tesseract",
                    processing_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.warning(f"Error en Tesseract: {e}")

        return None

    def _detect_factura_type(self, image: np.ndarray) -> FacturaType:
        """Detectar automáticamente el tipo de factura"""
        try:
            # OCR rápido para detectar tipo
            if self.easyocr_reader:
                results = self.easyocr_reader.readtext(image)
                text = " ".join([result[1] for result in results if result[2] > 0.5])
            else:
                text = pytesseract.image_to_string(image)

            text_upper = text.upper()

            # Patrones de detección
            if re.search(r'FACTURA\s*[:\s]*A', text_upper):
                return FacturaType.FACTURA_A
            elif re.search(r'FACTURA\s*[:\s]*B', text_upper):
                return FacturaType.FACTURA_B
            elif re.search(r'FACTURA\s*[:\s]*C', text_upper):
                return FacturaType.FACTURA_C
            elif re.search(r'NOTA\s+CREDITO|NOTA\s+DE\s+CREDITO', text_upper):
                return FacturaType.NOTA_CREDITO
            elif re.search(r'NOTA\s+DEBITO|NOTA\s+DE\s+DEBITO', text_upper):
                return FacturaType.NOTA_DEBITO
            elif re.search(r'REMITO', text_upper):
                return FacturaType.REMITO

        except Exception as e:
            self.logger.warning(f"Error detectando tipo factura: {e}")

        return FacturaType.UNKNOWN

    def _apply_voting_system(self, ocr_results: List[OCRResult]) -> OCRResult:
        """Aplicar voting system para combinar resultados de múltiples engines"""
        if not ocr_results:
            return OCRResult("", 0.0, (0, 0, 0, 0), "NoEngine", 0.0)

        if len(ocr_results) == 1:
            return ocr_results[0]

        # Estrategia: usar el resultado con mayor confidence, pero validar consistencia
        ocr_results.sort(key=lambda x: x.confidence, reverse=True)
        best_result = ocr_results[0]

        # Verificar consistencia entre engines
        texts = [result.text for result in ocr_results]

        # Calcular similitud entre textos
        similarities = []
        for i in range(len(texts)):
            for j in range(i+1, len(texts)):
                similarity = self._calculate_text_similarity(texts[i], texts[j])
                similarities.append(similarity)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0

        # Ajustar confidence basado en consenso entre engines
        consensus_confidence = best_result.confidence * avg_similarity

        return OCRResult(
            text=best_result.text,
            confidence=consensus_confidence,
            bbox=best_result.bbox,
            engine=f"Voting({len(ocr_results)}engines)",
            processing_time=sum(r.processing_time for r in ocr_results)
        )

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud entre dos textos"""
        if not text1 or not text2:
            return 0.0

        # Normalizar textos
        t1 = re.sub(r'[^a-zA-Z0-9]', '', text1.lower())
        t2 = re.sub(r'[^a-zA-Z0-9]', '', text2.lower())

        if not t1 or not t2:
            return 0.0

        # Similitud por caracteres comunes
        common_chars = set(t1) & set(t2)
        total_chars = set(t1) | set(t2)

        return len(common_chars) / len(total_chars) if total_chars else 0.0

    def _postprocess_argentina(self, ocr_result: OCRResult, factura_type: FacturaType) -> Dict:
        """Postprocesamiento específico para facturas argentinas"""
        try:
            text = ocr_result.text

            # Extraer campos específicos argentinos
            campos = self._extract_campos_argentinos(text, factura_type)

            return {
                "success": True,
                "text_raw": text,
                "confidence": ocr_result.confidence,
                "bbox": ocr_result.bbox,
                "engine": ocr_result.engine,
                "campos_extraidos": campos,
                "factura_type": factura_type.value,
                "validation_passed": self._validate_campos_argentinos(campos)
            }

        except Exception as e:
            self.logger.error(f"Error en postprocesamiento: {e}")
            return {
                "success": False,
                "error": str(e),
                "text_raw": ocr_result.text,
                "confidence": ocr_result.confidence
            }

    def _extract_campos_argentinos(self, text: str, factura_type: FacturaType) -> Dict:
        """Extraer campos específicos de facturas argentinas"""
        campos = {}

        # Patrones regex para campos argentinos
        patterns = {
            "cuit": r'CUIT[:\s]*(\d{2}-\d{8}-\d{1}|\d{11})',
            "numero_factura": r'N°[:\s]*(\d{4}-\d{8}|\d+)',
            "fecha": r'FECHA[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            "razon_social": r'RAZON\s+SOCIAL[:\s]*([A-Z\s]+)',
            "total": r'TOTAL[:\s]*\$?[\s]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "iva": r'IVA[:\s]*\$?[\s]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "subtotal": r'SUBTOTAL[:\s]*\$?[\s]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'
        }

        for campo, pattern in patterns.items():
            match = re.search(pattern, text.upper())
            if match:
                campos[campo] = match.group(1).strip()

        # Postprocesamiento específico
        if "cuit" in campos:
            # Normalizar formato CUIT
            cuit = re.sub(r'\D', '', campos["cuit"])
            if len(cuit) == 11:
                campos["cuit"] = f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"

        # Normalizar montos argentinos
        for campo in ["total", "iva", "subtotal"]:
            if campo in campos:
                # Convertir formato argentino a float
                monto_str = campos[campo].replace(".", "").replace(",", ".")
                try:
                    campos[f"{campo}_float"] = float(monto_str)
                except ValueError:
                    pass

        return campos

    def _validate_campos_argentinos(self, campos: Dict) -> bool:
        """Validar campos extraídos según normativas argentinas"""
        try:
            # Validar CUIT
            if "cuit" in campos:
                cuit = re.sub(r'\D', '', campos["cuit"])
                if len(cuit) != 11:
                    return False
                # Validar dígito verificador CUIT (simplificado)
                # En producción usar algoritmo completo AFIP

            # Validar montos
            if "total_float" in campos and "subtotal_float" in campos:
                if campos["total_float"] < campos["subtotal_float"]:
                    return False

            return True

        except Exception:
            return False

    def _update_stats(self, processing_time: float, confidence: float):
        """Actualizar estadísticas de performance"""
        self.stats["total_processed"] += 1

        # Actualizar tiempo promedio
        n = self.stats["total_processed"]
        prev_avg = self.stats["avg_processing_time"]
        self.stats["avg_processing_time"] = ((prev_avg * (n-1)) + processing_time) / n

    def get_stats(self) -> Dict:
        """Obtener estadísticas de performance del OCR"""
        return {
            **self.stats,
            "engines_available": {
                "easyocr": self.easyocr_reader is not None,
                "paddleocr": self.paddleocr_reader is not None,
                "tesseract": True  # Siempre disponible
            }
        }

    async def health_check(self) -> Dict:
        """Health check del sistema OCR"""
        health = {
            "status": "healthy",
            "engines": {},
            "cache": "unknown"
        }

        # Test engines
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "TEST 123", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Test EasyOCR
        try:
            if self.easyocr_reader:
                self.easyocr_reader.readtext(test_image)
                health["engines"]["easyocr"] = "ok"
            else:
                health["engines"]["easyocr"] = "not_available"
        except Exception as e:
            health["engines"]["easyocr"] = f"error: {e}"

        # Test PaddleOCR
        try:
            if self.paddleocr_reader:
                self.paddleocr_reader.ocr(test_image)
                health["engines"]["paddleocr"] = "ok"
            else:
                health["engines"]["paddleocr"] = "not_available"
        except Exception as e:
            health["engines"]["paddleocr"] = f"error: {e}"

        # Test Tesseract
        try:
            pytesseract.image_to_string(test_image)
            health["engines"]["tesseract"] = "ok"
        except Exception as e:
            health["engines"]["tesseract"] = f"error: {e}"

        # Test cache
        if self.cache_manager:
            try:
                await self.cache_manager.set("health_test", "ok", ttl=60)
                test_value = await self.cache_manager.get("health_test")
                health["cache"] = "ok" if test_value == "ok" else "error"
            except Exception as e:
                health["cache"] = f"error: {e}"

        # Determinar estado general
        engine_errors = [status for status in health["engines"].values() if status.startswith("error")]
        if engine_errors:
            health["status"] = "degraded"

        return health

# Ejemplo de uso
if __name__ == "__main__":
    import asyncio

    async def test_ocr():
        ocr_engine = OCREngineAdvanced()

        # Health check
        health = await ocr_engine.health_check()
        print("OCR Health:", health)

        # Stats
        stats = ocr_engine.get_stats()
        print("OCR Stats:", stats)

    asyncio.run(test_ocr())
