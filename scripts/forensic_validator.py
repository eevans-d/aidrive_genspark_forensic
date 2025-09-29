#!/usr/bin/env python3
"""
HERRAMIENTA FORENSE AVANZADA - VALIDADOR DE METODOLOGÍA
Valida que los análisis forenses cumplan con los principios fundamentales
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class ForensicValidator:
    """Validador de metodología forense para análisis técnicos"""
    
    def __init__(self, repository_path: str):
        self.repo_path = Path(repository_path)
        self.forensic_principles = {
            'archivo_linea_citations': r'`[^`]+:\d+(-\d+)?`',
            'risk_markers': r'(RIESGO|RISK)\s+(CRÍTICO|ALTO|MEDIO|HIGH|MEDIUM|CRITICAL)',
            'no_evidenciado': r'NO\s+EVIDENCIADO',
            'passive_mode': r'(modificar|cambiar|editar|modify|change|edit)',
            'verification_commands': r'```bash\n.*?```'
        }
        
    def validate_forensic_analysis(self, analysis_file: Path) -> Dict[str, any]:
        """Valida un archivo de análisis forense contra los principios"""
        
        if not analysis_file.exists():
            return {'error': f'Archivo no encontrado: {analysis_file}'}
            
        content = analysis_file.read_text(encoding='utf-8')
        
        results = {
            'file': str(analysis_file),
            'total_lines': len(content.split('\n')),
            'citations_count': 0,
            'risk_markers_count': 0,
            'no_evidenciado_count': 0,
            'passive_violations': [],
            'verification_commands': 0,
            'compliance_score': 0.0,
            'recommendations': []
        }
        
        # Validar citas archivo:línea
        citations = re.findall(self.forensic_principles['archivo_linea_citations'], content)
        results['citations_count'] = len(citations)
        
        # Validar marcadores de riesgo
        risk_markers = re.findall(self.forensic_principles['risk_markers'], content, re.IGNORECASE)
        results['risk_markers_count'] = len(risk_markers)
        
        # Validar marcadores "NO EVIDENCIADO"
        no_evidenciado = re.findall(self.forensic_principles['no_evidenciado'], content, re.IGNORECASE)
        results['no_evidenciado_count'] = len(no_evidenciado)
        
        # Detectar violaciones de modo pasivo
        passive_violations = re.findall(self.forensic_principles['passive_mode'], content, re.IGNORECASE)
        results['passive_violations'] = passive_violations[:5]  # Limitar a 5 ejemplos
        
        # Contar comandos de verificación
        verification_commands = re.findall(self.forensic_principles['verification_commands'], content, re.DOTALL)
        results['verification_commands'] = len(verification_commands)
        
        # Calcular score de compliance
        results['compliance_score'] = self._calculate_compliance_score(results)
        
        # Generar recomendaciones
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _calculate_compliance_score(self, results: Dict) -> float:
        """Calcula score de compliance forense (0-100)"""
        
        score = 0.0
        
        # Citas archivo:línea (40% del score)
        if results['citations_count'] > 0:
            score += min(40, results['citations_count'] * 2)
        
        # Marcadores de riesgo (20% del score)
        if results['risk_markers_count'] > 0:
            score += min(20, results['risk_markers_count'] * 4)
        
        # NO EVIDENCIADO (15% del score)
        if results['no_evidenciado_count'] > 0:
            score += min(15, results['no_evidenciado_count'] * 3)
        
        # Comandos de verificación (15% del score)
        if results['verification_commands'] > 0:
            score += min(15, results['verification_commands'] * 3)
        
        # Penalización por violaciones de modo pasivo (hasta -30)
        passive_penalty = min(30, len(results['passive_violations']) * 10)
        score -= passive_penalty
        
        # Bonus por integridad metodológica (10%)
        if (results['citations_count'] >= 10 and 
            results['risk_markers_count'] >= 3 and 
            len(results['passive_violations']) == 0):
            score += 10
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Genera recomendaciones para mejorar compliance forense"""
        
        recommendations = []
        
        if results['citations_count'] < 10:
            recommendations.append(
                f"❌ CRÍTICO: Solo {results['citations_count']} citas archivo:línea detectadas. "
                "Mínimo requerido: 10+ para análisis forense válido."
            )
        
        if results['risk_markers_count'] < 3:
            recommendations.append(
                f"⚠️ ALTO: Solo {results['risk_markers_count']} marcadores de riesgo. "
                "Análisis forense debe identificar mínimo 3 riesgos con severidad."
            )
        
        if results['no_evidenciado_count'] == 0:
            recommendations.append(
                "⚠️ MEDIO: Sin marcadores 'NO EVIDENCIADO'. "
                "Análisis forense debe reconocer explícitamente limitaciones."
            )
        
        if len(results['passive_violations']) > 0:
            recommendations.append(
                f"❌ CRÍTICO: {len(results['passive_violations'])} violaciones de modo pasivo detectadas. "
                "El análisis NO debe sugerir modificaciones de código."
            )
        
        if results['verification_commands'] < 5:
            recommendations.append(
                f"⚠️ MEDIO: Solo {results['verification_commands']} comandos de verificación. "
                "Incluir mínimo 5 comandos ejecutables para validación."
            )
        
        if results['compliance_score'] >= 90:
            recommendations.append("✅ EXCELENTE: Metodología forense aplicada correctamente.")
        elif results['compliance_score'] >= 70:
            recommendations.append("✅ BUENO: Metodología forense en gran parte correcta.")
        else:
            recommendations.append("❌ DEFICIENTE: Metodología forense requiere mejoras significativas.")
            
        return recommendations
    
    def validate_all_forensic_files(self) -> Dict[str, any]:
        """Valida todos los archivos de análisis forense en el repositorio"""
        
        forensic_files = list(self.repo_path.glob("**/EJEMPLO_ANALISIS_FORENSE_*.md"))
        forensic_files.extend(self.repo_path.glob("**/ANALISIS_FORENSE_*.md"))
        
        if not forensic_files:
            return {
                'error': 'No se encontraron archivos de análisis forense',
                'searched_patterns': ['**/EJEMPLO_ANALISIS_FORENSE_*.md', '**/ANALISIS_FORENSE_*.md']
            }
        
        results = {
            'total_files': len(forensic_files),
            'files_analyzed': [],
            'overall_compliance': 0.0,
            'summary': {
                'excellent': 0,  # >= 90
                'good': 0,       # >= 70
                'poor': 0        # < 70
            }
        }
        
        total_score = 0.0
        
        for file_path in forensic_files:
            file_result = self.validate_forensic_analysis(file_path)
            results['files_analyzed'].append(file_result)
            
            score = file_result.get('compliance_score', 0.0)
            total_score += score
            
            if score >= 90:
                results['summary']['excellent'] += 1
            elif score >= 70:
                results['summary']['good'] += 1
            else:
                results['summary']['poor'] += 1
        
        results['overall_compliance'] = total_score / len(forensic_files) if forensic_files else 0.0
        
        return results
    
    def generate_compliance_report(self, output_file: Optional[Path] = None) -> str:
        """Genera reporte completo de compliance forense"""
        
        validation_results = self.validate_all_forensic_files()
        
        if 'error' in validation_results:
            return f"Error: {validation_results['error']}"
        
        report = []
        report.append("# 🔬 REPORTE DE COMPLIANCE FORENSE")
        report.append("## Validación de Metodología de Análisis Forense")
        report.append("")
        report.append(f"**📅 Fecha**: {os.popen('date').read().strip()}")
        report.append(f"**📍 Repositorio**: {self.repo_path.name}")
        report.append(f"**📊 Archivos analizados**: {validation_results['total_files']}")
        report.append(f"**🎯 Compliance promedio**: {validation_results['overall_compliance']:.1f}%")
        report.append("")
        
        # Resumen ejecutivo
        report.append("## 📈 RESUMEN EJECUTIVO")
        report.append("")
        summary = validation_results['summary']
        report.append(f"- ✅ **Excelente** (≥90%): {summary['excellent']} archivos")
        report.append(f"- ⚠️ **Bueno** (≥70%): {summary['good']} archivos")
        report.append(f"- ❌ **Deficiente** (<70%): {summary['poor']} archivos")
        report.append("")
        
        # Análisis detallado por archivo
        report.append("## 🔍 ANÁLISIS DETALLADO")
        report.append("")
        
        for file_result in validation_results['files_analyzed']:
            file_name = Path(file_result['file']).name
            score = file_result['compliance_score']
            
            if score >= 90:
                status = "✅ EXCELENTE"
            elif score >= 70:
                status = "⚠️ BUENO"
            else:
                status = "❌ DEFICIENTE"
            
            report.append(f"### {file_name} - {status} ({score:.1f}%)")
            report.append("")
            report.append(f"- **Citas archivo:línea**: {file_result['citations_count']}")
            report.append(f"- **Marcadores de riesgo**: {file_result['risk_markers_count']}")
            report.append(f"- **NO EVIDENCIADO**: {file_result['no_evidenciado_count']}")
            report.append(f"- **Comandos verificación**: {file_result['verification_commands']}")
            report.append(f"- **Violaciones modo pasivo**: {len(file_result['passive_violations'])}")
            report.append("")
            
            if file_result['recommendations']:
                report.append("**Recomendaciones:**")
                for rec in file_result['recommendations'][:3]:  # Top 3 recomendaciones
                    report.append(f"- {rec}")
                report.append("")
        
        # Recomendaciones generales
        report.append("## 🎯 RECOMENDACIONES GENERALES")
        report.append("")
        
        if validation_results['overall_compliance'] >= 90:
            report.append("✅ La metodología forense se está aplicando correctamente en todo el repositorio.")
        elif validation_results['overall_compliance'] >= 70:
            report.append("⚠️ La metodología forense se aplica bien pero requiere mejoras menores.")
        else:
            report.append("❌ La metodología forense requiere mejoras significativas.")
            report.append("")
            report.append("### Acciones prioritarias:")
            report.append("1. Incrementar citas `archivo:línea` en análisis técnicos")
            report.append("2. Identificar y clasificar más riesgos con severidad")
            report.append("3. Eliminar sugerencias de modificación de código")
            report.append("4. Añadir más comandos de verificación ejecutables")
        
        report_text = "\n".join(report)
        
        if output_file:
            output_file.write_text(report_text, encoding='utf-8')
            
        return report_text


