"""
Provider Logic - Lógica específica de proveedores Mini Market
Integración con sistema OCR existente
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProviderMatch:
    """Resultado de coincidencia con proveedor"""
    provider_code: str
    provider_name: str
    confidence: float
    match_type: str
    product_normalized: str

class MiniMarketProviderLogic:
    """Lógica de asignación de proveedores específica para Mini Market"""
    
    PROVIDERS = {
        'BC': {
            'name': 'Bodega Cedeira',
            'categorias': ['vino', 'fernet', 'whisky', 'vodka', 'ron', 'licor', 'champagne', 'bebida alcoholica'],
            'marcas_directas': ['bodega cedeira'],
            'exclude_keywords': ['cerveza', 'beer']
        },
        'CO': {
            'name': 'Coca Cola',
            'categorias': ['gaseosa', 'bebida sin alcohol'],
            'marcas_directas': ['coca-cola', 'coca cola', 'cocacola'],
            'marcas_distribuidas': ['sprite', 'fanta', 'aquarius', 'ades', 'cepita', 'monster', 'schweppes']
        },
        'Q': {
            'name': 'Quilmes',
            'categorias': ['cerveza', 'beer'],
            'marcas_directas': ['quilmes'],
            'marcas_distribuidas': [
                'brahma', 'stella artois', 'andes', 'corona',
                'gatorade', 'glaciar', 'pepsi', '7up', 'paso de los toros', 
                'eco de los andes', 'red bull'
            ]
        },
        'FA': {
            'name': 'Fargo',
            'categorias': ['panificado', 'pan', 'congelado'],
            'marcas_directas': ['fargo'],
            'marcas_distribuidas': [
                'levite', 'baggio', 'natura', 'luchetti', 'matarazzo', 'don vicente',
                'cabrales', 'arlistan', 'barfy', 'friar', 'granja del sol', 'veggies', 'mccain',
                'paulina', 'ilolay', 'jet food', 'paladini', 'fela'
            ]
        },
        'LS': {
            'name': 'La Serenísima',
            'categorias': ['lacteo', 'leche', 'yogur', 'queso'],
            'marcas_directas': ['la serenisima', 'la serenísima'],
            'marcas_distribuidas': ['yogurisimo', 'yogurísimo', 'ser', 'casancrem', 'finlandia', 'cremon', 'cindor']
        },
        'ACE': {
            'name': 'Aceitumar (MDP)',
            'categorias': ['fruto seco', 'semilla', 'snack', 'aceite gourmet', 'especia', 'salsa', 'conserva'],
            'marcas_directas': ['aceitumar'],
            'marcas_distribuidas': [
                'chocolart', 'cris-jor', 'laur', 'tau delta', 'cumana', 'zoraida', 
                'el ruedo', 'contraviento', 'sakanashi', 'shun yuan', 'healthy boy', 'marvavic', 'la delfina'
            ]
        },
        'TER': {
            'name': 'Terrabusi (Mondelez)',
            'categorias': ['galletita', 'chocolate', 'golosina', 'chicle', 'alfajor'],
            'marcas_directas': ['terrabusi'],
            'marcas_distribuidas': ['oreo', 'pepitos', 'milka', 'beldent', 'infinit', 'rhodesia', 'tita']
        },
        'LV': {
            'name': 'La Virginia',
            'categorias': ['cafe', 'té', 'te', 'yerba mate', 'infusion'],
            'marcas_directas': ['la virginia']
        },
        'FR': {
            'name': 'Frutas y Verduras (Bicho)',
            'categorias': ['fruta', 'verdura', 'fresco', 'banana', 'tomate', 'manzana', 'lechuga'],
            'marcas_directas': ['bicho']
        },
        'MU': {
            'name': 'Multienvase (MDP)',
            'categorias': ['envase', 'descartable', 'vaso plastico', 'plato descartable'],
            'marcas_directas': ['multienvase']
        },
        'GA': {
            'name': 'Galletitera (MDP)',
            'categorias': ['galleteria artesanal', 'panaderia local'],
            'marcas_directas': ['galletitera']
        },
        'MAX': {
            'name': 'Maxiconsumo',
            'categorias': ['mayorista', 'general'],
            'marcas_directas': ['maxiconsumo'],
            'is_default': True
        }
    }
    
    def __init__(self):
        self.pedidos_cache = []
        
    def normalize_product_name(self, product_name: str) -> str:
        """Normaliza nombre de producto para matching"""
        if not product_name:
            return ""
            
        normalized = product_name.lower().strip()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for accented, normal in replacements.items():
            normalized = normalized.replace(accented, normal)
            
        return normalized
    
    def asignar_proveedor(self, product_name: str, categoria: Optional[str] = None) -> ProviderMatch:
        """Asigna proveedor según jerarquía de reglas definida en documentación"""
        if not product_name:
            return self._get_default_provider("Producto vacío")
            
        normalized_product = self.normalize_product_name(product_name)
        normalized_categoria = self.normalize_product_name(categoria) if categoria else ""
        
        logger.info(f"Asignando proveedor para: '{product_name}' (normalizado: '{normalized_product}')")
        
        # 1. Coincidencia Directa de Marca del Proveedor
        direct_match = self._check_direct_brand_match(normalized_product)
        if direct_match:
            return direct_match
            
        # 2. Coincidencia de Sub-Marca Específica
        submarca_match = self._check_submarca_match(normalized_product)
        if submarca_match:
            return submarca_match
            
        # 3. Coincidencia por Categoría Especializada
        categoria_match = self._check_categoria_match(normalized_product, normalized_categoria)
        if categoria_match:
            return categoria_match
            
        # 5. Proveedor por Defecto
        return self._get_default_provider(f"No match encontrado para: {product_name}")
    
    def _check_direct_brand_match(self, normalized_product: str) -> Optional[ProviderMatch]:
        """Verifica coincidencia directa con marca del proveedor"""
        for code, provider in self.PROVIDERS.items():
            for marca in provider.get('marcas_directas', []):
                if marca in normalized_product:
                    return ProviderMatch(
                        provider_code=code,
                        provider_name=provider['name'],
                        confidence=0.95,
                        match_type='direct',
                        product_normalized=normalized_product
                    )
        return None
    
    def _check_submarca_match(self, normalized_product: str) -> Optional[ProviderMatch]:
        """Verifica coincidencia con sub-marcas distribuidas"""
        for code, provider in self.PROVIDERS.items():
            for submarca in provider.get('marcas_distribuidas', []):
                if submarca in normalized_product:
                    return ProviderMatch(
                        provider_code=code,
                        provider_name=provider['name'],
                        confidence=0.90,
                        match_type='submarca',
                        product_normalized=normalized_product
                    )
        return None
    
    def _check_categoria_match(self, normalized_product: str, normalized_categoria: str) -> Optional[ProviderMatch]:
        """Verifica coincidencia por categoría especializada"""
        combined_text = f"{normalized_product} {normalized_categoria}".strip()
        
        for code, provider in self.PROVIDERS.items():
            if 'exclude_keywords' in provider:
                for exclude in provider['exclude_keywords']:
                    if exclude in combined_text:
                        continue
                        
            for categoria in provider.get('categorias', []):
                if categoria in combined_text:
                    return ProviderMatch(
                        provider_code=code,
                        provider_name=provider['name'],
                        confidence=0.80,
                        match_type='categoria',
                        product_normalized=normalized_product
                    )
        return None
    
    def _get_default_provider(self, reason: str) -> ProviderMatch:
        """Retorna proveedor por defecto (Maxiconsumo)"""
        logger.info(f"Asignando proveedor por defecto - Razón: {reason}")
        return ProviderMatch(
            provider_code='MAX',
            provider_name='Maxiconsumo',
            confidence=0.50,
            match_type='default',
            product_normalized=reason
        )
    
    def registrar_pedido(self, producto: str, cantidad: int = 1, empleado_turno: str = "N/A") -> Dict:
        """Registra un nuevo pedido según la documentación del cliente"""
        try:
            provider_match = self.asignar_proveedor(producto)
            
            pedido = {
                "id": len(self.pedidos_cache) + 1,
                "proveedor_code": provider_match.provider_code,
                "producto": producto,
                "cantidad": cantidad,
                "estado": "Pendiente",
                "empleado_turno": empleado_turno,
                "fecha_pedido": datetime.now().isoformat(),
                "confidence_asignacion": provider_match.confidence,
                "match_type": provider_match.match_type
            }
            
            self.pedidos_cache.append(pedido)
            
            logger.info(f"Pedido registrado: {producto} -> {provider_match.provider_name} ({provider_match.provider_code})")
            
            return {
                "success": True,
                "pedido_id": pedido["id"],
                "producto": producto,
                "proveedor": {
                    "codigo": provider_match.provider_code,
                    "nombre": provider_match.provider_name,
                    "confidence": provider_match.confidence,
                    "match_type": provider_match.match_type
                },
                "cantidad": cantidad,
                "estado": "Pendiente"
            }
            
        except Exception as e:
            logger.error(f"Error registrando pedido: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def procesar_comando_natural(self, comando: str) -> Dict:
        """Procesa comandos en lenguaje natural según documentación"""
        try:
            comando_lower = comando.lower().strip()
            
            pedido_patterns = [
                r'(?:pedir|anotar|necesito|traer)\s+(.+?)(?:\s+x\s*(\d+))?$',
                r'falta\s+(.+?)(?:\s+x\s*(\d+))?$',
                r'agregar.*?lista.*?:\s*(.+?)(?:\s+x\s*(\d+))?$'
            ]
            
            for pattern in pedido_patterns:
                match = re.search(pattern, comando_lower)
                if match:
                    producto = match.group(1).strip()
                    cantidad_str = match.group(2) or "1"
                    cantidad = int(cantidad_str)
                    
                    producto = producto.replace(' de ', ' ')
                    producto = producto.replace(' y medio', '.5')
                    
                    result = self.registrar_pedido(producto, cantidad)
                    result['comando_procesado'] = comando
                    result['producto_extraido'] = producto
                    result['cantidad_extraida'] = cantidad
                    
                    return result
            
            return {
                "success": False,
                "error": "No se pudo interpretar el comando",
                "comando": comando,
                "sugerencia": "Usa formato: 'Pedir [Producto] x [Cantidad]' o 'Falta [Producto]'"
            }
            
        except Exception as e:
            logger.error(f"Error procesando comando natural: {e}")
            return {
                "success": False,
                "error": str(e),
                "comando": comando
            }
    
    def obtener_pedidos_por_proveedor(self, proveedor_code: Optional[str] = None) -> Dict:
        """Obtiene pedidos agrupados por proveedor"""
        try:
            pedidos = self.pedidos_cache
            
            if proveedor_code:
                pedidos = [p for p in pedidos if p.get('proveedor_code') == proveedor_code]
                
            grouped = {}
            for pedido in pedidos:
                code = pedido.get('proveedor_code')
                if code not in grouped:
                    provider_info = self.PROVIDERS.get(code, {})
                    grouped[code] = {
                        "proveedor": {
                            "codigo": code,
                            "nombre": provider_info.get('name', 'Desconocido')
                        },
                        "productos": []
                    }
                
                grouped[code]["productos"].append({
                    "id": pedido.get('id'),
                    "producto": pedido.get('producto'),
                    "cantidad": pedido.get('cantidad'),
                    "fecha_pedido": pedido.get('fecha_pedido'),
                    "empleado_turno": pedido.get('empleado_turno')
                })
            
            return {
                "success": True,
                "pedidos_por_proveedor": grouped,
                "total_proveedores": len(grouped),
                "total_productos": len(pedidos)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo pedidos: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def enhance_ocr_with_provider_logic(ocr_result: Dict, provider_logic: MiniMarketProviderLogic) -> Dict:
    """Mejora resultado OCR con lógica de proveedores"""
    enhanced_result = ocr_result.copy()
    
    if 'productos' in ocr_result:
        enhanced_products = []
        for producto in ocr_result['productos']:
            if isinstance(producto, dict) and 'descripcion' in producto:
                provider_match = provider_logic.asignar_proveedor(
                    producto['descripcion'], 
                    producto.get('categoria')
                )
                
                producto['proveedor_sugerido'] = {
                    "codigo": provider_match.provider_code,
                    "nombre": provider_match.provider_name,
                    "confidence": provider_match.confidence,
                    "match_type": provider_match.match_type
                }
                
            enhanced_products.append(producto)
        
        enhanced_result['productos'] = enhanced_products
    
    return enhanced_result

class StockCommands:
    """Comandos de stock para integración con Agente Depósito"""
    
    ENTRADA_PATTERNS = [
        r'(?:deje|dejé|ingreso|traje|sumar)\s+(\d+)\s+(.+?)(?:\s+(?:de|del)\s+(.+))?$',
        r'/entrada\s+"([^"]+)"\s+(\d+)(?:\s+"([^"]+)")?'
    ]
    
    SALIDA_PATTERNS = [
        r'(?:saque|saqué|llevo|retiro|descontar)\s+(\d+)\s+(.+?)(?:\s+(?:para|del|al)\s+(.+))?$',
        r'/salida\s+"([^"]+)"\s+(\d+)(?:\s+"([^"]+)")?'
    ]
    
    @staticmethod
    def procesar_comando_stock(comando: str, provider_logic: MiniMarketProviderLogic) -> Dict:
        """Procesa comandos de stock según documentación"""
        comando_clean = comando.strip()
        
        if any(pattern in comando.lower() for pattern in ['deje', 'dejé', 'ingreso', 'traje', 'sumar', '/entrada']):
            return StockCommands._procesar_entrada(comando_clean, provider_logic)
        elif any(pattern in comando.lower() for pattern in ['saque', 'saqué', 'llevo', 'retiro', 'descontar', '/salida']):
            return StockCommands._procesar_salida(comando_clean, provider_logic)
        else:
            return {
                "success": False,
                "error": "Comando no reconocido",
                "tipos_validos": ["entrada", "salida"]
            }
    
    @staticmethod
    def _procesar_entrada(comando: str, provider_logic: MiniMarketProviderLogic) -> Dict:
        """Procesa comando de entrada de stock"""
        for pattern in StockCommands.ENTRADA_PATTERNS:
            match = re.search(pattern, comando, re.IGNORECASE)
            if match:
                if pattern.startswith('/entrada'):
                    producto = match.group(1)
                    cantidad = int(match.group(2))
                    origen = match.group(3) or "N/A"
                else:
                    cantidad = int(match.group(1))
                    producto = match.group(2)
                    origen = match.group(3) or "N/A"
                
                provider_match = provider_logic.asignar_proveedor(producto)
                
                return {
                    "success": True,
                    "operacion": "entrada",
                    "producto": producto,
                    "cantidad": cantidad,
                    "origen": origen,
                    "proveedor_sugerido": {
                        "codigo": provider_match.provider_code,
                        "nombre": provider_match.provider_name,
                        "confidence": provider_match.confidence
                    },
                    "comando_original": comando
                }
        
        return {
            "success": False,
            "error": "Formato de entrada no válido",
            "ejemplo": "Dejé 4 productos del proveedor X"
        }
    
    @staticmethod
    def _procesar_salida(comando: str, provider_logic: MiniMarketProviderLogic) -> Dict:
        """Procesa comando de salida de stock"""
        for pattern in StockCommands.SALIDA_PATTERNS:
            match = re.search(pattern, comando, re.IGNORECASE)
            if match:
                if pattern.startswith('/salida'):
                    producto = match.group(1)
                    cantidad = int(match.group(2))
                    destino = match.group(3) or "local"
                else:
                    cantidad = int(match.group(1))
                    producto = match.group(2)
                    destino = match.group(3) or "local"
                
                return {
                    "success": True,
                    "operacion": "salida",
                    "producto": producto,
                    "cantidad": cantidad,
                    "destino": destino,
                    "comando_original": comando
                }
        
        return {
            "success": False,
            "error": "Formato de salida no válido",
            "ejemplo": "Saqué 2 productos para el local"
        }
