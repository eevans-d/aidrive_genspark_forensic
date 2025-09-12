"""
Tests para AgenteDepósito
"""
import pytest
from fastapi.testclient import TestClient
from agente_deposito.main import app

client = TestClient(app)

def test_health_check():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_crear_producto():
    """Test crear producto"""
    producto_data = {
        "codigo": "TEST001",
        "nombre": "Producto Test",
        "categoria": "Test",
        "precio_compra": 100.0,
        "stock_actual": 50,
        "stock_minimo": 10
    }

    response = client.post("/productos", json=producto_data)
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "TEST001"

def test_listar_productos():
    """Test listar productos"""
    response = client.get("/productos")
    assert response.status_code == 200
    data = response.json()
    assert "productos" in data
    assert "total" in data
