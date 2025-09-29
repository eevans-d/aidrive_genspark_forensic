#!/usr/bin/env python3
"""
TESTS DE CALIDAD FORENSE
Suite de tests para validar metodología forense en análisis técnicos
"""

import unittest
import re
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Añadir scripts al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from forensic_validator import ForensicValidator
except ImportError:
    ForensicValidator = None


class TestForensicQuality(unittest.TestCase):
    """Tests de calidad para análisis forenses"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para toda la clase de tests"""
        cls.repo_path = Path(__file__).parent.parent
        cls.forensic_files = list(cls.repo_path.glob("**/EJEMPLO_ANALISIS_FORENSE_*.md"))
        
        if not cls.forensic_files:
            # Buscar archivos alternativos
            cls.forensic_files = list(cls.repo_path.glob("**/ANALISIS_FORENSE_*.md"))
        
        print(f"📁 Encontrados {len(cls.forensic_files)} archivos forenses para testing")
        for f in cls.forensic_files:
            print(f"  - {f.name}")
    
    def test_forensic_files_exist(self):
        """Test: Verificar que existen archivos de análisis forense"""
        self.assertGreater(
            len(self.forensic_files), 0,
            "No se encontraron archivos de análisis forense en el repositorio"
        )
    
    def test_forensic_citations_quality(self):
        """Test: Verificar calidad de citas archivo:línea"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar citas formato archivo:línea
                citations = re.findall(r'`[^`]+:\d+(-\d+)?`', content)
                
                # Verificar cantidad mínima
                self.assertGreaterEqual(
                    len(citations), 10,
                    f"❌ {forensic_file.name}: Insuficientes citas archivo:línea. "
                    f"Encontradas: {len(citations)}, Mínimo: 10"
                )
                
                # Verificar formato correcto
                for citation in citations[:5]:  # Verificar primeras 5
                    self.assertRegex(
                        citation,
                        r'`[^`]+:\d+(-\d+)?`',
                        f"❌ {forensic_file.name}: Formato incorrecto de cita: {citation}"
                    )
    
    def test_risk_assessment_quality(self):
        """Test: Verificar calidad de evaluación de riesgos"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar marcadores de riesgo con severidad
                risk_patterns = [
                    r'RIESGO\s+(CRÍTICO|ALTO|MEDIO)',
                    r'RISK\s+(CRITICAL|HIGH|MEDIUM)',
                    r'🔴\s*(CRÍTICO|CRITICAL)',
                    r'🟡\s*(ALTO|HIGH)',
                    r'🟢\s*(MEDIO|MEDIUM)'
                ]
                
                total_risks = 0
                for pattern in risk_patterns:
                    risks = re.findall(pattern, content, re.IGNORECASE)
                    total_risks += len(risks)
                
                self.assertGreaterEqual(
                    total_risks, 3,
                    f"❌ {forensic_file.name}: Insuficientes marcadores de riesgo. "
                    f"Encontrados: {total_risks}, Mínimo: 3"
                )
    
    def test_passive_mode_compliance(self):
        """Test: Verificar cumplimiento de modo pasivo (no modificación)"""
        
        # Patrones que violan modo pasivo
        violation_patterns = [
            r'\bmodifica\s+',
            r'\bcambia\s+',
            r'\bedita\s+',
            r'\bmodify\s+',
            r'\bchange\s+',
            r'\bedit\s+',
            r'debes\s+modificar',
            r'debes\s+cambiar',
            r'you\s+should\s+modify',
            r'you\s+should\s+change'
        ]
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8').lower()
                
                violations = []
                for pattern in violation_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    violations.extend(matches)
                
                self.assertEqual(
                    len(violations), 0,
                    f"❌ {forensic_file.name}: Violaciones de modo pasivo detectadas: {violations[:3]}..."
                )
    
    def test_verification_commands_quality(self):
        """Test: Verificar calidad de comandos de verificación"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar bloques de comandos bash
                command_blocks = re.findall(r'```bash(.*?)```', content, re.DOTALL)
                
                self.assertGreaterEqual(
                    len(command_blocks), 1,
                    f"❌ {forensic_file.name}: Sin bloques de comandos de verificación"
                )
                
                # Contar comandos ejecutables
                total_commands = 0
                for block in command_blocks:
                    lines = [line.strip() for line in block.split('\n') 
                           if line.strip() and not line.startswith('#') 
                           and not line.startswith('```')]
                    
                    # Filtrar comandos reales (no comentarios o vacíos)
                    real_commands = [line for line in lines 
                                   if not line.startswith('#') and 
                                   any(cmd in line for cmd in ['find', 'grep', 'ls', 'wc', 'head', 'tail', 'cat'])]
                    
                    total_commands += len(real_commands)
                
                self.assertGreaterEqual(
                    total_commands, 5,
                    f"❌ {forensic_file.name}: Insuficientes comandos ejecutables. "
                    f"Encontrados: {total_commands}, Mínimo: 5"
                )
    
    def test_mandatory_structure(self):
        """Test: Verificar estructura metodológica obligatoria"""
        
        mandatory_sections = [
            "STACK TECNOLÓGICO",
            "ARQUITECTURA",
            "REQUISITOS DE DESPLIEGUE",
            "CONFIGURACIÓN"
        ]
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8').upper()
                
                missing_sections = []
                for section in mandatory_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                self.assertEqual(
                    len(missing_sections), 0,
                    f"❌ {forensic_file.name}: Secciones obligatorias faltantes: {missing_sections}"
                )
    
    def test_evidence_integrity(self):
        """Test: Verificar integridad de evidencia (NO EVIDENCIADO)"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar marcadores de honestidad forense
                honesty_markers = re.findall(
                    r'(NO\s+EVIDENCIADO|NOT\s+EVIDENCED|SIN\s+EVIDENCIA)', 
                    content, re.IGNORECASE
                )
                
                # Debe haber al menos algunos elementos no evidenciados
                self.assertGreaterEqual(
                    len(honesty_markers), 1,
                    f"❌ {forensic_file.name}: Sin marcadores 'NO EVIDENCIADO'. "
                    "El análisis forense debe reconocer limitaciones."
                )
    
    def test_project_specificity(self):
        """Test: Verificar especificidad del proyecto (no genérico)"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8').lower()
                
                # Indicadores de contenido específico
                specific_indicators = [
                    'requirements.txt',
                    'package.json',
                    'main.py',
                    'app.py',
                    'fastapi',
                    'django',
                    'flask',
                    'express',
                    'docker-compose',
                    'dockerfile'
                ]
                
                found_indicators = 0
                for indicator in specific_indicators:
                    if indicator in content:
                        found_indicators += 1
                
                self.assertGreaterEqual(
                    found_indicators, 3,
                    f"❌ {forensic_file.name}: Contenido muy genérico. "
                    f"Indicadores específicos: {found_indicators}/≥3"
                )
    
    def test_comprehensive_coverage(self):
        """Test: Verificar cobertura comprensiva del análisis"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Elementos que deben estar presentes en análisis forense completo
                required_elements = [
                    ('languages', ['python', 'javascript', 'lenguaje']),
                    ('frameworks', ['framework', 'fastapi', 'django', 'flask', 'express']),
                    ('databases', ['database', 'base de datos', 'sql', 'postgresql', 'mysql']),
                    ('dependencies', ['dependencias', 'requirements', 'package.json']),
                    ('architecture', ['arquitectura', 'architecture', 'estructura']),
                    ('deployment', ['despliegue', 'deployment', 'deploy']),
                    ('configuration', ['configuración', 'configuration', 'config'])
                ]
                
                content_lower = content.lower()
                missing_elements = []
                
                for element_name, keywords in required_elements:
                    if not any(keyword in content_lower for keyword in keywords):
                        missing_elements.append(element_name)
                
                self.assertLessEqual(
                    len(missing_elements), 1,
                    f"❌ {forensic_file.name}: Elementos faltantes en cobertura: {missing_elements}"
                )


