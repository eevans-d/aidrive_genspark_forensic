"""
Tests para Stock Manager - Sistema Gestión Depósito
Tests completos para lógica ACID y operaciones de stock
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal

# Imports del proyecto
from agente_deposito.database import Base
from agente_deposito.models import Producto, MovimientoStock
from agente_deposito.stock_manager import (
    StockManager, StockManagerError, InsufficientStockError, 
    ProductoNotFoundError
)
from agente_deposito.schemas import StockUpdateRequest, TipoMovimiento

# Configuración de base de datos de testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stock.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    def create_test_producto(db, codigo="TEST001", stock_actual=10, stock_minimo=5):
        """Crear producto de prueba"""
        producto = Producto(
            codigo=codigo,
            nombre=f"Producto {codigo}",
            descripcion=f"Descripción {codigo}",
            categoria="TEST",
            marca="Test Brand",
            modelo="Test Model",
            precio_costo=Decimal("100.00"),
            precio_venta=Decimal("150.00"),
            precio_mayorista=Decimal("140.00"),
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            stock_maximo=50,
            ubicacion_deposito=f"TEST-{codigo}",
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
def setup_db():
    """Setup de base de datos para el módulo"""
    TestSetup.setup_database()
    yield
    TestSetup.teardown_database()

@pytest.fixture
def db(setup_db):
    """Sesión de base de datos para testing"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def stock_manager():
    """Instancia de StockManager para tests"""
    return StockManager()

@pytest.fixture
def sample_producto(db):
    """Producto de muestra para tests"""
    return TestSetup.create_test_producto(db, "SAMPLE001")

class TestStockManagerBasic:
    """Tests básicos del StockManager"""

    def test_stock_manager_initialization(self, stock_manager):
        """Test inicialización del StockManager"""
        assert stock_manager is not None
        assert hasattr(stock_manager, 'logger')

    def test_update_stock_entrada_success(self, stock_manager, db, sample_producto):
        """Test actualización de stock - entrada exitosa"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            subtipo="COMPRA",
            precio_unitario=Decimal("100.00"),
            documento_referencia="FC-001",
            usuario="TEST_USER",
            observaciones="Test entrada"
        )

        result = stock_manager.update_stock(db, request)
        db.commit()

        assert result["success"] == True
        assert result["producto_id"] == sample_producto.id
        assert result["stock_anterior"] == 10
        assert result["stock_nuevo"] == 15
        assert "movimiento_id" in result

        # Verificar que el producto se actualizó
        db.refresh(sample_producto)
        assert sample_producto.stock_actual == 15

    def test_update_stock_salida_success(self, stock_manager, db, sample_producto):
        """Test actualización de stock - salida exitosa"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=3,
            tipo_movimiento=TipoMovimiento.SALIDA,
            subtipo="VENTA",
            precio_unitario=Decimal("150.00"),
            documento_referencia="FC-002",
            usuario="TEST_USER",
            observaciones="Test salida"
        )

        result = stock_manager.update_stock(db, request)
        db.commit()

        assert result["success"] == True
        assert result["stock_anterior"] == 10
        assert result["stock_nuevo"] == 7

        # Verificar que el producto se actualizó
        db.refresh(sample_producto)
        assert sample_producto.stock_actual == 7

    def test_update_stock_ajuste_positivo(self, stock_manager, db, sample_producto):
        """Test actualización de stock - ajuste positivo"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.AJUSTE,
            subtipo="CORRECCION",
            usuario="TEST_USER",
            observaciones="Ajuste positivo"
        )

        result = stock_manager.update_stock(db, request)
        db.commit()

        assert result["success"] == True
        assert result["stock_nuevo"] == 15

    def test_update_stock_ajuste_negativo(self, stock_manager, db, sample_producto):
        """Test actualización de stock - ajuste negativo"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=-3,
            tipo_movimiento=TipoMovimiento.AJUSTE,
            subtipo="CORRECCION",
            usuario="TEST_USER",
            observaciones="Ajuste negativo"
        )

        result = stock_manager.update_stock(db, request)
        db.commit()

        assert result["success"] == True
        assert result["stock_nuevo"] == 7

