"""
Modelos SQLAlchemy para sistema multi-agente retail argentino
Incluye constraints SQL, validaciones y auditoría automática
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, CheckConstraint, Index, UniqueConstraint, text
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import Optional
import re

from .database import Base


class Producto(Base):
    """
    Modelo de Producto para retail argentino
    Incluye validaciones específicas y constraints de negocio
    """
    __tablename__ = "productos"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(100), nullable=False, default="General")

    # Stock y precios (campos críticos con constraints)
    stock_actual = Column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Stock actual - no puede ser negativo"
    )
    stock_minimo = Column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Stock mínimo para alerta - ajustable por temporada"
    )
    stock_maximo = Column(
        Integer,
        nullable=True,
        doc="Stock máximo sugerido para compras"
    )

    # Precios en formato argentino (centavos para precisión)
    precio_compra = Column(
        Float,
        nullable=False,
        doc="Precio de compra al proveedor (pesos argentinos)"
    )
    precio_venta = Column(
        Float,
        nullable=True,
        doc="Precio de venta sugerido"
    )

    # Información proveedor
    proveedor_cuit = Column(String(13), nullable=True, index=True)
    proveedor_nombre = Column(String(200), nullable=True)

    # Metadatos
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    movimientos = relationship("MovimientoStock", back_populates="producto")

    # Constraints SQL a nivel de tabla
    __table_args__ = (
        # Stock no puede ser negativo
        CheckConstraint("stock_actual >= 0", name="ck_stock_actual_positive"),
        CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo_positive"),
        CheckConstraint("stock_maximo IS NULL OR stock_maximo >= stock_minimo", 
                       name="ck_stock_maximo_valid"),

        # Precios deben ser positivos
        CheckConstraint("precio_compra > 0", name="ck_precio_compra_positive"),
        CheckConstraint("precio_venta IS NULL OR precio_venta > 0", 
                       name="ck_precio_venta_positive"),

        # Código no puede estar vacío
        CheckConstraint("length(trim(codigo)) > 0", name="ck_codigo_not_empty"),
        CheckConstraint("length(trim(nombre)) > 0", name="ck_nombre_not_empty"),

        # CUIT formato válido (si existe)
        CheckConstraint(
            "proveedor_cuit IS NULL OR (length(proveedor_cuit) IN (11, 13) AND proveedor_cuit GLOB '[0-9-]*')",
            name="ck_cuit_format"
        ),

        # Índices para performance
        Index("idx_producto_categoria_activo", "categoria", "activo"),
        Index("idx_producto_stock_critico", "stock_actual", "stock_minimo"),
        Index("idx_producto_proveedor", "proveedor_cuit", "activo"),
    )

    @validates("codigo")
    def validate_codigo(self, key, value):
        """Validar formato de código de producto"""
        if not value or not value.strip():
            raise ValueError("Código de producto no puede estar vacío")

        # Convertir a mayúsculas y limpiar
        value = value.strip().upper()

        # Validar formato básico (alfanumérico + guiones)
        if not re.match(r"^[A-Z0-9\-_]+$", value):
            raise ValueError("Código solo puede contener letras, números, guiones y guiones bajos")

        return value

    @validates("proveedor_cuit")
    def validate_cuit(self, key, value):
        """Validar formato CUIT argentino"""
        if not value:
            return None

        # Limpiar CUIT (solo números y guiones)
        value = re.sub(r"[^\d\-]", "", value)

        # Validar formato básico
        if not re.match(r"^\d{2}-?\d{8}-?\d{1}$", value):
            raise ValueError("CUIT debe tener formato XX-XXXXXXXX-X")

        return value

    @validates("precio_compra", "precio_venta")
    def validate_precios(self, key, value):
        """Validar que los precios sean positivos"""
        if value is not None and value <= 0:
            raise ValueError(f"{key} debe ser mayor a 0")
        return value

    def is_stock_critico(self, factor_temporada: float = 1.0) -> bool:
        """
        Determina si el producto tiene stock crítico
        Considera factor estacional para stock mínimo
        """
        stock_minimo_ajustado = self.stock_minimo * factor_temporada
        return self.stock_actual <= stock_minimo_ajustado

    def precio_con_inflacion(self, dias_transcurridos: int, inflacion_diaria: float) -> float:
        """
        Calcula precio actualizado con inflación
        """
        if dias_transcurridos <= 0:
            return self.precio_compra

        factor_inflacion = (1 + inflacion_diaria) ** dias_transcurridos
        return self.precio_compra * factor_inflacion

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario para JSON"""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "stock_actual": self.stock_actual,
            "stock_minimo": self.stock_minimo,
            "stock_maximo": self.stock_maximo,
            "precio_compra": self.precio_compra,
            "precio_venta": self.precio_venta,
            "proveedor_cuit": self.proveedor_cuit,
            "proveedor_nombre": self.proveedor_nombre,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Producto(codigo='{self.codigo}', nombre='{self.nombre}', stock={self.stock_actual})>"