class TestForensicConsistency(unittest.TestCase):
    """Tests de consistencia cross-proyecto"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para tests de consistencia"""
        cls.repo_path = Path(__file__).parent.parent
        cls.forensic_files = list(cls.repo_path.glob("**/EJEMPLO_ANALISIS_FORENSE_*.md"))
    
    def test_terminology_consistency(self):
        """Test: Verificar consistencia de terminología forense"""
        
        if len(self.forensic_files) < 2:
            self.skipTest("Se requieren al menos 2 archivos forenses para test de consistencia")
        
        # Terminología que debe ser consistente
        standard_terms = [
            'STACK TECNOLÓGICO',
            'ARQUITECTURA DEL SISTEMA',
            'REQUISITOS DE DESPLIEGUE',
            'NO EVIDENCIADO',
            'RIESGO CRÍTICO',
            'RIESGO ALTO',
            'RIESGO MEDIO'
        ]
        
        inconsistent_files = []
        
        for forensic_file in self.forensic_files:
            content = forensic_file.read_text(encoding='utf-8')
            
            missing_terms = []
            for term in standard_terms[:4]:  # Verificar términos principales
                if term not in content:
                    missing_terms.append(term)
            
            if missing_terms:
                inconsistent_files.append((forensic_file.name, missing_terms))
        
        self.assertEqual(
            len(inconsistent_files), 0,
            f"❌ Inconsistencia terminológica en archivos: {inconsistent_files}"
        )
    
    def test_quality_variance(self):
        """Test: Verificar que no hay gran variación en calidad"""
        
        if len(self.forensic_files) < 2:
            self.skipTest("Se requieren al menos 2 archivos forenses para test de varianza")
        
        # Calcular score simple para cada archivo
        file_scores = []
        
        for forensic_file in self.forensic_files:
            content = forensic_file.read_text(encoding='utf-8')
            
            # Score basado en elementos clave
            score = 0
            
            # Citas (hasta 40 puntos)
            citations = len(re.findall(r'`[^`]+:\d+(-\d+)?`', content))
            score += min(40, citations * 2)
            
            # Riesgos (hasta 30 puntos)
            risks = len(re.findall(r'RIESGO\s+(CRÍTICO|ALTO|MEDIO)', content, re.IGNORECASE))
            score += min(30, risks * 10)
            
            # Comandos (hasta 30 puntos)
            commands = len(re.findall(r'```bash.*?```', content, re.DOTALL))
            score += min(30, commands * 15)
            
            file_scores.append((forensic_file.name, score))
        
        # Verificar que no hay gran variación
        scores = [score for _, score in file_scores]
        score_range = max(scores) - min(scores)
        
        self.assertLessEqual(
            score_range, 40,
            f"❌ Gran variación en calidad. Scores: {file_scores}. Rango: {score_range}"
        )


