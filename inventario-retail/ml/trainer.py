"""
Entrenador de modelo RandomForest para predicción de demanda
Incluye validación cruzada, backtesting y métricas de performance
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DemandModelTrainer:
    """Entrenador de modelo de predicción de demanda"""

    def __init__(self, model_dir: str = "data/ml/models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        # Parámetros del modelo RandomForest
        self.rf_params = {
            'n_estimators': 100,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }

        self.model = None
        self.feature_columns = None
        self.scaler_stats = None

    def prepare_training_data(self, sales_df: pd.DataFrame, db_session=None) -> Tuple[pd.DataFrame, pd.Series]:
        """Preparar datos para entrenamiento"""

        print("📊 Preparando datos de entrenamiento...")

        # Agrupar ventas por producto y fecha
        daily_sales = sales_df.groupby(['fecha', 'producto_id']).agg({
            'cantidad': 'sum',
            'precio_unitario': 'mean',
            'categoria': 'first',
            'codigo': 'first',
            'nombre': 'first'
        }).reset_index()

        # Crear dataset con ventana deslizante para series temporales
        features_list = []
        targets_list = []

        # Para cada producto
        for producto_id in daily_sales['producto_id'].unique():
            producto_data = daily_sales[daily_sales['producto_id'] == producto_id].copy()
            producto_data = producto_data.sort_values('fecha')

            if len(producto_data) < 30:  # Mínimo 30 días de datos
                continue

            # Ventana deslizante: usar últimos 14 días para predecir próximos 7
            for i in range(14, len(producto_data) - 7):

                # Features de ventana histórica (últimos 14 días)
                historical_window = producto_data.iloc[i-14:i]
                target_window = producto_data.iloc[i:i+7]  # Próximos 7 días

                # Extraer features
                features = self._extract_window_features(
                    historical_window, 
                    target_window.iloc[0]['fecha'],
                    producto_id
                )

                # Target: suma de ventas en próximos 7 días
                target = target_window['cantidad'].sum()

                features_list.append(features)
                targets_list.append(target)

        # Convertir a DataFrames
        X = pd.DataFrame(features_list)
        y = pd.Series(targets_list)

        print(f"✅ Dataset preparado: {len(X)} muestras, {len(X.columns)} features")

        return X, y

    def train_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Entrenar modelo RandomForest con validación cruzada"""

        print("🤖 Entrenando modelo RandomForest...")

        # Guardar columnas de features
        self.feature_columns = X.columns.tolist()

        # Calcular estadísticas para normalización simple
        self.scaler_stats = {
            'mean': X.mean().to_dict(),
            'std': X.std().to_dict()
        }

        # Normalizar features (Z-score)
        X_scaled = (X - X.mean()) / X.std()
        X_scaled = X_scaled.fillna(0)  # Manejar NaN en std=0

        # Validación cruzada con series temporales
        tscv = TimeSeriesSplit(n_splits=5)

        # Entrenar modelo
        self.model = RandomForestRegressor(**self.rf_params)

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_scaled, y, 
            cv=tscv, 
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )

        # Entrenar modelo final con todos los datos
        self.model.fit(X_scaled, y)

        # Predicciones en training set para métricas
        y_pred = self.model.predict(X_scaled)

        # Calcular métricas
        metrics = {
            'mae_cv': -cv_scores.mean(),
            'mae_cv_std': cv_scores.std(),
            'mae_train': mean_absolute_error(y, y_pred),
            'mse_train': mean_squared_error(y, y_pred),
            'rmse_train': np.sqrt(mean_squared_error(y, y_pred)),
            'r2_train': r2_score(y, y_pred),
            'feature_count': len(self.feature_columns),
            'sample_count': len(X),
            'training_date': datetime.now().isoformat()
        }

        # Feature importance
        feature_importance = dict(zip(
            self.feature_columns,
            self.model.feature_importances_
        ))

        # Top 10 features más importantes
        top_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]

        metrics['top_features'] = top_features

        print(f"✅ Modelo entrenado:")
        print(f"  📊 MAE (CV): {metrics['mae_cv']:.2f} ± {metrics['mae_cv_std']:.2f}")
        print(f"  📈 R² (train): {metrics['r2_train']:.3f}")
        print(f"  🎯 Accuracy esperada: {max(0, min(100, (1 - metrics['mae_cv']/10) * 100)):.1f}%")

        return metrics

    def save_model(self, metrics: Dict, model_name: str = "demand_predictor") -> str:
        """Guardar modelo entrenado"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{model_name}_{timestamp}.joblib"
        model_path = os.path.join(self.model_dir, model_filename)

        # Guardar modelo
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'scaler_stats': self.scaler_stats,
            'metrics': metrics,
            'rf_params': self.rf_params
        }

        joblib.dump(model_data, model_path)

        # Guardar metadata
        metadata = {
            'model_file': model_filename,
            'model_path': model_path,
            'created_at': datetime.now().isoformat(),
            'metrics': metrics,
            'feature_count': len(self.feature_columns),
            'model_type': 'RandomForestRegressor'
        }

        metadata_path = os.path.join(self.model_dir, f"{model_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"💾 Modelo guardado:")
        print(f"  📁 {model_path}")
        print(f"  📋 {metadata_path}")

        return model_path

    def _extract_window_features(self, historical_window: pd.DataFrame, target_date: datetime, 
                                producto_id: int) -> Dict[str, float]:
        """Extraer features de ventana histórica"""

        if len(historical_window) == 0:
            return self._get_default_features()

        features = {}

        # Features estadísticos de la ventana
        cantidades = historical_window['cantidad'].values
        precios = historical_window['precio_unitario'].values

        features.update({
            # Estadísticas de ventas
            'venta_promedio_14d': np.mean(cantidades),
            'venta_mediana_14d': np.median(cantidades),
            'venta_std_14d': np.std(cantidades),
            'venta_max_14d': np.max(cantidades),
            'venta_min_14d': np.min(cantidades),
            'venta_total_14d': np.sum(cantidades),

            # Tendencias
            'tendencia_ventas': np.polyfit(range(len(cantidades)), cantidades, 1)[0] if len(cantidades) > 1 else 0,
            'tendencia_precios': np.polyfit(range(len(precios)), precios, 1)[0] if len(precios) > 1 else 0,

            # Estadísticas de precios
            'precio_promedio_14d': np.mean(precios),
            'precio_std_14d': np.std(precios),

            # Features temporales del target
            'target_dia_semana': target_date.weekday(),
            'target_mes': target_date.month,
            'target_dia_mes': target_date.day,
            'target_trimestre': (target_date.month - 1) // 3 + 1,

            # Features de contexto
            'es_fin_semana': 1.0 if target_date.weekday() >= 5 else 0.0,
            'es_inicio_mes': 1.0 if target_date.day <= 5 else 0.0,
            'es_fin_mes': 1.0 if target_date.day >= 25 else 0.0,

            # Features del producto (si disponible)
            'categoria_encoded': self._encode_category(historical_window.iloc[0]['categoria']),
            'producto_id': float(producto_id)
        })

        return features

    def _encode_category(self, categoria: str) -> float:
        """Encoding de categorías"""
        mapping = {
            'bebidas': 1.0, 'lacteos': 2.0, 'panaderia': 3.0,
            'almacen': 4.0, 'limpieza': 5.0, 'otros': 6.0
        }
        return mapping.get(categoria.lower(), 6.0)

    def _get_default_features(self) -> Dict[str, float]:
        """Features default cuando no hay datos"""
        return {
            'venta_promedio_14d': 0.0, 'venta_mediana_14d': 0.0,
            'venta_std_14d': 0.0, 'venta_max_14d': 0.0,
            'venta_min_14d': 0.0, 'venta_total_14d': 0.0,
            'tendencia_ventas': 0.0, 'tendencia_precios': 0.0,
            'precio_promedio_14d': 0.0, 'precio_std_14d': 0.0,
            'target_dia_semana': 0.0, 'target_mes': 1.0,
            'target_dia_mes': 1.0, 'target_trimestre': 1.0,
            'es_fin_semana': 0.0, 'es_inicio_mes': 0.0,
            'es_fin_mes': 0.0, 'categoria_encoded': 6.0,
            'producto_id': 1.0
        }

def train_demand_model_from_sample() -> str:
    """Función principal para entrenar modelo desde datos sample"""

    print("🚀 Iniciando entrenamiento de modelo de demanda...")

    # Generar datos sample si no existen
    sample_data_path = "data/sample/ventas_historicas.csv"

    if not os.path.exists(sample_data_path):
        print("📊 Generando datos sample...")
        from .data_generator import SampleDataGenerator
        generator = SampleDataGenerator()
        sales_df, _, _ = generator.save_sample_data()
    else:
        print("📂 Cargando datos sample existentes...")
        sales_df = pd.read_csv(sample_data_path)
        sales_df['fecha'] = pd.to_datetime(sales_df['fecha'])

    # Entrenar modelo
    trainer = DemandModelTrainer()

    # Preparar datos
    X, y = trainer.prepare_training_data(sales_df)

    if len(X) == 0:
        raise ValueError("No se pudieron generar datos de entrenamiento")

    # Entrenar
    metrics = trainer.train_model(X, y)

    # Guardar modelo
    model_path = trainer.save_model(metrics)

    print(f"\n🎉 Entrenamiento completado:")
    print(f"  📁 Modelo: {model_path}")
    print(f"  🎯 Accuracy estimada: {max(0, min(100, (1 - metrics['mae_cv']/10) * 100)):.1f}%")

    return model_path

if __name__ == "__main__":
    model_path = train_demand_model_from_sample()
    print(f"✅ Modelo entrenado y guardado en: {model_path}")