class MovimientoStock(Base):
    """
    Modelo de auditoría para movimientos de stock
    Registra todos los cambios con trazabilidad completa
    """
    __tablename__ = "movimientos_stock"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)

    # Tipo de movimiento
    tipo_movimiento = Column(
        String(20), 
        nullable=False,
        doc="Tipo: 'entrada', 'salida', 'ajuste', 'transferencia'"
    )

    # Cantidades y stock
    cantidad = Column(
        Integer, 
        nullable=False,
        doc="Cantidad del movimiento (positiva para entrada, negativa para salida)"
    )
    stock_anterior = Column(
        Integer, 
        nullable=False,
        doc="Stock antes del movimiento"
    )
    stock_posterior = Column(
        Integer, 
        nullable=False,
        doc="Stock después del movimiento"
    )

    # Información del movimiento
    motivo = Column(String(200), nullable=True, doc="Motivo del movimiento")
    referencia = Column(String(100), nullable=True, doc="Número de factura, remito, etc.")
    precio_unitario = Column(Float, nullable=True, doc="Precio unitario del movimiento")

    # Información de origen/destino
    origen = Column(String(100), nullable=True, doc="Origen del movimiento")
    destino = Column(String(100), nullable=True, doc="Destino del movimiento")

    # Metadatos y auditoría
    usuario = Column(String(100), nullable=True, doc="Usuario que realizó el movimiento")
    agente_origen = Column(String(50), nullable=True, doc="Agente que originó el movimiento")
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)

    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relaciones
    producto = relationship("Producto", back_populates="movimientos")

    # Constraints SQL
    __table_args__ = (
        # Validar tipos de movimiento
        CheckConstraint(
            "tipo_movimiento IN ('entrada', 'salida', 'ajuste', 'transferencia')",
            name="ck_tipo_movimiento_valid"
        ),

        # Cantidad no puede ser cero
        CheckConstraint("cantidad != 0", name="ck_cantidad_not_zero"),

        # Stock no puede ser negativo
        CheckConstraint("stock_anterior >= 0", name="ck_stock_anterior_positive"),
        CheckConstraint("stock_posterior >= 0", name="ck_stock_posterior_positive"),

        # Consistencia del movimiento
        CheckConstraint(
            "stock_posterior = stock_anterior + cantidad",
            name="ck_movimiento_consistency"
        ),

        # Precio unitario debe ser positivo si existe
        CheckConstraint(
            "precio_unitario IS NULL OR precio_unitario > 0",
            name="ck_precio_unitario_positive"
        ),

        # Índices para consultas frecuentes
        Index("idx_movimiento_fecha_tipo", "timestamp", "tipo_movimiento"),
        Index("idx_movimiento_producto_fecha", "producto_id", "timestamp"),
        Index("idx_movimiento_referencia", "referencia"),
    )

    @validates("tipo_movimiento")
    def validate_tipo_movimiento(self, key, value):
        """Validar tipo de movimiento"""
        tipos_validos = ["entrada", "salida", "ajuste", "transferencia"]
        if value not in tipos_validos:
            raise ValueError(f"Tipo de movimiento debe ser uno de: {tipos_validos}")
        return value

    @validates("cantidad")
    def validate_cantidad(self, key, value):
        """Validar que la cantidad no sea cero"""
        if value == 0:
            raise ValueError("Cantidad no puede ser cero")
        return value

    def calcular_valor_total(self) -> Optional[float]:
        """Calcula el valor total del movimiento"""
        if self.precio_unitario is not None:
            return abs(self.cantidad) * self.precio_unitario
        return None

    def is_entrada(self) -> bool:
        """Determina si es un movimiento de entrada"""
        return self.cantidad > 0

    def is_salida(self) -> bool:
        """Determina si es un movimiento de salida"""
        return self.cantidad < 0

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario para JSON"""
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "tipo_movimiento": self.tipo_movimiento,
            "cantidad": self.cantidad,
            "stock_anterior": self.stock_anterior,
            "stock_posterior": self.stock_posterior,
            "motivo": self.motivo,
            "referencia": self.referencia,
            "precio_unitario": self.precio_unitario,
            "origen": self.origen,
            "destino": self.destino,
            "usuario": self.usuario,
            "agente_origen": self.agente_origen,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "valor_total": self.calcular_valor_total()
        }

    def __repr__(self):
        return (f"<MovimientoStock(producto_id={self.producto_id}, "
                f"tipo='{self.tipo_movimiento}', cantidad={self.cantidad})>")


class OutboxMessage(Base):
    """
    Modelo para Outbox Pattern - Garantiza entrega de mensajes
    Usado para comunicación confiable entre agentes
    """
    __tablename__ = "outbox_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Contenido del mensaje
    event_type = Column(String(100), nullable=False, doc="Tipo de evento")
    payload = Column(Text, nullable=False, doc="Payload JSON del mensaje")
    destination = Column(String(100), nullable=False, doc="Destino del mensaje")

    # Estado del mensaje
    status = Column(
        String(20), 
        nullable=False, 
        default="pending",
        doc="Estado: pending, sent, failed, cancelled"
    )
    retries = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)

    # Error info
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'cancelled')",
            name="ck_outbox_status_valid"
        ),
        CheckConstraint("retries >= 0", name="ck_retries_positive"),
        CheckConstraint("max_retries >= 0", name="ck_max_retries_positive"),

        Index("idx_outbox_status_retry", "status", "next_retry_at"),
        Index("idx_outbox_created", "created_at"),
    )

    def can_retry(self) -> bool:
        """Determina si el mensaje puede ser reintentado"""
        return (self.status in ["pending", "failed"] and 
                self.retries < self.max_retries)

    def mark_sent(self):
        """Marca el mensaje como enviado exitosamente"""
        self.status = "sent"
        self.sent_at = func.now()

    def mark_failed(self, error_message: str):
        """Marca el mensaje como fallido y programa reinento"""
        self.status = "failed"
        self.retries += 1
        self.last_error = error_message

        if self.retries < self.max_retries:
            # Backoff exponencial: 30s, 60s, 120s, 240s, 480s
            delay_seconds = min(30 * (2 ** self.retries), 480)
            self.next_retry_at = func.datetime('now', f'+{delay_seconds} seconds')

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "destination": self.destination,
            "status": self.status,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "last_error": self.last_error
        }
