# 🗄️ MODELOS DE BASE DE DATOS MINI MARKET
## Extensiones para proveedores y pedidos

```python
"""
Modelos de base de datos para proveedores Mini Market
Extensión del sistema de shared/models.py
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from shared.database import Base

class Proveedor(Base):
    """Modelo de proveedor Mini Market"""
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, index=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(50))
    email = Column(String(100))
    activo = Column(Integer, default=1)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Proveedor(codigo='{self.codigo}', nombre='{self.nombre}')>"

class Pedido(Base):
    """Modelo de pedido a proveedor"""
    __tablename__ = 'pedidos'
    
    id = Column(Integer, primary_key=True, index=True)
    proveedor_code = Column(String(10), nullable=False, index=True)
    producto = Column(String(500), nullable=False)
    cantidad = Column(Integer, default=1)
    estado = Column(String(50), default="Pendiente", index=True)
    empleado_turno = Column(String(100))
    fecha_pedido = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_completado = Column(DateTime, nullable=True)
    confidence_asignacion = Column(Float, default=0.0)
    match_type = Column(String(50))
    observaciones = Column(Text)
    
    def __repr__(self):
        return f"<Pedido(id={self.id}, producto='{self.producto}', proveedor='{self.proveedor_code}')>"

class StockMovimiento(Base):
    """Registro de movimientos de stock (entrada/salida)"""
    __tablename__ = 'stock_movimientos'
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False, index=True)  # 'entrada', 'salida'
    producto = Column(String(500), nullable=False)
    cantidad = Column(Integer, nullable=False)
    origen_destino = Column(String(200))  # proveedor origen o destino
    empleado = Column(String(100))
    fecha_movimiento = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    comando_original = Column(Text)  # comando natural que generó el movimiento
    
    def __repr__(self):
        return f"<StockMovimiento(tipo='{self.tipo}', producto='{self.producto}', cantidad={self.cantidad})>"

# Datos iniciales para proveedores
PROVEEDORES_INICIALES = [
    {'codigo': 'BC', 'nombre': 'Bodega Cedeira', 'contacto': 'Representante BC'},
    {'codigo': 'CO', 'nombre': 'Coca Cola', 'contacto': 'Distribuidor Coca Cola'},
    {'codigo': 'Q', 'nombre': 'Quilmes', 'contacto': 'Distribuidor Quilmes'},
    {'codigo': 'FA', 'nombre': 'Fargo', 'contacto': 'Distribuidor Fargo'},
    {'codigo': 'LS', 'nombre': 'La Serenísima', 'contacto': 'Distribuidor LS'},
    {'codigo': 'ACE', 'nombre': 'Aceitumar (MDP)', 'contacto': 'Aceitumar Mar del Plata'},
    {'codigo': 'TER', 'nombre': 'Terrabusi (Mondelez)', 'contacto': 'Distribuidor Terrabusi'},
    {'codigo': 'LV', 'nombre': 'La Virginia', 'contacto': 'Distribuidor La Virginia'},
    {'codigo': 'FR', 'nombre': 'Frutas y Verduras (Bicho)', 'contacto': 'Bicho - Verdulería'},
    {'codigo': 'MU', 'nombre': 'Multienvase (MDP)', 'contacto': 'Multienvase Mar del Plata'},
    {'codigo': 'GA', 'nombre': 'Galletitera (MDP)', 'contacto': 'Galletitera Mar del Plata'},
    {'codigo': 'MAX', 'nombre': 'Maxiconsumo', 'contacto': 'Mayorista Maxiconsumo'}
]
```

---

## 🔧 **SCRIPT DE INICIALIZACIÓN**

```python
"""
Inicialización de datos Mini Market
Script para crear proveedores iniciales
"""

import logging
from sqlalchemy.orm import sessionmaker
from shared.database import engine, Base
from .models import Proveedor, PROVEEDORES_INICIALES

logger = logging.getLogger(__name__)

def init_providers():
    """Inicializa proveedores Mini Market en base de datos"""
    try:
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        # Crear sesión
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Verificar si ya existen proveedores
            existing_count = db.query(Proveedor).count()
            if existing_count > 0:
                logger.info(f"Ya existen {existing_count} proveedores. Saltando inicialización.")
                return
            
            # Crear proveedores iniciales
            for proveedor_data in PROVEEDORES_INICIALES:
                proveedor = Proveedor(**proveedor_data)
                db.add(proveedor)
            
            db.commit()
            logger.info(f"Creados {len(PROVEEDORES_INICIALES)} proveedores Mini Market")
            
            # Verificar creación
            for proveedor in db.query(Proveedor).all():
                logger.info(f"Proveedor creado: {proveedor.codigo} - {proveedor.nombre}")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error inicializando proveedores: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error crítico inicializando proveedores: {e}")
        raise

if __name__ == "__main__":
    init_providers()
```