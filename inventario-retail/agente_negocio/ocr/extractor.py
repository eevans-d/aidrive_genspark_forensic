"""
AgenteNegocio - OCR Data Extractor
Extracción de datos específicos usando patrones regex AFIP
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InvoiceData:
    """Datos estructurados de una factura"""
    # Identificación
    tipo_comprobante: Optional[str] = None
    numero_factura: Optional[str] = None
    punto_venta: Optional[str] = None
    codigo_autorizacion: Optional[str] = None

    # Fechas
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None

    # Emisor
    razon_social_emisor: Optional[str] = None
    cuit_emisor: Optional[str] = None
    condicion_iva_emisor: Optional[str] = None
    domicilio_emisor: Optional[str] = None

    # Receptor
    razon_social_receptor: Optional[str] = None
    cuit_receptor: Optional[str] = None
    condicion_iva_receptor: Optional[str] = None
    domicilio_receptor: Optional[str] = None

    # Montos
    subtotal: Optional[Decimal] = None
    iva_total: Optional[Decimal] = None
    impuestos_internos: Optional[Decimal] = None
    percepciones: Optional[Decimal] = None
    total: Optional[Decimal] = None

    # Items/Productos
    items: List[Dict[str, Any]] = field(default_factory=list)

    # Información adicional
    observaciones: Optional[str] = None
    codigo_barras: Optional[str] = None
    qr_code: Optional[str] = None

    # Metadata de extracción
    confidence_score: float = 0.0
    extracted_fields: List[str] = field(default_factory=list)
    raw_text: str = ""

class AFIPDataExtractor:
    """
    Extractor de datos específicos para facturas AFIP
    Utiliza patrones regex optimizados para documentos argentinos
    """

    def __init__(self):
        """Inicializa el extractor con patrones AFIP"""
        self.patterns = self._initialize_patterns()
        self.confidence_weights = self._initialize_confidence_weights()
        logger.info("AFIPDataExtractor inicializado con patrones AFIP")

    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Inicializa todos los patrones regex para campos AFIP"""
        return {
            # Fechas
            'fecha_emision': [
                r'(?:fecha|emisión|emisión):\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
                r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
                r'(?:fecha)[\s:]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
            ],

            'fecha_vencimiento': [
                r'(?:venc|vencimiento|vto)[\s:]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
                r'(?:válida hasta|vigente hasta)[\s:]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})'
            ],

            # CUIT/CUIL
            'cuit_emisor': [
                r'(?:cuit|cuil)[\s:]*(\d{2}[\-\s]?\d{8}[\-\s]?\d{1})',
                r'(\d{2}[\-\s]?\d{8}[\-\s]?\d{1})',
                r'(?:cuit|cuil)[\s:]*(\d{11})'
            ],

            'cuit_receptor': [
                r'(?:cliente|comprador).*?(?:cuit|cuil)[\s:]*(\d{2}[\-\s]?\d{8}[\-\s]?\d{1})',
                r'(?:destinatario).*?(\d{2}[\-\s]?\d{8}[\-\s]?\d{1})'
            ],

            # Números de factura
            'numero_factura': [
                r'(?:n[°º]|nro|número|factura)[\s:]*(\d{4}[\-\s]?\d{8})',
                r'(?:comprobante)[\s:]*(\d{4}[\-\s]?\d{8})',
                r'(\d{4}[\-\s]?\d{8})',
                r'(?:fc|fact)[\s:]*(\d+)'
            ],

            'punto_venta': [
                r'(?:pto|punto)[\s:]*(?:venta|vta)[\s:]*(\d{4})',
                r'(?:pv|p\.v\.)[\s:]*(\d{4})',
                r'(\d{4})[\-\s]?\d{8}'  # Del número completo
            ],

            # Códigos de autorización
            'codigo_autorizacion': [
                r'(?:cae|cod\.?\s*aut|autorización)[\s:]*(\d+)',
                r'(?:comprobante autorizado)[\s:]*(\d+)',
                r'cae[\s:]*(\d{14})'
            ],

            # Tipos de comprobante
            'tipo_comprobante': [
                r'(factura\s*[abc])',
                r'(nota\s*(?:de\s*)?(?:crédito|débito))',
                r'(remito|recibo|ticket)',
                r'(?:tipo|cod)[\s:]*([abc])',
                r'(factura|fc|fact)'
            ],

            # Razones sociales
            'razon_social_emisor': [
                r'(?:razón social|empresa|denominación)[\s:]*([^
]{3,80})',
                r'^([A-ZÁÉÍÓÚ][A-Za-zÁÉÍÓÚáéíóúÑñ\s&\.\-]{5,80})',
                r'(?:emisor|proveedor)[\s:]*([^
]{5,80})'
            ],

            'razon_social_receptor': [
                r'(?:cliente|comprador|destinatario)[\s:]*([^
]{5,80})',
                r'(?:señor|sra?)[\s:]*([^
]{5,80})',
                r'(?:a:?\s*)([A-ZÁÉÍÓÚ][A-Za-zÁÉÍÓÚáéíóúÑñ\s&\.\-]{5,80})'
            ],

            # Condiciones IVA
            'condicion_iva_emisor': [
                r'(responsable\s*inscripto|resp\.\s*inscripto|ri)',
                r'(monotributo|monotributista|mt)',
                r'(exento|excento)',
                r'(no\s*responsable|consumidor\s*final)'
            ],

            'condicion_iva_receptor': [
                r'(?:cliente|comprador).*?(responsable\s*inscripto|monotributo|exento|consumidor\s*final)',
                r'iva[\s:]*([^
]{5,30})'
            ],

            # Montos y valores
            'subtotal': [
                r'(?:subtotal|sub[\-\s]?total)[\s:$]*([\d,.]+)',
                r'(?:neto|base\s*imponible)[\s:$]*([\d,.]+)',
                r'(?:importe\s*neto)[\s:$]*([\d,.]+)'
            ],

            'iva_total': [
                r'(?:iva|i\.v\.a\.)[\s:$]*([\d,.]+)',
                r'(?:impuesto\s*al\s*valor\s*agregado)[\s:$]*([\d,.]+)',
                r'(?:iva\s*21%)[\s:$]*([\d,.]+)'
            ],

            'total': [
                r'(?:total|importe\s*total)[\s:$]*([\d,.]+)',
                r'(?:total\s*general|total\s*a\s*pagar)[\s:$]*([\d,.]+)',
                r'(?:monto\s*total)[\s:$]*([\d,.]+)',
                r'\$[\s]*([\d,.]+)(?=\s*$)'  # Último monto con $
            ],

            'impuestos_internos': [
                r'(?:imp\.\s*int|impuestos\s*internos)[\s:$]*([\d,.]+)',
                r'(?:iibb|ing\.\s*brutos)[\s:$]*([\d,.]+)'
            ],

            'percepciones': [
                r'(?:percepciones?|perc\.)[\s:$]*([\d,.]+)',
                r'(?:retenciones?)[\s:$]*([\d,.]+)'
            ],

            # Domicilios
            'domicilio_emisor': [
                r'(?:domicilio|dirección|dir\.)[\s:]*([^
]{10,100})',
                r'(?:domicilio\s*fiscal)[\s:]*([^
]{10,100})'
            ],

            'domicilio_receptor': [
                r'(?:cliente|comprador).*?(?:domicilio|dirección)[\s:]*([^
]{10,100})',
                r'(?:entregar\s*en|enviar\s*a)[\s:]*([^
]{10,100})'
            ],

            # Códigos especiales
            'codigo_barras': [
                r'(?:cod\.?\s*barras?|código\s*de\s*barras?)[\s:]*(\d{8,})',
                r'(\d{13})',  # EAN-13
                r'(\d{12})'   # UPC-A
            ],

            'qr_code': [
                r'(?:qr|codigo\s*qr)[\s:]*([A-Za-z0-9+/=]{20,})'
            ],

            # Items de productos
            'item_codigo': [
                r'(?:cod|código|art|artículo)[\s:]*(\w+)',
                r'^(\d+)\s+[A-Za-z]'  # Código seguido de descripción
            ],

            'item_descripcion': [
                r'(?:descripción|detalle|producto)[\s:]*([^
]{5,100})',
                r'^\d+\s+([A-Za-zÁÉÍÓÚáéíóúÑñ\s&\.\-]{5,100})'
            ],

            'item_cantidad': [
                r'(?:cant|cantidad|qty)[\s:]*([\d,.]+)',
                r'([\d,.]+)(?=\s*(?:kg|un|lt|mt))'
            ],

            'item_precio_unitario': [
                r'(?:precio|p\.u\.|unitario)[\s:$]*([\d,.]+)',
                r'(?:valor\s*unit)[\s:$]*([\d,.]+)'
            ],

            'item_importe': [
                r'(?:importe|total\s*item)[\s:$]*([\d,.]+)',
                r'([\d,.]+)(?=\s*$)'  # Último número de la línea
            ]
        }

    def _initialize_confidence_weights(self) -> Dict[str, float]:
        """Inicializa pesos de confianza por tipo de campo"""
        return {
            'cuit_emisor': 1.0,
            'numero_factura': 1.0,
            'fecha_emision': 0.9,
            'total': 0.8,
            'razon_social_emisor': 0.7,
            'subtotal': 0.7,
            'iva_total': 0.6,
            'tipo_comprobante': 0.6,
            'punto_venta': 0.5,
            'default': 0.4
        }

    def extract_from_text(self, text: str, confidence_threshold: float = 0.3) -> InvoiceData:
        """
        Extrae datos estructurados del texto OCR

        Args:
            text: Texto extraído por OCR
            confidence_threshold: Umbral mínimo de confianza

        Returns:
            InvoiceData: Datos estructurados de la factura
        """
        logger.info(f"Iniciando extracción de datos - {len(text)} caracteres")

        # Preprocesar texto
        clean_text = self._preprocess_text(text)

        # Crear objeto de datos
        invoice_data = InvoiceData(raw_text=text)

        # Extraer cada tipo de campo
        extracted_count = 0
        total_confidence = 0.0

        for field_name, patterns in self.patterns.items():
            if field_name.startswith('item_'):
                continue  # Los items se procesan por separado

            value, confidence = self._extract_field(clean_text, field_name, patterns)

            if value and confidence >= confidence_threshold:
                # Procesar valor según el tipo de campo
                processed_value = self._process_field_value(field_name, value)

                if processed_value is not None:
                    setattr(invoice_data, field_name, processed_value)
                    invoice_data.extracted_fields.append(field_name)
                    extracted_count += 1
                    total_confidence += confidence

                    logger.debug(f"Campo extraído: {field_name} = {processed_value} (conf: {confidence:.2f})")

        # Extraer items de productos
        items = self._extract_items(clean_text)
        if items:
            invoice_data.items = items
            extracted_count += len(items)
            total_confidence += 0.5 * len(items)  # Peso menor para items

        # Calcular confianza global
        if extracted_count > 0:
            invoice_data.confidence_score = total_confidence / extracted_count

        # Validar y mejorar datos
        invoice_data = self._validate_and_enhance_data(invoice_data)

        logger.info(f"Extracción completada - {extracted_count} campos, confianza: {invoice_data.confidence_score:.2f}")

        return invoice_data

    def _preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para mejorar la extracción"""
        # Normalizar espacios y saltos de línea
        clean_text = re.sub(r'\s+', ' ', text)
        clean_text = re.sub(r'\n+', '\n', clean_text)

        # Corregir caracteres comunes del OCR
        replacements = {
            'º': '°',
            'Nº': 'N°',
            '|': 'I',
            'l': '1',  # En contextos numéricos
            'O': '0',  # En contextos numéricos
            'S': '5',  # En contextos numéricos específicos
        }

        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)

        # Normalizar montos (convertir comas por puntos decimales)
        clean_text = re.sub(r'(\d+),(\d{2})(?!\d)', r'\1.\2', clean_text)

        return clean_text

    def _extract_field(self, text: str, field_name: str, patterns: List[str]) -> Tuple[Optional[str], float]:
        """Extrae un campo específico usando múltiples patrones"""
        best_match = None
        best_confidence = 0.0

        for i, pattern in enumerate(patterns):
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

                if matches:
                    # Tomar la primera coincidencia válida
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # Si el patrón tiene grupos

                        match = match.strip()
                        if self._is_valid_match(field_name, match):
                            # Calcular confianza basada en posición del patrón y contexto
                            pattern_confidence = 1.0 - (i * 0.2)  # Primer patrón = mayor confianza
                            context_confidence = self._calculate_context_confidence(text, match, field_name)
                            total_confidence = (pattern_confidence + context_confidence) / 2

                            if total_confidence > best_confidence:
                                best_match = match
                                best_confidence = total_confidence

            except re.error as e:
                logger.warning(f"Error en patrón regex para {field_name}: {e}")
                continue

        return best_match, best_confidence

    def _is_valid_match(self, field_name: str, match: str) -> bool:
        """Valida si una coincidencia es válida para el tipo de campo"""
        if not match or len(match.strip()) == 0:
            return False

        # Validaciones específicas por tipo de campo
        if 'cuit' in field_name:
            # CUIT debe tener 11 dígitos
            digits = re.sub(r'[^\d]', '', match)
            return len(digits) == 11

        elif 'fecha' in field_name:
            # Fecha debe tener formato válido
            return self._is_valid_date(match)

        elif 'numero_factura' in field_name:
            # Número de factura debe tener al menos 4 dígitos
            digits = re.sub(r'[^\d]', '', match)
            return len(digits) >= 4

        elif any(x in field_name for x in ['subtotal', 'total', 'iva']):
            # Montos deben ser números válidos
            return self._is_valid_amount(match)

        elif 'razon_social' in field_name:
            # Razón social debe tener longitud mínima
            return len(match.strip()) >= 5

        return True

    def _is_valid_date(self, date_str: str) -> bool:
        """Valida si una cadena representa una fecha válida"""
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}'
        ]

        for pattern in date_patterns:
            if re.match(pattern, date_str):
                try:
                    # Intentar parsear la fecha
                    parts = re.split(r'[/-]', date_str)
                    if len(parts) == 3:
                        day, month, year = map(int, parts)
                        if year < 100:
                            year += 2000 if year < 50 else 1900
                        datetime(year, month, day)
                        return True
                except (ValueError, OverflowError):
                    continue

        return False

    def _is_valid_amount(self, amount_str: str) -> bool:
        """Valida si una cadena representa un monto válido"""
        try:
            # Limpiar el string (quitar símbolos de moneda, espacios, etc.)
            clean_amount = re.sub(r'[^\d,.]', '', amount_str)
            clean_amount = clean_amount.replace(',', '.')

            # Debe tener al menos un dígito
            if not re.search(r'\d', clean_amount):
                return False

            # Intentar convertir a decimal
            float(clean_amount)
            return True
        except (ValueError, AttributeError):
            return False

    def _calculate_context_confidence(self, text: str, match: str, field_name: str) -> float:
        """Calcula confianza basada en el contexto de la coincidencia"""
        # Buscar palabras clave cercanas al match
        match_pos = text.find(match)
        if match_pos == -1:
            return 0.5

        # Texto de contexto (50 caracteres antes y después)
        start = max(0, match_pos - 50)
        end = min(len(text), match_pos + len(match) + 50)
        context = text[start:end].lower()

        # Palabras clave por tipo de campo
        context_keywords = {
            'cuit': ['cuit', 'cuil', 'tributario', 'fiscal'],
            'fecha_emision': ['fecha', 'emisión', 'expedición'],
            'fecha_vencimiento': ['vencimiento', 'válida', 'vto', 'vigente'],
            'numero_factura': ['factura', 'número', 'comprobante', 'nro'],
            'total': ['total', 'importe', 'pagar', 'suma'],
            'subtotal': ['subtotal', 'neto', 'base'],
            'iva_total': ['iva', 'impuesto', 'agregado'],
            'razon_social': ['razón', 'social', 'empresa', 'denominación']
        }

        keywords = context_keywords.get(field_name, [])
        found_keywords = sum(1 for keyword in keywords if keyword in context)

        # Confianza basada en palabras clave encontradas
        if keywords:
            return min(1.0, found_keywords / len(keywords) + 0.3)

        return 0.5

    def _process_field_value(self, field_name: str, value: str) -> Any:
        """Procesa el valor del campo según su tipo"""
        try:
            if 'fecha' in field_name:
                return self._parse_date(value)

            elif any(x in field_name for x in ['subtotal', 'total', 'iva', 'impuesto', 'percepciones']):
                return self._parse_amount(value)

            elif 'cuit' in field_name:
                # Normalizar CUIT
                digits = re.sub(r'[^\d]', '', value)
                if len(digits) == 11:
                    return f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
                return digits

            elif field_name in ['razon_social_emisor', 'razon_social_receptor', 'domicilio_emisor', 'domicilio_receptor']:
                # Limpiar y capitalizar
                clean_value = value.strip().title()
                return clean_value if len(clean_value) >= 3 else None

            else:
                return value.strip()

        except Exception as e:
            logger.warning(f"Error procesando valor {value} para campo {field_name}: {e}")
            return value.strip() if value else None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Convierte string de fecha a objeto date"""
        try:
            # Patrones de fecha soportados
            patterns = [
                (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
                (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),
                (r'(\d{1,2})/(\d{1,2})/(\d{2,4})', '%d/%m/%Y'),
                (r'(\d{1,2})-(\d{1,2})-(\d{2,4})', '%d-%m-%Y')
            ]

            for pattern, date_format in patterns:
                match = re.match(pattern, date_str)
                if match:
                    day, month, year = map(int, match.groups())

                    # Manejar años de 2 dígitos
                    if year < 100:
                        year += 2000 if year < 50 else 1900

                    return date(year, month, day)

            return None

        except (ValueError, OverflowError) as e:
            logger.warning(f"Error parseando fecha {date_str}: {e}")
            return None

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Convierte string de monto a Decimal"""
        try:
            # Limpiar el string
            clean_amount = re.sub(r'[^\d,.]', '', amount_str)

            # Manejar separadores decimales
            if ',' in clean_amount and '.' in clean_amount:
                # Formato: 1.234,56 o 1,234.56
                if clean_amount.rindex(',') > clean_amount.rindex('.'):
                    clean_amount = clean_amount.replace('.', '').replace(',', '.')
                else:
                    clean_amount = clean_amount.replace(',', '')
            elif ',' in clean_amount:
                # Solo comas: puede ser separador de miles o decimal
                comma_parts = clean_amount.split(',')
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    # Probablemente decimal
                    clean_amount = clean_amount.replace(',', '.')
                else:
                    # Probablemente separador de miles
                    clean_amount = clean_amount.replace(',', '')

            return Decimal(clean_amount)

        except (ValueError, InvalidOperation) as e:
            logger.warning(f"Error parseando monto {amount_str}: {e}")
            return None

    def _extract_items(self, text: str) -> List[Dict[str, Any]]:
        """Extrae items/productos de la factura"""
        items = []

        # Buscar líneas que parezcan items de productos
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if len(line) < 10:  # Líneas muy cortas probablemente no son items
                continue

            # Patrón para detectar líneas de items
            # Formato típico: [código] descripción [cantidad] [precio] [importe]
            item_pattern = r'(\w+)?\s+([A-Za-zÁÉÍÓÚáéíóúÑñ\s&\.\-]{5,50})\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)'

            match = re.search(item_pattern, line)
            if match:
                codigo, descripcion, cantidad, precio, importe = match.groups()

                # Validar que los números sean válidos
                if (self._is_valid_amount(cantidad) and 
                    self._is_valid_amount(precio) and 
                    self._is_valid_amount(importe)):

                    item = {
                        'codigo': codigo.strip() if codigo else None,
                        'descripcion': descripcion.strip(),
                        'cantidad': self._parse_amount(cantidad),
                        'precio_unitario': self._parse_amount(precio),
                        'importe': self._parse_amount(importe),
                        'raw_line': line
                    }
                    items.append(item)

        logger.info(f"Items extraídos: {len(items)}")
        return items

    def _validate_and_enhance_data(self, invoice_data: InvoiceData) -> InvoiceData:
        """Valida y mejora los datos extraídos"""

        # Validar consistencia de montos
        if invoice_data.subtotal and invoice_data.iva_total and invoice_data.total:
            calculated_total = invoice_data.subtotal + invoice_data.iva_total
            if invoice_data.impuestos_internos:
                calculated_total += invoice_data.impuestos_internos
            if invoice_data.percepciones:
                calculated_total += invoice_data.percepciones

            # Verificar si el total calculado es consistente (con tolerancia del 1%)
            if abs(calculated_total - invoice_data.total) / invoice_data.total > 0.01:
                logger.warning(f"Inconsistencia en totales: calculado={calculated_total}, declarado={invoice_data.total}")

        # Validar CUIT usando algoritmo de verificación
        for cuit_field in ['cuit_emisor', 'cuit_receptor']:
            cuit_value = getattr(invoice_data, cuit_field)
            if cuit_value and not self._validate_cuit(cuit_value):
                logger.warning(f"CUIT inválido detectado: {cuit_value}")

        # Mejorar confianza basada en campos críticos
        critical_fields = ['numero_factura', 'fecha_emision', 'total', 'cuit_emisor']
        critical_found = sum(1 for field in critical_fields if getattr(invoice_data, field) is not None)

        if critical_found >= 3:
            invoice_data.confidence_score *= 1.2  # Bonus por campos críticos

        invoice_data.confidence_score = min(1.0, invoice_data.confidence_score)

        return invoice_data

    def _validate_cuit(self, cuit: str) -> bool:
        """Valida CUIT usando el algoritmo oficial AFIP"""
        try:
            # Limpiar CUIT
            digits = re.sub(r'[^\d]', '', cuit)
            if len(digits) != 11:
                return False

            # Algoritmo de validación CUIT
            multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            sum_products = sum(int(digits[i]) * multipliers[i] for i in range(10))

            remainder = sum_products % 11
            if remainder == 0:
                check_digit = 0
            elif remainder == 1:
                check_digit = 9
            else:
                check_digit = 11 - remainder

            return int(digits[10]) == check_digit

        except (ValueError, IndexError):
            return False

    def save_to_json(self, invoice_data: InvoiceData, output_path: Union[str, Path]) -> bool:
        """Guarda los datos extraídos en formato JSON"""
        try:
            # Convertir a diccionario serializable
            data_dict = {}

            for field_name in invoice_data.__dataclass_fields__:
                value = getattr(invoice_data, field_name)

                if isinstance(value, (date, datetime)):
                    data_dict[field_name] = value.isoformat()
                elif isinstance(value, Decimal):
                    data_dict[field_name] = float(value)
                elif isinstance(value, list):
                    data_dict[field_name] = [
                        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}
                        if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    data_dict[field_name] = value

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"Datos guardados en: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
            return False

# Funciones de utilidad
def extract_invoice_data(text: str, confidence_threshold: float = 0.3) -> InvoiceData:
    """
    Función conveniente para extraer datos de factura

    Args:
        text: Texto OCR de la factura
        confidence_threshold: Umbral mínimo de confianza

    Returns:
        InvoiceData: Datos estructurados extraídos
    """
    extractor = AFIPDataExtractor()
    return extractor.extract_from_text(text, confidence_threshold)

def extract_and_save_invoice_data(text: str, 
                                output_path: Union[str, Path],
                                confidence_threshold: float = 0.3) -> bool:
    """
    Extrae datos de factura y los guarda en archivo JSON

    Args:
        text: Texto OCR de la factura
        output_path: Ruta donde guardar los datos
        confidence_threshold: Umbral mínimo de confianza

    Returns:
        bool: True si se guardó exitosamente
    """
    extractor = AFIPDataExtractor()
    invoice_data = extractor.extract_from_text(text, confidence_threshold)
    return extractor.save_to_json(invoice_data, output_path)
