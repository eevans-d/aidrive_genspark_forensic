#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Market FastAPI Integration
===============================

API REST para el sistema integrado de proveedores Mini Market con persistencia
en base de datos SQLite.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import json

from database_provider_integration import MiniMarketDatabaseManager, DatabaseResult
from provider_logic import MiniMarketProviderLogic, enhance_ocr_with_provider_logic

# Configuración de la aplicación
app = FastAPI(
    title="Mini Market Provider System API",
    description="API REST para el sistema de proveedores Mini Market con persistencia",
    version="1.0.0"
)

# Gestor de base de datos global
db_manager = None

def get_db_manager():
    """Dependencia para obtener el gestor de base de datos"""
    global db_manager
    if db_manager is None:
        try:
            db_manager = MiniMarketDatabaseManager("minimarket_inventory.db")
        except FileNotFoundError:
            raise HTTPException(
                status_code=500, 
                detail="Base de datos no inicializada. Ejecuta database_init_minimarket.py"
            )
    return db_manager

# Modelos Pydantic
class ComandoRequest(BaseModel):
    comando: str
    usuario: Optional[str] = "api_user"

class AsignacionProveedorRequest(BaseModel):
    producto: str
    categoria: Optional[str] = None

class MovimientoStockRequest(BaseModel):
    producto_nombre: str
    tipo_movimiento: str  # 'entrada' o 'salida'
    cantidad: int
    proveedor_codigo: Optional[str] = None
    origen: Optional[str] = ""
    destino: Optional[str] = ""
    observaciones: Optional[str] = ""
    usuario: Optional[str] = "api"

class PedidoRequest(BaseModel):
    productos: List[Dict[str, Any]]
    observaciones: Optional[str] = ""

class FacturaOCRRequest(BaseModel):
    factura_numero: str
    proveedor_original: Optional[str] = ""
    productos: List[Dict[str, Any]]
    total: Optional[float] = 0.0

# Endpoints principales

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Mini Market Provider System API",
        "version": "1.0.0",
        "endpoints": {
            "comando": "/comando - Procesa comandos en lenguaje natural",
            "asignar_proveedor": "/asignar_proveedor - Asigna proveedor a un producto",
            "pedidos": "/pedidos - Gestión de pedidos",
            "stock": "/stock - Gestión de movimientos de stock",
            "ocr": "/ocr - Procesamiento de facturas OCR",
            "resumen": "/resumen - Informes y resúmenes"
        }
    }