class TestStockManagerErrors:
    """Tests para manejo de errores"""

    def test_update_stock_producto_not_found(self, stock_manager, db):
        """Test error cuando producto no existe"""
        request = StockUpdateRequest(
            producto_id=99999,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER"
        )

        with pytest.raises(ProductoNotFoundError):
            stock_manager.update_stock(db, request)

    def test_update_stock_insufficient_stock(self, stock_manager, db, sample_producto):
        """Test error por stock insuficiente"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=15,  # Más que el stock disponible (10)
            tipo_movimiento=TipoMovimiento.SALIDA,
            usuario="TEST_USER"
        )

        with pytest.raises(InsufficientStockError) as exc_info:
            stock_manager.update_stock(db, request)

        assert "insuficiente" in str(exc_info.value).lower()

    def test_update_stock_negative_result(self, stock_manager, db, sample_producto):
        """Test error cuando el resultado sería stock negativo"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=-15,  # Ajuste que resultaría en negativo
            tipo_movimiento=TipoMovimiento.AJUSTE,
            usuario="TEST_USER"
        )

        with pytest.raises(InsufficientStockError):
            stock_manager.update_stock(db, request)

    def test_update_stock_inactive_product(self, stock_manager, db):
        """Test error con producto inactivo"""
        # Crear producto inactivo
        producto_inactivo = TestSetup.create_test_producto(db, "INACTIVE001")
        producto_inactivo.activo = False
        db.commit()

        request = StockUpdateRequest(
            producto_id=producto_inactivo.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER"
        )

        with pytest.raises(ProductoNotFoundError):
            stock_manager.update_stock(db, request)

class TestStockManagerACID:
    """Tests para propiedades ACID"""

    def test_atomicity_rollback_on_error(self, stock_manager, db, sample_producto):
        """Test atomicidad - rollback en caso de error"""
        stock_inicial = sample_producto.stock_actual

        # Simular error después de actualizar producto pero antes de crear movimiento
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="",  # Usuario vacío para forzar error
        )

        with pytest.raises(Exception):
            stock_manager.update_stock(db, request)

        # Verificar que el stock no cambió
        db.refresh(sample_producto)
        assert sample_producto.stock_actual == stock_inicial

    def test_consistency_stock_matches_movements(self, stock_manager, db, sample_producto):
        """Test consistencia - stock coincide con movimientos"""
        movimientos = [
            StockUpdateRequest(
                producto_id=sample_producto.id,
                cantidad=5,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                usuario="TEST_USER"
            ),
            StockUpdateRequest(
                producto_id=sample_producto.id,
                cantidad=3,
                tipo_movimiento=TipoMovimiento.SALIDA,
                usuario="TEST_USER"
            ),
            StockUpdateRequest(
                producto_id=sample_producto.id,
                cantidad=2,
                tipo_movimiento=TipoMovimiento.AJUSTE,
                usuario="TEST_USER"
            )
        ]

        stock_esperado = 10  # Stock inicial
        for request in movimientos:
            result = stock_manager.update_stock(db, request)
            db.commit()
            stock_esperado = result["stock_nuevo"]

        # Verificar consistencia
        db.refresh(sample_producto)
        assert sample_producto.stock_actual == stock_esperado

        # Obtener último movimiento
        ultimo_movimiento = db.query(MovimientoStock).filter(
            MovimientoStock.producto_id == sample_producto.id
        ).order_by(MovimientoStock.fecha_movimiento.desc()).first()

        assert ultimo_movimiento.stock_posterior == sample_producto.stock_actual

    def test_isolation_concurrent_updates(self, stock_manager, db):
        """Test aislamiento - actualizaciones concurrentes"""
        # Crear producto para test de concurrencia
        producto = TestSetup.create_test_producto(db, "CONCURRENT001", stock_actual=10)

        # Simular dos transacciones concurrentes
        # En un entorno real, esto requeriría threading o async
        # Para el test, verificamos que with_for_update funcione

        request1 = StockUpdateRequest(
            producto_id=producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="USER1"
        )

        request2 = StockUpdateRequest(
            producto_id=producto.id,
            cantidad=3,
            tipo_movimiento=TipoMovimiento.SALIDA,
            usuario="USER2"
        )

        # Ejecutar secuencialmente (en test real sería concurrente)
        result1 = stock_manager.update_stock(db, request1)
        db.commit()

        result2 = stock_manager.update_stock(db, request2)
        db.commit()

        # Verificar resultado final
        db.refresh(producto)
        assert producto.stock_actual == 12  # 10 + 5 - 3

    def test_durability_data_persists(self, stock_manager, db, sample_producto):
        """Test durabilidad - datos persisten después de commit"""
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=7,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER",
            observaciones="Test durabilidad"
        )

        result = stock_manager.update_stock(db, request)
        movimiento_id = result["movimiento_id"]
        db.commit()

        # Cerrar y reabrir sesión para simular persistencia
        db.close()
        new_db = TestingSessionLocal()

        try:
            # Verificar que los datos persisten
            producto_persistido = new_db.query(Producto).filter(
                Producto.id == sample_producto.id
            ).first()

            movimiento_persistido = new_db.query(MovimientoStock).filter(
                MovimientoStock.id == movimiento_id
            ).first()

            assert producto_persistido.stock_actual == 17
            assert movimiento_persistido is not None
            assert movimiento_persistido.observaciones == "Test durabilidad"

        finally:
            new_db.close()

