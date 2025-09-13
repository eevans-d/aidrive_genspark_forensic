
"""
Cliente AFIP WSFE (Web Services Facturación Electrónica)
Validación y generación de CAE/CAI para facturación electrónica argentina.
"""

import os
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


@dataclass
class AFIPCredentials:
    """
    Credenciales AFIP para autenticación y acceso a servicios WSFE.
    """
    cuit: str
    certificate_path: str
    private_key_path: str
    environment: str = "testing"  # "testing" o "production"

    @property
    def base_url(self) -> str:
        """
        Retorna la URL base según el entorno.
        """
        if self.environment == "production":
            return "https://servicios1.afip.gov.ar/wsfev1"
        return "https://wswhomo.afip.gov.ar/wsfev1"


@dataclass
class FacturaElectronica:
    """
    Estructura de factura electrónica AFIP.
    """
    tipo_cbte: int  # 1=A, 6=B, 11=C
    punto_venta: int
    numero: int
    fecha_cbte: str  # YYYYMMDD
    tipo_doc: int = 80  # 80=CUIT
    nro_doc: str = ""
    importe_total: float = 0.0
    importe_neto: float = 0.0
    importe_iva: float = 0.0
    importe_trib: float = 0.0
    importe_op_ex: float = 0.0
    fecha_venc_pago: str = ""
    moneda_id: str = "PES"
    moneda_ctz: float = 1.0

