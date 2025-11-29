import unittest
import sys
import importlib
from unittest.mock import MagicMock, patch, call

# Mock modules
if 'tkinter' not in sys.modules:
    sys.modules['tkinter'] = MagicMock()
if 'tkinter.messagebox' not in sys.modules:
    sys.modules['tkinter.messagebox'] = MagicMock()
if 'tkinter.filedialog' not in sys.modules:
    sys.modules['tkinter.filedialog'] = MagicMock()
if 'customtkinter' not in sys.modules:
    sys.modules['customtkinter'] = MagicMock()

# Setup CTk mocks
mock_ctk = sys.modules['customtkinter']

import settings_dialog_ctk as settings_dialog
import organizer

class TestSettingsDialog(unittest.TestCase):
    def setUp(self):
        # Reset global mock
        mock_ctk.reset_mock()
        # Ensure CTkTextbox returns unique mocks each instantiation
        mock_ctk.CTkTextbox.side_effect = lambda *args, **kwargs: MagicMock()

        # Reload module to ensure it uses the current mock_ctk
        importlib.reload(settings_dialog)

        self.mock_parent = MagicMock()
        self.organizer = organizer.FileOrganizer()
        # Pre-populate organizer data
        self.organizer.directories = {"Images": [".jpg"], "Videos": [".mp4"]}
        self.organizer.excluded_extensions = {".tmp"}
        self.organizer.excluded_folders = {".git"}

    def test_init(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        # Check window creation
        mock_ctk.CTkToplevel.assert_called_once()
        dialog.window.title.assert_called_with("Configuration")

        # Check tabs creation
        dialog.tabview.add.assert_has_calls([call("Categories"), call("Exclusions"), call("Profiles")])

    def test_add_category_success(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        # Mock Input Dialog
        mock_input = MagicMock()
        mock_input.get_input.return_value = "Music"
        mock_ctk.CTkInputDialog.return_value = mock_input

        dialog.add_category()

        self.assertIn("Music", self.organizer.directories)
        self.assertEqual(self.organizer.directories["Music"], [])

    def test_add_category_empty(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        mock_input = MagicMock()
        mock_input.get_input.return_value = "   "
        mock_ctk.CTkInputDialog.return_value = mock_input

        # patch where it is used
        with patch('settings_dialog_ctk.messagebox.showerror') as mock_error:
            dialog.add_category()
            mock_error.assert_called_with("Error", "Category name cannot be empty.")

    def test_delete_category(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        # Select "Images"
        dialog.on_cat_select("Images")
        self.assertEqual(dialog.last_selected_cat, "Images")

        with patch('settings_dialog_ctk.messagebox.askyesno', return_value=True):
            dialog.delete_category()

        self.assertNotIn("Images", self.organizer.directories)

    def test_save_changes_updates_organizer(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        # With reload, we need to be careful about side_effect on CTkTextbox.
        # It creates new mocks.
        # We need to find the mocks attached to the dialog instance.

        dialog.txt_exts.get.return_value = ".png, .jpeg\n"
        dialog.txt_excl_exts.get.return_value = ".log, .bak\n"
        dialog.txt_excl_folders.get.return_value = "node_modules, build\n"

        dialog.last_selected_cat = "Images"

        dialog.save_config()

        self.assertEqual(self.organizer.directories["Images"], [".png", ".jpeg"])
        self.assertEqual(self.organizer.excluded_extensions, {".log", ".bak"})
        self.assertEqual(self.organizer.excluded_folders, {"node_modules", "build"})

    def test_save_config_with_errors(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        dialog.txt_exts.get.return_value = ""
        dialog.txt_excl_exts.get.return_value = ""
        dialog.txt_excl_folders.get.return_value = ""

        dialog.organizer.directories["Invalid"] = ["jpg"] # No dot

        with patch('settings_dialog_ctk.messagebox.showerror') as mock_error:
            dialog.save_config()
            mock_error.assert_called()
            dialog.window.destroy.assert_not_called()

    def test_export_profile(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        dialog.txt_exts.get.return_value = ""
        dialog.txt_excl_exts.get.return_value = ""
        dialog.txt_excl_folders.get.return_value = ""

        with patch('settings_dialog_ctk.filedialog.asksaveasfilename', return_value="test_profile.json"):
            with patch.object(self.organizer, 'export_config_file', return_value=True) as mock_export:
                with patch('settings_dialog_ctk.messagebox.showinfo') as mock_info:
                    dialog.export_profile()

                    mock_export.assert_called_with("test_profile.json")
                    mock_info.assert_called_with("Success", "Profile exported successfully.")

    def test_import_profile(self):
        dialog = settings_dialog.SettingsDialog(self.mock_parent, self.organizer)

        with patch('settings_dialog_ctk.filedialog.askopenfilename', return_value="test_profile.json"):
            with patch('settings_dialog_ctk.messagebox.askyesno', return_value=True):
                with patch.object(self.organizer, 'import_config_file', return_value=True) as mock_import:
                    dialog.import_profile()

                    mock_import.assert_called_with("test_profile.json")

if __name__ == "__main__":
    unittest.main()
