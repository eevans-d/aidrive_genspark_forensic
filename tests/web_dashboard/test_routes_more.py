import os
import sys
import importlib.machinery
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

# Forzar API key y desactivar rate limit para este módulo de pruebas
os.environ["DASHBOARD_API_KEY"] = "test-key"
os.environ["DASHBOARD_RATELIMIT_ENABLED"] = "false"

# Helper para leer la API key efectiva del entorno en cada request
def _key():
    return os.getenv("DASHBOARD_API_KEY", "test-key")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

dashboard_path = ROOT / "inventario-retail" / "web_dashboard" / "dashboard_app.py"
loader = importlib.machinery.SourceFileLoader("dashboard_app_more", str(dashboard_path))
spec = importlib.util.spec_from_loader("dashboard_app_more", loader)
module = importlib.util.module_from_spec(spec)  # type: ignore
loader.exec_module(module)  # type: ignore
app = getattr(module, "app")
analytics = getattr(module, "analytics")
client = TestClient(app)


def test_trends_months_clamp_and_filters_invalid():
    # months fuera de rango alto -> clamp a 24; fechas inválidas se ignoran (sanitización -> None)
    r = client.get("/api/trends?months=999&start_date=2025-99-99&end_date=2025-13-40&proveedor=@@X", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    body = r.json()
    # Debe devolver dict con llaves esperadas aunque filtros inválidos se limpien
    assert isinstance(body, dict)
    assert "pedidos_mensuales" in body


def test_stock_timeline_days_clamp():
    # days=0 -> clamp a 1
    r = client.get("/api/stock-timeline?days=0", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_weekly_sales_weeks_clamp():
    # weeks fuera de rango alto -> clamp 52
    r = client.get("/api/weekly-sales?weeks=999", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_export_summary_error_branch(monkeypatch):
    def summary_error():
        return {"error": "falla resumida"}
    monkeypatch.setattr(analytics, "get_dashboard_summary", summary_error)
    r = client.get("/api/export/summary.csv", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    assert r.text.startswith("error,message")


def test_stock_by_provider_fallback(monkeypatch):
    # Forzar excepción en primera consulta y devolver lista de provider stats válida para fallback
    def providers_ok():
        return [
            {"codigo": "P1", "nombre": "Prov Uno", "total_productos": 10},
            {"codigo": "P2", "nombre": "Prov Dos", "total_productos": 5},
        ]
    monkeypatch.setattr(analytics, "get_provider_stats", providers_ok)
    # Simular error en get_stock_by_provider leyendo conexión levantando excepción mediante monkeypatch al método db_manager
    original_db_manager = analytics.db_manager
    class BrokenDB:
        def get_connection(self):
            raise RuntimeError("db fail")
    analytics.db_manager = BrokenDB()  # type: ignore
    try:
        r = client.get("/api/stock-by-provider", headers={"X-API-Key": _key()})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert any(item.get("codigo") == "P1" for item in data)
    finally:
        analytics.db_manager = original_db_manager  # restore
