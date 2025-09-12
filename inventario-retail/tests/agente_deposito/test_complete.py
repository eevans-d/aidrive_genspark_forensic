"""
Test Suite Completa para AgenteDepósito
Versión: 2.0 - Production Ready

Tests completos para:
- Todos los endpoints CRUD
- Operaciones de stock ACID
- Validaciones de negocio
- Escenarios de error
- Performance básico
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importaciones del sistema
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agente_deposito.main_complete import app
from agente_deposito.dependencies import get_database
from agente_deposito.models import Base, Producto, MovimientoStock
from agente_deposito.schemas import TipoMovimiento

# Configuración de base de datos de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agente_deposito.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency
def override_get_database():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_database] = override_get_database

# Cliente de test
client = TestClient(app)

# === FIXTURES ===

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture para sesión de base de datos de test
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_producto_data():
    """
    Fixture con datos de producto de ejemplo
    """
    return {
        "codigo": "TEST001",
        "nombre": "Producto Test",
        "descripcion": "Producto para testing",
        "precio": 100.50,
        "stock_actual": 50,
        "stock_minimo": 10,
        "stock_maximo": 200,
        "categoria": "Test",
        "ubicacion": "A1-01",
        "activo": True
    }

@pytest.fixture
def sample_producto_update():
    """
    Fixture con datos de actualización de producto
    """
    return {
        "nombre": "Producto Test Actualizado",
        "precio": 120.75,
        "descripcion": "Producto actualizado para testing"
    }

# === TESTS DE HEALTH CHECK ===

class TestHealthCheck:
    """
    Tests para endpoints de health check
    """

    def test_health_check_basic(self):
        """
        Test del health check básico
        """
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "system" in data["components"]

    def test_health_check_detailed(self):
        """
        Test del health check detallado
        """
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["version"] == "2.0.0"
        assert "database" in data
        assert "system" in data
        assert "endpoints" in data

# === TESTS DE PRODUCTOS ===

class TestProductos:
    """
    Tests completos para endpoints de productos
    """

    def test_create_producto_success(self, sample_producto_data):
        """
        Test crear producto exitoso
        """
        response = client.post("/api/v1/productos", json=sample_producto_data)
        assert response.status_code == 201

        data = response.json()
        assert data["codigo"] == sample_producto_data["codigo"]
        assert data["nombre"] == sample_producto_data["nombre"]
        assert data["precio"] == sample_producto_data["precio"]
        assert data["stock_actual"] == sample_producto_data["stock_actual"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_producto_duplicate_codigo(self, sample_producto_data):
        """
        Test crear producto con código duplicado
        """
        # Crear producto inicial
        client.post("/api/v1/productos", json=sample_producto_data)

        # Intentar crear otro con mismo código
        response = client.post("/api/v1/productos", json=sample_producto_data)
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "Ya existe un producto" in str(data)

    def test_create_producto_invalid_data(self):
        """
        Test crear producto con datos inválidos
        """
        invalid_data = {
            "codigo": "",  # Código vacío
            "nombre": "Test",
            "precio": -10,  # Precio negativo
            "stock_minimo": 100,
            "stock_maximo": 50  # Stock máximo menor que mínimo
        }

        response = client.post("/api/v1/productos", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_producto_success(self, sample_producto_data):
        """
        Test obtener producto exitoso
        """
        # Crear producto
        create_response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = create_response.json()["id"]

        # Obtener producto
        response = client.get(f"/api/v1/productos/{producto_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == producto_id
        assert data["codigo"] == sample_producto_data["codigo"]

    def test_get_producto_not_found(self):
        """
        Test obtener producto inexistente
        """
        response = client.get("/api/v1/productos/99999")
        assert response.status_code == 404

    def test_get_producto_by_codigo_success(self, sample_producto_data):
        """
        Test obtener producto por código exitoso
        """
        # Crear producto
        client.post("/api/v1/productos", json=sample_producto_data)

        # Obtener por código
        response = client.get(f"/api/v1/productos/codigo/{sample_producto_data['codigo']}")
        assert response.status_code == 200

        data = response.json()
        assert data["codigo"] == sample_producto_data["codigo"]

    def test_get_producto_by_codigo_not_found(self):
        """
        Test obtener producto por código inexistente
        """
        response = client.get("/api/v1/productos/codigo/NOEXISTE")
        assert response.status_code == 404

    def test_update_producto_success(self, sample_producto_data, sample_producto_update):
        """
        Test actualizar producto exitoso
        """
        # Crear producto
        create_response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = create_response.json()["id"]

        # Actualizar producto
        response = client.put(f"/api/v1/productos/{producto_id}", json=sample_producto_update)
        assert response.status_code == 200

        data = response.json()
        assert data["nombre"] == sample_producto_update["nombre"]
        assert data["precio"] == sample_producto_update["precio"]
        # Campos no actualizados deben mantener valores originales
        assert data["codigo"] == sample_producto_data["codigo"]

    def test_update_producto_not_found(self, sample_producto_update):
        """
        Test actualizar producto inexistente
        """
        response = client.put("/api/v1/productos/99999", json=sample_producto_update)
        assert response.status_code == 404

    def test_delete_producto_success(self, sample_producto_data):
        """
        Test eliminar producto exitoso (sin stock)
        """
        # Crear producto sin stock
        sample_producto_data["stock_actual"] = 0
        create_response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = create_response.json()["id"]

        # Eliminar producto
        response = client.delete(f"/api/v1/productos/{producto_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "eliminado exitosamente" in data["message"]

    def test_delete_producto_with_stock(self, sample_producto_data):
        """
        Test eliminar producto con stock (debe fallar)
        """
        # Crear producto con stock
        create_response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = create_response.json()["id"]

        # Intentar eliminar
        response = client.delete(f"/api/v1/productos/{producto_id}")
        assert response.status_code == 400

        data = response.json()
        assert "stock existente" in str(data).lower()

    def test_list_productos_pagination(self, sample_producto_data):
        """
        Test listar productos con paginación
        """
        # Crear múltiples productos
        for i in range(5):
            producto_data = sample_producto_data.copy()
            producto_data["codigo"] = f"TEST{i:03d}"
            producto_data["nombre"] = f"Producto Test {i}"
            client.post("/api/v1/productos", json=producto_data)

        # Obtener primera página
        response = client.get("/api/v1/productos?page=1&size=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["size"] == 3
        assert data["total"] == 5
        assert data["pages"] == 2

    def test_list_productos_filters(self, sample_producto_data):
        """
        Test listar productos con filtros
        """
        # Crear productos con diferentes categorías
        for i, categoria in enumerate(["Electronics", "Books", "Clothing"]):
            producto_data = sample_producto_data.copy()
            producto_data["codigo"] = f"TEST{i:03d}"
            producto_data["categoria"] = categoria
            client.post("/api/v1/productos", json=producto_data)

        # Filtrar por categoría
        response = client.get("/api/v1/productos?categoria=Electronics")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["categoria"] == "Electronics"

    def test_search_productos(self, sample_producto_data):
        """
        Test búsqueda de productos
        """
        # Crear productos
        productos = [
            {"codigo": "LAPTOP001", "nombre": "Laptop Gaming"},
            {"codigo": "MOUSE001", "nombre": "Mouse Gamer"},
            {"codigo": "BOOK001", "nombre": "Programming Book"}
        ]

        for producto in productos:
            producto_data = sample_producto_data.copy()
            producto_data.update(producto)
            client.post("/api/v1/productos", json=producto_data)

        # Buscar por término
        response = client.get("/api/v1/productos/search?q=gaming")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1  # Solo "Laptop Gaming" debería coincidir
        assert "gaming" in data[0]["nombre"].lower()

# === TESTS DE STOCK ===

class TestStock:
    """
    Tests completos para operaciones de stock
    """

    @pytest.fixture
    def producto_with_stock(self, sample_producto_data):
        """
        Fixture que crea un producto con stock
        """
        response = client.post("/api/v1/productos", json=sample_producto_data)
        return response.json()

    def test_update_stock_success(self, producto_with_stock):
        """
        Test actualizar stock exitoso
        """
        stock_request = {
            "producto_id": producto_with_stock["id"],
            "nueva_cantidad": 75,
            "motivo": "Ajuste de inventario",
            "usuario": "test_user"
        }

        response = client.put("/api/v1/stock/update", json=stock_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["producto"]["stock_actual"] == 75
        assert data["movimiento_id"] is not None

    def test_update_stock_producto_not_found(self):
        """
        Test actualizar stock de producto inexistente
        """
        stock_request = {
            "producto_id": 99999,
            "nueva_cantidad": 75,
            "motivo": "Test",
            "usuario": "test_user"
        }

        response = client.put("/api/v1/stock/update", json=stock_request)
        assert response.status_code == 404

    def test_adjust_stock_positive(self, producto_with_stock):
        """
        Test ajustar stock positivo
        """
        initial_stock = producto_with_stock["stock_actual"]

        adjust_request = {
            "producto_id": producto_with_stock["id"],
            "cantidad_ajuste": 25,
            "motivo": "Recepción de mercancía",
            "usuario": "test_user"
        }

        response = client.put("/api/v1/stock/adjust", json=adjust_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["producto"]["stock_actual"] == initial_stock + 25
        assert data["movimiento"]["tipo"] == "ENTRADA"

    def test_adjust_stock_negative(self, producto_with_stock):
        """
        Test ajustar stock negativo
        """
        initial_stock = producto_with_stock["stock_actual"]

        adjust_request = {
            "producto_id": producto_with_stock["id"],
            "cantidad_ajuste": -15,
            "motivo": "Corrección de inventario",
            "usuario": "test_user"
        }

        response = client.put("/api/v1/stock/adjust", json=adjust_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["producto"]["stock_actual"] == initial_stock - 15
        assert data["movimiento"]["tipo"] == "SALIDA"

    def test_adjust_stock_insufficient(self, producto_with_stock):
        """
        Test ajustar stock con cantidad insuficiente
        """
        initial_stock = producto_with_stock["stock_actual"]

        adjust_request = {
            "producto_id": producto_with_stock["id"],
            "cantidad_ajuste": -(initial_stock + 100),  # Más de lo disponible
            "motivo": "Test insuficiente",
            "usuario": "test_user"
        }

        response = client.put("/api/v1/stock/adjust", json=adjust_request)
        assert response.status_code == 400

        data = response.json()
        assert "stock negativo" in str(data).lower()

    def test_process_movement_entrada(self, producto_with_stock):
        """
        Test procesar movimiento de entrada
        """
        initial_stock = producto_with_stock["stock_actual"]

        movement_request = {
            "producto_id": producto_with_stock["id"],
            "tipo_movimiento": "ENTRADA",
            "cantidad": 30,
            "motivo": "Compra",
            "referencia": "FACT-001",
            "usuario": "test_user"
        }

        response = client.post("/api/v1/stock/movement", json=movement_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["producto"]["stock_actual"] == initial_stock + 30
        assert data["movimiento"]["tipo"] == "ENTRADA"
        assert data["movimiento"]["cantidad"] == 30

    def test_process_movement_salida(self, producto_with_stock):
        """
        Test procesar movimiento de salida
        """
        initial_stock = producto_with_stock["stock_actual"]

        movement_request = {
            "producto_id": producto_with_stock["id"],
            "tipo_movimiento": "SALIDA",
            "cantidad": 20,
            "motivo": "Venta",
            "referencia": "VENTA-001",
            "usuario": "test_user"
        }

        response = client.post("/api/v1/stock/movement", json=movement_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["producto"]["stock_actual"] == initial_stock - 20
        assert data["movimiento"]["tipo"] == "SALIDA"

    def test_process_movement_salida_insufficient(self, producto_with_stock):
        """
        Test procesar salida con stock insuficiente
        """
        initial_stock = producto_with_stock["stock_actual"]

        movement_request = {
            "producto_id": producto_with_stock["id"],
            "tipo_movimiento": "SALIDA",
            "cantidad": initial_stock + 100,  # Más de lo disponible
            "motivo": "Test insuficiente",
            "usuario": "test_user"
        }

        response = client.post("/api/v1/stock/movement", json=movement_request)
        assert response.status_code == 400

        data = response.json()
        assert "insuficiente" in str(data).lower()

    def test_get_stock_critico(self, sample_producto_data):
        """
        Test obtener productos con stock crítico
        """
        # Crear producto con stock crítico
        producto_data = sample_producto_data.copy()
        producto_data["stock_actual"] = 5  # Menor que stock_minimo (10)
        producto_data["codigo"] = "CRITICO001"
        client.post("/api/v1/productos", json=producto_data)

        # Crear producto con stock normal
        producto_data["stock_actual"] = 50
        producto_data["codigo"] = "NORMAL001"
        client.post("/api/v1/productos", json=producto_data)

        response = client.get("/api/v1/stock/critical")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["productos"]) == 1
        assert data["productos"][0]["codigo"] == "CRITICO001"

    def test_get_stock_movements_history(self, producto_with_stock):
        """
        Test obtener historial de movimientos
        """
        # Realizar algunos movimientos
        movements = [
            {"tipo_movimiento": "ENTRADA", "cantidad": 10, "motivo": "Compra 1"},
            {"tipo_movimiento": "SALIDA", "cantidad": 5, "motivo": "Venta 1"},
            {"tipo_movimiento": "ENTRADA", "cantidad": 15, "motivo": "Compra 2"}
        ]

        for movement in movements:
            movement["producto_id"] = producto_with_stock["id"]
            movement["usuario"] = "test_user"
            client.post("/api/v1/stock/movement", json=movement)

        # Obtener historial
        response = client.get(f"/api/v1/stock/movements?producto_id={producto_with_stock['id']}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["movimientos"]) >= 3  # Al menos los 3 movimientos + stock inicial
        assert data["total"] >= 3

# === TESTS DE REPORTES ===

class TestReportes:
    """
    Tests para endpoints de reportes
    """

    def test_generate_stock_report(self, sample_producto_data):
        """
        Test generar reporte de stock
        """
        # Crear algunos productos
        for i in range(3):
            producto_data = sample_producto_data.copy()
            producto_data["codigo"] = f"REPORT{i:03d}"
            client.post("/api/v1/productos", json=producto_data)

        response = client.get("/api/v1/reportes/stock")
        assert response.status_code == 200

        data = response.json()
        assert "total_productos" in data
        assert "productos_activos" in data
        assert "productos_stock_critico" in data
        assert "productos_sobrestock" in data
        assert "valor_total_inventario" in data
        assert "fecha_reporte" in data
        assert data["total_productos"] >= 3

    def test_get_top_movimientos(self, sample_producto_data):
        """
        Test obtener top movimientos
        """
        # Crear producto
        response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = response.json()["id"]

        # Realizar movimientos
        for i in range(5):
            movement = {
                "producto_id": producto_id,
                "tipo_movimiento": "ENTRADA",
                "cantidad": 10,
                "motivo": f"Movimiento {i}",
                "usuario": "test_user"
            }
            client.post("/api/v1/stock/movement", json=movement)

        response = client.get("/api/v1/reportes/top-movimientos?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert "top_movimientos" in data
        assert len(data["top_movimientos"]) >= 1
        assert data["periodo_dias"] == 30

    def test_validate_stock_integrity(self, sample_producto_data):
        """
        Test validar integridad de stock
        """
        # Crear producto y realizar movimientos
        response = client.post("/api/v1/productos", json=sample_producto_data)
        producto_id = response.json()["id"]

        # Realizar algunos movimientos
        movements = [
            {"tipo_movimiento": "ENTRADA", "cantidad": 20},
            {"tipo_movimiento": "SALIDA", "cantidad": 10}
        ]

        for movement in movements:
            movement["producto_id"] = producto_id
            movement["motivo"] = "Test integrity"
            movement["usuario"] = "test_user"
            client.post("/api/v1/stock/movement", json=movement)

        response = client.get("/api/v1/reportes/integrity-check")
        assert response.status_code == 200

        data = response.json()
        assert "total_productos_revisados" in data
        assert "inconsistencias_encontradas" in data
        assert "integridad_ok" in data
        assert isinstance(data["integridad_ok"], bool)

# === TESTS DE INTEGRACIÓN ===

class TestIntegracion:
    """
    Tests de integración para flujos completos
    """

    def test_flujo_completo_producto_stock(self, sample_producto_data):
        """
        Test de flujo completo: crear producto, movimientos, reportes
        """
        # 1. Crear producto
        create_response = client.post("/api/v1/productos", json=sample_producto_data)
        assert create_response.status_code == 201
        producto = create_response.json()

        # 2. Realizar entrada de stock
        entrada_request = {
            "producto_id": producto["id"],
            "tipo_movimiento": "ENTRADA",
            "cantidad": 100,
            "motivo": "Compra inicial",
            "referencia": "PO-001",
            "usuario": "admin"
        }

        entrada_response = client.post("/api/v1/stock/movement", json=entrada_request)
        assert entrada_response.status_code == 200

        # 3. Realizar salida de stock
        salida_request = {
            "producto_id": producto["id"],
            "tipo_movimiento": "SALIDA",
            "cantidad": 30,
            "motivo": "Venta",
            "referencia": "SO-001",
            "usuario": "vendedor"
        }

        salida_response = client.post("/api/v1/stock/movement", json=salida_request)
        assert salida_response.status_code == 200

        # 4. Verificar stock final
        get_response = client.get(f"/api/v1/productos/{producto['id']}")
        assert get_response.status_code == 200

        producto_final = get_response.json()
        # Stock inicial (50) + entrada (100) - salida (30) = 120
        assert producto_final["stock_actual"] == 120

        # 5. Verificar historial
        history_response = client.get(f"/api/v1/stock/movements?producto_id={producto['id']}")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert len(history_data["movimientos"]) >= 3  # Stock inicial + entrada + salida

        # 6. Generar reporte
        report_response = client.get("/api/v1/reportes/stock")
        assert report_response.status_code == 200

        report_data = report_response.json()
        assert report_data["total_productos"] >= 1
        assert report_data["valor_total_inventario"] > 0

# === TESTS DE RENDIMIENTO BÁSICO ===

class TestPerformance:
    """
    Tests básicos de rendimiento
    """

    @pytest.mark.slow
    def test_create_multiple_productos_performance(self, sample_producto_data):
        """
        Test de rendimiento para crear múltiples productos
        """
        import time

        start_time = time.time()

        # Crear 100 productos
        for i in range(100):
            producto_data = sample_producto_data.copy()
            producto_data["codigo"] = f"PERF{i:03d}"
            producto_data["nombre"] = f"Producto Performance {i}"

            response = client.post("/api/v1/productos", json=producto_data)
            assert response.status_code == 201

        end_time = time.time()
        duration = end_time - start_time

        # Debe crear 100 productos en menos de 10 segundos
        assert duration < 10.0, f"Creación de 100 productos tomó {duration:.2f}s (límite: 10s)"

        # Verificar que se crearon todos
        list_response = client.get("/api/v1/productos?size=100")
        assert list_response.status_code == 200

        list_data = list_response.json()
        assert list_data["total"] >= 100


# === RUNNER DE TESTS ===

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
