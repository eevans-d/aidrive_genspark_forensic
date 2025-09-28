"""
Tests for retail domain validations
"""
import pytest
from decimal import Decimal
from app.retail.validation import (
    MovimientoStock, ProductoRetail, ValidacionStock, 
    validar_codigo_barras_argentino, validar_precio_argentino
)


class TestMovimientoStock:
    """Tests para validaciones de movimientos de stock"""
    
    def test_movimiento_valido(self):
        """Test movimiento de stock válido"""
        movimiento = MovimientoStock(
            producto_id=123,
            cantidad=50,
            tipo_movimiento="ENTRADA",
            deposito_id=1,
            precio_unitario=Decimal("199.99")
        )
        
        assert movimiento.producto_id == 123
        assert movimiento.cantidad == 50
        assert movimiento.tipo_movimiento == "ENTRADA"
        assert movimiento.precio_unitario == Decimal("199.99")
    
    def test_cantidad_cero_invalida(self):
        """Test que cantidad cero es inválida"""
        with pytest.raises(ValueError, match="La cantidad no puede ser cero"):
            MovimientoStock(
                producto_id=123,
                cantidad=0,
                tipo_movimiento="ENTRADA",
                deposito_id=1
            )
    
    def test_precio_con_mas_de_dos_decimales_invalido(self):
        """Test que precio con más de 2 decimales es inválido"""
        with pytest.raises(ValueError, match="no puede tener más de 2 decimales"):
            MovimientoStock(
                producto_id=123,
                cantidad=10,
                tipo_movimiento="ENTRADA",
                deposito_id=1,
                precio_unitario=Decimal("199.999")
            )


class TestProductoRetail:
    """Tests para validaciones de productos retail"""
    
    def test_producto_valido(self):
        """Test producto retail válido"""
        producto = ProductoRetail(
            codigo_barras="7790001234567",
            nombre="Coca Cola 500ml",
            categoria="Bebidas",
            precio_venta=Decimal("350.00"),
            precio_costo=Decimal("280.00"),
            stock_minimo=10,
            stock_maximo=100,
            iva_categoria="21"
        )
        
        assert producto.codigo_barras == "7790001234567"
        assert producto.precio_venta == Decimal("350.00")
        assert producto.iva_categoria == "21"
    
    def test_codigo_barras_longitud_invalida(self):
        """Test código de barras con longitud inválida"""
        with pytest.raises(ValueError, match="Longitud de código de barras no válida"):
            ProductoRetail(
                codigo_barras="123456",  # Muy corto
                nombre="Producto Test",
                categoria="Test",
                precio_venta=Decimal("100.00")
            )
    
    def test_codigo_barras_no_numerico_invalido(self):
        """Test código de barras no numérico"""
        with pytest.raises(ValueError, match="debe contener solo números"):
            ProductoRetail(
                codigo_barras="12345abc67890",
                nombre="Producto Test",
                categoria="Test",
                precio_venta=Decimal("100.00")
            )
    
    def test_stock_maximo_menor_que_minimo_invalido(self):
        """Test stock máximo menor que mínimo"""
        with pytest.raises(ValueError, match="debe ser mayor al stock mínimo"):
            ProductoRetail(
                codigo_barras="1234567890123",
                nombre="Producto Test",
                categoria="Test",
                precio_venta=Decimal("100.00"),
                stock_minimo=50,
                stock_maximo=30  # Menor que el mínimo
            )


class TestValidacionStock:
    """Tests para validaciones específicas de stock"""
    
    def test_validar_stock_no_negativo_valido(self):
        """Test validación de stock no negativo válida"""
        result = ValidacionStock.validar_stock_no_negativo(
            stock_actual=100,
            cantidad_movimiento=-50
        )
        assert result is True
    
    def test_validar_stock_no_negativo_invalido(self):
        """Test validación de stock que quedaría negativo"""
        with pytest.raises(ValueError, match="Stock resultante sería -50"):
            ValidacionStock.validar_stock_no_negativo(
                stock_actual=30,
                cantidad_movimiento=-80
            )
    
    def test_validar_transferencia_depositos_valida(self):
        """Test transferencia entre depósitos diferentes"""
        result = ValidacionStock.validar_transferencia_depositos(
            deposito_origen=1,
            deposito_destino=2
        )
        assert result is True
    
    def test_validar_transferencia_mismo_deposito_invalida(self):
        """Test transferencia al mismo depósito es inválida"""
        with pytest.raises(ValueError, match="debe ser diferente al destino"):
            ValidacionStock.validar_transferencia_depositos(
                deposito_origen=1,
                deposito_destino=1
            )


class TestUtilidades:
    """Tests para funciones de utilidad"""
    
    def test_validar_codigo_barras_ean13_valido(self):
        """Test validación EAN-13 válido"""
        # EAN-13 con checksum correcto
        assert validar_codigo_barras_argentino("7790001234567") is True
    
    def test_validar_codigo_barras_ean13_checksum_invalido(self):
        """Test validación EAN-13 con checksum inválido"""
        # EAN-13 con checksum incorrecto
        assert validar_codigo_barras_argentino("7790001234568") is False
    
    def test_validar_codigo_barras_longitudes_validas(self):
        """Test validación de longitudes válidas"""
        assert validar_codigo_barras_argentino("12345678") is True  # 8 dígitos
        assert validar_codigo_barras_argentino("123456789012") is True  # 12 dígitos
        assert validar_codigo_barras_argentino("12345678901234") is True  # 14 dígitos
    
    def test_validar_codigo_barras_no_numerico(self):
        """Test código de barras no numérico"""
        assert validar_codigo_barras_argentino("12345abc6789") is False
    
    def test_validar_precio_argentino_valido(self):
        """Test precio argentino válido"""
        assert validar_precio_argentino(Decimal("199.99")) is True
        assert validar_precio_argentino(Decimal("100.5")) is True
        assert validar_precio_argentino(Decimal("50")) is True
    
    def test_validar_precio_argentino_invalido(self):
        """Test precio con más de 2 decimales"""
        assert validar_precio_argentino(Decimal("199.999")) is False
        assert validar_precio_argentino(Decimal("100.123")) is False