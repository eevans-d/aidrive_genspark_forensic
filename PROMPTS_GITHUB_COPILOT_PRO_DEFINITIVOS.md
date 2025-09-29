# 🎯 PROMPTS DEFINITIVOS OPTIMIZADOS PARA GITHUB COPILOT PRO
## Estrategia Híbrida para Análisis Autónomo y Optimización Integral

**🚀 OBJETIVO**: Implementar la estrategia híbrida consolidada que combina precisión quirúrgica, enfoque modular exhaustivo y sofisticación técnica para sesiones autónomas de 90-130 minutos con máximo valor agregado.

---

## **📋 INSTRUCCIONES GLOBALES REFINADAS**
### (Aplicar a TODOS los prompts - Copiar antes de cada ejecución)

```markdown
**CONTEXTO CRÍTICO:**
- Repositorio: eevans-d/aidrive_genspark_forensic únicamente
- Submódulos: inventario-retail/, business-intelligence-orchestrator-v3.1/, sistema_deposito_semana1/

**RESTRICCIONES ABSOLUTAS:**
- NO cambiar estructura de carpetas existente
- NO modificar endpoints/contratos públicos
- NO mover/eliminar archivos existentes (solo marcar duplicados en docs/)
- NO crear carpetas top-level nuevas (usar estructura existente de submódulos)

**OPERATIVA SEGURA:**
- Trabajar en ramas: chore/[submódulo]-[fase]-[descripción]
- PRs pequeños por fase con artefactos y plan de rollback
- Feature flags para nuevas funcionalidades (OBSERVABILITY_ENABLED, IDEMPOTENCY_ENABLED)
- Si detectas algo "MUY MALO": crear DRAFT PR con justificación técnica y esperar aprobación

**DOCUMENTACIÓN OBLIGATORIA:**
- Registrar TODO en docs/ como parte de cada entrega
- Métricas before/after en cada optimización
- Tests de regresión para validar 0 cambios funcionales
```

---

## 🎯 **PROMPT DEFINITIVO 1: Consolidación Arquitectónica y Performance (90-120 min)**

```markdown
**APLICAR INSTRUCCIONES GLOBALES ARRIBA**

**MISIÓN AUTÓNOMA:** Análisis arquitectónico profundo, consolidación de lógica duplicada y optimización de performance sin romper compatibilidad.

**CADENA DE TAREAS SECUENCIALES:**

**FASE 1 - DIAGNÓSTICO INTEGRAL (30 min):**
- Mapear dependencias cruzadas entre submódulos con análisis estático
- Benchmarking con hey/k6 (10-15 min por servicio): P50/P95/P99 por endpoint
- Identificar top-10 queries lentas con EXPLAIN ANALYZE
- Detectar código duplicado entre submódulos (especialmente reglas de stock/validaciones)
- Documentar en `docs/diagnostico/baseline_consolidado.md`

**FASE 2 - HARDENING DB NO INTRUSIVO (25 min):**
- SQLite: Aplicar PRAGMAs óptimos (WAL, busy_timeout=10s, foreign_keys=ON, cache_size=-64000)
- Crear `[submódulo]/app/db/sqlite_config.py` con `get_db_connection()` centralizada
- PostgreSQL: Índices concurrentes en campos de alto uso
- Constraints de integridad: stock no negativo, unicidad para idempotencia
- Tests: validar PRAGMAs activos y uso de índices

**FASE 3 - CONSOLIDACIÓN INTELIGENTE (30 min):**
- Crear `[submódulo]/app/shared/core/` con validadores y políticas unificadas
- Implementar decoradores reutilizables:
  * `@memoize_with_ttl` para funciones costosas
  * `@retry_with_circuit_breaker` para integraciones
  * `@profile_performance` para monitoreo automático
- Refactorizar duplicación SIN cambiar APIs públicas
- Tests de regresión que validen comportamiento idéntico

**FASE 4 - OBSERVABILIDAD BÁSICA (20 min):**
- Métricas técnicas: request_latency_ms, db_query_time_ms, error_count
- Métricas retail: stock_value, turnover_days, low_stock_items
- Exportar `/metrics` solo con `OBSERVABILITY_ENABLED=true`
- Logs JSON estructurados con trace_id

**FASE 5 - VALIDACIÓN Y DOCUMENTACIÓN (15 min):**
- Ejecutar benchmarks post-optimización
- Comparar métricas before/after
- Actualizar `docs/architecture/sistema_consolidado.md`
- Crear PRs por fase con evidencia cuantitativa

**CRITERIOS DE ÉXITO MEDIBLES:**
- Reducción >25% código duplicado entre submódulos críticos
- Mejora >20% P95 latencia en al menos 3 endpoints
- PRAGMA journal_mode=wal verificado en tests
- 0 regresiones funcionales
- Documentación completa con evidencia

**EVIDENCIA FORENSE OBLIGATORIA:**
- Cada optimización debe incluir `archivo:línea-inicial–línea-final` de cambios
- Screenshots de benchmarks before/after
- Logs de tests de regresión pasando
- Métricas cuantitativas en formato tabla
```

