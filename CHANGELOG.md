# Changelog

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
