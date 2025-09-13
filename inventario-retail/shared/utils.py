"""
Utilidades para contexto argentino
Validación CUIT, formato precios, fechas y funciones auxiliares
"""
import re
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, Tuple
import locale


def validar_cuit(cuit: str) -> Tuple[bool, Optional[str]]:
    """
    Valida CUIT argentino con dígito verificador

    Args:
        cuit: CUIT a validar (puede incluir guiones)

    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not cuit:
        return False, "CUIT no puede estar vacío"

    # Limpiar CUIT - solo números
    cuit_limpio = re.sub(r"[^\d]", "", cuit)

    # Verificar longitud
    if len(cuit_limpio) != 11:
        return False, "CUIT debe tener 11 dígitos"

    # Verificar que todos son dígitos
    if not cuit_limpio.isdigit():
        return False, "CUIT solo puede contener números"

    # Verificar prefijo válido (tipo de persona)
    prefijos_validos = [
        "20",  # Personas físicas masculinas
        "23",  # Personas físicas masculinas (hasta 1986)
        "24",  # Personas físicas masculinas (hasta 1986) 
        "27",  # Personas físicas femeninas
        "30",  # Personas jurídicas
        "33",  # Servicios del exterior
        "34",  # Servicios del exterior
    ]

    prefijo = cuit_limpio[:2]
    if prefijo not in prefijos_validos:
        return False, f"Prefijo CUIT '{prefijo}' no válido"

    # Calcular dígito verificador
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0

    for i, digito in enumerate(cuit_limpio[:10]):
        suma += int(digito) * multiplicadores[i]

    resto = suma % 11

    if resto < 2:
        digito_calculado = resto
    else:
        digito_calculado = 11 - resto

    digito_informado = int(cuit_limpio[10])

    if digito_calculado != digito_informado:
        return False, f"Dígito verificador inválido. Esperado: {digito_calculado}, Recibido: {digito_informado}"

    return True, None


def formatear_cuit(cuit: str) -> str:
    """
    Formatea CUIT con guiones: XX-XXXXXXXX-X

    Args:
        cuit: CUIT sin formato

    Returns:
        str: CUIT formateado
    """
    cuit_limpio = re.sub(r"[^\d]", "", cuit)

    if len(cuit_limpio) == 11:
        return f"{cuit_limpio[:2]}-{cuit_limpio[2:10]}-{cuit_limpio[10]}"

    return cuit


def formatear_precio_argentino(precio: Union[float, int, Decimal], 
                              incluir_simbolo: bool = True,
                              decimales: int = 2) -> str:
    """
    Formatea precios en formato argentino: $1.234,56

    Args:
        precio: Precio a formatear
        incluir_simbolo: Si incluir símbolo $
        decimales: Cantidad de decimales

    Returns:
        str: Precio formateado
    """
    if precio is None:
        return ""

    # Convertir a Decimal para precisión
    if isinstance(precio, (int, float)):
        precio_decimal = Decimal(str(precio))
    else:
        precio_decimal = precio

    # Redondear a decimales especificados
    precio_redondeado = precio_decimal.quantize(
        Decimal(10) ** -decimales, 
        rounding=ROUND_HALF_UP
    )

    # Separar parte entera y decimal
    partes = str(precio_redondeado).split(".")
    parte_entera = partes[0]
    parte_decimal = partes[1] if len(partes) > 1 else "00"

    # Formatear parte entera con separador de miles (punto)
    if len(parte_entera) > 3:
        # Agregar puntos cada 3 dígitos desde la derecha
        parte_entera_formateada = ""
        for i, digito in enumerate(reversed(parte_entera)):
            if i > 0 and i % 3 == 0:
                parte_entera_formateada = "." + parte_entera_formateada
            parte_entera_formateada = digito + parte_entera_formateada
        parte_entera = parte_entera_formateada

    # Asegurar que decimales tengan la longitud correcta
    parte_decimal = parte_decimal[:decimales].ljust(decimales, "0")

    # Construir precio final
    precio_formateado = f"{parte_entera},{parte_decimal}"

    if incluir_simbolo:
        precio_formateado = f"${precio_formateado}"

    return precio_formateado


def parsear_precio_argentino(precio_str: str) -> Optional[float]:
    """
    Parsea precio en formato argentino a float

    Args:
        precio_str: Precio como string "$1.234,56" o "1234.56"

    Returns:
        Optional[float]: Precio como número o None si inválido
    """
    if not precio_str:
        return None

    # Limpiar string
    precio_limpio = precio_str.strip().replace("$", "").replace(" ", "")

    # Verificar si tiene formato argentino (coma como decimal)
    if "," in precio_limpio:
        # Separar miles y decimales
        if "." in precio_limpio and precio_limpio.rindex(".") < precio_limpio.rindex(","):
            # Formato: 1.234.567,89
            partes = precio_limpio.rsplit(",", 1)
            parte_entera = partes[0].replace(".", "")
            parte_decimal = partes[1]
        else:
            # Formato: 1234,89
            partes = precio_limpio.split(",")
            parte_entera = partes[0]
            parte_decimal = partes[1] if len(partes) > 1 else "0"

        precio_normalizado = f"{parte_entera}.{parte_decimal}"
    else:
        # Asumir formato estándar (punto como decimal)
        precio_normalizado = precio_limpio.replace(".", "", precio_limpio.count(".") - 1)


    """
    Funciones utilitarias compartidas para el sistema multiagente.
    Incluye helpers para carga y guardado de archivos JSON.
    """

    # Imports principales
    import os
    import json
    from typing import Any, Dict, List

    def load_json_file(filepath: str) -> Any:
        """
        Carga un archivo JSON y devuelve su contenido.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json_file(filepath: str, data: Any) -> None:
        """
        Guarda datos en un archivo JSON con formato legible.
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def calcular_inflacion_acumulada(meses: int, inflacion_mensual: float) -> float:
    """
    Calcula la inflación acumulada en porcentaje.
    Args:
        meses (int): Cantidad de meses.
        inflacion_mensual (float): Inflación mensual en porcentaje.
    Returns:
        float: Inflación acumulada en porcentaje.
    """
    if meses <= 0:
        return 0.0
    factor_acumulado = (1 + inflacion_mensual / 100) ** meses
    return (factor_acumulado - 1) * 100



def calcular_precio_con_inflacion(precio_base: float,
                                 dias_transcurridos: int,
                                 inflacion_mensual: float) -> float:
    """
    Calcula el precio ajustado por inflación.
    Args:
        precio_base (float): Precio original.
        dias_transcurridos (int): Días desde la compra.
        inflacion_mensual (float): Inflación mensual en porcentaje.
    Returns:
        float: Precio ajustado.
    """
    if dias_transcurridos <= 0:
        return precio_base
    inflacion_diaria = (1 + inflacion_mensual / 100) ** (1 / 30.44) - 1
    factor_inflacion = (1 + inflacion_diaria) ** dias_transcurridos
    return precio_base * factor_inflacion


def obtener_factor_estacional(temporada: str) -> float:
    """
    Obtiene factor estacional para stock mínimo según temporada argentina

    Args:
        temporada: Temporada actual

    Returns:
        float: Factor multiplicador para stock mínimo
    """
    factores = {
        "verano": 1.3,      # Diciembre-Marzo: +30% (vacaciones, mayor consumo)
        "otoño": 1.0,       # Marzo-Junio: Normal
        "invierno": 0.8,    # Junio-Septiembre: -20% (menor actividad)
        "primavera": 1.1    # Septiembre-Diciembre: +10% (preparación verano)
    }

    return factores.get(temporada.lower(), 1.0)


def obtener_temporada_actual() -> str:
    """
    Determina la temporada actual basada en el mes (hemisferio sur)

    Returns:
        str: Temporada actual
    """
    mes_actual = datetime.now().month

    if mes_actual in [12, 1, 2]:
        return "verano"
    elif mes_actual in [3, 4, 5]:
        return "otoño"
    elif mes_actual in [6, 7, 8]:
        return "invierno"
    else:  # 9, 10, 11
        return "primavera"


def validar_numero_factura_afip(numero: str, tipo_factura: str) -> Tuple[bool, Optional[str]]:
    """
    Valida formato de número de factura AFIP

    Args:
        numero: Número de factura
        tipo_factura: Tipo de factura (A, B, C, E, M)

    Returns:
        Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
    """
    if not numero:
        return False, "Número de factura no puede estar vacío"

    # Limpiar número
    numero_limpio = numero.strip().upper()

    # Patrones según tipo de factura
    patrones = {
        "A": r"^\d{4}-\d{8}$|^\d{5}-\d{8}$",  # XXXX-XXXXXXXX o XXXXX-XXXXXXXX
        "B": r"^\d{4}-\d{8}$|^\d{5}-\d{8}$",  # Similar a A
        "C": r"^\d{4}-\d{8}$|^\d{5}-\d{8}$",  # Similar a A
        "E": r"^\d{4}-\d{8}$",                # Exportación
        "M": r"^\d{4}-\d{8}$"                 # Mercado interno
    }

    patron = patrones.get(tipo_factura.upper())
    if not patron:
        return False, f"Tipo de factura '{tipo_factura}' no válido"

    if not re.match(patron, numero_limpio):
        return False, f"Formato de número inválido para factura tipo {tipo_factura}"

    return True, None


def formatear_fecha_argentina(fecha: Union[datetime, date], 
                            incluir_hora: bool = False) -> str:
    """
    Formatea fecha en formato argentino DD/MM/YYYY

    Args:
        fecha: Fecha a formatear
        incluir_hora: Si incluir hora HH:MM

    Returns:
        str: Fecha formateada
    """
    if not fecha:
        return ""

    if incluir_hora and isinstance(fecha, datetime):
        return fecha.strftime("%d/%m/%Y %H:%M")
    else:
        return fecha.strftime("%d/%m/%Y")


def generar_codigo_producto(categoria: str, contador: int) -> str:
    """
    Genera código de producto siguiendo patrón argentino

    Args:
        categoria: Categoría del producto
        contador: Número secuencial

    Returns:
        str: Código generado
    """
    # Mapear categorías a prefijos
    prefijos = {
        "almacen": "ALM",
        "bebidas": "BEB",
        "limpieza": "LIM", 
        "perfumeria": "PER",
        "lacteos": "LAC",
        "carniceria": "CAR",
        "verduleria": "VER",
        "panaderia": "PAN",
        "general": "GEN"
    }

    prefijo = prefijos.get(categoria.lower(), "GEN")
    codigo = f"{prefijo}{contador:06d}"  # ALM000001

    return codigo


def calcular_dias_habiles(fecha_inicio: date, fecha_fin: date) -> int:
    """
    Calcula días hábiles entre dos fechas (excluyendo sábados y domingos)

    Args:
        fecha_inicio: Fecha inicial
        fecha_fin: Fecha final

    Returns:
        int: Número de días hábiles
    """
    if fecha_inicio > fecha_fin:
        return 0

    dias_totales = (fecha_fin - fecha_inicio).days + 1
    semanas_completas = dias_totales // 7
    dias_restantes = dias_totales % 7

    # Días hábiles en semanas completas (5 por semana)
    dias_habiles = semanas_completas * 5

    # Agregar días hábiles de la semana parcial
    dia_inicial = fecha_inicio.weekday()  # 0=Lunes, 6=Domingo

    for i in range(dias_restantes):
        dia_actual = (dia_inicial + i) % 7
        if dia_actual < 5:  # Lunes a Viernes
            dias_habiles += 1

    return dias_habiles


def normalizar_texto_factura(texto: str) -> str:
    """
    Normaliza texto extraído de OCR de facturas
    Limpia caracteres especiales, espacios múltiples, etc.

    Args:
        texto: Texto crudo del OCR

    Returns:
        str: Texto normalizado
    """
    if not texto:
        return ""

    # Limpiar caracteres problemáticos del OCR
    texto_limpio = texto.replace("\n", " ").replace("\t", " ")

    # Remover caracteres no imprimibles
    texto_limpio = "".join(char for char in texto_limpio if char.isprintable())

    # Normalizar espacios múltiples
    texto_limpio = re.sub(r"\s+", " ", texto_limpio)

    # Limpiar bordes
    texto_limpio = texto_limpio.strip()

    return texto_limpio


class FormateadorArgentino:
    """
    Clase utilitaria para formateo consistente de datos argentinos
    """

    @staticmethod
    def precio(valor: Union[float, int, Decimal], con_simbolo: bool = True) -> str:
        """Formatea precio en formato argentino"""
        return formatear_precio_argentino(valor, con_simbolo)

    @staticmethod
    def cuit(cuit: str) -> str:
        """Formatea CUIT con guiones"""
        return formatear_cuit(cuit)

    @staticmethod
    def fecha(fecha: Union[datetime, date], con_hora: bool = False) -> str:
        """Formatea fecha argentina"""
        return formatear_fecha_argentina(fecha, con_hora)

    @staticmethod
    def porcentaje(valor: float, decimales: int = 2) -> str:
        """Formatea porcentaje con coma decimal"""
        return f"{valor:.{decimales}f}%".replace(".", ",")


# Instancia global del formateador
formateador = FormateadorArgentino()