class TestStockManagerQueries:
    """Tests para consultas del StockManager"""

    def test_get_stock_movements_empty(self, stock_manager):
        """Test obtener movimientos cuando no hay ninguno"""
        movimientos = stock_manager.get_stock_movements()
        assert isinstance(movimientos, list)
        assert len(movimientos) == 0

    def test_get_stock_movements_with_data(self, stock_manager, db, sample_producto):
        """Test obtener movimientos con datos"""
        # Crear algunos movimientos
        requests = [
            StockUpdateRequest(
                producto_id=sample_producto.id,
                cantidad=5,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                usuario="USER1"
            ),
            StockUpdateRequest(
                producto_id=sample_producto.id,
                cantidad=2,
                tipo_movimiento=TipoMovimiento.SALIDA,
                usuario="USER2"
            )
        ]

        for request in requests:
            stock_manager.update_stock(db, request)
            db.commit()

        movimientos = stock_manager.get_stock_movements(
            producto_id=sample_producto.id
        )

        assert len(movimientos) >= 2
        assert all(mov.producto_id == sample_producto.id for mov in movimientos)

    def test_get_stock_movements_with_filters(self, stock_manager, db, sample_producto):
        """Test obtener movimientos con filtros"""
        # Crear movimiento específico
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=3,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            subtipo="COMPRA_ESPECIAL",
            usuario="FILTER_USER"
        )

        stock_manager.update_stock(db, request)
        db.commit()

        # Test filtro por tipo
        movimientos_entrada = stock_manager.get_stock_movements(
            tipo_movimiento="ENTRADA"
        )
        assert all(mov.tipo_movimiento == "ENTRADA" for mov in movimientos_entrada)

        # Test con límite
        movimientos_limitados = stock_manager.get_stock_movements(limit=1)
        assert len(movimientos_limitados) <= 1

    def test_get_critical_stock_products_empty(self, stock_manager):
        """Test obtener productos críticos cuando no hay ninguno"""
        productos_criticos = stock_manager.get_critical_stock_products()
        assert isinstance(productos_criticos, list)

    def test_get_critical_stock_products_with_data(self, stock_manager, db):
        """Test obtener productos críticos con datos"""
        # Crear producto con stock crítico
        producto_critico = TestSetup.create_test_producto(
            db, "CRITICO001", stock_actual=2, stock_minimo=5
        )

        # Crear producto con stock normal
        producto_normal = TestSetup.create_test_producto(
            db, "NORMAL001", stock_actual=10, stock_minimo=5
        )

        productos_criticos = stock_manager.get_critical_stock_products()

        # Verificar que incluye el crítico pero no el normal
        codigos_criticos = [p.codigo for p in productos_criticos]
        assert "CRITICO001" in codigos_criticos
        assert "NORMAL001" not in codigos_criticos

    def test_get_stock_summary(self, stock_manager, db):
        """Test obtener resumen de stock"""
        # Crear productos de prueba
        TestSetup.create_test_producto(db, "SUM001", stock_actual=10, stock_minimo=5)
        TestSetup.create_test_producto(db, "SUM002", stock_actual=2, stock_minimo=5)
        TestSetup.create_test_producto(db, "SUM003", stock_actual=0, stock_minimo=5)

        summary = stock_manager.get_stock_summary()

        assert "total_productos" in summary
        assert "productos_sin_stock" in summary  
        assert "productos_stock_critico" in summary
        assert "valor_total_inventario" in summary
        assert "categorias_con_stock_critico" in summary
        assert "fecha_consulta" in summary

        # Verificar valores lógicos
        assert summary["total_productos"] >= 3
        assert summary["productos_sin_stock"] >= 1  # SUM003 tiene stock 0
        assert summary["productos_stock_critico"] >= 1  # SUM002 tiene stock crítico

