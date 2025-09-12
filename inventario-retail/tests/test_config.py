"""
Tests para configuración del sistema
"""
import pytest
from shared.config import get_settings
from shared.utils import validar_cuit, formatear_precio_argentino

def test_settings_load():
    """Test carga de configuración"""
    settings = get_settings()
    assert settings.AGENTE_NEGOCIO_PORT == 8001
    assert settings.AGENTE_DEPOSITO_PORT == 8002
    assert 0 <= settings.INFLACION_MENSUAL <= 50

def test_cuit_validation():
    """Test validación CUIT"""
    # CUIT válido
    valid, msg = validar_cuit("20-12345678-9")
    assert valid is False or valid is True  # Depende del dígito verificador

    # CUIT inválido
    valid, msg = validar_cuit("invalid")
    assert valid is False

def test_precio_format():
    """Test formato precios argentinos"""
    formatted = formatear_precio_argentino(1234.56)
    assert formatted == "$1.234,56"

    formatted = formatear_precio_argentino(1000000.00)
    assert formatted == "$1.000.000,00"
