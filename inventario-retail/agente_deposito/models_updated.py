"""
Modelos de Base de Datos - Sistema Gestión Depósito
Implementación SQLAlchemy con constraints y relaciones
"""

from sqlalchemy import (
    Column, Integer, String, Decimal, DateTime, Boolean, 
    Text, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()

class Producto(Base):
    """
    Modelo Producto - Catálogo completo de productos
    """
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(100), nullable=False, index=True)
    marca = Column(String(100))
    modelo = Column(String(100))

    # Precios
    precio_costo = Column(Decimal(12, 2), nullable=False)
    precio_venta = Column(Decimal(12, 2), nullable=False)
    precio_mayorista = Column(Decimal(12, 2))

    # Stock y control
    stock_actual = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=False, default=0)
    stock_maximo = Column(Integer)

    # Ubicación y medidas
    ubicacion_deposito = Column(String(100))
    peso_kg = Column(Decimal(8, 3))
    dimensiones = Column(String(100))  # "LxAxH en cm"

    # Control de estado
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())
    usuario_creacion = Column(String(100))

    # Relaciones
    movimientos = relationship("MovimientoStock", back_populates="producto")

    # Constraints
    __table_args__ = (
        CheckConstraint('precio_costo > 0', name='chk_precio_costo_positivo'),
        CheckConstraint('precio_venta > 0', name='chk_precio_venta_positivo'),
        CheckConstraint('stock_actual >= 0', name='chk_stock_no_negativo'),
        CheckConstraint('stock_minimo >= 0', name='chk_stock_minimo_no_negativo'),
        Index('idx_producto_categoria_activo', 'categoria', 'activo'),
        Index('idx_producto_stock_critico', 'stock_actual', 'stock_minimo'),
    )

    def __repr__(self):
        return f"<Producto(codigo='{self.codigo}', nombre='{self.nombre}', stock={self.stock_actual})>"

    @property
    def stock_critico(self) -> bool:
        """Indica si el producto está en stock crítico"""
        return self.stock_actual <= self.stock_minimo

    @property
    def margen_ganancia(self) -> Optional[float]:
        """Calcula el margen de ganancia"""
        if self.precio_costo and self.precio_venta:
            return float((self.precio_venta - self.precio_costo) / self.precio_costo * 100)
        return None


class MovimientoStock(Base):
    """
    Modelo MovimientoStock - Historial completo de movimientos
    """
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)

    # Tipo de movimiento
    tipo_movimiento = Column(String(50), nullable=False)  # ENTRADA, SALIDA, AJUSTE, TRANSFERENCIA
    subtipo = Column(String(50))  # COMPRA, VENTA, DEVOLUCION, CORRECCION, etc.

    # Cantidad y valores
    cantidad = Column(Integer, nullable=False)
    stock_anterior = Column(Integer, nullable=False)
    stock_posterior = Column(Integer, nullable=False)
    precio_unitario = Column(Decimal(12, 2))
    valor_total = Column(Decimal(15, 2))

    # Referencias externas
    documento_referencia = Column(String(100))  # Número factura, remito, etc.
    lote_numero = Column(String(50))
    fecha_vencimiento = Column(DateTime)

    # Ubicaciones
    ubicacion_origen = Column(String(100))
    ubicacion_destino = Column(String(100))

    # Auditoria
    fecha_movimiento = Column(DateTime, default=func.now(), nullable=False)
    usuario = Column(String(100), nullable=False)
    observaciones = Column(Text)

    # Estado del movimiento
    estado = Column(String(20), default='CONFIRMADO')  # PENDIENTE, CONFIRMADO, ANULADO
    fecha_confirmacion = Column(DateTime)
    usuario_confirmacion = Column(String(100))

    # Relaciones
    producto = relationship("Producto", back_populates="movimientos")

    # Constraints
    __table_args__ = (
        CheckConstraint("cantidad != 0", name='chk_cantidad_no_cero'),
        CheckConstraint("stock_anterior >= 0", name='chk_stock_anterior_no_negativo'),
        CheckConstraint("stock_posterior >= 0", name='chk_stock_posterior_no_negativo'),
        CheckConstraint("tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE', 'TRANSFERENCIA')", 
                       name='chk_tipo_movimiento_valido'),
        Index('idx_movimiento_producto_fecha', 'producto_id', 'fecha_movimiento'),
        Index('idx_movimiento_tipo_fecha', 'tipo_movimiento', 'fecha_movimiento'),
        Index('idx_movimiento_documento', 'documento_referencia'),
    )

    def __repr__(self):
        return f"<MovimientoStock(producto_id={self.producto_id}, tipo='{self.tipo_movimiento}', cantidad={self.cantidad})>"


