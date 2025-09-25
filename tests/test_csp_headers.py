import os
import sys
import importlib.machinery
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

os.environ.setdefault("DASHBOARD_API_KEY", "test-key")

# Añadir raíz del proyecto al PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# El paquete contiene un directorio con guion, usamos importlib.machinery.SourceFileLoader
dashboard_path = ROOT / "inventario-retail" / "web_dashboard" / "dashboard_app.py"
spec_name = "dashboard_app_dynamic"
loader = importlib.machinery.SourceFileLoader(spec_name, str(dashboard_path))
spec = importlib.util.spec_from_loader(spec_name, loader)
module = importlib.util.module_from_spec(spec)  # type: ignore
loader.exec_module(module)  # type: ignore
app = getattr(module, "app")
client = TestClient(app)


def test_csp_header_present_and_strict():
    r = client.get("/")
    csp = r.headers.get("content-security-policy")
    assert csp is not None, "CSP header debe existir"
    assert "unsafe-inline" not in csp.lower(), "No debe contener 'unsafe-inline' tras refactor"
    assert "script-src 'self' https://cdn.jsdelivr.net" in csp
    assert "media-src 'self' https://cdn.pixabay.com" in csp


def test_no_inline_scripts_in_templates():
    r = client.get("/")
    html = r.text
    # Permitimos <script type="application/json"> para datos
    # Buscamos patrones <script> ... </script> sin atributos que indiquen src o type json
    import re
    inline_blocks = re.findall(r"<script(?![^>]*src)(?![^>]*application/json)[^>]*>\\s*[^<]+</script>", html, flags=re.IGNORECASE)
    assert not inline_blocks, f"Se encontraron scripts inline no permitidos: {inline_blocks[:2]}"


def test_csp_snapshot_policy():
    """Asegura que la política CSP completa no cambie sin revisión.

    Si se requiere modificar la CSP (nuevos CDNs, directivas, etc.) actualizar
    la cadena expected_csp abajo y documentar la justificación en DOCUMENTACION_CI_CD.md.
    """
    r = client.get("/")
    csp = r.headers.get("content-security-policy")
    assert csp, "Header CSP ausente"
    expected_csp = (
        "default-src 'self'; "
        "img-src 'self' data: https://cdn.jsdelivr.net https://cdn.pixabay.com; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net data:; "
        "media-src 'self' https://cdn.pixabay.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'"
    )
    # Comparamos exacto; si difiere, mostramos diff amigable
    if csp != expected_csp:
        import difflib
        diff = '\n'.join(difflib.unified_diff(expected_csp.split(), csp.split(), fromfile='expected', tofile='actual', lineterm=''))
        raise AssertionError(f"La política CSP ha cambiado. Actualiza el snapshot si es intencional. Diff:\n{diff}")


def test_hsts_header_when_enabled(monkeypatch):
    """Verifica que Strict-Transport-Security se añade cuando se activa el flag.

    El middleware revisa la variable de entorno en cada request, por lo que basta
    con definirla antes del GET. No validamos el header si no está activado aquí; ese
    caso se cubre indirectamente por ausencia en otros tests.
    """
    monkeypatch.setenv("DASHBOARD_ENABLE_HSTS", "true")
    r = client.get("/")
    hsts = r.headers.get("strict-transport-security")
    assert hsts is not None and "max-age=" in hsts
