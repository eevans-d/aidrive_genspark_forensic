"""
OCR Testing Framework
====================

Framework completo para testing y comparativa de performance entre
OCR básico vs OCR avanzado. Incluye métricas, benchmarks y reportes
automáticos de accuracy y performance.

Autor: Sistema Inventario Retail Argentino
Fecha: 2025-08-22
"""

import os
import time
import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import asyncio
import logging
from pathlib import Path

# Importar OCR engines para comparación
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_engine_advanced import OCREngineAdvanced
from image_preprocessor import ImagePreprocessor  
from factura_validator import FacturaValidatorArgentino
from ocr_postprocessor import OCRPostprocessor

# OCR Básico (simulado - representaría tu sistema anterior)
import easyocr

@dataclass
class OCRTestResult:
    """Resultado de test OCR individual"""
    image_path: str
    engine_name: str
    processing_time: float
    confidence_score: float
    text_extracted: str
    structured_data: Dict
    validation_passed: bool
    errors: List[str]
    accuracy_score: Optional[float] = None

@dataclass
class ComparisonReport:
    """Reporte de comparación entre engines"""
    test_timestamp: str
    total_images_tested: int
    basic_ocr_results: List[OCRTestResult]
    advanced_ocr_results: List[OCRTestResult]
    performance_comparison: Dict
    accuracy_comparison: Dict
    recommendations: List[str]

