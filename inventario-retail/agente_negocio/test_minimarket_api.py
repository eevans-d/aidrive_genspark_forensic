#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite - API Sistema Mini Market
===================================

Suite de pruebas completa para validar todos los endpoints de la API
FastAPI del sistema Mini Market.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"


class MiniMarketAPITester:
    """Tester para la API del sistema Mini Market"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def test_endpoint(self, name: str, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
        """
        Ejecuta un test para un endpoint específico
        
        Args:
            name: Nombre descriptivo del test
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint a probar
            data: Datos para enviar (si aplica)
            expected_status: Código de estado esperado
            
        Returns:
            Resultado del test
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            # Analizar respuesta
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": response_data,
                "error": None
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            
            self.test_results.append(result)
            return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Ejecuta toda la suite de tests de la API
        
        Returns:
            Resumen completo de todos los tests
        """
        print("🏪 === TESTING API SISTEMA MINI MARKET ===")
        print()
        print("⚠️  NOTA: Asegúrate de que la API esté ejecutándose en http://localhost:8000")
        print("   Ejecuta: python3 minimarket_api.py en otra terminal")
        print()
        
        # Pequeña pausa para dar tiempo al usuario
        print("⏳ Esperando 3 segundos antes de iniciar tests...")
        time.sleep(3)
        
        # 1. Test básico de estado
        print("1️⃣  Testing endpoint raíz y estado")
        print("-" * 50)
        
        result = self.test_endpoint("Estado de la API", "GET", "/")
        self._print_test_result(result)
        
        result = self.test_endpoint("Health Check", "GET", "/health")
        self._print_test_result(result)
        
        print()
        
        # 2. Test listado proveedores
        print("2️⃣  Testing listado de proveedores")
        print("-" * 50)
        
        result = self.test_endpoint("Listar Proveedores", "GET", "/proveedores")
        self._print_test_result(result)
        
        print()
        
        # 3. Test asignación de proveedores
        print("3️⃣  Testing asignación de proveedores")
        print("-" * 50)
        
        test_cases = [
            ("Coca Cola", None),
            ("Galletitas Oreo", None),
            ("Vino tinto", "bebida alcoholica"),
            ("Banana", "fruta")
        ]
        
        for producto, categoria in test_cases:
            data = {"producto": producto}
            if categoria:
                data["categoria"] = categoria
            
            result = self.test_endpoint(f"Asignar proveedor: {producto}", "POST", "/asignar-proveedor", data)
            self._print_test_result(result, show_response=True)
        
        print()
        
        # 4. Test comandos naturales
        print("4️⃣  Testing comandos naturales")
        print("-" * 50)
        
        comandos = [
            "Pedir Coca Cola x 6",
            "Falta Sprite lima limón", 
            "Anotar Salchichas Paladini x 3",
            "Necesito bananas x 5"
        ]
        
        for comando in comandos:
            data = {"comando": comando, "usuario": "test_api"}
            result = self.test_endpoint(f"Comando: {comando}", "POST", "/comando-natural", data)
            self._print_test_result(result)
        
        print()
        
        # 5. Test comandos de stock
        print("5️⃣  Testing comandos de stock")
        print("-" * 50)
        
        comandos_stock = [
            "Dejé 4 bananas del ecuador",
            "Ingreso 12 Coca Cola del distribuidor",
            "Saqué 6 productos para el kiosco"
        ]
        
        for comando in comandos_stock:
            data = {"comando": comando, "usuario": "test_api"}
            result = self.test_endpoint(f"Stock: {comando}", "POST", "/comando-stock", data)
            self._print_test_result(result)
        
        print()
        
        # 6. Test procesamiento OCR
        print("6️⃣  Testing procesamiento OCR")
        print("-" * 50)
        
        ocr_data = {
            "numero_factura": "F001-TEST-API-001",
            "proveedor_original": "DISTRIBUIDOR API TEST",
            "productos": [
                {"descripcion": "Coca Cola 2.5L", "precio": 450.00, "cantidad": 2},
                {"descripcion": "Galletitas Oreo", "precio": 380.00, "cantidad": 1},
                {"descripcion": "Banana ecuador kg", "precio": 280.00, "cantidad": 3}
            ],
            "total": 1390.00,
            "usuario": "test_api"
        }
        
        result = self.test_endpoint("Procesar Factura OCR", "POST", "/procesar-factura-ocr", ocr_data)
        self._print_test_result(result)
        
        print()
        
        # 7. Test resúmenes y reportes
        print("7️⃣  Testing resúmenes y reportes")
        print("-" * 50)
        
        result = self.test_endpoint("Resumen de Pedidos", "GET", "/resumen-pedidos?dias=7")
        self._print_test_result(result, show_response=True)
        
        result = self.test_endpoint("Stock Bajo", "GET", "/stock-bajo?limite=10")
        self._print_test_result(result, show_response=True)
        
        result = self.test_endpoint("Pedidos por Proveedor", "GET", "/pedidos-por-proveedor")
        self._print_test_result(result)
        
        print()
        
        # Resumen final
        return self._generate_final_summary()
    
    def _print_test_result(self, result: Dict[str, Any], show_response: bool = False):
        """Imprime el resultado de un test individual"""
        if result['success']:
            print(f"✅ {result['test_name']}")
            if show_response and result['response_data']:
                # Mostrar información relevante de la respuesta
                if 'proveedor_asignado' in result['response_data']:
                    prov = result['response_data']['proveedor_asignado']
                    print(f"   → {prov['codigo']} - {prov['nombre']} (confianza: {prov['confianza']})")
                elif 'total_proveedores_activos' in result['response_data']:
                    print(f"   → {result['response_data']['total_proveedores_activos']} proveedores activos")
                elif 'total_productos' in result['response_data']:
                    print(f"   → {result['response_data']['total_productos']} productos con stock bajo")
        else:
            print(f"❌ {result['test_name']}")
            if result['error']:
                print(f"   Error: {result['error']}")
            elif result['actual_status']:
                print(f"   Status: {result['actual_status']} (esperado: {result['expected_status']})")
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """Genera resumen final de todos los tests"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("="*60)
        print("📊 RESUMEN FINAL DE TESTS")
        print("="*60)
        print(f"Total de tests ejecutados: {total_tests}")
        print(f"Tests exitosos: {successful_tests}")
        print(f"Tests fallidos: {failed_tests}")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTS FALLIDOS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  • {test['test_name']}: {test.get('error', 'Status code incorrecto')}")
            print()
        
        if success_rate >= 90:
            print("🎉 ¡EXCELENTE! La API está funcionando correctamente")
        elif success_rate >= 70:
            print("⚠️  BUENO: La API funciona con algunos problemas menores")
        else:
            print("❌ CRÍTICO: La API tiene problemas significativos")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }


def main():
    """Función principal para ejecutar los tests"""
    tester = MiniMarketAPITester()
    
    try:
        summary = tester.run_all_tests()
        
        # Guardar resultados en archivo
        with open('api_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: api_test_results.json")
        
        return summary['success_rate'] >= 90
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrumpidos por el usuario")
        return False
    except Exception as e:
        print(f"\n💥 Error ejecutando tests: {e}")
        return False


if __name__ == "__main__":
    main()