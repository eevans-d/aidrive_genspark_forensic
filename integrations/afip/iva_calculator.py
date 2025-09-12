"""
Calculadora de IVA según normativa argentina
Incluye todas las alícuotas oficiales de AFIP
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class IVABracket:
    """Alícuota de IVA"""
    codigo: str
    porcentaje: float
    descripcion: str
    categoria: str

class CategoriaFiscal(Enum):
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    EXENTO = "exento"
    CONSUMIDOR_FINAL = "consumidor_final"
    MONOTRIBUTO = "monotributo"

class IVACalculator:
    """Calculadora de IVA argentina"""

    # Alícuotas oficiales AFIP
    ALICUOTAS = {
        '21': IVABracket('21', 21.0, 'IVA 21% - Tasa General', 'general'),
        '10.5': IVABracket('10.5', 10.5, 'IVA 10,5% - Tasa Reducida', 'reducida'),
        '27': IVABracket('27', 27.0, 'IVA 27% - Tasa Adicional', 'adicional'),
        '5': IVABracket('5', 5.0, 'IVA 5% - Productos Medicamentos', 'especial'),
        '2.5': IVABracket('2.5', 2.5, 'IVA 2,5% - Productos Específicos', 'especial'),
        '0': IVABracket('0', 0.0, 'IVA 0% - Exento', 'exento')
    }

    def calculate_iva(self, neto: Decimal, alicuota: str) -> Dict[str, Any]:
        """Calcula IVA para un monto neto"""
        if alicuota not in self.ALICUOTAS:
            raise ValueError(f"Alícuota {alicuota} no válida")

        bracket = self.ALICUOTAS[alicuota]
        porcentaje = Decimal(str(bracket.porcentaje))

        # Calcular IVA
        iva = (neto * porcentaje / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = neto + iva

        return {
            "neto": float(neto),
            "alicuota": alicuota,
            "porcentaje": float(porcentaje),
            "iva": float(iva),
            "total": float(total),
            "descripcion": bracket.descripcion
        }

    def calculate_multiple_alicuotas(self, items: List[Dict]) -> Dict[str, Any]:
        """Calcula IVA para múltiples items con diferentes alícuotas"""
        detalles = []
        total_neto = Decimal('0')
        total_iva = Decimal('0')

        for item in items:
            neto = Decimal(str(item['neto']))
            alicuota = item['alicuota']

            calculo = self.calculate_iva(neto, alicuota)
            detalles.append(calculo)

            total_neto += neto
            total_iva += Decimal(str(calculo['iva']))

        return {
            "total_neto": float(total_neto),
            "total_iva": float(total_iva),
            "total_general": float(total_neto + total_iva),
            "detalles": detalles
        }
