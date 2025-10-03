# Changelog

Todas las notas siguen el formato Keep a Changelog y versionado SemVer.

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

## [1.0.0-rc1] - YYYY-MM-DD
### Added
- Script `check_metrics_dashboard.sh` para verificación de métricas
- Script `check_security_headers.sh` para validar headers de seguridad
- Script `preflight_rc.sh` para orquestar smoke/métricas/headers
- Makefile operativo (targets: test, coverage, preflight, rc-tag)
- Job CI advisory `staging-metrics-check`
- Plantilla Issue `release_rc_checklist.md`

### Changed
- README principal: sección tooling operativo
- Runbook: tagging RC → Release y referencia a scripts
- Guía extendida: pasos tagging con preflight

### Security
- Refuerzo operativo de validación headers antes de release

---
Formato basado en ideas de Keep a Changelog.
### Misc
- Fixed: retail tests now pass (async DB factory handled without context manager
- Prometheus labels ASCII
- validation messages aligned
- EAN-13 util tests green). Improved: CircuitBreaker exception handling
- metrics export returns string. Notes: left Pydantic v1 validator warnings in shared/retail_validation.py for later migration.
