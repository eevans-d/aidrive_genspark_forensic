#!/usr/bin/env python3
"""
Script de ejecución diaria del Dashboard Operativo
Ejecutar cada mañana para obtener recomendaciones de compra
"""

from reorder_engine_integrated import ReorderEngineIntegrated
from datetime import datetime
import json

def main():
    """Generar reporte diario de inventario"""
    print("🌅 INICIANDO REPORTE DIARIO DE INVENTARIO")
    print("="*60)

    # Crear motor integrado
    engine = ReorderEngineIntegrated()

    # Generar dashboard para hoy
    dashboard = engine.generar_dashboard_operativo_diario()

    # Mostrar resumen ejecutivo
    print(f"📅 REPORTE DEL {dashboard.fecha_reporte.strftime('%Y-%m-%d')}")
    print("-" * 60)

    # 1. COMPRAS URGENTES
    compras_urgentes = [c for c in dashboard.compras_recomendadas if c.get('prioridad') == 'ALTA']
    if compras_urgentes:
        print("🔴 COMPRAS URGENTES (ACCIÓN INMEDIATA):")
        for compra in compras_urgentes:
            print(f"   • {compra['codigo']}: {compra['cantidad_sugerida']} unidades (${compra['costo_total']:,.2f})")

    # 2. ALERTAS CRÍTICAS  
    alertas_criticas = [a for a in dashboard.alertas_criticas if a.nivel_criticidad == 'CRITICO']
    if alertas_criticas:
        print("\n⚠️ ALERTAS CRÍTICAS:")
        for alerta in alertas_criticas:
            print(f"   • {alerta.producto_nombre}: {alerta.mensaje}")

    # 3. RESUMEN FINANCIERO
    fin = dashboard.metricas_financieras
    print(f"\n💰 RESUMEN FINANCIERO:")
    print(f"   • Inversión recomendada hoy: ${fin['costo_compras_recomendadas_hoy']:,.2f}")
    print(f"   • Valor inventario actual: ${fin['valor_inventario_actual']:,.2f}")
    print(f"   • Impacto inflación diario: ${fin['impacto_inflacion_diario']:,.2f}")

    # 4. KPIs PRINCIPALES
    kpis = dashboard.kpis_principales
    print(f"\n📊 KPIs PRINCIPALES:")
    print(f"   • Disponibilidad productos: {kpis['porcentaje_disponibilidad']}%")
    print(f"   • Productos sin stock: {kpis['productos_sin_stock']}")
    print(f"   • Cobertura promedio: {kpis['cobertura_promedio_dias']} días")

    print("\n" + "="*60)
    print("✅ Reporte generado exitosamente")
    print("📧 TIP: Puedes enviar este reporte por email o integrarlo con Slack/Teams")

    # Opcional: Guardar reporte en archivo
    fecha_str = dashboard.fecha_reporte.strftime('%Y-%m-%d')
    filename = f'reporte_diario_{fecha_str}.json'

    # Serializar dashboard para JSON
    dashboard_dict = {
        'fecha_reporte': dashboard.fecha_reporte.isoformat(),
        'compras_recomendadas': dashboard.compras_recomendadas,
        'kpis_principales': dashboard.kpis_principales,
        'metricas_financieras': dashboard.metricas_financieras,
        'resumen_ejecutivo': {
            'productos_para_comprar': len(dashboard.compras_recomendadas),
            'alertas_criticas': len(dashboard.alertas_criticas),
            'inversion_total': fin['costo_compras_recomendadas_hoy']
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dashboard_dict, f, indent=2, ensure_ascii=False)

    print(f"💾 Reporte guardado en: {filename}")

if __name__ == "__main__":
    main()
