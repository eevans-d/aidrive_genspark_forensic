# 🚀 GUÍA DE IMPLEMENTACIÓN - PROMPTS DEFINITIVOS OPTIMIZADOS
## Metodología Práctica para Maximizar el Valor del Agente Autónomo

**🎯 OBJETIVO**: Guía paso a paso para implementar la estrategia híbrida consolidada usando GitHub Copilot Pro en modo agente autónomo con sesiones de 90-130 minutos.

---

## 📋 **PREPARACIÓN INICIAL**

### 1. **Configuración del Entorno**
```bash
# Clonar y preparar repositorio
git clone https://github.com/eevans-d/aidrive_genspark_forensic.git
cd aidrive_genspark_forensic

# Verificar estructura de submódulos
ls -la inventario-retail/ business-intelligence-orchestrator-v3.1/ sistema_deposito_semana1/

# Instalar herramientas de monitoreo
chmod +x scripts/*.sh
```

### 2. **Validación Pre-Ejecución**
```bash
# Verificar estado inicial
./scripts/validate_success_criteria.sh --prompt=1
./scripts/validate_success_criteria.sh --prompt=2  
./scripts/validate_success_criteria.sh --prompt=3

# Generar baseline inicial
./scripts/generate_executive_report.sh --all-prompts
```

---

## 🎯 **EJECUCIÓN DE PROMPTS**

### **SEMANA 1: PROMPT 1 - Consolidación Arquitectónica**

#### **Pre-Ejecución (5 min)**
1. **Abrir GitHub Copilot Pro** en el repositorio
2. **Verificar contexto completo** del repositorio cargado
3. **Copiar instrucciones globales** desde `PROMPTS_GITHUB_COPILOT_PRO_DEFINITIVOS.md`

#### **Durante Ejecución (90-120 min)**
```bash
# Iniciar monitoreo
./scripts/monitor_progress.sh --prompt=1 --phase=current &

# En GitHub Copilot Pro:
# 1. Pegar INSTRUCCIONES GLOBALES
# 2. Pegar PROMPT DEFINITIVO 1 completo
# 3. Confirmar entendimiento de restricciones
# 4. Ejecutar automáticamente
```

#### **Validación Continua**
```bash
# Cada 30 minutos durante ejecución
./scripts/validate_success_criteria.sh --prompt=1 --verbose

# Al finalizar
./scripts/generate_executive_report.sh --all-prompts
```

#### **Criterios de Finalización**
- ✅ Score ≥ 4/5 en validación
- ✅ Documentación en `docs/diagnostico/baseline_consolidado.md`
- ✅ Configuración SQLite centralizada
- ✅ Estructura `app/shared/core/` implementada
- ✅ Métricas `/metrics` funcionales

---

### **SEMANA 2: PROMPT 2 - Security Hardening**

#### **Pre-Ejecución (5 min)**
```bash
# Verificar completitud del Prompt 1
./scripts/validate_success_criteria.sh --prompt=1

# Si Score < 4/5, completar Prompt 1 antes de continuar
```

#### **Durante Ejecución (90-110 min)**
```bash
# Iniciar monitoreo específico
./scripts/monitor_progress.sh --prompt=2 --phase=current &

# En GitHub Copilot Pro:
# 1. Contexto: resultados del Prompt 1
# 2. Pegar INSTRUCCIONES GLOBALES
# 3. Pegar PROMPT DEFINITIVO 2 completo
# 4. Ejecutar auditoría y hardening
```

#### **Validación de Seguridad**
```bash
# Validar durante ejecución
./scripts/validate_success_criteria.sh --prompt=2

# Verificar pipelines de seguridad
if [ -f .github/workflows/security_pipeline.yml ]; then
    echo "✅ Security pipeline creado"
fi
```

#### **Criterios de Finalización**
- ✅ Auditoría de dependencias completa
- ✅ Security headers implementados
- ✅ Sistema de auditoría funcional
- ✅ Pipeline CI/CD de seguridad
- ✅ 0 vulnerabilidades críticas

---

### **SEMANA 3: PROMPT 3 - Testing y Observabilidad**

#### **Pre-Ejecución (5 min)**
```bash
# Verificar completitud de Prompts anteriores
./scripts/validate_success_criteria.sh --prompt=1
./scripts/validate_success_criteria.sh --prompt=2

# Solo proceder si ambos tienen Score ≥ 4/5
```

#### **Durante Ejecución (100-130 min)**
```bash
# Monitoreo avanzado
./scripts/monitor_progress.sh --prompt=3 --phase=current &

# En GitHub Copilot Pro:
# 1. Contexto: resultados de Prompts 1 y 2
# 2. Pegar INSTRUCCIONES GLOBALES
# 3. Pegar PROMPT DEFINITIVO 3 completo
# 4. Implementar suite completa de testing
```

