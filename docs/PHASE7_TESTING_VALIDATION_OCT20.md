# 🚀 PHASE 7: TESTING & VALIDATION
## Octubre 20-21, 2025 (Próximas Acciones)

---

## 📋 ESTADO ACTUAL

**Fase Anterior**: Phase 6 ✅ COMPLETADA
- Memory Leak Fix: ✅ Implementado
- HTTP Timeouts: ✅ Verificados (100%)
- Exception Logging: ✅ Verificados (99%)
- Usuario JWT: ✅ Verificado (100%)

**Archivos Modificados**: 1
- `inventario-retail/agente_negocio/integrations/deposito_client(1).py`

**Commit Hash**: `b33f6c8`
**Branch**: `feature/resilience-hardening`

---

## 🧪 FASE 7: TESTING & VALIDATION

### Etapa 1: Unit Tests (1h)

```bash
# Ejecutar tests específicos para deposito_client
pytest -v tests/web_dashboard/test_*.py -k "deposito or stats" --tb=short

# Verificar cobertura completa
pytest --cov=inventario-retail/web_dashboard --cov-fail-under=85 \
       --cov-report=term-missing tests/web_dashboard

# Validar memory metrics
pytest -v tests/ -k "memory" --tb=short
```

**Criterios de Aceptación**:
- ✓ Cobertura ≥ 85%
- ✓ All tests PASS
- ✓ Memory leak fix testeable
- ✓ No regresiones

### Etapa 2: Integration Tests (1.5h)

```bash
# Tests de integración con backends
pytest -v tests/integration/ --tb=short

# Load testing con memory monitoring
python scripts/performance/profile_performance.py \
       --duration=300 --monitor-memory

# Stress test con gc.collect() validation
pytest -v tests/integration/test_stress.py
```

**Criterios de Aceptación**:
- ✓ Endpoints responden correctamente
- ✓ Memory no crece indefinidamente
- ✓ gc.collect() libera memoria
- ✓ No hay file descriptor leaks

### Etapa 3: Staging Validation (2h)

```bash
# Deploy a staging
make rc-tag TAG=v1.0.0-rc1 STAGING_URL=... STAGING_KEY=...

# Smoke tests
./scripts/preflight_rc.sh STAGING_URL=... STAGING_API_KEY=...

# Memory profiling en staging
python scripts/memory_profiler.py --duration=600 --endpoint=staging

# Health check con métricas
curl -H "X-API-Key: $STAGING_API_KEY" \
     http://staging/metrics | grep dashboard_memory_bytes
```

**Criterios de Aceptación**:
- ✓ Health check PASS
- ✓ Memory stable (no growth)
- ✓ Metrics expuestas correctamente
- ✓ Logs estructurados OK

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Target | Método Validación |
|---------|--------|-------------------|
| Cobertura | ≥85% | `pytest --cov=...` |
| Memory Leak Fix | RESUELTO | Memory profile con psutil |
| gc.collect() | Funciona | Logs con memory freed |
| HTTP Timeouts | 100% | Code review |
| Exception Logging | 99% | Grep de except blocks |
| Tests Passing | 100% | `pytest -v ...` |
| Staging Ready | YES | Smoke tests |

---

## 🎯 PRÓXIMAS ACCIONES

### HOY (Oct 20) - Contingencia
- [ ] Revisar errores de lint en deposito_client(1).py
- [ ] Instalar psutil si no está disponible
- [ ] Validar imports gc, psutil, os

### MAÑANA (Oct 21) - Testing
- [ ] Ejecutar suite de tests Unit
- [ ] Ejecutar suite de tests Integration
- [ ] Load testing con memory monitoring
- [ ] Generar reporte de coverage

### PASADO MAÑANA (Oct 22) - Staging
- [ ] Deploy a staging v1.0.0-rc1
- [ ] Smoke tests en staging
- [ ] Memory profiling 10 minutos
- [ ] Validar métricas Prometheus

### JUE-VIE (Oct 23-24) - Final
- [ ] PR Review completo
- [ ] Merge a master (si todo OK)
- [ ] Deploy a producción (optional)
- [ ] Post-mortem y lecciones aprendidas

---

## ⚠️ RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|-----------|
| psutil no instalado | MEDIA | Verificar requirements.txt |
| gc.collect() impacta performance | BAJA | Logging muestra delta pequeño |
| Lint errors en deposito_client(1).py | MEDIA | Revisar type hints |
| Tests no coveran memory leak fix | MEDIA | Crear test específico |

---

## 📚 REFERENCIAS

- Diagnóstico Forense: `DIAGNOSTICO_AIDRIVE_GENSPARK_FORENSIC.txt`
- Phase 6 Doc: `docs/PHASE6_CRITICAL_FIXES_OCT20.md`
- Coverage Base: `coverage.xml` (85.74%)
- Commit Anterior: `b33f6c8` (Phase 6)

---

## 📞 NOTAS DE CONTINGENCIA

Si hay problemas:

### LintError en deposito_client(1).py
```python
# Revisar line 133 (type hint issue)
# Revisar lines 725, 747 (params category)
# Solución: Revisar tipos en Response.json()
```

### psutil ImportError
```bash
pip install psutil
# O si necesario: pip install -r requirements-resilience.txt
```

### Memory tests fallan
```bash
# Validar que gc.collect() realmente libera
python -c "import gc; gc.collect(); print('gc works')"
```

---

**Última Actualización**: Oct 20, 2025 - 15:30
**Responsable**: GitHub Copilot
**Fase**: 7/7 (Final antes de Production)
