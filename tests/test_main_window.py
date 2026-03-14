import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_ui_mocks

# Apply standardized mocks
mock_ctk, mock_dnd = get_ui_mocks()
sys.modules['customtkinter'] = mock_ctk
sys.modules['tkinterdnd2'] = mock_dnd

# Reload main_window
import pro_file_organizer.ui.main_window  # noqa: E402

importlib.reload(pro_file_organizer.ui.main_window)
from pro_file_organizer.ui.main_window import OrganizerApp  # noqa: E402


class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch('pro_file_organizer.ui.main_window.FileOrganizer'),
            patch('pro_file_organizer.ui.main_window.MultimodalFileOrganizer'),
            patch('pro_file_organizer.ui.main_window.MainWindowController'),
            patch('pro_file_organizer.ui.main_window.SettingsDialog'),
            patch('pro_file_organizer.ui.main_window.BatchDialog'),
            patch('pro_file_organizer.ui.main_window.messagebox'),
            patch('pro_file_organizer.ui.main_window.filedialog')
        ]
        self.mocks = [p.start() for p in self.patchers]
        self.app = OrganizerApp()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_init(self):
        self.assertIsNotNone(self.app.controller)

    def test_update_folder_display(self):
        self.app.update_folder_display("/tmp/test")
        self.assertEqual(self.app.lbl_drop.cget("text"), "Selected: test")
        self.assertEqual(self.app.btn_run.cget("state"), "normal")

    def test_clear_results(self):
        mock_child = MagicMock()
        self.app.scroll_results.winfo_children.return_value = [mock_child]
        self.app.clear_results()
        mock_child.destroy.assert_called()

    def test_show_status(self):
        self.app.show_status("Busy...")
        self.assertEqual(self.app.lbl_status.cget("text"), "Busy...")

    def test_update_progress(self):
        # Numeric progress
        self.app.update_progress(5, 10, "file.txt")
        self.app.progress_bar.set.assert_called_with(0.5)

        # Float progress (ML loading)
        self.app.update_progress(0.7, 1.0, "Model Loading")
        self.app.progress_bar.set.assert_called_with(0.7)

    def test_ui_toggles(self):
        self.app.enable_ai_ui()
        self.app.frame_ai_conf.pack.assert_called()

        self.app.disable_ai_ui()
        self.app.frame_ai_conf.pack_forget.assert_called()

    def test_set_running_state(self):
        self.app.set_running_state(True)
        self.assertEqual(self.app.btn_run.cget("state"), "disabled")
        self.assertEqual(self.app.scroll_results.cget("label_text"), "Processing...")

    def test_open_dialogs(self):
        self.app.open_settings()
        self.app.controller.open_settings.assert_called()

        self.app.open_batch()
        self.app.controller.open_batch.assert_called()

    def test_change_appearance(self):
        with patch('pro_file_organizer.ui.main_window.ctk.set_appearance_mode') as mock_set:
            self.app.change_appearance_mode_event("Dark")
            mock_set.assert_called_with("Dark")
            self.app.organizer.save_theme_mode.assert_called_with("Dark")

    def test_on_drop(self):
        event = MagicMock()
        event.data = "/tmp/drop"
        self.app.on_drop(event)
        self.app.controller.set_folder.assert_called_with("/tmp/drop")

        # Braced path
        event.data = "{/tmp/spaced path}"
        self.app.on_drop(event)
        self.app.controller.set_folder.assert_called_with("/tmp/spaced path")

if __name__ == '__main__':
    unittest.main()
