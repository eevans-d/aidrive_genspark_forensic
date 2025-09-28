"""
Servicio OCR optimizado con circuit breakers y timeouts para sistema retail
Incluye fallbacks automáticos y cache inteligente
"""
import asyncio
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from contextlib import asynccontextmanager
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .metrics import retail_metrics, MetricsTimer


logger = logging.getLogger(__name__)


class OCRStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout" 
    ERROR = "error"
    CACHED = "cached"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class OCRResult:
    text: str
    confidence: float
    processing_time: float
    status: OCRStatus
    source: str = "primary"
    cached: bool = False
    bbox: Optional[List[int]] = None


class CircuitBreaker:
    """Circuit breaker pattern para OCR resiliente"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def can_execute(self) -> bool:
        """Verificar si se puede ejecutar la operación"""
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            # Verificar si es momento de intentar de nuevo
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
            
        # HALF_OPEN: permitir una ejecución de prueba
        return True
    
    def record_success(self):
        """Registrar éxito"""
        self.failure_count = 0
        self.state = "CLOSED"
        
    def record_failure(self):
        """Registrar falla"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


class OCRCacheManager:
    """Cache inteligente para resultados OCR"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1", ttl: int = 3600):
        self.ttl = ttl  # 1 hora por defecto
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("OCR cache connected to Redis")
            except Exception as e:
                logger.warning(f"Redis not available for OCR cache: {e}")
                self.redis_client = None
    
    def _generate_cache_key(self, image_path: str, ocr_params: Dict[str, Any]) -> str:
        """Generar clave de cache basada en imagen y parámetros"""
        # Hash del contenido de la imagen + parámetros OCR
        content_hash = hashlib.md5()
        
        if isinstance(image_path, (str, Path)):
            try:
                with open(image_path, 'rb') as f:
                    content_hash.update(f.read())
            except Exception:
                content_hash.update(str(image_path).encode())
        else:
            # Para arrays numpy u otros tipos
            content_hash.update(str(image_path).encode())
            
        # Incluir parámetros en el hash
        params_str = '|'.join(f"{k}:{v}" for k, v in sorted(ocr_params.items()))
        content_hash.update(params_str.encode())
        
        return f"ocr:result:{content_hash.hexdigest()}"
    
    async def get_cached_result(self, image_path: str, ocr_params: Dict[str, Any]) -> Optional[OCRResult]:
        """Obtener resultado cacheado"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(image_path, ocr_params)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                import json
                data = json.loads(cached_data)
                
                result = OCRResult(
                    text=data['text'],
                    confidence=data['confidence'],
                    processing_time=data['processing_time'],
                    status=OCRStatus.CACHED,
                    source=data.get('source', 'cache'),
                    cached=True,
                    bbox=data.get('bbox')
                )
                
                logger.debug(f"OCR cache hit for key: {cache_key[:16]}...")
                return result
                
        except Exception as e:
            logger.error(f"Error retrieving OCR cache: {e}")
            
        return None
    
    async def cache_result(self, image_path: str, ocr_params: Dict[str, Any], result: OCRResult):
        """Cachear resultado OCR"""
        if not self.redis_client or result.cached:
            return
            
        try:
            cache_key = self._generate_cache_key(image_path, ocr_params)
            
            cache_data = {
                'text': result.text,
                'confidence': result.confidence,
                'processing_time': result.processing_time,
                'source': result.source,
                'bbox': result.bbox,
                'timestamp': time.time()
            }
            
            import json
            self.redis_client.setex(
                cache_key, 
                self.ttl, 
                json.dumps(cache_data)
            )
            
            logger.debug(f"OCR result cached for key: {cache_key[:16]}...")
            
        except Exception as e:
            logger.error(f"Error caching OCR result: {e}")


