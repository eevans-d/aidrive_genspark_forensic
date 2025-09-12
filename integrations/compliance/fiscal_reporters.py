"""
Reportes de compliance fiscal argentino
Incluye IVA, SIFERE, retención de datos y auditoría
"""
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
from enum import Enum
import json
import zipfile
import hashlib
import os
import logging
from decimal import Decimal, ROUND_HALF_UP

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TipoComprobante(Enum):
    FACTURA_A = "01"
    NOTA_DEBITO_A = "02"
    NOTA_CREDITO_A = "03"
    RECIBO_A = "04"
    FACTURA_B = "06"
    NOTA_DEBITO_B = "07"
    NOTA_CREDITO_B = "08"
    RECIBO_B = "09"
    FACTURA_C = "11"
    NOTA_DEBITO_C = "12"
    NOTA_CREDITO_C = "13"
    RECIBO_C = "15"

class AlicuotaIVA(Enum):
    EXENTO = "1"
    NO_GRAVADO = "2"
    GRAVADO_0 = "3"
    GRAVADO_10_5 = "4"
    GRAVADO_21 = "5"
    GRAVADO_27 = "6"

@dataclass
class ComprobanteVenta:
    """Comprobante de venta para reportes fiscales"""
    fecha_comprobante: date
    tipo_comprobante: str
    punto_venta: int
    numero_comprobante: int
    numero_comprobante_hasta: int
    codigo_documento_comprador: str
    numero_documento_comprador: str
    denominacion_comprador: str
    importe_total_operacion: Decimal
    importe_total_conceptos: Decimal
    importe_percepciones: Decimal
    importe_iibb: Decimal
    importe_percepcion_municipal: Decimal
    importe_impuestos_internos: Decimal
    codigo_moneda: str
    tipo_cambio: Decimal
    cantidad_alicuotas_iva: int
    codigo_operacion: str
    otros_tributos: Decimal
    fecha_vencimiento_pago: date

    # IVA por alícuota
    neto_gravado_5: Decimal = Decimal('0.00')
    iva_5: Decimal = Decimal('0.00')
    neto_gravado_10_5: Decimal = Decimal('0.00')
    iva_10_5: Decimal = Decimal('0.00')
    neto_gravado_21: Decimal = Decimal('0.00')
    iva_21: Decimal = Decimal('0.00')
    neto_gravado_27: Decimal = Decimal('0.00')
    iva_27: Decimal = Decimal('0.00')

@dataclass
class ComprobanteCompra:
    """Comprobante de compra para reportes fiscales"""
    fecha_comprobante: date
    tipo_comprobante: str
    punto_venta: int
    numero_comprobante: int
    despacho_importacion: str
    codigo_documento_vendedor: str
    numero_documento_vendedor: str
    denominacion_vendedor: str
    importe_total_operacion: Decimal
    importe_total_conceptos: Decimal
    importe_operaciones_exentas: Decimal
    importe_percepciones: Decimal
    importe_iibb: Decimal
    importe_percepcion_municipal: Decimal
    importe_impuestos_internos: Decimal
    codigo_moneda: str
    tipo_cambio: Decimal
    cantidad_alicuotas_iva: int
    codigo_operacion: str

    # IVA por alícuota
    neto_gravado_5: Decimal = Decimal('0.00')
    iva_5: Decimal = Decimal('0.00')
    neto_gravado_10_5: Decimal = Decimal('0.00')
    iva_10_5: Decimal = Decimal('0.00')
    neto_gravado_21: Decimal = Decimal('0.00')
    iva_21: Decimal = Decimal('0.00')
    neto_gravado_27: Decimal = Decimal('0.00')
    iva_27: Decimal = Decimal('0.00')

