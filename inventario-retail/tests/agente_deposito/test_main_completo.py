"""
Tests para API Principal - Sistema Gestión Depósito
Tests completos para todos los endpoints con pytest
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Imports del proyecto
from agente_deposito.main import app
from agente_deposito.database import get_database_session, Base
from agente_deposito.models import Producto, MovimientoStock

# Configuración de base de datos de testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override de la dependencia de base de datos para testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_database_session] = override_get_db

class TestSetup:
    """Clase para configuración de tests"""

    @staticmethod
    def setup_database():
        """Crear tablas de test"""
        Base.metadata.create_all(bind=engine)

    @staticmethod
    def teardown_database():
        """Eliminar tablas de test"""
        Base.metadata.drop_all(bind=engine)

    @staticmethod
    def create_test_producto(db, codigo="TEST001"):
        """Crear producto de prueba"""
        producto = Producto(
            codigo=codigo,
            nombre="Producto Test",
            descripcion="Descripción test",
            categoria="TEST",
            marca="Test Brand",
            modelo="Test Model",
            precio_costo=Decimal("100.00"),
            precio_venta=Decimal("150.00"),
            precio_mayorista=Decimal("140.00"),
            stock_actual=10,
            stock_minimo=5,
            stock_maximo=50,
            ubicacion_deposito="TEST-001",
            peso_kg=Decimal("1.5"),
            dimensiones="10x10x10",
            activo=True,
            usuario_creacion="TEST_USER"
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto

@pytest.fixture(scope="module")
def client():
    """Cliente de testing para FastAPI"""
    TestSetup.setup_database()
    with TestClient(app) as c:
        yield c
    TestSetup.teardown_database()

@pytest.fixture
def test_db():
    """Sesión de base de datos para testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestProductosEndpoints:
    """Tests para endpoints de productos"""

    def test_create_producto_success(self, client, test_db):
        """Test crear producto exitosamente"""
        producto_data = {
            "codigo": "TEST001",
            "nombre": "Producto Test",
            "descripcion": "Descripción test",
            "categoria": "TEST",
            "marca": "Test Brand",
            "modelo": "Test Model",
            "precio_costo": 100.00,
            "precio_venta": 150.00,
            "precio_mayorista": 140.00,
            "stock_actual": 10,
            "stock_minimo": 5,
            "stock_maximo": 50,
            "ubicacion_deposito": "TEST-001",
            "peso_kg": 1.5,
            "dimensiones": "10x10x10",
            "activo": True,
            "usuario_creacion": "TEST_USER"
        }

        response = client.post("/productos", json=producto_data)

        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "TEST001"
        assert data["nombre"] == "Producto Test"
        assert data["stock_actual"] == 10
        assert "id" in data
        assert "fecha_creacion" in data

    def test_create_producto_duplicate_codigo(self, client, test_db):
        """Test crear producto con código duplicado"""
        # Crear primer producto
        TestSetup.create_test_producto(test_db, "DUPLICATE001")

        # Intentar crear producto con mismo código
        producto_data = {
            "codigo": "DUPLICATE001",
            "nombre": "Producto Duplicado",
            "categoria": "TEST",
            "precio_costo": 100.00,
            "precio_venta": 150.00,
            "stock_actual": 5,
            "stock_minimo": 2
        }

        response = client.post("/productos", json=producto_data)

        assert response.status_code == 400
        assert "Ya existe un producto con código" in response.json()["detail"]

    def test_create_producto_invalid_data(self, client):
        """Test crear producto con datos inválidos"""
        producto_data = {
            "codigo": "T",  # Muy corto
            "nombre": "Te",  # Muy corto
            "categoria": "TEST",
            "precio_costo": -10.00,  # Negativo
            "precio_venta": 0,  # Cero
            "stock_actual": -5,  # Negativo
            "stock_minimo": -1  # Negativo
        }

        response = client.post("/productos", json=producto_data)

        assert response.status_code == 422  # Validation error

    def test_list_productos_empty(self, client):
        """Test listar productos cuando no hay ninguno"""
        response = client.get("/productos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["pages"] == 0

    def test_list_productos_with_data(self, client, test_db):
        """Test listar productos con datos"""
        # Crear varios productos de prueba
        for i in range(5):
            TestSetup.create_test_producto(test_db, f"LIST{i:03d}")

        response = client.get("/productos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["pages"] == 1

    def test_list_productos_with_filters(self, client, test_db):
        """Test listar productos con filtros"""
        # Crear productos con diferentes categorías
        producto1 = TestSetup.create_test_producto(test_db, "FILTER001")
        producto1.categoria = "ELECTRODOMESTICOS"
        producto1.stock_actual = 2  # Stock crítico

        producto2 = TestSetup.create_test_producto(test_db, "FILTER002") 
        producto2.categoria = "TECNOLOGIA"
        producto2.stock_actual = 20  # Stock normal

        test_db.commit()

        # Test filtro por categoría
        response = client.get("/productos?categoria=ELECTRODOMESTICOS")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["categoria"] == "ELECTRODOMESTICOS"

        # Test filtro por stock crítico
        response = client.get("/productos?stock_critico=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["stock_critico"] == True

    def test_list_productos_pagination(self, client, test_db):
        """Test paginación de productos"""
        # Crear 25 productos
        for i in range(25):
            TestSetup.create_test_producto(test_db, f"PAGE{i:03d}")

        # Test primera página
        response = client.get("/productos?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["pages"] == 3

        # Test segunda página
        response = client.get("/productos?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

        # Test última página
        response = client.get("/productos?page=3&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 3

    def test_get_producto_success(self, client, test_db):
        """Test obtener producto específico"""
        producto = TestSetup.create_test_producto(test_db, "GET001")

        response = client.get(f"/productos/{producto.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == producto.id
        assert data["codigo"] == "GET001"
        assert data["nombre"] == "Producto Test"

    def test_get_producto_not_found(self, client):
        """Test obtener producto inexistente"""
        response = client.get("/productos/99999")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_update_producto_success(self, client, test_db):
        """Test actualizar producto exitosamente"""
        producto = TestSetup.create_test_producto(test_db, "UPDATE001")

        update_data = {
            "nombre": "Producto Actualizado",
            "precio_venta": 200.00,
            "stock_minimo": 10
        }

        response = client.put(f"/productos/{producto.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Producto Actualizado"
        assert data["precio_venta"] == 200.00
        assert data["stock_minimo"] == 10
        assert "fecha_modificacion" in data

    def test_update_producto_not_found(self, client):
        """Test actualizar producto inexistente"""
        update_data = {"nombre": "No existe"}

        response = client.put("/productos/99999", json=update_data)

        assert response.status_code == 404

    def test_update_producto_duplicate_codigo(self, client, test_db):
        """Test actualizar producto con código duplicado"""
        producto1 = TestSetup.create_test_producto(test_db, "DUP001")
        producto2 = TestSetup.create_test_producto(test_db, "DUP002")

        update_data = {"codigo": "DUP001"}  # Código que ya existe

        response = client.put(f"/productos/{producto2.id}", json=update_data)

        assert response.status_code == 400
        assert "Ya existe otro producto" in response.json()["detail"]

    def test_delete_producto_success(self, client, test_db):
        """Test eliminar producto exitosamente"""
        producto = TestSetup.create_test_producto(test_db, "DELETE001")

        response = client.delete(f"/productos/{producto.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "eliminado" in data["message"] or "desactivado" in data["message"]

    def test_delete_producto_not_found(self, client):
        """Test eliminar producto inexistente"""
        response = client.delete("/productos/99999")

        assert response.status_code == 404

class TestStockEndpoints:
    """Tests para endpoints de stock"""

    def test_update_stock_entrada_success(self, client, test_db):
        """Test actualización de stock - entrada exitosa"""
        producto = TestSetup.create_test_producto(test_db, "STOCK001")

        stock_data = {
            "producto_id": producto.id,
            "cantidad": 5,
            "tipo_movimiento": "ENTRADA",
            "subtipo": "COMPRA",
            "precio_unitario": 100.00,
            "documento_referencia": "FC-001",
            "usuario": "TEST_USER",
            "observaciones": "Test entrada stock"
        }

        response = client.post("/stock/update", json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["producto_id"] == producto.id
        assert data["stock_anterior"] == 10
        assert data["stock_nuevo"] == 15
        assert "movimiento_id" in data

    def test_update_stock_salida_success(self, client, test_db):
        """Test actualización de stock - salida exitosa"""
        producto = TestSetup.create_test_producto(test_db, "STOCK002")

        stock_data = {
            "producto_id": producto.id,
            "cantidad": 3,
            "tipo_movimiento": "SALIDA",
            "subtipo": "VENTA",
            "precio_unitario": 150.00,
            "documento_referencia": "FC-002",
            "usuario": "TEST_USER",
            "observaciones": "Test salida stock"
        }

        response = client.post("/stock/update", json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["stock_anterior"] == 10
        assert data["stock_nuevo"] == 7

    def test_update_stock_insufficient(self, client, test_db):
        """Test actualización de stock - stock insuficiente"""
        producto = TestSetup.create_test_producto(test_db, "STOCK003")

        stock_data = {
            "producto_id": producto.id,
            "cantidad": 15,  # Más que el stock disponible (10)
            "tipo_movimiento": "SALIDA",
            "subtipo": "VENTA",
            "usuario": "TEST_USER"
        }

        response = client.post("/stock/update", json=stock_data)

        assert response.status_code == 400
        assert "insuficiente" in response.json()["detail"].lower()

    def test_update_stock_producto_not_found(self, client):
        """Test actualización de stock - producto inexistente"""
        stock_data = {
            "producto_id": 99999,
            "cantidad": 5,
            "tipo_movimiento": "ENTRADA",
            "usuario": "TEST_USER"
        }

        response = client.post("/stock/update", json=stock_data)

        assert response.status_code == 404

    def test_get_stock_movements_empty(self, client):
        """Test obtener movimientos cuando no hay ninguno"""
        response = client.get("/stock/movements")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_stock_movements_with_data(self, client, test_db):
        """Test obtener movimientos con datos"""
        producto = TestSetup.create_test_producto(test_db, "MOVES001")

        # Crear algunos movimientos
        for i in range(3):
            stock_data = {
                "producto_id": producto.id,
                "cantidad": 1,
                "tipo_movimiento": "ENTRADA",
                "usuario": "TEST_USER"
            }
            client.post("/stock/update", json=stock_data)

        response = client.get("/stock/movements")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3  # Al menos los 3 que creamos
        assert len(data["items"]) >= 3

    def test_get_stock_movements_with_filters(self, client, test_db):
        """Test obtener movimientos con filtros"""
        producto = TestSetup.create_test_producto(test_db, "FILTER001")

        # Crear movimiento específico
        stock_data = {
            "producto_id": producto.id,
            "cantidad": 5,
            "tipo_movimiento": "ENTRADA",
            "usuario": "FILTER_USER",
            "documento_referencia": "FILTER-001"
        }
        client.post("/stock/update", json=stock_data)

        # Test filtro por producto
        response = client.get(f"/stock/movements?producto_id={producto.id}")
        assert response.status_code == 200
        data = response.json()
        assert all(item["producto_id"] == producto.id for item in data["items"])

        # Test filtro por tipo movimiento
        response = client.get("/stock/movements?tipo_movimiento=ENTRADA")
        assert response.status_code == 200
        data = response.json()
        assert all(item["tipo_movimiento"] == "ENTRADA" for item in data["items"])

    def test_get_critical_stock_empty(self, client):
        """Test obtener stock crítico cuando no hay productos críticos"""
        response = client.get("/stock/critical")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_critical_stock_with_data(self, client, test_db):
        """Test obtener stock crítico con productos"""
        # Crear producto con stock crítico
        producto = TestSetup.create_test_producto(test_db, "CRIT001")
        producto.stock_actual = 2  # Menor que stock_minimo (5)
        test_db.commit()

        response = client.get("/stock/critical")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        # Verificar que incluye nuestro producto crítico
        codigos_criticos = [item["codigo"] for item in data]
        assert "CRIT001" in codigos_criticos

    def test_get_stock_summary(self, client, test_db):
        """Test obtener resumen de stock"""
        # Crear algunos productos de prueba
        TestSetup.create_test_producto(test_db, "SUM001")

        producto_critico = TestSetup.create_test_producto(test_db, "SUM002")
        producto_critico.stock_actual = 1  # Crítico
        test_db.commit()

        response = client.get("/stock/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_productos" in data
        assert "productos_stock_critico" in data
        assert "valor_total_inventario" in data
        assert "productos_sin_stock" in data
        assert isinstance(data["categorias_con_stock_critico"], list)

class TestHealthEndpoint:
    """Tests para endpoint de health check"""

    def test_health_check_success(self, client):
        """Test health check exitoso"""
        response = client.get("/health")

        assert response.status_code == 200 or response.status_code == 503
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "version" in data

class TestErrorHandling:
    """Tests para manejo de errores"""

    def test_invalid_endpoint(self, client):
        """Test endpoint inexistente"""
        response = client.get("/invalid/endpoint")

        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test método HTTP no permitido"""
        response = client.patch("/productos")  # PATCH no está definido

        assert response.status_code == 405

    def test_invalid_json(self, client):
        """Test JSON inválido"""
        response = client.post(
            "/productos", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
