# Forzar que matplotlib no cargue su paquete de tests ni backend interactivo durante la colección.
import os
os.environ.setdefault("MPLBACKEND", "Agg")

def pytest_ignore_collect(path):  # type: ignore
    p = str(path)
    if "matplotlib/tests" in p:
        return True
    return False
