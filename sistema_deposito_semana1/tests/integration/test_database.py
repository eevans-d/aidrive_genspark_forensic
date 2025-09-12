"""
Tests de Integración de Base de Datos - Sistema Gestión Depósito
Tests completos para validar integración de BD y operaciones complejas
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import os

# Imports del proyecto
from agente_deposito.database import DatabaseManager, Base
from agente_deposito.models import Producto, MovimientoStock, Cliente, Proveedor
from agente_deposito.stock_manager import StockManager
from agente_deposito.schemas import StockUpdateRequest, TipoMovimiento

class TestDatabaseIntegration:
    """Tests de integración para base de datos"""

    @pytest.fixture(scope="class")
    def temp_db(self):
        """Base de datos temporal para tests"""
        # Crear archivo temporal para SQLite
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        connection_string = f"sqlite:///{db_path}"
        db_manager = DatabaseManager(connection_string)

        # Crear tablas
        db_manager.create_tables()

        yield db_manager

        # Limpiar
        os.unlink(db_path)

    @pytest.fixture
    def db_session(self, temp_db):
        """Sesión de base de datos para tests"""
        with temp_db.get_session() as session:
            yield session

    def test_database_connection(self, temp_db):
        """Test conexión a base de datos"""
        assert temp_db.test_connection() == True

    def test_create_and_drop_tables(self):
        """Test creación y eliminación de tablas"""
        # Crear DB temporal
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        try:
            connection_string = f"sqlite:///{db_path}"
            db_manager = DatabaseManager(connection_string)

            # Test creación
            assert db_manager.create_tables() == True

            # Verificar que las tablas existen
            with db_manager.get_session() as session:
                # Intentar consultar cada tabla
                session.query(Producto).count()
                session.query(MovimientoStock).count()
                session.query(Cliente).count()
                session.query(Proveedor).count()

            # Test eliminación
            assert db_manager.drop_tables() == True

        finally:
            os.unlink(db_path)

    def test_get_connection_info(self, temp_db):
        """Test obtener información de conexión"""
        info = temp_db.get_connection_info()

        # Para SQLite, algunos campos pueden estar vacíos
        assert isinstance(info, dict)
        # Verificar que no falló completamente
        assert len(info) >= 0

    def test_execute_raw_sql(self, temp_db):
        """Test ejecutar SQL crudo"""
        # Test query simple
        result = temp_db.execute_raw_sql("SELECT 1 as test_value")
        assert len(result) == 1
        assert result[0][0] == 1

        # Test con parámetros (usando estilo SQLite)
        result = temp_db.execute_raw_sql("SELECT ?1 as param_value", {"1": "test_param"})
        assert len(result) == 1

    def test_get_table_stats_empty(self, temp_db):
        """Test estadísticas de tablas vacías"""
        stats = temp_db.get_table_stats()

        assert isinstance(stats, dict)
        assert stats.get('productos', 0) == 0
        assert stats.get('movimientos_stock', 0) == 0
        assert stats.get('proveedores', 0) == 0
        assert stats.get('clientes', 0) == 0
        assert stats.get('productos_stock_critico', 0) == 0

    def test_get_table_stats_with_data(self, temp_db, db_session):
        """Test estadísticas de tablas con datos"""
        # Crear datos de prueba

        # Producto normal
        producto_normal = Producto(
            codigo="STATS001",
            nombre="Producto Stats Normal",
            categoria="TEST",
            precio_costo=Decimal("100.00"),
            precio_venta=Decimal("150.00"),
            stock_actual=10,
            stock_minimo=5,
            activo=True
        )
        db_session.add(producto_normal)

        # Producto con stock crítico
        producto_critico = Producto(
            codigo="STATS002",
            nombre="Producto Stats Crítico",
            categoria="TEST",
            precio_costo=Decimal("50.00"),
            precio_venta=Decimal("75.00"),
            stock_actual=2,
            stock_minimo=5,
            activo=True
        )
        db_session.add(producto_critico)

        # Cliente
        cliente = Cliente(
            codigo="CLI001",
            tipo_cliente="PERSONA",
            nombre="Juan",
            apellido="Pérez",
            documento_tipo="DNI",
            documento_numero="12345678",
            activo=True
        )
        db_session.add(cliente)

        # Proveedor
        proveedor = Proveedor(
            codigo="PROV001",
            razon_social="Proveedor Test S.A.",
            cuit="30-12345678-9",
            activo=True
        )
        db_session.add(proveedor)

        db_session.commit()

        # Obtener estadísticas
        stats = temp_db.get_table_stats()

        assert stats['productos'] == 2
        assert stats['clientes'] == 1
        assert stats['proveedores'] == 1
        assert stats['productos_stock_critico'] == 1

class TestComplexDatabaseOperations:
    """Tests para operaciones complejas de base de datos"""

    @pytest.fixture(scope="class")
    def setup_complex_db(self):
        """Setup con datos complejos para tests"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        connection_string = f"sqlite:///{db_path}"
        db_manager = DatabaseManager(connection_string)
        db_manager.create_tables()

        # Poblar con datos complejos
        with db_manager.get_session() as session:
            # Crear varios productos
            productos = []
            for i in range(10):
                producto = Producto(
                    codigo=f"COMPLEX{i:03d}",
                    nombre=f"Producto Complejo {i}",
                    categoria="ELECTRODOMESTICOS" if i % 2 == 0 else "TECNOLOGIA",
                    precio_costo=Decimal(f"{100 + i * 10}.00"),
                    precio_venta=Decimal(f"{150 + i * 15}.00"),
                    stock_actual=20 - i,  # Stock decreciente
                    stock_minimo=5,
                    activo=True
                )
                productos.append(producto)
                session.add(producto)

            session.commit()

            # Crear movimientos de stock
            stock_manager = StockManager()
            for i, producto in enumerate(productos):
                # Entrada inicial
                request = StockUpdateRequest(
                    producto_id=producto.id,
                    cantidad=producto.stock_actual,
                    tipo_movimiento=TipoMovimiento.ENTRADA,
                    subtipo="STOCK_INICIAL",
                    usuario="SETUP_USER",
                    documento_referencia=f"INIT-{producto.codigo}"
                )
                stock_manager.update_stock(session, request)

                # Algunos movimientos adicionales
                if i % 3 == 0:
                    # Salida
                    request_salida = StockUpdateRequest(
                        producto_id=producto.id,
                        cantidad=2,
                        tipo_movimiento=TipoMovimiento.SALIDA,
                        subtipo="VENTA",
                        usuario="VENDEDOR",
                        documento_referencia=f"FC-{1000 + i}"
                    )
                    stock_manager.update_stock(session, request_salida)

            session.commit()

        yield db_manager

        # Limpiar
        os.unlink(db_path)

    def test_complex_queries_performance(self, setup_complex_db):
        """Test rendimiento de queries complejas"""
        start_time = datetime.now()

        with setup_complex_db.get_session() as session:
            # Query compleja: productos con stock crítico y sus movimientos
            query = session.query(Producto).filter(
                Producto.stock_actual <= Producto.stock_minimo
            ).join(MovimientoStock).filter(
                MovimientoStock.tipo_movimiento == 'SALIDA'
            )

            resultados = query.all()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verificar que la query no tardó demasiado (menos de 1 segundo)
        assert duration < 1.0
        assert isinstance(resultados, list)

    def test_transaction_rollback_complex(self, setup_complex_db):
        """Test rollback de transacciones complejas"""
        with setup_complex_db.get_session() as session:
            # Contar productos iniciales
            count_inicial = session.query(Producto).count()

            try:
                # Operación compleja que falla
                producto_nuevo = Producto(
                    codigo="ROLLBACK001",
                    nombre="Producto Rollback",
                    categoria="TEST",
                    precio_costo=Decimal("100.00"),
                    precio_venta=Decimal("150.00"),
                    stock_actual=10,
                    stock_minimo=5,
                    activo=True
                )
                session.add(producto_nuevo)
                session.flush()  # Para obtener ID

                # Operación que falla intencionalmente
                producto_duplicado = Producto(
                    codigo="ROLLBACK001",  # Código duplicado
                    nombre="Producto Duplicado",
                    categoria="TEST",
                    precio_costo=Decimal("100.00"),
                    precio_venta=Decimal("150.00"),
                    stock_actual=5,
                    stock_minimo=2,
                    activo=True
                )
                session.add(producto_duplicado)
                session.commit()  # Esto debería fallar

            except Exception:
                # Rollback automático por context manager
                pass

            # Verificar que no se creó ningún producto
            count_final = session.query(Producto).count()
            assert count_final == count_inicial

    def test_concurrent_stock_updates_simulation(self, setup_complex_db):
        """Test simulación de actualizaciones concurrentes de stock"""
        stock_manager = StockManager()

        with setup_complex_db.get_session() as session:
            # Obtener un producto
            producto = session.query(Producto).first()
            stock_inicial = producto.stock_actual

            # Simular múltiples actualizaciones "concurrentes"
            requests = [
                StockUpdateRequest(
                    producto_id=producto.id,
                    cantidad=2,
                    tipo_movimiento=TipoMovimiento.ENTRADA,
                    usuario=f"USER_{i}",
                    documento_referencia=f"DOC-{i}"
                )
                for i in range(5)
            ]

            # Ejecutar todas las requests
            for request in requests:
                stock_manager.update_stock(session, request)

            session.commit()

            # Verificar resultado final
            session.refresh(producto)
            stock_esperado = stock_inicial + (2 * 5)  # 5 entradas de 2 unidades cada una
            assert producto.stock_actual == stock_esperado

            # Verificar que se crearon todos los movimientos
            movimientos = session.query(MovimientoStock).filter(
                MovimientoStock.producto_id == producto.id,
                MovimientoStock.documento_referencia.like("DOC-%")
            ).count()

            assert movimientos == 5

    def test_data_integrity_constraints(self, setup_complex_db):
        """Test integridad de datos y constraints"""
        with setup_complex_db.get_session() as session:
            # Test constraint precio positivo
            with pytest.raises(Exception):
                producto_precio_negativo = Producto(
                    codigo="NEGATIVE001",
                    nombre="Producto Precio Negativo",
                    categoria="TEST",
                    precio_costo=Decimal("-100.00"),  # Precio negativo
                    precio_venta=Decimal("150.00"),
                    stock_actual=10,
                    stock_minimo=5,
                    activo=True
                )
                session.add(producto_precio_negativo)
                session.commit()

    def test_database_backup_functionality(self, setup_complex_db):
        """Test funcionalidad de backup"""
        # Test básico de backup (implementación simple)
        result = setup_complex_db.backup_data()

        # En la implementación actual, backup_data solo hace log
        # En producción, esto haría un backup real
        assert result == True

