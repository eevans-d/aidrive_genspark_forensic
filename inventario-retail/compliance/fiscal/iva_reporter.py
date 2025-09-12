"""
Generador de reportes IVA mensual según formato AFIP
Compliance fiscal para retail argentino
"""
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class AlicuotasIVA:
    """Alícuotas IVA oficiales AFIP actualizadas"""

    ALICUOTAS = {
        0.0: "No Gravado",
        10.5: "IVA 10.5%",
        21.0: "IVA 21%",
        27.0: "IVA 27%"
    }

    # Códigos AFIP para alícuotas
    CODIGOS_AFIP = {
        0.0: "2",    # No gravado
        10.5: "4",   # 10.5%
        21.0: "5",   # 21%
        27.0: "6"    # 27%
    }

    @classmethod
    def get_alicuota_nombre(cls, alicuota: float) -> str:
        """Obtener nombre de alícuota"""
        return cls.ALICUOTAS.get(alicuota, f"Alícuota {alicuota}%")

    @classmethod
    def get_codigo_afip(cls, alicuota: float) -> str:
        """Obtener código AFIP para alícuota"""
        return cls.CODIGOS_AFIP.get(alicuota, "5")  # Default 21%

class ReporteIVA:
    """Generador de reportes IVA mensual AFIP"""

    def __init__(self, db_session, output_dir: str = "compliance/reportes"):
        self.db = db_session
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_reporte_mensual(self, año: int, mes: int, cuit_emisor: str) -> Dict:
        """Generar reporte IVA completo para el mes"""
        try:
            # Validar período
            if not (1 <= mes <= 12):
                raise ValueError("Mes debe estar entre 1 y 12")

            # Fechas del período
            fecha_desde = datetime(año, mes, 1)
            if mes == 12:
                fecha_hasta = datetime(año + 1, 1, 1) - timedelta(days=1)
            else:
                fecha_hasta = datetime(año, mes + 1, 1) - timedelta(days=1)

            logger.info(f"Generando reporte IVA {mes:02d}/{año}")

            # Obtener datos de facturas del período
            facturas = self._obtener_facturas_periodo(fecha_desde, fecha_hasta, cuit_emisor)

            # Procesar datos
            resumen_iva = self._procesar_resumen_iva(facturas)
            detalle_compras = self._procesar_detalle_compras(facturas)
            detalle_ventas = self._procesar_detalle_ventas(facturas)

            # Generar archivos
            archivos_generados = self._generar_archivos_afip(
                año, mes, resumen_iva, detalle_compras, detalle_ventas
            )

            # Resumen del reporte
            reporte = {
                'periodo': f"{mes:02d}/{año}",
                'fecha_generacion': datetime.now().isoformat(),
                'total_facturas': len(facturas),
                'iva_debito_fiscal': resumen_iva['iva_ventas'],
                'iva_credito_fiscal': resumen_iva['iva_compras'],
                'saldo_tecnico': resumen_iva['iva_ventas'] - resumen_iva['iva_compras'],
                'archivos_generados': archivos_generados,
                'validaciones': self._validar_reporte(resumen_iva)
            }

            # Guardar resumen JSON
            resumen_file = self.output_dir / f"reporte_iva_{año}_{mes:02d}_resumen.json"
            with open(resumen_file, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            logger.info(f"Reporte IVA generado exitosamente: {len(archivos_generados)} archivos")
            return reporte

        except Exception as e:
            logger.error(f"Error generando reporte IVA: {e}")
            raise

    def _obtener_facturas_periodo(self, fecha_desde: datetime, fecha_hasta: datetime, cuit_emisor: str) -> List[Dict]:
        """Obtener facturas del período desde BD"""
        try:
            from shared.models import Factura, FacturaItem

            query = self.db.query(Factura).filter(
                Factura.fecha_emision >= fecha_desde,
                Factura.fecha_emision <= fecha_hasta,
                Factura.estado_procesamiento == 'procesada'
            )

            if cuit_emisor:
                query = query.filter(Factura.cuit_emisor == cuit_emisor)

            facturas_db = query.all()

            facturas = []
            for factura in facturas_db:
                factura_dict = {
                    'id': factura.id,
                    'numero': factura.numero,
                    'tipo': factura.tipo,
                    'punto_venta': factura.punto_venta,
                    'fecha_emision': factura.fecha_emision,
                    'cuit_emisor': factura.cuit_emisor,
                    'nombre_emisor': factura.nombre_emisor,
                    'subtotal': float(factura.subtotal or 0),
                    'iva': float(factura.iva or 0),
                    'total': float(factura.total),
                    'items': []
                }

                # Obtener items
                for item in factura.items:
                    factura_dict['items'].append({
                        'descripcion': item.descripcion,
                        'cantidad': float(item.cantidad),
                        'precio_unitario': float(item.precio_unitario),
                        'subtotal': float(item.subtotal),
                        'alicuota_iva': self._determinar_alicuota_iva(item.subtotal, factura.iva)
                    })

                facturas.append(factura_dict)

            return facturas

        except Exception as e:
            logger.error(f"Error obteniendo facturas: {e}")
            return []

    def _determinar_alicuota_iva(self, subtotal: float, iva_total: float) -> float:
        """Determinar alícuota IVA basada en proporción"""
        if subtotal == 0 or iva_total == 0:
            return 0.0

        # Calcular alícuota aproximada
        alicuota_calculada = (iva_total / subtotal) * 100

        # Redondear a alícuota más cercana
        alicuotas_validas = [0.0, 10.5, 21.0, 27.0]
        alicuota_mas_cercana = min(alicuotas_validas, key=lambda x: abs(x - alicuota_calculada))

        return alicuota_mas_cercana

    def _procesar_resumen_iva(self, facturas: List[Dict]) -> Dict:
        """Procesar resumen IVA por alícuotas"""
        resumen = {
            'iva_ventas': Decimal('0.00'),
            'iva_compras': Decimal('0.00'),
            'ventas_por_alicuota': {},
            'compras_por_alicuota': {}
        }

        for factura in facturas:
            iva_factura = Decimal(str(factura['iva']))

            # Clasificar como venta o compra basado en tipo de factura
            es_venta = factura['tipo'] in ['A', 'B', 'C']  # Facturas emitidas

            if es_venta:
                resumen['iva_ventas'] += iva_factura

                # Agrupar por alícuota
                for item in factura['items']:
                    alicuota = item['alicuota_iva']
                    if alicuota not in resumen['ventas_por_alicuota']:
                        resumen['ventas_por_alicuota'][alicuota] = {
                            'neto': Decimal('0.00'),
                            'iva': Decimal('0.00')
                        }

                    item_neto = Decimal(str(item['subtotal']))
                    item_iva = item_neto * Decimal(str(alicuota)) / Decimal('100')

                    resumen['ventas_por_alicuota'][alicuota]['neto'] += item_neto
                    resumen['ventas_por_alicuota'][alicuota]['iva'] += item_iva
            else:
                resumen['iva_compras'] += iva_factura

                # Similar para compras
                for item in factura['items']:
                    alicuota = item['alicuota_iva']
                    if alicuota not in resumen['compras_por_alicuota']:
                        resumen['compras_por_alicuota'][alicuota] = {
                            'neto': Decimal('0.00'),
                            'iva': Decimal('0.00')
                        }

                    item_neto = Decimal(str(item['subtotal']))
                    item_iva = item_neto * Decimal(str(alicuota)) / Decimal('100')

                    resumen['compras_por_alicuota'][alicuota]['neto'] += item_neto
                    resumen['compras_por_alicuota'][alicuota]['iva'] += item_iva

        return resumen

    def _procesar_detalle_compras(self, facturas: List[Dict]) -> List[Dict]:
        """Procesar detalle de compras para archivo AFIP"""
        detalle = []

        for factura in facturas:
            # Solo facturas de compra (recibidas)
            if factura['tipo'] not in ['A', 'B', 'C']:
                continue

            registro = {
                'fecha': factura['fecha_emision'].strftime('%d/%m/%Y'),
                'tipo_comprobante': self._get_codigo_tipo_comprobante(factura['tipo']),
                'punto_venta': f"{factura['punto_venta']:04d}",
                'numero_comprobante': f"{int(factura['numero']):08d}",
                'despacho_importacion': '',
                'codigo_documento_vendedor': '80',  # CUIT
                'numero_identificacion_vendedor': factura['cuit_emisor'],
                'apellido_nombre_vendedor': factura['nombre_emisor'][:30],
                'importe_total': f"{factura['total']:.2f}".replace('.', ','),
                'importe_total_conceptos_no_integran_precio_neto': '0,00',
                'importe_operaciones_exentas': '0,00',
                'importe_percepciones_iva': '0,00',
                'importe_percepciones_otros_tributos': '0,00',
                'importe_percepciones_ingresos_brutos': '0,00',
                'importe_percepciones_municipales': '0,00',
                'importe_impuestos_internos': '0,00',
                'codigo_moneda': 'PES',
                'tipo_cambio': '1,000000',
                'cantidad_alicuotas_iva': str(len([i for i in factura['items'] if i['alicuota_iva'] > 0])),
                'codigo_operacion': 'N'  # Normal
            }

            detalle.append(registro)

        return detalle

    def _procesar_detalle_ventas(self, facturas: List[Dict]) -> List[Dict]:
        """Procesar detalle de ventas para archivo AFIP"""
        detalle = []

        for factura in facturas:
            # Solo facturas de venta (emitidas)
            if factura['tipo'] not in ['A', 'B', 'C']:
                continue

            registro = {
                'fecha': factura['fecha_emision'].strftime('%d/%m/%Y'),
                'tipo_comprobante': self._get_codigo_tipo_comprobante(factura['tipo']),
                'punto_venta': f"{factura['punto_venta']:04d}",
                'numero_comprobante_desde': f"{int(factura['numero']):08d}",
                'numero_comprobante_hasta': f"{int(factura['numero']):08d}",
                'codigo_documento_comprador': '80',  # CUIT
                'numero_identificacion_comprador': factura.get('cuit_comprador', '0'),
                'apellido_nombre_comprador': factura.get('nombre_comprador', 'CONSUMIDOR FINAL')[:30],
                'importe_total': f"{factura['total']:.2f}".replace('.', ','),
                'importe_total_conceptos_no_integran_precio_neto': '0,00',
                'importe_operaciones_exentas': '0,00',
                'importe_percepciones_iva': '0,00',
                'importe_percepciones_otros_tributos': '0,00',
                'codigo_moneda': 'PES',
                'tipo_cambio': '1,000000',
                'cantidad_alicuotas_iva': str(len([i for i in factura['items'] if i['alicuota_iva'] > 0])),
                'codigo_operacion': 'N'  # Normal
            }

            detalle.append(registro)

        return detalle

    def _get_codigo_tipo_comprobante(self, tipo: str) -> str:
        """Obtener código AFIP para tipo de comprobante"""
        codigos = {
            'A': '001',  # Factura A
            'B': '006',  # Factura B
            'C': '011'   # Factura C
        }
        return codigos.get(tipo, '006')

    def _generar_archivos_afip(self, año: int, mes: int, resumen: Dict, 
                              compras: List[Dict], ventas: List[Dict]) -> List[str]:
        """Generar archivos en formato AFIP"""
        archivos = []

        try:
            # Archivo resumen IVA
            resumen_file = self.output_dir / f"iva_resumen_{año}_{mes:02d}.txt"
            with open(resumen_file, 'w', encoding='utf-8') as f:
                f.write("RESUMEN MENSUAL IVA\n")
                f.write(f"Período: {mes:02d}/{año}\n")
                f.write(f"IVA Débito Fiscal (Ventas): ${resumen['iva_ventas']:.2f}\n")
                f.write(f"IVA Crédito Fiscal (Compras): ${resumen['iva_compras']:.2f}\n")
                f.write(f"Saldo Técnico: ${resumen['iva_ventas'] - resumen['iva_compras']:.2f}\n")

            archivos.append(str(resumen_file))

            # Archivo detalle compras (formato AFIP)
            if compras:
                compras_file = self.output_dir / f"compras_{año}_{mes:02d}.txt"
                fieldnames = list(compras[0].keys())

                with open(compras_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='|')
                    writer.writerows(compras)

                archivos.append(str(compras_file))

            # Archivo detalle ventas (formato AFIP)
            if ventas:
                ventas_file = self.output_dir / f"ventas_{año}_{mes:02d}.txt"
                fieldnames = list(ventas[0].keys())

                with open(ventas_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='|')
                    writer.writerows(ventas)

                archivos.append(str(ventas_file))

            # Archivo Excel para revisión manual
            excel_file = self.output_dir / f"reporte_iva_{año}_{mes:02d}.xlsx"
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Hoja resumen
                df_resumen = pd.DataFrame([{
                    'Concepto': 'IVA Ventas',
                    'Importe': float(resumen['iva_ventas'])
                }, {
                    'Concepto': 'IVA Compras', 
                    'Importe': float(resumen['iva_compras'])
                }, {
                    'Concepto': 'Saldo Técnico',
                    'Importe': float(resumen['iva_ventas'] - resumen['iva_compras'])
                }])
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)

                # Hoja compras
                if compras:
                    df_compras = pd.DataFrame(compras)
                    df_compras.to_excel(writer, sheet_name='Compras', index=False)

                # Hoja ventas
                if ventas:
                    df_ventas = pd.DataFrame(ventas)
                    df_ventas.to_excel(writer, sheet_name='Ventas', index=False)

            archivos.append(str(excel_file))

            return archivos

        except Exception as e:
            logger.error(f"Error generando archivos AFIP: {e}")
            return archivos

    def _validar_reporte(self, resumen: Dict) -> List[str]:
        """Validar consistencia del reporte"""
        validaciones = []

        # Validar que hay datos
        if resumen['iva_ventas'] == 0 and resumen['iva_compras'] == 0:
            validaciones.append("ADVERTENCIA: No se encontraron operaciones con IVA")

        # Validar alícuotas válidas
        alicuotas_validas = [0.0, 10.5, 21.0, 27.0]
        for alicuota in resumen['ventas_por_alicuota'].keys():
            if alicuota not in alicuotas_validas:
                validaciones.append(f"ADVERTENCIA: Alícuota IVA no estándar: {alicuota}%")

        # Validar importes positivos
        if resumen['iva_ventas'] < 0:
            validaciones.append("ERROR: IVA ventas negativo")

        if resumen['iva_compras'] < 0:
            validaciones.append("ERROR: IVA compras negativo")

        return validaciones

    def generar_declaracion_jurada(self, año: int, mes: int) -> Dict:
        """Generar estructura para declaración jurada IVA"""
        reporte = self.generar_reporte_mensual(año, mes, "")

        # Estructura simplificada DDJJ
        ddjj = {
            'periodo': f"{año}{mes:02d}",
            'debito_fiscal': float(reporte['iva_debito_fiscal']),
            'credito_fiscal': float(reporte['iva_credito_fiscal']),
            'saldo_tecnico': float(reporte['saldo_tecnico']),
            'saldo_libre_disponibilidad': 0.0,
            'reintegros': 0.0,
            'retenciones_sufridas': 0.0,
            'percepciones_realizadas': 0.0,
            'saldo_resultante': float(reporte['saldo_tecnico']),
            'observaciones': reporte.get('validaciones', [])
        }

        # Guardar DDJJ
        ddjj_file = self.output_dir / f"ddjj_iva_{año}_{mes:02d}.json"
        with open(ddjj_file, 'w', encoding='utf-8') as f:
            json.dump(ddjj, f, indent=2, ensure_ascii=False)

        return ddjj

# Función de utilidad para testing
def generar_reporte_ejemplo():
    """Generar reporte de ejemplo para testing"""
    from shared.database import get_db_session

    with get_db_session() as db:
        reporter = ReporteIVA(db)

        # Generar reporte del mes actual
        ahora = datetime.now()
        reporte = reporter.generar_reporte_mensual(
            ahora.year, 
            ahora.month, 
            "20123456789"
        )

        print(f"✅ Reporte IVA generado: {reporte['total_facturas']} facturas")
        print(f"IVA Débito: ${reporte['iva_debito_fiscal']:.2f}")
        print(f"IVA Crédito: ${reporte['iva_credito_fiscal']:.2f}")
        print(f"Archivos: {len(reporte['archivos_generados'])}")

        return reporte

if __name__ == "__main__":
    # Test del generador
    reporte = generar_reporte_ejemplo()
