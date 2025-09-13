
import unittest
import numpy as np
from pathlib import Path
from PIL import Image
import os
import cv2
import sys

# This is a hack to get the project root on the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agente_negocio.ocr.preprocessor import ImagePreprocessor


class TestImagePreprocessor(unittest.TestCase):

    def setUp(self):
        """Set up a test image and preprocessor instance."""
        self.preprocessor = ImagePreprocessor()
        self.test_image_path = "test_image.png"
        self._create_dummy_image(self.test_image_path)

    def tearDown(self):
        """Clean up created files."""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        if os.path.exists("processed_test_image.png"):
            os.remove("processed_test_image.png")

    def _create_dummy_image(self, file_path: str, width: int = 600, height: int = 400):
        """Creates a dummy image for testing."""
        img_array = np.full((height, width, 3), 240, dtype=np.uint8) # Light gray background
        # Add some text to the image to simulate a document
        cv2.putText(img_array, "Test Invoice", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        img = Image.fromarray(img_array)
        img.save(file_path)

    def test_initialization(self):
        """Tests that the preprocessor is initialized with default values."""
        self.assertEqual(self.preprocessor.target_dpi, 300)
        self.assertEqual(self.preprocessor.max_size, (2048, 2048))

    def test_load_image_from_path(self):
        """Tests loading an image from a file path."""
        image = self.preprocessor._load_image(self.test_image_path)
        self.assertIsInstance(image, np.ndarray)
        self.assertEqual(image.shape, (400, 600, 3))

    def test_load_image_from_bytes(self):
        """Tests loading an image from a byte stream."""
        with open(self.test_image_path, "rb") as f:
            image_bytes = f.read()
        image = self.preprocessor._load_image(image_bytes)
        self.assertIsInstance(image, np.ndarray)
        self.assertEqual(image.shape, (400, 600, 3))

    def test_preprocess_image_pipeline(self):
        """Tests the full preprocessing pipeline on a valid image."""
        processed_image = self.preprocessor.preprocess_image(self.test_image_path)
        self.assertIsInstance(processed_image, np.ndarray)
        # The shape might change due to skew correction, so we just check it's a valid image
        self.assertTrue(len(processed_image.shape) == 3)

    def test_preprocess_non_existent_image(self):
        """Tests that preprocessing a non-existent image returns None."""
        processed_image = self.preprocessor.preprocess_image("non_existent_image.png")
        self.assertIsNone(processed_image)

    def test_save_image(self):
        """Tests saving a processed image."""
        output_path = "processed_test_image.png"
        image_array = self.preprocessor._load_image(self.test_image_path)
        result = self.preprocessor.save_processed_image(image_array, output_path)
        self.assertTrue(result)
        self.assertTrue(Path(output_path).exists())

    def test_get_quality_metrics(self):
        """Tests the image quality metrics calculation."""
        image_array = self.preprocessor._load_image(self.test_image_path)
        metrics = self.preprocessor.get_image_quality_metrics(image_array)
        self.assertIsInstance(metrics, dict)
        self.assertIn("brightness", metrics)
        self.assertIn("contrast", metrics)
        self.assertIn("sharpness", metrics)
        self.assertIsInstance(metrics["brightness"], float)

if __name__ == "__main__":
    # Run tests from the 'tests' directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    unittest.main()
