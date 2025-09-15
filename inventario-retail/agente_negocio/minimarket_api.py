#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API FastAPI - Sistema Mini Market
=================================

API REST completa para el sistema de proveedores Mini Market con persistencia
en base de datos SQLite y funcionalidades completas de gestión.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json
import uvicorn

# Importar módulos del sistema
from provider_logic import MiniMarketProviderLogic, enhance_ocr_with_provider_logic, StockCommands
from provider_database_integration import MiniMarketDatabaseManager

# Configuración de la aplicación
app = FastAPI(
    title="Sistema Mini Market - API",
    description="API REST para gestión de proveedores, pedidos y stock del Mini Market",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Instancias globales
provider_logic = MiniMarketProviderLogic()
db_manager = MiniMarketDatabaseManager()


# Modelos Pydantic para la API
class ComandoNaturalRequest(BaseModel):
    comando: str = Field(..., description="Comando natural en español", example="Pedir Coca Cola x 6")
    usuario: str = Field(default="api_user", description="Usuario que ejecuta el comando")


class ComandoStockRequest(BaseModel):
    comando: str = Field(..., description="Comando de stock", example="Dejé 4 bananas del ecuador")
    usuario: str = Field(default="api_user", description="Usuario que ejecuta el comando")


class AsignacionProveedorRequest(BaseModel):
    producto: str = Field(..., description="Nombre del producto", example="Coca Cola")
    categoria: Optional[str] = Field(None, description="Categoría del producto", example="bebida")


class FacturaOCRRequest(BaseModel):
    numero_factura: str = Field(..., description="Número de factura", example="F001-12345")
    proveedor_original: Optional[str] = Field(None, description="Proveedor según OCR original")
    productos: List[Dict[str, Any]] = Field(..., description="Lista de productos detectados")
    total: Optional[float] = Field(None, description="Total de la factura")
    fecha_factura: Optional[str] = Field(None, description="Fecha de la factura")
    usuario: str = Field(default="api_user", description="Usuario que procesa la factura")


# Endpoints principales

@app.get("/", summary="Estado de la API")
async def root():
    """Endpoint raíz con información básica de la API"""
    return {
        "mensaje": "API Sistema Mini Market",
        "version": "1.0.0",
        "estado": "activo",
        "proveedores_configurados": len(provider_logic.PROVIDERS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/proveedores", summary="Listar todos los proveedores")
async def listar_proveedores():
    """
    Obtiene la lista completa de proveedores configurados
    
    Returns:
        Lista de proveedores con su configuración
    """
    try:
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
            "total_proveedores": len(proveedores),
            "proveedores": proveedores
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proveedores: {str(e)}")


@app.post("/asignar-proveedor", summary="Asignar proveedor a producto")
async def asignar_proveedor(request: AsignacionProveedorRequest):
    """
    Asigna automáticamente un proveedor a un producto basado en la lógica jerárquica
    
    Args:
        request: Datos del producto para asignación
        
    Returns:
        Información del proveedor asignado con confianza
    """
    try:
        result = provider_logic.asignar_proveedor(request.producto, request.categoria)
        
        return {
            "success": True,
            "producto": request.producto,
            "categoria": request.categoria,
            "proveedor_asignado": {
                "codigo": result.provider_code,
                "nombre": result.provider_name,
                "confianza": result.confidence,
                "tipo_match": result.match_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error asignando proveedor: {str(e)}")


@app.post("/comando-natural", summary="Procesar comando natural")
async def procesar_comando_natural(request: ComandoNaturalRequest):
    """
    Procesa un comando natural y lo registra en la base de datos
    
    Args:
        request: Comando natural a procesar
        
    Returns:
        Resultado del procesamiento y registro
    """
    try:
        # Registrar pedido con persistencia
        resultado = db_manager.registrar_pedido_natural(request.comando, request.usuario)
        
        return {
            "success": resultado['success'],
            "comando_original": request.comando,
            "usuario": request.usuario,
            **resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando comando natural: {str(e)}")


@app.post("/comando-stock", summary="Procesar comando de stock")
async def procesar_comando_stock(request: ComandoStockRequest):
    """
    Procesa un comando de movimiento de stock y lo registra en la base de datos
    
    Args:
        request: Comando de stock a procesar
        
    Returns:
        Resultado del procesamiento y registro
    """
    try:
        # Registrar movimiento con persistencia
        resultado = db_manager.registrar_movimiento_stock(request.comando, request.usuario)
        
        return {
            "success": resultado['success'],
            "comando_original": request.comando,
            "usuario": request.usuario,
            **resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando comando de stock: {str(e)}")


@app.post("/procesar-factura-ocr", summary="Procesar factura OCR")
async def procesar_factura_ocr(request: FacturaOCRRequest):
    """
    Procesa una factura desde OCR, asigna proveedores y registra en BD
    
    Args:
        request: Datos de la factura OCR
        
    Returns:
        Resultado del procesamiento con proveedores asignados
    """
    try:
        # Convertir request a formato OCR estándar
        ocr_data = {
            "factura_numero": request.numero_factura,
            "proveedor_original": request.proveedor_original,
            "productos": request.productos,
            "total": request.total,
            "fecha_factura": request.fecha_factura
        }
        
        # Procesar con persistencia
        resultado = db_manager.procesar_factura_ocr(ocr_data, request.usuario)
        
        return {
            "success": resultado['success'],
            "usuario": request.usuario,
            **resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando factura OCR: {str(e)}")


@app.get("/resumen-pedidos", summary="Obtener resumen de pedidos")
async def obtener_resumen_pedidos(dias: int = Query(7, description="Días a considerar en el resumen")):
    """
    Obtiene un resumen de pedidos por proveedor en los últimos días
    
    Args:
        dias: Número de días a considerar (default: 7)
        
    Returns:
        Resumen de pedidos y movimientos
    """
    try:
        resultado = db_manager.obtener_resumen_pedidos(dias)
        
        if not resultado['success']:
            raise HTTPException(status_code=500, detail=resultado['error'])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")


@app.get("/stock-bajo", summary="Obtener productos con stock bajo")
async def obtener_stock_bajo(limite: int = Query(5, description="Límite de stock considerado bajo")):
    """
    Obtiene productos con stock bajo y sugiere proveedores
    
    Args:
        limite: Cantidad límite para considerar stock bajo
        
    Returns:
        Lista de productos con stock bajo y proveedores sugeridos
    """
    try:
        resultado = db_manager.obtener_stock_bajo(limite)
        
        if not resultado['success']:
            raise HTTPException(status_code=500, detail=resultado['error'])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando stock bajo: {str(e)}")


@app.get("/pedidos-por-proveedor", summary="Obtener pedidos agrupados por proveedor")
async def obtener_pedidos_por_proveedor():
    """
    Obtiene pedidos agrupados por proveedor desde la lógica interna
    
    Returns:
        Pedidos agrupados por proveedor
    """
    try:
        resultado = provider_logic.obtener_pedidos_por_proveedor()
        
        if not resultado['success']:
            raise HTTPException(status_code=500, detail=resultado['error'])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo pedidos por proveedor: {str(e)}")


@app.get("/health", summary="Estado de salud del sistema")
async def health_check():
    """
    Verifica el estado de salud del sistema completo
    
    Returns:
        Estado de todos los componentes
    """
    try:
        # Verificar base de datos
        db_status = "ok"
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM proveedores")
            proveedores_count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            db_status = f"error: {str(e)}"
            proveedores_count = 0
        
        # Verificar lógica de proveedores
        logic_status = "ok"
        try:
            test_result = provider_logic.asignar_proveedor("test producto")
            if not test_result.provider_code:
                logic_status = "warning: no provider assigned"
        except Exception as e:
            logic_status = f"error: {str(e)}"
        
        health_status = {
            "sistema": "Mini Market API",
            "timestamp": datetime.now().isoformat(),
            "componentes": {
                "api": "ok",
                "base_datos": db_status,
                "logica_proveedores": logic_status
            },
            "metricas": {
                "proveedores_configurados": len(provider_logic.PROVIDERS),
                "proveedores_en_bd": proveedores_count
            }
        }
        
        # Determinar status code
        overall_status = "healthy"
        if "error" in db_status or "error" in logic_status:
            overall_status = "unhealthy"
        elif "warning" in db_status or "warning" in logic_status:
            overall_status = "degraded"
        
        health_status["status"] = overall_status
        
        # Status code HTTP basado en la salud
        status_code = 200
        if overall_status == "unhealthy":
            status_code = 503
        elif overall_status == "degraded":
            status_code = 200  # Sigue funcionando pero con advertencias
        
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": f"Error en health check: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


# Función principal para ejecutar el servidor
def main():
    """Función principal para ejecutar el servidor FastAPI"""
    print("🏪 === INICIANDO API SISTEMA MINI MARKET ===")
    print()
    print("📋 Configuración:")
    print(f"  • Proveedores configurados: {len(provider_logic.PROVIDERS)}")
    print(f"  • Base de datos: {db_manager.db_path}")
    print()
    print("🌐 Endpoints disponibles:")
    print("  • Documentación: http://localhost:8000/docs")
    print("  • Estado: http://localhost:8000/health")
    print("  • Proveedores: http://localhost:8000/proveedores")
    print()
    print("🚀 Iniciando servidor...")
    
    uvicorn.run(
        "minimarket_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()