class AFIPWSFEClient:
    """
    Cliente AFIP WSFE para facturación electrónica.
    Métodos para autenticación, generación y validación de CAE/CAI.
    """

    def __init__(self, credentials: AFIPCredentials):
        self.credentials = credentials
        self.token = None
        self.sign = None
        self.token_expiry = None

    def _load_certificate(self) -> str:
        """
        Carga el certificado AFIP desde archivo.
        """
        try:
            with open(self.credentials.certificate_path, 'r') as f:
                cert_content = f.read()
            return cert_content
        except FileNotFoundError:
            logger.error(f"Certificado AFIP no encontrado: {self.credentials.certificate_path}")
            raise

    def _load_private_key(self) -> str:
        """Cargar clave privada desde archivo"""
        try:
            with open(self.credentials.private_key_path, 'r') as f:
                key_content = f.read()
            return key_content
        except FileNotFoundError:
            logger.error(f"Clave privada no encontrada: {self.credentials.private_key_path}")
            raise

    def _create_tra(self) -> str:
        """Crear Ticket de Requerimiento de Acceso (TRA)"""
        now = datetime.now()
        from_time = now.strftime('%Y-%m-%dT%H:%M:%S')
        to_time = (now + timedelta(hours=23)).strftime('%Y-%m-%dT%H:%M:%S')
        unique_id = int(now.timestamp())

        tra_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <loginTicketRequest version="1.0">
            <header>
                <source>{unique_id}</source>
                <destination>CN=wsfe,O=AFIP,C=AR,SERIALNUMBER=CUIT 33693450239</destination>
                <uniqueId>{unique_id}</uniqueId>
                <generationTime>{from_time}</generationTime>
                <expirationTime>{to_time}</expirationTime>
            </header>
            <service>wsfe</service>
        </loginTicketRequest>"""

        return tra_xml.strip()

    def _sign_tra(self, tra_xml: str) -> str:
        """Firmar TRA con certificado AFIP"""
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization

            # Cargar clave privada
            private_key_pem = self._load_private_key()
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), 
                password=None
            )

            # Firmar TRA
            signature = private_key.sign(
                tra_xml.encode(),
                padding.PKCS1v15(),
                hashes.SHA1()
            )

            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Error firmando TRA: {e}")
            raise

    def _authenticate(self) -> bool:
        """Autenticar con AFIP y obtener token/sign"""
        try:
            # Crear y firmar TRA
            tra_xml = self._create_tra()
            signature = self._sign_tra(tra_xml)

            # Preparar request WSAA
            certificate = self._load_certificate()
            wsaa_url = self.credentials.base_url.replace('wsfev1', 'wsaa')

            login_cms = f"""-----BEGIN PKCS7-----
{signature}
-----END PKCS7-----"""

            request_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
                <soap:Body>
                    <loginCms>
                        <in0>{base64.b64encode(tra_xml.encode()).decode()}</in0>
                        <in1>{base64.b64encode(login_cms.encode()).decode()}</in1>
                    </loginCms>
                </soap:Body>
            </soap:Envelope>"""

            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': ''
            }

            response = requests.post(f"{wsaa_url}/ws/services/LoginCms", 
                                   data=request_xml, 
                                   headers=headers, 
                                   timeout=30)

            if response.status_code == 200:
                # Parsear respuesta y extraer token/sign
                root = ET.fromstring(response.content)
                credentials_elem = root.find('.//{http://wsaa.view.sua.dvadac.desein.afip.gov}credentials')

                if credentials_elem is not None:
                    self.token = credentials_elem.find('token').text
                    self.sign = credentials_elem.find('sign').text
                    self.token_expiry = datetime.now() + timedelta(hours=12)
                    logger.info("Autenticación AFIP exitosa")
                    return True

            logger.error(f"Error autenticación AFIP: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error en autenticación AFIP: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Asegurar que tenemos token válido"""
        if (self.token is None or 
            self.token_expiry is None or 
            datetime.now() >= self.token_expiry):
            return self._authenticate()
        return True

    def validar_cae(self, tipo_cbte: int, punto_venta: int, numero_cbte: int, cae: str) -> Dict:
        """Validar CAE existente"""
        if not self._ensure_authenticated():
            raise Exception("No se pudo autenticar con AFIP")

        request_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Body>
                <FECAEConsultar>
                    <Auth>
                        <Token>{self.token}</Token>
                        <Sign>{self.sign}</Sign>
                        <Cuit>{self.credentials.cuit}</Cuit>
                    </Auth>
                    <FeCAEConsReq>
                        <CbteTipo>{tipo_cbte}</CbteTipo>
                        <PtoVta>{punto_venta}</PtoVta>
                        <CbteNro>{numero_cbte}</CbteNro>
                    </FeCAEConsReq>
                </FECAEConsultar>
            </soap:Body>
        </soap:Envelope>"""

        try:
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': ''
            }

            response = requests.post(f"{self.credentials.base_url}/ws/services/wsfev1", 
                                   data=request_xml, 
                                   headers=headers, 
                                   timeout=30)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                result_elem = root.find('.//ResultGet')

                if result_elem is not None:
                    return {
                        'valido': True,
                        'cae': result_elem.find('CAE').text,
                        'fecha_vencimiento': result_elem.find('CAEFchVto').text,
                        'estado': 'APROBADO'
                    }

            return {'valido': False, 'error': 'CAE no encontrado'}

        except Exception as e:
            logger.error(f"Error validando CAE: {e}")
            return {'valido': False, 'error': str(e)}

    def generar_cae(self, factura: FacturaElectronica) -> Dict:
        """Generar CAE para factura electrónica"""
        if not self._ensure_authenticated():
            raise Exception("No se pudo autenticar con AFIP")

        # Obtener último número de comprobante
        ultimo_cbte = self.obtener_ultimo_comprobante(factura.tipo_cbte, factura.punto_venta)
        factura.numero = ultimo_cbte + 1

        request_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Body>
                <FECAESolicitar>
                    <Auth>
                        <Token>{self.token}</Token>
                        <Sign>{self.sign}</Sign>
                        <Cuit>{self.credentials.cuit}</Cuit>
                    </Auth>
                    <FeCAEReq>
                        <FeCabReq>
                            <CantReg>1</CantReg>
                            <PtoVta>{factura.punto_venta}</PtoVta>
                            <CbteTipo>{factura.tipo_cbte}</CbteTipo>
                        </FeCabReq>
                        <FeDetReq>
                            <FECAEDetRequest>
                                <Concepto>1</Concepto>
                                <DocTipo>{factura.tipo_doc}</DocTipo>
                                <DocNro>{factura.nro_doc}</DocNro>
                                <CbteDesde>{factura.numero}</CbteDesde>
                                <CbteHasta>{factura.numero}</CbteHasta>
                                <CbteFch>{factura.fecha_cbte}</CbteFch>
                                <ImpTotal>{factura.importe_total:.2f}</ImpTotal>
                                <ImpTotConc>0.00</ImpTotConc>
                                <ImpNeto>{factura.importe_neto:.2f}</ImpNeto>
                                <ImpOpEx>{factura.importe_op_ex:.2f}</ImpOpEx>
                                <ImpTrib>{factura.importe_trib:.2f}</ImpTrib>
                                <ImpIVA>{factura.importe_iva:.2f}</ImpIVA>
                                <FchServDesde></FchServDesde>
                                <FchServHasta></FchServHasta>
                                <FchVtoPago>{factura.fecha_venc_pago}</FchVtoPago>
                                <MonId>{factura.moneda_id}</MonId>
                                <MonCotiz>{factura.moneda_ctz}</MonCotiz>
                            </FECAEDetRequest>
                        </FeDetReq>
                    </FeCAEReq>
                </FECAESolicitar>
            </soap:Body>
        </soap:Envelope>"""

        try:
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': ''
            }

            response = requests.post(f"{self.credentials.base_url}/ws/services/wsfev1", 
                                   data=request_xml, 
                                   headers=headers, 
                                   timeout=30)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                fe_det_resp = root.find('.//FECAEDetResponse')

                if fe_det_resp is not None:
                    resultado = fe_det_resp.find('Resultado').text

                    if resultado == 'A':  # Aprobado
                        return {
                            'exitoso': True,
                            'cae': fe_det_resp.find('CAE').text,
                            'fecha_vencimiento': fe_det_resp.find('CAEFchVto').text,
                            'numero_comprobante': factura.numero,
                            'resultado': 'APROBADO'
                        }
                    else:
                        # Rechazado, obtener errores
                        observaciones = []
                        for obs in fe_det_resp.findall('.//Obs'):
                            observaciones.append({
                                'codigo': obs.find('Code').text,
                                'mensaje': obs.find('Msg').text
                            })

                        return {
                            'exitoso': False,
                            'resultado': 'RECHAZADO',
                            'observaciones': observaciones
                        }

            return {'exitoso': False, 'error': 'Error en comunicación con AFIP'}

        except Exception as e:
            logger.error(f"Error generando CAE: {e}")
            return {'exitoso': False, 'error': str(e)}

    def obtener_ultimo_comprobante(self, tipo_cbte: int, punto_venta: int) -> int:
        """Obtener último número de comprobante autorizado"""
        if not self._ensure_authenticated():
            raise Exception("No se pudo autenticar con AFIP")

        request_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Body>
                <FECompUltimoAutorizado>
                    <Auth>
                        <Token>{self.token}</Token>
                        <Sign>{self.sign}</Sign>
                        <Cuit>{self.credentials.cuit}</Cuit>
                    </Auth>
                    <PtoVta>{punto_venta}</PtoVta>
                    <CbteTipo>{tipo_cbte}</CbteTipo>
                </FECompUltimoAutorizado>
            </soap:Body>
        </soap:Envelope>"""

        try:
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': ''
            }

            response = requests.post(f"{self.credentials.base_url}/ws/services/wsfev1", 
                                   data=request_xml, 
                                   headers=headers, 
                                   timeout=30)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                cbte_nro = root.find('.//CbteNro')

                if cbte_nro is not None:
                    return int(cbte_nro.text)

            return 0

        except Exception as e:
            logger.error(f"Error obteniendo último comprobante: {e}")
            return 0

    def obtener_puntos_venta(self) -> List[Dict]:
        """Obtener puntos de venta habilitados"""
        if not self._ensure_authenticated():
            raise Exception("No se pudo autenticar con AFIP")

        request_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
            <soap:Body>
                <FEParamGetPtosVenta>
                    <Auth>
                        <Token>{self.token}</Token>
                        <Sign>{self.sign}</Sign>
                        <Cuit>{self.credentials.cuit}</Cuit>
                    </Auth>
                </FEParamGetPtosVenta>
            </soap:Body>
        </soap:Envelope>"""

        try:
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': ''
            }

            response = requests.post(f"{self.credentials.base_url}/ws/services/wsfev1", 
                                   data=request_xml, 
                                   headers=headers, 
                                   timeout=30)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                puntos_venta = []

                for pto_venta in root.findall('.//PtoVenta'):
                    puntos_venta.append({
                        'numero': int(pto_venta.find('Nro').text),
                        'bloqueado': pto_venta.find('Bloqueado').text == 'S',
                        'fecha_baja': pto_venta.find('FchBaja').text if pto_venta.find('FchBaja') is not None else None
                    })

                return puntos_venta

            return []

        except Exception as e:
            logger.error(f"Error obteniendo puntos de venta: {e}")
            return []

