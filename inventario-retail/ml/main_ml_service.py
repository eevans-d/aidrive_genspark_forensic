"""
Main ML Service - Complete Independent ML Service on Port 8003
Integrates predictor, model manager, and cache manager with FastAPI
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import pandas as pd

# Import our ML components
from model_manager import ModelManager, ModelConfig, ModelType, EvictionPolicy
from cache_manager import MLCacheManager, CacheConfig, CacheType
from shared.auth import require_role, ML_ROLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models for API
class PredictionRequest(BaseModel):
    model_name: str
    features: Dict[str, Union[float, int, str]]
    use_cache: bool = Field(default=True, description="Use caching for predictions")
    include_probabilities: bool = Field(default=False, description="Include prediction probabilities")
    include_feature_importance: bool = Field(default=False, description="Include feature importance")

class PredictionResponse(BaseModel):
    predictions: List[Union[float, int, str]]
    model_name: str
    model_version: str
    prediction_time_ms: float
    cached: bool = False
    probabilities: Optional[List[List[float]]] = None
    class_names: Optional[List[str]] = None
    feature_importance: Optional[Dict[str, float]] = None
    confidence_score: Optional[float] = None

class ModelTrainingRequest(BaseModel):
    model_name: str
    model_type: str = Field(description="'classification' or 'regression'")
    algorithm: str = Field(default="random_forest", description="Algorithm to use")
    dataset_path: Optional[str] = None
    target_column: str
    feature_columns: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    use_feature_selection: bool = Field(default=True)
    scaling_method: str = Field(default="standard", description="'standard', 'minmax', or 'none'")

class ModelResponse(BaseModel):
    model_name: str
    version: str
    status: str
    model_type: str
    algorithm: str
    created_at: str
    updated_at: str
    feature_count: int
    latest_metrics: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    components: Dict[str, str]
    model_summary: Dict[str, Any]
    cache_summary: Dict[str, Any]
    system_info: Dict[str, Any]

class DataUploadRequest(BaseModel):
    data: List[Dict[str, Any]]
    filename: Optional[str] = None

# Configuration
ML_SERVICE_CONFIG = {
    "host": "0.0.0.0",
    "port": 8003,
    "models_path": "models",
    "data_path": "data",
    "cache_type": os.getenv("CACHE_TYPE", "memory"),  # redis, memory, hybrid
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
    "max_cache_memory_mb": int(os.getenv("MAX_CACHE_MEMORY_MB", "100")),
    "enable_monitoring": os.getenv("ENABLE_MONITORING", "true").lower() == "true",
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(",")
}

class MLService:
    """Main ML Service orchestrator"""

    def __init__(self):
        self.start_time = time.time()
        self.model_manager = None
        self.cache_manager = None
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories"""
        for path in [ML_SERVICE_CONFIG["models_path"], ML_SERVICE_CONFIG["data_path"]]:
            Path(path).mkdir(exist_ok=True)
        logger.info(f"Directories setup: {ML_SERVICE_CONFIG['models_path']}, {ML_SERVICE_CONFIG['data_path']}")

    async def initialize(self):
        """Initialize ML service components"""
        try:
            # Initialize model manager
            self.model_manager = ModelManager(ML_SERVICE_CONFIG["models_path"])
            await self.model_manager.load_all_models()

            # Initialize cache manager
            cache_type_map = {
                "redis": CacheType.REDIS,
                "memory": CacheType.MEMORY,
                "hybrid": CacheType.HYBRID
            }

            cache_config = CacheConfig(
                cache_type=cache_type_map.get(ML_SERVICE_CONFIG["cache_type"], CacheType.MEMORY),
                redis_url=ML_SERVICE_CONFIG["redis_url"],
                default_ttl=ML_SERVICE_CONFIG["cache_ttl"],
                max_memory_mb=ML_SERVICE_CONFIG["max_cache_memory_mb"]
            )

            self.cache_manager = MLCacheManager(cache_config)

            # Start model monitoring if enabled
            if ML_SERVICE_CONFIG["enable_monitoring"]:
                self.model_manager.start_monitoring(check_interval_hours=24)

            logger.info("ML Service components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ML service: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.model_manager and ML_SERVICE_CONFIG["enable_monitoring"]:
                self.model_manager.stop_monitoring()

            logger.info("ML Service cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time

# Global service instance
ml_service = MLService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ML Service...")
    await ml_service.initialize()
    logger.info("ML Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down ML Service...")
    await ml_service.cleanup()

# FastAPI App
app = FastAPI(
    title="ML Service Complete",
    description="Complete ML prediction service with model management and caching",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ML_SERVICE_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/", response_model=Dict[str, Any])
async def root(current_user: dict = Depends(require_role(ML_ROLE))):
    """Service information and status"""
    return {
        "service": "ML Service Complete",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": ml_service.get_uptime(),
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "models": "/models",
            "train": "/train",
            "cache": "/cache",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health(current_user: dict = Depends(require_role(ML_ROLE))):
    """Comprehensive health check"""
    uptime = ml_service.get_uptime()

    # Check components
    components = {}

    # Model manager health
    try:
        model_summary = ml_service.model_manager.get_model_performance_summary()
        components["model_manager"] = "healthy"
    except Exception as e:
        components["model_manager"] = f"error: {str(e)}"
        model_summary = {}

    # Cache manager health
    try:
        cache_health = await ml_service.cache_manager.health_check()
        components["cache_manager"] = cache_health["status"]
        cache_summary = cache_health["cache_info"]
    except Exception as e:
        components["cache_manager"] = f"error: {str(e)}"
        cache_summary = {}

    # Overall status
    overall_status = "healthy"
    if any("error" in status for status in components.values()):
        overall_status = "unhealthy"
    elif any("degraded" in status for status in components.values()):
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=uptime,
        components=components,
        model_summary=model_summary,
        cache_summary=cache_summary,
        system_info={
            "python_version": sys.version,
            "models_path": ML_SERVICE_CONFIG["models_path"],
            "cache_type": ML_SERVICE_CONFIG["cache_type"],
            "monitoring_enabled": ML_SERVICE_CONFIG["enable_monitoring"]
        }
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    current_user: dict = Depends(require_role(ML_ROLE))
):
    """Make predictions using trained models"""
    start_time = time.time()

    try:
        # Check if model exists
        if request.model_name not in ml_service.model_manager.models:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{request.model_name}' not found"
            )

        cached_result = None

        # Try cache first if enabled
        if request.use_cache:
            cache_key = ml_service.cache_manager.generate_prediction_key(
                request.model_name,
                request.features,
                ml_service.model_manager.models[request.model_name].version
            )
            cached_result = await ml_service.cache_manager.get_prediction(cache_key)

        if cached_result:
            # Return cached result
            cached_result["cached"] = True
            return PredictionResponse(**cached_result)

        # Make new prediction
        input_df = pd.DataFrame([request.features])

        prediction_result = await ml_service.model_manager.predict(
            request.model_name,
            input_df,
            include_probabilities=request.include_probabilities
        )

        # Calculate confidence score
        confidence_score = None
        if request.include_probabilities and "probabilities" in prediction_result:
            # Use max probability as confidence for classification
            probabilities = prediction_result["probabilities"][0]
            confidence_score = max(probabilities)

        # Prepare response
        response_data = {
            "predictions": prediction_result["predictions"],
            "model_name": request.model_name,
            "model_version": prediction_result["model_version"],
            "prediction_time_ms": prediction_result["prediction_time_ms"],
            "cached": False,
            "confidence_score": confidence_score
        }

        # Add optional fields
        if request.include_probabilities and "probabilities" in prediction_result:
            response_data["probabilities"] = prediction_result["probabilities"]
            response_data["class_names"] = prediction_result.get("class_names", [])

        if request.include_feature_importance and "feature_importance" in prediction_result:
            response_data["feature_importance"] = prediction_result["feature_importance"]

        # Cache result if enabled
        if request.use_cache:
            await ml_service.cache_manager.set_prediction(cache_key, response_data)

        return PredictionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@app.post("/train", response_model=Dict[str, Any])
async def train(
    request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(ML_ROLE))
):
    """Train a new model"""
    try:
        # Validate model type
        model_type = ModelType.CLASSIFICATION if request.model_type == "classification" else ModelType.REGRESSION

        # Create model configuration
        hyperparameters = request.hyperparameters or {}
        if "random_state" not in hyperparameters:
            hyperparameters["random_state"] = 42

        config = ModelConfig(
            model_type=model_type,
            algorithm=request.algorithm,
            hyperparameters=hyperparameters,
            feature_selection=request.use_feature_selection,
            scaling_method=request.scaling_method,
            test_size=request.test_size
        )

        # Create model
        version = ml_service.model_manager.create_model(request.model_name, config)

        # Load training data
        if request.dataset_path and Path(request.dataset_path).exists():
            df = pd.read_csv(request.dataset_path)
        else:
            # Generate sample data for demonstration
            from sklearn.datasets import make_classification, make_regression
            import numpy as np

            np.random.seed(42)
            if model_type == ModelType.CLASSIFICATION:
                X, y = make_classification(n_samples=1000, n_features=5, n_classes=3, random_state=42)
            else:
                X, y = make_regression(n_samples=1000, n_features=5, noise=0.1, random_state=42)

            feature_names = request.feature_columns or [f"feature_{i}" for i in range(X.shape[1])]
            df = pd.DataFrame(X, columns=feature_names)
            df[request.target_column] = y

        # Prepare training data
        if request.feature_columns:
            X = df[request.feature_columns]
        else:
            X = df.drop(columns=[request.target_column])

        y = df[request.target_column]

        # Train model (in background for large datasets)
        background_tasks.add_task(
            train_model_background,
            request.model_name,
            X,
            y
        )

        return {
            "message": f"Training started for model '{request.model_name}'",
            "model_name": request.model_name,
            "version": version,
            "status": "training",
            "config": {
                "model_type": request.model_type,
                "algorithm": request.algorithm,
                "features": list(X.columns),
                "target": request.target_column
            }
        }

    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Training failed: {str(e)}"
        )

