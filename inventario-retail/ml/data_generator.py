"""
Generador de datos históricos sample para entrenamiento ML
Crea datos realistas de ventas con patrones estacionales e inflación
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from typing import Dict, List
import os

class SampleDataGenerator:
    """Generador de datos de ventas realistas para Argentina"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)

        # Productos sample típicos de retail argentino
        self.productos_sample = [
            {"codigo": "COCA001", "nombre": "Coca Cola 600ml", "categoria": "bebidas", "precio_base": 120.0},
            {"codigo": "PAN001", "nombre": "Pan Lactal Bimbo", "categoria": "panaderia", "precio_base": 250.0},
            {"codigo": "LECHE001", "nombre": "Leche Entera La Serenísima 1L", "categoria": "lacteos", "precio_base": 180.0},
            {"codigo": "ARROZ001", "nombre": "Arroz Largo Fino Gallo 1kg", "categoria": "almacen", "precio_base": 320.0},
            {"codigo": "ACEITE001", "nombre": "Aceite Girasol Natura 900ml", "categoria": "almacen", "precio_base": 890.0},
            {"codigo": "YERBA001", "nombre": "Yerba Mate Amanda 1kg", "categoria": "almacen", "precio_base": 450.0},
            {"codigo": "DULCE001", "nombre": "Dulce de Leche La Serenísima 400g", "categoria": "lacteos", "precio_base": 380.0},
            {"codigo": "GALLES001", "nombre": "Galletas Oreo 118g", "categoria": "almacen", "precio_base": 280.0},
            {"codigo": "DETER001", "nombre": "Detergente Ala 750ml", "categoria": "limpieza", "precio_base": 420.0},
            {"codigo": "PAPEL001", "nombre": "Papel Higiénico Elite x4", "categoria": "limpieza", "precio_base": 650.0}
        ]

        # Factores estacionales por categoría
        self.seasonal_patterns = {
            "bebidas": {12: 1.4, 1: 1.3, 2: 1.2, 3: 1.0, 4: 0.9, 5: 0.8, 6: 0.7, 7: 0.8, 8: 0.9, 9: 1.0, 10: 1.1, 11: 1.2},
            "panaderia": {12: 1.1, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 0.9, 8: 0.9, 9: 1.0, 10: 1.0, 11: 1.1},
            "lacteos": {12: 1.2, 1: 1.1, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.9, 6: 0.8, 7: 0.8, 8: 0.9, 9: 1.0, 10: 1.1, 11: 1.2},
            "almacen": {12: 1.3, 1: 1.1, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 0.9, 7: 0.9, 8: 1.0, 9: 1.0, 10: 1.1, 11: 1.2},
            "limpieza": {12: 1.1, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.1}
        }

        # Patrones semanales (lunes=0, domingo=6)
        self.weekly_patterns = [1.1, 1.0, 0.9, 1.0, 1.2, 1.4, 1.3]  # Fin de semana más ventas

        # Feriados argentinos
        self.feriados_2024 = [
            "2024-01-01", "2024-02-20", "2024-03-24", "2024-04-02",
            "2024-05-01", "2024-05-25", "2024-06-17", "2024-06-20", 
            "2024-07-09", "2024-08-17", "2024-10-12", "2024-11-20",
            "2024-12-08", "2024-12-25"
        ]

    def generate_sales_history(self, days_back: int = 365, inflacion_mensual: float = 4.5) -> pd.DataFrame:
        """Generar histórico de ventas realista"""

        # Rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        all_sales = []

        # Para cada producto
        for i, producto in enumerate(self.productos_sample):
            producto_id = i + 1

            # Patrón base de demanda (ventas diarias promedio)
            base_demand = self._get_base_demand_by_category(producto["categoria"])

            # Generar ventas día a día
            current_date = start_date
            while current_date <= end_date:

                # Calcular demanda para este día
                daily_demand = self._calculate_daily_demand(
                    base_demand, 
                    current_date, 
                    producto["categoria"],
                    inflacion_mensual
                )

                # Generar ventas (puede ser 0 algunos días)
                if random.random() < 0.8:  # 80% probabilidad de ventas
                    # Cantidad vendida (Poisson con media = daily_demand)
                    cantidad = max(1, np.random.poisson(daily_demand))

                    # Precio con inflación
                    precio = self._calculate_price_with_inflation(
                        producto["precio_base"], 
                        current_date, 
                        inflacion_mensual
                    )

                    all_sales.append({
                        "fecha": current_date,
                        "producto_id": producto_id,
                        "codigo": producto["codigo"],
                        "nombre": producto["nombre"],
                        "categoria": producto["categoria"],
                        "cantidad": cantidad,
                        "precio_unitario": round(precio, 2),
                        "subtotal": round(cantidad * precio, 2),
                        "dia_semana": current_date.weekday(),
                        "mes": current_date.month,
                        "es_feriado": current_date.strftime("%Y-%m-%d") in self.feriados_2024,
                        "factor_estacional": self.seasonal_patterns[producto["categoria"]].get(current_date.month, 1.0)
                    })

                current_date += timedelta(days=1)

        df = pd.DataFrame(all_sales)

        # Agregar features calculadas
        df["trimestre"] = df["fecha"].dt.quarter
        df["semana_año"] = df["fecha"].dt.isocalendar().week
        df["es_fin_semana"] = (df["dia_semana"] >= 5).astype(int)
        df["dias_desde_inicio"] = (df["fecha"] - start_date).dt.days

        return df

    def generate_stock_movements(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """Generar movimientos de stock basados en ventas"""

        movements = []

        # Agrupar ventas por producto y fecha
        for producto_id in sales_df["producto_id"].unique():
            producto_sales = sales_df[sales_df["producto_id"] == producto_id].copy()
            producto_sales = producto_sales.sort_values("fecha")

            stock_actual = 100  # Stock inicial

            for _, sale in producto_sales.iterrows():
                # Movimiento de salida (venta)
                stock_anterior = stock_actual
                stock_actual = max(0, stock_actual - sale["cantidad"])

                movements.append({
                    "fecha": sale["fecha"],
                    "producto_id": producto_id,
                    "tipo": "salida",
                    "cantidad": sale["cantidad"],
                    "stock_anterior": stock_anterior,
                    "stock_posterior": stock_actual,
                    "motivo": "Venta mostrador",
                    "precio_unitario": sale["precio_unitario"]
                })

                # Restock periódico
                if stock_actual < 20 and random.random() < 0.6:  # 60% chance de restock
                    cantidad_entrada = random.randint(50, 100)
                    stock_anterior = stock_actual
                    stock_actual += cantidad_entrada

                    movements.append({
                        "fecha": sale["fecha"] + timedelta(hours=random.randint(1, 12)),
                        "producto_id": producto_id,
                        "tipo": "entrada",
                        "cantidad": cantidad_entrada,
                        "stock_anterior": stock_anterior,
                        "stock_posterior": stock_actual,
                        "motivo": "Reposición proveedor",
                        "precio_unitario": sale["precio_unitario"] * 0.7  # Precio compra
                    })

        return pd.DataFrame(movements)

    def save_sample_data(self, output_dir: str = "data/sample"):
        """Guardar datos sample en archivos"""

        os.makedirs(output_dir, exist_ok=True)

        # Generar datos
        print("📊 Generando datos de ventas...")
        sales_df = self.generate_sales_history(days_back=365)

        print("📦 Generando movimientos de stock...")
        movements_df = self.generate_stock_movements(sales_df)

        # Guardar CSVs
        sales_file = os.path.join(output_dir, "ventas_historicas.csv")
        movements_file = os.path.join(output_dir, "movimientos_stock.csv")
        productos_file = os.path.join(output_dir, "productos_sample.json")

        sales_df.to_csv(sales_file, index=False)
        movements_df.to_csv(movements_file, index=False)

        # Guardar info productos
        with open(productos_file, 'w', encoding='utf-8') as f:
            json.dump(self.productos_sample, f, indent=2, ensure_ascii=False)

        # Estadísticas
        stats = {
            "total_ventas": len(sales_df),
            "total_movimientos": len(movements_df),
            "productos": len(self.productos_sample),
            "fechas": {
                "inicio": sales_df["fecha"].min().strftime("%Y-%m-%d"),
                "fin": sales_df["fecha"].max().strftime("%Y-%m-%d")
            },
            "ventas_por_categoria": sales_df.groupby("categoria")["cantidad"].sum().to_dict(),
            "ingresos_por_mes": sales_df.groupby(sales_df["fecha"].dt.month)["subtotal"].sum().round(2).to_dict()
        }

        stats_file = os.path.join(output_dir, "estadisticas.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"✅ Datos guardados en {output_dir}:")
        print(f"  📈 {sales_file} - {len(sales_df)} ventas")
        print(f"  📦 {movements_file} - {len(movements_df)} movimientos") 
        print(f"  🏷️ {productos_file} - {len(self.productos_sample)} productos")
        print(f"  📊 {stats_file} - estadísticas")

        return sales_df, movements_df, stats

    def _get_base_demand_by_category(self, categoria: str) -> float:
        """Demanda base diaria por categoría"""
        base_demands = {
            "bebidas": 8.0,     # Alta rotación
            "panaderia": 12.0,  # Muy alta rotación
            "lacteos": 6.0,     # Alta rotación
            "almacen": 4.0,     # Media rotación
            "limpieza": 2.0     # Baja rotación
        }
        return base_demands.get(categoria, 3.0)

    def _calculate_daily_demand(self, base_demand: float, date: datetime, categoria: str, inflacion_mensual: float) -> float:
        """Calcular demanda ajustada para un día específico"""

        # Factor estacional
        seasonal_factor = self.seasonal_patterns[categoria].get(date.month, 1.0)

        # Factor semanal
        weekly_factor = self.weekly_patterns[date.weekday()]

        # Factor feriado
        holiday_factor = 0.3 if date.strftime("%Y-%m-%d") in self.feriados_2024 else 1.0

        # Factor inflación (reduce demanda gradualmente)
        days_since_start = (date - datetime(2024, 1, 1)).days
        inflation_factor = 1.0 / ((1 + inflacion_mensual/100) ** (days_since_start / 30.44 / 2))  # Efecto más suave

        # Factor random noise
        noise_factor = random.uniform(0.7, 1.3)

        # Demanda final
        final_demand = base_demand * seasonal_factor * weekly_factor * holiday_factor * inflation_factor * noise_factor

        return max(0.5, final_demand)

    def _calculate_price_with_inflation(self, base_price: float, date: datetime, inflacion_mensual: float) -> float:
        """Calcular precio con inflación acumulada"""

        days_since_start = (date - datetime(2024, 1, 1)).days
        inflation_factor = (1 + inflacion_mensual/100) ** (days_since_start / 30.44)

        # Agregar variabilidad del mercado
        market_variation = random.uniform(0.95, 1.05)

        return base_price * inflation_factor * market_variation

if __name__ == "__main__":
    print("🎲 Generando datos sample para entrenamiento ML...")

    generator = SampleDataGenerator(seed=42)
    sales_df, movements_df, stats = generator.save_sample_data()

    print(f"\n📊 Estadísticas generadas:")
    print(f"  Total ventas: {stats['total_ventas']:,}")
    print(f"  Período: {stats['fechas']['inicio']} a {stats['fechas']['fin']}")
    print(f"  Categorías: {list(stats['ventas_por_categoria'].keys())}")

    print("\n💰 Ingresos por mes (últimos 6 meses):")
    for mes, ingreso in sorted(stats['ingresos_por_mes'].items())[-6:]:
        print(f"  Mes {mes}: ${ingreso:,.2f}")

    print("\n✅ Datos sample generados correctamente")