class TestForensicIntegration(unittest.TestCase):
    """Tests de integración con herramientas forenses"""
    
    def setUp(self):
        """Setup para tests de integración"""
        self.repo_path = Path(__file__).parent.parent
    
    @unittest.skipIf(ForensicValidator is None, "ForensicValidator no disponible")
    def test_validator_integration(self):
        """Test: Integración con ForensicValidator"""
        
        validator = ForensicValidator(str(self.repo_path))
        results = validator.validate_all_forensic_files()
        
        # Verificar que el validador funciona
        self.assertIsInstance(results, dict)
        self.assertIn('total_files', results)
        
        # Verificar que encuentra archivos
        if results.get('total_files', 0) > 0:
            self.assertGreater(
                results['overall_compliance'], 0,
                "Validador debe detectar algún nivel de compliance"
            )
    
    def test_file_accessibility(self):
        """Test: Verificar accesibilidad de archivos forenses"""
        
        forensic_files = list(self.repo_path.glob("**/EJEMPLO_ANALISIS_FORENSE_*.md"))
        
        for forensic_file in forensic_files:
            with self.subTest(file=forensic_file.name):
                # Verificar que el archivo es legible
                try:
                    content = forensic_file.read_text(encoding='utf-8')
                    self.assertGreater(
                        len(content), 1000,
                        f"❌ {forensic_file.name}: Archivo muy corto, posible truncamiento"
                    )
                except Exception as e:
                    self.fail(f"❌ {forensic_file.name}: Error al leer archivo: {e}")


def run_forensic_test_suite():
    """Ejecuta la suite completa de tests forenses"""
    
    print("🧪 INICIANDO SUITE DE TESTS FORENSES")
    print("=" * 50)
    
    # Crear test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir test classes
    suite.addTests(loader.loadTestsFromTestCase(TestForensicQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestForensicConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestForensicIntegration))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generar reporte final
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ TODOS LOS TESTS FORENSES EXITOSOS")
        print(f"📊 Tests ejecutados: {result.testsRun}")
        print(f"⏱️ Tiempo: {result.testsRun}s (aprox)")
        return True
    else:
        print(f"❌ TESTS FALLIDOS: {len(result.failures)}")
        print(f"🚫 ERRORES: {len(result.errors)}")
        print(f"📊 Total ejecutados: {result.testsRun}")
        
        # Mostrar primer fallo para diagnóstico rápido
        if result.failures:
            print(f"\n🔍 PRIMER FALLO:")
            print(f"Test: {result.failures[0][0]}")
            print(f"Error: {result.failures[0][1].split('AssertionError:')[-1].strip()}")
        
        return False


if __name__ == "__main__":
    success = run_forensic_test_suite()
    sys.exit(0 if success else 1)