async def train_model_background(model_name: str, X: pd.DataFrame, y: pd.Series):
    """Background task for model training"""
    try:
        metrics = await ml_service.model_manager.train_model(model_name, X, y)
        logger.info(f"Model {model_name} training completed successfully")

        # Clear model cache after training
        await ml_service.cache_manager.invalidate_model_cache(model_name)

    except Exception as e:
        logger.error(f"Background training failed for {model_name}: {e}")

@app.get("/models", response_model=List[ModelResponse])
async def list_models(current_user: dict = Depends(require_role(ML_ROLE))):
    """List all available models"""
    try:
        models = ml_service.model_manager.list_models()

        detailed_models = []
        for model_info in models:
            try:
                detailed_info = ml_service.model_manager.get_model_info(model_info["name"])
                detailed_models.append(ModelResponse(**detailed_info))
            except Exception as e:
                logger.error(f"Error getting model info for {model_info['name']}: {e}")
                # Add basic info even if detailed fetch fails
                detailed_models.append(ModelResponse(
                    model_name=model_info["name"],
                    version=model_info["version"],
                    status=model_info["status"],
                    model_type=model_info["model_type"],
                    algorithm=model_info["algorithm"],
                    created_at=model_info["updated_at"],
                    updated_at=model_info["updated_at"],
                    feature_count=0
                ))

        return detailed_models

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )

