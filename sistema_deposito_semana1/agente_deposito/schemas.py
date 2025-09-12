"""
Esquemas Pydantic - Sistema Gestión Depósito
Modelos de validación para API REST
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

# Enums para validación
class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"

class TipoCliente(str, Enum):
    PERSONA = "PERSONA"
    EMPRESA = "EMPRESA"

class EstadoMovimiento(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    ANULADO = "ANULADO"

# Schemas base
class ProductoBase(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=50)
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    categoria: str = Field(..., min_length=3, max_length=100)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    precio_costo: Decimal = Field(..., gt=0)
    precio_venta: Decimal = Field(..., gt=0)
    precio_mayorista: Optional[Decimal] = Field(None, gt=0)
    stock_actual: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)
    stock_maximo: Optional[int] = Field(None, gt=0)
    ubicacion_deposito: Optional[str] = Field(None, max_length=100)
    peso_kg: Optional[Decimal] = Field(None, gt=0)
    dimensiones: Optional[str] = Field(None, max_length=100)
    activo: bool = True
    usuario_creacion: Optional[str] = Field(None, max_length=100)

    @validator('precio_mayorista')
    def validate_precio_mayorista(cls, v, values):
        if v is not None and 'precio_costo' in values and 'precio_venta' in values:
            if v <= values['precio_costo']:
                raise ValueError('Precio mayorista debe ser mayor al precio de costo')
            if v > values['precio_venta']:
                raise ValueError('Precio mayorista debe ser menor o igual al precio de venta')
        return v

    @validator('stock_maximo')
    def validate_stock_maximo(cls, v, values):
        if v is not None and 'stock_minimo' in values and v <= values['stock_minimo']:
            raise ValueError('Stock máximo debe ser mayor al stock mínimo')
        return v

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=3, max_length=50)
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = Field(None, min_length=3, max_length=100)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    precio_costo: Optional[Decimal] = Field(None, gt=0)
    precio_venta: Optional[Decimal] = Field(None, gt=0)
    precio_mayorista: Optional[Decimal] = Field(None, gt=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, gt=0)
    ubicacion_deposito: Optional[str] = Field(None, max_length=100)
    peso_kg: Optional[Decimal] = Field(None, gt=0)
    dimensiones: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None

class ProductoResponse(ProductoBase):
    id: int
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]
    stock_critico: bool
    margen_ganancia: Optional[float]

    class Config:
        from_attributes = True

# Schemas de Movimiento Stock
class MovimientoStockBase(BaseModel):
    producto_id: int
    tipo_movimiento: TipoMovimiento
    subtipo: Optional[str] = Field(None, max_length=50)
    cantidad: int = Field(..., ne=0)  # No puede ser cero
    precio_unitario: Optional[Decimal] = Field(None, gt=0)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    lote_numero: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[datetime] = None
    ubicacion_origen: Optional[str] = Field(None, max_length=100)
    ubicacion_destino: Optional[str] = Field(None, max_length=100)
    usuario: str = Field(..., min_length=3, max_length=100)
    observaciones: Optional[str] = None

class MovimientoStockCreate(MovimientoStockBase):
    pass

class MovimientoStockResponse(MovimientoStockBase):
    id: int
    stock_anterior: int
    stock_posterior: int
    valor_total: Optional[Decimal]
    fecha_movimiento: datetime
    estado: EstadoMovimiento
    fecha_confirmacion: Optional[datetime]
    usuario_confirmacion: Optional[str]

    class Config:
        from_attributes = True

# Schemas de Actualización de Stock
class StockUpdateRequest(BaseModel):
    producto_id: int
    cantidad: int = Field(..., ne=0)
    tipo_movimiento: TipoMovimiento
    subtipo: Optional[str] = Field(None, max_length=50)
    precio_unitario: Optional[Decimal] = Field(None, gt=0)
    documento_referencia: Optional[str] = Field(None, max_length=100)
    usuario: str = Field(..., min_length=3, max_length=100)
    observaciones: Optional[str] = None
    ubicacion_origen: Optional[str] = Field(None, max_length=100)
    ubicacion_destino: Optional[str] = Field(None, max_length=100)

class StockUpdateResponse(BaseModel):
    success: bool
    message: str
    producto_id: int
    stock_anterior: int
    stock_nuevo: int
    movimiento_id: int

# Schemas de Cliente
class ClienteBase(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=20)
    tipo_cliente: TipoCliente
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    documento_tipo: Optional[str] = Field(None, max_length=10)
    documento_numero: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=50)
    celular: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    condicion_iva: Optional[str] = Field(None, max_length=50)
    lista_precio: Optional[str] = Field("GENERAL", max_length=50)
    limite_credito: Optional[Decimal] = Field(0, ge=0)
    descuento_general: Optional[Decimal] = Field(0, ge=0, le=100)
    activo: bool = True

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Email debe contener @')
        return v

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=3, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=50)
    celular: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    condicion_iva: Optional[str] = Field(None, max_length=50)
    lista_precio: Optional[str] = Field(None, max_length=50)
    limite_credito: Optional[Decimal] = Field(None, ge=0)
    descuento_general: Optional[Decimal] = Field(None, ge=0, le=100)
    activo: Optional[bool] = None

class ClienteResponse(ClienteBase):
    id: int
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]
    nombre_completo: str

    class Config:
        from_attributes = True

# Schemas de Proveedor
class ProveedorBase(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=20)
    razon_social: str = Field(..., min_length=3, max_length=200)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    cuit: Optional[str] = Field(None, max_length=13)
    tipo_documento: Optional[str] = Field(None, max_length=10)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    sitio_web: Optional[str] = Field(None, max_length=200)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: Optional[str] = Field("Argentina", max_length=100)
    condicion_iva: Optional[str] = Field(None, max_length=50)
    condicion_pago: Optional[str] = Field(None, max_length=100)
    descuento_general: Optional[Decimal] = Field(0, ge=0, le=100)
    activo: bool = True

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorResponse(ProveedorBase):
    id: int
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]

    class Config:
        from_attributes = True

# Schemas de respuesta común
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# Schemas para reportes
class ProductoStockCritico(BaseModel):
    id: int
    codigo: str
    nombre: str
    categoria: str
    stock_actual: int
    stock_minimo: int
    diferencia: int
    ubicacion_deposito: Optional[str]

class ResumenStock(BaseModel):
    total_productos: int
    productos_activos: int
    productos_stock_critico: int
    valor_total_inventario: Decimal
    productos_sin_stock: int
    categorias_con_stock_critico: List[str]

# Schemas para filtros
class ProductoFilter(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    stock_critico: Optional[bool] = None
    activo: Optional[bool] = True
    precio_min: Optional[Decimal] = None
    precio_max: Optional[Decimal] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class MovimientoFilter(BaseModel):
    producto_id: Optional[int] = None
    tipo_movimiento: Optional[TipoMovimiento] = None
    usuario: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    documento_referencia: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
