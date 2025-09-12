"""
ML Model Manager - Advanced Model Management with Automatic Retraining
Manages model lifecycle, performance monitoring, and automatic retraining
"""

import asyncio
import logging
import time
import os
import pickle
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression, f_classif
import joblib
from concurrent.futures import ThreadPoolExecutor
import threading
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"

class ModelStatus(Enum):
    TRAINING = "training"
    READY = "ready"
    RETRAINING = "retraining"
    FAILED = "failed"
    DEPRECATED = "deprecated"

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    cross_val_score: Optional[float] = None
    training_time: Optional[float] = None
    prediction_time: Optional[float] = None
    dataset_size: Optional[int] = None
    feature_count: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ModelConfig:
    """Model configuration and hyperparameters"""
    model_type: ModelType
    algorithm: str
    hyperparameters: Dict[str, Any]
    feature_selection: bool = True
    max_features: Optional[int] = None
    scaling_method: str = "standard"  # standard, minmax, none
    test_size: float = 0.2
    cv_folds: int = 5
    random_state: int = 42

@dataclass
class RetrainingTrigger:
    """Retraining trigger configuration"""
    performance_threshold: float
    time_threshold_days: int
    data_drift_threshold: float
    min_samples_for_retrain: int = 100
    enabled: bool = True