---

## 🔒 **PROMPT DEFINITIVO 2: Security Hardening y Supply Chain (90-110 min)**

```markdown
**APLICAR INSTRUCCIONES GLOBALES ARRIBA**

**MISIÓN AUTÓNOMA:** Fortalecimiento integral de seguridad con auditoría forense y automatización de compliance.

**CADENA DE TAREAS SECUENCIALES:**

**FASE 1 - AUDITORÍA DE DEPENDENCIAS (25 min):**
- Inventario completo con pip-tools: directas, transitivas, OS packages
- Análisis de licencias: MIT/Apache vs GPL, riesgos copyleft
- Health score por dependencia: actividad, mantenedores, vulnerabilidades
- Detectar typosquatting, dependencias abandonadas, fuentes no oficiales
- Generar `security/supply_chain/dependency_audit.md`

**FASE 2 - HARDENING MULTICAPA (30 min):**
- Input validation estricta con Pydantic schemas
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- Rate limiting adaptativo por endpoint (configurar en Nginx si existe)
- CORS policies restrictivas
- Manejo de errores sin stack traces en respuestas
- Implementar en `[submódulo]/app/security/`

**FASE 3 - SISTEMA DE AUDITORÍA (25 min):**
- Event logging inmutable para operaciones críticas
- Audit trail con checksums para integridad
- Chain of custody para datos sensibles
- Implementar en `[submódulo]/app/audit/`
- Tests de tamper detection

**FASE 4 - AUTOMATIZACIÓN CI/CD (20 min):**
- GitHub Actions: Bandit, Safety, Trivy scanning
- SBOM generation automática con Syft
- Secret scanning y rotación
- Pipeline en `.github/workflows/security_pipeline.yml`
- Políticas fail-fast configurables

**FASE 5 - COMPLIANCE Y DOCUMENTACIÓN (10 min):**
- Scanners básicos para GDPR/PCI-DSS aplicables a retail
- Security runbooks en `docs/security/`
- Incident response procedures
- Métricas de seguridad en dashboards

**CRITERIOS DE ÉXITO:**
- 0 vulnerabilidades críticas/altas en dependencias productivas
- 100% operaciones críticas auditables
- Security pipeline operativa con <5% falsos positivos
- Compliance básica verificable
- Documentación completa de procedimientos

**EVIDENCIA FORENSE OBLIGATORIA:**
- Reportes de scanners (Bandit, Safety, Trivy) before/after
- Lista de vulnerabilidades con severidad y status
- Tests de penetración básicos documentados
- SBOM completo y verificado
```

---

## 📊 **PROMPT DEFINITIVO 3: Testing Integral y Observabilidad Avanzada (100-130 min)**