class FiscalComplianceReporter:
    """Generador de reportes de compliance fiscal argentino"""

    def __init__(self, cuit_empresa: str, razon_social: str, data_source):
        self.cuit_empresa = cuit_empresa
        self.razon_social = razon_social
        self.data_source = data_source  # Conexión a BD o fuente de datos

        # Directorio para archivos de compliance
        self.compliance_dir = "compliance_reports"
        os.makedirs(self.compliance_dir, exist_ok=True)

        # Configuración de retención (5 años según normativa)
        self.retention_years = 5

    def generar_libro_iva_ventas(
        self, 
        periodo_desde: date, 
        periodo_hasta: date,
        formato: str = "txt"
    ) -> Dict[str, Any]:
        """
        Genera Libro IVA Ventas según RG AFIP

        Args:
            periodo_desde: Fecha inicio del período
            periodo_hasta: Fecha fin del período
            formato: 'txt', 'excel' o 'xml'

        Returns:
            Dict con información del archivo generado
        """
        try:
            logger.info(f"Generando Libro IVA Ventas {periodo_desde} - {periodo_hasta}")

            # 1. Obtener comprobantes de venta del período
            comprobantes = self._obtener_comprobantes_venta(periodo_desde, periodo_hasta)

            # 2. Procesar y validar datos
            comprobantes_procesados = self._procesar_comprobantes_venta(comprobantes)

            # 3. Generar archivo según formato
            if formato == "txt":
                archivo_path = self._generar_iva_ventas_txt(comprobantes_procesados, periodo_desde, periodo_hasta)
            elif formato == "excel":
                archivo_path = self._generar_iva_ventas_excel(comprobantes_procesados, periodo_desde, periodo_hasta)
            elif formato == "xml":
                archivo_path = self._generar_iva_ventas_xml(comprobantes_procesados, periodo_desde, periodo_hasta)
            else:
                raise ValueError(f"Formato no soportado: {formato}")

            # 4. Calcular totales y estadísticas
            totales = self._calcular_totales_ventas(comprobantes_procesados)

            # 5. Generar hash de integridad
            hash_archivo = self._calcular_hash_archivo(archivo_path)

            resultado = {
                "success": True,
                "archivo_path": archivo_path,
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "total_comprobantes": len(comprobantes_procesados),
                "totales": totales,
                "hash_integridad": hash_archivo,
                "formato": formato,
                "generado_en": datetime.now().isoformat()
            }

            # 6. Registrar en log de auditoría
            self._registrar_auditoria("LIBRO_IVA_VENTAS", resultado)

            logger.info(f"Libro IVA Ventas generado exitosamente: {archivo_path}")
            return resultado

        except Exception as e:
            logger.error(f"Error generando Libro IVA Ventas: {e}")
            return {
                "success": False,
                "error": str(e),
                "archivo_path": None
            }

    def generar_libro_iva_compras(
        self, 
        periodo_desde: date, 
        periodo_hasta: date,
        formato: str = "txt"
    ) -> Dict[str, Any]:
        """Genera Libro IVA Compras según RG AFIP"""
        try:
            logger.info(f"Generando Libro IVA Compras {periodo_desde} - {periodo_hasta}")

            # 1. Obtener comprobantes de compra del período
            comprobantes = self._obtener_comprobantes_compra(periodo_desde, periodo_hasta)

            # 2. Procesar y validar datos
            comprobantes_procesados = self._procesar_comprobantes_compra(comprobantes)

            # 3. Generar archivo según formato
            if formato == "txt":
                archivo_path = self._generar_iva_compras_txt(comprobantes_procesados, periodo_desde, periodo_hasta)
            elif formato == "excel":
                archivo_path = self._generar_iva_compras_excel(comprobantes_procesados, periodo_desde, periodo_hasta)
            elif formato == "xml":
                archivo_path = self._generar_iva_compras_xml(comprobantes_procesados, periodo_desde, periodo_hasta)
            else:
                raise ValueError(f"Formato no soportado: {formato}")

            # 4. Calcular totales
            totales = self._calcular_totales_compras(comprobantes_procesados)

            # 5. Hash de integridad
            hash_archivo = self._calcular_hash_archivo(archivo_path)

            resultado = {
                "success": True,
                "archivo_path": archivo_path,
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "total_comprobantes": len(comprobantes_procesados),
                "totales": totales,
                "hash_integridad": hash_archivo,
                "formato": formato,
                "generado_en": datetime.now().isoformat()
            }

            self._registrar_auditoria("LIBRO_IVA_COMPRAS", resultado)

            logger.info(f"Libro IVA Compras generado exitosamente: {archivo_path}")
            return resultado

        except Exception as e:
            logger.error(f"Error generando Libro IVA Compras: {e}")
            return {
                "success": False,
                "error": str(e),
                "archivo_path": None
            }

    def generar_sifere_exportacion(
        self, 
        periodo_desde: date, 
        periodo_hasta: date
    ) -> Dict[str, Any]:
        """
        Genera archivo SIFERE para exportación a AFIP
        Sistema de Intercambio de Facturas Electrónicas Registrales
        """
        try:
            logger.info(f"Generando exportación SIFERE {periodo_desde} - {periodo_hasta}")

            # 1. Obtener facturas electrónicas del período
            facturas_electronicas = self._obtener_facturas_electronicas(periodo_desde, periodo_hasta)

            # 2. Convertir a formato SIFERE
            registros_sifere = self._convertir_a_sifere(facturas_electronicas)

            # 3. Generar XML según especificación AFIP
            archivo_xml = self._generar_sifere_xml(registros_sifere, periodo_desde, periodo_hasta)

            # 4. Validar XML contra XSD de AFIP
            validacion = self._validar_sifere_xml(archivo_xml)

            # 5. Comprimir archivo
            archivo_zip = self._comprimir_sifere(archivo_xml)

            resultado = {
                "success": True,
                "archivo_xml": archivo_xml,
                "archivo_zip": archivo_zip,
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "total_facturas": len(facturas_electronicas),
                "validacion_xsd": validacion,
                "hash_integridad": self._calcular_hash_archivo(archivo_zip),
                "generado_en": datetime.now().isoformat()
            }

            self._registrar_auditoria("SIFERE_EXPORTACION", resultado)

            logger.info(f"Exportación SIFERE generada: {archivo_zip}")
            return resultado

        except Exception as e:
            logger.error(f"Error generando SIFERE: {e}")
            return {
                "success": False,
                "error": str(e),
                "archivo_xml": None,
                "archivo_zip": None
            }

    def generar_retencion_datos_5_anos(self, ano_base: int) -> Dict[str, Any]:
        """
        Genera archivo de retención de datos fiscales por 5 años
        Según normativa argentina de conservación de registros
        """
        try:
            logger.info(f"Generando archivo de retención para año {ano_base}")

            fecha_desde = date(ano_base, 1, 1)
            fecha_hasta = date(ano_base, 12, 31)

            # 1. Recopilar todos los datos fiscales del año
            datos_fiscales = {
                "facturas_emitidas": self._obtener_facturas_emitidas(fecha_desde, fecha_hasta),
                "facturas_recibidas": self._obtener_facturas_recibidas(fecha_desde, fecha_hasta),
                "libros_iva": self._obtener_libros_iva_ano(ano_base),
                "retenciones_percibidas": self._obtener_retenciones(fecha_desde, fecha_hasta),
                "pagos_realizados": self._obtener_pagos(fecha_desde, fecha_hasta),
                "inventarios": self._obtener_inventarios_ano(ano_base)
            }

            # 2. Estructurar datos en formato estándar
            datos_estructurados = self._estructurar_datos_retencion(datos_fiscales, ano_base)

            # 3. Generar archivos de respaldo
            archivo_json = self._generar_respaldo_json(datos_estructurados, ano_base)
            archivo_excel = self._generar_respaldo_excel(datos_estructurados, ano_base)

            # 4. Crear package comprimido con verificación de integridad
            archivo_retencion = self._crear_package_retencion(
                [archivo_json, archivo_excel], 
                ano_base
            )

            # 5. Calcular métricas de retención
            metricas = self._calcular_metricas_retencion(datos_estructurados)

            resultado = {
                "success": True,
                "ano_base": ano_base,
                "archivo_retencion": archivo_retencion,
                "archivos_incluidos": [archivo_json, archivo_excel],
                "metricas": metricas,
                "fecha_vencimiento": date(ano_base + self.retention_years, 12, 31).isoformat(),
                "hash_integridad": self._calcular_hash_archivo(archivo_retencion),
                "generado_en": datetime.now().isoformat()
            }

            self._registrar_auditoria("RETENCION_5_ANOS", resultado)

            logger.info(f"Archivo de retención generado: {archivo_retencion}")
            return resultado

        except Exception as e:
            logger.error(f"Error generando archivo de retención: {e}")
            return {
                "success": False,
                "error": str(e),
                "archivo_retencion": None
            }

    def generar_auditoria_fiscal(
        self, 
        periodo_desde: date, 
        periodo_hasta: date
    ) -> Dict[str, Any]:
        """Genera reporte completo de auditoría fiscal"""
        try:
            logger.info(f"Generando auditoría fiscal {periodo_desde} - {periodo_hasta}")

            # 1. Recopilar datos para auditoría
            datos_auditoria = {
                "resumen_ventas": self._generar_resumen_ventas(periodo_desde, periodo_hasta),
                "resumen_compras": self._generar_resumen_compras(periodo_desde, periodo_hasta),
                "conciliacion_iva": self._generar_conciliacion_iva(periodo_desde, periodo_hasta),
                "validaciones": self._ejecutar_validaciones_fiscales(periodo_desde, periodo_hasta),
                "inconsistencias": self._detectar_inconsistencias(periodo_desde, periodo_hasta)
            }

            # 2. Generar reporte en múltiples formatos
            reporte_pdf = self._generar_auditoria_pdf(datos_auditoria, periodo_desde, periodo_hasta)
            reporte_excel = self._generar_auditoria_excel(datos_auditoria, periodo_desde, periodo_hasta)

            # 3. Crear dashboard interactivo
            dashboard_html = self._generar_dashboard_auditoria(datos_auditoria, periodo_desde, periodo_hasta)

            resultado = {
                "success": True,
                "periodo_desde": periodo_desde.isoformat(),
                "periodo_hasta": periodo_hasta.isoformat(),
                "reporte_pdf": reporte_pdf,
                "reporte_excel": reporte_excel,
                "dashboard_html": dashboard_html,
                "datos_auditoria": datos_auditoria,
                "generado_en": datetime.now().isoformat()
            }

            self._registrar_auditoria("AUDITORIA_FISCAL", resultado)

            logger.info("Auditoría fiscal generada exitosamente")
            return resultado

        except Exception as e:
            logger.error(f"Error generando auditoría fiscal: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # Métodos privados de implementación

    def _obtener_comprobantes_venta(self, desde: date, hasta: date) -> List[Dict]:
        """Obtiene comprobantes de venta del período"""
        # Mock implementation - reemplazar con query real
        return [
            {
                "fecha": date(2024, 1, 15),
                "tipo_comprobante": "06",  # Factura B
                "punto_venta": 1,
                "numero": 123,
                "cliente_documento": "20123456789",
                "cliente_nombre": "Cliente Test SA",
                "importe_total": Decimal("1210.00"),
                "neto_21": Decimal("1000.00"),
                "iva_21": Decimal("210.00")
            }
        ]

    def _obtener_comprobantes_compra(self, desde: date, hasta: date) -> List[Dict]:
        """Obtiene comprobantes de compra del período"""
        # Mock implementation
        return [
            {
                "fecha": date(2024, 1, 10),
                "tipo_comprobante": "01",  # Factura A
                "punto_venta": 5,
                "numero": 456,
                "proveedor_documento": "30987654321",
                "proveedor_nombre": "Proveedor Test SRL",
                "importe_total": Decimal("605.00"),
                "neto_21": Decimal("500.00"),
                "iva_21": Decimal("105.00")
            }
        ]

    def _procesar_comprobantes_venta(self, comprobantes: List[Dict]) -> List[ComprobanteVenta]:
        """Procesa y valida comprobantes de venta"""
        procesados = []

        for comp in comprobantes:
            try:
                comprobante = ComprobanteVenta(
                    fecha_comprobante=comp["fecha"],
                    tipo_comprobante=comp["tipo_comprobante"],
                    punto_venta=comp["punto_venta"],
                    numero_comprobante=comp["numero"],
                    numero_comprobante_hasta=comp["numero"],  # Mismo número para comprobante individual
                    codigo_documento_comprador="80",  # CUIT
                    numero_documento_comprador=comp["cliente_documento"],
                    denominacion_comprador=comp["cliente_nombre"],
                    importe_total_operacion=comp["importe_total"],
                    importe_total_conceptos=Decimal('0.00'),
                    importe_percepciones=Decimal('0.00'),
                    importe_iibb=Decimal('0.00'),
                    importe_percepcion_municipal=Decimal('0.00'),
                    importe_impuestos_internos=Decimal('0.00'),
                    codigo_moneda="PES",
                    tipo_cambio=Decimal('1.00'),
                    cantidad_alicuotas_iva=1,
                    codigo_operacion="0",  # Contado
                    otros_tributos=Decimal('0.00'),
                    fecha_vencimiento_pago=comp["fecha"],
                    neto_gravado_21=comp.get("neto_21", Decimal('0.00')),
                    iva_21=comp.get("iva_21", Decimal('0.00'))
                )
                procesados.append(comprobante)

            except Exception as e:
                logger.error(f"Error procesando comprobante {comp}: {e}")
                continue

        return procesados

    def _procesar_comprobantes_compra(self, comprobantes: List[Dict]) -> List[ComprobanteCompra]:
        """Procesa y valida comprobantes de compra"""
        procesados = []

        for comp in comprobantes:
            try:
                comprobante = ComprobanteCompra(
                    fecha_comprobante=comp["fecha"],
                    tipo_comprobante=comp["tipo_comprobante"],
                    punto_venta=comp["punto_venta"],
                    numero_comprobante=comp["numero"],
                    despacho_importacion="",
                    codigo_documento_vendedor="80",
                    numero_documento_vendedor=comp["proveedor_documento"],
                    denominacion_vendedor=comp["proveedor_nombre"],
                    importe_total_operacion=comp["importe_total"],
                    importe_total_conceptos=Decimal('0.00'),
                    importe_operaciones_exentas=Decimal('0.00'),
                    importe_percepciones=Decimal('0.00'),
                    importe_iibb=Decimal('0.00'),
                    importe_percepcion_municipal=Decimal('0.00'),
                    importe_impuestos_internos=Decimal('0.00'),
                    codigo_moneda="PES",
                    tipo_cambio=Decimal('1.00'),
                    cantidad_alicuotas_iva=1,
                    codigo_operacion="0",
                    neto_gravado_21=comp.get("neto_21", Decimal('0.00')),
                    iva_21=comp.get("iva_21", Decimal('0.00'))
                )
                procesados.append(comprobante)

            except Exception as e:
                logger.error(f"Error procesando comprobante compra {comp}: {e}")
                continue

        return procesados

    def _generar_iva_ventas_txt(self, comprobantes: List[ComprobanteVenta], desde: date, hasta: date) -> str:
        """Genera archivo TXT del Libro IVA Ventas"""
        filename = f"iva_ventas_{desde.strftime('%Y%m')}_{hasta.strftime('%Y%m')}.txt"
        filepath = os.path.join(self.compliance_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            for comp in comprobantes:
                # Formato según RG AFIP para Libro IVA Ventas
                linea = "|".join([
                    comp.fecha_comprobante.strftime("%d/%m/%Y"),
                    comp.tipo_comprobante.zfill(3),
                    str(comp.punto_venta).zfill(5),
                    str(comp.numero_comprobante).zfill(20),
                    str(comp.numero_comprobante_hasta).zfill(20),
                    comp.codigo_documento_comprador.zfill(2),
                    comp.numero_documento_comprador.zfill(20),
                    comp.denominacion_comprador[:30],
                    f"{comp.importe_total_operacion:.2f}".replace('.', ','),
                    f"{comp.importe_total_conceptos:.2f}".replace('.', ','),
                    f"{comp.importe_percepciones:.2f}".replace('.', ','),
                    f"{comp.importe_iibb:.2f}".replace('.', ','),
                    f"{comp.importe_percepcion_municipal:.2f}".replace('.', ','),
                    f"{comp.importe_impuestos_internos:.2f}".replace('.', ','),
                    comp.codigo_moneda,
                    f"{comp.tipo_cambio:.6f}".replace('.', ','),
                    str(comp.cantidad_alicuotas_iva),
                    comp.codigo_operacion,
                    f"{comp.otros_tributos:.2f}".replace('.', ','),
                    comp.fecha_vencimiento_pago.strftime("%d/%m/%Y") if comp.fecha_vencimiento_pago else ""
                ])
                f.write(linea + "\n")

        return filepath

    def _calcular_totales_ventas(self, comprobantes: List[ComprobanteVenta]) -> Dict[str, Any]:
        """Calcula totales del Libro IVA Ventas"""
        total_operaciones = sum(comp.importe_total_operacion for comp in comprobantes)
        total_iva_21 = sum(comp.iva_21 for comp in comprobantes)
        total_neto_21 = sum(comp.neto_gravado_21 for comp in comprobantes)

        return {
            "cantidad_comprobantes": len(comprobantes),
            "total_operaciones": float(total_operaciones),
            "total_iva_21": float(total_iva_21),
            "total_neto_21": float(total_neto_21),
            "promedio_operacion": float(total_operaciones / len(comprobantes)) if comprobantes else 0
        }

    def _calcular_totales_compras(self, comprobantes: List[ComprobanteCompra]) -> Dict[str, Any]:
        """Calcula totales del Libro IVA Compras"""
        total_operaciones = sum(comp.importe_total_operacion for comp in comprobantes)
        total_iva_21 = sum(comp.iva_21 for comp in comprobantes)
        total_neto_21 = sum(comp.neto_gravado_21 for comp in comprobantes)

        return {
            "cantidad_comprobantes": len(comprobantes),
            "total_operaciones": float(total_operaciones),
            "total_iva_21": float(total_iva_21),
            "total_neto_21": float(total_neto_21)
        }

    def _calcular_hash_archivo(self, filepath: str) -> str:
        """Calcula hash SHA256 para integridad del archivo"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _registrar_auditoria(self, operacion: str, resultado: Dict[str, Any]):
        """Registra operación en log de auditoría"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operacion": operacion,
            "usuario": "sistema",  # Obtener usuario real
            "resultado": resultado.get("success", False),
            "archivo_generado": resultado.get("archivo_path") or resultado.get("archivo_retencion"),
            "hash_integridad": resultado.get("hash_integridad"),
            "error": resultado.get("error")
        }

        # Guardar en archivo de auditoría
        audit_file = os.path.join(self.compliance_dir, "auditoria.jsonl")
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")

    # Mock implementations para métodos restantes
    def _obtener_facturas_electronicas(self, desde: date, hasta: date) -> List[Dict]:
        return []

    def _convertir_a_sifere(self, facturas: List[Dict]) -> List[Dict]:
        return []

    def _generar_sifere_xml(self, registros: List[Dict], desde: date, hasta: date) -> str:
        return f"{self.compliance_dir}/sifere_{desde.strftime('%Y%m')}.xml"

    def _validar_sifere_xml(self, archivo: str) -> Dict[str, Any]:
        return {"valido": True, "errores": []}

    def _comprimir_sifere(self, archivo_xml: str) -> str:
        zip_path = archivo_xml.replace('.xml', '.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(archivo_xml, os.path.basename(archivo_xml))
        return zip_path

    # Implementaciones adicionales para retención de datos...
    def _obtener_facturas_emitidas(self, desde: date, hasta: date) -> List[Dict]:
        return []

    def _obtener_facturas_recibidas(self, desde: date, hasta: date) -> List[Dict]:
        return []

    def _obtener_libros_iva_ano(self, ano: int) -> Dict:
        return {}

    def _obtener_retenciones(self, desde: date, hasta: date) -> List[Dict]:
        return []

    def _obtener_pagos(self, desde: date, hasta: date) -> List[Dict]:
        return []

    def _obtener_inventarios_ano(self, ano: int) -> List[Dict]:
        return []

    def _estructurar_datos_retencion(self, datos: Dict, ano: int) -> Dict:
        return {
            "ano": ano,
            "empresa": {
                "cuit": self.cuit_empresa,
                "razon_social": self.razon_social
            },
            "datos_fiscales": datos,
            "generado_en": datetime.now().isoformat()
        }

    def _generar_respaldo_json(self, datos: Dict, ano: int) -> str:
        filepath = os.path.join(self.compliance_dir, f"retencion_{ano}_datos.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, default=str)
        return filepath

    def _generar_respaldo_excel(self, datos: Dict, ano: int) -> str:
        filepath = os.path.join(self.compliance_dir, f"retencion_{ano}_resumen.xlsx")
        # Mock: crear archivo Excel básico
        with open(filepath, 'w') as f:
            f.write("Mock Excel file")
        return filepath

    def _crear_package_retencion(self, archivos: List[str], ano: int) -> str:
        zip_path = os.path.join(self.compliance_dir, f"retencion_fiscal_{ano}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for archivo in archivos:
                zipf.write(archivo, os.path.basename(archivo))
        return zip_path

    def _calcular_metricas_retencion(self, datos: Dict) -> Dict:
        return {
            "total_archivos": 2,
            "size_total_mb": 1.5,
            "periodo_cobertura": "año completo"
        }


# Utilidades adicionales
class ComplianceUtils:
    """Utilidades para compliance fiscal"""

    @staticmethod
    def validar_cuit_formato(cuit: str) -> bool:
        """Valida formato de CUIT"""
        if not cuit or len(cuit) != 11:
            return False
        return cuit.isdigit()

    @staticmethod
    def calcular_digito_verificador_cuit(cuit_base: str) -> int:
        """Calcula dígito verificador de CUIT"""
        if len(cuit_base) != 10:
            raise ValueError("CUIT base debe tener 10 dígitos")

        multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(d) * m for d, m in zip(cuit_base, multiplicadores))
        resto = suma % 11

        if resto == 0:
            return 0
        elif resto == 1:
            return 9
        else:
            return 11 - resto

    @staticmethod
    def formatear_importe_afip(importe: Decimal) -> str:
        """Formatea importe según especificación AFIP"""
        return f"{importe:.2f}".replace('.', ',')


# Ejemplo de uso
if __name__ == "__main__":
    # Configuración de ejemplo
    reporter = FiscalComplianceReporter(
        cuit_empresa="20123456789",
        razon_social="Mi Empresa SRL",
        data_source=None  # Conexión a BD
    )

    # Generar Libro IVA Ventas
    periodo_desde = date(2024, 1, 1)
    periodo_hasta = date(2024, 1, 31)

    resultado_ventas = reporter.generar_libro_iva_ventas(
        periodo_desde, 
        periodo_hasta, 
        formato="txt"
    )

    if resultado_ventas["success"]:
        print(f"Libro IVA Ventas generado: {resultado_ventas['archivo_path']}")
        print(f"Total comprobantes: {resultado_ventas['total_comprobantes']}")
        print(f"Totales: {resultado_ventas['totales']}")
    else:
        print(f"Error: {resultado_ventas['error']}")
