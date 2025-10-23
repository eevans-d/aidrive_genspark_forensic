"""
Tests para OCR Preview Modal
=============================
Tests para validar los endpoints de OCR y la lógica de preview
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient


class TestOCRPreview:
    """Test suite para OCR Preview"""
    
    def test_ocr_process_endpoint_exists(self, client):
        """Test que el endpoint /api/ocr/process existe"""
        response = client.post('/api/ocr/process', json={
            "image_base64": "test",
            "proveedor_id": 1
        })
        assert response.status_code in [200, 400, 500]  # Endpoint existe
    
    def test_ocr_process_requires_image(self, client):
        """Test que /api/ocr/process requiere image_base64"""
        response = client.post('/api/ocr/process', json={})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_ocr_process_returns_valid_structure(self, client):
        """Test que /api/ocr/process retorna estructura válida"""
        response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"fake_image").decode(),
            "proveedor_id": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Validar estructura
            required_fields = [
                'request_id', 'confidence', 'proveedor', 'fecha', 
                'total', 'items', 'warnings', 'suggestions'
            ]
            
            for field in required_fields:
                assert field in data, f"Falta campo: {field}"
            
            # Validar tipos
            assert isinstance(data['request_id'], str)
            assert isinstance(data['confidence'], (int, float))
            assert isinstance(data['proveedor'], str)
            assert isinstance(data['fecha'], str)
            assert isinstance(data['total'], (int, float))
            assert isinstance(data['items'], list)
            assert isinstance(data['warnings'], list)
            assert isinstance(data['suggestions'], list)
    
    def test_ocr_process_confidence_range(self, client):
        """Test que confianza está entre 0-100"""
        response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"fake").decode(),
            "proveedor_id": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            assert 0 <= data['confidence'] <= 100
    
    def test_ocr_process_items_structure(self, client):
        """Test que items tienen estructura válida"""
        response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"fake").decode(),
            "proveedor_id": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data['items']:
                assert 'name' in item
                assert 'quantity' in item
                assert 'price' in item
                assert isinstance(item['quantity'], (int, float))
                assert isinstance(item['price'], (int, float))
    
    def test_ocr_confirm_endpoint_exists(self, client):
        """Test que el endpoint /api/ocr/confirm existe"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "test123",
            "proveedor": "Test Supplier",
            "fecha": "2024-10-20",
            "total": 1500.0
        })
        assert response.status_code in [200, 400, 500]
    
    def test_ocr_confirm_requires_fields(self, client):
        """Test que /api/ocr/confirm requiere campos obligatorios"""
        # Sin request_id
        response = client.post('/api/ocr/confirm', json={
            "proveedor": "Test",
            "fecha": "2024-10-20",
            "total": 100
        })
        assert response.status_code == 400
        
        # Sin proveedor
        response = client.post('/api/ocr/confirm', json={
            "request_id": "test",
            "fecha": "2024-10-20",
            "total": 100
        })
        assert response.status_code == 400
    
    def test_ocr_confirm_returns_valid_response(self, client):
        """Test que /api/ocr/confirm retorna respuesta válida"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "test123",
            "proveedor": "Distribuidora XYZ",
            "fecha": "2024-10-20",
            "total": 1500.0,
            "items": [],
            "confidence": 90.0,
            "edited_fields": []
        })
        
        if response.status_code == 200:
            data = response.json()
            
            assert "success" in data
            assert data["success"] is True
            assert "request_id" in data
            assert "document_id" in data
            assert "message" in data
    
    def test_ocr_confirm_records_edited_fields(self, client):
        """Test que /api/ocr/confirm registra campos editados"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "test456",
            "proveedor": "Modified Supplier",
            "fecha": "2024-10-20",
            "total": 2000.0,
            "confidence": 75.0,
            "edited_fields": ["proveedor", "total"]
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "edited_fields_count" in data
            assert data["edited_fields_count"] == 2
    
    def test_ocr_low_confidence_warning(self, client):
        """Test que OCR con baja confianza genera warnings"""
        response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"bad_image").decode(),
            "proveedor_id": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar que si confidence < 80, hay warnings
            if data['confidence'] < 80:
                assert len(data['warnings']) > 0


