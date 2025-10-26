# Changelog

Todas las notas siguen el formato Keep a Changelog y versionado SemVer.

## [Unreleased]
### ETAPA 3 - Phase 1: Deploy & Observability (IN PROGRESS)

#### Week 1: Staging Deployment Success (9h/23h COMPLETADO - 39%)
**Objetivo**: Resolver blocker de staging deployment (PyPI timeouts ~2.8GB ML packages)

**✅ COMPLETADO (Oct 4, 2025):**
- **T1.1.1** (2h): PIP_DEFAULT_TIMEOUT=600 + PIP_RETRIES=5 en 4 Dockerfiles
  - Commit: 9af3d1a "fix(docker): increase pip timeout to 600s"
  - Mitiga timeouts en descarga de torch (888MB), nvidia-cudnn (707MB)
- **T1.1.2** (3h): PyPI mirror Tsinghua configurado en 4 Dockerfiles  
  - Commit: 7193be4 "feat(docker): add PyPI mirror (Tsinghua)"
  - Fallback: https://pypi.tuna.tsinghua.edu.cn/simple
- **T1.1.3** (4h): Pre-download wheels strategy
  - Commit: 8ba725f "feat(deploy): add pre-download wheels strategy"
  - Script: `scripts/download_wheels.sh` para packages críticos
  - Documentado en `inventario-retail/DEPLOYMENT_GUIDE.md`
- **T1.1.4** (1h): Sequential build script
  - Commit: 3fedb6d "feat(scripts): add sequential build script"
  - Script: `scripts/build_sequential.sh` (builds one service at a time)

**⏳ PENDIENTE (14h) - Requiere servidor staging:**
- **T1.1.5** (3h): Deploy staging con nueva estrategia (3 soluciones implementadas)
- **T1.1.6** (2h): Smoke tests R1-R6 en staging
- **T1.1.7** (8h): Monitoring 48h + gate decision M1

**📊 Milestone M1 Status**: BLOCKED - Requiere servidor staging externo para validar soluciones

---

### Planning (Completed Oct 3, 2025)
- **ETAPA 3**: Mega plan created - Consolidación Operacional y Features Críticas
  - Fase 1: Deploy & Observability (Mes 1, 40-48h)
  - Fase 2: Automation & Features (Mes 2-3, 60-72h)
  - Fase 3: Optimization & Tech Debt (Mes 3-4, 32-40h)
  - Total: 132-160h / 14 semanas
  - ROI esperado: 2.1x promedio
  - Doc: `MEGA_PLAN_ETAPA_3.md` (690 lines)

## [v0.10.0] - 2025-10-03
### Security (ETAPA 2 COMPLETA: Risk Mitigations R1, R2, R3, R4, R6)

**Forensic Analysis Implementation**: Este release completa 5 de 7 mitigaciones identificadas en el análisis forense exhaustivo del sistema. Total: 23h de esfuerzo, ROI promedio 1.95.

#### R1: Container Security (Severity 10) ✅
- **Problema**: Dashboard container ejecutándose como root (vulnerabilidad crítica)
- **Solución**: Hardened all 4 agent containers with non-root users
  - `agente_deposito`: USER agente ✅
  - `agente_negocio`: USER negocio ✅
  - `ml_service`: USER mluser ✅
  - `web_dashboard`: USER dashboarduser ✅ (NEW)
- **Impacto**: Previene escalación de privilegios en caso de compromiso del container
- **Commits**: b02f2ae | Effort: 3h | ROI: 3.5

