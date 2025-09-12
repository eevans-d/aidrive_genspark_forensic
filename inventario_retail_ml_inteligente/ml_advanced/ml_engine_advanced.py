"""
Motor ML Avanzado para Sistema de Inventario Retail Argentino
Predicciones inteligentes para decisiones comerciales diarias
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

class MLEngineAdvanced:
    """Motor ML principal con múltiples algoritmos para predicciones retail"""

    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(random_state=42),
            'arima': None  # Se inicializa por producto
        }

        self.model_weights = {
            'random_forest': 0.4,
            'xgboost': 0.4, 
            'arima': 0.2
        }

        self.trained_models = {}
        self.feature_importance = {}
        self.accuracy_metrics = {}

    def create_features(self, df, target_product=None):
        """Crear features avanzadas para ML"""

        # Features básicas
        df['year'] = df['fecha'].dt.year
        df['month'] = df['fecha'].dt.month  
        df['day'] = df['fecha'].dt.day
        df['weekday'] = df['fecha'].dt.weekday
        df['quarter'] = df['fecha'].dt.quarter
        df['week_of_year'] = df['fecha'].dt.isocalendar().week

        # Features estacionales Argentina
        df['es_verano'] = df['month'].isin([12, 1, 2]).astype(int)
        df['es_invierno'] = df['month'].isin([6, 7, 8]).astype(int)
        df['es_fin_semana'] = df['weekday'].isin([5, 6]).astype(int)

        # Features económicos Argentina
        df['inflacion_mensual'] = 0.045  # 4.5% mensual promedio
        df['semana_mes'] = (df['day'] - 1) // 7 + 1

        # Features de lag (valores históricos)
        if target_product:
            product_data = df[df['codigo_producto'] == target_product].copy()
            product_data = product_data.sort_values('fecha')

            # Lags de demanda
            for lag in [1, 7, 14, 30]:
                product_data[f'demanda_lag_{lag}'] = product_data['cantidad_vendida'].shift(lag)

            # Medias móviles
            for window in [7, 14, 30]:
                product_data[f'media_movil_{window}'] = product_data['cantidad_vendida'].rolling(window=window).mean()

            # Trend y estacionalidad
            product_data['trend'] = range(len(product_data))

            return product_data.dropna()

        return df

    def detect_events_argentina(self, date):
        """Detectar eventos/feriados argentinos que afectan ventas"""

        events = {
            # Feriados nacionales principales
            'año_nuevo': [(1, 1)],
            'carnaval': [(2, 12), (2, 13)],  # Aproximado, cambia cada año
            'dia_memoria': [(3, 24)],
            'malvinas': [(4, 2)], 
            'dia_trabajador': [(5, 1)],
            'revolucion_mayo': [(5, 25)],
            'belgrano': [(6, 20)],
            'independencia': [(7, 9)],
            'san_martin': [(8, 17)],
            'dia_raza': [(10, 12)],
            'soberania': [(11, 20)],
            'navidad': [(12, 25)]
        }

        month_day = (date.month, date.day)

        for event, dates in events.items():
            if month_day in dates:
                return event

        # Eventos especiales retail
        if date.month == 2:  # Febrero - Back to school
            return 'back_to_school'
        elif date.month == 6:  # Junio - Día del padre + invierno
            return 'dia_padre_invierno'  
        elif date.month == 10:  # Octubre - Día madre + primavera
            return 'dia_madre_primavera'
        elif date.month == 11:  # Noviembre - Hot Sale + Black Friday
            return 'hot_sale'
        elif date.month == 12:  # Diciembre - Navidad + vacaciones
            return 'temporada_alta'

        return 'normal'

    def prepare_training_data(self, df, producto_codigo):
        """Preparar datos para entrenamiento específico por producto"""

        # Filtrar por producto
        product_df = df[df['codigo_producto'] == producto_codigo].copy()
        product_df = product_df.sort_values('fecha')

        if len(product_df) < 30:  # Mínimo 30 registros
            return None, None

        # Crear features
        product_df = self.create_features(product_df, producto_codigo)

        # Agregar eventos
        product_df['evento'] = product_df['fecha'].apply(self.detect_events_argentina)

        # One-hot encoding eventos
        eventos_dummies = pd.get_dummies(product_df['evento'], prefix='evento')
        product_df = pd.concat([product_df, eventos_dummies], axis=1)

        # Seleccionar features para modelo
        feature_cols = [
            'month', 'day', 'weekday', 'quarter', 'week_of_year',
            'es_verano', 'es_invierno', 'es_fin_semana',
            'semana_mes', 'trend'
        ]

        # Agregar lags si existen
        lag_cols = [col for col in product_df.columns if 'lag_' in col or 'media_movil_' in col]
        feature_cols.extend(lag_cols)

        # Agregar eventos
        event_cols = [col for col in product_df.columns if col.startswith('evento_')]
        feature_cols.extend(event_cols)

        # Eliminar columnas que no existen
        feature_cols = [col for col in feature_cols if col in product_df.columns]

        X = product_df[feature_cols]
        y = product_df['cantidad_vendida']

        return X, y

    def train_ensemble_model(self, X, y, producto_codigo):
        """Entrenar ensemble de modelos para un producto"""

        if len(X) < 20:
            print(f"Datos insuficientes para {producto_codigo}")
            return False

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        trained_models = {}
        predictions = {}

        # Random Forest
        try:
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X_train, y_train)
            rf_pred = rf_model.predict(X_test)
            predictions['random_forest'] = rf_pred
            trained_models['random_forest'] = rf_model

            # Feature importance
            self.feature_importance[f'{producto_codigo}_rf'] = dict(zip(X.columns, rf_model.feature_importances_))

        except Exception as e:
            print(f"Error Random Forest {producto_codigo}: {e}")

        # XGBoost
        try:
            xgb_model = xgb.XGBRegressor(random_state=42, verbosity=0)
            xgb_model.fit(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)
            predictions['xgboost'] = xgb_pred
            trained_models['xgboost'] = xgb_model

        except Exception as e:
            print(f"Error XGBoost {producto_codigo}: {e}")

        # ARIMA (solo para series temporales largas)
        try:
            if len(y_train) >= 50:
                # Usar solo valores históricos para ARIMA
                arima_model = ARIMA(y_train, order=(1, 1, 1))
                arima_fitted = arima_model.fit()
                arima_pred = arima_fitted.forecast(steps=len(y_test))
                predictions['arima'] = arima_pred
                trained_models['arima'] = arima_fitted

        except Exception as e:
            print(f"Error ARIMA {producto_codigo}: {e}")

        if not predictions:
            return False

        # Calcular accuracy por modelo
        model_accuracy = {}
        for model_name, pred in predictions.items():
            mae = mean_absolute_error(y_test, pred)
            model_accuracy[model_name] = 1 / (1 + mae)  # Convertir MAE a accuracy score

        # Guardar modelos y métricas
        self.trained_models[producto_codigo] = trained_models
        self.accuracy_metrics[producto_codigo] = model_accuracy

        print(f"✅ Modelo entrenado para {producto_codigo}")
        print(f"   Accuracy: {model_accuracy}")

        return True

    def predict_demand(self, producto_codigo, fecha_target, X_features=None):
        """Predecir demanda para un producto específico"""

        if producto_codigo not in self.trained_models:
            return None, "Modelo no entrenado para este producto"

        models = self.trained_models[producto_codigo]
        predictions = {}

        # Generar features para fecha target si no se proveen
        if X_features is None:
            # Crear DataFrame con fecha target
            target_df = pd.DataFrame({
                'fecha': [fecha_target],
                'codigo_producto': [producto_codigo]
            })

            # Crear features básicas
            target_df['month'] = target_df['fecha'].dt.month
            target_df['day'] = target_df['fecha'].dt.day
            target_df['weekday'] = target_df['fecha'].dt.weekday
            target_df['quarter'] = target_df['fecha'].dt.quarter
            target_df['week_of_year'] = target_df['fecha'].dt.isocalendar().week
            target_df['es_verano'] = target_df['month'].isin([12, 1, 2]).astype(int)
            target_df['es_invierno'] = target_df['month'].isin([6, 7, 8]).astype(int)
            target_df['es_fin_semana'] = target_df['weekday'].isin([5, 6]).astype(int)
            target_df['semana_mes'] = (target_df['day'] - 1) // 7 + 1

            # Evento
            evento = self.detect_events_argentina(fecha_target)
            target_df[f'evento_{evento}'] = 1

            # Completar con ceros las columnas faltantes
            feature_cols = list(models.values())[0].feature_names_in_ if hasattr(list(models.values())[0], 'feature_names_in_') else []

            for col in feature_cols:
                if col not in target_df.columns:
                    target_df[col] = 0

            X_features = target_df[feature_cols]

        # Predicciones por modelo
        for model_name, model in models.items():
            try:
                if model_name == 'arima':
                    pred = model.forecast(steps=1)[0]
                else:
                    pred = model.predict(X_features)[0]

                predictions[model_name] = max(0, pred)  # No predecir valores negativos

            except Exception as e:
                print(f"Error predicción {model_name}: {e}")

        if not predictions:
            return None, "Error en todas las predicciones"

        # Ensemble prediction (promedio ponderado)
        ensemble_pred = 0
        total_weight = 0

        for model_name, pred in predictions.items():
            if modelo_name in self.model_weights:
                weight = self.model_weights[model_name]
                ensemble_pred += pred * weight
                total_weight += weight

        if total_weight > 0:
            ensemble_pred = ensemble_pred / total_weight
        else:
            ensemble_pred = np.mean(list(predictions.values()))

        return {
            'prediccion_ensemble': round(ensemble_pred, 2),
            'predicciones_individuales': predictions,
            'confianza': min(self.accuracy_metrics.get(producto_codigo, {}).values()) if producto_codigo in self.accuracy_metrics else 0.5
        }, None

    def get_model_stats(self, producto_codigo=None):
        """Obtener estadísticas de modelos"""

        if producto_codigo:
            return {
                'accuracy_metrics': self.accuracy_metrics.get(producto_codigo, {}),
                'feature_importance': self.feature_importance.get(f'{producto_codigo}_rf', {}),
                'models_trained': list(self.trained_models.get(producto_codigo, {}).keys())
            }
        else:
            return {
                'total_products': len(self.trained_models),
                'avg_accuracy': np.mean([np.mean(list(metrics.values())) for metrics in self.accuracy_metrics.values()]) if self.accuracy_metrics else 0,
                'products_trained': list(self.trained_models.keys())
            }

# Función para generar datos de ejemplo
def generate_sample_data():
    """Generar datos de ejemplo para testing"""

    np.random.seed(42)

    # Productos ejemplo argentinos
    productos = [
        {'codigo': 'ACEIT001', 'nombre': 'Aceite Girasol 900ml', 'categoria': 'Almacen'},
        {'codigo': 'LECHE001', 'nombre': 'Leche Larga Vida 1L', 'categoria': 'Lacteos'},
        {'codigo': 'PAN001', 'nombre': 'Pan Lactal Bimbo', 'categoria': 'Panaderia'},
        {'codigo': 'AZUC001', 'nombre': 'Azúcar 1kg', 'categoria': 'Almacen'},
        {'codigo': 'CERV001', 'nombre': 'Cerveza Quilmes 970ml', 'categoria': 'Bebidas'}
    ]

    # Generar datos 6 meses
    start_date = datetime.now() - timedelta(days=180)
    dates = pd.date_range(start_date, periods=180, freq='D')

    data = []

    for producto in productos:
        base_demand = np.random.normal(20, 5)  # Demanda base

        for i, date in enumerate(dates):
            # Patrón estacional
            seasonal_factor = 1.0
            if date.month in [12, 1, 2]:  # Verano - más bebidas
                if producto['categoria'] == 'Bebidas':
                    seasonal_factor = 1.5
            elif date.month in [6, 7, 8]:  # Invierno - más almacén
                if producto['categoria'] == 'Almacen':
                    seasonal_factor = 1.3

            # Patrón semanal
            weekday_factor = 1.2 if date.weekday() in [4, 5, 6] else 0.9

            # Tendencia leve creciente (inflación)
            trend_factor = 1 + (i * 0.001)

            # Ruido aleatorio
            noise = np.random.normal(0, 2)

            demand = max(0, base_demand * seasonal_factor * weekday_factor * trend_factor + noise)

            data.append({
                'fecha': date,
                'codigo_producto': producto['codigo'],
                'nombre_producto': producto['nombre'],
                'categoria': producto['categoria'],
                'cantidad_vendida': round(demand),
                'precio_unitario': round(np.random.uniform(100, 500), 2)  # Precios argentinos
            })

    return pd.DataFrame(data)

if __name__ == "__main__":
    # Test del motor ML
    print("🤖 Iniciando Motor ML Avanzado...")

    # Generar datos ejemplo
    df = generate_sample_data()
    print(f"📊 Datos generados: {len(df)} registros, {df['codigo_producto'].nunique()} productos")

    # Inicializar motor
    ml_engine = MLEngineAdvanced()

    # Entrenar modelos por producto
    productos = df['codigo_producto'].unique()

    for producto in productos:
        print(f"\n🔄 Entrenando modelo para {producto}...")
        X, y = ml_engine.prepare_training_data(df, producto)

        if X is not None:
            success = ml_engine.train_ensemble_model(X, y, producto)
            if success:
                # Test predicción
                fecha_test = datetime.now() + timedelta(days=7)
                pred_result, error = ml_engine.predict_demand(producto, fecha_test)

                if pred_result:
                    print(f"   📈 Predicción 7 días: {pred_result['prediccion_ensemble']} unidades")
                    print(f"   🎯 Confianza: {pred_result['confianza']:.2%}")

    # Estadísticas generales
    print(f"\n📊 Resumen Motor ML:")
    stats = ml_engine.get_model_stats()
    print(f"   - Productos entrenados: {stats['total_products']}")
    print(f"   - Accuracy promedio: {stats['avg_accuracy']:.2%}")

    print("\n✅ Motor ML Avanzado listo!")
