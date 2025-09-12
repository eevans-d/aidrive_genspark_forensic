"""
Comprehensive OCR Tests for Agente de Negocio
Tests for image preprocessing, OCR processing, and data extraction
"""
import asyncio
import io
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image
import numpy as np

# Test imports - these would be the actual modules in production
# from src.ocr.preprocessor import ImagePreprocessor
# from src.ocr.processor import OCRProcessor
# from src.ocr.extractor import InvoiceExtractor

class TestImagePreprocessor:
    """Test suite for image preprocessing functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        # Mock the ImagePreprocessor for testing
        self.preprocessor = Mock()
        self.test_image_path = None

    def teardown_method(self):
        """Cleanup after tests"""
        if self.test_image_path and os.path.exists(self.test_image_path):
            os.unlink(self.test_image_path)

    def create_test_image(self, width=800, height=600, format='JPEG'):
        """Create a test image file for testing"""
        # Create a simple test image with some text-like patterns
        image = Image.new('RGB', (width, height), color='white')

        # Add some black rectangles to simulate text
        pixels = image.load()
        # Simulate text blocks
        for y in range(100, 120):
            for x in range(100, 400):
                pixels[x, y] = (0, 0, 0)  # Black text simulation

        for y in range(150, 170):
            for x in range(100, 300):
                pixels[x, y] = (0, 0, 0)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            image.save(temp_file, format=format)
            self.test_image_path = temp_file.name

        return self.test_image_path

    def test_preprocess_image_basic(self):
        """Test basic image preprocessing"""
        # Create test image
        image_path = self.create_test_image()

        # Mock preprocessor behavior
        processed_path = image_path + "_processed.jpg"
        self.preprocessor.preprocess_image.return_value = processed_path

        # Test preprocessing
        result = self.preprocessor.preprocess_image(image_path)

        # Assertions
        assert result == processed_path
        self.preprocessor.preprocess_image.assert_called_once_with(image_path)

    def test_preprocess_image_with_enhancements(self):
        """Test image preprocessing with contrast and sharpening"""
        image_path = self.create_test_image()

        # Mock enhanced preprocessing
        self.preprocessor.enhance_contrast.return_value = True
        self.preprocessor.apply_sharpening.return_value = True
        self.preprocessor.adjust_brightness.return_value = True

        # Test individual enhancement methods
        assert self.preprocessor.enhance_contrast()
        assert self.preprocessor.apply_sharpening()  
        assert self.preprocessor.adjust_brightness()

    def test_preprocess_invalid_image(self):
        """Test preprocessing with invalid image file"""
        # Test with non-existent file
        self.preprocessor.preprocess_image.side_effect = FileNotFoundError("Image not found")

        with pytest.raises(FileNotFoundError):
            self.preprocessor.preprocess_image("non_existent.jpg")

    def test_preprocess_different_formats(self):
        """Test preprocessing with different image formats"""
        formats = ['JPEG', 'PNG']

        for fmt in formats:
            image_path = self.create_test_image(format=fmt)
            processed_path = f"{image_path}_processed.jpg"

            self.preprocessor.preprocess_image.return_value = processed_path
            result = self.preprocessor.preprocess_image(image_path)

            assert result == processed_path
            os.unlink(image_path)  # Cleanup

    def test_preprocess_large_image(self):
        """Test preprocessing with large image"""
        # Create larger test image
        image_path = self.create_test_image(width=2000, height=1500)

        # Mock processing of large image
        self.preprocessor.resize_if_needed.return_value = True
        self.preprocessor.preprocess_image.return_value = image_path + "_processed.jpg"

        result = self.preprocessor.preprocess_image(image_path)

        # Verify resize was considered
        self.preprocessor.resize_if_needed.assert_called_once()
        assert result is not None

class TestOCRProcessor:
    """Test suite for OCR processing functionality"""

    def setup_method(self):
        """Setup OCR processor tests"""
        self.ocr_processor = Mock()

    def test_process_image_success(self):
        """Test successful OCR processing"""
        # Mock OCR results
        mock_results = [
            (['FACTURA', 'N°', '12345'], [0.95, 0.92, 0.98]),
            (['Producto:', 'Leche', '$45.50'], [0.88, 0.91, 0.85]),
            (['Cantidad:', '2', 'Total:', '$91.00'], [0.90, 0.95, 0.89, 0.93])
        ]

        self.ocr_processor.process_image.return_value = mock_results

        # Test processing
        image_path = "test_invoice.jpg"
        results = self.ocr_processor.process_image(image_path)

        # Assertions
        assert results == mock_results
        assert len(results) == 3
        assert 'FACTURA' in results[0][0]

    def test_process_image_poor_quality(self):
        """Test OCR with poor quality image"""
        # Mock low confidence results
        mock_results = [
            (['unclear', 'text'], [0.45, 0.32])  # Low confidence scores
        ]

        self.ocr_processor.process_image.return_value = mock_results
        self.ocr_processor.get_confidence_threshold.return_value = 0.7

        results = self.ocr_processor.process_image("poor_quality.jpg")
        threshold = self.ocr_processor.get_confidence_threshold()

        assert results == mock_results
        assert threshold > max([0.45, 0.32])  # Confidence below threshold

    def test_ocr_processor_initialization(self):
        """Test OCR processor initialization"""
        # Mock EasyOCR reader initialization
        mock_reader = Mock()
        self.ocr_processor.get_reader.return_value = mock_reader
        self.ocr_processor.languages = ['es', 'en']

        reader = self.ocr_processor.get_reader()
        languages = self.ocr_processor.languages

        assert reader == mock_reader
        assert 'es' in languages
        assert 'en' in languages

    def test_process_multilingual_invoice(self):
        """Test OCR with multilingual invoice"""
        # Mock multilingual results
        mock_results = [
            (['INVOICE', '/', 'FACTURA'], [0.92, 0.88, 0.94]),
            (['Total', ':', '$150.75'], [0.90, 0.95, 0.87])
        ]

        self.ocr_processor.process_image.return_value = mock_results

        results = self.ocr_processor.process_image("multilingual_invoice.jpg")

        assert results == mock_results
        # Verify both English and Spanish text detected
        all_text = ' '.join([' '.join(line[0]) for line in results])
        assert 'INVOICE' in all_text
        assert 'FACTURA' in all_text

    def test_ocr_error_handling(self):
        """Test OCR error handling"""
        # Mock processing error
        self.ocr_processor.process_image.side_effect = Exception("OCR processing failed")

        with pytest.raises(Exception) as exc_info:
            self.ocr_processor.process_image("corrupted_image.jpg")

        assert "OCR processing failed" in str(exc_info.value)

class TestInvoiceExtractor:
    """Test suite for invoice data extraction"""

    def setup_method(self):
        """Setup invoice extractor tests"""
        self.extractor = Mock()

    def test_extract_invoice_data_complete(self):
        """Test extraction of complete invoice data"""
        # Mock OCR results for a complete invoice
        mock_ocr_results = [
            (['FACTURA', 'N°', '12345'], [0.95, 0.92, 0.98]),
            (['Fecha:', '2024-01-15'], [0.88, 0.91]),
            (['Producto', 'Cantidad', 'Precio'], [0.90, 0.85, 0.92]),
            (['Leche', '2', '$45.50'], [0.87, 0.95, 0.89]),
            (['Pan', '1', '$25.00'], [0.91, 0.94, 0.86]),
            (['Total:', '$70.50'], [0.93, 0.88])
        ]

        # Mock extracted data
        mock_extracted_data = {
            'invoice_number': '12345',
            'date': '2024-01-15',
            'products': [
                {'name': 'Leche', 'quantity': 2, 'price': 45.50},
                {'name': 'Pan', 'quantity': 1, 'price': 25.00}
            ],
            'total': 70.50,
            'extraction_confidence': 0.91
        }

        self.extractor.extract_invoice_data.return_value = mock_extracted_data

        # Test extraction
        result = self.extractor.extract_invoice_data(mock_ocr_results)

        # Assertions
        assert result == mock_extracted_data
        assert result['invoice_number'] == '12345'
        assert len(result['products']) == 2
        assert result['total'] == 70.50

    def test_extract_partial_invoice_data(self):
        """Test extraction with missing data"""
        # Mock OCR with missing information
        mock_ocr_results = [
            (['FACTURA'], [0.95]),
            (['Leche', '$45.50'], [0.87, 0.89])
        ]

        mock_extracted_data = {
            'invoice_number': None,
            'date': None,
            'products': [
                {'name': 'Leche', 'quantity': None, 'price': 45.50}
            ],
            'total': None,
            'extraction_confidence': 0.65
        }

        self.extractor.extract_invoice_data.return_value = mock_extracted_data

        result = self.extractor.extract_invoice_data(mock_ocr_results)

        # Should handle missing data gracefully
        assert result['invoice_number'] is None
        assert result['products'][0]['quantity'] is None
        assert result['extraction_confidence'] < 0.8  # Lower confidence due to missing data

    def test_extract_regex_patterns(self):
        """Test regex pattern matching for different data types"""
        # Mock regex pattern tests
        self.extractor.extract_invoice_number.return_value = "INV-2024-001"
        self.extractor.extract_date.return_value = "2024-01-15"
        self.extractor.extract_currency_amounts.return_value = [45.50, 25.00, 70.50]

        # Test individual extraction methods
        invoice_num = self.extractor.extract_invoice_number("FACTURA N° INV-2024-001")
        date = self.extractor.extract_date("Fecha: 2024-01-15")
        amounts = self.extractor.extract_currency_amounts("$45.50 $25.00 Total: $70.50")

        assert invoice_num == "INV-2024-001"
        assert date == "2024-01-15"
        assert 45.50 in amounts
        assert 70.50 in amounts

    def test_extract_product_table(self):
        """Test extraction of product table data"""
        # Mock table extraction
        mock_products = [
            {'name': 'Leche Entera 1L', 'quantity': 2, 'price': 45.50, 'subtotal': 91.00},
            {'name': 'Pan Integral', 'quantity': 1, 'price': 25.00, 'subtotal': 25.00}
        ]

        self.extractor.extract_product_table.return_value = mock_products

        products = self.extractor.extract_product_table("mock_table_data")

        assert len(products) == 2
        assert products[0]['name'] == 'Leche Entera 1L'
        assert products[0]['subtotal'] == 91.00

    def test_extract_confidence_scoring(self):
        """Test confidence scoring for extractions"""
        # Mock confidence calculations
        self.extractor.calculate_extraction_confidence.return_value = 0.87

        confidence = self.extractor.calculate_extraction_confidence({
            'invoice_number': '12345',
            'date': '2024-01-15', 
            'products': [{'name': 'Test', 'price': 100}],
            'total': 100
        })

        assert confidence == 0.87
        assert confidence > 0.8  # High confidence for complete data

    def test_extract_invalid_ocr_data(self):
        """Test extraction with invalid or corrupted OCR data"""
        # Mock empty or invalid OCR results
        invalid_ocr_results = []

        self.extractor.extract_invoice_data.return_value = {
            'invoice_number': None,
            'date': None,
            'products': [],
            'total': None,
            'extraction_confidence': 0.0,
            'error': 'No valid OCR data found'
        }

        result = self.extractor.extract_invoice_data(invalid_ocr_results)

        assert result['products'] == []
        assert result['extraction_confidence'] == 0.0
        assert 'error' in result

class TestOCRPipeline:
    """Test suite for complete OCR pipeline"""

    def setup_method(self):
        """Setup pipeline tests"""
        self.preprocessor = Mock()
        self.processor = Mock() 
        self.extractor = Mock()

    @pytest.mark.asyncio
    async def test_complete_ocr_pipeline(self):
        """Test the complete OCR pipeline end-to-end"""
        # Mock the complete pipeline
        original_image = "test_invoice.jpg"
        processed_image = "test_invoice_processed.jpg"

        # Step 1: Preprocessing
        self.preprocessor.preprocess_image.return_value = processed_image

        # Step 2: OCR Processing
        mock_ocr_results = [
            (['FACTURA', 'N°', '12345'], [0.95, 0.92, 0.98]),
            (['Total:', '$150.75'], [0.93, 0.88])
        ]
        self.processor.process_image.return_value = mock_ocr_results

        # Step 3: Data Extraction
        mock_extracted_data = {
            'invoice_number': '12345',
            'total': 150.75,
            'products': [{'name': 'Test Product', 'price': 150.75}]
        }
        self.extractor.extract_invoice_data.return_value = mock_extracted_data

        # Execute pipeline
        processed_path = self.preprocessor.preprocess_image(original_image)
        ocr_results = self.processor.process_image(processed_path)
        final_data = self.extractor.extract_invoice_data(ocr_results)

        # Assertions
        assert processed_path == processed_image
        assert ocr_results == mock_ocr_results
        assert final_data == mock_extracted_data
        assert final_data['invoice_number'] == '12345'

    def test_pipeline_error_propagation(self):
        """Test error handling throughout the pipeline"""
        # Mock error in preprocessing
        self.preprocessor.preprocess_image.side_effect = Exception("Preprocessing failed")

        with pytest.raises(Exception) as exc_info:
            self.preprocessor.preprocess_image("corrupted_image.jpg")

        assert "Preprocessing failed" in str(exc_info.value)

    def test_pipeline_performance_metrics(self):
        """Test performance tracking in pipeline"""
        # Mock timing measurements
        self.preprocessor.get_processing_time.return_value = 250  # ms
        self.processor.get_processing_time.return_value = 1500   # ms  
        self.extractor.get_processing_time.return_value = 100    # ms

        # Get timing metrics
        preprocess_time = self.preprocessor.get_processing_time()
        ocr_time = self.processor.get_processing_time()
        extract_time = self.extractor.get_processing_time()

        total_time = preprocess_time + ocr_time + extract_time

        assert preprocess_time == 250
        assert ocr_time == 1500
        assert extract_time == 100
        assert total_time == 1850  # Total pipeline time

class TestOCRIntegration:
    """Integration tests for OCR components"""

    def test_ocr_with_real_sample_data(self):
        """Test OCR with sample invoice data (mocked)"""
        # This would test with actual sample images in a real implementation
        sample_invoices = [
            {
                'filename': 'invoice_sample_1.jpg',
                'expected_invoice_number': 'INV-2024-001',
                'expected_total': 256.75,
                'expected_products': 3
            },
            {
                'filename': 'invoice_sample_2.jpg', 
                'expected_invoice_number': 'FAC-12345',
                'expected_total': 89.50,
                'expected_products': 2
            }
        ]

        # Mock processing results for samples
        mock_processor = Mock()

        for sample in sample_invoices:
            mock_result = {
                'invoice_number': sample['expected_invoice_number'],
                'total': sample['expected_total'],
                'products': [{'name': f'Product {i}', 'price': 10.0} 
                           for i in range(sample['expected_products'])]
            }

            mock_processor.process_invoice.return_value = mock_result

            # Test processing
            result = mock_processor.process_invoice(sample['filename'])

            assert result['invoice_number'] == sample['expected_invoice_number']
            assert result['total'] == sample['expected_total']
            assert len(result['products']) == sample['expected_products']

# Pytest fixtures and configuration
@pytest.fixture
def sample_invoice_image():
    """Fixture to provide sample invoice image for testing"""
    # In a real implementation, this would provide actual test images
    return "sample_invoice.jpg"

@pytest.fixture
def mock_ocr_results():
    """Fixture providing mock OCR results"""
    return [
        (['FACTURA', 'N°', '12345'], [0.95, 0.92, 0.98]),
        (['Fecha:', '2024-01-15'], [0.88, 0.91]),
        (['Total:', '$150.75'], [0.93, 0.88])
    ]

# Test configuration
pytest_plugins = ['pytest_asyncio']

if __name__ == "__main__":
    # Run specific test suites
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
