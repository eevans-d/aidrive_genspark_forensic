# 🧪 FRAMEWORK DE TESTING PARA PROMPTS FORENSES
## Sistema de Validación Automática de Metodología Forense

**🎯 OBJETIVO**: Proporcionar un sistema completo de testing para validar que los prompts forenses generen resultados consistentes y de alta calidad.

---

## 📋 COMPONENTES DEL FRAMEWORK

### 1. 🔬 Test de Validación Forense
- **Verificación de citas**: Cada dato técnico debe incluir `archivo:línea`
- **Detección de riesgos**: Mínimo 3 riesgos identificados con severidad
- **Modo pasivo**: 0 sugerencias de modificación de código
- **Comandos ejecutables**: Mínimo 5 comandos de verificación

### 2. 🎯 Test de Adaptación Contextual
- **Stack específico**: Configuraciones adaptadas al stack detectado
- **NO genérico**: Sin plantillas genéricas aplicables a cualquier proyecto
- **Evidencia empírica**: Inferencias basadas solo en código real

### 3. 📊 Test de Integridad Metodológica
- **Estructura completa**: 4 secciones principales presentes
- **Terminología consistente**: Uso consistente de términos forenses
- **Calidad de análisis**: Score mínimo de 80% en métricas de calidad

---

## 🛠️ HERRAMIENTAS DE TESTING

