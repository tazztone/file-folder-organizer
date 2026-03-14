import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_pyside_mocks

# Apply standardized mocks
mock_qtwidgets, mock_qtcore, mock_qtgui = get_pyside_mocks()
sys.modules["PySide6.QtWidgets"] = mock_qtwidgets
sys.modules["PySide6.QtCore"] = mock_qtcore
sys.modules["PySide6.QtGui"] = mock_qtgui

from pro_file_organizer.ui.dialogs import settings_dialog


class TestSettingsDialog(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()
        self.mock_organizer = MagicMock()
        self.mock_organizer.directories = {"Images": [".png"], "Videos": [".mp4"]}
        self.mock_organizer.ml_confidence = 0.5
        self.mock_organizer.excluded_extensions = {".tmp"}
        self.mock_organizer.excluded_folders = {"node_modules"}

        self.dialog = settings_dialog.SettingsDialog(self.mock_parent, self.mock_organizer)

    def test_init(self):
        self.assertEqual(self.dialog.organizer, self.mock_organizer)

    def test_add_category_success(self):
        with patch.object(settings_dialog, "QInputDialog") as mock_input:
            mock_input.getText.return_value = ("Music", True)
            self.dialog.add_category()
            self.assertIn("Music", self.mock_organizer.directories)

    def test_delete_category(self):
        self.dialog.on_cat_select("Videos")
        with patch.object(settings_dialog, "QMessageBox") as mock_msg:
            mock_msg.StandardButton.Yes = 1
            mock_msg.StandardButton.No = 0
            mock_msg.question.return_value = 1
            self.dialog.delete_category()
            self.assertNotIn("Videos", self.mock_organizer.directories)

    def test_save_config_with_validation_errors(self):
        self.mock_organizer.validate_config.return_value = ["Error 1"]
        with patch.object(settings_dialog, "QMessageBox") as mock_msg:
            self.dialog.save_config()
            mock_msg.critical.assert_called()

    def test_exclusion_logic(self):
        self.dialog.txt_excl_exts.toPlainText.return_value = ".log, .tmp"
        self.dialog.txt_excl_folders.toPlainText.return_value = "dist, build"
        self.dialog.slider_ml.value.return_value = 80 # 0.8 * 100

        self.dialog._apply_exclusions()

        self.assertIn(".log", self.mock_organizer.excluded_extensions)
        self.assertIn("dist", self.mock_organizer.excluded_folders)
        self.assertEqual(self.mock_organizer.ml_confidence, 0.8)

    def test_save_pending_cat_changes(self):
        self.dialog.last_selected_cat = "Images"
        self.dialog.txt_exts.toPlainText.return_value = ".jpg, .jpeg"
        self.dialog.save_pending_cat_changes()
        self.assertEqual(self.mock_organizer.directories["Images"], [".jpg", ".jpeg"])

    def test_export_import(self):
        with patch.object(settings_dialog, "QFileDialog") as mock_fd:
            mock_fd.getSaveFileName.return_value = ("/tmp/conf.json", "filter")
            self.dialog.export_profile()
            self.mock_organizer.export_config_file.assert_called_with("/tmp/conf.json")

        with patch.object(settings_dialog, "QFileDialog") as mock_fd:
            mock_fd.getOpenFileName.return_value = ("/tmp/conf.json", "filter")
            with patch.object(settings_dialog, "QMessageBox") as mock_msg:
                mock_msg.StandardButton.Yes = 1
                mock_msg.StandardButton.No = 0
                mock_msg.question.return_value = 1
                self.dialog.import_profile()
                self.mock_organizer.import_config_file.assert_called_with("/tmp/conf.json")


if __name__ == "__main__":
    unittest.main()