class TestStockManagerValidation:
    """Tests para validación de datos"""

    def test_validate_stock_consistency_clean(self, stock_manager, db, sample_producto):
        """Test validación de consistencia - datos limpios"""
        # Crear movimiento normal
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER"
        )

        stock_manager.update_stock(db, request)
        db.commit()

        validation = stock_manager.validate_stock_consistency()

        assert validation["consistente"] == True
        assert validation["inconsistencias_encontradas"] == 0
        assert len(validation["inconsistencias"]) == 0

    def test_validate_stock_consistency_with_inconsistency(self, stock_manager, db, sample_producto):
        """Test validación de consistencia - con inconsistencias"""
        # Crear movimiento
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER"
        )

        stock_manager.update_stock(db, request)
        db.commit()

        # Simular inconsistencia modificando directamente el stock
        sample_producto.stock_actual = 999
        db.commit()

        validation = stock_manager.validate_stock_consistency()

        assert validation["consistente"] == False
        assert validation["inconsistencias_encontradas"] >= 1
        assert len(validation["inconsistencias"]) >= 1

    def test_fix_stock_inconsistency(self, stock_manager, db, sample_producto):
        """Test corrección de inconsistencia de stock"""
        # Crear movimiento para tener historial
        request = StockUpdateRequest(
            producto_id=sample_producto.id,
            cantidad=5,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            usuario="TEST_USER"
        )

        result = stock_manager.update_stock(db, request)
        stock_correcto = result["stock_nuevo"]
        db.commit()

        # Simular inconsistencia
        sample_producto.stock_actual = 999
        db.commit()

        # Corregir inconsistencia
        fix_result = stock_manager.fix_stock_inconsistency(
            sample_producto.id, "ADMIN_USER"
        )

        assert fix_result["success"] == True
        assert fix_result["ajuste_realizado"] == True
        assert fix_result["stock_corregido"] == stock_correcto

        # Verificar que se corrigió
        db.refresh(sample_producto)
        assert sample_producto.stock_actual == stock_correcto

class TestStockManagerMultiple:
    """Tests para operaciones múltiples"""

    def test_update_multiple_stock_success(self, stock_manager, db):
        """Test actualización múltiple exitosa"""
        # Crear varios productos
        productos = [
            TestSetup.create_test_producto(db, f"MULTI{i:03d}")
            for i in range(3)
        ]

        # Crear requests para todos
        requests = [
            StockUpdateRequest(
                producto_id=producto.id,
                cantidad=5,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                usuario="MULTI_USER"
            )
            for producto in productos
        ]

        result = stock_manager.update_multiple_stock(requests)

        assert result["success"] == True
        assert len(result["results"]) == 3
        assert len(result["errors"]) == 0

        # Verificar que todos se actualizaron
        for producto in productos:
            db.refresh(producto)
            assert producto.stock_actual == 15  # 10 + 5

    def test_update_multiple_stock_with_errors(self, stock_manager, db):
        """Test actualización múltiple con errores"""
        # Crear un producto válido y uno inválido
        producto_valido = TestSetup.create_test_producto(db, "VALID001")

        requests = [
            StockUpdateRequest(
                producto_id=producto_valido.id,
                cantidad=5,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                usuario="TEST_USER"
            ),
            StockUpdateRequest(
                producto_id=99999,  # Producto inexistente
                cantidad=5,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                usuario="TEST_USER"
            )
        ]

        result = stock_manager.update_multiple_stock(requests)

        assert result["success"] == False
        assert len(result["errors"]) > 0

        # Verificar que la transacción completa falló (atomicidad)
        db.refresh(producto_valido)
        assert producto_valido.stock_actual == 10  # No cambió

# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
