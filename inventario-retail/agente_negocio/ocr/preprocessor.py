"""
AgenteNegocio - OCR Preprocessor
Mejora automática de imágenes de facturas para OCR óptimo
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Tuple, Optional, Union
from PIL import Image, ImageFilter, ImageEnhance
import io

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Procesador de imágenes optimizado para facturas AFIP
    Mejora la calidad de las imágenes para maximizar la precisión del OCR
    """

    def __init__(self, target_dpi: int = 300, max_size: Tuple[int, int] = (2048, 2048)):
        """
        Inicializa el preprocesador con configuraciones optimizadas

        Args:
            target_dpi: DPI objetivo para las imágenes procesadas
            max_size: Tamaño máximo de imagen (ancho, alto)
        """
        self.target_dpi = target_dpi
        self.max_size = max_size
        logger.info(f"ImagePreprocessor inicializado - DPI: {target_dpi}, Max Size: {max_size}")

    def preprocess_image(self, image_path: Union[str, Path, bytes]) -> np.ndarray:
        """
        Pipeline completo de preprocesamiento de imagen

        Args:
            image_path: Ruta de imagen, objeto Path o bytes de imagen

        Returns:
            numpy.ndarray: Imagen procesada optimizada para OCR

        Raises:
            ValueError: Si la imagen no se puede procesar
        """
        try:
            # Cargar imagen
            image = self._load_image(image_path)
            logger.info(f"Imagen cargada - Shape original: {image.shape}")

            # Pipeline de procesamiento
            image = self._resize_image(image)
            image = self._enhance_contrast(image)
            image = self._denoise_image(image)
            image = self._correct_skew(image)
            image = self._enhance_text_clarity(image)
            image = self._normalize_brightness(image)

            logger.info(f"Preprocesamiento completado - Shape final: {image.shape}")
            return image

        except Exception as e:
            logger.error(f"Error en preprocesamiento: {str(e)}")
            raise ValueError(f"No se pudo procesar la imagen: {str(e)}")

    def _load_image(self, image_input: Union[str, Path, bytes]) -> np.ndarray:
        """Carga imagen desde diferentes fuentes"""
        try:
            if isinstance(image_input, bytes):
                # Cargar desde bytes
                image = Image.open(io.BytesIO(image_input))
            else:
                # Cargar desde archivo
                image = Image.open(image_input)

            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convertir a numpy array
            return np.array(image)

        except Exception as e:
            raise ValueError(f"Error cargando imagen: {str(e)}")

    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """Redimensiona imagen manteniendo aspect ratio"""
        height, width = image.shape[:2]
        max_w, max_h = self.max_size

        if width <= max_w and height <= max_h:
            return image

        # Calcular factor de escala
        scale_w = max_w / width
        scale_h = max_h / height
        scale = min(scale_w, scale_h)

        # Nuevas dimensiones
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Redimensionar
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        logger.info(f"Imagen redimensionada: {width}x{height} -> {new_width}x{new_height}")

        return resized

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Mejora el contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization)"""
        # Convertir a LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Aplicar CLAHE al canal L
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)

        # Recombinar canales
        enhanced = cv2.merge((l_channel, a_channel, b_channel))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

        return enhanced

    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Reduce el ruido preservando los bordes del texto"""
        # Usar filtro bilateral para reducir ruido manteniendo bordes
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        return denoised

    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """Corrige la inclinación del documento"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Aplicar threshold para obtener imagen binaria
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Encontrar contornos
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return image

            # Encontrar el contorno más grande (probablemente el documento)
            largest_contour = max(contours, key=cv2.contourArea)

            # Calcular el rectángulo mínimo rotado
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]

            # Ajustar ángulo
            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90

            # Corregir solo si la inclinación es significativa
            if abs(angle) > 1.0:
                # Rotar imagen
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

                # Calcular nuevas dimensiones
                cos = np.abs(rotation_matrix[0, 0])
                sin = np.abs(rotation_matrix[0, 1])
                new_w = int((h * sin) + (w * cos))
                new_h = int((h * cos) + (w * sin))

                # Ajustar centro de rotación
                rotation_matrix[0, 2] += (new_w / 2) - center[0]
                rotation_matrix[1, 2] += (new_h / 2) - center[1]

                # Aplicar rotación
                rotated = cv2.warpAffine(image, rotation_matrix, (new_w, new_h), 
                                       flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

                logger.info(f"Inclinación corregida: {angle:.2f} grados")
                return rotated

            return image

        except Exception as e:
            logger.warning(f"No se pudo corregir inclinación: {str(e)}")
            return image

    def _enhance_text_clarity(self, image: np.ndarray) -> np.ndarray:
        """Mejora la claridad del texto usando sharpening"""
        # Kernel de sharpening optimizado para texto
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])

        # Aplicar sharpening
        sharpened = cv2.filter2D(image, -1, kernel)

        # Combinar con imagen original para evitar over-sharpening
        enhanced = cv2.addWeighted(image, 0.7, sharpened, 0.3, 0)

        return enhanced

    def _normalize_brightness(self, image: np.ndarray) -> np.ndarray:
        """Normaliza el brillo y contraste final"""
        # Convertir a escala de grises para análisis
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Calcular estadísticas de brillo
        mean_brightness = np.mean(gray)
        target_brightness = 150  # Brillo objetivo para OCR óptimo

        # Ajustar brillo si es necesario
        if mean_brightness < 120 or mean_brightness > 180:
            adjustment = target_brightness - mean_brightness
            adjusted = cv2.convertScaleAbs(image, alpha=1.0, beta=adjustment)
            logger.info(f"Brillo ajustado: {mean_brightness:.1f} -> {np.mean(cv2.cvtColor(adjusted, cv2.COLOR_RGB2GRAY)):.1f}")
            return adjusted

        return image

    def save_processed_image(self, image: np.ndarray, output_path: Union[str, Path]) -> bool:
        """
        Guarda la imagen procesada

        Args:
            image: Imagen procesada
            output_path: Ruta donde guardar la imagen

        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Convertir numpy array a PIL Image
            pil_image = Image.fromarray(image)

            # Guardar con máxima calidad
            pil_image.save(output_path, quality=95, optimize=True, dpi=(self.target_dpi, self.target_dpi))

            logger.info(f"Imagen guardada: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando imagen: {str(e)}")
            return False

    def get_image_quality_metrics(self, image: np.ndarray) -> dict:
        """
        Calcula métricas de calidad de imagen

        Args:
            image: Imagen a analizar

        Returns:
            dict: Métricas de calidad
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Calcular métricas
            metrics = {
                'brightness': float(np.mean(gray)),
                'contrast': float(np.std(gray)),
                'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
                'noise_level': self._estimate_noise_level(gray),
                'resolution': image.shape[:2],
                'aspect_ratio': image.shape[1] / image.shape[0]
            }

            return metrics

        except Exception as e:
            logger.error(f"Error calculando métricas: {str(e)}")
            return {}

    def _estimate_noise_level(self, gray_image: np.ndarray) -> float:
        """Estima el nivel de ruido en la imagen"""
        try:
            # Usar la desviación estándar del Laplaciano como estimador de ruido
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            noise_level = np.std(laplacian)
            return float(noise_level)
        except:
            return 0.0

# Funciones de utilidad
def preprocess_invoice_image(image_path: Union[str, Path, bytes], 
                           output_path: Optional[Union[str, Path]] = None) -> np.ndarray:
    """
    Función conveniente para preprocesar una imagen de factura

    Args:
        image_path: Ruta o bytes de la imagen
        output_path: Ruta opcional donde guardar la imagen procesada

    Returns:
        numpy.ndarray: Imagen procesada
    """
    preprocessor = ImagePreprocessor()
    processed_image = preprocessor.preprocess_image(image_path)

    if output_path:
        preprocessor.save_processed_image(processed_image, output_path)

    return processed_image

def batch_preprocess_images(input_dir: Union[str, Path], 
                          output_dir: Union[str, Path]) -> list:
    """
    Procesa múltiples imágenes en lote

    Args:
        input_dir: Directorio de imágenes de entrada
        output_dir: Directorio de salida

    Returns:
        list: Lista de archivos procesados exitosamente
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    preprocessor = ImagePreprocessor()
    processed_files = []

    # Extensiones de imagen soportadas
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

    for image_file in input_path.iterdir():
        if image_file.suffix.lower() in image_extensions:
            try:
                # Procesar imagen
                processed_image = preprocessor.preprocess_image(image_file)

                # Guardar imagen procesada
                output_file = output_path / f"processed_{image_file.name}"
                if preprocessor.save_processed_image(processed_image, output_file):
                    processed_files.append(str(output_file))

            except Exception as e:
                logger.error(f"Error procesando {image_file}: {str(e)}")

    logger.info(f"Procesamiento en lote completado: {len(processed_files)} archivos")
    return processed_files
