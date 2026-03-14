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

# Reload main_window
import pro_file_organizer.ui.main_window  # noqa: E402

importlib.reload(pro_file_organizer.ui.main_window)
from pro_file_organizer.ui.main_window import OrganizerApp  # noqa: E402


class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch("pro_file_organizer.ui.main_window.FileOrganizer"),
            patch("pro_file_organizer.ui.main_window.MultimodalFileOrganizer"),
            patch("pro_file_organizer.ui.main_window.MainWindowController"),
            patch("pro_file_organizer.ui.main_window.SettingsDialog"),
            patch("pro_file_organizer.ui.main_window.BatchDialog"),
            patch("pro_file_organizer.ui.main_window.QMessageBox"),
            patch("pro_file_organizer.ui.main_window.QFileDialog"),
        ]
        self.mocks = [p.start() for p in self.patchers]
        self.mocks[5].Yes = 1
        self.mocks[5].No = 0
        self.app = OrganizerApp()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_init(self):
        self.assertIsNotNone(self.app.controller)

    def test_update_folder_display(self):
        self.app.update_folder_display("/tmp/test")
        self.app.drop_zone.lbl_text.setText.assert_called_with("Selected: test")
        self.app.btn_run.setEnabled.assert_called_with(True)

    def test_clear_results(self):
        self.app.results_layout.count.return_value = 3  # 2 items to clear + 1 stretch
        mock_item = MagicMock()
        mock_widget = MagicMock()
        mock_item.widget.return_value = mock_widget
        self.app.results_layout.takeAt.return_value = mock_item

        self.app.clear_results()
        # Should be called count-1 times
        self.assertEqual(self.app.results_layout.takeAt.call_count, 2)
        mock_widget.deleteLater.assert_called()

    def test_show_status(self):
        self.app.show_status("Busy...")
        self.app.lbl_status.setText.assert_called_with("Busy...")

    def test_update_progress(self):
        # Numeric progress
        self.app.update_progress(5, 10, "file.txt")
        self.app.progress_bar.setValue.assert_called_with(50)

        # Float progress (ML loading)
        self.app.update_progress(0.7, 1.0, "Model Loading")
        self.app.progress_bar.setValue.assert_called_with(70)

    def test_ui_toggles(self):
        self.app.enable_ai_ui()
        self.app.ai_conf_container.show.assert_called()

        self.app.disable_ai_ui()
        self.app.ai_conf_container.hide.assert_called()

    def test_set_running_state(self):
        self.app.set_running_state(True)
        self.app.btn_run.setEnabled.assert_called_with(False)

    def test_open_dialogs(self):
        self.app.open_settings()
        self.app.controller.open_settings.assert_called()

        self.app.open_batch()
        self.app.controller.open_batch.assert_called()

    def test_change_appearance(self):
        with patch.object(self.app, "_apply_theme") as mock_apply:
            self.app.change_appearance_mode_event("Dark")
            mock_apply.assert_called_with("Dark")
            self.app.organizer.save_theme_mode.assert_called_with("Dark")

    def test_handle_drop(self):
        self.app._handle_drop("/tmp/drop")
        self.app.controller.set_folder.assert_called_with("/tmp/drop")

    def test_show_error(self):
        self.app.show_error("Title", "Message")
        self.mocks[5].critical.assert_called_with(self.app, "Title", "Message")

    def test_show_info(self):
        self.app.show_info("Title", "Message")
        self.mocks[5].information.assert_called_with(self.app, "Title", "Message")

    def test_confirm_action(self):
        self.mocks[5].StandardButton.Yes = 1
        self.mocks[5].StandardButton.No = 0
        self.mocks[5].question.return_value = 1
        res = self.app.confirm_action("Title", "Message")
        self.assertTrue(res)
        self.mocks[5].question.assert_called_with(
            self.app, "Title", "Message", self.mocks[5].StandardButton.Yes | self.mocks[5].StandardButton.No
        )

    def test_update_stats_display(self):
        stats = {"total_files": 100, "last_run": "Today"}
        self.app.update_stats_display(stats)
        self.app.lbl_stats_total.setText.assert_called_with("Files Organized: 100")
        self.app.lbl_stats_last.setText.assert_called_with("Last Run: Today")

    def test_show_model_download(self):
        with patch("pro_file_organizer.ui.main_window.ModelDownloadModal") as mock_modal:
            callback = MagicMock()
            self.app.show_model_download(callback)
            mock_modal.assert_called_with(self.app, on_complete=callback)
            mock_modal().exec.assert_called()

    def test_show_settings(self):
        with patch("pro_file_organizer.ui.main_window.SettingsDialog") as mock_dialog:
            self.app.show_settings(self.app.organizer)
            mock_dialog.assert_called_with(self.app, self.app.organizer)
            mock_dialog().exec.assert_called()

    def test_show_batch(self):
        with patch("pro_file_organizer.ui.main_window.BatchDialog") as mock_dialog:
            self.app.show_batch(self.app.organizer)
            mock_dialog.assert_called_with(self.app, self.app.organizer)
            mock_dialog().exec.assert_called()

    def test_set_ai_switch_state(self):
        self.app.set_ai_switch_state(True)
        self.app.switch_ai.setChecked.assert_called_with(True)

    def test_set_watch_switch_state(self):
        self.app.set_watch_switch_state(True)
        self.app.chk_watch.setChecked.assert_called_with(True)

    def test_getters(self):
        self.app.slider_conf.value.return_value = 5
        self.assertEqual(self.app.get_ai_confidence(), 0.5)

    def test_browse_folder(self):
        self.app.controller.selected_path = "/tmp"
        self.mocks[6].getExistingDirectory.return_value = "/new/path"
        self.app.browse_folder()
        self.mocks[6].getExistingDirectory.assert_called_with(self.app, "Select Folder", "/tmp")
        self.app.controller.set_folder.assert_called_with("/new/path")

    def test_add_result_card(self):
        with patch("pro_file_organizer.ui.main_window.FileCard") as mock_card:
            data = {"file": "test.txt", "category": "Docs"}
            self.app.add_result_card(data)
            self.assertEqual(len(self.app.result_cards), 1)
            mock_card.assert_called()


if __name__ == "__main__":
    unittest.main()
