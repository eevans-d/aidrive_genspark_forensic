#!/usr/bin/env python3
"""
VALIDADOR DE CONSISTENCIA CROSS-PROYECTO
Valida que la metodología forense se aplique consistentemente across múltiples proyectos
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectAnalysis:
    """Análisis de un proyecto individual"""
    name: str
    path: Path
    has_forensic_analysis: bool
    has_requirements: bool
    has_main_files: bool
    stack_type: str
    forensic_quality_score: float
    identified_gaps: List[str]


class CrossProjectConsistencyValidator:
    """Validador de consistencia metodológica across proyectos"""
    
    def __init__(self, repository_path: str):
        self.repo_path = Path(repository_path)
        self.projects = []
        self.consistency_report = {
            'timestamp': datetime.now().isoformat(),
            'repository': str(self.repo_path),
            'projects_analyzed': 0,
            'consistency_score': 0.0,
            'gaps_identified': [],
            'recommendations': []
        }
    
    def discover_projects(self) -> List[Path]:
        """Descubre proyectos en el repositorio"""
        
        project_indicators = [
            'requirements.txt',
            'package.json',
            'main.py',
            'app.py',
            'Dockerfile'
        ]
        
        potential_projects = []
        
        # Buscar directorios que contengan indicadores de proyecto
        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Verificar si contiene indicadores
                has_indicators = False
                for indicator in project_indicators:
                    if list(item.rglob(indicator)):
                        has_indicators = True
                        break
                
                if has_indicators:
                    potential_projects.append(item)
        
        # Filtrar proyectos principales (evitar subdirectorios pequeños)
        main_projects = []
        for project in potential_projects:
            # Verificar que tenga suficiente código
            python_files = list(project.rglob("*.py"))
            js_files = list(project.rglob("*.js"))
            
            if len(python_files) >= 3 or len(js_files) >= 3:
                main_projects.append(project)
        
        return main_projects
    
    def analyze_project(self, project_path: Path) -> ProjectAnalysis:
        """Analiza un proyecto individual"""
        
        analysis = ProjectAnalysis(
            name=project_path.name,
            path=project_path,
            has_forensic_analysis=False,
            has_requirements=False,
            has_main_files=False,
            stack_type="unknown",
            forensic_quality_score=0.0,
            identified_gaps=[]
        )
        
        # Verificar análisis forense existente
        forensic_files = list(self.repo_path.glob(f"*FORENSE*{project_path.name.upper()}*.md"))
        forensic_files.extend(self.repo_path.glob(f"*forensic*{project_path.name}*.md"))
        
        if forensic_files:
            analysis.has_forensic_analysis = True
            # Evaluar calidad del análisis forense
            analysis.forensic_quality_score = self._evaluate_forensic_quality(forensic_files[0])
        else:
            analysis.identified_gaps.append("Sin análisis forense disponible")
        
        # Verificar archivos de dependencias
        req_files = list(project_path.rglob("requirements*.txt"))
        package_files = list(project_path.rglob("package.json"))
        
        if req_files or package_files:
            analysis.has_requirements = True
        else:
            analysis.identified_gaps.append("Sin archivo de dependencias")
        
        # Verificar archivos principales
        main_files = list(project_path.rglob("main.py"))
        main_files.extend(project_path.rglob("app.py"))
        main_files.extend(project_path.rglob("server.py"))
        main_files.extend(project_path.rglob("index.js"))
        
        if main_files:
            analysis.has_main_files = True
        else:
            analysis.identified_gaps.append("Sin punto de entrada claro")
        
        # Determinar tipo de stack
        analysis.stack_type = self._determine_stack_type(project_path)
        
        return analysis
    
    def _evaluate_forensic_quality(self, forensic_file: Path) -> float:
        """Evalúa la calidad de un análisis forense"""
        
        try:
            content = forensic_file.read_text(encoding='utf-8')
            
            score = 0.0
            
            # Citas archivo:línea (30 puntos)
            import re
            citations = re.findall(r'`[^`]+:\d+(-\d+)?`', content)
            score += min(30, len(citations) * 1.5)
            
            # Marcadores de riesgo (25 puntos)
            risk_markers = re.findall(r'(RIESGO|RISK)\s+(CRÍTICO|ALTO|MEDIO)', content, re.IGNORECASE)
            score += min(25, len(risk_markers) * 5)
            
            # NO EVIDENCIADO (20 puntos)
            no_evidenciado = re.findall(r'NO\s+EVIDENCIADO', content, re.IGNORECASE)
            score += min(20, len(no_evidenciado) * 4)
            
            # Comandos de verificación (15 puntos)
            commands = re.findall(r'```bash.*?```', content, re.DOTALL)
            score += min(15, len(commands) * 3)
            
            # Estructura metodológica (10 puntos)
            if "STACK TECNOLÓGICO" in content and "ARQUITECTURA" in content:
                score += 10
            
            return min(100.0, score)
            
        except Exception:
            return 0.0
    
    def _determine_stack_type(self, project_path: Path) -> str:
        """Determina el tipo de stack del proyecto"""
        
        # Python
        if list(project_path.rglob("requirements*.txt")) or list(project_path.rglob("*.py")):
            # Determinar framework Python
            try:
                req_files = list(project_path.rglob("requirements*.txt"))
                if req_files:
                    content = req_files[0].read_text().lower()
                    if 'fastapi' in content:
                        return "python_fastapi"
                    elif 'django' in content:
                        return "python_django"
                    elif 'flask' in content:
                        return "python_flask"
                    else:
                        return "python_generic"
            except:
                pass
            return "python_generic"
        
        # JavaScript/Node.js
        elif list(project_path.rglob("package.json")):
            try:
                package_file = list(project_path.rglob("package.json"))[0]
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    
                    if 'express' in deps:
                        return "node_express"
                    elif 'react' in deps:
                        return "node_react"
                    else:
                        return "node_generic"
            except:
                return "node_generic"
        
        # Docker/Kubernetes
        elif list(project_path.rglob("Dockerfile")) or list(project_path.rglob("k8s/")):
            return "containerized"
        
        return "unknown"
    
    def validate_cross_project_consistency(self) -> Dict[str, Any]:
        """Valida consistencia cross-proyecto"""
        
        print("🔍 Descubriendo proyectos en el repositorio...")
        project_paths = self.discover_projects()
        
        print(f"📊 Encontrados {len(project_paths)} proyectos principales")
        
        # Analizar cada proyecto
        for project_path in project_paths:
            print(f"  🔬 Analizando: {project_path.name}")
            analysis = self.analyze_project(project_path)
            self.projects.append(analysis)
        
        self.consistency_report['projects_analyzed'] = len(self.projects)
        
        # Calcular métricas de consistencia
        self._calculate_consistency_metrics()
        
        # Identificar gaps globales
        self._identify_global_gaps()
        
        # Generar recomendaciones
        self._generate_consistency_recommendations()
        
        return self.consistency_report
    
    def _calculate_consistency_metrics(self):
        """Calcula métricas de consistencia"""
        
        if not self.projects:
            return
        
        # Porcentaje con análisis forense
        with_forensic = sum(1 for p in self.projects if p.has_forensic_analysis)
        forensic_coverage = (with_forensic / len(self.projects)) * 100
        
        # Score promedio de calidad forense
        total_score = sum(p.forensic_quality_score for p in self.projects)
        avg_quality = total_score / len(self.projects)
        
        # Distribución por stack
        stack_distribution = {}
        for project in self.projects:
            stack_distribution[project.stack_type] = stack_distribution.get(project.stack_type, 0) + 1
        
        # Score general de consistencia
        consistency_score = (forensic_coverage * 0.4) + (avg_quality * 0.6)
        
        self.consistency_report.update({
            'forensic_coverage_percentage': forensic_coverage,
            'average_forensic_quality': avg_quality,
            'consistency_score': consistency_score,
            'stack_distribution': stack_distribution
        })
    
    def _identify_global_gaps(self):
        """Identifica gaps globales en el repositorio"""
        
        gaps = []
        
        # Proyectos sin análisis forense
        without_forensic = [p for p in self.projects if not p.has_forensic_analysis]
        if without_forensic:
            gaps.append({
                'type': 'missing_forensic_analysis',
                'severity': 'HIGH',
                'description': f"{len(without_forensic)} proyectos sin análisis forense",
                'affected_projects': [p.name for p in without_forensic]
            })
        
        # Proyectos con análisis forense de baja calidad
        low_quality = [p for p in self.projects if p.has_forensic_analysis and p.forensic_quality_score < 70]
        if low_quality:
            gaps.append({
                'type': 'low_quality_forensic',
                'severity': 'MEDIUM',
                'description': f"{len(low_quality)} proyectos con análisis forense de baja calidad",
                'affected_projects': [p.name for p in low_quality]
            })
        
        # Inconsistencia de metodología por stack
        stack_consistency = self._check_stack_consistency()
        if stack_consistency:
            gaps.extend(stack_consistency)
        
        self.consistency_report['gaps_identified'] = gaps
    
    def _check_stack_consistency(self) -> List[Dict[str, Any]]:
        """Verifica consistencia de metodología por tipo de stack"""
        
        gaps = []
        
        # Agrupar por stack type
        by_stack = {}
        for project in self.projects:
            if project.stack_type not in by_stack:
                by_stack[project.stack_type] = []
            by_stack[project.stack_type].append(project)
        
        # Verificar consistencia dentro de cada stack
        for stack_type, projects in by_stack.items():
            if len(projects) < 2:
                continue  # Skip stacks con solo un proyecto
            
            # Verificar que todos tengan análisis forense
            without_analysis = [p for p in projects if not p.has_forensic_analysis]
            if without_analysis:
                gaps.append({
                    'type': 'stack_inconsistency',
                    'severity': 'MEDIUM',
                    'description': f"Stack {stack_type}: metodología inconsistente",
                    'affected_projects': [p.name for p in without_analysis],
                    'stack_type': stack_type
                })
            
            # Verificar calidad similar
            qualities = [p.forensic_quality_score for p in projects if p.has_forensic_analysis]
            if qualities and (max(qualities) - min(qualities)) > 30:
                gaps.append({
                    'type': 'quality_variance',
                    'severity': 'LOW',
                    'description': f"Stack {stack_type}: gran variación en calidad de análisis",
                    'quality_range': f"{min(qualities):.1f} - {max(qualities):.1f}",
                    'stack_type': stack_type
                })
        
        return gaps
    
    def _generate_consistency_recommendations(self):
        """Genera recomendaciones para mejorar consistencia"""
        
        recommendations = []
        
        # Basado en coverage forense
        coverage = self.consistency_report.get('forensic_coverage_percentage', 0)
        if coverage < 50:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Implementar análisis forense en proyectos faltantes',
                'description': f"Solo {coverage:.1f}% de proyectos tienen análisis forense",
                'estimated_effort': f"{len([p for p in self.projects if not p.has_forensic_analysis])} análisis por crear"
            })
        
        # Basado en calidad promedio
        avg_quality = self.consistency_report.get('average_forensic_quality', 0)
        if avg_quality < 70:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Mejorar calidad de análisis forense existentes',
                'description': f"Calidad promedio: {avg_quality:.1f}% (objetivo: >80%)",
                'estimated_effort': "Refactorización de análisis existentes"
            })
        
        # Basado en gaps específicos
        gaps = self.consistency_report.get('gaps_identified', [])
        high_severity_gaps = [g for g in gaps if g['severity'] == 'HIGH']
        if high_severity_gaps:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Resolver gaps críticos identificados',
                'description': f"{len(high_severity_gaps)} issues de alta severidad",
                'estimated_effort': "Análisis y corrección inmediata"
            })
        
        # Recomendación para estandarización
        if len(set(p.stack_type for p in self.projects)) > 3:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Estandarizar templates por tipo de stack',
                'description': "Múltiples stacks detectados, crear templates específicos",
                'estimated_effort': "Desarrollo de templates especializados"
            })
        
        self.consistency_report['recommendations'] = recommendations
    
    def generate_consistency_report(self, output_file: Optional[Path] = None) -> str:
        """Genera reporte de consistencia cross-proyecto"""
        
        report = []
        report.append("# 🔄 REPORTE DE CONSISTENCIA CROSS-PROYECTO")
        report.append("## Validación de Metodología Forense Across Proyectos")
        report.append("")
        report.append(f"**📅 Fecha**: {self.consistency_report['timestamp']}")
        report.append(f"**📍 Repositorio**: {self.consistency_report['repository']}")
        report.append(f"**📊 Proyectos analizados**: {self.consistency_report['projects_analyzed']}")
        report.append(f"**🎯 Score de consistencia**: {self.consistency_report['consistency_score']:.1f}%")
        report.append("")
        
        # Resumen ejecutivo
        report.append("## 📈 RESUMEN EJECUTIVO")
        report.append("")
        coverage = self.consistency_report.get('forensic_coverage_percentage', 0)
        quality = self.consistency_report.get('average_forensic_quality', 0)
        
        report.append(f"- **Coverage forense**: {coverage:.1f}% de proyectos")
        report.append(f"- **Calidad promedio**: {quality:.1f}%")
        report.append(f"- **Gaps identificados**: {len(self.consistency_report['gaps_identified'])}")
        report.append(f"- **Recomendaciones**: {len(self.consistency_report['recommendations'])}")
        report.append("")
        
        # Distribución por stack
        report.append("## 🏗️ DISTRIBUCIÓN POR STACK")
        report.append("")
        stack_dist = self.consistency_report.get('stack_distribution', {})
        for stack, count in stack_dist.items():
            report.append(f"- **{stack}**: {count} proyecto(s)")
        report.append("")
        
        # Análisis por proyecto
        report.append("## 📊 ANÁLISIS POR PROYECTO")
        report.append("")
        
        for project in self.projects:
            status = "✅" if project.has_forensic_analysis else "❌"
            quality_str = f"{project.forensic_quality_score:.1f}%" if project.has_forensic_analysis else "N/A"
            
            report.append(f"### {status} {project.name}")
            report.append(f"- **Stack**: {project.stack_type}")
            report.append(f"- **Análisis forense**: {'Sí' if project.has_forensic_analysis else 'No'}")
            report.append(f"- **Calidad**: {quality_str}")
            
            if project.identified_gaps:
                report.append("- **Gaps identificados**:")
                for gap in project.identified_gaps:
                    report.append(f"  - {gap}")
            report.append("")
        
        # Gaps globales
        report.append("## 🚨 GAPS GLOBALES IDENTIFICADOS")
        report.append("")
        
        gaps = self.consistency_report.get('gaps_identified', [])
        if not gaps:
            report.append("✅ No se identificaron gaps críticos.")
        else:
            for gap in gaps:
                severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(gap['severity'], "⚪")
                report.append(f"### {severity_icon} {gap['type'].upper()}")
                report.append(f"**Severidad**: {gap['severity']}")
                report.append(f"**Descripción**: {gap['description']}")
                
                if 'affected_projects' in gap:
                    report.append(f"**Proyectos afectados**: {', '.join(gap['affected_projects'])}")
                report.append("")
        
        # Recomendaciones
        report.append("## 🎯 PLAN DE ACCIÓN RECOMENDADO")
        report.append("")
        
        recommendations = self.consistency_report.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            priority_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(rec['priority'], "⚪")
            report.append(f"### {i}. {priority_icon} {rec['action']}")
            report.append(f"**Prioridad**: {rec['priority']}")
            report.append(f"**Descripción**: {rec['description']}")
            report.append(f"**Esfuerzo estimado**: {rec['estimated_effort']}")
            report.append("")
        
        # Próximos pasos
        report.append("## 🚀 PRÓXIMOS PASOS")
        report.append("")
        
        if coverage < 100:
            missing_count = len([p for p in self.projects if not p.has_forensic_analysis])
            report.append(f"1. **Completar análisis forense**: {missing_count} proyectos pendientes")
        
        if quality < 80:
            report.append("2. **Mejorar calidad**: Refactorizar análisis existentes")
        
        report.append("3. **Automatización**: Implementar validación continua")
        report.append("4. **Templates**: Crear templates específicos por stack")
        
        report_text = "\n".join(report)
        
        if output_file:
            output_file.write_text(report_text, encoding='utf-8')
        
        return report_text


def main():
    parser = argparse.ArgumentParser(description='Validador de consistencia cross-proyecto')
    parser.add_argument('repository', help='Ruta al repositorio a analizar')
    parser.add_argument('--output', '-o', help='Archivo de salida para el reporte')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.repository):
        print(f"❌ Error: Repositorio no encontrado: {args.repository}")
        return 1
    
    validator = CrossProjectConsistencyValidator(args.repository)
    
    print("🔄 Iniciando validación de consistencia cross-proyecto...")
    print()
    
    results = validator.validate_cross_project_consistency()
    
    print()
    print("📊 RESULTADOS:")
    print(f"  - Proyectos analizados: {results['projects_analyzed']}")
    print(f"  - Coverage forense: {results.get('forensic_coverage_percentage', 0):.1f}%")
    print(f"  - Calidad promedio: {results.get('average_forensic_quality', 0):.1f}%")
    print(f"  - Score consistencia: {results['consistency_score']:.1f}%")
    print()
    
    # Generar reporte
    output_file = None
    if args.output:
        output_file = Path(args.output)
    
    report = validator.generate_consistency_report(output_file)
    
    if not args.output:
        print(report)
    else:
        print(f"📄 Reporte guardado en: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())