"""
Validaciones específicas del dominio Retail Argentino
Incluye constraints de negocio, códigos EAN/UPC y validaciones AFIP
"""
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Literal, Optional, List
from decimal import Decimal
from datetime import datetime
import re


class MovimientoStock(BaseModel):
    """Validaciones para movimientos de stock retail"""
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(..., description="Cantidad del movimiento (puede ser negativa para salidas)")
    tipo_movimiento: Literal["ENTRADA", "SALIDA", "AJUSTE", "TRANSFERENCIA"]
    deposito_id: int = Field(..., gt=0, description="ID del depósito")
    precio_unitario: Optional[Decimal] = Field(None, ge=0.01, description="Precio unitario si aplica")
    observaciones: Optional[str] = Field(None, max_length=500)
    
    @field_validator('cantidad')
    @classmethod
    def validate_cantidad_no_zero(cls, v):
        if v == 0:
            raise ValueError("La cantidad no puede ser cero")
        return v
    
    @field_validator('precio_unitario')
    @classmethod
    def validate_precio_formato_argentino(cls, v):
        if v is not None:
            # Validar que tenga máximo 2 decimales (centavos)
            if v.as_tuple().exponent < -2:
                raise ValueError("El precio no puede tener más de 2 decimales")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "producto_id": 123,
                "cantidad": 50,
                "tipo_movimiento": "ENTRADA",
                "deposito_id": 1,
                "precio_unitario": "199.99",
                "observaciones": "Recepción de mercadería proveedor XYZ"
            }
        }
    )


class ProductoRetail(BaseModel):
    """Validaciones para productos retail argentinos"""
    codigo_barras: str = Field(..., pattern=r'^\d{8,14}$', description="Código EAN/UPC válido")
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    categoria: str = Field(..., min_length=1, max_length=50)
    precio_venta: Decimal = Field(..., ge=0.01, description="Precio de venta al público")
    precio_costo: Optional[Decimal] = Field(None, ge=0.01, description="Precio de costo")
    stock_minimo: int = Field(0, ge=0, description="Stock mínimo para alertas")
    stock_maximo: Optional[int] = Field(None, ge=1, description="Stock máximo sugerido")
    iva_categoria: Literal["EXENTO", "10.5", "21", "27"] = Field("21", description="Categoría IVA Argentina")
    
    @field_validator('codigo_barras')
    @classmethod
    def validate_codigo_barras_argentino(cls, v):
        """Validar códigos de barras comunes en Argentina"""
        if not v.isdigit():
            raise ValueError("El código de barras debe contener solo números")
        
        # Validar longitudes comunes EAN-8, EAN-13, UPC-A
        if len(v) not in [8, 12, 13, 14]:
            raise ValueError("Longitud de código de barras no válida (debe ser 8, 12, 13 o 14 dígitos)")
        
        return v
    
    @field_validator('precio_venta', 'precio_costo')
    @classmethod
    def validate_precios_decimales(cls, v):
        if v is not None and v.as_tuple().exponent < -2:
            raise ValueError("Los precios no pueden tener más de 2 decimales")
        return v
    
    @field_validator('stock_maximo')
    @classmethod
    def validate_stock_maximo_mayor_minimo(cls, v, info):
        if v is not None and 'stock_minimo' in info.data:
            if v <= info.data['stock_minimo']:
                raise ValueError("El stock máximo debe ser mayor al stock mínimo")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_barras": "7790001234567",
                "nombre": "Coca Cola 500ml",
                "descripcion": "Bebida gaseosa cola",
                "categoria": "Bebidas",
                "precio_venta": "350.00",
                "precio_costo": "280.00",
                "stock_minimo": 10,
                "stock_maximo": 100,
                "iva_categoria": "21"
            }
        }
    )


class ValidacionStock(BaseModel):
    """Validaciones específicas para operaciones de stock"""
    
    @staticmethod
    def validar_stock_no_negativo(stock_actual: int, cantidad_movimiento: int) -> bool:
        """Validar que el stock no quede negativo"""
        stock_resultante = stock_actual + cantidad_movimiento
        if stock_resultante < 0:
            raise ValueError(
                f"Operación inválida: Stock resultante sería {stock_resultante}. "
                f"Stock actual: {stock_actual}, Movimiento: {cantidad_movimiento}"
            )
        return True
    
    @staticmethod
    def validar_transferencia_depositos(deposito_origen: int, deposito_destino: int) -> bool:
        """Validar transferencias entre depósitos"""
        if deposito_origen == deposito_destino:
            raise ValueError("El depósito origen debe ser diferente al destino")
        return True


class AlertaStock(BaseModel):
    """Modelo para alertas de stock"""
    producto_id: int
    stock_actual: int
    stock_minimo: int
    nivel_criticidad: Literal["BAJO", "CRITICO", "AGOTADO"]
    fecha_alerta: datetime = Field(default_factory=datetime.now)
    
    @field_validator('nivel_criticidad', mode="before")
    @classmethod
    def determinar_criticidad(cls, v, info):
        if 'stock_actual' in info.data and 'stock_minimo' in info.data:
            stock_actual = info.data['stock_actual']
            stock_minimo = info.data['stock_minimo']
            
            if stock_actual == 0:
                return "AGOTADO"
            elif stock_actual <= stock_minimo * 0.5:
                return "CRITICO"
            elif stock_actual <= stock_minimo:
                return "BAJO"
        
        return v or "BAJO"


# Funciones de utilidad para validaciones comunes
def validar_codigo_barras_argentino(codigo: str) -> bool:
    """
    Validar códigos de barras específicos del mercado argentino
    Incluye validación de dígito verificador para EAN-13
    """
    if not codigo.isdigit():
        return False
    
    if len(codigo) == 13:  # EAN-13
        # Calcular dígito verificador
        suma = 0
        for i, digito in enumerate(codigo[:-1]):
            if i % 2 == 0:
                suma += int(digito)
            else:
                suma += int(digito) * 3
        
        digito_verificador = (10 - (suma % 10)) % 10
        return digito_verificador == int(codigo[-1])
    
    return len(codigo) in [8, 12, 14]  # Otras longitudes válidas


def validar_precio_argentino(precio: Decimal) -> bool:
    """Validar formato de precio argentino (máximo 2 decimales)"""
    return precio.as_tuple().exponent >= -2