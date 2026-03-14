import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Mock dependencies before importing ml_organizer
sys.modules["transformers"] = MagicMock()
sys.modules["transformers"].AutoConfig = MagicMock()
sys.modules["transformers"].AutoModel = MagicMock()
sys.modules["transformers"].AutoProcessor = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["pypdf"] = MagicMock()
sys.modules["docx"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.metrics"] = MagicMock()
sys.modules["sklearn.metrics.pairwise"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.sparse"] = MagicMock()

# Now import the module to test
from pro_file_organizer.core.ml_organizer import MultimodalFileOrganizer


class TestMultimodalFileOrganizer(unittest.TestCase):
    def setUp(self):
        try:
            import numpy as np
        except ImportError:
            np = MagicMock()

        self.mock_text_model = MagicMock()
        self.mock_text_model.encode.return_value = np.ones(384)

        # Create organizer and manually populate mock modules as it would happen in load_models
        self.organizer = MultimodalFileOrganizer(
            categories_config={
                "Images/Personal": {"text": "desc", "visual": ["label"]},
                "Documents/Code": {"text": "code", "visual": ["code"]},
            }
        )

        # Populate the instance with mocks for most tests
        self.organizer.SentenceTransformer = MagicMock(return_value=self.mock_text_model)
        self.organizer.AutoModel = MagicMock()
        self.organizer.AutoProcessor = MagicMock()
        self.organizer.torch = MagicMock()
        self.organizer.np = np
        self.organizer.Image = MagicMock()
        self.organizer.pypdf = MagicMock()
        self.organizer.docx = MagicMock()

        self.organizer.text_model = self.mock_text_model
        self.organizer.image_model = self.organizer.AutoModel.from_pretrained.return_value
        self.organizer.image_processor = self.organizer.AutoProcessor.from_pretrained.return_value
        self.organizer.models_loaded = True

    def test_precompute_text_embeddings(self):
        self.organizer.text_category_embeddings = {}
        self.organizer._precompute_text_embeddings()
        self.assertIn("Images/Personal", self.organizer.text_category_embeddings)
        self.assertIn("Documents/Code", self.organizer.text_category_embeddings)
        self.mock_text_model.encode.assert_called()

    def test_get_device_cuda(self):
        self.organizer.torch.cuda.is_available.return_value = True
        self.assertEqual(self.organizer._get_device(), "cuda")

    def test_get_device_mps(self):
        self.organizer.torch.cuda.is_available.return_value = False
        self.organizer.torch.backends.mps.is_available.return_value = True
        self.assertEqual(self.organizer._get_device(), "mps")

    def test_get_device_cpu(self):
        self.organizer.torch.cuda.is_available.return_value = False
        self.organizer.torch.backends.mps.is_available.return_value = False
        self.assertEqual(self.organizer._get_device(), "cpu")

    def test_models_exist(self):
        import sys
        with patch("sys.modules", dict(sys.modules)):
            mock_hf = MagicMock()
            sys.modules["huggingface_hub"] = mock_hf
            mock_hf.try_to_load_from_cache.return_value = "/tmp/path"
            self.assertTrue(self.organizer.models_exist())
            mock_hf.try_to_load_from_cache.return_value = None
            self.assertFalse(self.organizer.models_exist())

    def test_extract_text_variations(self):
        # JSON
        with patch("builtins.open", mock_open(read_data='{"test": 1}')):
            self.assertEqual(self.organizer.extract_text(Path("test.json")), '{"test": 1}')

        # PDF Success
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "pdf content"
        mock_reader.pages = [mock_page]
        self.organizer.pypdf.PdfReader.return_value = mock_reader
        text = self.organizer.extract_text(Path("test.pdf"))
        self.assertEqual(text, "pdf content\n")

        # PDF Error
        self.organizer.pypdf.PdfReader.side_effect = Exception("PDF Error")
        self.assertEqual(self.organizer.extract_text(Path("test.pdf")), "")
        self.organizer.pypdf.PdfReader.side_effect = None  # Reset

        # DOCX Success
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "docx content"
        mock_doc.paragraphs = [mock_para]
        self.organizer.docx.Document.return_value = mock_doc
        text = self.organizer.extract_text(Path("test.docx"))
        self.assertEqual(text, "docx content")

        # DOCX Error
        self.organizer.docx.Document.side_effect = Exception("Docx Error")
        self.assertEqual(self.organizer.extract_text(Path("test.docx")), "")
        self.organizer.docx.Document.side_effect = None

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
        self.organizer.image_processor.to.return_value = mock_inputs

        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = [MagicMock()]
        self.organizer.image_model.return_value = mock_outputs

        mock_probs = MagicMock()
        mock_probs.argmax.return_value.item.return_value = 1
        mock_probs[1].item.return_value = 0.95

        self.organizer.Image.open.return_value = MagicMock()
        self.organizer.torch.no_grad.return_value = MagicMock()
        self.organizer.torch.sigmoid.return_value = mock_probs

        cat, conf = self.organizer.categorize_image(Path("test.jpg"))
        self.assertEqual(cat, "Documents/Code")
        self.assertEqual(conf, 0.95)

    def test_categorize_image_error(self):
        self.organizer.Image.open.side_effect = Exception("Open Error")
        cat, conf = self.organizer.categorize_image(Path("bad.jpg"))
        self.assertIsNone(cat)
        self.organizer.Image.open.side_effect = None

    def test_categorize_text_file_logic_extended(self):
        try:
            import numpy as np
        except ImportError:
            np = MagicMock()

        content = "This is a long enough content to pass the 10 char check."
        self.organizer.text_category_embeddings = {"Images/Personal": np.array([1.0, 0.0])}

        with patch.object(self.mock_text_model, "encode", return_value=np.array([1.0, 0.0])):
            cat, conf = self.organizer.categorize_text_file(Path("test.txt"), content)
            self.assertEqual(cat, "Images/Personal")
            self.assertAlmostEqual(conf, 1.0)

        # Exception
        with patch.object(self.mock_text_model, "encode", side_effect=Exception("Encode fail")):
            cat, conf = self.organizer.categorize_text_file(Path("test.txt"), content)
            self.assertIsNone(cat)

    def test_smart_categorize_branches(self):
        # Not loaded
        self.organizer.models_loaded = False
        cat, conf, method = self.organizer.smart_categorize(Path("test.txt"))
        self.assertEqual(method, "ml-not-loaded")

        self.organizer.models_loaded = True

        # Image success
        with patch.object(self.organizer, "categorize_image", return_value=("Images/Personal", 0.9)):
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
        # Since we use local imports, we patch the modules themselves
        with patch("sentence_transformers.SentenceTransformer", return_value=self.mock_text_model):
            with patch("transformers.AutoModel"):
                with patch("transformers.AutoProcessor"):
                    success = self.organizer.load_models(progress_callback=MagicMock())
                    self.assertTrue(success)
                    self.assertTrue(self.organizer.models_loaded)
                    self.assertIsNotNone(self.organizer.torch)

    def test_load_models_already_loaded(self):
        self.organizer.models_loaded = True
        cb = MagicMock()
        self.organizer.load_models(progress_callback=cb)
        cb.assert_called_with("Models already loaded.", 1.0)

    def test_load_models_error(self):
        self.organizer.models_loaded = False
        # Trigger an exception inside load_models
        with patch.object(self.organizer, "_get_device", side_effect=Exception("Load Fail")):
            success = self.organizer.load_models()
            self.assertFalse(success)

    def test_ensure_models(self):
        with patch.object(self.organizer, "load_models") as mock_load:
            self.organizer.ensure_models()
            mock_load.assert_called()


if __name__ == "__main__":
    unittest.main()
