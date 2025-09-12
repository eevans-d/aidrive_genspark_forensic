"""
Factura Validator Argentino
=========================

Validador especializado para facturas argentinas con validaciones
específicas de CUIT, numeración AFIP, formatos A/B/C, y normativas locales.

Autor: Sistema Inventario Retail Argentino
Fecha: 2025-08-22
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

class TipoFactura(Enum):
    """Tipos de factura según AFIP"""
    FACTURA_A = "A"
    FACTURA_B = "B"
    FACTURA_C = "C"
    NOTA_CREDITO_A = "NC-A"
    NOTA_CREDITO_B = "NC-B"
    NOTA_CREDITO_C = "NC-C"
    NOTA_DEBITO_A = "ND-A"
    NOTA_DEBITO_B = "ND-B"
    NOTA_DEBITO_C = "ND-C"
    REMITO = "REMITO"

class TipoContribuyente(Enum):
    """Tipos de contribuyente según AFIP"""
    RESPONSABLE_INSCRIPTO = "RI"
    MONOTRIBUTISTA = "MONO"
    EXENTO = "EX"
    CONSUMIDOR_FINAL = "CF"
    NO_RESPONSABLE = "NR"

@dataclass
class ValidationResult:
    """Resultado de validación con detalles"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_data: Dict
    confidence_score: float

