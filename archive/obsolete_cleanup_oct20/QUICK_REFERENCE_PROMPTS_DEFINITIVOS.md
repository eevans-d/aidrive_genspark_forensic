# 📚 QUICK REFERENCE - PROMPTS DEFINITIVOS OPTIMIZADOS

## 🚀 **COMANDOS RÁPIDOS**

### **Preparación**
```bash
# Validar estado inicial
./scripts/validate_success_criteria.sh --prompt=1
./scripts/validate_success_criteria.sh --prompt=2  
./scripts/validate_success_criteria.sh --prompt=3

# Generar reporte baseline
./scripts/generate_executive_report.sh --all-prompts
```

### **Durante Ejecución**
```bash
# Monitorear progreso (terminal separado)
./scripts/monitor_progress.sh --prompt=1 --phase=current

# Validar cada 30 min
./scripts/validate_success_criteria.sh --prompt=1

# Test de regresión
./scripts/regression_test_full.sh
```

### **Post-Ejecución**
```bash
# Comparar performance
./scripts/benchmark_compare.sh --before=baseline --after=current

# Auditoría de seguridad
./scripts/security_audit_complete.sh

# Reporte ejecutivo final
./scripts/generate_executive_report.sh --all-prompts
```

---

## 🎯 **PROMPTS RESUMIDOS**

### **PROMPT 1: Consolidación (90-120 min)**
**Fases:** Diagnóstico → DB Hardening → Consolidación → Observabilidad → Validación  
**Éxito:** >25% menos duplicación, >20% mejor P95, SQLite WAL, 0 regresiones  

### **PROMPT 2: Security (90-110 min)**  
**Fases:** Auditoría Deps → Hardening → Sistema Audit → CI/CD → Compliance  
**Éxito:** 0 vulns críticas, 100% ops auditables, pipeline <5% falsos positivos  

### **PROMPT 3: Testing (100-130 min)**
**Fases:** Mega Suite → Framework → Observabilidad → Dashboards → Quality Gates  
**Éxito:** >90% cobertura crítica, suite <10min, dashboards funcionales  

---

## 📊 **CRITERIOS DE ÉXITO RÁPIDOS**

| Prompt | Score Mínimo | Entregables Clave |
|--------|---------------|-------------------|
| 1 | 4/5 | `docs/diagnostico/baseline_consolidado.md`, SQLite config, `/metrics` |
| 2 | 4/5 | `security/supply_chain/dependency_audit.md`, security pipeline |
| 3 | 4/5 | Suite tests >90%, dashboards, quality gates CI/CD |

---

## 🚨 **TROUBLESHOOTING EXPRESS**

### **Score Estancado < 3/5**
```bash
# 1. Verificar GitHub Copilot Pro tiene contexto completo
# 2. Re-aplicar instrucciones globales
# 3. Dividir prompt en sub-fases
# 4. Crear DRAFT PR para revisión
```

### **Tests Fallan**
```bash
# Ver detalles
cat /tmp/test_output_*.log

# Re-ejecutar específico
python -m pytest tests/specific_test.py -v
```

### **Performance Degrada**
```bash
# Reiniciar contexto GitHub Copilot Pro
# Verificar recursos sistema
# Simplificar prompt actual
```

---

## 🔧 **COMANDOS DE EMERGENCIA**

```bash
# Validación completa express
./scripts/regression_test_full.sh && echo "✅ No regressions"

# Status rápido todos los prompts
for i in {1..3}; do ./scripts/validate_success_criteria.sh --prompt=$i; done

# Reporte ejecutivo urgente
./scripts/generate_executive_report.sh --all-prompts && \
cat docs/progress/executive_summary_*.md | tail -20
```

---

## 📋 **CHECKLIST PRE-EJECUCIÓN**

- [ ] Repositorio clonado y actualizado
- [ ] GitHub Copilot Pro activo con contexto completo
- [ ] Scripts de monitoreo ejecutables (`chmod +x scripts/*.sh`)
- [ ] Terminal separado para monitoreo listo
- [ ] Instrucciones globales copiadas

## 📋 **CHECKLIST POST-EJECUCIÓN**

- [ ] Score ≥ 4/5 en validación
- [ ] Tests de regresión pasando (≥80% success rate)
- [ ] Documentación actualizada en `docs/`
- [ ] Reporte ejecutivo generado
- [ ] PRs creados por fase con evidencia

---

**⚡ LISTO PARA ACCIÓN INMEDIATA** 🚀