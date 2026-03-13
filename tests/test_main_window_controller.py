import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import os
from pro_file_organizer.ui.main_window_controller import MainWindowController

class TestMainWindowController(unittest.TestCase):
    def setUp(self):
        self.view = MagicMock()
        self.organizer = MagicMock()
        self.ml_organizer = MagicMock()
        
        self.view.confirm_action.return_value = True
        self.view.get_recursive_val.return_value = False
        self.view.get_date_sort_val.return_value = False
        self.view.get_del_empty_val.return_value = False
        self.view.get_ai_confidence.return_value = 0.3

        def side_effect(path, mode='r', *args, **kwargs):
            p_str = str(path)
            if 'stats.json' in p_str:
                return mock_open(read_data='{"total_files": 10, "last_run": "2026-03-13"}')()
            if 'recent.json' in p_str:
                return mock_open(read_data='["/tmp/dir1"]')()
            return mock_open()()

        with patch("builtins.open", side_effect=side_effect):
            with patch("pathlib.Path.exists", return_value=True):
                self.controller = MainWindowController(self.view, self.organizer, self.ml_organizer)

    def test_init_loads_stats_and_recent(self):
        self.assertEqual(self.controller.stats.get("total_files"), 10)
        self.assertIn("/tmp/dir1", self.controller.recent_folders)

    def test_toggle_ai_download_needed(self):
        self.ml_organizer.models_exist.return_value = False
        self.view.confirm_action.return_value = True
        self.controller.toggle_ai(True)
        self.view.show_model_download.assert_called()

    @patch('pro_file_organizer.ui.main_window_controller.datetime')
    def test_on_complete_success(self, mock_dt):
        mock_dt.now.return_value.strftime.return_value = "2026-03-13 22:00"
        self.controller.stats = {"total_files": 0, "last_run": "Never"}
        with patch("builtins.open", mock_open()):
            self.controller._on_complete({"moved": 5, "errors": 0}, dry_run=False)
            self.assertEqual(self.controller.stats["total_files"], 5)
            self.view.update_stats_display.assert_called()

    def test_select_folder(self):
        # Patch where it is imported
        with patch("pro_file_organizer.ui.main_window_controller.filedialog.askdirectory", return_value="/tmp/selected"):
            with patch("pathlib.Path.is_dir", return_value=True):
                self.controller.select_folder()
                self.assertEqual(self.controller.selected_path, Path("/tmp/selected"))

    def test_undo_action_success(self):
        self.organizer.undo_stack = [MagicMock()]
        self.view.confirm_action.return_value = True
        self.controller.undo_action()
        self.organizer.undo_changes.assert_called()

if __name__ == '__main__':
    unittest.main()
