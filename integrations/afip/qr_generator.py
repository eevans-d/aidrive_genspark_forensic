"""
Generador de códigos QR para facturas electrónicas AFIP
Cumple con RG 4290 - Especificaciones técnicas para QR en comprobantes
"""
import qrcode
import base64
from io import BytesIO
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass

@dataclass
class QRFacturaData:
    """Datos para generar QR según RG 4290"""
    ver: int = 1  # Versión del formato
    fecha: str = ""  # YYYY-MM-DD
    cuit: str = ""  # CUIT emisor
    ptoVta: int = 0  # Punto de venta
    tipoCmp: int = 0  # Tipo de comprobante
    nroCmp: int = 0  # Número de comprobante
    importe: float = 0.0  # Importe total
    moneda: str = "PES"  # Moneda
    ctz: float = 1.0  # Cotización
    tipoDocRec: int = 0  # Tipo documento receptor
    nroDocRec: str = ""  # Número documento receptor
    tipoCodAut: str = "E"  # Tipo código autorización
    codAut: str = ""  # CAE/CAEA

class AFIPQRGenerator:
    """Generador de códigos QR para facturas AFIP según RG 4290"""

    # Tipos de comprobante según AFIP
    TIPOS_COMPROBANTE = {
        1: "Factura A",
        2: "Nota de Débito A", 
        3: "Nota de Crédito A",
        4: "Recibo A",
        5: "Nota de Venta al Contado A",
        6: "Factura B",
        7: "Nota de Débito B",
        8: "Nota de Crédito B",
        9: "Recibo B",
        10: "Nota de Venta al Contado B",
        11: "Factura C",
        12: "Nota de Débito C",
        13: "Nota de Crédito C",
        15: "Recibo C"
    }

    # Tipos de documento según AFIP
    TIPOS_DOCUMENTO = {
        80: "CUIT",
        86: "CUIL", 
        87: "CDI",
        89: "LE",
        90: "LC",
        91: "CI Extranjera",
        92: "en trámite",
        93: "Acta nacimiento",
        95: "CI Bs. As. RNP",
        96: "DNI",
        99: "Sin identificar/Consumidor Final",
        30: "Certificado de Migración"
    }

    def __init__(self):
        self.base_url = "https://www.afip.gob.ar/fe/qr/"

    def generar_qr_factura(
        self,
        cuit_emisor: str,
        punto_venta: int,
        tipo_comprobante: int,
        numero_comprobante: int,
        fecha_emision: datetime,
        importe_total: float,
        cae: str,
        cuit_receptor: str = "",
        tipo_doc_receptor: int = 99,
        moneda: str = "PES",
        cotizacion: float = 1.0
    ) -> Dict[str, Any]:
        """
        Genera código QR para factura electrónica según RG 4290

        Args:
            cuit_emisor: CUIT del emisor
            punto_venta: Punto de venta
            tipo_comprobante: Tipo de comprobante AFIP
            numero_comprobante: Número del comprobante
            fecha_emision: Fecha de emisión
            importe_total: Importe total del comprobante
            cae: Código de autorización electrónica
            cuit_receptor: CUIT del receptor (opcional)
            tipo_doc_receptor: Tipo documento receptor
            moneda: Código de moneda (PES, USD, EUR)
            cotizacion: Cotización de la moneda

        Returns:
            Dict con URL, datos QR y imagen base64
        """
        try:
            # Validar datos obligatorios
            if not all([cuit_emisor, punto_venta, tipo_comprobante, 
                       numero_comprobante, fecha_emision, cae]):
                raise ValueError("Faltan datos obligatorios para generar QR")

            # Formatear fecha
            fecha_str = fecha_emision.strftime("%Y-%m-%d")

            # Crear estructura de datos según RG 4290
            qr_data = QRFacturaData(
                ver=1,
                fecha=fecha_str,
                cuit=self._limpiar_cuit(cuit_emisor),
                ptoVta=punto_venta,
                tipoCmp=tipo_comprobante,
                nroCmp=numero_comprobante,
                importe=round(importe_total, 2),
                moneda=moneda,
                ctz=cotizacion,
                tipoDocRec=tipo_doc_receptor,
                nroDocRec=self._limpiar_cuit(cuit_receptor) if cuit_receptor else "",
                tipoCodAut="E",  # CAE
                codAut=cae
            )

            # Generar URL según especificación AFIP
            url_qr = self._generar_url_qr(qr_data)

            # Generar código QR
            qr_image = self._crear_qr_image(url_qr)

            # Convertir a base64
            qr_base64 = self._image_to_base64(qr_image)

            # Generar hash de verificación
            hash_verificacion = self._generar_hash_verificacion(qr_data)

            return {
                "success": True,
                "url_qr": url_qr,
                "qr_base64": qr_base64,
                "hash_verificacion": hash_verificacion,
                "datos": {
                    "cuit_emisor": cuit_emisor,
                    "punto_venta": punto_venta,
                    "tipo_comprobante": tipo_comprobante,
                    "numero_comprobante": numero_comprobante,
                    "fecha": fecha_str,
                    "importe": importe_total,
                    "cae": cae
                },
                "metadatos": {
                    "tipo_comprobante_desc": self.TIPOS_COMPROBANTE.get(tipo_comprobante, "Desconocido"),
                    "tipo_documento_desc": self.TIPOS_DOCUMENTO.get(tipo_doc_receptor, "Desconocido"),
                    "moneda": moneda,
                    "generado": datetime.now().isoformat()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error generando QR: {str(e)}",
                "url_qr": None,
                "qr_base64": None
            }

    def _generar_url_qr(self, data: QRFacturaData) -> str:
        """Genera URL según formato RG 4290"""
        params = []

        # Agregar parámetros según especificación
        params.append(f"ver={data.ver}")
        params.append(f"fecha={data.fecha}")
        params.append(f"cuit={data.cuit}")
        params.append(f"ptoVta={data.ptoVta}")
        params.append(f"tipoCmp={data.tipoCmp}")
        params.append(f"nroCmp={data.nroCmp}")
        params.append(f"importe={data.importe}")
        params.append(f"moneda={data.moneda}")
        params.append(f"ctz={data.ctz}")

        if data.nroDocRec:
            params.append(f"tipoDocRec={data.tipoDocRec}")
            params.append(f"nroDocRec={data.nroDocRec}")

        params.append(f"tipoCodAut={data.tipoCodAut}")
        params.append(f"codAut={data.codAut}")

        return f"{self.base_url}?{'&'.join(params)}"

    def _crear_qr_image(self, url: str, size: int = 200) -> Any:
        """Crea imagen QR con configuración optimizada"""
        qr = qrcode.QRCode(
            version=1,  # Tamaño automático
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # 7% de corrección
            box_size=10,
            border=4,
        )

        qr.add_data(url)
        qr.make(fit=True)

        # Crear imagen con colores estándar
        img = qr.make_image(fill_color="black", back_color="white")

        # Redimensionar si es necesario
        if size != 200:
            img = img.resize((size, size))

        return img

    def _image_to_base64(self, img) -> str:
        """Convierte imagen PIL a base64"""
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    def _limpiar_cuit(self, cuit: str) -> str:
        """Limpia y formatea CUIT"""
        if not cuit:
            return ""
        # Remover guiones y espacios
        return ''.join(filter(str.isdigit, cuit))

    def _generar_hash_verificacion(self, data: QRFacturaData) -> str:
        """Genera hash de verificación para validar integridad"""
        # Crear string con datos críticos
        verificacion_string = f"{data.cuit}{data.ptoVta}{data.tipoCmp}{data.nroCmp}{data.fecha}{data.importe}{data.codAut}"

        # Generar hash SHA256
        return hashlib.sha256(verificacion_string.encode('utf-8')).hexdigest()[:16]

    def validar_qr_data(self, qr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida los datos de un QR generado"""
        try:
            required_fields = ['cuit_emisor', 'punto_venta', 'tipo_comprobante', 
                             'numero_comprobante', 'fecha', 'importe', 'cae']

            # Verificar campos obligatorios
            missing_fields = [field for field in required_fields 
                            if field not in qr_data.get('datos', {})]

            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Campos faltantes: {', '.join(missing_fields)}"
                }

            # Validar CUIT
            cuit = qr_data['datos']['cuit_emisor']
            if not self._validar_cuit_format(cuit):
                return {
                    "valid": False,
                    "error": "Formato de CUIT inválido"
                }

            # Validar tipo de comprobante
            tipo_comp = qr_data['datos']['tipo_comprobante']
            if tipo_comp not in self.TIPOS_COMPROBANTE:
                return {
                    "valid": False,
                    "error": f"Tipo de comprobante inválido: {tipo_comp}"
                }

            # Validar CAE
            cae = qr_data['datos']['cae']
            if not cae or len(cae) != 14:
                return {
                    "valid": False,
                    "error": "CAE debe tener 14 dígitos"
                }

            return {
                "valid": True,
                "message": "QR válido según especificaciones RG 4290"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Error en validación: {str(e)}"
            }

    def _validar_cuit_format(self, cuit: str) -> bool:
        """Valida formato básico de CUIT"""
        cuit_limpio = self._limpiar_cuit(cuit)
        return len(cuit_limpio) == 11 and cuit_limpio.isdigit()

    def generar_qr_lote(self, facturas: list) -> Dict[str, Any]:
        """Genera QR para múltiples facturas"""
        resultados = []
        errores = []

        for i, factura in enumerate(facturas):
            try:
                resultado = self.generar_qr_factura(**factura)
                if resultado['success']:
                    resultados.append({
                        'indice': i,
                        'factura': factura,
                        'qr': resultado
                    })
                else:
                    errores.append({
                        'indice': i,
                        'factura': factura,
                        'error': resultado['error']
                    })
            except Exception as e:
                errores.append({
                    'indice': i,
                    'factura': factura,
                    'error': f"Error procesando factura: {str(e)}"
                })

        return {
            'total_procesadas': len(facturas),
            'exitosas': len(resultados),
            'con_errores': len(errores),
            'resultados': resultados,
            'errores': errores
        }


# Utilidades adicionales para QR
class QRUtils:
    """Utilidades adicionales para manejo de QR AFIP"""

    @staticmethod
    def extraer_datos_url_qr(url_qr: str) -> Dict[str, Any]:
        """Extrae datos de una URL de QR AFIP"""
        try:
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(url_qr)
            params = parse_qs(parsed_url.query)

            # Extraer parámetros
            datos = {}
            for key, value in params.items():
                if value:
                    datos[key] = value[0]

            return {
                "success": True,
                "datos": datos,
                "url_base": f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error extrayendo datos: {str(e)}"
            }

    @staticmethod
    def generar_qr_simple(texto: str, size: int = 200) -> str:
        """Genera QR simple para cualquier texto"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(texto)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            if size != 200:
                img = img.resize((size, size))

            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            return f"Error: {str(e)}"


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de generación de QR para factura
    generator = AFIPQRGenerator()

    # Datos de ejemplo
    resultado = generator.generar_qr_factura(
        cuit_emisor="20123456789",
        punto_venta=1,
        tipo_comprobante=6,  # Factura B
        numero_comprobante=123,
        fecha_emision=datetime.now(),
        importe_total=1500.50,
        cae="12345678901234",
        cuit_receptor="27987654321",
        tipo_doc_receptor=80  # CUIT
    )

    if resultado['success']:
        print("QR generado exitosamente")
        print(f"URL: {resultado['url_qr']}")
        print(f"Hash: {resultado['hash_verificacion']}")
    else:
        print(f"Error: {resultado['error']}")
