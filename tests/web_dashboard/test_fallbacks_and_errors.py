import importlib.util
import importlib.machinery
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
dashboard_path = ROOT / "inventario-retail" / "web_dashboard" / "dashboard_app.py"
loader = importlib.machinery.SourceFileLoader("dashboard_app_fallbacks", str(dashboard_path))
spec = importlib.util.spec_from_loader("dashboard_app_fallbacks", loader)
assert spec is not None
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)  # type: ignore

app = mod.app
client = TestClient(app, raise_server_exceptions=False)


def test_stock_by_provider_fallback(monkeypatch):
    """Fuerza excepción primaria en get_stock_by_provider para cubrir fallback basado en provider_stats."""
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")

    # Simular provider_stats devolviendo datos válidos
    fake_stats = [
        {"codigo": "A", "nombre": "Prov A", "total_productos": 50},
        {"codigo": "B", "nombre": "Prov B", "total_productos": 10},
    ]
    monkeypatch.setattr(mod.analytics, "get_provider_stats", lambda: fake_stats)  # type: ignore

    class BrokenDB:
        def get_connection(self):  # se llamará dentro del with y lanzará para activar except
            raise RuntimeError("db offline")

    monkeypatch.setattr(mod.analytics, "db_manager", BrokenDB())  # type: ignore
    # Limpiar cache para que no use resultados previos
    mod.analytics._cache.pop('stock_by_provider', None)  # type: ignore

    r = client.get("/api/stock-by-provider", headers={"X-API-Key": "secret"})
    assert r.status_code == 200
    data = r.json()
    # Debe provenir del fallback (ordenado por total_productos)
    assert data[0]["codigo"] == "A" and data[0]["stock_total"] == 50


def test_export_summary_error_branch(monkeypatch):
    """Cubre la rama de export CSV cuando summary retorna error."""
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    monkeypatch.setattr(mod.analytics, "get_dashboard_summary", lambda: {"error": "fallo simulado"})  # type: ignore
    r = client.get("/api/export/summary.csv", headers={"X-API-Key": "secret"})
    assert r.status_code == 200
    body = r.text.splitlines()
    assert body[0] == "error,message"
    assert body[1].startswith("true,fallo simulado")


def test_metrics_labels_after_requests(monkeypatch):
    """Verifica que /metrics refleje paths usados (cubre loop de formateo)."""
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    # Generar algunas requests
    for _ in range(2):
        client.get("/api/summary", headers={"X-API-Key": "secret"})
        client.get("/api/providers", headers={"X-API-Key": "secret"})

    r = client.get("/metrics", headers={"X-API-Key": "secret"})
    assert r.status_code == 200
    text = r.text
    assert 'dashboard_requests_by_path_total{path="/api/summary"}' in text
    assert 'dashboard_requests_by_path_total{path="/api/providers"}' in text


def test_export_top_products_error_branch(monkeypatch):
    """Fuerza la rama de error en export top-products cuando la función devuelve lista con error."""
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    monkeypatch.setattr(mod.analytics, "get_top_products", lambda *a, **k: [{"error": "x"}])  # type: ignore
    r = client.get("/api/export/top-products.csv", headers={"X-API-Key": "secret"})
    assert r.status_code == 200
    lines = r.text.splitlines()
    assert lines[0] == "error,message"
    assert lines[1].startswith("true,x")
