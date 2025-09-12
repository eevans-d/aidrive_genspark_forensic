"""
ML Predictor Complete - FastAPI with Real Database Integration
Production-ready ML prediction service with caching and monitoring
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import hashlib
import pickle
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
import redis
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Models
Base = declarative_base()

class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    input_hash = Column(String(64), unique=True, index=True)
    input_data = Column(Text)
    prediction = Column(Text)
    model_version = Column(String(50))
    confidence_score = Column(Float)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100))
    model_version = Column(String(50))
    metric_name = Column(String(50))
    metric_value = Column(Float)
    dataset_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class PredictionRequest(BaseModel):
    features: Dict[str, Union[float, int, str]]
    model_type: str = Field(default="auto", description="Model type: 'classification', 'regression', or 'auto'")
    include_confidence: bool = Field(default=True, description="Include confidence scores")

    @validator('features')
    def validate_features(cls, v):
        if not v:
            raise ValueError("Features cannot be empty")
        return v

class PredictionResponse(BaseModel):
    prediction: Union[float, int, str, List[float]]
    confidence_score: Optional[float] = None
    model_version: str
    processing_time_ms: float
    cached: bool = False
    feature_importance: Optional[Dict[str, float]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: float
    cache_status: str
    db_status: str
    model_status: Dict[str, str]
    metrics: Dict[str, Any]

class ModelTrainingRequest(BaseModel):
    dataset_path: Optional[str] = None
    target_column: str
    feature_columns: Optional[List[str]] = None
    model_type: str = Field(description="'classification' or 'regression'")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    retrain: bool = Field(default=False, description="Force retrain even if model exists")

# Database and Cache Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ml_predictions.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
MODEL_PATH = Path("models")
MODEL_PATH.mkdir(exist_ok=True)

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        async with self.async_session() as session:
            yield session

    async def close(self):
        await self.engine.dispose()

class CacheManager:
    def __init__(self, redis_url: str):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
            self.available = False
            self._memory_cache = {}

    def _generate_cache_key(self, data: Dict) -> str:
        """Generate cache key from input data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Dict]:
        try:
            if self.available:
                cached_data = self.redis_client.get(f"pred:{key}")
                if cached_data:
                    return json.loads(cached_data)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Dict, ttl: int = CACHE_TTL):
        try:
            if self.available:
                self.redis_client.setex(
                    f"pred:{key}", 
                    ttl, 
                    json.dumps(value, default=str)
                )
            else:
                self._memory_cache[key] = value
                # Simple TTL simulation for memory cache
                if len(self._memory_cache) > 1000:
                    # Clear oldest 20% entries
                    keys_to_remove = list(self._memory_cache.keys())[:200]
                    for k in keys_to_remove:
                        del self._memory_cache[k]
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def get_status(self) -> str:
        if self.available:
            try:
                self.redis_client.ping()
                return "connected"
            except:
                return "error"
        return "memory_fallback"

class MLPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = {}
        self.model_versions = {}
        self.start_time = time.time()

    async def load_models(self):
        """Load existing models from disk"""
        try:
            for model_file in MODEL_PATH.glob("*.pkl"):
                model_name = model_file.stem
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)

                self.models[model_name] = model_data.get('model')
                self.scalers[model_name] = model_data.get('scaler')
                self.encoders[model_name] = model_data.get('encoders', {})
                self.feature_names[model_name] = model_data.get('feature_names', [])
                self.model_versions[model_name] = model_data.get('version', '1.0.0')

                logger.info(f"Loaded model: {model_name} v{self.model_versions[model_name]}")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    async def train_model(self, request: ModelTrainingRequest, session: AsyncSession) -> Dict:
        """Train a new model"""
        try:
            # Load data
            if request.dataset_path and os.path.exists(request.dataset_path):
                df = pd.read_csv(request.dataset_path)
            else:
                # Generate sample data for demonstration
                np.random.seed(42)
                n_samples = 1000
                n_features = 5

                if request.model_type == "classification":
                    from sklearn.datasets import make_classification
                    X, y = make_classification(
                        n_samples=n_samples, 
                        n_features=n_features, 
                        n_classes=3, 
                        random_state=42
                    )
                    feature_names = [f"feature_{i}" for i in range(n_features)]
                else:
                    from sklearn.datasets import make_regression
                    X, y = make_regression(
                        n_samples=n_samples, 
                        n_features=n_features, 
                        noise=0.1, 
                        random_state=42
                    )
                    feature_names = [f"feature_{i}" for i in range(n_features)]

                df = pd.DataFrame(X, columns=feature_names)
                df[request.target_column] = y

            # Prepare features and target
            if request.feature_columns:
                X = df[request.feature_columns]
            else:
                X = df.drop(columns=[request.target_column])

            y = df[request.target_column]

            # Handle categorical features
            encoders = {}
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                encoders[col] = le

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=request.test_size, random_state=42
            )

            # Train model
            if request.model_type == "classification":
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                metric_value = accuracy
                metric_name = "accuracy"
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                metric_value = mse
                metric_name = "mse"

            # Save model
            model_name = f"{request.model_type}_model"
            version = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            model_data = {
                'model': model,
                'scaler': scaler,
                'encoders': encoders,
                'feature_names': list(X.columns),
                'version': version,
                'model_type': request.model_type
            }

            model_file = MODEL_PATH / f"{model_name}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)

            # Update in-memory models
            self.models[model_name] = model
            self.scalers[model_name] = scaler
            self.encoders[model_name] = encoders
            self.feature_names[model_name] = list(X.columns)
            self.model_versions[model_name] = version

            # Save metrics to database
            metrics_record = ModelMetrics(
                model_name=model_name,
                model_version=version,
                metric_name=metric_name,
                metric_value=metric_value,
                dataset_size=len(df)
            )
            session.add(metrics_record)
            await session.commit()

            logger.info(f"Model trained successfully: {model_name} v{version}")

            return {
                "model_name": model_name,
                "version": version,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "dataset_size": len(df),
                "features": list(X.columns)
            }

        except Exception as e:
            logger.error(f"Model training error: {e}")
            raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

    async def predict(self, request: PredictionRequest) -> Dict:
        """Make prediction with caching"""
        start_time = time.time()

        try:
            # Determine model to use
            if request.model_type == "auto":
                # Simple heuristic: use first available model
                if not self.models:
                    raise HTTPException(status_code=404, detail="No models available")
                model_name = list(self.models.keys())[0]
            else:
                model_name = f"{request.model_type}_model"
                if model_name not in self.models:
                    raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

            model = self.models[model_name]
            scaler = self.scalers[model_name]
            encoders = self.encoders.get(model_name, {})
            feature_names = self.feature_names[model_name]

            # Prepare input data
            input_df = pd.DataFrame([request.features])

            # Ensure all required features are present
            for feature in feature_names:
                if feature not in input_df.columns:
                    input_df[feature] = 0  # Default value

            # Apply encoders
            for col, encoder in encoders.items():
                if col in input_df.columns:
                    try:
                        input_df[col] = encoder.transform(input_df[col].astype(str))
                    except ValueError:
                        # Handle unseen categories
                        input_df[col] = 0

            # Select and order features
            input_df = input_df[feature_names]

            # Scale features
            input_scaled = scaler.transform(input_df)

            # Make prediction
            prediction = model.predict(input_scaled)[0]

            # Calculate confidence score
            confidence_score = None
            if request.include_confidence and hasattr(model, 'predict_proba'):
                try:
                    proba = model.predict_proba(input_scaled)[0]
                    confidence_score = float(np.max(proba))
                except:
                    pass

            # Get feature importance
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(
                    feature_names, 
                    model.feature_importances_.tolist()
                ))

            processing_time = (time.time() - start_time) * 1000

            return {
                "prediction": float(prediction) if isinstance(prediction, (np.number, float, int)) else prediction,
                "confidence_score": confidence_score,
                "model_version": self.model_versions[model_name],
                "processing_time_ms": processing_time,
                "cached": False,
                "feature_importance": feature_importance
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded models"""
        return {
            name: f"v{version} - Ready" 
            for name, version in self.model_versions.items()
        }

# Global instances
db_manager = DatabaseManager(DATABASE_URL)
cache_manager = CacheManager(REDIS_URL)
ml_predictor = MLPredictor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ML Predictor Service...")
    await db_manager.create_tables()
    await ml_predictor.load_models()
    logger.info("ML Predictor Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down ML Predictor Service...")
    await db_manager.close()

# FastAPI App
app = FastAPI(
    title="ML Predictor Complete",
    description="Production-ready ML prediction service with caching and monitoring",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db_session():
    async for session in db_manager.get_session():
        yield session

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "service": "ML Predictor Complete",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    uptime = time.time() - ml_predictor.start_time

    # Check database
    db_status = "connected"
    try:
        async for session in db_manager.get_session():
            await session.execute(sa.text("SELECT 1"))
            break
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        cache_status=cache_manager.get_status(),
        db_status=db_status,
        model_status=ml_predictor.get_model_status(),
        metrics={
            "models_loaded": len(ml_predictor.models),
            "cache_type": "redis" if cache_manager.available else "memory"
        }
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """Make prediction with caching and database logging"""

    # Check cache first
    cache_key = cache_manager._generate_cache_key(request.features)
    cached_result = await cache_manager.get(cache_key)

    if cached_result:
        cached_result["cached"] = True
        return PredictionResponse(**cached_result)

    # Make prediction
    result = await ml_predictor.predict(request)

    # Cache result
    await cache_manager.set(cache_key, result)

    # Log to database (background task)
    background_tasks.add_task(
        log_prediction,
        session,
        cache_key,
        request.dict(),
        result
    )

    return PredictionResponse(**result)

async def log_prediction(session: AsyncSession, input_hash: str, input_data: Dict, result: Dict):
    """Log prediction to database"""
    try:
        record = PredictionRecord(
            input_hash=input_hash,
            input_data=json.dumps(input_data),
            prediction=json.dumps(result["prediction"], default=str),
            model_version=result["model_version"],
            confidence_score=result.get("confidence_score"),
            processing_time_ms=result["processing_time_ms"]
        )
        session.add(record)
        await session.commit()
    except Exception as e:
        logger.error(f"Failed to log prediction: {e}")

@app.post("/train", response_model=Dict[str, Any])
async def train_model(
    request: ModelTrainingRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Train a new model"""
    return await ml_predictor.train_model(request, session)

@app.get("/models", response_model=Dict[str, Any])
async def list_models():
    """List available models and their status"""
    return {
        "models": ml_predictor.get_model_status(),
        "total_models": len(ml_predictor.models),
        "model_path": str(MODEL_PATH)
    }

@app.get("/metrics/{model_name}", response_model=List[Dict[str, Any]])
async def get_model_metrics(
    model_name: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get model performance metrics"""
    try:
        result = await session.execute(
            sa.select(ModelMetrics).where(ModelMetrics.model_name == model_name)
        )
        metrics = result.scalars().all()

        return [
            {
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "model_version": m.model_version,
                "dataset_size": m.dataset_size,
                "created_at": m.created_at
            }
            for m in metrics
        ]
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@app.get("/predictions/history", response_model=List[Dict[str, Any]])
async def get_prediction_history(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session)
):
    """Get prediction history"""
    try:
        result = await session.execute(
            sa.select(PredictionRecord)
            .order_by(PredictionRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        predictions = result.scalars().all()

        return [
            {
                "id": p.id,
                "input_hash": p.input_hash,
                "prediction": json.loads(p.prediction),
                "model_version": p.model_version,
                "confidence_score": p.confidence_score,
                "processing_time_ms": p.processing_time_ms,
                "created_at": p.created_at
            }
            for p in predictions
        ]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@app.delete("/cache/clear")
async def clear_cache():
    """Clear prediction cache"""
    try:
        if cache_manager.available:
            # Clear Redis keys with pred: prefix
            for key in cache_manager.redis_client.scan_iter(match="pred:*"):
                cache_manager.redis_client.delete(key)
        else:
            cache_manager._memory_cache.clear()

        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

if __name__ == "__main__":
    uvicorn.run(
        "predictor_complete:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
