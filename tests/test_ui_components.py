import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_pyside_mocks

# Apply standardized mocks
mock_qtwidgets, mock_qtcore, mock_qtgui = get_pyside_mocks()
sys.modules["PySide6.QtWidgets"] = mock_qtwidgets
sys.modules["PySide6.QtCore"] = mock_qtcore
sys.modules["PySide6.QtGui"] = mock_qtgui

# Force reload of components
import pro_file_organizer.ui.components.ui_components  # noqa: E402

importlib.reload(pro_file_organizer.ui.components.ui_components)
from pro_file_organizer.ui.components.ui_components import (  # noqa: E402
    FileCard,
    ModelDownloadModal,
    RedirectedStderr,
)


class TestUIComponents(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()

    def test_file_card_init_variations(self):
        # AI Method
        data = {"file": "test.png", "method": "image-ml", "confidence": 0.85, "destination": "/tmp/dest/file.png"}
        card = FileCard(data, self.mock_parent)
        self.assertEqual(card.lbl_badge.text.return_value, "AI 85%")

        # Error type
        data = {"file": "error.txt", "type": "error", "error": "Access Denied"}
        card = FileCard(data, self.mock_parent)
        self.assertEqual(card.lbl_badge.text.return_value, "ERR")
        self.assertIn("Access Denied", card.lbl_dest.text.return_value)

        # Path exception in dest display
        patch_path = "pro_file_organizer.ui.components.ui_components.Path"
        with patch(patch_path, side_effect=Exception("Path error")):
            card = FileCard({"file": "f.txt", "destination": "dest"}, self.mock_parent)
            self.assertEqual(card.lbl_dest.text.return_value, "→ dest")

    def test_redirected_stderr_logic(self):
        signals = MagicMock()
        redirector = RedirectedStderr(signals)

        # Test write emits signal
        redirector.write("err")
        signals.log_emitted.emit.assert_called_with("err")

        # Flush
        redirector.flush()

    def test_model_download_modal_space_checks(self):
        patch_path = "pro_file_organizer.ui.components.ui_components.shutil.disk_usage"
        # High space
        with patch(patch_path, return_value=(100, 50, 10 * 1024**3)):
            modal = ModelDownloadModal(self.mock_parent)
            print(f"DEBUG: hasattr(modal, 'lbl_warn')={hasattr(modal, 'lbl_warn')}")
            self.assertFalse(hasattr(modal, "lbl_warn"))

        # Low space
        with patch(patch_path, return_value=(100, 98, 2 * 1024**3)):
            modal = ModelDownloadModal(self.mock_parent)
            self.assertTrue(hasattr(modal, "lbl_warn"))

        # Exception in space check
        with patch(patch_path, side_effect=Exception("Space check error")):
            modal = ModelDownloadModal(self.mock_parent)
            self.assertEqual(modal._get_free_space_gb(), 0.0)

    def test_model_download_modal_lifecycle(self):
        on_complete = MagicMock()
        modal = ModelDownloadModal(self.mock_parent, on_complete)

        # Reject/Cancel
        modal.reject()
        on_complete.assert_not_called() # reject doesn't call on_complete(False) in my new impl, it's just destroy
        # Actually I should check my impl of on_download_finished

        # Start
        with patch("threading.Thread"):
            modal.start_download()
            self.assertTrue(modal.download_started)
            modal.start_download()  # Should return immediately

        # Mock _download_task completion - Success
        modal._on_download_finished(True, "")
        on_complete.assert_called_with(True)

        # Mock _download_task completion - Error
        on_complete.reset_mock()
        modal = ModelDownloadModal(self.mock_parent, on_complete)
        modal._on_download_finished(False, "Failed")
        on_complete.assert_called_with(False)

    def test_download_task_execution(self):
        modal = ModelDownloadModal(self.mock_parent)
        # Patch where it's imported
        patch_ml = "pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer"
        with patch(patch_ml) as mock_org_class:
            mock_org_instance = mock_org_class.return_value
            with patch("pro_file_organizer.ui.components.ui_components.sys.stderr", MagicMock()):
                # Success path
                modal._download_task()
                mock_org_instance.ensure_models.assert_called()

                # Error path
                mock_org_instance.ensure_models.side_effect = Exception("Down error")
                modal._download_task()
                # Should emit finished(False, "Down error")
                modal.signals.finished.emit.assert_called_with(False, "Down error")


if __name__ == "__main__":
    unittest.main()