# Funciones de utilidad para testing
def crear_factura_ejemplo() -> FacturaElectronica:
    """Crear factura de ejemplo para testing"""
    return FacturaElectronica(
        tipo_cbte=6,  # Factura B
        punto_venta=1,
        numero=0,  # Se asigna automáticamente
        fecha_cbte=datetime.now().strftime('%Y%m%d'),
        tipo_doc=80,  # CUIT
        nro_doc="20123456789",
        importe_total=1210.0,
        importe_neto=1000.0,
        importe_iva=210.0,
        importe_trib=0.0,
        importe_op_ex=0.0,
        fecha_venc_pago=datetime.now().strftime('%Y%m%d'),
        moneda_id="PES",
        moneda_ctz=1.0
    )

if __name__ == "__main__":
    # Ejemplo de uso (requiere certificados AFIP válidos)
    credentials = AFIPCredentials(
        cuit="20123456789",
        certificate_path="path/to/certificate.crt",
        private_key_path="path/to/private.key",
        environment="testing"
    )

    client = AFIPWSFEClient(credentials)

    # Validar CAE existente
    resultado = client.validar_cae(6, 1, 123, "12345678901234")
    print(f"Validación CAE: {resultado}")

    # Obtener puntos de venta
    puntos_venta = client.obtener_puntos_venta()
    print(f"Puntos de venta: {puntos_venta}")
