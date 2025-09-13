"""
Módulo de preprocesamiento de imágenes para OCR.

Este módulo proporciona herramientas para mejorar la calidad de las imágenes,
especialmente facturas, para maximizar la precisión del reconocimiento óptico de
caracteres (OCR).
"""

import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

# Configuración del logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Clase para preprocesar imágenes y optimizarlas para OCR.

    Esta clase encapsula un pipeline de técnicas de mejora de imagen diseñadas
    para facturas y documentos similares, con el objetivo de aumentar la
    precisión del motor de OCR.
    """

    def __init__(
        self, target_dpi: int = 300, max_size: Tuple[int, int] = (2048, 2048)
    ) -> None:
        """
        Inicializa el preprocesador de imágenes.

        Args:
            target_dpi: DPI (puntos por pulgada) objetivo para la imagen de salida.
            max_size: Tupla (ancho, alto) que define el tamaño máximo de la imagen.
        """
        self.target_dpi = target_dpi
        self.max_size = max_size
        logger.info(
            "ImagePreprocessor inicializado con DPI: %d y tamaño máximo: %s",
            target_dpi,
            max_size,
        )

    def preprocess_image(
        self, image_input: Union[str, Path, bytes]
    ) -> Optional[np.ndarray]:
        """
        Ejecuta el pipeline completo de preprocesamiento en una imagen.

        Args:
            image_input: Ruta del archivo, objeto Path o bytes de la imagen.

        Returns:
            Un array de numpy representando la imagen procesada, o None si ocurre un error.
        """
        try:
            image = self._load_image(image_input)
            if image is None:
                return None

            logger.info("Imagen cargada. Shape original: %s", image.shape)

            # Pipeline de procesamiento
            image = self._resize_image(image)
            image = self._enhance_contrast(image)
            image = self._denoise_image(image)
            image = self._correct_skew(image)
            image = self._enhance_text_clarity(image)
            image = self._normalize_brightness(image)

            logger.info("Preprocesamiento completado. Shape final: %s", image.shape)
            return image

        except Exception as e:
            logger.error("Error fatal durante el preprocesamiento de la imagen: %s", e)
            return None

    def _load_image(
        self, image_input: Union[str, Path, bytes]
    ) -> Optional[np.ndarray]:
        """
        Carga una imagen desde un archivo, Path o bytes.

        Args:
            image_input: La fuente de la imagen.

        Returns:
            La imagen como un array de numpy en formato RGB, o None si falla la carga.
        """
        try:
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            else:
                image = Image.open(image_input)

            if image.mode != "RGB":
                image = image.convert("RGB")

            return np.array(image)
        except Exception as e:
            logger.error("No se pudo cargar la imagen: %s", e)
            return None

    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Redimensiona la imagen si excede el tamaño máximo, manteniendo la proporción.

        Args:
            image: La imagen a redimensionar.

        Returns:
            La imagen redimensionada.
        """
        height, width = image.shape[:2]
        max_w, max_h = self.max_size

        if width <= max_w and height <= max_h:
            return image

        scale = min(max_w / width, max_h / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4
        )
        logger.info(
            "Imagen redimensionada de %dx%d a %dx%d", width, height, new_width, new_height
        )
        return resized

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste usando ecualización adaptativa del histograma (CLAHE).

        Args:
            image: La imagen a mejorar.

        Returns:
            La imagen con contraste mejorado.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)

        enhanced = cv2.merge((l_channel, a_channel, b_channel))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce el ruido de la imagen utilizando un filtro bilateral.

        Args:
            image: La imagen a limpiar.

        Returns:
            La imagen sin ruido.
        """
        return cv2.bilateralFilter(image, 9, 75, 75)

    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        Detecta y corrige la inclinación en la imagen del documento.

        Args:
            image: La imagen a corregir.

        Returns:
            La imagen con la inclinación corregida.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Coordenadas de los píxeles blancos
            coords = np.column_stack(np.where(binary > 0))
            angle = cv2.minAreaRect(coords)[-1]

            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 1.0:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image,
                    rotation_matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                logger.info("Inclinación corregida en %.2f grados", angle)
                return rotated

            return image
        except Exception as e:
            logger.warning("No se pudo corregir la inclinación: %s. Se devuelve la imagen original.", e)
            return image


    def _enhance_text_clarity(self, image: np.ndarray) -> np.ndarray:
        """
        Aumenta la nitidez del texto en la imagen.

        Args:
            image: La imagen a mejorar.

        Returns:
            La imagen con texto más nítido.
        """
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        return cv2.addWeighted(image, 0.7, sharpened, 0.3, 0)

    def _normalize_brightness(self, image: np.ndarray) -> np.ndarray:
        """
        Normaliza el brillo de la imagen a un nivel óptimo para OCR.

        Args:
            image: La imagen a normalizar.

        Returns:
            La imagen con brillo normalizado.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        mean_brightness = np.mean(gray)
        target_brightness = 150.0

        if not (120 < mean_brightness < 180):
            adjustment = target_brightness - mean_brightness
            adjusted = cv2.convertScaleAbs(image, alpha=1.0, beta=adjustment)
            logger.info(
                "Brillo ajustado de %.1f a %.1f",
                mean_brightness,
                np.mean(cv2.cvtColor(adjusted, cv2.COLOR_RGB2GRAY)),
            )
            return adjusted
        return image

    def save_processed_image(
        self, image: np.ndarray, output_path: Union[str, Path]
    ) -> bool:
        """
        Guarda una imagen procesada en el disco.

        Args:
            image: El array de numpy de la imagen a guardar.
            output_path: La ruta de destino para guardar la imagen.

        Returns:
            True si la imagen se guardó correctamente, False en caso contrario.
        """
        try:
            pil_image = Image.fromarray(image)
            pil_image.save(
                output_path,
                quality=95,
                optimize=True,
                dpi=(self.target_dpi, self.target_dpi),
            )
            logger.info("Imagen guardada exitosamente en: %s", output_path)
            return True
        except Exception as e:
            logger.error("Error al guardar la imagen en %s: %s", output_path, e)
            return False

    def get_image_quality_metrics(self, image: np.ndarray) -> Dict[str, float]:
        """
        Calcula un diccionario de métricas de calidad sobre la imagen.

        Args:
            image: La imagen a analizar.

        Returns:
            Un diccionario con métricas de calidad como brillo, contraste y nitidez.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            return {
                "brightness": float(np.mean(gray)),
                "contrast": float(np.std(gray)),
                "sharpness": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
            }
        except Exception as e:
            logger.error("No se pudieron calcular las métricas de calidad: %s", e)
            return {}


def preprocess_invoice_image(
    image_input: Union[str, Path, bytes],
    output_path: Optional[Union[str, Path]] = None,
) -> Optional[np.ndarray]:
    """
    Función de conveniencia para preprocesar una única imagen de factura.

    Args:
        image_input: Ruta del archivo, objeto Path o bytes de la imagen.
        output_path: Si se proporciona, guarda la imagen procesada en esta ruta.

    Returns:
        La imagen procesada como un array de numpy, o None si falla.
    """
    preprocessor = ImagePreprocessor()
    processed_image = preprocessor.preprocess_image(image_input)

    if processed_image is not None and output_path:
        preprocessor.save_processed_image(processed_image, output_path)

    return processed_image


def batch_preprocess_images(
    input_dir: Union[str, Path], output_dir: Union[str, Path]
) -> List[str]:
    """
    Procesa un lote de imágenes de un directorio de entrada a un directorio de salida.

    Args:
        input_dir: Directorio que contiene las imágenes a procesar.
        output_dir: Directorio donde se guardarán las imágenes procesadas.

    Returns:
        Una lista de rutas de los archivos procesados exitosamente.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    preprocessor = ImagePreprocessor()
    processed_files: List[str] = []
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

    for image_file in input_path.iterdir():
        if image_file.suffix.lower() in image_extensions:
            try:
                processed_image = preprocessor.preprocess_image(image_file)
                if processed_image is not None:
                    output_file = output_path / f"processed_{image_file.name}"
                    if preprocessor.save_processed_image(processed_image, output_file):
                        processed_files.append(str(output_file))
            except Exception as e:
                logger.error(
                    "Error procesando el archivo %s: %s", image_file, e
                )

    logger.info(
        "Procesamiento por lotes completado. %d archivos procesados.",
        len(processed_files),
    )
    return processed_files