"""
Pydantic schemas para AgenteDepósito
Validaciones de entrada y salida de API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Dict
from datetime import datetime

class ProductoBase(BaseModel):
    """Base para producto"""
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    categoria: str = Field(default="General", max_length=100)
    stock_minimo: int = Field(default=0, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)
    precio_compra: float = Field(..., gt=0)
    precio_venta: Optional[float] = Field(None, gt=0)
    proveedor_cuit: Optional[str] = Field(None, max_length=13)
    proveedor_nombre: Optional[str] = Field(None, max_length=200)

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v or not v.strip():
            raise ValueError('Código no puede estar vacío')
        return v.strip().upper()

class ProductoCreate(ProductoBase):
    """Crear producto"""
    stock_actual: int = Field(default=0, ge=0)

class ProductoUpdate(BaseModel):
    """Actualizar producto"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    categoria: Optional[str] = Field(None, max_length=100)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)
    precio_compra: Optional[float] = Field(None, gt=0)
    precio_venta: Optional[float] = Field(None, gt=0)
    proveedor_cuit: Optional[str] = Field(None, max_length=13)
    proveedor_nombre: Optional[str] = Field(None, max_length=200)
    activo: Optional[bool] = None

class ProductoResponse(ProductoBase):
    """Response de producto"""
    id: int
    stock_actual: int
    activo: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class ProductoListResponse(BaseModel):
    """Response lista productos con paginación"""
    productos: List[ProductoResponse]
    total: int
    skip: int
    limit: int

class StockCriticoResponse(BaseModel):
    """Response para productos con stock crítico"""
    producto_id: int
    codigo: str
    nombre: str
    categoria: str
    stock_actual: int
    stock_minimo_original: int
    stock_minimo_ajustado: int
    factor_temporada: float
    temporada: str
    deficit: int
    precio_compra_formateado: str

class StockUpdateResponse(BaseModel):
    """Response actualización stock"""
    success: bool
    movimiento_id: int
    producto_id: int
    stock_anterior: int
    stock_nuevo: int
    mensaje: str

class HealthResponse(BaseModel):
    """Response health check"""
    status: str
    service: str
    version: str
    timestamp: str
    uptime_seconds: float
    database: Dict[str, Any]
    endpoints_disponibles: List[str]
