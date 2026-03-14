import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import numpy as np

# Mock dependencies before importing ml_organizer
sys.modules['transformers'] = MagicMock()
sys.modules['transformers'].AutoConfig = MagicMock()
sys.modules['transformers'].AutoModel = MagicMock()
sys.modules['transformers'].AutoProcessor = MagicMock()
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
        self.mock_text_model = MagicMock()
        self.mock_text_model.encode.return_value = np.ones(384)

        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer',
                   return_value=self.mock_text_model):
             with patch('pro_file_organizer.core.ml_organizer.AutoModel') as mock_auto_model:
                 with patch('pro_file_organizer.core.ml_organizer.AutoProcessor') as mock_auto_processor:
                     self.organizer = MultimodalFileOrganizer(categories_config={
                         "Images/Personal": {"text": "desc", "visual": ["label"]},
                         "Documents/Code": {"text": "code", "visual": ["code"]}
                     })
                     self.organizer.text_model = self.mock_text_model
                     self.organizer.image_model = mock_auto_model.return_value
                     self.organizer.image_processor = mock_auto_processor.return_value
                     self.organizer.models_loaded = True

    def test_precompute_text_embeddings(self):
        self.organizer.text_category_embeddings = {}
        self.organizer._precompute_text_embeddings()
        self.assertIn("Images/Personal", self.organizer.text_category_embeddings)
        self.assertIn("Documents/Code", self.organizer.text_category_embeddings)
        self.mock_text_model.encode.assert_called()

    def test_get_device_cuda(self):
        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available', return_value=True):
            self.assertEqual(self.organizer._get_device(), "cuda")

    def test_get_device_mps(self):
        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available',
                   return_value=False):
            with patch('pro_file_organizer.core.ml_organizer.torch.backends.mps.is_available',
                       return_value=True):
                self.assertEqual(self.organizer._get_device(), "mps")

    def test_get_device_cpu(self):
        with patch('pro_file_organizer.core.ml_organizer.torch.cuda.is_available',
                   return_value=False):
            with patch('pro_file_organizer.core.ml_organizer.torch.backends.mps.is_available', return_value=False):
                self.assertEqual(self.organizer._get_device(), "cpu")

    def test_are_models_present(self):
        with patch('transformers.AutoConfig.from_pretrained') as mock_conf:
            mock_conf.return_value = True
            self.assertTrue(self.organizer.are_models_present())
            mock_conf.side_effect = Exception("Not found")
            self.assertFalse(self.organizer.are_models_present())

    def test_extract_text_variations(self):
        # JSON
        with patch("builtins.open", mock_open(read_data='{"test": 1}')):
            self.assertEqual(self.organizer.extract_text(Path("test.json")), '{"test": 1}')

        # PDF Success
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "pdf content"
        mock_reader.pages = [mock_page]
        with patch('pro_file_organizer.core.ml_organizer.pypdf.PdfReader',
                   return_value=mock_reader):
            text = self.organizer.extract_text(Path("test.pdf"))
            self.assertEqual(text, "pdf content\n")

        # PDF Error
        with patch('pro_file_organizer.core.ml_organizer.pypdf.PdfReader', side_effect=Exception("PDF Error")):
            self.assertEqual(self.organizer.extract_text(Path("test.pdf")), "")

        # DOCX Success
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "docx content"
        mock_doc.paragraphs = [mock_para]
        with patch('pro_file_organizer.core.ml_organizer.docx.Document', return_value=mock_doc):
            text = self.organizer.extract_text(Path("test.docx"))
            self.assertEqual(text, "docx content")

        # DOCX Error
        with patch('pro_file_organizer.core.ml_organizer.docx.Document', side_effect=Exception("Docx Error")):
            self.assertEqual(self.organizer.extract_text(Path("test.docx")), "")

        # General Exception
        with patch("builtins.open", side_effect=Exception("IO Error")):
            self.assertEqual(self.organizer.extract_text(Path("test.txt")), "")

    def test_categorize_image_no_models(self):
        self.organizer.models_loaded = False
        cat, conf = self.organizer.categorize_image(Path("test.jpg"))
        self.assertIsNone(cat)
        self.assertEqual(conf, 0.0)

    def test_categorize_image_no_labels(self):
        self.organizer.categories_config = {"NoVisual": {"text": "only"}}
        cat, conf = self.organizer.categorize_image(Path("test.jpg"))
        self.assertIsNone(cat)
        self.assertEqual(conf, 0.0)

    def test_categorize_image_logic(self):
        mock_inputs = MagicMock()
        self.organizer.image_processor.return_value = MagicMock()
        self.organizer.image_processor.return_value.to.return_value = mock_inputs

        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = [MagicMock()]
        self.organizer.image_model.return_value = mock_outputs

        mock_probs = MagicMock()
        mock_probs.argmax.return_value.item.return_value = 1
        mock_probs[1].item.return_value = 0.95

        with patch('pro_file_organizer.core.ml_organizer.Image.open', return_value=MagicMock()):
            with patch('pro_file_organizer.core.ml_organizer.torch.no_grad'):
                with patch('pro_file_organizer.core.ml_organizer.torch.sigmoid', return_value=mock_probs):
                    cat, conf = self.organizer.categorize_image(Path("test.jpg"))
                    self.assertEqual(cat, "Documents/Code")
                    self.assertEqual(conf, 0.95)

    def test_categorize_image_error(self):
        with patch('pro_file_organizer.core.ml_organizer.Image.open', side_effect=Exception("Open Error")):
            cat, conf = self.organizer.categorize_image(Path("bad.jpg"))
            self.assertIsNone(cat)

    def test_categorize_text_file_logic_extended(self):
        content = "This is a long enough content to pass the 10 char check."
        self.organizer.text_category_embeddings = {"Images/Personal": np.array([1.0, 0.0])}
        with patch.object(self.mock_text_model, 'encode', return_value=np.array([1.0, 0.0])):
            cat, conf = self.organizer.categorize_text_file(Path("test.txt"), content)
            self.assertEqual(cat, "Images/Personal")
            self.assertAlmostEqual(conf, 1.0)

        # Exception
        with patch.object(self.mock_text_model, 'encode', side_effect=Exception("Encode fail")):
            cat, conf = self.organizer.categorize_text_file(Path("test.txt"), content)
            self.assertIsNone(cat)

    def test_smart_categorize_branches(self):
        # Not loaded
        self.organizer.models_loaded = False
        cat, conf, method = self.organizer.smart_categorize(Path("test.txt"))
        self.assertEqual(method, "ml-not-loaded")

        self.organizer.models_loaded = True

        # Image success
        with patch.object(self.organizer, 'categorize_image', return_value=("Images/Personal", 0.9)):
            cat, conf, method = self.organizer.smart_categorize(Path("photo.jpg"))
            self.assertEqual(method, "image-ml")

        # Text success
        with patch.object(self.organizer, "extract_text", return_value="some text content"):
            with patch.object(self.organizer, "categorize_text_file", return_value=("Documents/Code", 0.8)):
                cat, conf, method = self.organizer.smart_categorize(Path("script.py"))
                self.assertEqual(method, "text-ml")

        # Fallback
        with patch.object(self.organizer, "extract_text", return_value=""):
            cat, conf, method = self.organizer.smart_categorize(Path("unknown.dat"))
            self.assertEqual(method, "extension")

    def test_load_models_full(self):
        self.organizer.models_loaded = False
        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer', return_value=self.mock_text_model):
            with patch('pro_file_organizer.core.ml_organizer.AutoModel'):
                with patch('pro_file_organizer.core.ml_organizer.AutoProcessor'):
                    self.organizer.load_models(progress_callback=MagicMock())
                    self.assertTrue(self.organizer.models_loaded)

    def test_load_models_already_loaded(self):
        self.organizer.models_loaded = True
        cb = MagicMock()
        self.organizer.load_models(progress_callback=cb)
        cb.assert_called_with("Models already loaded.", 1.0)

    def test_load_models_error(self):
        self.organizer.models_loaded = False
        with patch('pro_file_organizer.core.ml_organizer.SentenceTransformer', side_effect=Exception("Load Fail")):
            with self.assertRaises(Exception):
                self.organizer.load_models()

    def test_ensure_models(self):
        with patch.object(self.organizer, 'load_models') as mock_load:
            self.organizer.ensure_models()
            mock_load.assert_called()

if __name__ == '__main__':
    unittest.main()
