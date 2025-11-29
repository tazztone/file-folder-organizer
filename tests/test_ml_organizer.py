import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
from pathlib import Path

# Mock dependencies before importing ml_organizer
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['pypdf'] = MagicMock()
sys.modules['docx'] = MagicMock()
sys.modules['numpy'] = MagicMock()

# Now import the module to test
from ml_organizer import MultimodalFileOrganizer

class TestMultimodalFileOrganizer(unittest.TestCase):

    def setUp(self):
        # Configure the mock model to return dummy embeddings
        self.mock_text_model = MagicMock()
        # Mock encode to return a numpy array of ones
        self.mock_text_model.encode.return_value = MagicMock()

        # Patch SentenceTransformer to return our mock
        with patch('ml_organizer.SentenceTransformer', return_value=self.mock_text_model):
             # Patch AutoModel/Processor
             with patch('ml_organizer.AutoModel') as mock_auto_model:
                 with patch('ml_organizer.AutoProcessor') as mock_auto_processor:
                     self.organizer = MultimodalFileOrganizer(categories_config={
                         "Images/Personal": {"text": "desc", "visual": ["label"]},
                         "Documents/Code": {"text": "code", "visual": ["code"]}
                     })
                     # Simulate load
                     self.organizer.text_model = self.mock_text_model
                     self.organizer.image_model = mock_auto_model.return_value
                     self.organizer.image_processor = mock_auto_processor.return_value
                     self.organizer.models_loaded = True

    def test_extract_text_txt(self):
        # Test basic text extraction
        with patch("builtins.open", mock_open(read_data="content")):
            text = self.organizer.extract_text(Path("test.txt"))
            self.assertEqual(text, "content")

    def test_smart_categorize_image_fallback(self):
        # If confidence is low, should return extension fallback
        # Mock categorize_image to return low confidence
        self.organizer.categorize_image = MagicMock(return_value=("Images/Personal", 0.1))

        cat, conf, method = self.organizer.smart_categorize(Path("photo.jpg"))
        self.assertEqual(method, "extension")

    def test_smart_categorize_image_success(self):
        # If confidence is high
        self.organizer.categorize_image = MagicMock(return_value=("Images/Personal", 0.9))

        cat, conf, method = self.organizer.smart_categorize(Path("photo.jpg"))
        self.assertEqual(cat, "Images/Personal")
        self.assertEqual(method, "image-ml")
        self.assertEqual(conf, 0.9)

    def test_smart_categorize_text_success(self):
        # Mock extract text
        self.organizer.extract_text = MagicMock(return_value="some code content")
        # Mock categorize_text_file
        self.organizer.categorize_text_file = MagicMock(return_value=("Documents/Code", 0.8))

        cat, conf, method = self.organizer.smart_categorize(Path("script.py"))
        self.assertEqual(cat, "Documents/Code")
        self.assertEqual(method, "text-ml")

    def test_device_selection(self):
        # Test device detection logic
        # We need to re-instantiate or test the private method if we can access it,
        # or mock torch.cuda.is_available
        with patch('ml_organizer.torch.cuda.is_available', return_value=True):
            dev = self.organizer._get_device()
            self.assertEqual(dev, "cuda")

        with patch('ml_organizer.torch.cuda.is_available', return_value=False):
            with patch('ml_organizer.torch.backends.mps.is_available', return_value=True):
                dev = self.organizer._get_device()
                self.assertEqual(dev, "mps")

if __name__ == '__main__':
    unittest.main()