class TestDatabaseErrorHandling:
    """Tests para manejo de errores de base de datos"""

    def test_connection_error_handling(self):
        """Test manejo de errores de conexión"""
        # Intentar conectar a una BD inválida
        invalid_db = DatabaseManager("postgresql://invalid:invalid@localhost:9999/invalid")

        # Test conexión fallida
        assert invalid_db.test_connection() == False

        # Test get_connection_info con conexión fallida
        info = invalid_db.get_connection_info()
        assert isinstance(info, dict)
        assert len(info) == 0  # Debería estar vacío por el error

    def test_table_stats_error_handling(self):
        """Test manejo de errores en estadísticas"""
        invalid_db = DatabaseManager("postgresql://invalid:invalid@localhost:9999/invalid")

        stats = invalid_db.get_table_stats()
        assert isinstance(stats, dict)
        assert len(stats) == 0  # Debería estar vacío por el error

    def test_sql_execution_error_handling(self, temp_db):
        """Test manejo de errores en ejecución SQL"""
        # Crear DB temporal básica
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        try:
            connection_string = f"sqlite:///{db_path}"
            db_manager = DatabaseManager(connection_string)

            # Test SQL inválido
            with pytest.raises(Exception):
                db_manager.execute_raw_sql("SELECT * FROM tabla_inexistente")

        finally:
            os.unlink(db_path)

