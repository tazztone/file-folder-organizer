import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import importlib
import os
from tests.ui_test_utils import get_ui_mocks

# Apply standardized mocks
mock_ctk, _ = get_ui_mocks()
sys.modules['customtkinter'] = mock_ctk

# Force reload of components
import pro_file_organizer.ui.components.ui_components
importlib.reload(pro_file_organizer.ui.components.ui_components)
from pro_file_organizer.ui.components.ui_components import FileCard, ModelDownloadModal, RedirectedStderr

class TestUIComponents(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()

    def test_file_card_init_variations(self):
        # AI Method
        data = {"file": "test.png", "method": "image-ml", "confidence": 0.85, "destination": "/tmp/dest/file.png"}
        card = FileCard(self.mock_parent, data)
        self.assertEqual(card.lbl_badge.cget("text"), "AI 85%")
        
        # Error type
        data = {"file": "error.txt", "type": "error", "error": "Access Denied"}
        card = FileCard(self.mock_parent, data)
        self.assertEqual(card.lbl_badge.cget("text"), "ERR")
        self.assertIn("Access Denied", card.lbl_dest.cget("text"))

        # Path exception in dest display
        with patch("pro_file_organizer.ui.components.ui_components.Path", side_effect=Exception("Path error")):
            card = FileCard(self.mock_parent, {"file": "f.txt", "destination": "dest"})
            self.assertEqual(card.lbl_dest.cget("text"), "→ dest")

    def test_redirected_stderr_logic(self):
        text_widget = MagicMock()
        text_widget.after = MagicMock(side_effect=lambda t, f: f())
        redirector = RedirectedStderr(text_widget)
        
        # Test write schedules append
        redirector.write("err")
        text_widget.after.assert_called()
        
        # Test _append logic
        redirector._append("new text")
        text_widget.insert.assert_called_with("end", "new text")
        
        # Test \r handling (simple branch coverage)
        redirector._append("\rprogress")
        text_widget.insert.assert_called()
        
        # Test exception safety in append
        text_widget.insert.side_effect = Exception("Insert Error")
        redirector._append("wont crash") # Should pass due to try-except

        # Flush
        redirector.flush()

    def test_model_download_modal_space_checks(self):
        # High space
        with patch("shutil.disk_usage", return_value=(100, 50, 10*1024**3)):
            modal = ModelDownloadModal(self.mock_parent)
            self.assertFalse(hasattr(modal, 'lbl_warn'))

        # Low space
        with patch("shutil.disk_usage", return_value=(100, 98, 2*1024**3)):
            modal = ModelDownloadModal(self.mock_parent)
            self.assertTrue(hasattr(modal, 'lbl_warn'))

        # Exception in space check
        with patch("shutil.disk_usage", side_effect=Exception("Space check error")):
            modal = ModelDownloadModal(self.mock_parent)
            self.assertEqual(modal._get_free_space_gb(), 0.0)

    def test_model_download_modal_lifecycle(self):
        on_complete = MagicMock()
        modal = ModelDownloadModal(self.mock_parent, on_complete)
        
        # Cancel
        modal.on_cancel()
        on_complete.assert_called_with(False)
        modal.destroy.assert_called()
        
        # Reset and Start
        on_complete.reset_mock()
        modal = ModelDownloadModal(self.mock_parent, on_complete)
        with patch('threading.Thread') as mock_thread:
            modal.start_download()
            self.assertTrue(modal.download_started)
            modal.start_download() # Should return immediately
            
        # Mock _download_task completion - Success
        modal.after = MagicMock(side_effect=lambda t, f: f())
        modal._finish_success()
        on_complete.assert_called_with(True)
        
        # Mock _download_task completion - Error
        on_complete.reset_mock()
        modal = ModelDownloadModal(self.mock_parent, on_complete)
        modal.after = MagicMock(side_effect=lambda t, f: f())
        modal._finish_error("Failed")
        on_complete.assert_called_with(False)

    def test_download_task_execution(self):
        modal = ModelDownloadModal(self.mock_parent)
        modal.after = MagicMock()
        # Patch where it's imported
        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer') as mock_org_class:
            mock_org_instance = mock_org_class.return_value
            with patch('pro_file_organizer.ui.components.ui_components.sys.stderr', MagicMock()):
                # Success path
                modal._download_task()
                mock_org_instance.ensure_models.assert_called()
                modal.after.assert_called()
                
                # Error path
                modal.after.reset_mock()
                mock_org_instance.ensure_models.side_effect = Exception("Down error")
                modal._download_task()
                modal.after.assert_called()

if __name__ == '__main__':
    unittest.main()
