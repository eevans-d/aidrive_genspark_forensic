# CHECKLIST: STAGING DEPLOYMENT v0.10.0
**Fecha Preparación**: Octubre 3, 2025  
**Release**: v0.10.0 (ETAPA 2 Security Mitigations)  
**Objetivo**: Zero-downtime deployment con validación completa

---

## PRE-DEPLOYMENT

### 1. Preparación de Secrets (30 min)
- [ ] Generar JWT_SECRET_DEPOSITO: `openssl rand -base64 32`
- [ ] Generar JWT_SECRET_NEGOCIO: `openssl rand -base64 32`
- [ ] Generar JWT_SECRET_ML: `openssl rand -base64 32`
- [ ] Generar JWT_SECRET_DASHBOARD: `openssl rand -base64 32`
- [ ] Backup del `.env.staging` actual
- [ ] Agregar nuevos secrets al `.env.staging`

**Archivo a actualizar**: `inventario-retail/.env.staging`

```bash
# Nuevas variables ETAPA 2
JWT_SECRET_DEPOSITO=<generado_arriba>
JWT_SECRET_NEGOCIO=<generado_arriba>
JWT_SECRET_ML=<generado_arriba>
JWT_SECRET_DASHBOARD=<generado_arriba>
OCR_TIMEOUT_SECONDS=30
INFLATION_RATE_MONTHLY=0.045  # 4.5% INDEC Sept 2025
```

### 2. Validación Local (20 min)
- [ ] Ejecutar `python3 validate_etapa2_mitigations.py` (27/27 passed)
- [ ] Build containers locales: `docker-compose -f inventario-retail/docker-compose.production.yml build`
- [ ] Test startup local (sin deploy)
- [ ] Verificar logs no muestran errores JWT/OCR/ML

### 3. CI/CD Verification (10 min)
- [ ] Verificar CI pipeline pasó en master (commit `ea0db23`)
- [ ] Trivy scan completed sin CRITICAL/HIGH
- [ ] Tests pasaron con cobertura ≥85%
- [ ] Containers built y pusheados a GHCR

**Comando**: Ver https://github.com/eevans-d/aidrive_genspark_forensic/actions

---

## DEPLOYMENT

### 4. Backup Current State (15 min)
- [ ] SSH a staging: `ssh ${STAGING_USER}@${STAGING_HOST}`
- [ ] Backup DB: `docker exec postgres pg_dump -U postgres inventory > backup_pre_v0.10.0.sql`
- [ ] Backup compose: `cp docker-compose.production.yml docker-compose.production.yml.bak`
- [ ] Backup .env: `cp .env.production .env.production.bak`
- [ ] Export logs: `docker-compose logs > logs_pre_v0.10.0.txt`

### 5. Deploy v0.10.0 (30 min)
- [ ] Pull código: `git pull origin master`
- [ ] Pull images: `docker-compose pull`
- [ ] Update .env con secrets generados
- [ ] Restart servicios: `docker-compose up -d --force-recreate`
- [ ] Esperar 30s para startup
- [ ] Verificar containers running: `docker ps`

**Directorio**: `~/aidrive_genspark_forensic/inventario-retail/`

### 6. Health Checks (15 min)
- [ ] Test deposito: `curl -f http://localhost:8001/health || echo FAIL`
- [ ] Test negocio: `curl -f http://localhost:8002/health || echo FAIL`
- [ ] Test ml: `curl -f http://localhost:8003/health || echo FAIL`
- [ ] Test dashboard: `curl -f http://localhost:8080/health || echo FAIL`
- [ ] Test nginx: `curl -f http://localhost:80/api/deposito/health || echo FAIL`
- [ ] Check logs: `docker-compose logs --tail=50 | grep -i error`

---

## VALIDATION

### 7. Smoke Tests - R1 Container Security (10 min)
- [ ] Exec deposito: `docker exec -it deposito whoami` → expect `agente`
- [ ] Exec negocio: `docker exec -it negocio whoami` → expect `negocio`
- [ ] Exec ml: `docker exec -it ml whoami` → expect `mluser`
- [ ] Exec dashboard: `docker exec -it dashboard whoami` → expect `dashboarduser`

**Expected**: Todos deben retornar non-root user

### 8. Smoke Tests - R2 JWT Isolation (20 min)
- [ ] Login deposito: `curl -X POST http://localhost:8001/auth/login -d '{"username":"admin","password":"test"}'`
- [ ] Extraer token deposito (JWT_DEPOSITO)
- [ ] Test cross-agent: `curl -H "Authorization: Bearer $JWT_DEPOSITO" http://localhost:8002/api/productos`
- [ ] Verificar logs negocio muestran error de issuer mismatch

**Expected**: Cross-agent requests deben fallar (401/403)

### 9. Smoke Tests - R3 OCR Timeout (15 min)
- [ ] Preparar imagen pesada (>10MB)
- [ ] POST a `/procesar_factura_completa`: `curl -X POST http://localhost:8002/procesar_factura_completa -F "file=@heavy_invoice.pdf"`
- [ ] Monitor logs: `docker-compose logs -f negocio | grep -i timeout`
- [ ] Verificar timeout a 30s si OCR demora

