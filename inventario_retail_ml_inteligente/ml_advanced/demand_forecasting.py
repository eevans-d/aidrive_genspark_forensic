"""
Sistema de Predicción de Demanda Multi-Dimensional
Específico para retail argentino con patrones estacionales y eventos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ml_engine_advanced import MLEngineAdvanced
import holidays
import calendar

class DemandForecaster:
    """Sistema avanzado de predicción de demanda para retail argentino"""

    def __init__(self, ml_engine=None):
        self.ml_engine = ml_engine or MLEngineAdvanced()
        self.argentina_holidays = self._get_argentina_holidays()

        # Patrones estacionales argentinos
        self.seasonal_patterns = {
            'Bebidas': {
                'verano_multiplier': 1.8,    # Verano aumenta bebidas 80%
                'invierno_multiplier': 0.7,  # Invierno baja 30%
                'finde_multiplier': 1.4      # Fin de semana +40%
            },
            'Almacen': {
                'verano_multiplier': 0.9,    # Verano baja almacén
                'invierno_multiplier': 1.3,  # Invierno sube conservas
                'finde_multiplier': 1.1      # Fin de semana +10%
            },
            'Lacteos': {
                'verano_multiplier': 1.2,    # Verano sube lácteos
                'invierno_multiplier': 1.0,  # Invierno normal
                'finde_multiplier': 1.2      # Fin de semana +20%
            },
            'Panaderia': {
                'verano_multiplier': 0.9,    # Verano baja pan
                'invierno_multiplier': 1.1,  # Invierno sube pan
                'finde_multiplier': 1.5      # Fin de semana +50%
            }
        }

        # Efectos eventos argentinos
        self.event_effects = {
            'navidad': 2.5,           # Navidad aumenta 150%
            'año_nuevo': 2.0,         # Año nuevo +100%
            'dia_madre': 1.8,         # Día madre +80%
            'dia_padre': 1.5,         # Día padre +50%
            'hot_sale': 1.7,          # Hot Sale +70%
            'back_to_school': 1.4,    # Vuelta al cole +40%
            'carnaval': 1.6,          # Carnaval +60%
            'independencia': 1.3,     # Feriados patrios +30%
            'normal': 1.0             # Días normales
        }

    def _get_argentina_holidays(self):
        """Obtener feriados argentinos"""

        argentina_holidays = holidays.Argentina(years=range(2023, 2026))
        return argentina_holidays

    def predict_demand_multi_period(self, producto_codigo, categoria, periods=[7, 15, 30]):
        """Predicción demanda múltiples períodos"""

        today = datetime.now()
        predictions = {}

        for days in periods:
            daily_predictions = []

            for i in range(days):
                target_date = today + timedelta(days=i+1)

                # Predicción base del ML
                base_prediction, error = self.ml_engine.predict_demand(
                    producto_codigo, target_date
                )

                if base_prediction:
                    base_value = base_prediction['prediccion_ensemble']

                    # Aplicar ajustes estacionales
                    adjusted_value = self._apply_seasonal_adjustments(
                        base_value, target_date, categoria
                    )

                    # Aplicar eventos argentinos
                    final_value = self._apply_event_effects(
                        adjusted_value, target_date
                    )

                    daily_predictions.append({
                        'fecha': target_date,
                        'prediccion_base': base_value,
                        'prediccion_ajustada': round(adjusted_value, 1),
                        'prediccion_final': round(final_value, 1),
                        'confianza': base_prediction['confianza'],
                        'es_feriado': target_date.date() in self.argentina_holidays,
                        'evento': self.ml_engine.detect_events_argentina(target_date)
                    })
                else:
                    # Fallback predicción simple
                    daily_predictions.append({
                        'fecha': target_date,
                        'prediccion_base': 0,
                        'prediccion_ajustada': 0,
                        'prediccion_final': 0,
                        'confianza': 0.3,
                        'es_feriado': target_date.date() in self.argentina_holidays,
                        'evento': 'normal'
                    })

            # Calcular estadísticas del período
            total_demand = sum([p['prediccion_final'] for p in daily_predictions])
            avg_daily = total_demand / days
            peak_day = max(daily_predictions, key=lambda x: x['prediccion_final'])
            low_day = min(daily_predictions, key=lambda x: x['prediccion_final'])

            predictions[f'{days}_dias'] = {
                'predicciones_diarias': daily_predictions,
                'demanda_total_periodo': round(total_demand, 1),
                'promedio_diario': round(avg_daily, 1),
                'dia_pico': {
                    'fecha': peak_day['fecha'].strftime('%Y-%m-%d'),
                    'demanda': peak_day['prediccion_final'],
                    'evento': peak_day['evento']
                },
                'dia_minimo': {
                    'fecha': low_day['fecha'].strftime('%Y-%m-%d'),
                    'demanda': low_day['prediccion_final'],
                    'evento': low_day['evento']
                }
            }

        return predictions

    def _apply_seasonal_adjustments(self, base_value, target_date, categoria):
        """Aplicar ajustes estacionales argentinos"""

        if categoria not in self.seasonal_patterns:
            return base_value

        pattern = self.seasonal_patterns[categoria]
        adjusted_value = base_value

        # Ajuste por estación
        month = target_date.month
        if month in [12, 1, 2]:  # Verano
            adjusted_value *= pattern['verano_multiplier']
        elif month in [6, 7, 8]:  # Invierno
            adjusted_value *= pattern['invierno_multiplier']

        # Ajuste por día de semana
        if target_date.weekday() in [5, 6]:  # Fin de semana
            adjusted_value *= pattern['finde_multiplier']
        elif target_date.weekday() == 4:  # Viernes
            adjusted_value *= (1 + (pattern['finde_multiplier'] - 1) * 0.5)

        return adjusted_value

    def _apply_event_effects(self, base_value, target_date):
        """Aplicar efectos de eventos argentinos"""

        evento = self.ml_engine.detect_events_argentina(target_date)
        multiplier = self.event_effects.get(evento, 1.0)

        # Efecto pre y post evento (3 días antes y después)
        if evento != 'normal':
            # Día del evento
            return base_value * multiplier

        # Verificar días cercanos a eventos importantes
        for dias_offset in [-3, -2, -1, 1, 2, 3]:
            check_date = target_date + timedelta(days=dias_offset)
            check_evento = self.ml_engine.detect_events_argentina(check_date)

            if check_evento in ['navidad', 'año_nuevo', 'dia_madre', 'hot_sale']:
                # Efecto gradual días cercanos
                effect_strength = 1 - (abs(dias_offset) * 0.1)
                event_multiplier = self.event_effects.get(check_evento, 1.0)
                partial_effect = 1 + ((event_multiplier - 1) * effect_strength)
                return base_value * partial_effect

        return base_value

    def get_weekly_pattern(self, producto_codigo, categoria, weeks=4):
        """Analizar patrón semanal de demanda"""

        today = datetime.now()
        weekly_data = {}

        for week in range(weeks):
            week_start = today + timedelta(weeks=week)
            week_predictions = []

            for day in range(7):
                target_date = week_start + timedelta(days=day)

                # Predicción día específico
                prediction, _ = self.ml_engine.predict_demand(producto_codigo, target_date)

                if prediction:
                    base_value = prediction['prediccion_ensemble']
                    adjusted = self._apply_seasonal_adjustments(base_value, target_date, categoria)
                    final = self._apply_event_effects(adjusted, target_date)

                    week_predictions.append({
                        'dia_semana': calendar.day_name[target_date.weekday()],
                        'fecha': target_date.strftime('%Y-%m-%d'),
                        'demanda': round(final, 1),
                        'es_feriado': target_date.date() in self.argentina_holidays
                    })

            weekly_data[f'semana_{week+1}'] = {
                'inicio': week_start.strftime('%Y-%m-%d'),
                'predicciones': week_predictions,
                'total_semanal': sum([p['demanda'] for p in week_predictions])
            }

        return weekly_data

    def detect_demand_trends(self, producto_codigo, categoria):
        """Detectar tendencias de demanda"""

        # Predicciones próximos 30 días
        predictions_30d = self.predict_demand_multi_period(
            producto_codigo, categoria, [30]
        )['30_dias']

        daily_demands = [p['prediccion_final'] for p in predictions_30d['predicciones_diarias']]

        # Calcular tendencia
        x = np.arange(len(daily_demands))
        slope = np.polyfit(x, daily_demands, 1)[0]

        # Análisis tendencia
        trend_analysis = {
            'tendencia_diaria': round(slope, 3),
            'direccion': 'creciente' if slope > 0.1 else 'decreciente' if slope < -0.1 else 'estable',
            'variacion_30d': round(slope * 30, 1),
            'demanda_promedio': round(np.mean(daily_demands), 1),
            'volatilidad': round(np.std(daily_demands), 1)
        }

        # Detectar patrones
        patterns = []

        if trend_analysis['direccion'] == 'creciente':
            patterns.append("📈 Demanda en crecimiento - considerar aumentar stock")
        elif trend_analysis['direccion'] == 'decreciente':
            patterns.append("📉 Demanda decreciente - revisar estrategia")

        if trend_analysis['volatilidad'] > trend_analysis['demanda_promedio'] * 0.5:
            patterns.append("⚠️ Alta volatilidad - demanda impredecible")

        # Detectar estacionalidad
        weekend_avg = np.mean([daily_demands[i] for i in range(len(daily_demands)) 
                              if (i % 7) in [5, 6]])
        weekday_avg = np.mean([daily_demands[i] for i in range(len(daily_demands)) 
                              if (i % 7) not in [5, 6]])

        if weekend_avg > weekday_avg * 1.2:
            patterns.append("🎉 Pico fin de semana - stockear viernes")
        elif weekend_avg < weekday_avg * 0.8:
            patterns.append("📅 Baja fin de semana - reducir stock sábado/domingo")

        trend_analysis['patrones_detectados'] = patterns

        return trend_analysis

    def generate_forecast_report(self, producto_codigo, nombre_producto, categoria):
        """Generar reporte completo de forecast"""

        report = {
            'producto': {
                'codigo': producto_codigo,
                'nombre': nombre_producto,
                'categoria': categoria
            },
            'fecha_reporte': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'predicciones_multiples': self.predict_demand_multi_period(
                producto_codigo, categoria
            ),
            'patron_semanal': self.get_weekly_pattern(
                producto_codigo, categoria, weeks=2
            ),
            'analisis_tendencias': self.detect_demand_trends(
                producto_codigo, categoria
            )
        }

        # Resumen ejecutivo
        pred_7d = report['predicciones_multiples']['7_dias']
        pred_30d = report['predicciones_multiples']['30_dias']

        report['resumen_ejecutivo'] = {
            'demanda_proxima_semana': pred_7d['demanda_total_periodo'],
            'demanda_proximo_mes': pred_30d['demanda_total_periodo'],
            'dia_pico_semana': pred_7d['dia_pico'],
            'recomendacion_stock': self._generate_stock_recommendation(pred_7d, pred_30d),
            'alertas': self._generate_alerts(report)
        }

        return report

    def _generate_stock_recommendation(self, pred_7d, pred_30d):
        """Generar recomendación de stock"""

        weekly_demand = pred_7d['demanda_total_periodo']
        monthly_demand = pred_30d['demanda_total_periodo']

        # Stock de seguridad (20% extra)
        safety_stock = weekly_demand * 0.2

        recommendations = {
            'stock_minimo_semanal': round(weekly_demand + safety_stock),
            'stock_optimo_mensual': round(monthly_demand * 1.1),
            'punto_reorden': round(weekly_demand * 0.7),
            'cantidad_compra_sugerida': round(weekly_demand * 2)
        }

        return recommendations

    def _generate_alerts(self, report):
        """Generar alertas basadas en el análisis"""

        alerts = []

        # Alertas de tendencia
        trend = report['analisis_tendencias']['direccion']
        if trend == 'creciente':
            alerts.append({
                'tipo': 'oportunidad',
                'mensaje': '📈 Demanda creciente detectada - considerar aumentar stock',
                'prioridad': 'media'
            })
        elif trend == 'decreciente':
            alerts.append({
                'tipo': 'atencion',
                'mensaje': '📉 Demanda decreciente - revisar estrategia de pricing',
                'prioridad': 'alta'
            })

        # Alertas de eventos
        pred_7d = report['predicciones_multiples']['7_dias']['predicciones_diarias']
        for pred in pred_7d:
            if pred['evento'] in ['navidad', 'hot_sale', 'dia_madre']:
                alerts.append({
                    'tipo': 'evento_importante',
                    'mensaje': f"🎯 {pred['evento'].title()} en {pred['fecha'].strftime('%d/%m')} - demanda esperada: {pred['prediccion_final']} unidades",
                    'prioridad': 'alta'
                })

        # Alertas de volatilidad
        volatilidad = report['analisis_tendencias']['volatilidad']
        promedio = report['analisis_tendencias']['demanda_promedio']

        if volatilidad > promedio * 0.5:
            alerts.append({
                'tipo': 'volatilidad',
                'mensaje': '⚠️ Alta volatilidad de demanda - revisar stock de seguridad',
                'prioridad': 'media'
            })

        return alerts

# Función para testing
def test_demand_forecaster():
    """Test del sistema de predicción de demanda"""

    print("🔮 Testing Sistema Predicción Demanda...")

    # Inicializar con datos ejemplo
    from ml_engine_advanced import generate_sample_data

    df = generate_sample_data()
    ml_engine = MLEngineAdvanced()

    # Entrenar modelo ejemplo
    producto_test = 'CERV001'
    X, y = ml_engine.prepare_training_data(df, producto_test)

    if X is not None:
        ml_engine.train_ensemble_model(X, y, producto_test)

        # Test predictor
        forecaster = DemandForecaster(ml_engine)

        # Predicción multi-período
        predictions = forecaster.predict_demand_multi_period(
            producto_test, 'Bebidas', [7, 15, 30]
        )

        print(f"\n📊 Predicciones para {producto_test}:")
        for period, data in predictions.items():
            print(f"  {period}: {data['demanda_total_periodo']} unidades")
            print(f"    Promedio diario: {data['promedio_diario']}")
            print(f"    Pico: {data['dia_pico']['demanda']} en {data['dia_pico']['fecha']}")

        # Análisis tendencias
        trends = forecaster.detect_demand_trends(producto_test, 'Bebidas')
        print(f"\n📈 Análisis Tendencias:")
        print(f"  Dirección: {trends['direccion']}")
        print(f"  Variación 30d: {trends['variacion_30d']} unidades")
        print(f"  Patrones: {len(trends['patrones_detectados'])} detectados")

        # Reporte completo
        report = forecaster.generate_forecast_report(
            producto_test, 'Cerveza Quilmes 970ml', 'Bebidas'
        )

        print(f"\n📋 Resumen Ejecutivo:")
        resumen = report['resumen_ejecutivo']
        print(f"  Demanda semana: {resumen['demanda_proxima_semana']} unidades")
        print(f"  Stock mínimo sugerido: {resumen['recomendacion_stock']['stock_minimo_semanal']} unidades")
        print(f"  Alertas: {len(resumen['alertas'])}")

        return report

    return None

if __name__ == "__main__":
    test_report = test_demand_forecaster()
    print("\n✅ Sistema Predicción Demanda listo!")
