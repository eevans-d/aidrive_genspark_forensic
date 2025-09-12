"""
ML Predictor Module - Sistema de Inventario Retail Argentina
===========================================================

Módulo de predicción de demanda usando RandomForest entrenado.
Proporciona endpoints FastAPI para predicciones de demanda a 7 días.

Contexto Argentino:
- Considera inflación mensual del 4.5%
- Incluye feriados nacionales y estacionalidad local
- Optimizado para retail argentino con patrones de consumo locales

Autor: Sistema Multi-Agente Inventario
Versión: Post-MVP con ML
"""

import os
import json
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator
import uvicorn

# Imports del sistema
from ..shared.config import get_config, ARGENTINA_TZ
from ..shared.models import Producto, Venta
from ..shared.database import get_db_session
from .features import DemandFeatures
from .trainer import DemandModelTrainer

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# MODELOS PYDANTIC
# ========================

class PredictionRequest(BaseModel):
    """Request para predicción de demanda"""

    producto_id: int = Field(..., description="ID del producto para predecir")
    dias_prediccion: int = Field(7, ge=1, le=30, description="Días a predecir (1-30)")
    incluir_confianza: bool = Field(True, description="Incluir intervalos de confianza")
    contexto_adicional: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional para predicción")

    @validator('dias_prediccion')
    def validate_dias(cls, v):
        if v not in [1, 3, 7, 14, 30]:
            raise ValueError("días_prediccion debe ser 1, 3, 7, 14 o 30")
        return v

class PredictionResponse(BaseModel):
    """Response de predicción de demanda"""

    producto_id: int
    producto_nombre: str
    predicciones: List[Dict[str, Any]]
    metricas_modelo: Dict[str, float]
    contexto_argentino: Dict[str, Any]
    timestamp: datetime
    confianza_general: float

class HealthResponse(BaseModel):
    """Response de health check"""

    status: str
    ml_model_loaded: bool
    feature_extractor_ready: bool
    database_connected: bool
    timestamp: datetime

# ========================
# PREDICTOR PRINCIPAL
# ========================

