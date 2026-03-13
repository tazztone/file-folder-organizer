import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk

# We need to ensure ctk is mocked within the module context
with patch('customtkinter.CTkFrame', MagicMock):
    with patch('customtkinter.CTkToplevel', MagicMock):
        from pro_file_organizer.ui.dialogs.settings_dialog_ctk import SettingsDialog

class TestSettingsDialog(unittest.TestCase):
    def setUp(self):
        # Create real-ish parent
        self.mock_parent = MagicMock()
        self.mock_organizer = MagicMock()
        self.mock_organizer.directories = {"Images": [".png"], "Videos": [".mp4"]}
        self.mock_organizer.ml_confidence = 0.5
        self.mock_organizer.excluded_extensions = {".tmp"}
        self.mock_organizer.excluded_folders = {"node_modules"}

        # Patch ctk components directly in the module
        self.patchers = [
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkToplevel'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkTabview'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkFrame'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkLabel'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkButton'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkTextbox'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkSlider'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkScrollableFrame'),
            patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ToolTip')
        ]
        for p in self.patchers:
            p.start()

        self.dialog = SettingsDialog(self.mock_parent, self.mock_organizer)

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_init(self):
        self.assertEqual(self.dialog.organizer, self.mock_organizer)

    @patch('pro_file_organizer.ui.dialogs.settings_dialog_ctk.ctk.CTkInputDialog')
    def test_add_category_success(self, mock_input_class):
        mock_input = MagicMock()
        mock_input.get_input.return_value = "Music"
        mock_input_class.return_value = mock_input
        self.dialog.add_category()
        self.assertIn("Music", self.mock_organizer.directories)

    def test_save_config(self):
        self.mock_organizer.validate_config.return_value = []
        self.mock_organizer.save_config.return_value = True
        self.dialog.save_config()
        self.mock_organizer.save_config.assert_called()

if __name__ == '__main__':
    unittest.main()