class FacturaValidatorArgentino:
    """Validador especializado para facturas argentinas"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Patrones regex para campos argentinos
        self.patterns = {
            "cuit": r'(?:CUIT[:\s]*)?(\d{2}[-\s]*\d{8}[-\s]*\d{1})',
            "numero_factura": r'(?:N°|Nº|NUMERO)[:\s]*(\d{4}[-\s]*\d{8})',
            "punto_venta": r'(?:PV|PUNTO\s+VENTA|PTO\s+VTA)[:\s]*(\d{4})',
            "numero_comprobante": r'(?:COMP|COMPROBANTE)[:\s]*(\d{8})',
            "fecha": r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            "fecha_vto": r'(?:VTO|VENCIMIENTO|VENCE)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            "cai": r'(?:CAI|COD\s+AUT)[:\s]*(\d{14})',
            "cae": r'(?:CAE)[:\s]*(\d{14})',
            "total": r'(?:TOTAL|IMPORTE\s+TOTAL)[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "subtotal": r'(?:SUBTOTAL|NETO)[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "iva": r'(?:IVA|I\.V\.A\.)[:\s]*\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            "iva_porcentaje": r'IVA\s*(\d{1,2}(?:[.,]\d{1,2})?)\s*%',
            "razon_social": r'(?:RAZON\s+SOCIAL|DENOMINACION)[:\s]*([A-ZÁÉÍÓÚÑ\s\.]+)',
            "domicilio": r'(?:DOMICILIO|DIRECCION)[:\s]*([A-ZÁÉÍÓÚÑ0-9\s\.,]+)',
            "condicion_iva": r'(?:CONDICION\s+(?:FRENTE\s+AL\s+)?IVA|CATEGORIA)[:\s]*([A-ZÁÉÍÓÚÑ\s]+)'
        }

        # Multiplicadores para validación dígito verificador CUIT
        self.cuit_multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

        # IVA rates válidos en Argentina
        self.iva_rates_validos = [0, 10.5, 21, 27]

        # Códigos de actividad AFIP (simplificado)
        self.actividades_afip = {
            "11": "Responsable Inscripto",
            "12": "Monotributo",
            "13": "Exento"
        }

    def validate_factura_completa(self, texto_ocr: str, factura_type: Optional[TipoFactura] = None) -> ValidationResult:
        """
        Validar factura completa con todos los campos requeridos

        Args:
            texto_ocr: Texto extraído por OCR
            factura_type: Tipo de factura si se conoce

        Returns:
            ValidationResult con detalles de validación
        """
        errors = []
        warnings = []
        normalized_data = {}

        try:
            # 1. Extraer todos los campos
            campos_extraidos = self._extract_all_fields(texto_ocr)

            # 2. Detectar tipo de factura si no se especificó
            if not factura_type:
                factura_type = self._detect_factura_type(texto_ocr)

            campos_extraidos["tipo_factura"] = factura_type.value if factura_type else "UNKNOWN"

            # 3. Validar campos obligatorios según tipo
            campos_obligatorios = self._get_campos_obligatorios(factura_type)

            for campo in campos_obligatorios:
                if campo not in campos_extraidos or not campos_extraidos[campo]:
                    errors.append(f"Campo obligatorio faltante: {campo}")

            # 4. Validaciones específicas por campo
            validation_results = {
                "cuit": self._validate_cuit(campos_extraidos.get("cuit", "")),
                "numero_factura": self._validate_numero_factura(campos_extraidos.get("numero_factura", "")),
                "fecha": self._validate_fecha(campos_extraidos.get("fecha", "")),
                "montos": self._validate_montos(campos_extraidos),
                "iva": self._validate_iva(campos_extraidos),
                "cai_cae": self._validate_cai_cae(campos_extraidos)
            }

            # Consolidar errores y warnings
            for field, result in validation_results.items():
                if not result["valid"]:
                    errors.extend(result["errors"])
                warnings.extend(result.get("warnings", []))
                if "normalized" in result:
                    normalized_data.update(result["normalized"])

            # 5. Validaciones de coherencia
            coherencia_result = self._validate_coherencia(campos_extraidos, factura_type)
            errors.extend(coherencia_result["errors"])
            warnings.extend(coherencia_result["warnings"])

            # 6. Calcular confidence score
            confidence_score = self._calculate_confidence_score(
                campos_extraidos, len(errors), len(warnings)
            )

            # Normalizar datos finales
            normalized_data.update(campos_extraidos)
            normalized_data = self._normalize_final_data(normalized_data)

            return ValidationResult(
                is_valid=(len(errors) == 0),
                errors=errors,
                warnings=warnings,
                normalized_data=normalized_data,
                confidence_score=confidence_score
            )

        except Exception as e:
            self.logger.error(f"Error en validación completa: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Error interno: {str(e)}"],
                warnings=[],
                normalized_data={},
                confidence_score=0.0
            )

    def _extract_all_fields(self, texto: str) -> Dict:
        """Extraer todos los campos usando patrones regex"""
        campos = {}

        for field_name, pattern in self.patterns.items():
            matches = re.findall(pattern, texto.upper(), re.IGNORECASE | re.MULTILINE)
            if matches:
                # Tomar la primera coincidencia válida
                campos[field_name] = matches[0].strip()

        return campos

    def _detect_factura_type(self, texto: str) -> TipoFactura:
        """Detectar tipo de factura desde el texto"""
        texto_upper = texto.upper()

        # Patrones de detección mejorados
        if re.search(r'FACTURA\s*[:\s]*A', texto_upper):
            return TipoFactura.FACTURA_A
        elif re.search(r'FACTURA\s*[:\s]*B', texto_upper):
            return TipoFactura.FACTURA_B
        elif re.search(r'FACTURA\s*[:\s]*C', texto_upper):
            return TipoFactura.FACTURA_C
        elif re.search(r'NOTA\s+(?:DE\s+)?CREDITO.*A', texto_upper):
            return TipoFactura.NOTA_CREDITO_A
        elif re.search(r'NOTA\s+(?:DE\s+)?CREDITO.*B', texto_upper):
            return TipoFactura.NOTA_CREDITO_B
        elif re.search(r'NOTA\s+(?:DE\s+)?CREDITO.*C', texto_upper):
            return TipoFactura.NOTA_CREDITO_C
        elif re.search(r'NOTA\s+(?:DE\s+)?DEBITO.*A', texto_upper):
            return TipoFactura.NOTA_DEBITO_A
        elif re.search(r'NOTA\s+(?:DE\s+)?DEBITO.*B', texto_upper):
            return TipoFactura.NOTA_DEBITO_B
        elif re.search(r'NOTA\s+(?:DE\s+)?DEBITO.*C', texto_upper):
            return TipoFactura.NOTA_DEBITO_C
        elif re.search(r'REMITO', texto_upper):
            return TipoFactura.REMITO

        return TipoFactura.FACTURA_B  # Default más común

    def _get_campos_obligatorios(self, factura_type: TipoFactura) -> List[str]:
        """Obtener campos obligatorios según tipo de factura"""
        base_fields = ["fecha", "numero_factura", "razon_social"]

        if factura_type in [TipoFactura.FACTURA_A, TipoFactura.FACTURA_B, TipoFactura.FACTURA_C]:
            base_fields.extend(["total", "cuit"])

        if factura_type == TipoFactura.FACTURA_A:
            base_fields.extend(["iva", "subtotal", "cai"])

        if factura_type in [TipoFactura.FACTURA_A, TipoFactura.FACTURA_B]:
            base_fields.append("condicion_iva")

        return base_fields

    def _validate_cuit(self, cuit: str) -> Dict:
        """Validar CUIT según algoritmo AFIP"""
        if not cuit:
            return {"valid": False, "errors": ["CUIT faltante"]}

        try:
            # Limpiar CUIT (solo dígitos)
            cuit_clean = re.sub(r'\D', '', cuit)

            if len(cuit_clean) != 11:
                return {"valid": False, "errors": ["CUIT debe tener 11 dígitos"]}

            # Validar dígito verificador
            digitos = [int(d) for d in cuit_clean[:10]]
            suma = sum(d * m for d, m in zip(digitos, self.cuit_multiplicadores))
            resto = suma % 11

            if resto < 2:
                digito_verificador = resto
            else:
                digito_verificador = 11 - resto

            if int(cuit_clean[10]) != digito_verificador:
                return {
                    "valid": False,
                    "errors": ["CUIT con dígito verificador inválido"],
                    "warnings": ["Verificar si el CUIT fue leído correctamente por OCR"]
                }

            # Formatear CUIT normalizado
            cuit_formatted = f"{cuit_clean[:2]}-{cuit_clean[2:10]}-{cuit_clean[10]}"

            return {
                "valid": True,
                "errors": [],
                "normalized": {"cuit_formatted": cuit_formatted, "cuit_clean": cuit_clean}
            }

        except Exception as e:
            return {"valid": False, "errors": [f"Error validando CUIT: {e}"]}

    def _validate_numero_factura(self, numero: str) -> Dict:
        """Validar formato de número de factura"""
        if not numero:
            return {"valid": False, "errors": ["Número de factura faltante"]}

        # Limpiar número
        numero_clean = re.sub(r'[^\d]', '', numero)

        if len(numero_clean) < 8:
            return {"valid": False, "errors": ["Número de factura muy corto"]}

        # Formato esperado: PPPPNNNNNNNN (4 dígitos PV + 8 dígitos número)
        if len(numero_clean) == 12:
            punto_venta = numero_clean[:4]
            numero_comp = numero_clean[4:]
            formatted = f"{punto_venta}-{numero_comp}"
        else:
            # Asumir formato libre
            formatted = numero_clean

        return {
            "valid": True,
            "errors": [],
            "normalized": {"numero_factura_formatted": formatted}
        }

    def _validate_fecha(self, fecha: str) -> Dict:
        """Validar formato de fecha"""
        if not fecha:
            return {"valid": False, "errors": ["Fecha faltante"]}

        # Intentar parsear diferentes formatos de fecha
        formatos = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']

        for formato in formatos:
            try:
                parsed_date = datetime.strptime(fecha, formato)

                # Validar rango de fechas razonable
                hoy = datetime.now()
                if parsed_date > hoy:
                    return {
                        "valid": False,
                        "errors": ["Fecha futura no válida"],
                        "warnings": ["La fecha no puede ser posterior a hoy"]
                    }

                # Validar que no sea demasiado antigua (más de 10 años)
                if (hoy - parsed_date).days > 3650:
                    warnings = ["Fecha muy antigua, verificar si es correcta"]
                else:
                    warnings = []

                return {
                    "valid": True,
                    "errors": [],
                    "warnings": warnings,
                    "normalized": {
                        "fecha_formatted": parsed_date.strftime('%d/%m/%Y'),
                        "fecha_iso": parsed_date.isoformat()
                    }
                }

            except ValueError:
                continue

        return {"valid": False, "errors": ["Formato de fecha inválido"]}

    def _validate_montos(self, campos: Dict) -> Dict:
        """Validar coherencia de montos"""
        errors = []
        warnings = []
        normalized = {}

        try:
            # Convertir montos a float
            montos = {}
            for campo in ["total", "subtotal", "iva"]:
                if campo in campos and campos[campo]:
                    monto_str = campos[campo].replace(".", "").replace(",", ".")
                    try:
                        montos[campo] = float(re.sub(r'[^\d.,]', '', monto_str))
                        normalized[f"{campo}_float"] = montos[campo]
                    except ValueError:
                        errors.append(f"Monto {campo} con formato inválido")

            # Validar coherencia: Total = Subtotal + IVA
            if "total" in montos and "subtotal" in montos and "iva" in montos:
                total_calculado = montos["subtotal"] + montos["iva"]
                diferencia = abs(montos["total"] - total_calculado)

                if diferencia > 0.01:  # Tolerancia de 1 centavo
                    warnings.append(
                        f"Inconsistencia en montos: Total={montos['total']}, "
                        f"Subtotal+IVA={total_calculado}"
                    )

            # Validar montos positivos
            for campo, monto in montos.items():
                if monto < 0:
                    errors.append(f"Monto {campo} no puede ser negativo")
                elif monto == 0 and campo == "total":
                    warnings.append("Total en cero, verificar si es correcto")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "normalized": normalized
            }

        except Exception as e:
            return {"valid": False, "errors": [f"Error validando montos: {e}"]}

    def _validate_iva(self, campos: Dict) -> Dict:
        """Validar IVA y sus porcentajes"""
        errors = []
        warnings = []
        normalized = {}

        try:
            # Validar porcentaje de IVA si está presente
            if "iva_porcentaje" in campos and campos["iva_porcentaje"]:
                porcentaje_str = campos["iva_porcentaje"].replace(",", ".")
                try:
                    porcentaje = float(porcentaje_str)

                    if porcentaje not in self.iva_rates_validos:
                        warnings.append(
                            f"Porcentaje IVA inusual: {porcentaje}%. "
                            f"Válidos: {self.iva_rates_validos}"
                        )

                    normalized["iva_porcentaje_float"] = porcentaje

                except ValueError:
                    errors.append("Porcentaje IVA con formato inválido")

            # Validar coherencia IVA vs Subtotal
            if ("iva" in campos and "subtotal" in campos and 
                "iva_porcentaje" in normalized):

                try:
                    iva_monto = float(campos["iva"].replace(".", "").replace(",", "."))
                    subtotal = float(campos["subtotal"].replace(".", "").replace(",", "."))
                    porcentaje = normalized["iva_porcentaje_float"]

                    iva_calculado = subtotal * (porcentaje / 100)
                    diferencia = abs(iva_monto - iva_calculado)

                    if diferencia > 0.01:
                        warnings.append(
                            f"IVA inconsistente: Declarado={iva_monto}, "
                            f"Calculado={iva_calculado:.2f}"
                        )

                except ValueError:
                    pass  # Ya validado en _validate_montos

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "normalized": normalized
            }

        except Exception as e:
            return {"valid": False, "errors": [f"Error validando IVA: {e}"]}

    def _validate_cai_cae(self, campos: Dict) -> Dict:
        """Validar CAI/CAE"""
        errors = []
        warnings = []
        normalized = {}

        cai = campos.get("cai", "")
        cae = campos.get("cae", "")

        if not cai and not cae:
            warnings.append("CAI o CAE faltante")
            return {"valid": True, "warnings": warnings}

        # Validar CAI (14 dígitos)
        if cai:
            cai_clean = re.sub(r'\D', '', cai)
            if len(cai_clean) != 14:
                errors.append("CAI debe tener 14 dígitos")
            else:
                normalized["cai_clean"] = cai_clean

        # Validar CAE (14 dígitos)
        if cae:
            cae_clean = re.sub(r'\D', '', cae)
            if len(cae_clean) != 14:
                errors.append("CAE debe tener 14 dígitos")
            else:
                normalized["cae_clean"] = cae_clean

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "normalized": normalized
        }

    def _validate_coherencia(self, campos: Dict, factura_type: TipoFactura) -> Dict:
        """Validar coherencia general de la factura"""
        errors = []
        warnings = []

        try:
            # Validar coherencia tipo factura vs contenido
            if factura_type == TipoFactura.FACTURA_C:
                # Factura C no debe tener discriminación de IVA
                if "iva" in campos and campos["iva"]:
                    try:
                        iva_monto = float(campos["iva"].replace(".", "").replace(",", "."))
                        if iva_monto > 0:
                            warnings.append("Factura C con IVA discriminado es inusual")
                    except ValueError:
                        pass

            # Validar CUIT vs tipo de contribuyente
            condicion_iva = campos.get("condicion_iva", "").upper()
            if condicion_iva:
                if "RESPONSABLE INSCRIPTO" in condicion_iva and factura_type == TipoFactura.FACTURA_C:
                    warnings.append("Responsable Inscripto emitiendo Factura C es inusual")
                elif "MONOTRIBUTO" in condicion_iva and factura_type == TipoFactura.FACTURA_A:
                    warnings.append("Monotributista emitiendo Factura A es inusual")

            return {"errors": errors, "warnings": warnings}

        except Exception as e:
            return {"errors": [f"Error en validación de coherencia: {e}"], "warnings": []}

    def _calculate_confidence_score(self, campos: Dict, num_errors: int, num_warnings: int) -> float:
        """Calcular score de confianza de la validación"""
        try:
            # Score base por campos extraídos
            campos_importantes = ["cuit", "numero_factura", "fecha", "total", "razon_social"]
            campos_presentes = sum(1 for campo in campos_importantes if campos.get(campo))
            base_score = campos_presentes / len(campos_importantes)

            # Penalización por errores y warnings
            error_penalty = num_errors * 0.2
            warning_penalty = num_warnings * 0.1

            # Score final
            final_score = max(0.0, base_score - error_penalty - warning_penalty)

            return round(final_score, 3)

        except Exception:
            return 0.5  # Score neutral en caso de error

    def _normalize_final_data(self, data: Dict) -> Dict:
        """Normalizar datos finales para consistencia"""
        normalized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Limpiar espacios extra
                normalized[key] = ' '.join(value.split())
            else:
                normalized[key] = value

        # Agregar campos calculados útiles
        if "fecha_iso" in normalized:
            try:
                fecha = datetime.fromisoformat(normalized["fecha_iso"])
                normalized["anio"] = fecha.year
                normalized["mes"] = fecha.month
                normalized["dia"] = fecha.day
            except ValueError:
                pass

        return normalized

    def validate_quick(self, texto_ocr: str) -> Dict:
        """Validación rápida con campos básicos"""
        try:
            campos = self._extract_all_fields(texto_ocr)
            factura_type = self._detect_factura_type(texto_ocr)

            # Validaciones básicas
            has_cuit = bool(campos.get("cuit"))
            has_numero = bool(campos.get("numero_factura"))
            has_fecha = bool(campos.get("fecha"))
            has_total = bool(campos.get("total"))

            score = sum([has_cuit, has_numero, has_fecha, has_total]) / 4

            return {
                "basic_validation_passed": score >= 0.5,
                "confidence_score": score,
                "factura_type": factura_type.value,
                "campos_detectados": len(campos),
                "campos_criticos": {
                    "cuit": has_cuit,
                    "numero": has_numero,
                    "fecha": has_fecha,
                    "total": has_total
                }
            }

        except Exception as e:
            return {
                "basic_validation_passed": False,
                "error": str(e),
                "confidence_score": 0.0
            }

# Ejemplo de uso
if __name__ == "__main__":
    validator = FacturaValidatorArgentino()

    # Test con texto de ejemplo
    texto_ejemplo = """
    FACTURA B
    CUIT: 20-12345678-9
    N° 0001-00000123
    FECHA: 15/08/2025
    TOTAL: $1.234,56
    """

    resultado = validator.validate_quick(texto_ejemplo)
    print("Validación rápida:", resultado)
