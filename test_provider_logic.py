"""
Test de lógica de proveedores Mini Market
Verificación de asignación automática y comandos naturales
"""

import unittest
import sys
import os

# Agregar directorio del proyecto al PATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'inventario-retail', 'agente_negocio'))

from provider_logic import (
    MiniMarketProviderLogic, 
    ProviderMatch, 
    enhance_ocr_with_provider_logic,
    StockCommands
)

class TestMiniMarketProviderLogic(unittest.TestCase):
    """Tests para la lógica de proveedores Mini Market"""
    
    def setUp(self):
        """Configurar instancia de lógica de proveedores para cada test"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_asignar_proveedor_marca_directa(self):
        """Test asignación por marca directa del proveedor"""
        # Test Coca Cola
        result = self.provider_logic.asignar_proveedor("Coca Cola de 2 litros")
        self.assertEqual(result.provider_code, 'CO')
        self.assertEqual(result.provider_name, 'Coca Cola')
        self.assertEqual(result.match_type, 'direct')
        self.assertGreaterEqual(result.confidence, 0.95)
        
        # Test Quilmes
        result = self.provider_logic.asignar_proveedor("Cerveza Quilmes lata")
        self.assertEqual(result.provider_code, 'Q')
        self.assertEqual(result.provider_name, 'Quilmes')
        self.assertEqual(result.match_type, 'direct')
        
        # Test La Serenísima
        result = self.provider_logic.asignar_proveedor("Leche La Serenísima entera")
        self.assertEqual(result.provider_code, 'LS')
        self.assertEqual(result.provider_name, 'La Serenísima')
        self.assertEqual(result.match_type, 'direct')
    
    def test_asignar_proveedor_submarca(self):
        """Test asignación por sub-marca distribuida"""
        # Test Sprite (distribuida por Coca Cola)
        result = self.provider_logic.asignar_proveedor("Sprite lima limón")
        self.assertEqual(result.provider_code, 'CO')
        self.assertEqual(result.provider_name, 'Coca Cola')
        self.assertEqual(result.match_type, 'submarca')
        self.assertGreaterEqual(result.confidence, 0.90)
        
        # Test Brahma (distribuida por Quilmes)
        result = self.provider_logic.asignar_proveedor("Cerveza Brahma rubia")
        self.assertEqual(result.provider_code, 'Q')
        self.assertEqual(result.provider_name, 'Quilmes')
        self.assertEqual(result.match_type, 'submarca')
        
        # Test Oreo (distribuida por Terrabusi)
        result = self.provider_logic.asignar_proveedor("Galletitas Oreo originales")
        self.assertEqual(result.provider_code, 'TER')
        self.assertEqual(result.provider_name, 'Terrabusi (Mondelez)')
        self.assertEqual(result.match_type, 'submarca')
        
        # Test Paladini (distribuida por Fargo)
        result = self.provider_logic.asignar_proveedor("Salchichas Paladini viena")
        self.assertEqual(result.provider_code, 'FA')
        self.assertEqual(result.provider_name, 'Fargo')
        self.assertEqual(result.match_type, 'submarca')
    
    def test_asignar_proveedor_categoria(self):
        """Test asignación por categoría especializada"""
        # Test categoría vino (Bodega Cedeira)
        result = self.provider_logic.asignar_proveedor("Vino tinto reserva", "bebida alcoholica")
        self.assertEqual(result.provider_code, 'BC')
        self.assertEqual(result.provider_name, 'Bodega Cedeira')
        self.assertEqual(result.match_type, 'categoria')
        self.assertGreaterEqual(result.confidence, 0.80)
        
        # Test categoría fruta (Frutas y Verduras Bicho)
        result = self.provider_logic.asignar_proveedor("Banana ecuador", "fruta")
        self.assertEqual(result.provider_code, 'FR')
        self.assertEqual(result.provider_name, 'Frutas y Verduras (Bicho)')
        self.assertEqual(result.match_type, 'categoria')
        
        # Test categoría galletita (Terrabusi)
        result = self.provider_logic.asignar_proveedor("Galletita dulce", "galletita")
        self.assertEqual(result.provider_code, 'TER')
        self.assertEqual(result.provider_name, 'Terrabusi (Mondelez)')
        self.assertEqual(result.match_type, 'categoria')
    
    def test_exclusiones_categoria(self):
        """Test exclusiones de categoría (ej: BC excluye cervezas)"""
        # Bodega Cedeira NO debe asignar cervezas
        result = self.provider_logic.asignar_proveedor("Cerveza artesanal", "bebida alcoholica")
        self.assertNotEqual(result.provider_code, 'BC')
        # Debe ir a Quilmes o Maxiconsumo por defecto
        self.assertIn(result.provider_code, ['Q', 'MAX'])
    
    def test_proveedor_por_defecto(self):
        """Test asignación a proveedor por defecto (Maxiconsumo)"""
        # Producto sin coincidencias específicas
        result = self.provider_logic.asignar_proveedor("Producto inexistente raro")
        self.assertEqual(result.provider_code, 'MAX')
        self.assertEqual(result.provider_name, 'Maxiconsumo')
        self.assertEqual(result.match_type, 'default')
        self.assertGreaterEqual(result.confidence, 0.50)
        
        # Producto vacío
        result = self.provider_logic.asignar_proveedor("")
        self.assertEqual(result.provider_code, 'MAX')
        self.assertEqual(result.match_type, 'default')
    
    def test_normalizacion_producto(self):
        """Test normalización de nombres de productos"""
        # Test acentos y caracteres especiales
        normalized = self.provider_logic.normalize_product_name("Bebída gaseosa Pepsi®")
        self.assertEqual(normalized, "bebida gaseosa pepsi")
        
        # Test espacios múltiples
        normalized = self.provider_logic.normalize_product_name("Coca   Cola    2L")
        self.assertEqual(normalized, "coca cola 2l")
        
        # Test string vacío
        normalized = self.provider_logic.normalize_product_name("")
        self.assertEqual(normalized, "")
    
    def test_comandos_naturales(self):
        """Test procesamiento de comandos en lenguaje natural"""
        # Test comando "Pedir"
        result = self.provider_logic.procesar_comando_natural("Pedir Coca Cola x 6")
        self.assertTrue(result['success'])
        self.assertEqual(result['producto_extraido'], 'coca cola')
        self.assertEqual(result['cantidad_extraida'], 6)
        self.assertEqual(result['proveedor']['codigo'], 'CO')
        
        # Test comando "Falta"
        result = self.provider_logic.procesar_comando_natural("Falta Brahma de litro")
        self.assertTrue(result['success'])
        self.assertEqual(result['producto_extraido'], 'brahma litro')
        self.assertEqual(result['cantidad_extraida'], 1)
        self.assertEqual(result['proveedor']['codigo'], 'Q')
        
        # Test comando "Anotar"
        result = self.provider_logic.procesar_comando_natural("Anotar Salchichas Paladini x 3")
        self.assertTrue(result['success'])
        self.assertEqual(result['producto_extraido'], 'salchichas paladini')
        self.assertEqual(result['cantidad_extraida'], 3)
        self.assertEqual(result['proveedor']['codigo'], 'FA')
        
        # Test comando inválido
        result = self.provider_logic.procesar_comando_natural("comando incomprensible xyz")
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_pedidos_por_proveedor(self):
        """Test agrupación de pedidos por proveedor"""
        # Registrar algunos pedidos
        self.provider_logic.procesar_comando_natural("Pedir Coca Cola x 2")
        self.provider_logic.procesar_comando_natural("Falta Sprite lima")
        self.provider_logic.procesar_comando_natural("Anotar Brahma x 4")
        
        # Obtener pedidos agrupados
        result = self.provider_logic.obtener_pedidos_por_proveedor()
        self.assertTrue(result['success'])
        self.assertEqual(result['total_productos'], 3)
        self.assertGreaterEqual(result['total_proveedores'], 2)
        
        # Verificar que Coca Cola tiene 2 productos (Coca Cola y Sprite)
        pedidos_co = result['pedidos_por_proveedor'].get('CO', {})
        if pedidos_co:
            self.assertEqual(len(pedidos_co['productos']), 2)
            self.assertEqual(pedidos_co['proveedor']['nombre'], 'Coca Cola')
        
        # Obtener pedidos de un proveedor específico
        result_q = self.provider_logic.obtener_pedidos_por_proveedor('Q')
        self.assertTrue(result_q['success'])
        if 'Q' in result_q['pedidos_por_proveedor']:
            self.assertEqual(len(result_q['pedidos_por_proveedor']['Q']['productos']), 1)


class TestStockCommands(unittest.TestCase):
    """Tests para comandos de stock"""
    
    def setUp(self):
        """Configurar instancia para cada test"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_comando_entrada_natural(self):
        """Test comando de entrada en lenguaje natural"""
        result = StockCommands.procesar_comando_stock(
            "Dejé 4 bananas ecuador", 
            self.provider_logic
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['operacion'], 'entrada')
        self.assertEqual(result['producto'], 'bananas')
        self.assertEqual(result['cantidad'], 4)
        self.assertEqual(result['origen'], 'ecuador')
        self.assertEqual(result['proveedor_sugerido']['codigo'], 'FR')
    
    def test_comando_entrada_formal(self):
        """Test comando de entrada formal"""
        result = StockCommands.procesar_comando_stock(
            '/entrada "Coca Cola 2L" 12 "Distribuidor"', 
            self.provider_logic
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['operacion'], 'entrada')
        self.assertEqual(result['producto'], 'Coca Cola 2L')
        self.assertEqual(result['cantidad'], 12)
        self.assertEqual(result['origen'], 'Distribuidor')
        self.assertEqual(result['proveedor_sugerido']['código'], 'CO')
    
    def test_comando_salida_natural(self):
        """Test comando de salida en lenguaje natural"""
        result = StockCommands.procesar_comando_stock(
            "Saqué 2 productos para el local", 
            self.provider_logic
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['operacion'], 'salida')
        self.assertEqual(result['producto'], 'productos')
        self.assertEqual(result['cantidad'], 2)
        self.assertEqual(result['destino'], 'el local')
    
    def test_comando_salida_formal(self):
        """Test comando de salida formal"""
        result = StockCommands.procesar_comando_stock(
            '/salida "Brahma lata" 6 "kiosco"', 
            self.provider_logic
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['operacion'], 'salida')
        self.assertEqual(result['producto'], 'Brahma lata')
        self.assertEqual(result['cantidad'], 6)
        self.assertEqual(result['destino'], 'kiosco')
    
    def test_comando_invalido(self):
        """Test comando inválido"""
        result = StockCommands.procesar_comando_stock(
            "comando incomprensible", 
            self.provider_logic
        )
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestOCRIntegration(unittest.TestCase):
    """Tests para integración con OCR"""
    
    def setUp(self):
        """Configurar instancia para cada test"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_enhance_ocr_with_provider_logic(self):
        """Test mejora de resultados OCR con lógica de proveedores"""
        # Simular resultado OCR
        ocr_result = {
            'factura_numero': '12345',
            'productos': [
                {
                    'descripcion': 'Coca Cola 2L',
                    'precio': 450.00,
                    'cantidad': 2
                },
                {
                    'descripcion': 'Galletitas Oreo',
                    'precio': 350.00,
                    'cantidad': 1
                },
                {
                    'descripcion': 'Banana ecuador',
                    'precio': 120.00,
                    'cantidad': 5,
                    'categoria': 'fruta'
                }
            ]
        }
        
        # Mejorar con lógica de proveedores
        enhanced_result = enhance_ocr_with_provider_logic(ocr_result, self.provider_logic)
        
        # Verificar que se mantienen los datos originales
        self.assertEqual(enhanced_result['factura_numero'], '12345')
        self.assertEqual(len(enhanced_result['productos']), 3)
        
        # Verificar asignación de proveedores
        productos = enhanced_result['productos']
        
        # Producto 1: Coca Cola -> CO
        self.assertIn('proveedor_sugerido', productos[0])
        self.assertEqual(productos[0]['proveedor_sugerido']['codigo'], 'CO')
        self.assertEqual(productos[0]['proveedor_sugerido']['nombre'], 'Coca Cola')
        
        # Producto 2: Oreo -> TER
        self.assertIn('proveedor_sugerido', productos[1])
        self.assertEqual(productos[1]['proveedor_sugerido']['codigo'], 'TER')
        self.assertEqual(productos[1]['proveedor_sugerido']['nombre'], 'Terrabusi (Mondelez)')
        
        # Producto 3: Banana -> FR
        self.assertIn('proveedor_sugerido', productos[2])
        self.assertEqual(productos[2]['proveedor_sugerido']['codigo'], 'FR')
        self.assertEqual(productos[2]['proveedor_sugerido']['nombre'], 'Frutas y Verduras (Bicho)')


if __name__ == '__main__':
    print("=== TESTING LÓGICA PROVEEDORES MINI MARKET ===")
    print()
    
    # Ejecutar tests
    unittest.main(verbosity=2)