@app.post("/comando")
def procesar_comando(
    request: ComandoRequest,
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Procesa un comando en lenguaje natural y lo registra en la base de datos
    
    Ejemplos de comandos:
    - "Pedir Coca Cola x 6"
    - "Falta Sprite lima limón"
    - "Dejé 4 bananas del ecuador"
    - "Saqué 2 galletitas para el kiosco"
    """
    try:
        result = db_manager.procesar_comando_con_bd(request.comando, request.usuario)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data,
                "comando_original": request.comando,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@app.post("/asignar_proveedor")
def asignar_proveedor(
    request: AsignacionProveedorRequest,
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Asigna un proveedor a un producto específico basado en la lógica de proveedores
    """
    try:
        provider_logic = db_manager.provider_logic
        result = provider_logic.asignar_proveedor(request.producto, request.categoria)
        
        return {
            "success": True,
            "producto": request.producto,
            "categoria": request.categoria,
            "proveedor_asignado": {
                "codigo": result.provider_code,
                "nombre": result.provider_name,
                "confidence": result.confidence,
                "match_type": result.match_type
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error asignando proveedor: {e}")

@app.post("/pedidos/registrar")
def registrar_pedido(
    request: PedidoRequest,
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Registra un pedido completo con múltiples productos
    
    Formato de productos:
    [
        {"producto": "Coca Cola", "cantidad": 6, "proveedor_codigo": "CO"},
        {"producto": "Bananas", "cantidad": 5, "proveedor_codigo": "FR"}
    ]
    """
    try:
        result = db_manager.registrar_pedido_completo(
            request.productos, 
            request.observaciones
        )
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando pedido: {e}")

@app.post("/stock/movimiento")
def registrar_movimiento_stock(
    request: MovimientoStockRequest,
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Registra un movimiento de stock (entrada/salida)
    """
    try:
        result = db_manager.registrar_movimiento_stock(
            producto_nombre=request.producto_nombre,
            tipo_movimiento=request.tipo_movimiento,
            cantidad=request.cantidad,
            proveedor_codigo=request.proveedor_codigo,
            origen=request.origen,
            destino=request.destino,
            observaciones=request.observaciones,
            usuario=request.usuario
        )
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando movimiento: {e}")

@app.post("/ocr/procesar_factura")
def procesar_factura_ocr(
    request: FacturaOCRRequest,
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Procesa una factura mediante OCR, asigna proveedores y registra movimientos
    """
    try:
        # Preparar datos de la factura
        factura_data = {
            "factura_numero": request.factura_numero,
            "proveedor_original": request.proveedor_original,
            "productos": request.productos,
            "total": request.total
        }
        
        # Procesar con lógica de proveedores
        provider_logic = db_manager.provider_logic
        enhanced_result = enhance_ocr_with_provider_logic(factura_data, provider_logic)
        
        # Registrar en base de datos
        result = db_manager.registrar_factura_ocr(enhanced_result)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "factura_procesada": enhanced_result,
                "data_bd": result.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando factura OCR: {e}")

@app.get("/resumen/pedidos")
def obtener_resumen_pedidos(
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Obtiene un resumen de pedidos en un rango de fechas
    """
    try:
        result = db_manager.obtener_resumen_pedidos(fecha_desde, fecha_hasta)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {e}")

@app.get("/resumen/stock_bajo")
def obtener_stock_bajo(
    limite_stock: int = Query(5, description="Límite de stock para considerar 'bajo'"),
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Obtiene productos con stock bajo
    """
    try:
        result = db_manager.obtener_stock_bajo(limite_stock)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "data": result.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo stock bajo: {e}")

@app.get("/proveedores")
def obtener_proveedores(
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Obtiene la lista completa de proveedores configurados
    """
    try:
        provider_logic = db_manager.provider_logic
        proveedores = []
        
        for codigo, config in provider_logic.PROVIDERS.items():
            proveedores.append({
                "codigo": codigo,
                "nombre": config["name"],
                "categorias": config.get("categorias", []),
                "marcas_directas": config.get("marcas_directas", []),
                "marcas_distribuidas": config.get("marcas_distribuidas", []),
                "exclude_keywords": config.get("exclude_keywords", [])
            })
        
        return {
            "success": True,
            "message": f"Lista de {len(proveedores)} proveedores",
            "proveedores": proveedores,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proveedores: {e}")

@app.get("/status")
def obtener_status_sistema(
    db_manager: MiniMarketDatabaseManager = Depends(get_db_manager)
):
    """
    Obtiene el estado general del sistema
    """
    try:
        # Obtener estadísticas básicas
        resumen_pedidos = db_manager.obtener_resumen_pedidos()
        stock_bajo = db_manager.obtener_stock_bajo()
        
        return {
            "success": True,
            "sistema": {
                "version": "1.0.0",
                "estado": "operativo",
                "base_datos": "conectada",
                "proveedores_configurados": len(db_manager.provider_logic.PROVIDERS)
            },
            "estadisticas": {
                "total_pedidos": resumen_pedidos.data["total_pedidos"] if resumen_pedidos.success else 0,
                "productos_stock_bajo": stock_bajo.data["total_productos"] if stock_bajo.success else 0,
                "total_facturado": resumen_pedidos.data["total_general"] if resumen_pedidos.success else 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo status: {e}")

# Manejador de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    print("🏪 === INICIANDO API MINI MARKET ===")
    print()
    print("📊 Endpoints disponibles:")
    print("• POST /comando - Comandos en lenguaje natural")
    print("• POST /asignar_proveedor - Asignación de proveedores")
    print("• POST /pedidos/registrar - Registro de pedidos")
    print("• POST /stock/movimiento - Movimientos de stock")
    print("• POST /ocr/procesar_factura - Procesamiento OCR")
    print("• GET /resumen/pedidos - Resumen de pedidos")
    print("• GET /resumen/stock_bajo - Productos con stock bajo")
    print("• GET /proveedores - Lista de proveedores")
    print("• GET /status - Estado del sistema")
    print()
    print("🌐 Servidor iniciando en: http://localhost:8000")
    print("📚 Documentación en: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")