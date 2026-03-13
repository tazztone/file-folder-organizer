import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import numpy as np
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
from pro_file_organizer.core.ml_organizer import MultimodalFileOrganizer

class TestMultimodalFileOrganizer(unittest.TestCase):

    def setUp(self):
        # Configure the mock model to return dummy embeddings
        self.mock_text_model = MagicMock()
        # Mock encode to return a numpy array of ones
        self.mock_text_model.encode.return_value = MagicMock()

        # Patch SentenceTransformer to return our mock
        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer', return_value=self.mock_text_model):
             # Patch AutoModel/Processor
             with patch('pro_file_organizer.core.ml_organizer.AutoModel') as mock_auto_model:
                 with patch('pro_file_organizer.core.ml_organizer.AutoProcessor') as mock_auto_processor:
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

    def test_extract_text_pdf_success(self):
        # Mock pypdf
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "pdf content"
        mock_reader.pages = [mock_page]
        
        with patch('pro_file_organizer.core.ml_organizer.pypdf.PdfReader', return_value=mock_reader):
            text = self.organizer.extract_text(Path("test.pdf"))
            self.assertEqual(text, "pdf content\n")

    def test_extract_text_pdf_error(self):
        with patch('pro_file_organizer.core.ml_organizer.pypdf.PdfReader', side_effect=Exception("PDF Error")):
            text = self.organizer.extract_text(Path("error.pdf"))
            self.assertEqual(text, "")

    def test_extract_text_docx_success(self):
        # Mock docx
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "docx content"
        mock_doc.paragraphs = [mock_para]
        
        with patch('pro_file_organizer.core.ml_organizer.docx.Document', return_value=mock_doc):
            text = self.organizer.extract_text(Path("test.docx"))
            self.assertEqual(text, "docx content")

    def test_extract_text_docx_error(self):
        with patch('pro_file_organizer.core.ml_organizer.docx.Document', side_effect=Exception("Docx Error")):
            text = self.organizer.extract_text(Path("error.docx"))
            self.assertEqual(text, "")

    def test_extract_text_unsupported(self):
        text = self.organizer.extract_text(Path("unsupported.exe"))
        self.assertEqual(text, "")

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
        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available', return_value=True):
            dev = self.organizer._get_device()
            self.assertEqual(dev, "cuda")

        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available', return_value=False):
            with patch('pro_file_organizer.core.ml_organizer.torch.backends.mps.is_available', return_value=True):
                dev = self.organizer._get_device()
                self.assertEqual(dev, "mps")

        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available', return_value=False):
            with patch('pro_file_organizer.core.ml_organizer.torch.backends.mps.is_available', return_value=False):
                dev = self.organizer._get_device()
                self.assertEqual(dev, "cpu")

    def test_are_models_present_success(self):
        with patch('transformers.AutoConfig.from_pretrained', return_value=MagicMock()):
            self.assertTrue(self.organizer.are_models_present())

    def test_are_models_present_failure(self):
        with patch('transformers.AutoConfig.from_pretrained', side_effect=Exception("Missing")):
            self.assertFalse(self.organizer.are_models_present())

    def test_load_models_success(self):
        # Mocking the actual model loading
        self.organizer.models_loaded = False
        mock_callback = MagicMock()
        
        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer', return_value=self.mock_text_model):
            with patch('pro_file_organizer.core.ml_organizer.AutoModel.from_pretrained'):
                with patch('pro_file_organizer.core.ml_organizer.AutoProcessor.from_pretrained'):
                    self.organizer.load_models(progress_callback=mock_callback)
                    
                    self.assertTrue(self.organizer.models_loaded)
                    mock_callback.assert_called()
                    # Verify it calls Precompute
                    self.assertIn("Images/Personal", self.organizer.text_category_embeddings)

    def test_load_models_already_loaded(self):
        self.organizer.models_loaded = True
        mock_callback = MagicMock()
        self.organizer.load_models(progress_callback=mock_callback)
        mock_callback.assert_called_with("Models already loaded.", 1.0)

    def test_load_models_error(self):
        self.organizer.models_loaded = False
        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer', side_effect=Exception("Load Fail")):
            with self.assertRaises(Exception):
                self.organizer.load_models()

    def test_precompute_no_config(self):
        self.organizer.categories_config = None
        self.organizer.text_category_embeddings = {"old": "data"}
        self.organizer._precompute_text_embeddings()
        self.assertEqual(self.organizer.text_category_embeddings, {})

    def test_smart_categorize_not_loaded(self):
        self.organizer.models_loaded = False
        cat, conf, method = self.organizer.smart_categorize(Path("test.txt"))
        self.assertEqual(method, "ml-not-loaded")

    def test_categorize_text_file_empty(self):
        # Testing empty content branch
        cat, conf = self.organizer.categorize_text_file(Path("empty.txt"), "  ")
        self.assertIsNone(cat)
        self.assertEqual(conf, 0.0)

    def test_categorize_image_no_labels(self):
        # Testing image with no visual labels in config
        self.organizer.categories_config = {"NoVisual": {"text": "only"}}
        cat, conf = self.organizer.categorize_image(Path("img.jpg"))
        self.assertIsNone(cat)
        self.assertEqual(conf, 0.0)

    def test_categorize_image_error(self):
        # Testing generic error in image categorization
        with patch('pro_file_organizer.core.ml_organizer.Image.open', side_effect=Exception("Open Fail")):
            cat, conf = self.organizer.categorize_image(Path("bad.jpg"))
            self.assertIsNone(cat)
            self.assertEqual(conf, 0.0)

    def test_categorize_text_file_low_sim(self):
        # Mocking low similarity
        self.organizer.extract_text = MagicMock(return_value="random text")
        # Ensure it doesn't match well
        with patch.object(self.mock_text_model, 'encode', return_value=np.zeros(384)):
             cat, conf, method = self.organizer.smart_categorize(Path("test.txt"))
             self.assertEqual(method, "extension")

    def test_smart_categorize_extensions(self):
        # Testing the extension-only path for non-ml extensions
        # .zip is not in ml extensions list in smart_categorize
        cat, conf, method = self.organizer.smart_categorize(Path("data.zip"))
        self.assertEqual(method, "extension")
        self.assertEqual(conf, 0.0)

    def test_ensure_models(self):
        self.organizer.models_loaded = False
        with patch.object(self.organizer, 'load_models') as mock_load:
            self.organizer.ensure_models()
            mock_load.assert_called_once()

    def test_categorize_image_not_loaded(self):
        self.organizer.models_loaded = False
        cat, conf = self.organizer.categorize_image(Path("img.jpg"))
        self.assertIsNone(cat)
        self.assertEqual(conf, 0.0)

    def test_categorize_image_logic(self):
        # Mock processor output
        mock_inputs = {"pixel_values": MagicMock()}
        self.organizer.image_processor.return_value = MagicMock()
        self.organizer.image_processor.return_value.to.return_value = mock_inputs
        
        # Mock model output
        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = [MagicMock()]
        self.organizer.image_model.return_value = mock_outputs
        
        # Mock probs behavior
        mock_probs = MagicMock()
        mock_probs.argmax.return_value.item.return_value = 1
        mock_probs.__getitem__.return_value.item.return_value = 0.99
        
        with patch('pro_file_organizer.core.ml_organizer.Image.open', return_value=MagicMock()):
            with patch('pro_file_organizer.core.ml_organizer.torch.no_grad'):
                 with patch('pro_file_organizer.core.ml_organizer.torch.sigmoid', return_value=mock_probs):
                     cat, conf = self.organizer.categorize_image(Path("test.jpg"))
                     self.assertEqual(cat, "Documents/Code")
                     self.assertEqual(conf, 0.99)

    @patch('pro_file_organizer.core.ml_organizer.np.dot')
    @patch('pro_file_organizer.core.ml_organizer.np.linalg.norm')
    def test_categorize_text_file_full(self, mock_norm, mock_dot):
        # Even more robust: mock the math directly to return floats
        mock_dot.return_value = 1.0
        mock_norm.return_value = 1.0
        self.mock_text_model.encode.return_value = np.array([1.0])
        
        self.organizer.text_category_embeddings = {"Images/Personal": np.array([1.0])}
        
        cat, conf = self.organizer.categorize_text_file(Path("test.txt"), "some content")
        self.assertEqual(cat, "Images/Personal")
        self.assertAlmostEqual(conf, 1.0, places=5)

    def test_extract_text_general_exception(self):
        # Trigger the outer except Exception as e in extract_text
        with patch("pro_file_organizer.core.ml_organizer.Path.suffix", side_effect=Exception("Outer Error")):
            text = self.organizer.extract_text(Path("test.txt"))
            self.assertEqual(text, "")

if __name__ == '__main__':
    unittest.main()