def main():
    parser = argparse.ArgumentParser(description='Validador de metodología forense')
    parser.add_argument('repository', help='Ruta al repositorio a analizar')
    parser.add_argument('--output', '-o', help='Archivo de salida para el reporte')
    parser.add_argument('--file', '-f', help='Analizar archivo específico')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.repository):
        print(f"Error: Repositorio no encontrado: {args.repository}")
        sys.exit(1)
    
    validator = ForensicValidator(args.repository)
    
    if args.file:
        # Analizar archivo específico
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = Path(args.repository) / file_path
            
        result = validator.validate_forensic_analysis(file_path)
        
        print(f"📄 Archivo: {result['file']}")
        print(f"🎯 Compliance Score: {result['compliance_score']:.1f}%")
        print(f"📝 Citas archivo:línea: {result['citations_count']}")
        print(f"⚠️ Marcadores de riesgo: {result['risk_markers_count']}")
        print(f"❌ Violaciones modo pasivo: {len(result['passive_violations'])}")
        print("")
        print("🔍 Recomendaciones:")
        for rec in result['recommendations']:
            print(f"  {rec}")
    else:
        # Generar reporte completo
        output_file = None
        if args.output:
            output_file = Path(args.output)
        
        report = validator.generate_compliance_report(output_file)
        print(report)
        
        if output_file:
            print(f"\n📄 Reporte guardado en: {output_file}")


if __name__ == "__main__":
    main()