class Proveedor(Base):
    """
    Modelo Proveedor - Información de proveedores
    """
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)
    razon_social = Column(String(200), nullable=False)
    nombre_fantasia = Column(String(200))

    # Identificación fiscal
    cuit = Column(String(13), unique=True)  # Format: XX-XXXXXXXX-X
    tipo_documento = Column(String(10))  # CUIT, CUIL, DNI

    # Contacto
    telefono = Column(String(50))
    email = Column(String(150))
    sitio_web = Column(String(200))

    # Dirección
    direccion = Column(String(200))
    ciudad = Column(String(100))
    provincia = Column(String(100))
    codigo_postal = Column(String(10))
    pais = Column(String(100), default='Argentina')

    # Información comercial
    condicion_iva = Column(String(50))  # Responsable Inscripto, Monotributo, etc.
    condicion_pago = Column(String(100))  # 30 días, contado, etc.
    descuento_general = Column(Decimal(5, 2), default=0)

    # Estado y auditoria
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        Index('idx_proveedor_cuit', 'cuit'),
        Index('idx_proveedor_razon_social', 'razon_social'),
    )

    def __repr__(self):
        return f"<Proveedor(codigo='{self.codigo}', razon_social='{self.razon_social}')>"


class Cliente(Base):
    """
    Modelo Cliente - Información de clientes
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, nullable=False)

    # Tipo de cliente
    tipo_cliente = Column(String(20), nullable=False)  # PERSONA, EMPRESA

    # Datos personales/empresa
    razon_social = Column(String(200))
    nombre = Column(String(100))
    apellido = Column(String(100))
    nombre_fantasia = Column(String(200))

    # Identificación
    documento_tipo = Column(String(10))  # DNI, CUIT, CUIL, PASAPORTE
    documento_numero = Column(String(20), unique=True)

    # Contacto
    telefono = Column(String(50))
    celular = Column(String(50))
    email = Column(String(150))

    # Dirección
    direccion = Column(String(200))
    ciudad = Column(String(100))
    provincia = Column(String(100))
    codigo_postal = Column(String(10))

    # Información comercial
    condicion_iva = Column(String(50))
    lista_precio = Column(String(50), default='GENERAL')  # GENERAL, MAYORISTA, ESPECIAL
    limite_credito = Column(Decimal(12, 2), default=0)
    descuento_general = Column(Decimal(5, 2), default=0)

    # Estado y auditoria
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("tipo_cliente IN ('PERSONA', 'EMPRESA')", name='chk_tipo_cliente_valido'),
        Index('idx_cliente_documento', 'documento_tipo', 'documento_numero'),
        Index('idx_cliente_nombre_apellido', 'nombre', 'apellido'),
    )

    def __repr__(self):
        if self.tipo_cliente == 'PERSONA':
            return f"<Cliente(codigo='{self.codigo}', nombre='{self.nombre} {self.apellido}')>"
        else:
            return f"<Cliente(codigo='{self.codigo}', razon_social='{self.razon_social}')>"

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo según el tipo de cliente"""
        if self.tipo_cliente == 'PERSONA':
            return f"{self.nombre} {self.apellido}".strip()
        else:
            return self.razon_social or self.nombre_fantasia or ''