@app.get("/models/{model_name}", response_model=ModelResponse)
async def get_model(model_name: str, current_user: dict = Depends(require_role(ML_ROLE))):
    """Get detailed information about a specific model"""
    try:
        if model_name not in ml_service.model_manager.models:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_name}' not found"
            )

        model_info = ml_service.model_manager.get_model_info(model_name)
        return ModelResponse(**model_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )

@app.delete("/models/{model_name}")
async def delete_model(model_name: str, current_user: dict = Depends(require_role(ML_ROLE))):
    """Delete a model"""
    try:
        if model_name not in ml_service.model_manager.models:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_name}' not found"
            )

        # Remove from memory
        del ml_service.model_manager.models[model_name]

        # Remove model file
        model_file = Path(ML_SERVICE_CONFIG["models_path"]) / f"{model_name}.pkl"
        if model_file.exists():
            model_file.unlink()

        # Clear cache
        await ml_service.cache_manager.invalidate_model_cache(model_name)

        return {"message": f"Model '{model_name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete model: {str(e)}"
        )

@app.get("/cache/info")
async def cache_info(current_user: dict = Depends(require_role(ML_ROLE))):
    """Get cache information and statistics"""
    try:
        cache_info = ml_service.cache_manager.get_cache_info()
        return cache_info

    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache info: {str(e)}"
        )

