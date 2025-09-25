import os
from pathlib import Path
import importlib.util
import importlib.machinery
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
dashboard_path = ROOT / "inventario-retail" / "web_dashboard" / "dashboard_app.py"
loader = importlib.machinery.SourceFileLoader("dashboard_app_additional", str(dashboard_path))
spec = importlib.util.spec_from_loader("dashboard_app_additional", loader)
assert spec is not None
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)  # type: ignore

app = module.app
client = TestClient(app, raise_server_exceptions=False)


def test_api_key_enforcement(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    # Sin header -> 401
    r = client.get("/api/summary")
    assert r.status_code == 401
    # Header incorrecto -> 401
    r = client.get("/api/summary", headers={"X-API-Key": "otra"})
    assert r.status_code == 401
    # Correcto -> 200
    r = client.get("/api/summary", headers={"X-API-Key": "secret"})
    assert r.status_code == 200


def test_global_exception_handler_api(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    # Forzar excepción en la función usada por /api/summary
    def boom():
        raise RuntimeError("fallo forzado")
    original = module.analytics.get_dashboard_summary  # type: ignore
    monkeypatch.setattr(module.analytics, "get_dashboard_summary", boom)  # type: ignore
    try:
        r = client.get("/api/summary", headers={"X-API-Key": "secret"})
        assert r.status_code == 500
        assert r.json().get("error") == "Error interno"
    finally:
        # Restaurar para otros tests
        monkeypatch.setattr(module.analytics, "get_dashboard_summary", original)  # type: ignore


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret")
    monkeypatch.setenv("DASHBOARD_RATELIMIT_ENABLED", "true")
    monkeypatch.setenv("DASHBOARD_RATELIMIT_MAX", "1")
    monkeypatch.setenv("DASHBOARD_RATELIMIT_WINDOW", "60")
    # Limpiar contadores
    module._rate_counters.clear()  # type: ignore
    ok = client.get("/api/summary", headers={"X-API-Key": "secret"})
    assert ok.status_code == 200
    limited = client.get("/api/summary", headers={"X-API-Key": "secret"})
    assert limited.status_code == 429
    assert limited.json().get("error") == "Rate limit excedido"


def test_sanitize_helpers():
    # Importar helpers desde el módulo dinámico ya cargado
    sanitize_date = module.sanitize_date  # type: ignore
    sanitize_text = module.sanitize_text  # type: ignore
    clamp_int = module.clamp_int  # type: ignore
    assert sanitize_date(None) is None
    assert sanitize_date("") is None
    assert sanitize_date("2025/01/01") is None  # formato inválido
    assert sanitize_date("2025-02-30") is None  # fecha inválida
    assert sanitize_date("2025-02-28") == "2025-02-28"

    # sanitize_text (elimina caracteres no permitidos y corta longitud)
    assert sanitize_text("hola<script>") == "holascript"
    largo = "x" * 120
    assert len(sanitize_text(largo, max_len=50)) == 50

    # clamp_int
    assert clamp_int("5", 1, 10) == 5
    assert clamp_int("abc", 1, 10) == 1  # fallback a min
    assert clamp_int(999, 1, 10) == 10  # clamp superior
    assert clamp_int(-5, 1, 10) == 1  # clamp inferior
