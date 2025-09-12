"""
AgenteNegocio - OCR Processor
EasyOCR optimizado para español con detección automática de layouts de facturas
"""

import easyocr
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import cv2
from dataclasses import dataclass
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Resultado de OCR con metadata completa"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    coordinates: List[List[int]]     # Coordenadas exactas del polígono
    line_number: int
    region_type: str  # 'header', 'body', 'footer', 'table', 'signature'

@dataclass
class DocumentLayout:
    """Layout detectado del documento"""
    header_region: Tuple[int, int, int, int]
    body_region: Tuple[int, int, int, int]
    footer_region: Tuple[int, int, int, int]
    table_regions: List[Tuple[int, int, int, int]]
    signature_regions: List[Tuple[int, int, int, int]]

class OCRProcessor:
    """
    Procesador OCR optimizado para facturas argentinas
    Usa EasyOCR con configuraciones específicas para español
    """

    def __init__(self, 
                 languages: List[str] = ['es', 'en'],
                 gpu: bool = False,
                 model_storage_directory: Optional[str] = None,
                 confidence_threshold: float = 0.4):
        """
        Inicializa el procesador OCR

        Args:
            languages: Lista de idiomas a detectar
            gpu: Usar GPU si está disponible
            model_storage_directory: Directorio para modelos OCR
            confidence_threshold: Umbral mínimo de confianza
        """
        self.languages = languages
        self.gpu = gpu
        self.confidence_threshold = confidence_threshold
        self._reader = None
        self._lock = threading.Lock()

        logger.info(f"OCRProcessor configurado - Idiomas: {languages}, GPU: {gpu}, Threshold: {confidence_threshold}")

        # Patrones específicos para facturas argentinas
        self.invoice_patterns = {
            'fecha': [r'\d{2}/\d{2}/\d{4}', r'\d{2}-\d{2}-\d{4}'],
            'cuit': [r'\d{2}-\d{8}-\d{1}', r'\d{11}'],
            'numero_factura': [r'N[°º]\s*\d+', r'Nº\s*\d+', r'Factura\s*\d+'],
            'montos': [r'\$\s*[\d,.]+'​, r'[\d,]+\.\d{2}'],
            'codigo_afip': [r'Cod\.\s*\d{2}', r'Código\s*\d{2}']
        }

    @property
    def reader(self):
        """Lazy loading del reader OCR"""
        if self._reader is None:
            with self._lock:
                if self._reader is None:
                    try:
                        logger.info("Inicializando EasyOCR reader...")
                        self._reader = easyocr.Reader(
                            self.languages, 
                            gpu=self.gpu,
                            verbose=False
                        )
                        logger.info("EasyOCR reader inicializado exitosamente")
                    except Exception as e:
                        logger.error(f"Error inicializando EasyOCR: {str(e)}")
                        raise
        return self._reader

    def process_image(self, 
                     image: Union[str, Path, np.ndarray], 
                     detect_layout: bool = True,
                     paragraph: bool = True) -> List[OCRResult]:
        """
        Procesa una imagen con OCR

        Args:
            image: Imagen a procesar (ruta o array numpy)
            detect_layout: Detectar regiones del documento
            paragraph: Agrupar texto en párrafos

        Returns:
            List[OCRResult]: Lista de resultados OCR
        """
        start_time = time.time()

        try:
            # Cargar imagen si es necesario
            if isinstance(image, (str, Path)):
                image_array = cv2.imread(str(image))
                if image_array is None:
                    raise ValueError(f"No se pudo cargar la imagen: {image}")
                image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                image_array = image

            logger.info(f"Procesando imagen - Shape: {image_array.shape}")

            # Detectar layout si se solicita
            layout = None
            if detect_layout:
                layout = self._detect_document_layout(image_array)

            # Ejecutar OCR
            raw_results = self.reader.readtext(
                image_array,
                paragraph=paragraph,
                width_ths=0.7,
                height_ths=0.7,
                detail=1
            )

            # Procesar resultados
            ocr_results = self._process_ocr_results(raw_results, layout, image_array.shape)

            # Filtrar por confianza
            filtered_results = [r for r in ocr_results if r.confidence >= self.confidence_threshold]

            processing_time = time.time() - start_time
            logger.info(f"OCR completado - {len(filtered_results)} elementos detectados en {processing_time:.2f}s")

            return filtered_results

        except Exception as e:
            logger.error(f"Error en procesamiento OCR: {str(e)}")
            raise

    def _detect_document_layout(self, image: np.ndarray) -> DocumentLayout:
        """
        Detecta el layout del documento usando análisis de contenido
        """
        try:
            height, width = image.shape[:2]

            # Regiones por defecto basadas en proporciones típicas de facturas
            header_region = (0, 0, width, int(height * 0.25))
            body_region = (0, int(height * 0.25), width, int(height * 0.75))
            footer_region = (0, int(height * 0.75), width, height)

            # Detectar posibles tablas usando contornos
            table_regions = self._detect_table_regions(image)

            # Detectar áreas de firma (generalmente en la parte inferior derecha)
            signature_regions = [(int(width * 0.6), int(height * 0.8), width, height)]

            layout = DocumentLayout(
                header_region=header_region,
                body_region=body_region,
                footer_region=footer_region,
                table_regions=table_regions,
                signature_regions=signature_regions
            )

            logger.info(f"Layout detectado - Tablas: {len(table_regions)}")
            return layout

        except Exception as e:
            logger.warning(f"Error detectando layout: {str(e)}")
            # Layout por defecto
            height, width = image.shape[:2]
            return DocumentLayout(
                header_region=(0, 0, width, int(height * 0.3)),
                body_region=(0, int(height * 0.3), width, int(height * 0.7)),
                footer_region=(0, int(height * 0.7), width, height),
                table_regions=[],
                signature_regions=[]
            )

    def _detect_table_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta regiones que contienen tablas"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Detectar líneas horizontales y verticales
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            # Operaciones morfológicas para detectar líneas
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)

            # Combinar líneas
            table_mask = cv2.add(horizontal_lines, vertical_lines)

            # Encontrar contornos de posibles tablas
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            table_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filtrar regiones muy pequeñas
                if w > 100 and h > 50:
                    table_regions.append((x, y, x + w, y + h))

            return table_regions

        except Exception as e:
            logger.warning(f"Error detectando tablas: {str(e)}")
            return []

    def _process_ocr_results(self, 
                           raw_results: List, 
                           layout: Optional[DocumentLayout],
                           image_shape: Tuple[int, int, int]) -> List[OCRResult]:
        """Procesa los resultados raw de OCR"""
        processed_results = []

        for i, (coordinates, text, confidence) in enumerate(raw_results):
            # Limpiar texto
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                continue

            # Calcular bounding box
            coords_array = np.array(coordinates)
            x1, y1 = coords_array.min(axis=0).astype(int)
            x2, y2 = coords_array.max(axis=0).astype(int)
            bbox = (x1, y1, x2, y2)

            # Determinar región del documento
            region_type = self._determine_region_type(bbox, layout)

            # Crear resultado
            ocr_result = OCRResult(
                text=cleaned_text,
                confidence=confidence,
                bbox=bbox,
                coordinates=coordinates,
                line_number=i,
                region_type=region_type
            )

            processed_results.append(ocr_result)

        return processed_results

    def _clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto extraído"""
        if not text:
            return ""

        # Normalizar espacios
        cleaned = ' '.join(text.split())

        # Correcciones específicas para OCR en español
        replacements = {
            'º': '°',
            '|': 'I',
            '0': 'O',  # Solo en contextos específicos
            'rn': 'm',
            'ii': 'll',
            'fi': 'fi',
            'cl': 'd'
        }

        # Aplicar correcciones contextuales
        for old, new in replacements.items():
            if old in cleaned:
                # Aquí se podrían agregar reglas más sofisticadas
                cleaned = cleaned.replace(old, new)

        return cleaned

    def _determine_region_type(self, 
                             bbox: Tuple[int, int, int, int], 
                             layout: Optional[DocumentLayout]) -> str:
        """Determina el tipo de región basado en la posición"""
        if layout is None:
            return 'body'

        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Verificar cada tipo de región
        if self._point_in_region((center_x, center_y), layout.header_region):
            return 'header'
        elif self._point_in_region((center_x, center_y), layout.footer_region):
            return 'footer'
        elif any(self._point_in_region((center_x, center_y), table) for table in layout.table_regions):
            return 'table'
        elif any(self._point_in_region((center_x, center_y), sig) for sig in layout.signature_regions):
            return 'signature'
        else:
            return 'body'

    def _point_in_region(self, point: Tuple[float, float], region: Tuple[int, int, int, int]) -> bool:
        """Verifica si un punto está dentro de una región"""
        x, y = point
        x1, y1, x2, y2 = region
        return x1 <= x <= x2 and y1 <= y <= y2

    def extract_structured_data(self, ocr_results: List[OCRResult]) -> Dict:
        """
        Extrae datos estructurados de los resultados OCR

        Args:
            ocr_results: Resultados del OCR

        Returns:
            Dict: Datos estructurados extraídos
        """
        structured_data = {
            'header_info': [],
            'body_content': [],
            'table_data': [],
            'footer_info': [],
            'raw_text': '',
            'detected_patterns': {}
        }

        # Agrupar por región
        for result in ocr_results:
            region_key = f"{result.region_type}_{'info' if result.region_type != 'body' else 'content'}"
            if result.region_type == 'table':
                region_key = 'table_data'

            if region_key in structured_data:
                structured_data[region_key].append({
                    'text': result.text,
                    'confidence': result.confidence,
                    'bbox': result.bbox,
                    'line_number': result.line_number
                })

        # Texto completo
        structured_data['raw_text'] = '\n'.join([r.text for r in ocr_results])

        # Detectar patrones específicos
        structured_data['detected_patterns'] = self._detect_invoice_patterns(structured_data['raw_text'])

        return structured_data

    def _detect_invoice_patterns(self, text: str) -> Dict:
        """Detecta patrones específicos de facturas"""
        import re

        detected = {}

        for pattern_type, patterns in self.invoice_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                matches.extend(found)

            if matches:
                detected[pattern_type] = matches

        return detected

    def batch_process(self, 
                     image_paths: List[Union[str, Path]], 
                     max_workers: int = 4) -> Dict[str, List[OCRResult]]:
        """
        Procesa múltiples imágenes en paralelo

        Args:
            image_paths: Lista de rutas de imágenes
            max_workers: Número máximo de workers

        Returns:
            Dict: Resultados por imagen
        """
        results = {}

        def process_single(path):
            try:
                return str(path), self.process_image(path)
            except Exception as e:
                logger.error(f"Error procesando {path}: {str(e)}")
                return str(path), []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single, path) for path in image_paths]

            for future in futures:
                path, ocr_results = future.result()
                results[path] = ocr_results

        logger.info(f"Procesamiento en lote completado: {len(results)} imágenes")
        return results

    def save_results_to_json(self, 
                           ocr_results: List[OCRResult], 
                           output_path: Union[str, Path]) -> bool:
        """Guarda los resultados OCR en formato JSON"""
        try:
            results_dict = []
            for result in ocr_results:
                results_dict.append({
                    'text': result.text,
                    'confidence': result.confidence,
                    'bbox': result.bbox,
                    'coordinates': result.coordinates,
                    'line_number': result.line_number,
                    'region_type': result.region_type
                })

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"Resultados guardados en: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando resultados: {str(e)}")
            return False

    def get_performance_stats(self) -> Dict:
        """Obtiene estadísticas de rendimiento del procesador"""
        return {
            'languages': self.languages,
            'gpu_enabled': self.gpu,
            'confidence_threshold': self.confidence_threshold,
            'reader_initialized': self._reader is not None
        }

# Funciones de utilidad
def quick_ocr(image_path: Union[str, Path, np.ndarray], 
              languages: List[str] = ['es', 'en']) -> str:
    """
    OCR rápido que devuelve solo el texto

    Args:
        image_path: Ruta de la imagen
        languages: Idiomas a detectar

    Returns:
        str: Texto extraído
    """
    processor = OCRProcessor(languages=languages)
    results = processor.process_image(image_path)
    return '\n'.join([r.text for r in results])

def process_invoice_ocr(image_path: Union[str, Path, np.ndarray]) -> Dict:
    """
    Procesamiento OCR específico para facturas

    Args:
        image_path: Ruta de la imagen de factura

    Returns:
        Dict: Datos estructurados de la factura
    """
    processor = OCRProcessor(languages=['es', 'en'], confidence_threshold=0.5)
    ocr_results = processor.process_image(image_path)
    return processor.extract_structured_data(ocr_results)