#### **Validación de Testing**
```bash
# Ejecutar suite de tests
python -m pytest tests/ --cov=. --cov-report=html

# Verificar cobertura
coverage report --show-missing

# Validar criterios
./scripts/validate_success_criteria.sh --prompt=3
```

---

## 📊 **MONITOREO Y VALIDACIÓN**

### **Dashboard de Progreso en Tiempo Real**
```bash
# Monitoreo continuo (ejecutar en terminal separado)
watch -n 30 './scripts/generate_executive_report.sh --all-prompts && cat docs/progress/executive_summary_*.md | tail -20'
```

### **Puntos de Control Obligatorios**
1. **Cada 30 min**: Validar criterios de éxito actuales
2. **Cada fase**: Actualizar documentación de progreso
3. **Cada prompt**: Generar reporte ejecutivo completo
4. **Al finalizar**: Validación integral y métricas ROI

### **Escalación de Problemas**
```bash
# Si Score < 3/5 por >60 minutos
echo "🚨 ALERTA: Prompt no está progresando adecuadamente"
echo "Acciones:"
echo "1. Revisar logs de GitHub Copilot Pro"
echo "2. Simplificar prompt actual"
echo "3. Continuar con fases siguientes"
echo "4. Crear DRAFT PR para revisión"
```

---

## 🎯 **CRITERIOS DE ÉXITO GLOBAL**

### **Métricas Cuantitativas Mínimas**
| Métrica | Prompt 1 | Prompt 2 | Prompt 3 | Global |
|---------|-----------|-----------|-----------|--------|
| Score Validación | ≥ 4/5 | ≥ 4/5 | ≥ 4/5 | 12/15 |
| Cobertura Tests | N/A | N/A | ≥ 80% | ≥ 80% |
| Vulnerabilidades | N/A | 0 críticas | N/A | 0 críticas |
| Documentación | 100% | 100% | 100% | 100% |

### **Validación Final Automatizada**
```bash
# Script de validación completa
./scripts/validate_all_prompts.sh
```

### **ROI Esperado Mínimo**
- **Desarrollo**: -25% tiempo debugging
- **Seguridad**: +200% visibilidad amenazas
- **Operaciones**: -40% tiempo troubleshooting
- **Calidad**: +150% confianza en releases

---

## 🔧 **TROUBLESHOOTING COMÚN**

### **Prompt No Progresa (Score Estancado)**
```bash
# Diagnóstico rápido
echo "1. ¿GitHub Copilot Pro tiene contexto completo del repo?"
echo "2. ¿Las instrucciones globales fueron aplicadas?"
echo "3. ¿Hay restricciones técnicas bloqueantes?"

# Solución: Simplificar y dividir en sub-prompts
```

### **Validación Falla Consistentemente**
```bash
# Revisar estructura esperada vs actual
find . -name "*.py" -path "*/app/shared/core/*" | head -5
find . -name "*security*" | head -5  
find . -name "test_*.py" | wc -l
```

### **Performance del Agente Degrada**
```bash
# Limpiar contexto y reiniciar
echo "Cerrar y reabrir GitHub Copilot Pro"
echo "Recargar repositorio completo"
echo "Verificar memoria/CPU disponible"
```

---

## 📈 **OPTIMIZACIÓN CONTINUA**

### **Post-Implementación (Día +7)**
```bash
# Métricas de adopción
./scripts/measure_adoption_metrics.sh

# Feedback de equipo
./scripts/collect_team_feedback.sh

# Ajustes basados en datos reales
./scripts/optimize_based_on_metrics.sh
```

### **Escalamiento (Día +30)**
```bash
# Aplicar a otros repositorios
./scripts/replicate_to_other_repos.sh

# Entrenar al equipo
./scripts/generate_training_materials.sh

# Documentar lecciones aprendidas
./scripts/document_lessons_learned.sh
```

---

## 🚨 **NOTAS CRÍTICAS DE IMPLEMENTACIÓN**

### **❌ NO HACER**
- NO modificar estructura de carpetas existente
- NO cambiar APIs públicas sin validación
- NO ejecutar prompts sin instrucciones globales
- NO continuar si Score < 3/5 por >90 minutos

### **✅ SIEMPRE HACER**
- Validar cada 30 minutos
- Documentar todo en `docs/`
- Crear PRs pequeños por fase
- Mantener evidencia forense (`archivo:línea`)

### **🔄 PROCESO ITERATIVO**
- Cada prompt mejora al anterior
- Validación continua vs regresiones
- Adaptación basada en métricas reales
- Documentación sincronizada con código

---

**¡LISTO PARA MAXIMIZAR EL POTENCIAL DEL MODO AGENTE AUTÓNOMO!** 🚀

*Última actualización: $(date)*