@app.delete("/cache/clear")
async def cache_clear(current_user: dict = Depends(require_role(ML_ROLE))):
    """Clear all cache entries"""
    try:
        await ml_service.cache_manager.cache.clear()
        ml_service.cache_manager.reset_stats()

        return {"message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

@app.get("/metrics")
async def metrics(current_user: dict = Depends(require_role(ML_ROLE))):
    """Get service metrics and performance statistics"""
    try:
        # Model metrics
        model_summary = ml_service.model_manager.get_model_performance_summary()

        # Cache metrics
        cache_metrics = ml_service.cache_manager.get_performance_metrics()

        # Service metrics
        uptime = ml_service.get_uptime()

        return {
            "service": {
                "uptime_seconds": uptime,
                "uptime_human": str(timedelta(seconds=int(uptime))),
                "timestamp": datetime.now().isoformat()
            },
            "models": model_summary,
            "cache": cache_metrics
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )

@app.post("/data/upload")
async def upload_data(request: dict, current_user: dict = Depends(require_role(ML_ROLE))):
    """Upload training data"""
    try:
        # Save data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = request.get("filename") or f"uploaded_data_{timestamp}.csv"

        if not filename.endswith('.csv'):
            filename += '.csv'

        data_path = Path(ML_SERVICE_CONFIG["data_path"]) / filename

        # Convert to DataFrame and save
        df = pd.DataFrame(request.get("data", []))
        df.to_csv(data_path, index=False)

        return {
            "message": f"Data uploaded successfully",
            "filename": filename,
            "path": str(data_path),
            "rows": len(df),
            "columns": list(df.columns)
        }

    except Exception as e:
        logger.error(f"Data upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Data upload failed: {str(e)}"
        )

@app.get("/data/list")
async def list_data(current_user: dict = Depends(require_role(ML_ROLE))):
    """List available data files"""
    try:
        data_path = Path(ML_SERVICE_CONFIG["data_path"])
        files = []

        for file_path in data_path.glob("*.csv"):
            try:
                # Get file info
                stat = file_path.stat()

                # Try to read first few rows to get column info
                try:
                    df_sample = pd.read_csv(file_path, nrows=5)
                    columns = list(df_sample.columns)
                    row_count = len(pd.read_csv(file_path))
                except:
                    columns = []
                    row_count = 0

                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "columns": columns,
                    "row_count": row_count
                })
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        return {"files": files, "total_files": len(files)}

    except Exception as e:
        logger.error(f"Error listing data files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list data files: {str(e)}"
        )

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Run the service
    uvicorn.run(
        "main_ml_service:app",
        host=ML_SERVICE_CONFIG["host"],
        port=ML_SERVICE_CONFIG["port"],
        reload=False,
        log_level="info",
        access_log=True
    )