### Test Suite Automatizado
```python
#!/usr/bin/env python3
"""
SUITE DE TESTS PARA PROMPTS FORENSES
Valida automáticamente la calidad de análisis forenses generados
"""

import unittest
import re
from pathlib import Path
from typing import Dict, List, Any


class ForensicPromptTestSuite(unittest.TestCase):
    """Suite de tests para validación de prompts forenses"""
    
    def setUp(self):
        """Setup para tests"""
        self.repo_path = Path(".")
        self.forensic_files = list(self.repo_path.glob("**/EJEMPLO_ANALISIS_FORENSE_*.md"))
    
    def test_forensic_citations_present(self):
        """Test: Verificar presencia de citas archivo:línea"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar citas formato archivo:línea
                citations = re.findall(r'`[^`]+:\d+(-\d+)?`', content)
                
                self.assertGreaterEqual(
                    len(citations), 10,
                    f"Insuficientes citas archivo:línea en {forensic_file.name}. "
                    f"Encontradas: {len(citations)}, Requeridas: ≥10"
                )
    
    def test_risk_markers_present(self):
        """Test: Verificar marcadores de riesgo con severidad"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar marcadores de riesgo
                risk_markers = re.findall(
                    r'(RIESGO|RISK)\s+(CRÍTICO|ALTO|MEDIO|HIGH|MEDIUM|CRITICAL)', 
                    content, re.IGNORECASE
                )
                
                self.assertGreaterEqual(
                    len(risk_markers), 3,
                    f"Insuficientes marcadores de riesgo en {forensic_file.name}. "
                    f"Encontrados: {len(risk_markers)}, Requeridos: ≥3"
                )
    
    def test_no_code_modification_suggestions(self):
        """Test: Verificar ausencia de sugerencias de modificación"""
        
        violation_patterns = [
            r'\bmodifica\b',
            r'\bcambia\b',
            r'\bedita\b',
            r'\bmodify\b',
            r'\bchange\b',
            r'\bedit\b'
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
                    f"Violaciones de modo pasivo en {forensic_file.name}: {violations}"
                )
    
    def test_verification_commands_present(self):
        """Test: Verificar comandos de verificación ejecutables"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Buscar bloques de comandos
                command_blocks = re.findall(r'```bash.*?```', content, re.DOTALL)
                
                self.assertGreaterEqual(
                    len(command_blocks), 1,
                    f"Sin comandos de verificación en {forensic_file.name}"
                )
                
                # Verificar que hay comandos específicos
                total_commands = 0
                for block in command_blocks:
                    commands = [line.strip() for line in block.split('\n') 
                               if line.strip() and not line.startswith('#') 
                               and not line.startswith('```')]
                    total_commands += len(commands)
                
                self.assertGreaterEqual(
                    total_commands, 5,
                    f"Insuficientes comandos en {forensic_file.name}. "
                    f"Encontrados: {total_commands}, Requeridos: ≥5"
                )
    
    def test_mandatory_sections_present(self):
        """Test: Verificar presencia de secciones obligatorias"""
        
        mandatory_sections = [
            "STACK TECNOLÓGICO",
            "ARQUITECTURA DEL SISTEMA",
            "REQUISITOS DE DESPLIEGUE",
            "CONFIGURACIÓN ACTUAL"
        ]
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                for section in mandatory_sections:
                    self.assertIn(
                        section, content,
                        f"Sección obligatoria '{section}' faltante en {forensic_file.name}"
                    )
    
    def test_no_evidenciado_markers_present(self):
        """Test: Verificar marcadores 'NO EVIDENCIADO'"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                no_evidenciado = re.findall(r'NO\s+EVIDENCIADO', content, re.IGNORECASE)
                
                # Al menos debe haber algunos elementos no evidenciados (honestidad forense)
                self.assertGreaterEqual(
                    len(no_evidenciado), 1,
                    f"Sin marcadores 'NO EVIDENCIADO' en {forensic_file.name}. "
                    "Análisis forense debe reconocer limitaciones."
                )
    
    def test_project_specific_content(self):
        """Test: Verificar contenido específico del proyecto"""
        
        for forensic_file in self.forensic_files:
            with self.subTest(file=forensic_file.name):
                content = forensic_file.read_text(encoding='utf-8')
                
                # Debe mencionar tecnologías específicas (no solo genéricas)
                specific_indicators = [
                    'fastapi', 'django', 'flask', 'express', 'react',
                    'requirements.txt', 'package.json', 'main.py', 'app.py'
                ]
                
                found_indicators = 0
                for indicator in specific_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators += 1
                
                self.assertGreaterEqual(
                    found_indicators, 2,
                    f"Contenido muy genérico en {forensic_file.name}. "
                    f"Indicadores específicos encontrados: {found_indicators}/≥2"
                )


def run_forensic_tests():
    """Ejecuta la suite completa de tests forenses"""
    
    # Configurar el test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ForensicPromptTestSuite)
    
    # Ejecutar tests con output detallado
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generar reporte de resultados
    if result.wasSuccessful():
        print("\n✅ TODOS LOS TESTS FORENSES PASARON")
        print(f"Tests ejecutados: {result.testsRun}")
        return True
    else:
        print(f"\n❌ TESTS FALLIDOS: {len(result.failures)}")
        print(f"ERRORES: {len(result.errors)}")
        print(f"Tests ejecutados: {result.testsRun}")
        
        # Mostrar detalles de fallos
        for test, error in result.failures:
            print(f"\n🔴 FALLO: {test}")
            print(f"Error: {error}")
        
        return False


if __name__ == "__main__":
    success = run_forensic_tests()
    exit(0 if success else 1)
```

---

## 📊 MÉTRICAS DE CALIDAD

### Scoring System
- **Citas archivo:línea**: 40% del score (≥10 citas = 100%)
- **Marcadores de riesgo**: 25% del score (≥3 riesgos = 100%)
- **Comandos verificación**: 20% del score (≥5 comandos = 100%)
- **Estructura metodológica**: 15% del score (4 secciones completas = 100%)

### Thresholds de Calidad
- **EXCELENTE**: ≥90% - Metodología forense aplicada perfectamente
- **BUENO**: 70-89% - Metodología mayormente correcta
- **DEFICIENTE**: <70% - Requiere mejoras significativas

---

## 🔄 INTEGRACIÓN CONTINUA

### Pre-commit Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit
# Validar análisis forenses antes de commit

echo "🔬 Validando metodología forense..."

python3 scripts/forensic_validator.py . --quiet
if [ $? -ne 0 ]; then
    echo "❌ Validación forense falló. Commit rechazado."
    exit 1
fi

echo "✅ Validación forense exitosa"
```

### GitHub Actions
```yaml
name: Forensic Quality Check
on: [push, pull_request]

jobs:
  forensic-validation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    - name: Run Forensic Tests
      run: python3 scripts/forensic_validator.py .
    - name: Cross-project Consistency
      run: python3 scripts/cross_project_consistency_validator.py .
```

---

## 🎯 CASOS DE TEST ESPECÍFICOS

### Test Case 1: Inventario Retail
```python
def test_inventario_retail_forensic():
    """Test específico para análisis forense de inventario retail"""
    
    file_path = Path("EJEMPLO_ANALISIS_FORENSE_INVENTARIO_RETAIL.md")
    content = file_path.read_text()
    
    # Debe detectar FastAPI
    assert "fastapi" in content.lower()
    assert "requirements.txt:" in content
    
    # Debe identificar riesgos específicos
    assert "RIESGO ALTO" in content or "RIESGO CRÍTICO" in content
    
    # Debe incluir comandos específicos para el stack
    assert "grep -r" in content
    assert "find ." in content
```

### Test Case 2: Business Intelligence
```python
def test_bi_orchestrator_forensic():
    """Test específico para análisis BI Orchestrator"""
    
    file_path = Path("EJEMPLO_ANALISIS_FORENSE_BI_ORCHESTRATOR.md")
    content = file_path.read_text()
    
    # Debe reconocer limitaciones
    assert "NO EVIDENCIADO" in content
    
    # Debe identificar estructura modular
    assert "src/" in content
    assert "web_automatico" in content
```

---

## 🚀 AUTOMATIZACIÓN AVANZADA

### Continuous Monitoring
```python
def monitor_forensic_quality():
    """Monitor continuo de calidad forense"""
    
    validator = ForensicValidator(".")
    results = validator.validate_all_forensic_files()
    
    # Alertar si calidad baja
    if results['overall_compliance'] < 80:
        send_alert(f"Calidad forense bajó a {results['overall_compliance']:.1f}%")
    
    # Generar trending report
    generate_quality_trend_report(results)
```

### Auto-improvement Suggestions
```python
def suggest_improvements(analysis_file: Path):
    """Sugerir mejoras automáticas para análisis forense"""
    
    suggestions = []
    content = analysis_file.read_text()
    
    citations = re.findall(r'`[^`]+:\d+(-\d+)?`', content)
    if len(citations) < 10:
        suggestions.append("Añadir más citas archivo:línea específicas")
    
    if "NO EVIDENCIADO" not in content:
        suggestions.append("Reconocer limitaciones con 'NO EVIDENCIADO'")
    
    return suggestions
```

---

## 📈 REPORTING Y ANALYTICS

### Quality Dashboard
- **Trending de calidad** por proyecto y tiempo
- **Heatmap de compliance** por tipo de stack
- **Alertas automáticas** cuando calidad baja
- **Benchmarking** contra mejores prácticas

### Automated Reporting
- **Reporte semanal** de calidad forense
- **Alertas de regresión** en calidad
- **Sugerencias de mejora** personalizadas
- **Tracking de progreso** en implementación

---

**🎯 RESULTADO**: Framework completo de testing que garantiza calidad consistente y alta en todos los análisis forenses, con automatización completa y mejora continua.