class OptimizedOCRService:
    """Servicio OCR optimizado con circuit breakers, timeouts y cache"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.cache_manager = OCRCacheManager(redis_url)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
        self.default_timeout = 10.0  # 10 segundos timeout por defecto
        self.fallback_engines = ['tesseract', 'easyocr']  # Engines de fallback
        self.current_engine = 'primary'
        
    @asynccontextmanager
    async def ocr_operation_context(self, image_path: str, operation_type: str):
        """Context manager para operaciones OCR con métricas y timeouts"""
        with MetricsTimer('ocr_processing', {
            'type': operation_type,
            'category': 'product_recognition'
        }):
            start_time = time.time()
            
            try:
                yield
                
                # Registrar éxito en circuit breaker
                self.circuit_breaker.record_success()
                
            except asyncio.TimeoutError:
                self.circuit_breaker.record_failure()
                retail_metrics.record_stock_validation_error(
                    error_type="ocr_timeout",
                    producto_id=0,
                    deposito_id=0
                )
                raise
                
            except Exception as e:
                self.circuit_breaker.record_failure()
                retail_metrics.record_stock_validation_error(
                    error_type="ocr_error",
                    producto_id=0,
                    deposito_id=0
                )
                logger.error(f"OCR operation failed: {e}")
                raise
                
            finally:
                processing_time = time.time() - start_time
                logger.debug(f"OCR operation completed in {processing_time:.2f}s")

    async def process_image_with_fallbacks(
        self, 
        image: Union[str, Path], 
        timeout: Optional[float] = None,
        detect_layout: bool = True,
        paragraph: bool = True,
        min_confidence: float = 0.5
    ) -> OCRResult:
        """
        Procesar imagen con fallbacks automáticos y optimizaciones
        """
        timeout = timeout or self.default_timeout
        ocr_params = {
            'detect_layout': detect_layout,
            'paragraph': paragraph,
            'min_confidence': min_confidence
        }
        
        # 1. Verificar cache primero
        cached_result = await self.cache_manager.get_cached_result(str(image), ocr_params)
        if cached_result:
            return cached_result
        
        # 2. Verificar circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("OCR circuit breaker is OPEN, skipping processing")
            return OCRResult(
                text="",
                confidence=0.0,
                processing_time=0.0,
                status=OCRStatus.CIRCUIT_OPEN,
                source="circuit_breaker"
            )
        
        # 3. Procesar con timeout y fallbacks
        async with self.ocr_operation_context(str(image), "image_processing"):
            
            # Intentar con engine principal
            try:
                result = await asyncio.wait_for(
                    self._process_with_primary_engine(image, ocr_params),
                    timeout=timeout
                )
                
                if result.confidence >= min_confidence:
                    # Cachear resultado exitoso
                    await self.cache_manager.cache_result(str(image), ocr_params, result)
                    return result
                    
            except asyncio.TimeoutError:
                logger.warning(f"Primary OCR engine timeout after {timeout}s")
                
            except Exception as e:
                logger.warning(f"Primary OCR engine failed: {e}")
            
            # 4. Intentar con engines de fallback
            for engine in self.fallback_engines:
                try:
                    logger.info(f"Trying fallback OCR engine: {engine}")
                    
                    result = await asyncio.wait_for(
                        self._process_with_fallback_engine(image, engine, ocr_params),
                        timeout=timeout * 0.8  # Timeout reducido para fallbacks
                    )
                    
                    if result.confidence >= min_confidence * 0.8:  # Criterio más relajado
                        result.source = f"fallback_{engine}"
                        await self.cache_manager.cache_result(str(image), ocr_params, result)
                        return result
                        
                except Exception as e:
                    logger.warning(f"Fallback engine {engine} failed: {e}")
                    continue
            
            # 5. Todos los engines fallaron
            return OCRResult(
                text="",
                confidence=0.0,
                processing_time=timeout,
                status=OCRStatus.ERROR,
                source="all_engines_failed"
            )

    async def _process_with_primary_engine(self, image: Union[str, Path], 
                                         params: Dict[str, Any]) -> OCRResult:
        """Procesar con engine principal (simulado - reemplazar con implementación real)"""
        
        # Simulación de procesamiento OCR real
        # En implementación real, aquí iría EasyOCR, Tesseract, etc.
        await asyncio.sleep(0.5)  # Simular procesamiento
        
        # Resultado simulado
        return OCRResult(
            text="Ejemplo texto OCR reconocido",
            confidence=0.85,
            processing_time=0.5,
            status=OCRStatus.SUCCESS,
            source="primary_engine",
            bbox=[10, 10, 200, 50]
        )

    async def _process_with_fallback_engine(self, image: Union[str, Path], 
                                          engine: str, params: Dict[str, Any]) -> OCRResult:
        """Procesar con engine de fallback"""
        
        # Simulación de engine de fallback
        await asyncio.sleep(0.3)
        
        return OCRResult(
            text="Texto fallback reconocido",
            confidence=0.65,
            processing_time=0.3,
            status=OCRStatus.SUCCESS,
            source=engine,
            bbox=[10, 10, 180, 45]
        )

    async def recognize_barcode(self, image: Union[str, Path], 
                              timeout: Optional[float] = None) -> OCRResult:
        """
        Reconocimiento específico de códigos de barras con validaciones argentinas
        """
        timeout = timeout or 5.0  # Timeout menor para códigos de barras
        
        async with self.ocr_operation_context(str(image), "barcode_recognition"):
            try:
                # Simulación de reconocimiento de código de barras
                await asyncio.sleep(0.2)
                
                # En implementación real, usar bibliotecas específicas como pyzbar
                barcode_text = "7790001234567"  # Ejemplo EAN-13 argentino
                
                # Validar formato
                if self._validate_barcode_format(barcode_text):
                    retail_metrics.record_barcode_recognition(
                        barcode_type="EAN-13",
                        success=True,
                        quality="high"
                    )
                    
                    return OCRResult(
                        text=barcode_text,
                        confidence=0.95,
                        processing_time=0.2,
                        status=OCRStatus.SUCCESS,
                        source="barcode_scanner"
                    )
                else:
                    retail_metrics.record_barcode_recognition(
                        barcode_type="unknown",
                        success=False,
                        quality="low"
                    )
                    
                    return OCRResult(
                        text="",
                        confidence=0.0,
                        processing_time=0.2,
                        status=OCRStatus.ERROR,
                        source="barcode_validation_failed"
                    )
                    
            except asyncio.TimeoutError:
                logger.warning(f"Barcode recognition timeout after {timeout}s")
                return OCRResult(
                    text="",
                    confidence=0.0,
                    processing_time=timeout,
                    status=OCRStatus.TIMEOUT,
                    source="barcode_timeout"
                )

    def _validate_barcode_format(self, barcode: str) -> bool:
        """Validar formato de código de barras argentino"""
        if not barcode.isdigit():
            return False
            
        # Validar longitudes comunes en Argentina
        if len(barcode) not in [8, 12, 13, 14]:
            return False
            
        # Validación específica EAN-13 (opcional)
        if len(barcode) == 13:
            return self._validate_ean13_checksum(barcode)
            
        return True

    def _validate_ean13_checksum(self, ean13: str) -> bool:
        """Validar checksum EAN-13"""
        if len(ean13) != 13:
            return False
            
        try:
            suma = 0
            for i, digit in enumerate(ean13[:-1]):
                if i % 2 == 0:
                    suma += int(digit)
                else:
                    suma += int(digit) * 3
            
            checksum = (10 - (suma % 10)) % 10
            return checksum == int(ean13[-1])
            
        except ValueError:
            return False

    def get_service_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio OCR"""
        return {
            'circuit_breaker_state': self.circuit_breaker.state,
            'failure_count': self.circuit_breaker.failure_count,
            'cache_available': self.cache_manager.redis_client is not None,
            'current_engine': self.current_engine,
            'fallback_engines': self.fallback_engines,
            'default_timeout': self.default_timeout
        }


# Instancia global del servicio OCR
ocr_service = OptimizedOCRService()