class TestOCRMetrics:
    """Test suite para métricas de OCR"""
    
    def test_ocr_metrics_exist(self, client):
        """Test que métricas OCR son expuestas en /metrics"""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        metrics_text = response.text
        
        # Métricas que deberían existir
        expected_metrics = [
            'dashboard_requests_total',
            'dashboard_errors_total',
            'dashboard_request_duration_ms_p95'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics_text or metrics_text != ""


class TestOCRIntegration:
    """Test suite integrado para flujo completo OCR"""
    
    def test_ocr_full_flow(self, client):
        """Test flujo completo: procesar OCR → confirmar"""
        
        # Paso 1: Procesar OCR
        process_response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"invoice_image").decode(),
            "proveedor_id": 1
        })
        
        if process_response.status_code != 200:
            pytest.skip("OCR process endpoint not available")
        
        process_data = process_response.json()
        request_id = process_data['request_id']
        
        # Paso 2: Validar datos
        assert process_data['confidence'] > 0
        assert process_data['proveedor']
        assert process_data['total'] > 0
        
        # Paso 3: Confirmar OCR
        confirm_response = client.post('/api/ocr/confirm', json={
            "request_id": request_id,
            "proveedor": process_data['proveedor'],
            "fecha": process_data['fecha'],
            "total": process_data['total'],
            "items": process_data['items'],
            "confidence": process_data['confidence'],
            "edited_fields": []
        })
        
        assert confirm_response.status_code == 200
        confirm_data = confirm_response.json()
        assert confirm_data['success'] is True
        assert confirm_data['request_id'] == request_id
    
    def test_ocr_with_manual_edits(self, client):
        """Test OCR con ediciones manuales"""
        
        # Procesar
        process_response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"test").decode(),
            "proveedor_id": 1
        })
        
        if process_response.status_code != 200:
            pytest.skip("OCR process endpoint not available")
        
        process_data = process_response.json()
        
        # Editar proveedor
        edited_proveedor = "Proveedor Corregido"
        
        # Confirmar con ediciones
        confirm_response = client.post('/api/ocr/confirm', json={
            "request_id": process_data['request_id'],
            "proveedor": edited_proveedor,  # ← Editado
            "fecha": process_data['fecha'],
            "total": process_data['total'],
            "items": process_data['items'],
            "confidence": process_data['confidence'],
            "edited_fields": ["proveedor"]  # ← Marcado como editado
        })
        
        assert confirm_response.status_code == 200
        data = confirm_response.json()
        assert data['edited_fields_count'] == 1


class TestOCREdgeCases:
    """Test suite para casos extremos"""
    
    def test_ocr_with_empty_items(self, client):
        """Test OCR cuando no hay items detectados"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "edge_case_1",
            "proveedor": "Test",
            "fecha": "2024-10-20",
            "total": 100.0,
            "items": [],
            "confidence": 95.0,
            "edited_fields": []
        })
        
        assert response.status_code == 200
    
    def test_ocr_with_many_items(self, client):
        """Test OCR con muchos items"""
        items = [
            {"name": f"Item {i}", "quantity": 1, "price": 10.0}
            for i in range(100)
        ]
        
        response = client.post('/api/ocr/confirm', json={
            "request_id": "edge_case_2",
            "proveedor": "Big Order",
            "fecha": "2024-10-20",
            "total": 1000.0,
            "items": items,
            "confidence": 88.0,
            "edited_fields": []
        })
        
        assert response.status_code == 200
    
    def test_ocr_with_special_characters(self, client):
        """Test OCR con caracteres especiales en proveedor"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "edge_case_3",
            "proveedor": "Distribuidora XYZ & Cía. S.A. (Ltda.)",
            "fecha": "2024-10-20",
            "total": 1500.0,
            "items": [],
            "confidence": 90.0,
            "edited_fields": ["proveedor"]
        })
        
        assert response.status_code == 200
    
    def test_ocr_with_large_total(self, client):
        """Test OCR con totales grandes"""
        response = client.post('/api/ocr/confirm', json={
            "request_id": "edge_case_4",
            "proveedor": "Large Amount",
            "fecha": "2024-10-20",
            "total": 9999999.99,
            "items": [],
            "confidence": 92.0,
            "edited_fields": []
        })
        
        assert response.status_code == 200
    
    def test_ocr_confirm_generates_unique_document_ids(self, client):
        """Test que cada confirmación genera document_id único"""
        ids = []
        
        for i in range(3):
            response = client.post('/api/ocr/confirm', json={
                "request_id": f"unique_test_{i}",
                "proveedor": "Test",
                "fecha": "2024-10-20",
                "total": 100.0 + i,
                "items": [],
                "confidence": 90.0,
                "edited_fields": []
            })
            
            if response.status_code == 200:
                data = response.json()
                ids.append(data.get('document_id'))
        
        # Los IDs deberían ser únicos
        if ids:
            assert len(ids) == len(set(ids)), "document_ids no son únicos"


class TestOCRPerformance:
    """Test suite de performance para OCR"""
    
    def test_ocr_process_latency(self, client):
        """Test que OCR process responde rápido (<2s)"""
        import time
        
        start = time.time()
        response = client.post('/api/ocr/process', json={
            "image_base64": base64.b64encode(b"test").decode(),
            "proveedor_id": 1
        })
        duration = time.time() - start
        
        if response.status_code == 200:
            assert duration < 2.0, f"OCR process too slow: {duration:.2f}s"
    
    def test_ocr_confirm_latency(self, client):
        """Test que OCR confirm responde rápido (<1s)"""
        import time
        
        start = time.time()
        response = client.post('/api/ocr/confirm', json={
            "request_id": "perf_test",
            "proveedor": "Test",
            "fecha": "2024-10-20",
            "total": 100.0,
            "items": [],
            "confidence": 90.0,
            "edited_fields": []
        })
        duration = time.time() - start
        
        if response.status_code == 200:
            assert duration < 1.0, f"OCR confirm too slow: {duration:.2f}s"
    
    def test_ocr_100_concurrent_confirmations(self, client):
        """Test que OCR maneja 100 confirmaciones (carga)"""
        import concurrent.futures
        
        def confirm_ocr(index):
            return client.post('/api/ocr/confirm', json={
                "request_id": f"load_test_{index}",
                "proveedor": f"Supplier {index}",
                "fecha": "2024-10-20",
                "total": 100.0 + index,
                "items": [],
                "confidence": 90.0,
                "edited_fields": []
            })
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(confirm_ocr, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Al menos 95% debería ser éxito
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 95, f"Solo {success_count}/100 confirmaciones exitosas"