#### R6: Dependency Scanning (Severity 7) ✅
- **Problema**: Trivy scan solo advisory (continue-on-error: true), no bloquea builds
- **Solución**: Enforced Trivy in CI/CD with exit-code=1
  - New job `trivy-scan-dependencies` scans requirements.txt (scan-type: fs)
  - Severity: CRITICAL,HIGH (excludes MEDIUM to avoid false positives)
  - ignore-unfixed: true (don't block on CVEs without patches)
  - Runs parallel to test-dashboard (no blocking dependencies)
- **Impacto**: Prevents vulnerable dependencies from reaching production
- **Commits**: b02f2ae | Effort: 2h | ROI: 2.1

#### R3: OCR Timeout Risk (Severity 7) ✅
- **Problema**: OCR processing sin timeout, riesgo de DoS con imágenes grandes/maliciosas
- **Solución**: Configurable timeout with asyncio.wait_for()
  - OCRProcessor.process_image: Changed from async to sync (correct for to_thread)
  - Wrapped OCR calls in both `/process-invoice` and `/test-ocr` endpoints
  - ENV var `OCR_TIMEOUT_SECONDS=30` (configurable)
  - Returns HTTP 504 with clear message on timeout
- **Impacto**: Prevents resource exhaustion, improves UX with clear error messages
- **Commits**: a5dc1de | Effort: 4h | ROI: 1.8

#### R2: JWT Single Secret (Severity 8) ✅
- **Problema**: All agents share JWT_SECRET_KEY, compromising one compromises all
- **Solución**: Per-agent JWT secrets with backward-compatible fallback
  - New env vars: JWT_SECRET_DEPOSITO, JWT_SECRET_NEGOCIO, JWT_SECRET_ML, JWT_SECRET_DASHBOARD
  - Fallback pattern: `${JWT_SECRET_AGENT:-${JWT_SECRET_KEY}}` (zero-downtime migration)
  - Added `iss` (issuer) claim to JWT tokens for origin validation
  - AuthManager accepts optional secret_key and issuer parameters
  - Helper function: `get_auth_manager_for_agent(agent_name)`
- **Impacto**: Agent compromise doesn't cascade, enables independent secret rotation
- **Migration Guide**: inventario-retail/R2_JWT_SECRET_MIGRATION_GUIDE.md
- **Commits**: d590f78 | Effort: 8h | ROI: 1.6

#### R4: ML Hardcoded Inflation (Severity 6) ✅
- **Problema**: Inflation rate hardcoded at 4.5%, requires redeploy to update (critical for Argentina)
- **Solución**: Externalized to INFLATION_RATE_MONTHLY env var
  - ml/predictor.py: Read from env var (default 0.045) with startup logging
  - ml/features.py: Optional inflation parameter, auto-detect decimal vs percentage
  - Update without redeploy: restart ml-service only (no full stack)
  - Aligned with INDEC/BCRA monthly reports
- **Impacto**: Operational agility (minutes vs hours), ML predictions reflect current economics
- **Migration Guide**: inventario-retail/R4_ML_INFLATION_MIGRATION_GUIDE.md
- **Commits**: d65c95a | Effort: 6h | ROI: 1.7

### Added
- Migration guides: R2_JWT_SECRET_MIGRATION_GUIDE.md, R4_ML_INFLATION_MIGRATION_GUIDE.md
- ENV vars: JWT_SECRET_DEPOSITO, JWT_SECRET_NEGOCIO, JWT_SECRET_ML, JWT_SECRET_DASHBOARD
- ENV vars: OCR_TIMEOUT_SECONDS, INFLATION_RATE_MONTHLY
- CI/CD: trivy-scan-dependencies job (enforced)
- AuthManager: per-agent instances with issuer claim support
- Logging: OCR timeout config, ML inflation rate at startup

### Changed
- shared/auth.py: AuthManager accepts optional secret_key and issuer
- docker-compose.production.yml: Per-agent secrets with fallback, new env vars
- .env.production.template: Documented R2, R3, R4 variables with generation instructions
- ml/predictor.py: Externalized inflation rate to env var
- ml/features.py: Optional inflation parameter with env var fallback
- agente_negocio/main_complete.py: OCR timeout wrappers on 2 endpoints
- agente_negocio/ocr/processor.py: Sync process_image (was async, incorrect)
- web_dashboard/Dockerfile: Added USER dashboarduser with proper setup

### Documentation
- R2 Migration Guide: Gradual rollout strategy, validation tests, rollback plan
- R4 Migration Guide: Monthly INDEC update process, operational guidelines
- CHANGELOG: Comprehensive ETAPA 2 summary with ROI metrics

### Metrics
- **Total Effort**: 23 hours (R1=3h, R6=2h, R3=4h, R2=8h, R4=6h)
- **Average ROI**: 1.95 (all exceed 1.6 threshold)
- **Severity Mitigated**: Avg 7.6/10 (range: 6-10)
- **Impact**: Security hardening, operational flexibility, zero-downtime migrations
- **Commits**: 5 technical + 1 docs = 6 total

### Analysis Results: Non-Applicable Findings
- **R5: Forensic audit cascade failure** → ⚠️ **N/A** (FSM teórica en audit_framework/, no código producción)
- **R7: WebSocket memory leak** → ⚠️ **N/A** (WebSockets no implementados en dashboard actual)

**Nota**: R5 y R7 fueron identificados por forensic analysis tool basándose en patrones teóricos/comunes, pero no corresponden a implementaciones reales en el sistema. ETAPA 2 considera **5/5 mitigaciones aplicables** completadas (100%).

---

## [v0.9.0] - 2025-10-03 [DEPRECATED - SEE v0.10.0]
### Note
This version was an intermediate release. All R1/R6/R3 mitigations are now consolidated in v0.10.0 above.

## [v0.8.4] - 2025-09-30
### Added


Todas las notas siguen el formato Keep a Changelog (simplificado) y versionado SemVer.

## [Unreleased]
- (pendiente) Ajustes menores post v1.0.0

## [v1.0.0-rc1] - 2025-10-26
### Added
- Documentación de Producción FASES 7-8 (3,000+ líneas):
  - `FASE7_PRODUCTION_VALIDATION_CHECKLIST.md` (50+ security/perf checks)
  - `FASE7_DISASTER_RECOVERY.md` (RTO/RPO, 5 escenarios, PITR)
  - `FASE7_PRE_PRODUCTION_CHECKLIST.md` (100+ validaciones, ALL GREEN)
  - `FASE8_GO_LIVE_PROCEDURES.md` (blue-green, staged rollout, rollback)
  - `PROYECTO_COMPLETADO_FASES_0_8_FINAL.md`, `ESTADO_FINAL_PRODUCCION_OCTUBRE_2025.md`,
    `INDICE_MAESTRO_FINAL_OCTUBRE_2025.md`, `QUICKSTART_PRODUCCION_FINAL.md`.
- Scripts operativos:
  - `scripts/load_testing_suite.sh` (4 escenarios: 100/500/1000+ req/s + baseline)
  - `scripts/preflight_rc.sh` (smoke + métricas + headers)
  - `scripts/check_security_headers.sh`, `scripts/check_metrics_dashboard.sh`.
- CI/CD: artefactos listos para RC, deploy prod por tags vX.Y.Z (sin cambios en lógica).

### Changed
- `README.md`: actualizado con estado PRODUCCIÓN LISTA, guía rápida y estructura final.
- Runbooks y guías: referencias a preflight, load testing y go-live.

### Security
- Validación completa de seguridad (50/50 checks): auth (API key/JWT), rate limit,
  headers (CSP/HSTS), input validation, logs sin datos sensibles, non-root containers.

### Performance
- Resultados de carga validados: p95 < 500ms @ 100 req/s, 99.2–99.8% success rate.

### Notes
- Release Candidate previo a `v1.0.0`. Despliegue a producción sólo con tag final `v1.0.0`.

---
Formato basado en ideas de Keep a Changelog.
### Misc
- Fixed: retail tests now pass (async DB factory handled without context manager
- Prometheus labels ASCII
- validation messages aligned
- EAN-13 util tests green). Improved: CircuitBreaker exception handling
- metrics export returns string. Notes: left Pydantic v1 validator warnings in shared/retail_validation.py for later migration.
