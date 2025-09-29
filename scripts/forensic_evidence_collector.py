#!/usr/bin/env python3
"""
RECOLECTOR FORENSE AUTOMÁTICO DE EVIDENCIA
Automatiza la recolección de evidencia técnica para análisis forense
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime


class ForensicEvidenceCollector:
    """Recolector automático de evidencia para análisis forense"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.evidence = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'stack_detection': {},
            'architecture_analysis': {},
            'deployment_requirements': {},
            'configuration_analysis': {},
            'risk_assessment': {},
            'verification_commands': []
        }
    
    def collect_stack_evidence(self) -> Dict[str, Any]:
        """Recolecta evidencia del stack tecnológico"""
        
        stack_evidence = {
            'languages': self._detect_languages(),
            'frameworks': self._detect_frameworks(),
            'databases': self._detect_databases(),
            'external_apis': self._detect_external_apis(),
            'ai_libraries': self._detect_ai_libraries(),
            'dependencies': self._collect_dependencies()
        }
        
        self.evidence['stack_detection'] = stack_evidence
        return stack_evidence
    
    def _detect_languages(self) -> Dict[str, Any]:
        """Detecta lenguajes de programación y versiones"""
        
        languages = {}
        
        # Python
        python_files = list(self.project_path.rglob("*.py"))
        if python_files:
            languages['python'] = {
                'detected': True,
                'files_count': len(python_files),
                'evidence_files': [str(f.relative_to(self.project_path)) for f in python_files[:5]]
            }
            
            # Buscar especificación de versión
            runtime_files = list(self.project_path.rglob("runtime.txt"))
            if runtime_files:
                try:
                    content = runtime_files[0].read_text()
                    languages['python']['version_spec'] = content.strip()
                    languages['python']['version_file'] = str(runtime_files[0].relative_to(self.project_path))
                except:
                    pass
        
        # JavaScript/Node.js
        js_files = list(self.project_path.rglob("*.js"))
        package_json = list(self.project_path.rglob("package.json"))
        if js_files or package_json:
            languages['javascript'] = {
                'detected': True,
                'js_files_count': len(js_files),
                'package_json_found': len(package_json) > 0
            }
            
            if package_json:
                try:
                    with open(package_json[0], 'r') as f:
                        pkg_data = json.load(f)
                        if 'engines' in pkg_data:
                            languages['javascript']['node_version'] = pkg_data['engines']
                except:
                    pass
        
        # Otros lenguajes
        for ext, lang in [('.go', 'go'), ('.rs', 'rust'), ('.java', 'java'), ('.cpp', 'cpp')]:
            files = list(self.project_path.rglob(f"*{ext}"))
            if files:
                languages[lang] = {
                    'detected': True,
                    'files_count': len(files)
                }
        
        return languages
    
    def _detect_frameworks(self) -> Dict[str, Any]:
        """Detecta frameworks web y sus versiones"""
        
        frameworks = {}
        
        # Buscar en archivos de dependencias
        req_files = list(self.project_path.rglob("requirements*.txt"))
        for req_file in req_files:
            try:
                content = req_file.read_text()
                
                # FastAPI
                if 'fastapi' in content.lower():
                    version_match = self._extract_version(content, 'fastapi')
                    frameworks['fastapi'] = {
                        'detected': True,
                        'version': version_match,
                        'evidence_file': str(req_file.relative_to(self.project_path))
                    }
                
                # Django
                if 'django' in content.lower():
                    version_match = self._extract_version(content, 'django')
                    frameworks['django'] = {
                        'detected': True,
                        'version': version_match,
                        'evidence_file': str(req_file.relative_to(self.project_path))
                    }
                
                # Flask
                if 'flask' in content.lower():
                    version_match = self._extract_version(content, 'flask')
                    frameworks['flask'] = {
                        'detected': True,
                        'version': version_match,
                        'evidence_file': str(req_file.relative_to(self.project_path))
                    }
                    
            except Exception as e:
                frameworks['_parsing_errors'] = frameworks.get('_parsing_errors', [])
                frameworks['_parsing_errors'].append(str(e))
        
        # Buscar en package.json
        package_files = list(self.project_path.rglob("package.json"))
        for pkg_file in package_files:
            try:
                with open(pkg_file, 'r') as f:
                    pkg_data = json.load(f)
                    
                deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                
                # Express
                if 'express' in deps:
                    frameworks['express'] = {
                        'detected': True,
                        'version': deps['express'],
                        'evidence_file': str(pkg_file.relative_to(self.project_path))
                    }
                
                # React
                if 'react' in deps:
                    frameworks['react'] = {
                        'detected': True,
                        'version': deps['react'],
                        'evidence_file': str(pkg_file.relative_to(self.project_path))
                    }
                    
            except Exception as e:
                frameworks['_parsing_errors'] = frameworks.get('_parsing_errors', [])
                frameworks['_parsing_errors'].append(str(e))
        
        return frameworks
    
    def _detect_databases(self) -> Dict[str, Any]:
        """Detecta bases de datos y configuraciones"""
        
        databases = {}
        
        # Buscar en archivos de código
        python_files = list(self.project_path.rglob("*.py"))
        
        db_indicators = {
            'postgresql': ['postgresql', 'psycopg2', 'asyncpg'],
            'mysql': ['mysql', 'pymysql', 'mysql-connector'],
            'sqlite': ['sqlite3', 'sqlite'],
            'mongodb': ['pymongo', 'mongodb', 'mongoengine'],
            'redis': ['redis', 'aioredis']
        }
        
        for py_file in python_files[:20]:  # Limitar a 20 archivos para performance
            try:
                content = py_file.read_text().lower()
                
                for db_type, indicators in db_indicators.items():
                    for indicator in indicators:
                        if indicator in content:
                            if db_type not in databases:
                                databases[db_type] = {
                                    'detected': True,
                                    'evidence_files': [],
                                    'indicators': []
                                }
                            
                            databases[db_type]['evidence_files'].append(
                                str(py_file.relative_to(self.project_path))
                            )
                            databases[db_type]['indicators'].append(indicator)
                            break
                            
            except Exception:
                continue
        
        # Buscar archivos de configuración de BD
        config_files = ['database.py', 'db_config.py', 'models.py']
        for config_file in config_files:
            found_files = list(self.project_path.rglob(config_file))
            if found_files:
                databases['_config_files'] = databases.get('_config_files', [])
                databases['_config_files'].extend([
                    str(f.relative_to(self.project_path)) for f in found_files
                ])
        
        return databases
    
    def _detect_external_apis(self) -> Dict[str, Any]:
        """Detecta integraciones con APIs externas"""
        
        apis = {}
        
        # Patrones de APIs conocidas
        api_patterns = {
            'openai': ['openai', 'gpt-', 'chatgpt'],
            'stripe': ['stripe', 'sk_live_', 'pk_live_'],
            'aws': ['boto3', 'aws-sdk', 's3', 'lambda'],
            'google': ['google-cloud', 'googleapis', 'gmail'],
            'telegram': ['telegram', 'bot_token'],
            'afip': ['afip', 'cuit', 'factura']
        }
        
        python_files = list(self.project_path.rglob("*.py"))
        env_files = list(self.project_path.rglob(".env*"))
        
        # Buscar en archivos Python
        for py_file in python_files[:15]:  # Limitar para performance
            try:
                content = py_file.read_text().lower()
                
                for api_name, patterns in api_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            if api_name not in apis:
                                apis[api_name] = {
                                    'detected': True,
                                    'evidence_files': [],
                                    'patterns_found': []
                                }
                            
                            apis[api_name]['evidence_files'].append(
                                str(py_file.relative_to(self.project_path))
                            )
                            apis[api_name]['patterns_found'].append(pattern)
                            
            except Exception:
                continue
        
        # Buscar en archivos de configuración
        for env_file in env_files:
            try:
                content = env_file.read_text().lower()
                
                for api_name, patterns in api_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            if api_name not in apis:
                                apis[api_name] = {
                                    'detected': True,
                                    'config_files': [],
                                    'patterns_found': []
                                }
                            
                            apis[api_name]['config_files'] = apis[api_name].get('config_files', [])
                            apis[api_name]['config_files'].append(
                                str(env_file.relative_to(self.project_path))
                            )
                            
            except Exception:
                continue
        
        return apis
    
    def _detect_ai_libraries(self) -> Dict[str, Any]:
        """Detecta librerías de IA y ML"""
        
        ai_libs = {}
        
        ai_indicators = {
            'machine_learning': ['scikit-learn', 'sklearn', 'pandas', 'numpy'],
            'deep_learning': ['tensorflow', 'torch', 'pytorch', 'keras'],
            'nlp': ['transformers', 'spacy', 'nltk', 'textblob'],
            'computer_vision': ['opencv', 'pillow', 'imageio'],
            'llm_apis': ['openai', 'anthropic', 'cohere']
        }
        
        # Buscar en requirements.txt
        req_files = list(self.project_path.rglob("requirements*.txt"))
        for req_file in req_files:
            try:
                content = req_file.read_text().lower()
                
                for category, indicators in ai_indicators.items():
                    for indicator in indicators:
                        if indicator in content:
                            if category not in ai_libs:
                                ai_libs[category] = {
                                    'detected': True,
                                    'libraries': [],
                                    'evidence_file': str(req_file.relative_to(self.project_path))
                                }
                            
                            version = self._extract_version(content, indicator)
                            ai_libs[category]['libraries'].append({
                                'name': indicator,
                                'version': version
                            })
                            
            except Exception:
                continue
        
        return ai_libs
    
    def _collect_dependencies(self) -> Dict[str, Any]:
        """Recolecta todas las dependencias del proyecto"""
        
        dependencies = {
            'python': [],
            'javascript': [],
            'docker': [],
            'system': []
        }
        
        # Python dependencies
        req_files = list(self.project_path.rglob("requirements*.txt"))
        for req_file in req_files:
            try:
                content = req_file.read_text()
                deps = [line.strip() for line in content.split('\n') 
                       if line.strip() and not line.startswith('#')]
                dependencies['python'].extend(deps)
            except Exception:
                continue
        
        # JavaScript dependencies
        package_files = list(self.project_path.rglob("package.json"))
        for pkg_file in package_files:
            try:
                with open(pkg_file, 'r') as f:
                    pkg_data = json.load(f)
                    
                deps = pkg_data.get('dependencies', {})
                dev_deps = pkg_data.get('devDependencies', {})
                
                dependencies['javascript'].extend([
                    f"{name}=={version}" for name, version in deps.items()
                ])
                dependencies['javascript'].extend([
                    f"{name}=={version} (dev)" for name, version in dev_deps.items()
                ])
                
            except Exception:
                continue
        
        # Docker
        docker_files = list(self.project_path.rglob("Dockerfile*"))
        dependencies['docker'] = [str(f.relative_to(self.project_path)) for f in docker_files]
        
        return dependencies
    
    def collect_architecture_evidence(self) -> Dict[str, Any]:
        """Recolecta evidencia arquitectónica"""
        
        arch_evidence = {
            'directory_structure': self._analyze_directory_structure(),
            'entry_points': self._find_entry_points(),
            'patterns': self._detect_architectural_patterns(),
            'integrations': self._analyze_integrations()
        }
        
        self.evidence['architecture_analysis'] = arch_evidence
        return arch_evidence
    
    def _analyze_directory_structure(self) -> Dict[str, Any]:
        """Analiza la estructura de directorios"""
        
        structure = {
            'top_level_dirs': [],
            'executable_dirs': [],
            'config_dirs': [],
            'test_dirs': []
        }
        
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure['top_level_dirs'].append(item.name)
                
                # Detectar directorios ejecutables
                if any(item.rglob("main.py")) or any(item.rglob("app.py")):
                    structure['executable_dirs'].append(item.name)
                
                # Detectar directorios de configuración
                if any(word in item.name.lower() for word in ['config', 'settings', 'env']):
                    structure['config_dirs'].append(item.name)
                
                # Detectar directorios de tests
                if any(word in item.name.lower() for word in ['test', 'tests', 'spec']):
                    structure['test_dirs'].append(item.name)
        
        return structure
    
    def _find_entry_points(self) -> List[Dict[str, Any]]:
        """Encuentra puntos de entrada del sistema"""
        
        entry_points = []
        
        # Buscar archivos principales
        main_patterns = ['main.py', 'app.py', 'server.py', '__main__.py', 'manage.py']
        
        for pattern in main_patterns:
            files = list(self.project_path.rglob(pattern))
            for file_path in files:
                entry_points.append({
                    'file': str(file_path.relative_to(self.project_path)),
                    'type': 'python_main',
                    'directory': str(file_path.parent.relative_to(self.project_path))
                })
        
        # Buscar archivos JavaScript principales
        js_patterns = ['index.js', 'server.js', 'app.js']
        for pattern in js_patterns:
            files = list(self.project_path.rglob(pattern))
            for file_path in files:
                entry_points.append({
                    'file': str(file_path.relative_to(self.project_path)),
                    'type': 'javascript_main',
                    'directory': str(file_path.parent.relative_to(self.project_path))
                })
        
        return entry_points
    
    def _detect_architectural_patterns(self) -> List[str]:
        """Detecta patrones arquitectónicos"""
        
        patterns = []
        
        # Microservicios - múltiples directorios con main.py
        main_files = list(self.project_path.rglob("main.py"))
        if len(main_files) > 1:
            patterns.append("microservices")
        
        # Docker/Containerización
        if list(self.project_path.rglob("Dockerfile")) or list(self.project_path.rglob("docker-compose*.yml")):
            patterns.append("containerized")
        
        # Kubernetes
        if list(self.project_path.rglob("*.yaml")) and any("k8s" in str(f) for f in self.project_path.rglob("*.yaml")):
            patterns.append("kubernetes")
        
        # API REST
        if any("fastapi" in str(f).lower() or "flask" in str(f).lower() for f in self.project_path.rglob("*.py")):
            patterns.append("rest_api")
        
        # Event-driven
        if any("event" in str(f).lower() or "queue" in str(f).lower() for f in self.project_path.rglob("*.py")):
            patterns.append("event_driven")
        
        return patterns
    
    def _analyze_integrations(self) -> Dict[str, Any]:
        """Analiza integraciones del sistema"""
        
        integrations = {
            'databases': len(self.evidence.get('stack_detection', {}).get('databases', {})),
            'external_apis': len(self.evidence.get('stack_detection', {}).get('external_apis', {})),
            'ai_services': len(self.evidence.get('stack_detection', {}).get('ai_libraries', {}))
        }
        
        return integrations
    
    def _extract_version(self, content: str, package_name: str) -> Optional[str]:
        """Extrae versión de un paquete del contenido"""
        
        import re
        
        patterns = [
            rf'{package_name}==([^\s\n]+)',
            rf'{package_name}>=([^\s\n]+)',
            rf'{package_name}~=([^\s\n]+)',
            rf'"{package_name}":\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def generate_verification_commands(self) -> List[str]:
        """Genera comandos de verificación basados en evidencia recolectada"""
        
        commands = []
        
        # Comandos básicos de estructura
        commands.append("find . -name '*.py' | head -10")
        commands.append("find . -name 'requirements*.txt'")
        commands.append("find . -name 'package.json'")
        
        # Comandos específicos basados en stack detectado
        stack = self.evidence.get('stack_detection', {})
        
        if stack.get('frameworks', {}).get('fastapi'):
            commands.append("grep -r 'FastAPI' . --include='*.py' | wc -l")
        
        if stack.get('databases', {}).get('postgresql'):
            commands.append("grep -r 'postgresql\\|psycopg2' . --include='*.py' | head -3")
        
        if stack.get('external_apis', {}).get('openai'):
            commands.append("grep -r 'openai\\|gpt-' . --include='*.py' | head -3")
        
        # Comandos de configuración
        commands.append("find . -name '.env*' -o -name 'config.py'")
        commands.append("grep -r 'os.getenv\\|environ' . --include='*.py' | wc -l")
        
        # Comandos de arquitectura
        commands.append("find . -name 'main.py' -o -name 'app.py' | wc -l")
        commands.append("find . -name 'Dockerfile' -o -name 'docker-compose*.yml'")
        
        self.evidence['verification_commands'] = commands
        return commands
    
    def collect_all_evidence(self) -> Dict[str, Any]:
        """Recolecta toda la evidencia forense del proyecto"""
        
        print("🔍 Recolectando evidencia del stack tecnológico...")
        self.collect_stack_evidence()
        
        print("🏗️ Analizando arquitectura del sistema...")
        self.collect_architecture_evidence()
        
        print("⚙️ Generando comandos de verificación...")
        self.generate_verification_commands()
        
        print("📊 Calculando métricas del proyecto...")
        self._calculate_project_metrics()
        
        return self.evidence
    
    def _calculate_project_metrics(self):
        """Calcula métricas del proyecto"""
        
        metrics = {
            'total_python_files': len(list(self.project_path.rglob("*.py"))),
            'total_js_files': len(list(self.project_path.rglob("*.js"))),
            'total_config_files': len(list(self.project_path.rglob(".env*"))) + len(list(self.project_path.rglob("config.py"))),
            'total_dockerfile': len(list(self.project_path.rglob("Dockerfile*"))),
            'has_tests': len(list(self.project_path.rglob("test*.py"))) > 0
        }
        
        self.evidence['project_metrics'] = metrics
    
    def save_evidence(self, output_file: Path):
        """Guarda la evidencia recolectada en archivo JSON"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.evidence, f, indent=2, ensure_ascii=False)
    
    def generate_forensic_analysis_template(self, output_file: Path):
        """Genera template de análisis forense basado en evidencia recolectada"""
        
        template = []
        template.append("# ANÁLISIS FORENSE AUTOMÁTICO - [NOMBRE_PROYECTO]")
        template.append("## Resultado de evidencia recolectada automáticamente")
        template.append("")
        template.append(f"**📅 Fecha de recolección**: {self.evidence['timestamp']}")
        template.append(f"**📍 Proyecto**: `{self.evidence['project_path']}`")
        template.append("**🔬 Principio**: Evidencia citada (`archivo:línea`) para cada dato técnico")
        template.append("")
        template.append("---")
        template.append("")
        
        # Stack tecnológico
        template.append("## 1. STACK TECNOLÓGICO — DETECCIÓN EMPÍRICA")
        template.append("")
        
        stack = self.evidence.get('stack_detection', {})
        
        # Lenguajes
        languages = stack.get('languages', {})
        if languages:
            template.append("### 🐍 Lenguajes Detectados")
            for lang, data in languages.items():
                if data.get('detected'):
                    template.append(f"- **{lang.title()}**: {data.get('files_count', 0)} archivos")
                    if 'version_spec' in data:
                        template.append(f"  - Versión: `{data['version_spec']}` en `{data['version_file']}`")
            template.append("")
        
        # Frameworks
        frameworks = stack.get('frameworks', {})
        if frameworks:
            template.append("### 🚀 Frameworks Detectados")
            for fw, data in frameworks.items():
                if fw.startswith('_'):
                    continue
                if data.get('detected'):
                    template.append(f"- **{fw.title()}**: {data.get('version', 'NO EVIDENCIADO')}")
                    template.append(f"  - Evidencia: `{data['evidence_file']}`")
            template.append("")
        
        # Comandos de verificación
        template.append("## 📋 COMANDOS DE VERIFICACIÓN EJECUTABLES")
        template.append("")
        template.append("```bash")
        for cmd in self.evidence.get('verification_commands', []):
            template.append(f"# {cmd}")
        template.append("```")
        template.append("")
        
        # Guardar template
        template_text = "\n".join(template)
        output_file.write_text(template_text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Recolector forense automático de evidencia')
    parser.add_argument('project_path', help='Ruta al proyecto a analizar')
    parser.add_argument('--output', '-o', help='Archivo de salida JSON', default='forensic_evidence.json')
    parser.add_argument('--template', '-t', help='Generar template de análisis forense')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"❌ Error: Proyecto no encontrado: {args.project_path}")
        return 1
    
    collector = ForensicEvidenceCollector(args.project_path)
    
    print(f"🔬 Iniciando recolección forense de evidencia...")
    print(f"📍 Proyecto: {args.project_path}")
    print()
    
    evidence = collector.collect_all_evidence()
    
    # Guardar evidencia
    output_path = Path(args.output)
    collector.save_evidence(output_path)
    print(f"💾 Evidencia guardada en: {output_path}")
    
    # Generar template si se solicita
    if args.template:
        template_path = Path(args.template)
        collector.generate_forensic_analysis_template(template_path)
        print(f"📄 Template generado en: {template_path}")
    
    # Resumen
    stack = evidence.get('stack_detection', {})
    arch = evidence.get('architecture_analysis', {})
    metrics = evidence.get('project_metrics', {})
    
    print()
    print("📊 RESUMEN DE EVIDENCIA RECOLECTADA:")
    print(f"  - Lenguajes detectados: {len(stack.get('languages', {}))}")
    print(f"  - Frameworks detectados: {len(stack.get('frameworks', {}))}")
    print(f"  - APIs externas: {len(stack.get('external_apis', {}))}")
    print(f"  - Puntos de entrada: {len(arch.get('entry_points', []))}")
    print(f"  - Archivos Python: {metrics.get('total_python_files', 0)}")
    print(f"  - Comandos de verificación: {len(evidence.get('verification_commands', []))}")
    
    return 0


if __name__ == "__main__":
    exit(main())