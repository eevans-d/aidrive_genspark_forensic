---
name: Release Candidate Checklist
title: "RC Checklist v1.0.0-rc1"
about: Checklist para preparar y validar un Release Candidate del Dashboard
labels: release, rc
---

## 1. Pre-condiciones
- [ ] Cobertura ≥ 85% (actual: _completar_)
- [ ] Último commit en `master` sin cambios pendientes
- [ ] CI verde (tests + build + smoke image)
- [ ] Secretos Staging completos (`staging-secrets-check` ✅)

## 2. Deploy Staging
- [ ] Job `deploy-staging` ejecutado
- [ ] Smoke interno OK
- [ ] Job `staging-metrics-check` ejecutado (advisory)

## 3. Validación funcional
- [ ] /health 200
- [ ] /api/summary 401 sin API Key
- [ ] /api/summary 200/500 con API Key
- [ ] /api/export/summary.csv 200
- [ ] Navegación UI (si aplica) sin errores JS

## 4. Métricas (script)
Ejecutar preflight unificado:
```bash
scripts/preflight_rc.sh -u https://staging.example.com -k $STAGING_DASHBOARD_API_KEY
```
Registrar:
- Requests totales: ____
- Errores totales: ____
- Error %: ____ (umbral <2%)
- p95(ms): ____ (umbral <800)

## 5. Seguridad / Headers
- [ ] CSP coincide con snapshot test
- [ ] HSTS DESACTIVADO en staging (>=prod only)
- [ ] Rate limiting habilitado (si configurado)

## 6. Decisión RC
- [ ] Criterios cumplidos
- [ ] Tag creado:
```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```
- [ ] Pipeline sobre tag completado

## 7. Observación Post-RC
Ventana mínima 30–60 min:
- [ ] Error % estable <2%
- [ ] Sin picos anómalos rutas
- [ ] Logs sin bursts 5xx

## 8. Preparación Release Final
- [ ] Plan de ventana final validado
- [ ] Secretos PROD listos (ver doc)
- [ ] API Key PROD generada (no aplicada aún)

## 9. Go / No-Go
- [ ] Go aprobado por (Nombres): ___________
- [ ] Si No-Go: incident ticket abierto (#___)

## 10. Tag Final (cuando corresponda)
```bash
git tag v1.0.0
git push origin v1.0.0
```

## 11. Post-Release
- [ ] Registrar métricas iniciales en Runbook
- [ ] Crear issue de mejoras Post-Go-Live (parking lot)

---
(Autogenerado plantilla RC)
