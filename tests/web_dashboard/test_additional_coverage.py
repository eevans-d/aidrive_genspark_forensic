import sys
import types
import runpy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "inventario-retail" / "web_dashboard" / "dashboard_app.py"


def _load_app_module():
    spec = importlib.util.spec_from_file_location("dashboard_app_cov", str(APP_PATH))
    assert spec is not None  # asegurar para tipado
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore
    return mod


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("DASHBOARD_API_KEY", "test-key")
    monkeypatch.setenv("DASHBOARD_RATELIMIT_MAX", "10000")
    yield


def test_monthly_trends_cached_path():
    """Ejecuta get_monthly_trends_cached dos veces para cubrir rama de cache hit."""
    mod = _load_app_module()
    analytics = mod.analytics
    first = analytics.get_monthly_trends_cached(6, None, None, None)
    second = analytics.get_monthly_trends_cached(6, None, None, None)
    # La segunda llamada debe devolver exactamente lo mismo (cache hit)
    assert first == second


def test_main_block_execution(monkeypatch):
    """Ejecuta el bloque __main__ sustituyendo uvicorn.run para cubrir líneas finales."""
    called = {}

    def fake_run(app_path, host, port, reload):  # firma similar a la usada
        called["ran"] = True
        # Validar parámetros esenciales sin arrancar servidor real
        assert host == "0.0.0.0"
        assert port == 8080

    # Inyectar módulo uvicorn simulado antes de ejecutar el script como __main__
    monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=fake_run))

    # Ejecutar el archivo como script (__name__ == "__main__") para cubrir impresión y llamada
    runpy.run_path(str(APP_PATH), run_name="__main__")

    assert called.get("ran") is True
