import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.ui_test_utils import get_ui_mocks

# Apply standardized mocks
mock_ctk, _ = get_ui_mocks()
sys.modules["customtkinter"] = mock_ctk

# Force reload
import pro_file_organizer.ui.dialogs.settings_dialog_ctk  # noqa: E402

importlib.reload(pro_file_organizer.ui.dialogs.settings_dialog_ctk)
from pro_file_organizer.ui.dialogs.settings_dialog_ctk import SettingsDialog  # noqa: E402


class TestSettingsDialog(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()
        self.mock_organizer = MagicMock()
        self.mock_organizer.directories = {"Images": [".png"], "Videos": [".mp4"]}
        self.mock_organizer.ml_confidence = 0.5
        self.mock_organizer.excluded_extensions = {".tmp"}
        self.mock_organizer.excluded_folders = {"node_modules"}

        with patch("pro_file_organizer.ui.dialogs.settings_dialog_ctk.ToolTip"):
            self.dialog = SettingsDialog(self.mock_parent, self.mock_organizer)

    def test_init(self):
        self.assertEqual(self.dialog.organizer, self.mock_organizer)

    @patch("pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkInputDialog")
    def test_add_category_success(self, mock_input_class):
        mock_input = MagicMock()
        mock_input.get_input.return_value = "Music"
        mock_input_class.return_value = mock_input
        self.dialog.add_category()
        self.assertIn("Music", self.mock_organizer.directories)

    def test_delete_category(self):
        self.dialog.on_cat_select("Videos")
        with patch("pro_file_organizer.ui.dialogs.settings_dialog_ctk.messagebox.askyesno", return_value=True):
            self.dialog.delete_category()
            self.assertNotIn("Videos", self.mock_organizer.directories)

    def test_save_config_with_validation_errors(self):
        self.mock_organizer.validate_config.return_value = ["Error 1"]
        patch_path = "pro_file_organizer.ui.dialogs.settings_dialog_ctk.messagebox.showerror"
        with patch(patch_path) as mock_err:
            self.dialog.save_config()
            mock_err.assert_called()

    def test_exclusion_logic(self):
        self.dialog.txt_excl_exts.get.return_value = ".log, .tmp"
        self.dialog.txt_excl_folders.get.return_value = "dist, build"
        self.dialog.slider_ml = MagicMock()
        self.dialog.slider_ml.get.return_value = 0.8

        self.dialog._apply_exclusions()

        self.assertIn(".log", self.mock_organizer.excluded_extensions)
        self.assertIn("dist", self.mock_organizer.excluded_folders)
        self.assertEqual(self.mock_organizer.ml_confidence, 0.8)

    def test_save_pending_cat_changes(self):
        self.dialog.last_selected_cat = "Images"
        self.dialog.txt_exts.get.return_value = ".jpg, .jpeg"
        self.dialog.save_pending_cat_changes()
        self.assertEqual(self.mock_organizer.directories["Images"], [".jpg", ".jpeg"])

    def test_export_import(self):
        patch_save = "pro_file_organizer.ui.dialogs.settings_dialog_ctk.filedialog.asksaveasfilename"
        with patch(patch_save, return_value="/tmp/conf.json"):
            self.dialog.export_profile()
            self.mock_organizer.export_config_file.assert_called()

        patch_open = "pro_file_organizer.ui.dialogs.settings_dialog_ctk.filedialog.askopenfilename"
        with patch(patch_open, return_value="/tmp/conf.json"):
            patch_confirm = "pro_file_organizer.ui.dialogs.settings_dialog_ctk.messagebox.askyesno"
            with patch(patch_confirm, return_value=True):
                self.dialog.import_profile()
                self.mock_organizer.import_config_file.assert_called()


if __name__ == "__main__":
    unittest.main()