```markdown
**APLICAR INSTRUCCIONES GLOBALES ARRIBA**

**MISIÓN AUTÓNOMA:** Suite completa de testing con >90% cobertura y observabilidad predictiva para toma de decisiones.

**CADENA DE TAREAS SECUENCIALES:**

**FASE 1 - MEGA SUITE DE TESTING (40 min):**
- Tests unitarios automáticos para TODA función/método público (target: 300+ tests)
- Tests de integración para CADA endpoint con mocks inteligentes
- Tests de contrato con snapshots para validar estabilidad de APIs
- Performance testing sostenido: load, stress con k6 (15-20 min por servicio)
- Chaos engineering básico: network failures, DB locks, timeouts
- Estructura en `tests/{unit,integration,contracts,performance,chaos}/`

**FASE 2 - FRAMEWORK DE TESTING AVANZADO (25 min):**
- Base classes con auto-rollback de transacciones
- Factories para datos sintéticos realistas
- Test impact analysis: ejecutar solo tests afectados
- Parallel testing con pytest-xdist
- Implementar en `testing_framework/`

**FASE 3 - OBSERVABILIDAD PREDICTIVA (30 min):**
- Métricas avanzadas de negocio:
  * stock_accuracy_variance, fulfillment_rate_by_supplier
  * dead_stock_value, inventory_shrinkage_rate
  * transaction_abandonment_rate, service_level_compliance
- Alertas correlacionales multi-métrica
- Anomaly detection básico con umbrales dinámicos
- Implementar en `[submódulo]/app/analytics/`

**FASE 4 - DASHBOARDS EJECUTIVOS (20 min):**
- Executive dashboard: KPIs financieros y trends
- Operational dashboard: métricas tiempo real con drill-down
- Mobile-friendly views para management
- Generar en `monitoring/dashboards/`

**FASE 5 - QUALITY GATES Y CI/CD (15 min):**
- Pipeline con fail-fast: cobertura <85% = fail
- Quality metrics: complejidad ciclomática, duplicación de código
- Performance regression detection
- Integrar en CI/CD existente

**CRITERIOS DE ÉXITO:**
- Cobertura >90% en código crítico, >80% general
- Suite ejecutable en <10 minutos
- Métricas de negocio operativas con <30s latencia
- Dashboards funcionales y actualizados
- Quality gates activos en CI/CD

**EVIDENCIA FORENSE OBLIGATORIA:**
- Reportes de cobertura con líneas específicas no cubiertas
- Screenshots de dashboards funcionando
- Métricas de performance de la suite de tests
- Evidencia de quality gates funcionando en CI/CD
```

---

## **📊 GUÍA DE IMPLEMENTACIÓN PRÁCTICA**

### **Secuencia Recomendada:**
1. **Semana 1**: PROMPT 1 (Arquitectura + Performance) - Establece baseline sólida
2. **Semana 2**: PROMPT 2 (Security + Compliance) - Fortalece seguridad crítica
3. **Semana 3**: PROMPT 3 (Testing + Observabilidad) - Completa quality assurance

### **Monitoreo de Progreso:**
Cada prompt debe generar `docs/progress/[prompt_name]_$(date +%Y%m%d).md` con:
- Timestamp inicio/fin y tareas completadas
- Métricas cuantitativas (latencias, cobertura, vulnerabilidades)
- Bloqueadores encontrados y resoluciones
- Próximos pasos y recomendaciones

### **Validación Continua:**
- Tests automatizados después de cada fase
- Benchmarks before/after documentados
- PRs con checklist completo y artefactos
- Plan de rollback validado por fase

---

## **🔧 HERRAMIENTAS DE SOPORTE**

### **Scripts de Monitoreo:**
```bash
# Monitoreo de progreso en tiempo real
./scripts/monitor_progress.sh --prompt=1 --phase=current

# Validación de criterios de éxito
./scripts/validate_success_criteria.sh --prompt=1

# Generación de reportes ejecutivos
./scripts/generate_executive_report.sh --all-prompts
```

### **Comandos de Validación:**
```bash
# Validar que no se rompió nada
./scripts/regression_test_full.sh

# Benchmark comparison
./scripts/benchmark_compare.sh --before=baseline --after=current

# Security audit
./scripts/security_audit_complete.sh
```

---

## **🎯 VALOR AGREGADO ESPERADO**

### **Métricas de Éxito Global:**
- **Consolidación**: >25% reducción código duplicado
- **Performance**: >20% mejora latencia P95
- **Security**: 0 vulnerabilidades críticas
- **Testing**: >90% cobertura en código crítico
- **Observabilidad**: Dashboards ejecutivos funcionales
- **Automatización**: Pipelines CI/CD completos

### **ROI Estimado:**
- **Desarrollo**: -40% tiempo debugging
- **Operaciones**: -60% tiempo troubleshooting
- **Seguridad**: +300% visibilidad de amenazas
- **Calidad**: +200% confianza en releases

---

## **🚨 NOTAS CRÍTICAS FINALES**

- 🔥 **MODO FORENSE ESTRICTO**: Los prompts observan y optimizan, nunca rompen
- 📝 **EVIDENCIA OBLIGATORIA**: Sin `archivo:línea`, la información no es válida
- 🛡️ **VALIDAR ANTES DE APLICAR**: Revisar todas las configuraciones en staging
- 🔄 **ACTUALIZACIÓN CONTINUA**: Re-ejecutar cuando el código cambie significativamente
- 💾 **VERSIONADO SINCRONIZADO**: Mantener documentación al día con el código

**¡Listos para maximizar el potencial del modo agente autónomo!** 🚀