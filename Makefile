# Makefile operativo (no invasivo) - Dashboard Mini Market
# Objetivo: facilitar comandos repetitivos de validación y release sin scripts adicionales.

.PHONY: help test coverage smoke preflight headers metrics rc-tag clean-artifacts

help:
	@echo "Targets disponibles:";
	@echo "  test          - Ejecuta tests rápidos del dashboard";
	@echo "  coverage      - Tests con coverage (umbral 85%)";
	@echo "  smoke         - Smoke local (requiere DASHBOARD_API_KEY y contenedor corriendo)";
	@echo "  metrics       - Verifica métricas en STAGING_URL (requiere STAGING_DASHBOARD_API_KEY)";
	@echo "  headers       - Verifica headers en STAGING_URL";
	@echo "  preflight     - Ejecuta preflight RC en STAGING_URL";
	@echo "  rc-tag        - Crea y push tag RC (VARIABLE TAG=) tras preflight";

TEST_DIR=tests
PYTHON=python3

# Usa requirements del dashboard; si faltan dependencias instalarlas antes.

test:
	DASHBOARD_API_KEY=test-key DASHBOARD_RATELIMIT_ENABLED=false pytest -q $(TEST_DIR)/web_dashboard

coverage:
	DASHBOARD_API_KEY=test-key DASHBOARD_RATELIMIT_ENABLED=false pytest -q $(TEST_DIR)/web_dashboard --cov=inventario-retail/web_dashboard --cov-report=term-missing --cov-fail-under=85

smoke:
	@[ -n "$$DASHBOARD_API_KEY" ] || { echo "Falta DASHBOARD_API_KEY en entorno"; exit 2; }
	bash scripts/smoke_dashboard_staging.sh

metrics:
	@[ -n "$$STAGING_URL" ] || { echo "Definir STAGING_URL"; exit 2; }
	@[ -n "$$STAGING_DASHBOARD_API_KEY" ] || { echo "Definir STAGING_DASHBOARD_API_KEY"; exit 2; }
	bash scripts/check_metrics_dashboard.sh -u $$STAGING_URL -k $$STAGING_DASHBOARD_API_KEY

headers:
	@[ -n "$$STAGING_URL" ] || { echo "Definir STAGING_URL"; exit 2; }
	bash scripts/check_security_headers.sh -u $$STAGING_URL

preflight:
	@[ -n "$$STAGING_URL" ] || { echo "Definir STAGING_URL"; exit 2; }
	@[ -n "$$STAGING_DASHBOARD_API_KEY" ] || { echo "Definir STAGING_DASHBOARD_API_KEY"; exit 2; }
	bash scripts/preflight_rc.sh -u $$STAGING_URL -k $$STAGING_DASHBOARD_API_KEY

# Uso: make rc-tag TAG=v1.0.0-rc1 STAGING_URL=... STAGING_DASHBOARD_API_KEY=...
rc-tag: preflight
	@[ -n "$$TAG" ] || { echo "Definir TAG=vX.Y.Z-rcN"; exit 2; }
	git tag $$TAG
	git push origin $$TAG
	@echo "Tag $$TAG creado y enviado."