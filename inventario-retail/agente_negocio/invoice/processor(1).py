"""
AgenteNegocio - Invoice Processor
Pipeline End-to-End completo para procesamiento de facturas
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import asyncio
import json
from decimal import Decimal
from enum import Enum

# Imports locales
from ..ocr.preprocessor import ImagePreprocessor, preprocess_invoice_image
from ..ocr.processor import OCRProcessor, process_invoice_ocr
from ..ocr.extractor import AFIPDataExtractor, InvoiceData, extract_invoice_data
from ..pricing.engine import PricingEngine, ProductCategory, calculate_simple_price
from ..pricing.cache import PriceCacheManager, get_global_cache

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Etapas del procesamiento de facturas"""
    RECEIVED = "received"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    DATA_EXTRACTION = "data_extraction"
    PRICE_CALCULATION = "price_calculation"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"

class ValidationLevel(Enum):
    """Niveles de validación"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

@dataclass
class ProcessingConfig:
    """Configuración del pipeline de procesamiento"""
    # OCR Configuration
    ocr_languages: List[str] = field(default_factory=lambda: ['es', 'en'])
    ocr_confidence_threshold: float = 0.5

    # Image preprocessing
    enable_preprocessing: bool = True
    target_dpi: int = 300
    max_image_size: Tuple[int, int] = (2048, 2048)

    # Data extraction
    extraction_confidence_threshold: float = 0.3

    # Price calculation
    enable_price_calculation: bool = True
    default_region: str = "CABA"
    price_cache_ttl: int = 14400  # 4 horas

    # Validation
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    required_fields: List[str] = field(default_factory=lambda: [
        'numero_factura', 'fecha_emision', 'total', 'cuit_emisor'
    ])

    # Performance
    enable_async: bool = True
    max_concurrent_jobs: int = 5
    processing_timeout: int = 300  # 5 minutos

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de factura"""
    # Identificación
    job_id: str
    original_filename: Optional[str] = None

    # Estado
    stage: ProcessingStage = ProcessingStage.RECEIVED
    success: bool = False
    error_message: Optional[str] = None

    # Tiempos
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    processing_time_seconds: float = 0.0

    # Datos extraídos
    invoice_data: Optional[InvoiceData] = None
    raw_ocr_text: str = ""

    # Cálculos de precios
    price_calculations: List[Dict[str, Any]] = field(default_factory=list)
    total_calculated_value: Optional[Decimal] = None

    # Métricas de calidad
    ocr_confidence: float = 0.0
    extraction_confidence: float = 0.0
    validation_score: float = 0.0

    # Metadata
    image_metrics: Dict[str, Any] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte resultado a diccionario serializable"""
        result_dict = {
            'job_id': self.job_id,
            'original_filename': self.original_filename,
            'stage': self.stage.value,
            'success': self.success,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processing_time_seconds': self.processing_time_seconds,
            'raw_ocr_text': self.raw_ocr_text,
            'price_calculations': self.price_calculations,
            'total_calculated_value': float(self.total_calculated_value) if self.total_calculated_value else None,
            'ocr_confidence': self.ocr_confidence,
            'extraction_confidence': self.extraction_confidence,
            'validation_score': self.validation_score,
            'image_metrics': self.image_metrics,
            'processing_metadata': self.processing_metadata
        }

        # Serializar invoice_data si existe
        if self.invoice_data:
            invoice_dict = {}
            for field_name in self.invoice_data.__dataclass_fields__:
                value = getattr(self.invoice_data, field_name)
                if isinstance(value, Decimal):
                    invoice_dict[field_name] = float(value)
                elif isinstance(value, datetime):
                    invoice_dict[field_name] = value.isoformat()
                elif isinstance(value, list):
                    invoice_dict[field_name] = [
                        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}
                        if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    invoice_dict[field_name] = value
            result_dict['invoice_data'] = invoice_dict

        return result_dict

class InvoiceProcessor:
    """
    Procesador End-to-End completo para facturas
    Integra OCR, extracción de datos, cálculo de precios y validación
    """

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Inicializa el procesador

        Args:
            config: Configuración del procesamiento
        """
        self.config = config or ProcessingConfig()

        # Inicializar componentes
        self.image_preprocessor = ImagePreprocessor(
            target_dpi=self.config.target_dpi,
            max_size=self.config.max_image_size
        )

        self.ocr_processor = OCRProcessor(
            languages=self.config.ocr_languages,
            confidence_threshold=self.config.ocr_confidence_threshold
        )

        self.data_extractor = AFIPDataExtractor()

        self.pricing_engine = PricingEngine()
        self.price_cache = PriceCacheManager(get_global_cache())

        # Jobs en progreso
        self.active_jobs: Dict[str, ProcessingResult] = {}

        logger.info(f"InvoiceProcessor inicializado - Async: {self.config.enable_async}")

    def process_invoice(self, 
                       image_path: Union[str, Path, bytes],
                       job_id: Optional[str] = None,
                       filename: Optional[str] = None) -> ProcessingResult:
        """
        Procesa una factura completa (sincrónico)

        Args:
            image_path: Ruta o bytes de la imagen
            job_id: ID único del trabajo
            filename: Nombre del archivo original

        Returns:
            ProcessingResult: Resultado completo del procesamiento
        """
        if job_id is None:
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        result = ProcessingResult(job_id=job_id, original_filename=filename)
        self.active_jobs[job_id] = result

        try:
            logger.info(f"Iniciando procesamiento de factura - Job: {job_id}")

            # Etapa 1: Preprocesamiento de imagen
            result.stage = ProcessingStage.PREPROCESSING
            if self.config.enable_preprocessing:
                processed_image = self._preprocess_image(image_path, result)
            else:
                processed_image = image_path

            # Etapa 2: OCR
            result.stage = ProcessingStage.OCR_PROCESSING
            ocr_results = self._perform_ocr(processed_image, result)

            # Etapa 3: Extracción de datos
            result.stage = ProcessingStage.DATA_EXTRACTION
            invoice_data = self._extract_data(result.raw_ocr_text, result)
            result.invoice_data = invoice_data

            # Etapa 4: Cálculo de precios (opcional)
            if self.config.enable_price_calculation:
                result.stage = ProcessingStage.PRICE_CALCULATION
                self._calculate_prices(invoice_data, result)

            # Etapa 5: Validación
            result.stage = ProcessingStage.VALIDATION
            validation_success = self._validate_results(result)

            # Finalizar
            result.stage = ProcessingStage.COMPLETED
            result.success = validation_success
            result.end_time = datetime.now()
            result.processing_time_seconds = (result.end_time - result.start_time).total_seconds()

            logger.info(f"Procesamiento completado - Job: {job_id}, "
                       f"Success: {result.success}, Time: {result.processing_time_seconds:.2f}s")

        except Exception as e:
            result.stage = ProcessingStage.FAILED
            result.success = False
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.processing_time_seconds = (result.end_time - result.start_time).total_seconds()

            logger.error(f"Error procesando factura {job_id}: {e}")

        finally:
            # Limpiar job activo después de un tiempo
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]

        return result

    async def process_invoice_async(self, 
                                  image_path: Union[str, Path, bytes],
                                  job_id: Optional[str] = None,
                                  filename: Optional[str] = None) -> ProcessingResult:
        """Versión asíncrona del procesamiento"""
        if not self.config.enable_async:
            return self.process_invoice(image_path, job_id, filename)

        # Ejecutar en thread pool para evitar bloquear el event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.process_invoice, image_path, job_id, filename
        )

    def _preprocess_image(self, image_path: Union[str, Path, bytes], 
                         result: ProcessingResult) -> Union[str, Path, bytes]:
        """Preprocesa la imagen para mejorar OCR"""
        try:
            logger.debug(f"Preprocesando imagen - Job: {result.job_id}")

            # Procesar imagen
            processed_image = self.image_preprocessor.preprocess_image(image_path)

            # Obtener métricas de calidad
            quality_metrics = self.image_preprocessor.get_image_quality_metrics(processed_image)
            result.image_metrics = quality_metrics

            logger.debug(f"Preprocesamiento completado - Resolución: {quality_metrics.get('resolution', 'N/A')}")

            return processed_image

        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            # Si falla el preprocesamiento, usar imagen original
            return image_path

    def _perform_ocr(self, image_input: Union[str, Path, bytes], 
                    result: ProcessingResult) -> List:
        """Ejecuta OCR en la imagen"""
        logger.debug(f"Ejecutando OCR - Job: {result.job_id}")

        # Procesar con OCR
        ocr_results = self.ocr_processor.process_image(image_input)

        # Extraer texto completo
        result.raw_ocr_text = '\n'.join([r.text for r in ocr_results])

        # Calcular confianza promedio
        if ocr_results:
            result.ocr_confidence = sum(r.confidence for r in ocr_results) / len(ocr_results)

        logger.debug(f"OCR completado - {len(ocr_results)} elementos, "
                    f"confianza: {result.ocr_confidence:.2f}")

        return ocr_results

    def _extract_data(self, ocr_text: str, result: ProcessingResult) -> InvoiceData:
        """Extrae datos estructurados del texto OCR"""
        logger.debug(f"Extrayendo datos - Job: {result.job_id}")

        # Extraer datos usando AFIP patterns
        invoice_data = self.data_extractor.extract_from_text(
            ocr_text, 
            confidence_threshold=self.config.extraction_confidence_threshold
        )

        result.extraction_confidence = invoice_data.confidence_score

        logger.debug(f"Extracción completada - {len(invoice_data.extracted_fields)} campos, "
                    f"confianza: {invoice_data.confidence_score:.2f}")

        return invoice_data

    def _calculate_prices(self, invoice_data: InvoiceData, result: ProcessingResult):
        """Calcula precios actualizados para los items de la factura"""
        if not invoice_data.items:
            logger.debug("No hay items para calcular precios")
            return

        logger.debug(f"Calculando precios para {len(invoice_data.items)} items")

        total_calculated = Decimal('0')

        for item in invoice_data.items:
            try:
                # Determinar categoría del producto (simplificado)
                category = self._determine_product_category(item.get('descripcion', ''))

                # Obtener precio base del item
                base_price = item.get('precio_unitario')
                if not base_price or base_price <= 0:
                    continue

                # Verificar cache primero
                cached_price = self.price_cache.get_price_calculation(
                    product_id=item.get('codigo', 'unknown'),
                    category=category.value,
                    region=self.config.default_region
                )

                if cached_price:
                    calculation = cached_price
                    logger.debug(f"Precio obtenido de cache para {item.get('codigo', 'unknown')}")
                else:
                    # Calcular precio nuevo
                    calculation = self.pricing_engine.calculate_price(
                        product_id=item.get('codigo', 'unknown'),
                        base_price=base_price,
                        category=category,
                        region=self.config.default_region
                    )

                    # Cachear resultado
                    self.price_cache.cache_price_calculation(
                        product_id=item.get('codigo', 'unknown'),
                        category=category.value,
                        region=self.config.default_region,
                        calculation_result=calculation,
                        ttl=self.config.price_cache_ttl
                    )

                # Agregar a resultados
                price_calc = {
                    'item_codigo': item.get('codigo'),
                    'item_descripcion': item.get('descripcion'),
                    'cantidad': float(item.get('cantidad', 0)),
                    'precio_original': float(base_price),
                    'precio_actualizado': float(calculation.final_price),
                    'variacion_porcentual': float(((calculation.final_price - base_price) / base_price) * 100),
                    'category': category.value,
                    'confidence': calculation.confidence_score
                }

                result.price_calculations.append(price_calc)

                # Sumar al total calculado
                cantidad = item.get('cantidad', Decimal('1'))
                total_calculated += calculation.final_price * cantidad

            except Exception as e:
                logger.warning(f"Error calculando precio para item {item}: {e}")

        result.total_calculated_value = total_calculated

        logger.debug(f"Cálculo de precios completado - Total: ${total_calculated}")

    def _determine_product_category(self, description: str) -> ProductCategory:
        """Determina la categoría del producto basándose en la descripción"""
        if not description:
            return ProductCategory.OTROS

        description_lower = description.lower()

        # Mapeo simple de palabras clave a categorías
        category_keywords = {
            ProductCategory.ALIMENTOS: ['alimento', 'comida', 'pan', 'leche', 'carne', 'verdura', 'fruta'],
            ProductCategory.BEBIDAS: ['bebida', 'agua', 'gaseosa', 'jugo', 'cerveza', 'vino'],
            ProductCategory.LIMPIEZA: ['limpieza', 'detergente', 'jabón', 'shampoo'],
            ProductCategory.HIGIENE: ['higiene', 'pasta', 'cepillo', 'desodorante'],
            ProductCategory.MEDICAMENTOS: ['medicamento', 'remedio', 'farmacia', 'aspirina'],
            ProductCategory.ROPA: ['ropa', 'camisa', 'pantalón', 'zapato', 'vestido'],
            ProductCategory.ELECTRODOMESTICOS: ['electro', 'televisor', 'heladera', 'lavarropas']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return category

        return ProductCategory.OTROS

    def _validate_results(self, result: ProcessingResult) -> bool:
        """Valida los resultados del procesamiento"""
        if not result.invoice_data:
            result.validation_score = 0.0
            return False

        validation_checks = []

        # Validación básica: campos requeridos
        required_fields_found = 0
        for field in self.config.required_fields:
            if getattr(result.invoice_data, field) is not None:
                required_fields_found += 1

        required_fields_score = required_fields_found / len(self.config.required_fields)
        validation_checks.append(('required_fields', required_fields_score))

        # Validación de confianza OCR
        ocr_confidence_score = min(1.0, result.ocr_confidence / 0.8)  # 0.8 como objetivo
        validation_checks.append(('ocr_confidence', ocr_confidence_score))

        # Validación de confianza de extracción
        extraction_confidence_score = result.extraction_confidence
        validation_checks.append(('extraction_confidence', extraction_confidence_score))

        # Validación de consistencia de montos (si hay datos de precios)
        amount_consistency_score = 1.0
        if (result.invoice_data.subtotal and result.invoice_data.iva_total and 
            result.invoice_data.total):
            expected_total = result.invoice_data.subtotal + result.invoice_data.iva_total
            if result.invoice_data.impuestos_internos:
                expected_total += result.invoice_data.impuestos_internos

            if result.invoice_data.total > 0:
                difference = abs(expected_total - result.invoice_data.total) / result.invoice_data.total
                amount_consistency_score = max(0.0, 1.0 - difference * 2)  # Penalizar diferencias

        validation_checks.append(('amount_consistency', amount_consistency_score))

        # Calcular score final basado en el nivel de validación
        if self.config.validation_level == ValidationLevel.BASIC:
            # Solo campos requeridos
            result.validation_score = required_fields_score
        elif self.config.validation_level == ValidationLevel.STANDARD:
            # Promedio ponderado
            weights = [0.4, 0.3, 0.2, 0.1]  # required, ocr, extraction, consistency
            result.validation_score = sum(score * weight for (_, score), weight 
                                        in zip(validation_checks, weights))
        else:  # STRICT
            # Todos los checks deben pasar un umbral mínimo
            min_scores = [0.8, 0.6, 0.5, 0.7]  # Umbrales estrictos
            all_pass = all(score >= min_score for (_, score), min_score 
                          in zip(validation_checks, min_scores))
            if all_pass:
                result.validation_score = sum(score for _, score in validation_checks) / len(validation_checks)
            else:
                result.validation_score = 0.0

        # Determinar éxito
        success_threshold = {
            ValidationLevel.BASIC: 0.6,
            ValidationLevel.STANDARD: 0.7,
            ValidationLevel.STRICT: 0.8
        }

        success = result.validation_score >= success_threshold[self.config.validation_level]

        # Agregar detalles de validación a metadata
        result.processing_metadata['validation_checks'] = {
            name: score for name, score in validation_checks
        }
        result.processing_metadata['validation_level'] = self.config.validation_level.value
        result.processing_metadata['success_threshold'] = success_threshold[self.config.validation_level]

        logger.debug(f"Validación completada - Score: {result.validation_score:.2f}, "
                    f"Success: {success}")

        return success

    def batch_process_invoices(self, 
                             image_paths: List[Union[str, Path, bytes]],
                             filenames: Optional[List[str]] = None) -> List[ProcessingResult]:
        """
        Procesa múltiples facturas en lote

        Args:
            image_paths: Lista de rutas/bytes de imágenes
            filenames: Lista opcional de nombres de archivo

        Returns:
            List[ProcessingResult]: Resultados de todos los procesamientos
        """
        if filenames and len(filenames) != len(image_paths):
            raise ValueError("La lista de filenames debe tener la misma longitud que image_paths")

        results = []
        logger.info(f"Iniciando procesamiento en lote de {len(image_paths)} facturas")

        for i, image_path in enumerate(image_paths):
            filename = filenames[i] if filenames else f"batch_item_{i}"
            job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"

            try:
                result = self.process_invoice(image_path, job_id, filename)
                results.append(result)

            except Exception as e:
                # Crear resultado de error
                error_result = ProcessingResult(
                    job_id=job_id,
                    original_filename=filename,
                    stage=ProcessingStage.FAILED,
                    success=False,
                    error_message=str(e),
                    end_time=datetime.now()
                )
                results.append(error_result)
                logger.error(f"Error en lote para {filename}: {e}")

        successful = sum(1 for r in results if r.success)
        logger.info(f"Procesamiento en lote completado - {successful}/{len(results)} exitosos")

        return results

    def get_job_status(self, job_id: str) -> Optional[ProcessingResult]:
        """Obtiene el estado de un trabajo activo"""
        return self.active_jobs.get(job_id)

    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del procesador"""
        return {
            'active_jobs': len(self.active_jobs),
            'config': {
                'ocr_languages': self.config.ocr_languages,
                'ocr_confidence_threshold': self.config.ocr_confidence_threshold,
                'extraction_confidence_threshold': self.config.extraction_confidence_threshold,
                'validation_level': self.config.validation_level.value,
                'enable_price_calculation': self.config.enable_price_calculation,
                'enable_async': self.config.enable_async
            },
            'cache_stats': self.price_cache.cache.get_stats().to_dict()
        }

# Funciones de utilidad
async def process_invoice_file(file_path: Union[str, Path], 
                             config: Optional[ProcessingConfig] = None) -> ProcessingResult:
    """
    Función conveniente para procesar una factura desde archivo

    Args:
        file_path: Ruta del archivo de imagen
        config: Configuración opcional

    Returns:
        ProcessingResult: Resultado del procesamiento
    """
    processor = InvoiceProcessor(config)
    filename = Path(file_path).name

    return await processor.process_invoice_async(file_path, filename=filename)

def process_invoice_bytes(image_bytes: bytes, 
                         filename: str = "unknown.jpg",
                         config: Optional[ProcessingConfig] = None) -> ProcessingResult:
    """
    Función conveniente para procesar factura desde bytes

    Args:
        image_bytes: Bytes de la imagen
        filename: Nombre del archivo
        config: Configuración opcional

    Returns:
        ProcessingResult: Resultado del procesamiento
    """
    processor = InvoiceProcessor(config)
    return processor.process_invoice(image_bytes, filename=filename)
