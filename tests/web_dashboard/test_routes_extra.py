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
loader = importlib.machinery.SourceFileLoader("dashboard_app_extra", str(dashboard_path))
spec = importlib.util.spec_from_loader("dashboard_app_extra", loader)
module = importlib.util.module_from_spec(spec)  # type: ignore
loader.exec_module(module)  # type: ignore
app = getattr(module, "app")
analytics = getattr(module, "analytics")
client = TestClient(app)


def test_dashboard_home_error_branch(monkeypatch):
    # Fuerza excepción en get_dashboard_summary para cubrir el except
    def boom():
        raise RuntimeError("fallo simulado")
    monkeypatch.setattr(analytics, "get_dashboard_summary", boom)
    r = client.get("/")
    assert r.status_code == 200
    assert "Error cargando" in r.text


def test_api_top_products_clamp_and_filters():
    # limit fuera de rango -> debe clamp a 100
    r = client.get("/api/top-products?limit=9999", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # limit negativo -> clamp a 1
    r2 = client.get("/api/top-products?limit=-5", headers={"X-API-Key": _key()})
    assert r2.status_code == 200


def test_metrics_endpoint_generates_lines():
    r = client.get("/metrics", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    body = r.text.splitlines()
    assert any(l.startswith("dashboard_requests_total") for l in body)


def test_csv_exports_and_error_paths(monkeypatch):
    # Forzar error en provider stats para cubrir rama de error CSV
    def providers_error():
        return [{"error": "falla"}]
    monkeypatch.setattr(analytics, "get_provider_stats", providers_error)
    r = client.get("/api/export/providers.csv", headers={"X-API-Key": _key()})
    assert r.status_code == 200
    assert "error,message" in r.text

    # Top products CSV normal path
    def top_products_mock(limit, s_start, s_end, s_prov):
        return [
            {"producto": "A", "cantidad_total": 10, "pedidos": 5, "proveedor": "P1"},
            {"producto": "B", "cantidad_total": 4, "pedidos": 2, "proveedor": "P2"},
        ]
    monkeypatch.setattr(analytics, "get_top_products", top_products_mock)
    r2 = client.get("/api/export/top-products.csv", headers={"X-API-Key": _key()})
    assert r2.status_code == 200
    assert "producto,cantidad_total,pedidos,proveedor" in r2.text


def test_health_check_error_branch(monkeypatch):
    def boom():
        raise RuntimeError("db caída")
    monkeypatch.setattr(analytics, "get_dashboard_summary", boom)
    r = client.get("/health", headers={"X-API-Key": _key()})
    # Health sin API key estricta (aquí no se exige) pero devolvemos 503 por la excepción
    assert r.status_code == 503
    assert r.json()["status"] == "unhealthy"