class OCRTestingFramework:
    """Framework principal de testing OCR"""

    def __init__(self, output_dir: str = "/home/user/output/ocr_testing"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # Inicializar engines
        self.advanced_ocr = OCREngineAdvanced()
        self.image_preprocessor = ImagePreprocessor()
        self.factura_validator = FacturaValidatorArgentino()
        self.ocr_postprocessor = OCRPostprocessor()

        # OCR básico (EasyOCR simple)
        try:
            self.basic_ocr = easyocr.Reader(['es', 'en'], gpu=False)
            self.logger.info("✅ OCR básico (EasyOCR) iniciado")
        except Exception as e:
            self.logger.warning(f"⚠️ Error iniciando OCR básico: {e}")
            self.basic_ocr = None

        # Métricas acumulativas
        self.test_results = []

    async def run_comprehensive_test(self, 
                                   test_images: List[str], 
                                   ground_truth_data: Optional[List[Dict]] = None) -> ComparisonReport:
        """
        Ejecutar test comprensivo comparando OCR básico vs avanzado

        Args:
            test_images: Lista de rutas a imágenes de test
            ground_truth_data: Datos reales para calcular accuracy (opcional)

        Returns:
            ComparisonReport con resultados completos
        """
        self.logger.info(f"🧪 Iniciando test comprensivo con {len(test_images)} imágenes")

        basic_results = []
        advanced_results = []

        for i, image_path in enumerate(test_images):
            self.logger.info(f"📸 Procesando imagen {i+1}/{len(test_images)}: {os.path.basename(image_path)}")

            # Ground truth para esta imagen si está disponible
            ground_truth = ground_truth_data[i] if ground_truth_data and i < len(ground_truth_data) else None

            # Test OCR Básico
            basic_result = await self._test_basic_ocr(image_path, ground_truth)
            basic_results.append(basic_result)

            # Test OCR Avanzado  
            advanced_result = await self._test_advanced_ocr(image_path, ground_truth)
            advanced_results.append(advanced_result)

            # Pequeña pausa para evitar sobrecarga
            await asyncio.sleep(0.1)

        # Generar reporte comparativo
        report = self._generate_comparison_report(basic_results, advanced_results)

        # Guardar resultados
        await self._save_test_results(report)

        self.logger.info("✅ Test comprensivo completado")
        return report

    async def _test_basic_ocr(self, image_path: str, ground_truth: Optional[Dict] = None) -> OCRTestResult:
        """Test con OCR básico (EasyOCR simple)"""
        start_time = time.time()

        try:
            if not self.basic_ocr:
                raise Exception("OCR básico no disponible")

            # OCR simple sin preprocessing
            results = self.basic_ocr.readtext(image_path)

            # Extraer texto
            text_parts = []
            confidences = []

            for bbox, text, confidence in results:
                if confidence > 0.3:  # Filtro básico
                    text_parts.append(text)
                    confidences.append(confidence)

            extracted_text = " ".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extracción básica de campos (regex simple)
            structured_data = self._basic_field_extraction(extracted_text)

            # Validación básica
            validation_passed = bool(structured_data.get("cuit") and structured_data.get("total"))

            processing_time = time.time() - start_time

            # Calcular accuracy si hay ground truth
            accuracy_score = None
            if ground_truth:
                accuracy_score = self._calculate_accuracy(structured_data, ground_truth)

            return OCRTestResult(
                image_path=image_path,
                engine_name="OCR_Basico_EasyOCR",
                processing_time=processing_time,
                confidence_score=avg_confidence,
                text_extracted=extracted_text,
                structured_data=structured_data,
                validation_passed=validation_passed,
                errors=[],
                accuracy_score=accuracy_score
            )

        except Exception as e:
            processing_time = time.time() - start_time

            return OCRTestResult(
                image_path=image_path,
                engine_name="OCR_Basico_EasyOCR",
                processing_time=processing_time,
                confidence_score=0.0,
                text_extracted="",
                structured_data={},
                validation_passed=False,
                errors=[str(e)],
                accuracy_score=0.0 if ground_truth else None
            )

    async def _test_advanced_ocr(self, image_path: str, ground_truth: Optional[Dict] = None) -> OCRTestResult:
        """Test con OCR avanzado completo"""
        start_time = time.time()

        try:
            # 1. Preprocessar imagen
            preprocess_result = self.image_preprocessor.preprocess_factura(image_path, auto_enhance=True)

            # Guardar imagen preprocessada temporalmente
            preprocessed_path = f"/tmp/test_preprocessed_{os.path.basename(image_path)}"
            import cv2
            cv2.imwrite(preprocessed_path, preprocess_result.processed_image)

            # 2. OCR Avanzado
            ocr_result = await self.advanced_ocr.process_factura(preprocessed_path)

            if not ocr_result.get("success", False):
                raise Exception(f"OCR avanzado falló: {ocr_result.get('error')}")

            # 3. Postprocesamiento
            postprocess_result = self.ocr_postprocessor.postprocess_ocr_result(
                ocr_result["text_raw"], 
                ocr_result["confidence"]
            )

            # 4. Validación completa
            validation_result = self.factura_validator.validate_factura_completa(
                postprocess_result.cleaned_text
            )

            # 5. Combinar datos estructurados
            structured_data = {
                **ocr_result.get("campos_extraidos", {}),
                **postprocess_result.structured_data,
                **validation_result.normalized_data
            }

            processing_time = time.time() - start_time

            # Limpiar archivo temporal
            try:
                os.unlink(preprocessed_path)
            except OSError:
                pass

            # Calcular accuracy si hay ground truth
            accuracy_score = None
            if ground_truth:
                accuracy_score = self._calculate_accuracy(structured_data, ground_truth)

            return OCRTestResult(
                image_path=image_path,
                engine_name="OCR_Avanzado_MultiEngine",
                processing_time=processing_time,
                confidence_score=postprocess_result.confidence_score,
                text_extracted=postprocess_result.cleaned_text,
                structured_data=structured_data,
                validation_passed=validation_result.is_valid,
                errors=validation_result.errors,
                accuracy_score=accuracy_score
            )

        except Exception as e:
            processing_time = time.time() - start_time

            return OCRTestResult(
                image_path=image_path,
                engine_name="OCR_Avanzado_MultiEngine",
                processing_time=processing_time,
                confidence_score=0.0,
                text_extracted="",
                structured_data={},
                validation_passed=False,
                errors=[str(e)],
                accuracy_score=0.0 if ground_truth else None
            )

    def _basic_field_extraction(self, text: str) -> Dict:
        """Extracción básica de campos con regex simple"""
        import re

        fields = {}
        text_upper = text.upper()

        # Patrones básicos
        patterns = {
            "cuit": r'CUIT[:\s]*(\d{2}[-\s]*\d{8}[-\s]*\d{1})',
            "numero_factura": r'N°[:\s]*(\d{4}[-\s]*\d{8})',
            "fecha": r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            "total": r'TOTAL[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "razon_social": r'RAZON\s+SOCIAL[:\s]*([A-Z\s\.]+)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text_upper)
            if match:
                fields[field] = match.group(1).strip()

        return fields

    def _calculate_accuracy(self, extracted_data: Dict, ground_truth: Dict) -> float:
        """Calcular accuracy comparando con ground truth"""
        if not ground_truth:
            return 0.0

        correct_fields = 0
        total_fields = 0

        # Campos importantes para comparar
        important_fields = ["cuit", "numero_factura", "fecha", "total", "razon_social"]

        for field in important_fields:
            if field in ground_truth:
                total_fields += 1

                extracted_value = extracted_data.get(field, "").strip().upper()
                ground_truth_value = str(ground_truth[field]).strip().upper()

                # Normalizar para comparación
                extracted_norm = self._normalize_for_comparison(extracted_value)
                ground_truth_norm = self._normalize_for_comparison(ground_truth_value)

                # Calcular similitud
                similarity = self._calculate_similarity(extracted_norm, ground_truth_norm)

                # Considerar correcto si similitud > 80%
                if similarity > 0.8:
                    correct_fields += 1

        return correct_fields / total_fields if total_fields > 0 else 0.0

    def _normalize_for_comparison(self, text: str) -> str:
        """Normalizar texto para comparación"""
        import re
        # Remover puntuación y espacios, solo alphanumeric
        return re.sub(r'[^A-Za-z0-9]', '', text)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud entre dos textos"""
        if not text1 or not text2:
            return 0.0

        # Usar Levenshtein distance simple
        if text1 == text2:
            return 1.0

        # Simple character-based similarity
        common_chars = set(text1) & set(text2)
        total_chars = set(text1) | set(text2)

        return len(common_chars) / len(total_chars) if total_chars else 0.0

    def _generate_comparison_report(self, 
                                  basic_results: List[OCRTestResult], 
                                  advanced_results: List[OCRTestResult]) -> ComparisonReport:
        """Generar reporte comparativo detallado"""

        # Calcular métricas de performance
        basic_times = [r.processing_time for r in basic_results if r.processing_time > 0]
        advanced_times = [r.processing_time for r in advanced_results if r.processing_time > 0]

        performance_comparison = {
            "basic_ocr": {
                "avg_processing_time": sum(basic_times) / len(basic_times) if basic_times else 0,
                "min_processing_time": min(basic_times) if basic_times else 0,
                "max_processing_time": max(basic_times) if basic_times else 0,
                "success_rate": sum(1 for r in basic_results if not r.errors) / len(basic_results),
                "avg_confidence": sum(r.confidence_score for r in basic_results) / len(basic_results)
            },
            "advanced_ocr": {
                "avg_processing_time": sum(advanced_times) / len(advanced_times) if advanced_times else 0,
                "min_processing_time": min(advanced_times) if advanced_times else 0,
                "max_processing_time": max(advanced_times) if advanced_times else 0,
                "success_rate": sum(1 for r in advanced_results if not r.errors) / len(advanced_results),
                "avg_confidence": sum(r.confidence_score for r in advanced_results) / len(advanced_results)
            }
        }

        # Calcular métricas de accuracy si hay ground truth
        basic_accuracies = [r.accuracy_score for r in basic_results if r.accuracy_score is not None]
        advanced_accuracies = [r.accuracy_score for r in advanced_results if r.accuracy_score is not None]

        accuracy_comparison = {}
        if basic_accuracies and advanced_accuracies:
            accuracy_comparison = {
                "basic_ocr_avg_accuracy": sum(basic_accuracies) / len(basic_accuracies),
                "advanced_ocr_avg_accuracy": sum(advanced_accuracies) / len(advanced_accuracies),
                "accuracy_improvement": (sum(advanced_accuracies) / len(advanced_accuracies)) - (sum(basic_accuracies) / len(basic_accuracies)),
                "validation_pass_rate_basic": sum(1 for r in basic_results if r.validation_passed) / len(basic_results),
                "validation_pass_rate_advanced": sum(1 for r in advanced_results if r.validation_passed) / len(advanced_results)
            }

        # Generar recomendaciones
        recommendations = self._generate_recommendations(performance_comparison, accuracy_comparison)

        return ComparisonReport(
            test_timestamp=datetime.now().isoformat(),
            total_images_tested=len(basic_results),
            basic_ocr_results=basic_results,
            advanced_ocr_results=advanced_results,
            performance_comparison=performance_comparison,
            accuracy_comparison=accuracy_comparison,
            recommendations=recommendations
        )

    def _generate_recommendations(self, performance: Dict, accuracy: Dict) -> List[str]:
        """Generar recomendaciones basadas en resultados"""
        recommendations = []

        # Análisis de performance
        basic_time = performance["basic_ocr"]["avg_processing_time"]
        advanced_time = performance["advanced_ocr"]["avg_processing_time"]

        if advanced_time > basic_time * 2:
            recommendations.append("⚠️ OCR avanzado es significativamente más lento, considerar optimizaciones")
        elif advanced_time > basic_time * 1.5:
            recommendations.append("📊 OCR avanzado es moderadamente más lento pero ofrece mejor accuracy")
        else:
            recommendations.append("✅ OCR avanzado mantiene performance competitivo")

        # Análisis de accuracy
        if accuracy:
            accuracy_improvement = accuracy.get("accuracy_improvement", 0)
            if accuracy_improvement > 0.2:
                recommendations.append("🎯 OCR avanzado muestra mejora significativa en accuracy (+20%)")
            elif accuracy_improvement > 0.1:
                recommendations.append("📈 OCR avanzado muestra mejora moderada en accuracy (+10%)")
            elif accuracy_improvement < 0:
                recommendations.append("⚠️ OCR avanzado muestra accuracy inferior, revisar configuración")

        # Análisis de confianza
        basic_conf = performance["basic_ocr"]["avg_confidence"]
        advanced_conf = performance["advanced_ocr"]["avg_confidence"]

        if advanced_conf > basic_conf + 0.1:
            recommendations.append("🔍 OCR avanzado muestra mayor confianza en resultados")

        # Análisis de validación
        if accuracy:
            basic_validation = accuracy.get("validation_pass_rate_basic", 0)
            advanced_validation = accuracy.get("validation_pass_rate_advanced", 0)

            if advanced_validation > basic_validation + 0.2:
                recommendations.append("✅ OCR avanzado tiene mayor tasa de validación exitosa")

        return recommendations

    async def _save_test_results(self, report: ComparisonReport):
        """Guardar resultados de test en múltiples formatos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Guardar reporte completo en JSON
        json_path = self.output_dir / f"ocr_comparison_report_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

        # 2. Guardar métricas en CSV
        csv_path = self.output_dir / f"ocr_performance_metrics_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Headers
            writer.writerow([
                'imagen', 'engine', 'tiempo_procesamiento', 'confidence', 
                'validacion_exitosa', 'accuracy', 'errores'
            ])

            # Datos básicos
            for result in report.basic_ocr_results:
                writer.writerow([
                    os.path.basename(result.image_path),
                    result.engine_name,
                    f"{result.processing_time:.3f}",
                    f"{result.confidence_score:.3f}",
                    result.validation_passed,
                    f"{result.accuracy_score:.3f}" if result.accuracy_score else "N/A",
                    "|".join(result.errors)
                ])

            # Datos avanzados
            for result in report.advanced_ocr_results:
                writer.writerow([
                    os.path.basename(result.image_path),
                    result.engine_name,
                    f"{result.processing_time:.3f}",
                    f"{result.confidence_score:.3f}",
                    result.validation_passed,
                    f"{result.accuracy_score:.3f}" if result.accuracy_score else "N/A",
                    "|".join(result.errors)
                ])

        # 3. Generar reporte HTML legible
        html_path = self.output_dir / f"ocr_comparison_report_{timestamp}.html"
        html_content = self._generate_html_report(report)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"📊 Resultados guardados en {self.output_dir}")
        self.logger.info(f"   - JSON: {json_path.name}")
        self.logger.info(f"   - CSV: {csv_path.name}")
        self.logger.info(f"   - HTML: {html_path.name}")

    def _generate_html_report(self, report: ComparisonReport) -> str:
        """Generar reporte HTML legible"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OCR Comparison Report - {report.test_timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric-box {{ background: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .recommendation {{ background: #fffacd; padding: 10px; margin: 5px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 OCR Comparison Report</h1>
                <p><strong>Timestamp:</strong> {report.test_timestamp}</p>
                <p><strong>Total Images Tested:</strong> {report.total_images_tested}</p>
            </div>

            <h2>📊 Performance Comparison</h2>
            <div class="metrics">
                <div class="metric-box">
                    <h3>OCR Básico</h3>
                    <p><strong>Tiempo Promedio:</strong> {report.performance_comparison['basic_ocr']['avg_processing_time']:.3f}s</p>
                    <p><strong>Success Rate:</strong> {report.performance_comparison['basic_ocr']['success_rate']:.1%}</p>
                    <p><strong>Confianza Promedio:</strong> {report.performance_comparison['basic_ocr']['avg_confidence']:.3f}</p>
                </div>
                <div class="metric-box">
                    <h3>OCR Avanzado</h3>
                    <p><strong>Tiempo Promedio:</strong> {report.performance_comparison['advanced_ocr']['avg_processing_time']:.3f}s</p>
                    <p><strong>Success Rate:</strong> {report.performance_comparison['advanced_ocr']['success_rate']:.1%}</p>
                    <p><strong>Confianza Promedio:</strong> {report.performance_comparison['advanced_ocr']['avg_confidence']:.3f}</p>
                </div>
            </div>
        """

        # Agregar accuracy comparison si está disponible
        if report.accuracy_comparison:
            html += f"""
            <h2>🎯 Accuracy Comparison</h2>
            <div class="metrics">
                <div class="metric-box">
                    <p><strong>OCR Básico Accuracy:</strong> {report.accuracy_comparison['basic_ocr_avg_accuracy']:.1%}</p>
                    <p><strong>OCR Avanzado Accuracy:</strong> {report.accuracy_comparison['advanced_ocr_avg_accuracy']:.1%}</p>
                    <p><strong>Mejora:</strong> {report.accuracy_comparison['accuracy_improvement']:+.1%}</p>
                </div>
            </div>
            """

        # Agregar recomendaciones
        html += "<h2>💡 Recomendaciones</h2>"
        for rec in report.recommendations:
            html += f'<div class="recommendation">{rec}</div>'

        html += """
            </body>
            </html>
        """

        return html

    def create_test_images(self, count: int = 5) -> List[str]:
        """Crear imágenes de test sintéticas para pruebas"""
        import cv2
        import numpy as np

        test_images = []

        for i in range(count):
            # Crear imagen de factura sintética
            img = np.ones((400, 800, 3), dtype=np.uint8) * 255

            # Agregar texto de ejemplo
            cv2.putText(img, f"FACTURA B", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
            cv2.putText(img, f"CUIT: 20-1234567{i}-9", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(img, f"N° 0001-0000012{i}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(img, f"FECHA: 15/08/2025", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(img, f"TOTAL: $1.23{i},56", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            cv2.putText(img, f"RAZON SOCIAL: EMPRESA TEST {i}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # Guardar imagen
            img_path = self.output_dir / f"test_factura_{i:02d}.jpg"
            cv2.imwrite(str(img_path), img)
            test_images.append(str(img_path))

        self.logger.info(f"📸 Creadas {count} imágenes de test en {self.output_dir}")
        return test_images

# Funciones utilitarias para uso standalone
async def run_quick_comparison_test():
    """Ejecutar test rápido de comparación"""
    framework = OCRTestingFramework()

    # Crear imágenes de test
    test_images = framework.create_test_images(3)

    # Ground truth de ejemplo
    ground_truth = [
        {"cuit": "20-12345670-9", "total": "1230,56", "numero_factura": "0001-00000120"},
        {"cuit": "20-12345671-9", "total": "1231,56", "numero_factura": "0001-00000121"},
        {"cuit": "20-12345672-9", "total": "1232,56", "numero_factura": "0001-00000122"}
    ]

    # Ejecutar test
    report = await framework.run_comprehensive_test(test_images, ground_truth)

    return report

if __name__ == "__main__":
    import asyncio

    async def main():
        print("🧪 Ejecutando OCR Testing Framework")
        report = await run_quick_comparison_test()

        print(f"✅ Test completado: {report.total_images_tested} imágenes procesadas")
        print(f"📊 Recomendaciones: {len(report.recommendations)}")
        for rec in report.recommendations[:3]:  # Mostrar primeras 3
            print(f"   - {rec}")

    asyncio.run(main())