**Expected**: HTTP 504 Gateway Timeout si excede OCR_TIMEOUT_SECONDS

### 10. Smoke Tests - R4 ML Inflation (10 min)
- [ ] Check startup log ml: `docker-compose logs ml | grep INFLATION`
- [ ] Verify valor leído: `0.045` o `4.5%`
- [ ] Test predicción: `curl http://localhost:8003/predict -d '{"producto_id":1}'`
- [ ] Verificar ajuste de inflación en response

**Expected**: Log muestra inflación configurada correctamente

### 11. Smoke Tests - R6 Dependency Scan (5 min)
- [ ] Review CI logs: https://github.com/eevans-d/aidrive_genspark_forensic/actions
- [ ] Confirmar Trivy job ejecutó
- [ ] Confirmar exit-code=1 configurado
- [ ] Confirmar severity CRITICAL,HIGH

**Expected**: Trivy scan passed sin vulnerabilidades bloqueantes

---

## OBSERVABILITY

### 12. Metrics Validation (15 min)
- [ ] Dashboard metrics: `curl http://localhost:8080/metrics`
- [ ] Verificar `dashboard_requests_total` incrementa
- [ ] Verificar `dashboard_errors_total` = 0
- [ ] Verificar `dashboard_request_duration_ms_p95` < 500ms
- [ ] Grafana dashboard (si disponible)

### 13. Security Headers (10 min)
- [ ] Test CSP: `curl -I http://localhost:8080/`
- [ ] Verify `Content-Security-Policy` header presente
- [ ] Verify `X-Content-Type-Options: nosniff`
- [ ] Verify `X-Frame-Options: DENY`
- [ ] Verify `Strict-Transport-Security` (si HTTPS)

**Script**: `scripts/check_security_headers.sh`

### 14. Logs Monitoring (30 min post-deploy)
- [ ] Monitor por 30 min: `docker-compose logs -f --tail=100`
- [ ] No errores 500 en logs
- [ ] No OOM kills en containers
- [ ] No JWT validation errors inesperados
- [ ] No OCR timeouts en cargas normales

---

## ROLLBACK PLAN (Si falla)

### 15. Emergency Rollback (15 min)
- [ ] Stop containers: `docker-compose down`
- [ ] Restore .env: `cp .env.production.bak .env.production`
- [ ] Restore compose: `cp docker-compose.production.yml.bak docker-compose.production.yml`
- [ ] Restore DB: `docker exec -i postgres psql -U postgres inventory < backup_pre_v0.10.0.sql`
- [ ] Start old version: `docker-compose up -d`
- [ ] Verify health checks
- [ ] Notify team

**Trigger Conditions**:
- Health checks fallan > 3 min
- Error rate > 10%
- Critical service down
- Data corruption detectada

---

## POST-DEPLOYMENT

### 16. Documentation (20 min)
- [ ] Actualizar `DEPLOYMENT_LOG.md` con timestamp, commit, issues
- [ ] Update `CHANGELOG.md` con fecha deployment staging
- [ ] Screenshot de métricas post-deploy
- [ ] Commit deployment notes: `git commit -m "docs: staging v0.10.0 deployed successfully"`

### 17. Monitoring Setup (1-2 días)
- [ ] Enable alertas para error rate > 5%
- [ ] Monitor memory usage containers
- [ ] Track JWT rotation readiness
- [ ] Monitor inflación updates (monthly)
- [ ] Setup dashboard para R1-R6 metrics

### 18. Team Communication (10 min)
- [ ] Notificar equipo del deployment
- [ ] Compartir `RESUMEN_EJECUTIVO_ETAPA2.md`
- [ ] Briefing sobre nuevas variables de entorno
- [ ] Schedule review meeting (1 semana post-deploy)

---

## COMPLETION CRITERIA

**Deployment es exitoso si**:
- ✅ Todos los health checks (4 agentes + nginx) pasan
- ✅ Smoke tests R1, R2, R3, R4, R6 pasan
- ✅ No errores críticos en logs (30 min monitoring)
- ✅ Métricas estables (request rate, error rate, latency)
- ✅ Security headers presentes
- ✅ Trivy scan passed en CI/CD

**Rollback si**:
- ❌ 2+ health checks fallan después de 3 min
- ❌ Error rate > 10% sostenido
- ❌ Critical vulnerabilities detectadas por Trivy
- ❌ Data corruption o DB issues
- ❌ JWT cross-agent validation no funciona como esperado

---

## REFERENCIAS

- **Deployment Guide**: `inventario-retail/DEPLOYMENT_GUIDE.md`
- **R2 Migration**: `inventario-retail/R2_JWT_SECRET_MIGRATION_GUIDE.md`
- **R4 Migration**: `inventario-retail/R4_ML_INFLATION_MIGRATION_GUIDE.md`
- **Runbook**: `RUNBOOK_OPERACIONES_DASHBOARD.md`
- **Preflight Script**: `scripts/preflight_rc.sh`

**Contacto Emergencia**: eevans-d (GitHub)  
**Backup Contact**: AI Development Team

---

**Checklist Owner**: _________________  
**Fecha Ejecución**: _________________  
**Resultado**: [ ] Success / [ ] Rollback  
**Notas**: _________________
