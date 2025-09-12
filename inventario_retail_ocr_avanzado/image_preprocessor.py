"""
Image Preprocessor Avanzado para OCR
===================================

Preprocessor de imágenes con computer vision para optimizar
facturas argentinas antes del OCR. Incluye detección de orientación,
corrección de perspectiva, mejora de calidad y ROI detection.

Autor: Sistema Inventario Retail Argentino  
Fecha: 2025-08-22
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, List
import logging
from dataclasses import dataclass
import math

@dataclass
class PreprocessResult:
    """Resultado del preprocessor con metadatos"""
    processed_image: np.ndarray
    original_size: Tuple[int, int]
    rotation_angle: float
    perspective_corrected: bool
    roi_detected: bool
    quality_score: float
    processing_steps: List[str]

class ImagePreprocessor:
    """Preprocessor avanzado para imágenes de facturas"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Parámetros de calidad
        self.min_resolution = (800, 600)
        self.max_resolution = (3000, 3000)
        self.target_dpi = 300

    def preprocess_factura(self, image_path: str, auto_enhance: bool = True) -> PreprocessResult:
        """
        Preprocessar imagen de factura para OCR óptimo

        Args:
            image_path: Ruta a la imagen
            auto_enhance: Aplicar mejoras automáticas

        Returns:
            PreprocessResult con imagen procesada y metadatos
        """
        processing_steps = []

        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar imagen: {image_path}")

            original_size = (image.shape[1], image.shape[0])
            processing_steps.append("imagen_cargada")

            # 1. Redimensionar si necesario
            image = self._resize_if_needed(image)
            if image.shape[:2] != original_size:
                processing_steps.append("redimensionado")

            # 2. Detectar y corregir orientación
            rotation_angle = self._detect_orientation(image)
            if abs(rotation_angle) > 1:  # Solo rotar si es significativo
                image = self._rotate_image(image, rotation_angle)
                processing_steps.append(f"rotacion_{rotation_angle:.1f}deg")

            # 3. Detectar y corregir perspectiva
            perspective_corrected = False
            corrected_image = self._correct_perspective(image)
            if corrected_image is not None:
                image = corrected_image
                perspective_corrected = True
                processing_steps.append("perspectiva_corregida")

            # 4. Detectar ROI (región de interés)
            roi_detected = False
            roi_image = self._detect_roi_factura(image)
            if roi_image is not None:
                image = roi_image
                roi_detected = True
                processing_steps.append("roi_detectado")

            # 5. Mejoras de calidad automáticas
            if auto_enhance:
                image = self._enhance_quality(image)
                processing_steps.append("calidad_mejorada")

            # 6. Preparar para OCR
            image = self._prepare_for_ocr(image)
            processing_steps.append("preparado_ocr")

            # Calcular score de calidad
            quality_score = self._calculate_quality_score(image)

            return PreprocessResult(
                processed_image=image,
                original_size=original_size,
                rotation_angle=rotation_angle,
                perspective_corrected=perspective_corrected,
                roi_detected=roi_detected,
                quality_score=quality_score,
                processing_steps=processing_steps
            )

        except Exception as e:
            self.logger.error(f"Error en preprocessing: {e}")
            # Retornar imagen original en caso de error
            fallback_image = cv2.imread(image_path)
            return PreprocessResult(
                processed_image=fallback_image,
                original_size=original_size,
                rotation_angle=0.0,
                perspective_corrected=False,
                roi_detected=False,
                quality_score=0.5,
                processing_steps=["error", str(e)]
            )

    def _resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Redimensionar imagen si excede límites o es muy pequeña"""
        height, width = image.shape[:2]

        # Verificar si necesita redimensionado
        if (width < self.min_resolution[0] or height < self.min_resolution[1] or 
            width > self.max_resolution[0] or height > self.max_resolution[1]):

            # Calcular nuevo tamaño manteniendo aspect ratio
            aspect_ratio = width / height

            if width > self.max_resolution[0] or height > self.max_resolution[1]:
                # Reducir tamaño
                if width > height:
                    new_width = self.max_resolution[0]
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = self.max_resolution[1]
                    new_width = int(new_height * aspect_ratio)
            else:
                # Aumentar tamaño
                if width < height:
                    new_width = self.min_resolution[0]
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = self.min_resolution[1]
                    new_width = int(new_height * aspect_ratio)

            # Aplicar redimensionado con interpolación de calidad
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        return image

    def _detect_orientation(self, image: np.ndarray) -> float:
        """Detectar orientación de la imagen usando análisis de texto"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Aplicar threshold adaptativo
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # Encontrar contornos de texto
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filtrar contornos por tamaño (probable texto)
            text_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                if 50 < area < 5000 and 2 <= w/h <= 20:  # Proporción típica de texto
                    text_contours.append(contour)

            if len(text_contours) < 3:
                return 0.0  # No hay suficiente texto para determinar orientación

            # Calcular ángulos dominantes
            angles = []
            for contour in text_contours:
                rect = cv2.minAreaRect(contour)
                angle = rect[2]

                # Normalizar ángulo entre -45 y 45
                if angle < -45:
                    angle += 90
                elif angle > 45:
                    angle -= 90

                angles.append(angle)

            # Usar mediana para robustez contra outliers
            if angles:
                median_angle = np.median(angles)

                # Solo retornar ángulos significativos
                if abs(median_angle) > 1:
                    return -median_angle  # Negativo para corregir

            return 0.0

        except Exception as e:
            self.logger.warning(f"Error detectando orientación: {e}")
            return 0.0

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotar imagen manteniendo todo el contenido visible"""
        try:
            height, width = image.shape[:2]
            center = (width // 2, height // 2)

            # Matriz de rotación
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Calcular nuevo tamaño para contener toda la imagen
            cos_angle = abs(rotation_matrix[0, 0])
            sin_angle = abs(rotation_matrix[0, 1])

            new_width = int((height * sin_angle) + (width * cos_angle))
            new_height = int((height * cos_angle) + (width * sin_angle))

            # Ajustar matriz de traslación
            rotation_matrix[0, 2] += (new_width / 2) - center[0]
            rotation_matrix[1, 2] += (new_height / 2) - center[1]

            # Aplicar rotación
            rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                   flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

            return rotated

        except Exception as e:
            self.logger.warning(f"Error rotando imagen: {e}")
            return image

    def _correct_perspective(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Corregir perspectiva de la factura"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detectar bordes
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Detectar líneas con Hough Transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            if lines is None or len(lines) < 4:
                return None

            # Encontrar esquinas del documento
            corners = self._find_document_corners(edges)

            if corners is None:
                return None

            # Ordenar esquinas: top-left, top-right, bottom-right, bottom-left
            corners = self._order_corners(corners)

            # Calcular dimensiones del rectángulo de destino
            width_top = np.linalg.norm(corners[1] - corners[0])
            width_bottom = np.linalg.norm(corners[2] - corners[3])
            width = max(int(width_top), int(width_bottom))

            height_right = np.linalg.norm(corners[2] - corners[1])
            height_left = np.linalg.norm(corners[3] - corners[0])
            height = max(int(height_right), int(height_left))

            # Puntos de destino
            dst_corners = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)

            # Calcular matriz de perspectiva
            perspective_matrix = cv2.getPerspectiveTransform(corners, dst_corners)

            # Aplicar corrección de perspectiva
            corrected = cv2.warpPerspective(image, perspective_matrix, (width, height))

            return corrected

        except Exception as e:
            self.logger.warning(f"Error corrigiendo perspectiva: {e}")
            return None

    def _find_document_corners(self, edges: np.ndarray) -> Optional[np.ndarray]:
        """Encontrar esquinas del documento"""
        try:
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Ordenar contornos por área
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours[:5]:  # Revisar los 5 contornos más grandes
                # Aproximar contorno a polígono
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Si es un cuadrilátero, probablemente es el documento
                if len(approx) == 4:
                    return approx.reshape(4, 2).astype(np.float32)

            return None

        except Exception as e:
            self.logger.warning(f"Error encontrando esquinas: {e}")
            return None

    def _order_corners(self, corners: np.ndarray) -> np.ndarray:
        """Ordenar esquinas en orden: top-left, top-right, bottom-right, bottom-left"""
        # Calcular centro de masa
        center = np.mean(corners, axis=0)

        # Ordenar por ángulo desde el centro
        def angle_from_center(point):
            return math.atan2(point[1] - center[1], point[0] - center[0])

        sorted_corners = sorted(corners, key=angle_from_center)

        # Reorganizar para empezar con top-left
        # Encontrar el punto más cercano a (0,0)
        distances = [np.linalg.norm(corner) for corner in sorted_corners]
        start_index = distances.index(min(distances))

        # Rotar array para empezar con top-left
        ordered = sorted_corners[start_index:] + sorted_corners[:start_index]

        return np.array(ordered, dtype=np.float32)

    def _detect_roi_factura(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detectar región de interés de la factura (eliminar márgenes)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Threshold para detectar contenido
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binary = cv2.bitwise_not(binary)  # Invertir: texto negro sobre blanco

            # Encontrar proyecciones horizontales y verticales
            horizontal_proj = np.sum(binary, axis=1)
            vertical_proj = np.sum(binary, axis=0)

            # Encontrar límites del contenido
            h_threshold = np.max(horizontal_proj) * 0.1
            v_threshold = np.max(vertical_proj) * 0.1

            # Límites verticales (filas)
            content_rows = np.where(horizontal_proj > h_threshold)[0]
            if len(content_rows) == 0:
                return None

            top = content_rows[0]
            bottom = content_rows[-1]

            # Límites horizontales (columnas)
            content_cols = np.where(vertical_proj > v_threshold)[0]
            if len(content_cols) == 0:
                return None

            left = content_cols[0]
            right = content_cols[-1]

            # Agregar margen pequeño
            margin = 20
            height, width = image.shape[:2]

            top = max(0, top - margin)
            bottom = min(height, bottom + margin)
            left = max(0, left - margin)
            right = min(width, right + margin)

            # Verificar que la ROI sea significativa
            roi_width = right - left
            roi_height = bottom - top

            if roi_width < width * 0.3 or roi_height < height * 0.3:
                return None  # ROI muy pequeña

            # Extraer ROI
            roi = image[top:bottom, left:right]

            return roi

        except Exception as e:
            self.logger.warning(f"Error detectando ROI: {e}")
            return None

    def _enhance_quality(self, image: np.ndarray) -> np.ndarray:
        """Mejorar calidad de imagen para OCR"""
        try:
            # 1. Reducir ruido con filtro bilateral
            denoised = cv2.bilateralFilter(image, 9, 75, 75)

            # 2. Mejorar contraste con CLAHE
            gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced_gray = clahe.apply(gray)

            # Convertir de vuelta a color manteniendo la mejora
            enhanced = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)

            # 3. Sharpening (realce de bordes)
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            # Combinar imagen original con la sharpened (50-50)
            result = cv2.addWeighted(enhanced, 0.5, sharpened, 0.5, 0)

            return result

        except Exception as e:
            self.logger.warning(f"Error mejorando calidad: {e}")
            return image

    def _prepare_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preparar imagen final para OCR"""
        try:
            # Convertir a escala de grises si no lo está
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Normalizar intensidades
            normalized = cv2.equalizeHist(gray)

            # Threshold adaptativo para mejor contraste
            binary = cv2.adaptiveThreshold(
                normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )

            # Operaciones morfológicas para limpiar
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Convertir de vuelta a 3 canales para compatibilidad
            result = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)

            return result

        except Exception as e:
            self.logger.warning(f"Error preparando para OCR: {e}")
            return image

    def _calculate_quality_score(self, image: np.ndarray) -> float:
        """Calcular score de calidad de la imagen"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 1. Sharpness score (usando varianza del Laplaciano)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalizar

            # 2. Contrast score
            contrast_score = gray.std() / 255.0

            # 3. Brightness score (penalizar demasiado oscuro/claro)
            brightness = gray.mean() / 255.0
            brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Óptimo en 0.5

            # 4. Resolution score
            height, width = gray.shape
            pixels = width * height
            resolution_score = min(pixels / (1000 * 1000), 1.0)  # Normalizar a 1MP

            # Score final ponderado
            final_score = (
                sharpness_score * 0.4 +
                contrast_score * 0.3 +
                brightness_score * 0.2 +
                resolution_score * 0.1
            )

            return round(final_score, 3)

        except Exception as e:
            self.logger.warning(f"Error calculando quality score: {e}")
            return 0.5

    def batch_preprocess(self, image_paths: List[str], auto_enhance: bool = True) -> List[PreprocessResult]:
        """Procesar múltiples imágenes en batch"""
        results = []

        for image_path in image_paths:
            try:
                result = self.preprocess_factura(image_path, auto_enhance)
                results.append(result)
                self.logger.info(f"Procesada {image_path}: quality={result.quality_score}")
            except Exception as e:
                self.logger.error(f"Error procesando {image_path}: {e}")
                # Continuar con la siguiente imagen

        return results

    def save_processed_image(self, result: PreprocessResult, output_path: str) -> bool:
        """Guardar imagen procesada"""
        try:
            success = cv2.imwrite(output_path, result.processed_image)
            if success:
                self.logger.info(f"Imagen guardada en {output_path}")
            return success
        except Exception as e:
            self.logger.error(f"Error guardando imagen: {e}")
            return False

# Ejemplo de uso
if __name__ == "__main__":
    preprocessor = ImagePreprocessor()

    # Test básico
    print("Image Preprocessor Avanzado inicializado")
    print("Funciones disponibles:")
    print("- preprocess_factura()")
    print("- batch_preprocess()")
    print("- save_processed_image()")