class ModelInfo:
    """Complete model information"""
    def __init__(self, name: str, config: ModelConfig):
        self.name = name
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.label_encoders = {}
        self.feature_names = []
        self.status = ModelStatus.TRAINING
        self.version = "1.0.0"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metrics_history = []
        self.retraining_trigger = RetrainingTrigger(
            performance_threshold=0.1,  # 10% degradation triggers retrain
            time_threshold_days=30,
            data_drift_threshold=0.05
        )
        self.lock = threading.Lock()

    def update_version(self):
        """Update model version"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.version = f"v{timestamp}"
        self.updated_at = datetime.now()

class ModelManager:
    """Advanced ML Model Manager with automatic retraining"""

    def __init__(self, model_path: str = "models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)

        self.models: Dict[str, ModelInfo] = {}
        self.training_executor = ThreadPoolExecutor(max_workers=2)
        self.monitoring_active = False
        self.performance_history = {}

        # Default model algorithms
        self.classification_algorithms = {
            'random_forest': RandomForestClassifier,
            'logistic_regression': LogisticRegression,
            'svm': SVC
        }

        self.regression_algorithms = {
            'random_forest': RandomForestRegressor,
            'linear_regression': LinearRegression,
            'svr': SVR
        }

        logger.info(f"ModelManager initialized with model path: {self.model_path}")

    def create_model(self, name: str, config: ModelConfig) -> str:
        """Create a new model with configuration"""
        try:
            if name in self.models:
                raise ValueError(f"Model '{name}' already exists")

            model_info = ModelInfo(name, config)
            self.models[name] = model_info

            logger.info(f"Created model configuration: {name}")
            return model_info.version

        except Exception as e:
            logger.error(f"Error creating model {name}: {e}")
            raise

    async def train_model(self, name: str, X: pd.DataFrame, y: pd.Series, 
                         validate: bool = True) -> ModelMetrics:
        """Train a model with comprehensive validation"""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found")

        model_info = self.models[name]

        with model_info.lock:
            model_info.status = ModelStatus.TRAINING
            start_time = time.time()

            try:
                # Prepare data
                X_processed, y_processed = self._preprocess_data(X, y, model_info)

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X_processed, y_processed,
                    test_size=model_info.config.test_size,
                    random_state=model_info.config.random_state,
                    stratify=y_processed if model_info.config.model_type == ModelType.CLASSIFICATION else None
                )

                # Train model with hyperparameter tuning
                best_model = await self._train_with_hyperparameter_tuning(
                    model_info, X_train, y_train
                )

                model_info.model = best_model

                # Evaluate model
                metrics = self._evaluate_model(
                    model_info, X_test, y_test, X_train, y_train
                )
                metrics.training_time = time.time() - start_time
                metrics.dataset_size = len(X)
                metrics.feature_count = X_processed.shape[1]

                # Update model info
                model_info.metrics_history.append(metrics)
                model_info.update_version()
                model_info.status = ModelStatus.READY

                # Save model
                await self._save_model(model_info)

                logger.info(f"Model {name} trained successfully - Version: {model_info.version}")
                return metrics

            except Exception as e:
                model_info.status = ModelStatus.FAILED
                logger.error(f"Error training model {name}: {e}")
                raise

    def _preprocess_data(self, X: pd.DataFrame, y: pd.Series, 
                        model_info: ModelInfo) -> Tuple[pd.DataFrame, pd.Series]:
        """Comprehensive data preprocessing"""
        X_processed = X.copy()
        y_processed = y.copy()

        # Handle categorical features in X
        categorical_columns = X_processed.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col not in model_info.label_encoders:
                le = LabelEncoder()
                X_processed[col] = le.fit_transform(X_processed[col].astype(str))
                model_info.label_encoders[col] = le
            else:
                # Handle unseen categories
                le = model_info.label_encoders[col]
                mask = X_processed[col].isin(le.classes_)
                X_processed.loc[~mask, col] = 'unknown'

                # Add 'unknown' to encoder if not present
                if 'unknown' not in le.classes_:
                    le.classes_ = np.append(le.classes_, 'unknown')

                X_processed[col] = le.transform(X_processed[col].astype(str))

        # Handle categorical target for classification
        if model_info.config.model_type == ModelType.CLASSIFICATION:
            if y_processed.dtype == 'object':
                if 'target' not in model_info.label_encoders:
                    le = LabelEncoder()
                    y_processed = pd.Series(le.fit_transform(y_processed))
                    model_info.label_encoders['target'] = le
                else:
                    le = model_info.label_encoders['target']
                    y_processed = pd.Series(le.transform(y_processed))

        # Feature scaling
        if model_info.config.scaling_method != "none":
            if model_info.scaler is None:
                if model_info.config.scaling_method == "standard":
                    model_info.scaler = StandardScaler()
                elif model_info.config.scaling_method == "minmax":
                    model_info.scaler = MinMaxScaler()

                X_processed = pd.DataFrame(
                    model_info.scaler.fit_transform(X_processed),
                    columns=X_processed.columns,
                    index=X_processed.index
                )
            else:
                X_processed = pd.DataFrame(
                    model_info.scaler.transform(X_processed),
                    columns=X_processed.columns,
                    index=X_processed.index
                )

        # Feature selection
        if model_info.config.feature_selection and model_info.feature_selector is None:
            k = model_info.config.max_features or min(10, X_processed.shape[1])

            if model_info.config.model_type == ModelType.CLASSIFICATION:
                model_info.feature_selector = SelectKBest(f_classif, k=k)
            else:
                model_info.feature_selector = SelectKBest(f_regression, k=k)

            X_processed = pd.DataFrame(
                model_info.feature_selector.fit_transform(X_processed, y_processed),
                columns=X_processed.columns[model_info.feature_selector.get_support()],
                index=X_processed.index
            )
        elif model_info.feature_selector is not None:
            X_processed = pd.DataFrame(
                model_info.feature_selector.transform(X_processed),
                columns=X_processed.columns[model_info.feature_selector.get_support()],
                index=X_processed.index
            )

        model_info.feature_names = list(X_processed.columns)
        return X_processed, y_processed

    async def _train_with_hyperparameter_tuning(self, model_info: ModelInfo, 
                                               X_train: pd.DataFrame, 
                                               y_train: pd.Series) -> BaseEstimator:
        """Train model with hyperparameter optimization"""
        config = model_info.config

        # Get algorithm class
        if config.model_type == ModelType.CLASSIFICATION:
            algorithm_class = self.classification_algorithms[config.algorithm]
        else:
            algorithm_class = self.regression_algorithms[config.algorithm]

        # Base model
        base_model = algorithm_class(**config.hyperparameters)

        # Define parameter grid for tuning
        param_grid = self._get_parameter_grid(config.algorithm, config.model_type)

        if param_grid:
            # Hyperparameter tuning
            scoring = 'accuracy' if config.model_type == ModelType.CLASSIFICATION else 'neg_mean_squared_error'

            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=config.cv_folds,
                scoring=scoring,
                n_jobs=-1,
                verbose=0
            )

            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_

            logger.info(f"Best parameters for {model_info.name}: {grid_search.best_params_}")
        else:
            # No hyperparameter tuning, use base model
            best_model = base_model
            best_model.fit(X_train, y_train)

        return best_model

    def _get_parameter_grid(self, algorithm: str, model_type: ModelType) -> Dict[str, List]:
        """Get parameter grid for hyperparameter tuning"""
        if algorithm == 'random_forest':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20],
                'min_samples_split': [2, 5, 10]
            }
        elif algorithm == 'logistic_regression':
            return {
                'C': [0.1, 1.0, 10.0],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs']
            }
        elif algorithm == 'svm' or algorithm == 'svr':
            return {
                'C': [0.1, 1.0, 10.0],
                'kernel': ['linear', 'rbf'],
                'gamma': ['scale', 'auto']
            }

        return {}  # No tuning for linear regression and others

    def _evaluate_model(self, model_info: ModelInfo, X_test: pd.DataFrame, 
                       y_test: pd.Series, X_train: pd.DataFrame, 
                       y_train: pd.Series) -> ModelMetrics:
        """Comprehensive model evaluation"""
        model = model_info.model
        metrics = ModelMetrics()

        # Predictions
        y_pred = model.predict(X_test)

        # Cross-validation score
        cv_scores = cross_val_score(
            model, X_train, y_train, 
            cv=model_info.config.cv_folds,
            scoring='accuracy' if model_info.config.model_type == ModelType.CLASSIFICATION else 'neg_mean_squared_error'
        )
        metrics.cross_val_score = cv_scores.mean()

        if model_info.config.model_type == ModelType.CLASSIFICATION:
            # Classification metrics
            metrics.accuracy = accuracy_score(y_test, y_pred)
            metrics.precision = precision_score(y_test, y_pred, average='weighted')
            metrics.recall = recall_score(y_test, y_pred, average='weighted')
            metrics.f1_score = f1_score(y_test, y_pred, average='weighted')

            logger.info(f"Classification metrics - Accuracy: {metrics.accuracy:.4f}, "
                       f"F1: {metrics.f1_score:.4f}")
        else:
            # Regression metrics
            metrics.mse = mean_squared_error(y_test, y_pred)
            metrics.mae = mean_absolute_error(y_test, y_pred)
            metrics.r2_score = r2_score(y_test, y_pred)

            logger.info(f"Regression metrics - MSE: {metrics.mse:.4f}, "
                       f"R2: {metrics.r2_score:.4f}")

        return metrics

    async def predict(self, name: str, X: pd.DataFrame, 
                     include_probabilities: bool = False) -> Dict[str, Any]:
        """Make predictions with a trained model"""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found")

        model_info = self.models[name]

        if model_info.status != ModelStatus.READY:
            raise ValueError(f"Model '{name}' is not ready (status: {model_info.status.value})")

        start_time = time.time()

        # Preprocess input data
        X_processed, _ = self._preprocess_data(X, pd.Series([0] * len(X)), model_info)

        # Make predictions
        predictions = model_info.model.predict(X_processed)

        # Convert predictions back if categorical
        if (model_info.config.model_type == ModelType.CLASSIFICATION and 
            'target' in model_info.label_encoders):
            le = model_info.label_encoders['target']
            predictions = le.inverse_transform(predictions.astype(int))

        result = {
            'predictions': predictions.tolist(),
            'model_version': model_info.version,
            'prediction_time_ms': (time.time() - start_time) * 1000,
            'feature_names': model_info.feature_names
        }

        # Add probabilities for classification
        if (include_probabilities and 
            model_info.config.model_type == ModelType.CLASSIFICATION and
            hasattr(model_info.model, 'predict_proba')):
            probabilities = model_info.model.predict_proba(X_processed)
            result['probabilities'] = probabilities.tolist()
            result['class_names'] = model_info.model.classes_.tolist()

        # Add feature importance if available
        if hasattr(model_info.model, 'feature_importances_'):
            result['feature_importance'] = dict(zip(
                model_info.feature_names,
                model_info.model.feature_importances_.tolist()
            ))

        return result

    async def _save_model(self, model_info: ModelInfo):
        """Save model to disk"""
        try:
            model_file = self.model_path / f"{model_info.name}.pkl"

            model_data = {
                'model': model_info.model,
                'scaler': model_info.scaler,
                'feature_selector': model_info.feature_selector,
                'label_encoders': model_info.label_encoders,
                'feature_names': model_info.feature_names,
                'config': asdict(model_info.config),
                'version': model_info.version,
                'created_at': model_info.created_at,
                'updated_at': model_info.updated_at,
                'metrics_history': [asdict(m) for m in model_info.metrics_history],
                'retraining_trigger': asdict(model_info.retraining_trigger)
            }

            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Model {model_info.name} saved to {model_file}")

        except Exception as e:
            logger.error(f"Error saving model {model_info.name}: {e}")
            raise

    async def load_model(self, name: str) -> bool:
        """Load model from disk"""
        try:
            model_file = self.model_path / f"{name}.pkl"

            if not model_file.exists():
                logger.warning(f"Model file not found: {model_file}")
                return False

            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)

            # Reconstruct ModelInfo
            config_dict = model_data['config']
            config_dict['model_type'] = ModelType(config_dict['model_type'])
            config = ModelConfig(**config_dict)

            model_info = ModelInfo(name, config)
            model_info.model = model_data['model']
            model_info.scaler = model_data.get('scaler')
            model_info.feature_selector = model_data.get('feature_selector')
            model_info.label_encoders = model_data.get('label_encoders', {})
            model_info.feature_names = model_data.get('feature_names', [])
            model_info.version = model_data['version']
            model_info.created_at = model_data['created_at']
            model_info.updated_at = model_data['updated_at']
            model_info.status = ModelStatus.READY

            # Load metrics history
            metrics_history = []
            for m_dict in model_data.get('metrics_history', []):
                m_dict['timestamp'] = datetime.fromisoformat(m_dict['timestamp']) if isinstance(m_dict['timestamp'], str) else m_dict['timestamp']
                metrics_history.append(ModelMetrics(**m_dict))
            model_info.metrics_history = metrics_history

            # Load retraining trigger
            if 'retraining_trigger' in model_data:
                model_info.retraining_trigger = RetrainingTrigger(**model_data['retraining_trigger'])

            self.models[name] = model_info

            logger.info(f"Model {name} loaded successfully - Version: {model_info.version}")
            return True

        except Exception as e:
            logger.error(f"Error loading model {name}: {e}")
            return False

    async def load_all_models(self):
        """Load all models from disk"""
        model_files = list(self.model_path.glob("*.pkl"))
        loaded_count = 0

        for model_file in model_files:
            model_name = model_file.stem
            if await self.load_model(model_name):
                loaded_count += 1

        logger.info(f"Loaded {loaded_count} models from disk")
        return loaded_count

    def get_model_info(self, name: str) -> Dict[str, Any]:
        """Get comprehensive model information"""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found")

        model_info = self.models[name]
        latest_metrics = model_info.metrics_history[-1] if model_info.metrics_history else None

        return {
            'name': model_info.name,
            'version': model_info.version,
            'status': model_info.status.value,
            'model_type': model_info.config.model_type.value,
            'algorithm': model_info.config.algorithm,
            'created_at': model_info.created_at.isoformat(),
            'updated_at': model_info.updated_at.isoformat(),
            'feature_count': len(model_info.feature_names),
            'feature_names': model_info.feature_names,
            'latest_metrics': asdict(latest_metrics) if latest_metrics else None,
            'metrics_history_count': len(model_info.metrics_history),
            'retraining_trigger': asdict(model_info.retraining_trigger)
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """List all models with basic information"""
        return [
            {
                'name': name,
                'version': info.version,
                'status': info.status.value,
                'model_type': info.config.model_type.value,
                'algorithm': info.config.algorithm,
                'updated_at': info.updated_at.isoformat()
            }
            for name, info in self.models.items()
        ]

    async def check_retraining_triggers(self):
        """Check if any models need retraining"""
        models_to_retrain = []

        for name, model_info in self.models.items():
            if not model_info.retraining_trigger.enabled:
                continue

            if model_info.status != ModelStatus.READY:
                continue

            needs_retrain = False
            reason = ""

            # Check time-based trigger
            days_since_update = (datetime.now() - model_info.updated_at).days
            if days_since_update >= model_info.retraining_trigger.time_threshold_days:
                needs_retrain = True
                reason = f"Time threshold exceeded ({days_since_update} days)"

            # Check performance degradation (would need new data to evaluate)
            # This is a placeholder for actual performance monitoring

            if needs_retrain:
                models_to_retrain.append({
                    'name': name,
                    'reason': reason,
                    'days_since_update': days_since_update
                })

        return models_to_retrain

    async def retrain_model(self, name: str, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """Retrain an existing model"""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found")

        model_info = self.models[name]
        original_status = model_info.status

        try:
            model_info.status = ModelStatus.RETRAINING
            logger.info(f"Starting retraining for model: {name}")

            # Train with existing configuration
            metrics = await self.train_model(name, X, y)

            logger.info(f"Model {name} retrained successfully")
            return metrics

        except Exception as e:
            model_info.status = original_status
            logger.error(f"Retraining failed for model {name}: {e}")
            raise

    def start_monitoring(self, check_interval_hours: int = 24):
        """Start automatic monitoring and retraining"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True

        # Schedule periodic checks
        schedule.every(check_interval_hours).hours.do(self._monitoring_job)

        def run_scheduler():
            while self.monitoring_active:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        threading.Thread(target=run_scheduler, daemon=True).start()
        logger.info(f"Started model monitoring with {check_interval_hours}h intervals")

    def stop_monitoring(self):
        """Stop automatic monitoring"""
        self.monitoring_active = False
        schedule.clear()
        logger.info("Stopped model monitoring")

    def _monitoring_job(self):
        """Background monitoring job"""
        try:
            asyncio.run(self._check_and_retrain())
        except Exception as e:
            logger.error(f"Monitoring job error: {e}")

    async def _check_and_retrain(self):
        """Check triggers and retrain if needed"""
        models_to_retrain = await self.check_retraining_triggers()

        if models_to_retrain:
            logger.info(f"Found {len(models_to_retrain)} models needing retraining")

            for model_info in models_to_retrain:
                logger.info(f"Model {model_info['name']} needs retraining: {model_info['reason']}")
                # Note: Actual retraining would need new data provided externally

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all models"""
        summary = {
            'total_models': len(self.models),
            'models_by_status': {},
            'models_by_type': {},
            'performance_overview': []
        }

        # Count by status
        for status in ModelStatus:
            count = sum(1 for m in self.models.values() if m.status == status)
            summary['models_by_status'][status.value] = count

        # Count by type
        for model_type in ModelType:
            count = sum(1 for m in self.models.values() if m.config.model_type == model_type)
            summary['models_by_type'][model_type.value] = count

        # Performance overview
        for name, model_info in self.models.items():
            if model_info.metrics_history:
                latest_metrics = model_info.metrics_history[-1]
                performance_metric = (
                    latest_metrics.accuracy if model_info.config.model_type == ModelType.CLASSIFICATION
                    else latest_metrics.r2_score
                )

                summary['performance_overview'].append({
                    'name': name,
                    'type': model_info.config.model_type.value,
                    'algorithm': model_info.config.algorithm,
                    'performance': performance_metric,
                    'last_updated': model_info.updated_at.isoformat()
                })

        return summary

# Example usage and testing
if __name__ == "__main__":
    async def example_usage():
        # Initialize model manager
        manager = ModelManager()

        # Create a classification model
        config = ModelConfig(
            model_type=ModelType.CLASSIFICATION,
            algorithm='random_forest',
            hyperparameters={'n_estimators': 100, 'random_state': 42}
        )

        manager.create_model('iris_classifier', config)

        # Generate sample data
        from sklearn.datasets import make_classification
        X, y = make_classification(n_samples=1000, n_features=4, n_classes=3, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(4)])
        y_series = pd.Series(y)

        # Train model
        metrics = await manager.train_model('iris_classifier', X_df, y_series)
        print(f"Training completed with accuracy: {metrics.accuracy:.4f}")

        # Make predictions
        result = await manager.predict('iris_classifier', X_df.head(10))
        print(f"Predictions: {result['predictions'][:5]}")

        # Get model info
        info = manager.get_model_info('iris_classifier')
        print(f"Model info: {info['name']} - {info['status']}")

        # Start monitoring
        manager.start_monitoring(check_interval_hours=1)

        print("Model manager example completed successfully!")

    # Run example
    asyncio.run(example_usage())