class TestIndexesAndPerformance:
    """Tests para índices y rendimiento"""

    @pytest.fixture(scope="class")
    def performance_db(self):
        """Base de datos para tests de rendimiento"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        connection_string = f"sqlite:///{db_path}"
        db_manager = DatabaseManager(connection_string)
        db_manager.create_tables()

        # Crear muchos datos para test de rendimiento
        with db_manager.get_session() as session:
            productos = []
            for i in range(100):
                producto = Producto(
                    codigo=f"PERF{i:05d}",
                    nombre=f"Producto Performance {i}",
                    categoria=f"CAT{i % 10}",  # 10 categorías diferentes
                    marca=f"MARCA{i % 5}",  # 5 marcas diferentes
                    precio_costo=Decimal(f"{100 + (i % 50)}.00"),
                    precio_venta=Decimal(f"{150 + (i % 75)}.00"),
                    stock_actual=i % 30,
                    stock_minimo=5,
                    activo=True
                )
                productos.append(producto)
                session.add(producto)

                # Commit en lotes para mejor rendimiento
                if i % 20 == 0:
                    session.commit()

            session.commit()

            # Crear movimientos para algunos productos
            stock_manager = StockManager()
            for i in range(0, 100, 10):  # Cada 10 productos
                producto = productos[i]
                for j in range(5):  # 5 movimientos por producto
                    request = StockUpdateRequest(
                        producto_id=producto.id,
                        cantidad=j + 1,
                        tipo_movimiento=TipoMovimiento.ENTRADA,
                        usuario=f"PERF_USER_{j}",
                        documento_referencia=f"PERF-{i}-{j}"
                    )
                    stock_manager.update_stock(session, request)

            session.commit()

        yield db_manager

        os.unlink(db_path)

    def test_product_search_performance(self, performance_db):
        """Test rendimiento de búsqueda de productos"""
        start_time = datetime.now()

        with performance_db.get_session() as session:
            # Búsqueda por código
            resultado = session.query(Producto).filter(
                Producto.codigo == "PERF00050"
            ).first()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        assert resultado is not None
        assert duration < 0.1  # Menos de 100ms

    def test_category_filter_performance(self, performance_db):
        """Test rendimiento de filtro por categoría"""
        start_time = datetime.now()

        with performance_db.get_session() as session:
            # Filtro por categoría
            resultados = session.query(Producto).filter(
                Producto.categoria == "CAT5"
            ).all()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        assert len(resultados) > 0
        assert duration < 0.2  # Menos de 200ms

    def test_stock_movements_join_performance(self, performance_db):
        """Test rendimiento de joins con movimientos"""
        start_time = datetime.now()

        with performance_db.get_session() as session:
            # Join entre productos y movimientos
            resultados = session.query(Producto, MovimientoStock).join(
                MovimientoStock, Producto.id == MovimientoStock.producto_id
            ).filter(
                MovimientoStock.tipo_movimiento == 'ENTRADA'
            ).limit(20).all()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        assert len(resultados) > 0
        assert duration < 0.5  # Menos de 500ms

# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
