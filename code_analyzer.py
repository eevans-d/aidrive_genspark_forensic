#!/usr/bin/env python3
"""
MEGA ANÁLISIS - FASE 1: Análisis de Código Profundo
Sistema Mini Market - Code Quality Assessment

Analizador estático personalizado para TypeScript/JavaScript
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

class CodeAnalyzer:
    def __init__(self, workspace_path="/workspace"):
        self.workspace = workspace_path
        self.results = {
            "overview": {},
            "complexity": {},
            "duplicates": {},
            "security": {},
            "quality": {},
            "patterns": {}
        }
        
    def analyze_file(self, file_path):
        """Analiza un archivo específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "path": file_path,
                "lines": len(content.split('\n')),
                "non_empty_lines": len([line for line in content.split('\n') if line.strip()]),
                "functions": self.count_functions(content),
                "complexity": self.calculate_complexity(content),
                "duplicates": self.find_duplicates(content),
                "security_issues": self.check_security(content),
                "code_smells": self.detect_code_smells(content),
                "imports": self.analyze_imports(content)
            }
        except Exception as e:
            return {"error": str(e), "path": file_path}
    
    def count_functions(self, content):
        """Cuenta funciones/métodos en el código"""
        patterns = [
            r'function\s+\w+',  # function declarations
            r'const\s+\w+\s*=\s*\(',  # arrow functions
            r'async\s+function\s+\w+',  # async functions
            r'\w+:\s*\(',  # object methods
            r'export\s+function\s+\w+',  # exported functions
        ]
        
        total = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            total += len(matches)
        
        return total
    
    def calculate_complexity(self, content):
        """Calcula complejidad ciclomática aproximada"""
        # Contar estructuras de control que aumentan complejidad
        complexity_keywords = [
            r'\bif\b', r'\belse\b', r'\belseif\b', r'\belse\s+if\b',
            r'\bwhile\b', r'\bfor\b', r'\bswitch\b', r'\bcase\b',
            r'\bcatch\b', r'\btry\b', r'\&&', r'\|\|',
            r'\?', r'\bdo\b'
        ]
        
        complexity = 1  # Base complexity
        for keyword in complexity_keywords:
            matches = re.findall(keyword, content, re.IGNORECASE)
            complexity += len(matches)
        
        # Penalizar funciones muy largas
        lines = content.split('\n')
        if len(lines) > 100:
            complexity += (len(lines) - 100) // 20
        
        return complexity
    
    def find_duplicates(self, content):
        """Busca código duplicado"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        duplicates = []
        
        # Buscar líneas idénticas (excluyendo imports y comentarios)
        line_counts = Counter()
        for i, line in enumerate(lines):
            if (not line.startswith('import') and 
                not line.startswith('//') and 
                not line.startswith('*') and
                len(line) > 10):
                line_counts[line] += 1
        
        for line, count in line_counts.items():
            if count > 1:
                duplicates.append({"line": line, "occurrences": count})
        
        return duplicates
    
    def check_security(self, content):
        """Detecta problemas de seguridad potenciales"""
        security_patterns = [
            (r'eval\s*\(', "Uso de eval() - Riesgo de inyección de código"),
            (r'innerHTML\s*=', "Uso de innerHTML - Riesgo XSS"),
            (r'\.exec\s*\(', "Uso de exec() - Riesgo de inyección"),
            (r'password.*=.*["\'][^"\']*["\']', "Password hardcodeado"),
            (r'api[_-]?key.*=.*["\'][^"\']*["\']', "API key hardcodeada"),
            (r'secret.*=.*["\'][^"\']*["\']', "Secret hardcodeado"),
            (r'console\.log\s*\(', "Console.log en producción"),
            (r'alert\s*\(', "Alert() usage - UX issue"),
            (r'document\.write\s*\(', "document.write usage - Security risk"),
            (r'setTimeout\s*\(\s*["\']', "setTimeout con string - Code injection risk")
        ]
        
        issues = []
        for pattern, message in security_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues.append({
                    "pattern": pattern,
                    "message": message,
                    "occurrences": len(matches),
                    "matches": matches[:3]  # Solo primeras 3 coincidencias
                })
        
        return issues
    
    def detect_code_smells(self, content):
        """Detecta code smells y anti-patterns"""
        smells = []
        lines = content.split('\n')
        
        # Función muy larga
        if len(lines) > 200:
            smells.append("Archivo muy largo (>200 líneas)")
        
        # Demasiados parámetros en funciones
        function_params = re.findall(r'function\s+\w+\s*\(([^)]*)\)', content)
        for params in function_params:
            param_count = len([p.strip() for p in params.split(',') if p.strip()])
            if param_count > 5:
                smells.append(f"Función con muchos parámetros ({param_count})")
        
        # TODO comments
        todo_count = len(re.findall(r'//.*TODO|//.*FIXME|//.*HACK', content, re.IGNORECASE))
        if todo_count > 0:
            smells.append(f"TODOs/FIXMEs pendientes ({todo_count})")
        
        # Magic numbers
        magic_numbers = re.findall(r'\b\d{4,}\b', content)
        if len(magic_numbers) > 3:
            smells.append(f"Magic numbers detectados ({len(magic_numbers)})")
        
        # Nested callbacks (callback hell)
        nested_callbacks = content.count('function(') + content.count('=>')
        if nested_callbacks > 10:
            smells.append("Posible callback hell")
        
        return smells
    
    def analyze_imports(self, content):
        """Analiza imports y dependencias"""
        imports = re.findall(r'import.*from\s+["\']([^"\']+)["\']', content)
        external_deps = [imp for imp in imports if not imp.startswith('.')]
        internal_deps = [imp for imp in imports if imp.startswith('.')]
        
        return {
            "total_imports": len(imports),
            "external_dependencies": external_deps,
            "internal_dependencies": internal_deps,
            "unused_imports": []  # Requeriría análisis más profundo
        }

def main():
    """Función principal"""
    analyzer = CodeAnalyzer()
    
    # Encontrar archivos TypeScript core
    core_files = [
        "/workspace/supabase/functions/scraper-maxiconsumo/index.ts",
        "/workspace/supabase/functions/api-proveedor/index.ts", 
        "/workspace/supabase/functions/api-minimarket/index.ts",
        "/workspace/supabase/functions/alertas-stock/index.ts",
        "/workspace/supabase/functions/notificaciones-tareas/index.ts",
        "/workspace/minimarket-system/src/App.tsx",
        "/workspace/minimarket-system/src/pages/Dashboard.tsx",
        "/workspace/minimarket-system/src/pages/Deposito.tsx"
    ]
    
    results = {}
    total_lines = 0
    total_functions = 0
    total_complexity = 0
    all_security_issues = []
    all_code_smells = []
    
    print("🔍 MEGA ANÁLISIS - FASE 1: Análisis de Código Profundo")
    print("=" * 60)
    
    for file_path in core_files:
        if os.path.exists(file_path):
            print(f"\n📁 Analizando: {file_path}")
            analysis = analyzer.analyze_file(file_path)
            
            if "error" not in analysis:
                results[file_path] = analysis
                total_lines += analysis["lines"]
                total_functions += analysis["functions"]
                total_complexity += analysis["complexity"]
                all_security_issues.extend(analysis["security_issues"])
                all_code_smells.extend(analysis["code_smells"])
                
                print(f"  ✓ Líneas: {analysis['lines']}")
                print(f"  ✓ Funciones: {analysis['functions']}")
                print(f"  ✓ Complejidad: {analysis['complexity']}")
                print(f"  ✓ Issues de seguridad: {len(analysis['security_issues'])}")
                print(f"  ✓ Code smells: {len(analysis['code_smells'])}")
            else:
                print(f"  ❌ Error: {analysis['error']}")
        else:
            print(f"  ⚠️  Archivo no encontrado: {file_path}")
    
    # Resumen general
    print("\n" + "=" * 60)
    print("📊 RESUMEN GENERAL")
    print("=" * 60)
    print(f"📄 Archivos analizados: {len(results)}")
    print(f"📝 Total líneas de código: {total_lines:,}")
    print(f"🔧 Total funciones: {total_functions}")
    print(f"🌀 Complejidad total: {total_complexity}")
    print(f"🛡️  Issues de seguridad: {len(all_security_issues)}")
    print(f"👃 Code smells: {len(all_code_smells)}")
    
    # Calcular score de calidad
    quality_score = calculate_quality_score(total_lines, total_functions, total_complexity, 
                                          len(all_security_issues), len(all_code_smells))
    print(f"\n🎯 SCORE DE CALIDAD: {quality_score}/10")
    
    # Generar reporte detallado
    return {
        "summary": {
            "files_analyzed": len(results),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_complexity": total_complexity,
            "security_issues_count": len(all_security_issues),
            "code_smells_count": len(all_code_smells),
            "quality_score": quality_score
        },
        "detailed_results": results,
        "security_issues": all_security_issues,
        "code_smells": all_code_smells
    }

def calculate_quality_score(lines, functions, complexity, security_issues, code_smells):
    """Calcula un score de calidad de código del 1-10"""
    score = 10.0
    
    # Penalizar por complejidad alta
    avg_complexity = complexity / max(functions, 1)
    if avg_complexity > 20:
        score -= 2.0
    elif avg_complexity > 15:
        score -= 1.0
    elif avg_complexity > 10:
        score -= 0.5
    
    # Penalizar por issues de seguridad
    score -= min(security_issues * 0.5, 3.0)
    
    # Penalizar por code smells
    score -= min(code_smells * 0.2, 2.0)
    
    # Penalizar archivos muy largos
    avg_lines_per_file = lines / max(len([f for f in [1]]), 1)  # Aproximación
    if avg_lines_per_file > 500:
        score -= 1.0
    
    return max(round(score, 1), 0.0)

if __name__ == "__main__":
    results = main()
    
    # Guardar resultados en JSON
    with open("/workspace/docs/code_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: /workspace/docs/code_analysis_results.json")