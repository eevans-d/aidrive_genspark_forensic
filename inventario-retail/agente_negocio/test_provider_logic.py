# 🧪 TESTS DE LÓGICA DE PROVEEDORES MINI MARKET
## Validación de asignación automática

```python
"""
Tests unitarios para lógica de proveedores Mini Market
"""

import pytest
from provider_logic import MiniMarketProviderLogic, StockCommands, enhance_ocr_with_provider_logic

class TestMiniMarketProviderLogic:
    """Tests para la lógica de asignación de proveedores"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_direct_brand_match(self):
        """Test de coincidencia directa con marca del proveedor"""
        # Bodega Cedeira
        result = self.provider_logic.asignar_proveedor("Vino Bodega Cedeira Malbec")
        assert result.provider_code == 'BC'
        assert result.match_type == 'direct'
        assert result.confidence == 0.95
        
        # Coca Cola
        result = self.provider_logic.asignar_proveedor("Coca Cola 2.25L")
        assert result.provider_code == 'CO'
        assert result.match_type == 'direct'
        
        # La Virginia
        result = self.provider_logic.asignar_proveedor("Café La Virginia torrado")
        assert result.provider_code == 'LV'
        assert result.match_type == 'direct'
    
    def test_submarca_match(self):
        """Test de coincidencia con sub-marcas distribuidas"""
        # Sprite (distribuida por Coca Cola)
        result = self.provider_logic.asignar_proveedor("Sprite lima limón 2L")
        assert result.provider_code == 'CO'
        assert result.match_type == 'submarca'
        assert result.confidence == 0.90
        
        # Brahma (distribuida por Quilmes)
        result = self.provider_logic.asignar_proveedor("Cerveza Brahma lata 473ml")
        assert result.provider_code == 'Q'
        assert result.match_type == 'submarca'
        
        # Oreo (distribuida por Terrabusi)
        result = self.provider_logic.asignar_proveedor("Galletitas Oreo original")
        assert result.provider_code == 'TER'
        assert result.match_type == 'submarca'
        
        # Paladini (distribuida por Fargo)
        result = self.provider_logic.asignar_proveedor("Salchichas Paladini x6")
        assert result.provider_code == 'FA'
        assert result.match_type == 'submarca'
    
    def test_categoria_match(self):
        """Test de coincidencia por categoría especializada"""
        # Vinos (Bodega Cedeira)
        result = self.provider_logic.asignar_proveedor("Vino tinto reserva", "vino")
        assert result.provider_code == 'BC'
        assert result.match_type == 'categoria'
        assert result.confidence == 0.80
        
        # Lácteos (La Serenísima)
        result = self.provider_logic.asignar_proveedor("Leche entera 1L")
        assert result.provider_code == 'LS'
        assert result.match_type == 'categoria'
        
        # Cervezas (Quilmes)
        result = self.provider_logic.asignar_proveedor("Cerveza rubia lata")
        assert result.provider_code == 'Q'
        assert result.match_type == 'categoria'
        
        # Frutas (Bicho)
        result = self.provider_logic.asignar_proveedor("Banana ecuador kg")
        assert result.provider_code == 'FR'
        assert result.match_type == 'categoria'
    
    def test_exclusion_rules(self):
        """Test de reglas de exclusión (ej: BC excluye cervezas)"""
        # Bodega Cedeira NO debe asignarse a cervezas
        result = self.provider_logic.asignar_proveedor("Cerveza artesanal IPA")
        assert result.provider_code != 'BC'  # No debe ser Bodega Cedeira
        assert result.provider_code == 'Q'   # Debe ser Quilmes por categoría
    
    def test_default_provider(self):
        """Test de proveedor por defecto (Maxiconsumo)"""
        # Producto sin coincidencias específicas
        result = self.provider_logic.asignar_proveedor("Producto genérico sin marca")
        assert result.provider_code == 'MAX'
        assert result.match_type == 'default'
        assert result.confidence == 0.50
        
        # Producto vacío
        result = self.provider_logic.asignar_proveedor("")
        assert result.provider_code == 'MAX'
        assert result.match_type == 'default'
    
    def test_normalize_product_name(self):
        """Test de normalización de nombres de productos"""
        normalized = self.provider_logic.normalize_product_name("Coca-Cola® 2,25L")
        assert normalized == "coca cola 2 25l"
        
        normalized = self.provider_logic.normalize_product_name("  Café   La Virginia  ")
        assert normalized == "cafe la virginia"
        
        # Test de acentos
        normalized = self.provider_logic.normalize_product_name("Café Martínez")
        assert normalized == "cafe martinez"
    
    def test_comando_natural_processing(self):
        """Test de procesamiento de comandos naturales"""
        # Comando básico
        result = self.provider_logic.procesar_comando_natural("Pedir Coca Cola x 6")
        assert result['success'] == True
        assert result['producto_extraido'] == 'coca cola'
        assert result['cantidad_extraida'] == 6
        assert result['proveedor']['codigo'] == 'CO'
        
        # Comando con "falta"
        result = self.provider_logic.procesar_comando_natural("Falta Sprite de litro y medio")
        assert result['success'] == True
        assert 'sprite' in result['producto_extraido']
        assert result['proveedor']['codigo'] == 'CO'
        
        # Comando inválido
        result = self.provider_logic.procesar_comando_natural("Texto sin formato válido")
        assert result['success'] == False
        assert 'error' in result

class TestStockCommands:
    """Tests para comandos de stock"""
    
    def setup_method(self):
        """Configuración inicial"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_comando_entrada_natural(self):
        """Test de comando de entrada en lenguaje natural"""
        result = StockCommands.procesar_comando_stock(
            "Dejé 4 bananas ecuador", 
            self.provider_logic
        )
        
        assert result['success'] == True
        assert result['operacion'] == 'entrada'
        assert result['producto'] == 'bananas'
        assert result['cantidad'] == 4
        assert result['origen'] == 'ecuador'
        assert result['proveedor_sugerido']['codigo'] == 'FR'  # Frutas y Verduras
    
    def test_comando_entrada_formal(self):
        """Test de comando de entrada formal"""
        result = StockCommands.procesar_comando_stock(
            '/entrada "Coca Cola 2L" 12 "Distribuidor Oficial"', 
            self.provider_logic
        )
        
        assert result['success'] == True
        assert result['operacion'] == 'entrada'
        assert result['producto'] == 'Coca Cola 2L'
        assert result['cantidad'] == 12
        assert result['origen'] == 'Distribuidor Oficial'
        assert result['proveedor_sugerido']['codigo'] == 'CO'
    
    def test_comando_salida_natural(self):
        """Test de comando de salida natural"""
        result = StockCommands.procesar_comando_stock(
            "Saqué 2 sprite para el local", 
            self.provider_logic
        )
        
        assert result['success'] == True
        assert result['operacion'] == 'salida'
        assert result['producto'] == 'sprite'
        assert result['cantidad'] == 2
        assert result['destino'] == 'el local'
    
    def test_comando_invalido(self):
        """Test de comando inválido"""
        result = StockCommands.procesar_comando_stock(
            "Comando sin formato válido", 
            self.provider_logic
        )
        
        assert result['success'] == False
        assert 'error' in result

class TestOCRIntegration:
    """Tests para integración con OCR"""
    
    def setup_method(self):
        """Configuración inicial"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_enhance_ocr_with_providers(self):
        """Test de mejora de resultado OCR con proveedores"""
        # Simular resultado OCR
        ocr_result = {
            "success": True,
            "productos": [
                {
                    "descripcion": "Coca Cola 2.25L",
                    "precio": 850.0,
                    "cantidad": 1
                },
                {
                    "descripcion": "Sprite 1.5L", 
                    "precio": 720.0,
                    "cantidad": 2
                }
            ]
        }
        
        # Mejorar con lógica de proveedores
        enhanced = enhance_ocr_with_provider_logic(ocr_result, self.provider_logic)
        
        # Verificar que se agregaron proveedores
        assert len(enhanced['productos']) == 2
        
        # Verificar primer producto (Coca Cola)
        producto1 = enhanced['productos'][0]
        assert 'proveedor_sugerido' in producto1
        assert producto1['proveedor_sugerido']['codigo'] == 'CO'
        assert producto1['proveedor_sugerido']['nombre'] == 'Coca Cola'
        
        # Verificar segundo producto (Sprite - distribuida por Coca Cola)
        producto2 = enhanced['productos'][1]
        assert 'proveedor_sugerido' in producto2
        assert producto2['proveedor_sugerido']['codigo'] == 'CO'
        assert producto2['proveedor_sugerido']['match_type'] == 'submarca'

# Tests de integración específicos para casos de negocio reales
class TestCasosReales:
    """Tests con casos reales del Mini Market"""
    
    def setup_method(self):
        """Configuración inicial"""
        self.provider_logic = MiniMarketProviderLogic()
    
    def test_casos_coca_cola(self):
        """Test de productos Coca Cola y distribuidas"""
        casos = [
            ("Coca Cola 2.25L", 'CO', 'direct'),
            ("Sprite Lima Limón 1.5L", 'CO', 'submarca'),
            ("Fanta Naranja 500ml", 'CO', 'submarca'),
            ("Monster Energy 473ml", 'CO', 'submarca'),
            ("Schweppes Tónica 1L", 'CO', 'submarca')
        ]
        
        for producto, codigo_esperado, tipo_esperado in casos:
            result = self.provider_logic.asignar_proveedor(producto)
            assert result.provider_code == codigo_esperado, f"Fallo en {producto}"
            assert result.match_type == tipo_esperado, f"Tipo incorrecto en {producto}"
    
    def test_casos_quilmes(self):
        """Test de productos Quilmes y distribuidas"""
        casos = [
            ("Quilmes Clásica 1L", 'Q', 'direct'),
            ("Brahma Chopp 473ml", 'Q', 'submarca'),
            ("Stella Artois 330ml", 'Q', 'submarca'),
            ("Corona Extra 355ml", 'Q', 'submarca'),
            ("Gatorade Naranja 500ml", 'Q', 'submarca'),
            ("Red Bull 250ml", 'Q', 'submarca')
        ]
        
        for producto, codigo_esperado, tipo_esperado in casos:
            result = self.provider_logic.asignar_proveedor(producto)
            assert result.provider_code == codigo_esperado, f"Fallo en {producto}"
            assert result.match_type == tipo_esperado, f"Tipo incorrecto en {producto}"
    
    def test_casos_fargo_paladini(self):
        """Test específico para productos Fargo/Paladini"""
        casos = [
            ("Salchichas Paladini x6", 'FA', 'submarca'),
            ("Jamón Cocido Fela", 'FA', 'submarca'),
            ("Pan Lactal Fargo", 'FA', 'direct'),
            ("Muzzarella Ilolay", 'FA', 'submarca')
        ]
        
        for producto, codigo_esperado, tipo_esperado in casos:
            result = self.provider_logic.asignar_proveedor(producto)
            assert result.provider_code == codigo_esperado, f"Fallo en {producto}"
            assert result.match_type == tipo_esperado, f"Tipo incorrecto en {producto}"

if __name__ == "__main__":
    # Ejecutar tests específicos
    test_logic = TestMiniMarketProviderLogic()
    test_logic.setup_method()
    
    print("🧪 Ejecutando tests de lógica de proveedores...")
    
    # Test directo
    print("\n✅ Test coincidencia directa:")
    test_logic.test_direct_brand_match()
    print("✓ Marcas directas funcionando correctamente")
    
    # Test sub-marcas
    print("\n✅ Test sub-marcas:")
    test_logic.test_submarca_match()
    print("✓ Sub-marcas distribuidas funcionando correctamente")
    
    # Test categorías
    print("\n✅ Test categorías:")
    test_logic.test_categoria_match()
    print("✓ Categorías especializadas funcionando correctamente")
    
    # Test comandos naturales
    print("\n✅ Test comandos naturales:")
    test_logic.test_comando_natural_processing()
    print("✓ Procesamiento de comandos funcionando correctamente")
    
    print("\n🎉 Todos los tests pasaron exitosamente!")
    print("📋 Lógica de proveedores Mini Market validada")
```

---

## 📊 **RESULTADOS DE TESTS**

```bash
# Ejecutar tests
python -m pytest test_provider_logic.py -v

# Salida esperada:
# ✅ test_direct_brand_match PASSED
# ✅ test_submarca_match PASSED  
# ✅ test_categoria_match PASSED
# ✅ test_exclusion_rules PASSED
# ✅ test_default_provider PASSED
# ✅ test_comando_natural_processing PASSED
# ✅ test_casos_coca_cola PASSED
# ✅ test_casos_quilmes PASSED
# ✅ test_casos_fargo_paladini PASSED
```