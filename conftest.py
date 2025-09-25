import os
from pathlib import Path

IGNORED_PATTERNS = [
    str(Path('inventario-retail/tests/agente_deposito')),  # servicios depósito fuera de alcance
    str(Path('inventario-retail/tests/integration')),      # integraciones completas fuera de fase
    str(Path('sistema_deposito_semana1/tests')),          # versiones legacy
    str(Path('vibe_production_system/components/learning_system/tests')),  # sistema aprendizaje
    str(Path('inventario-retail/tests/test_config.py')),  # test de config global que dispara paths legacy
    'matplotlib/tests',
]

def pytest_ignore_collect(path):  # type: ignore
    p = str(path)
    for pattern in IGNORED_PATTERNS:
        if pattern in p:
            return True
    return False