class DemandPredictor:
    """
    Predictor de demanda usando RandomForest entrenado.

    Características:
    - Predicciones multi-horizonte (1-30 días)
    - Intervalos de confianza usando quantile regression
    - Contexto argentino (inflación, feriados, estacionalidad)
    - Cache inteligente para predicciones frecuentes
    - Monitoreo de drift del modelo
    """

    def __init__(self, model_path: str = "models/"):
        self.model_path = Path(model_path)
        self.model = None
        self.feature_extractor = None
        self.model_metadata = {}
        self.prediction_cache = {}
        self.cache_ttl = 3600  # 1 hora

        # Configuración Argentina
        self.inflation_rate = 0.045  # 4.5% mensual
        self.currency_format = "ARS"

        self._initialize()

    def _initialize(self):
        """Inicializa el predictor cargando modelo y features"""
        try:
            # Cargar modelo entrenado
            model_file = self.model_path / "demand_model.joblib"
            if model_file.exists():
                self.model = joblib.load(model_file)
                logger.info(f"✅ Modelo cargado desde {model_file}")
            else:
                logger.warning("⚠️  No se encontró modelo entrenado, entrenando nuevo modelo...")
                self._train_new_model()

            # Cargar metadata del modelo
            metadata_file = self.model_path / "model_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.model_metadata = json.load(f)

            # Inicializar extractor de features
            self.feature_extractor = DemandFeatures()

            logger.info("🚀 Predictor inicializado correctamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando predictor: {str(e)}")
            raise

    def _train_new_model(self):
        """Entrena un nuevo modelo si no existe uno guardado"""
        try:
            logger.info("🔄 Entrenando nuevo modelo de demanda...")

            # Crear directorio de modelos
            self.model_path.mkdir(exist_ok=True)

            # Entrenar modelo
            trainer = DemandModelTrainer()
            model_info = trainer.train_model()

            # Guardar modelo
            model_file = self.model_path / "demand_model.joblib"
            joblib.dump(trainer.model, model_file)

            # Guardar metadata
            metadata = {
                'trained_at': datetime.now(ARGENTINA_TZ).isoformat(),
                'model_type': 'RandomForest',
                'accuracy': model_info['accuracy'],
                'features_count': len(model_info['feature_importance']),
                'training_samples': model_info.get('training_samples', 0)
            }

            metadata_file = self.model_path / "model_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Asignar modelo entrenado
            self.model = trainer.model
            self.model_metadata = metadata

            logger.info(f"✅ Nuevo modelo entrenado con accuracy: {model_info['accuracy']:.3f}")

        except Exception as e:
            logger.error(f"❌ Error entrenando modelo: {str(e)}")
            raise

    def predict_demand(self, 
                      producto_id: int, 
                      dias_prediccion: int = 7,
                      incluir_confianza: bool = True) -> Dict[str, Any]:
        """
        Predice demanda para un producto específico

        Args:
            producto_id: ID del producto
            dias_prediccion: Número de días a predecir
            incluir_confianza: Si incluir intervalos de confianza

        Returns:
            Diccionario con predicciones y metadata
        """
        try:
            # Verificar cache
            cache_key = f"{producto_id}_{dias_prediccion}_{incluir_confianza}"
            if self._is_cache_valid(cache_key):
                logger.info(f"📋 Usando predicción cacheada para producto {producto_id}")
                return self.prediction_cache[cache_key]['data']

            # Obtener datos del producto
            with get_db_session() as db:
                producto = db.query(Producto).filter(Producto.id == producto_id).first()
                if not producto:
                    raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")

            # Extraer features para predicción
            features_df = self.feature_extractor.extract_prediction_features(
                producto_id=producto_id,
                prediction_days=dias_prediccion
            )

            if features_df.empty:
                raise ValueError(f"No se pudieron extraer features para producto {producto_id}")

            # Realizar predicción
            predictions = self.model.predict(features_df)

            # Calcular intervalos de confianza si es solicitado
            confidence_intervals = None
            if incluir_confianza and hasattr(self.model, 'estimators_'):
                confidence_intervals = self._calculate_confidence_intervals(
                    features_df, predictions
                )

            # Formatear resultados
            result = self._format_prediction_result(
                producto=producto,
                predictions=predictions,
                confidence_intervals=confidence_intervals,
                dias_prediccion=dias_prediccion
            )

            # Cachear resultado
            self.prediction_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now(ARGENTINA_TZ)
            }

            logger.info(f"✅ Predicción generada para producto {producto_id}: {len(predictions)} días")
            return result

        except Exception as e:
            logger.error(f"❌ Error en predicción para producto {producto_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")

    def _calculate_confidence_intervals(self, features_df: pd.DataFrame, predictions: np.ndarray) -> Dict[str, List[float]]:
        """Calcula intervalos de confianza usando estimadores del Random Forest"""
        try:
            # Obtener predicciones de todos los árboles
            tree_predictions = np.array([
                tree.predict(features_df) for tree in self.model.estimators_
            ])

            # Calcular percentiles para intervalos de confianza
            lower_bound = np.percentile(tree_predictions, 10, axis=0)  # 10%
            upper_bound = np.percentile(tree_predictions, 90, axis=0)  # 90%

            return {
                'lower': lower_bound.tolist(),
                'upper': upper_bound.tolist(),
                'std': np.std(tree_predictions, axis=0).tolist()
            }

        except Exception as e:
            logger.warning(f"⚠️  No se pudieron calcular intervalos de confianza: {str(e)}")
            return None

    def _format_prediction_result(self, 
                                 producto: Producto,
                                 predictions: np.ndarray,
                                 confidence_intervals: Optional[Dict],
                                 dias_prediccion: int) -> Dict[str, Any]:
        """Formatea el resultado de predicción para la API"""

        # Generar fechas de predicción
        start_date = datetime.now(ARGENTINA_TZ).date()
        prediction_dates = [
            start_date + timedelta(days=i) for i in range(1, dias_prediccion + 1)
        ]

        # Formatear predicciones por día
        predicciones_detalle = []
        for i, fecha in enumerate(prediction_dates):
            pred_dia = {
                'fecha': fecha.isoformat(),
                'demanda_predicha': max(0, round(predictions[i], 2)),  # No negativas
                'dia_semana': fecha.strftime('%A'),
                'es_feriado': self.feature_extractor.holidays.is_holiday(fecha)
            }

            # Agregar intervalos de confianza si están disponibles
            if confidence_intervals:
                pred_dia.update({
                    'confianza_inferior': max(0, round(confidence_intervals['lower'][i], 2)),
                    'confianza_superior': round(confidence_intervals['upper'][i], 2),
                    'desviacion_estandar': round(confidence_intervals['std'][i], 2)
                })

            predicciones_detalle.append(pred_dia)

        # Calcular métricas resumen
        demanda_total = sum(pred['demanda_predicha'] for pred in predicciones_detalle)
        demanda_promedio = demanda_total / len(predicciones_detalle)

        # Contexto argentino
        contexto_argentino = {
            'moneda': 'ARS',
            'inflacion_mensual_estimada': f"{self.inflation_rate * 100:.1f}%",
            'feriados_periodo': sum(1 for pred in predicciones_detalle if pred['es_feriado']),
            'ajuste_estacional': self._get_seasonal_adjustment(start_date),
            'zona_horaria': 'America/Argentina/Buenos_Aires'
        }

        # Métricas del modelo
        metricas_modelo = {
            'accuracy': self.model_metadata.get('accuracy', 0.0),
            'modelo_entrenado': self.model_metadata.get('trained_at', ''),
            'features_utilizadas': self.model_metadata.get('features_count', 0),
            'confianza_prediccion': self._calculate_prediction_confidence(predictions, confidence_intervals)
        }

        return {
            'producto_id': producto.id,
            'producto_nombre': producto.nombre,
            'predicciones': predicciones_detalle,
            'resumen': {
                'demanda_total_periodo': round(demanda_total, 2),
                'demanda_promedio_diaria': round(demanda_promedio, 2),
                'dias_prediccion': dias_prediccion,
                'stock_actual': producto.stock_actual
            },
            'metricas_modelo': metricas_modelo,
            'contexto_argentino': contexto_argentino,
            'timestamp': datetime.now(ARGENTINA_TZ).isoformat(),
            'confianza_general': metricas_modelo['confianza_prediccion']
        }

    def _get_seasonal_adjustment(self, fecha: datetime.date) -> str:
        """Determina ajuste estacional para fecha dada"""
        month = fecha.month

        if month in [12, 1, 2]:  # Verano
            return "alta_demanda_verano"
        elif month in [6, 7, 8]:  # Invierno
            return "patron_invierno"
        elif month in [3, 4, 5]:  # Otoño
            return "patron_otono"
        else:  # Primavera
            return "patron_primavera"

    def _calculate_prediction_confidence(self, 
                                       predictions: np.ndarray, 
                                       confidence_intervals: Optional[Dict]) -> float:
        """Calcula confianza general de la predicción"""
        base_confidence = self.model_metadata.get('accuracy', 0.8)

        if confidence_intervals:
            # Ajustar confianza basado en variabilidad
            avg_std = np.mean(confidence_intervals['std'])
            avg_pred = np.mean(predictions)

            if avg_pred > 0:
                coefficient_of_variation = avg_std / avg_pred
                # Reducir confianza si hay mucha variabilidad
                confidence_adjustment = max(0.5, 1 - coefficient_of_variation)
                return min(0.95, base_confidence * confidence_adjustment)

        return base_confidence

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si hay una predicción válida en cache"""
        if cache_key not in self.prediction_cache:
            return False

        cached_time = self.prediction_cache[cache_key]['timestamp']
        elapsed = (datetime.now(ARGENTINA_TZ) - cached_time).total_seconds()

        return elapsed < self.cache_ttl

    def get_model_health(self) -> Dict[str, Any]:
        """Retorna estado de salud del modelo ML"""
        return {
            'model_loaded': self.model is not None,
            'feature_extractor_ready': self.feature_extractor is not None,
            'model_metadata': self.model_metadata,
            'cache_entries': len(self.prediction_cache),
            'last_prediction': max([
                entry['timestamp'] for entry in self.prediction_cache.values()
            ], default=None)
        }

# ========================
# FASTAPI APP
# ========================

# Instancia global del predictor
predictor = None

def get_predictor() -> DemandPredictor:
    """Dependency injection para el predictor"""
    global predictor
    if predictor is None:
        config = get_config()
        model_path = config.get('ml_model_path', 'models/')
        predictor = DemandPredictor(model_path=model_path)
    return predictor

# Crear app FastAPI
app = FastAPI(
    title="ML Predictor - Sistema Inventario Argentina",
    description="API de predicción de demanda usando ML para retail argentino",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ========================
# ENDPOINTS
# ========================

@app.get("/health", response_model=HealthResponse)
async def health_check(predictor: DemandPredictor = Depends(get_predictor)):
    """Health check del servicio ML"""
    try:
        model_health = predictor.get_model_health()

        # Verificar conexión a base de datos
        db_connected = True
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
        except:
            db_connected = False

        return HealthResponse(
            status="healthy" if all([
                model_health['model_loaded'],
                model_health['feature_extractor_ready'],
                db_connected
            ]) else "degraded",
            ml_model_loaded=model_health['model_loaded'],
            feature_extractor_ready=model_health['feature_extractor_ready'],
            database_connected=db_connected,
            timestamp=datetime.now(ARGENTINA_TZ)
        )

    except Exception as e:
        logger.error(f"❌ Error en health check: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            ml_model_loaded=False,
            feature_extractor_ready=False,
            database_connected=False,
            timestamp=datetime.now(ARGENTINA_TZ)
        )

@app.post("/predict/demanda", response_model=PredictionResponse)
async def predict_demand(
    request: PredictionRequest,
    predictor: DemandPredictor = Depends(get_predictor)
):
    """
    Predice demanda para un producto específico

    Endpoint principal para predicciones de demanda usando RandomForest.
    Optimizado para contexto argentino con inflación y feriados locales.
    """
    logger.info(f"🔮 Predicción solicitada: producto {request.producto_id}, {request.dias_prediccion} días")

    try:
        # Realizar predicción
        result = predictor.predict_demand(
            producto_id=request.producto_id,
            dias_prediccion=request.dias_prediccion,
            incluir_confianza=request.incluir_confianza
        )

        # Convertir a response model
        return PredictionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en predicción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor ML")

@app.get("/predict/batch/{categoria}")
async def predict_batch_by_category(
    categoria: str,
    dias_prediccion: int = 7,
    limit: int = 10,
    predictor: DemandPredictor = Depends(get_predictor)
):
    """Predicción batch para productos de una categoría"""
    try:
        logger.info(f"🔮 Predicción batch: categoría '{categoria}', {limit} productos")

        # Obtener productos de la categoría
        with get_db_session() as db:
            productos = db.query(Producto).filter(
                Producto.categoria == categoria,
                Producto.activo == True
            ).limit(limit).all()

        if not productos:
            raise HTTPException(status_code=404, detail=f"No se encontraron productos en categoría '{categoria}'")

        # Generar predicciones para cada producto
        resultados = []
        for producto in productos:
            try:
                pred_result = predictor.predict_demand(
                    producto_id=producto.id,
                    dias_prediccion=dias_prediccion,
                    incluir_confianza=False  # Reducir carga para batch
                )
                resultados.append({
                    'producto_id': producto.id,
                    'producto_nombre': producto.nombre,
                    'demanda_total_predicha': sum(
                        p['demanda_predicha'] for p in pred_result['predicciones']
                    ),
                    'stock_actual': producto.stock_actual,
                    'necesita_reposicion': sum(
                        p['demanda_predicha'] for p in pred_result['predicciones']
                    ) > producto.stock_actual
                })
            except Exception as e:
                logger.warning(f"⚠️  Error prediciendo producto {producto.id}: {str(e)}")
                continue

        return {
            'categoria': categoria,
            'productos_analizados': len(resultados),
            'dias_prediccion': dias_prediccion,
            'resultados': resultados,
            'resumen': {
                'productos_necesitan_reposicion': sum(1 for r in resultados if r['necesita_reposicion']),
                'demanda_total_categoria': sum(r['demanda_total_predicha'] for r in resultados)
            },
            'timestamp': datetime.now(ARGENTINA_TZ).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en predicción batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en predicción batch: {str(e)}")

@app.get("/model/info")
async def get_model_info(predictor: DemandPredictor = Depends(get_predictor)):
    """Información del modelo ML actual"""
    try:
        health = predictor.get_model_health()

        # Información adicional del modelo
        model_info = {
            'estado': health,
            'configuracion': {
                'tipo_modelo': 'RandomForest',
                'framework': 'scikit-learn',
                'contexto': 'Retail Argentina',
                'moneda': 'ARS',
                'zona_horaria': 'America/Argentina/Buenos_Aires'
            },
            'capacidades': {
                'prediccion_demanda': True,
                'intervalos_confianza': True,
                'prediccion_batch': True,
                'contexto_argentino': True,
                'cache_inteligente': True
            },
            'limites': {
                'dias_prediccion_max': 30,
                'productos_batch_max': 50,
                'cache_ttl_segundos': predictor.cache_ttl
            }
        }

        return model_info

    except Exception as e:
        logger.error(f"❌ Error obteniendo info del modelo: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo información del modelo")

@app.post("/model/retrain")
async def retrain_model(predictor: DemandPredictor = Depends(get_predictor)):
    """Reentrenar el modelo con datos actualizados"""
    try:
        logger.info("🔄 Iniciando reentrenamiento del modelo...")

        # Reentrenar modelo
        predictor._train_new_model()

        return {
            'status': 'success',
            'message': 'Modelo reentrenado exitosamente',
            'nuevo_modelo': predictor.model_metadata,
            'timestamp': datetime.now(ARGENTINA_TZ).isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error reentrenando modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reentrenando modelo: {str(e)}")

# ========================
# STARTUP Y SHUTDOWN
# ========================

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar el servicio"""
    logger.info("🚀 Iniciando servicio ML Predictor...")

    try:
        # Inicializar predictor global
        global predictor
        config = get_config()
        model_path = config.get('ml_model_path', 'models/')
        predictor = DemandPredictor(model_path=model_path)

        logger.info("✅ Servicio ML Predictor iniciado correctamente")

    except Exception as e:
        logger.error(f"❌ Error iniciando servicio ML: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar el servicio"""
    logger.info("🛑 Cerrando servicio ML Predictor...")

    # Limpiar cache si es necesario
    global predictor
    if predictor:
        predictor.prediction_cache.clear()

    logger.info("✅ Servicio ML Predictor cerrado correctamente")

# ========================
# MAIN PARA DESARROLLO
# ========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ML Predictor Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8003, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    print("🤖 Iniciando ML Predictor - Sistema Inventario Argentina")
    print(f"🌐 Servidor: http://{args.host}:{args.port}")
    print(f"📚 Documentación: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "ml.predictor:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
