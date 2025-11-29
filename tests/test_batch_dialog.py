import unittest
import sys
import threading
import importlib
from unittest.mock import MagicMock, patch, call
from pathlib import Path

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

import batch_dialog_ctk as batch_dialog
import organizer

class TestBatchDialog(unittest.TestCase):
    def setUp(self):
        # Reset Mocks
        mock_ctk.reset_mock()
        # Ensure side_effects for uniqueness where needed
        mock_ctk.CTkButton.side_effect = lambda *args, **kwargs: MagicMock()
        mock_ctk.CTkLabel.side_effect = lambda *args, **kwargs: MagicMock()

        # Reload module
        importlib.reload(batch_dialog)

        self.mock_parent = MagicMock()
        self.organizer = organizer.FileOrganizer()

        # Patch json load/dump to prevent reading/writing actual files
        self.json_patch = patch('batch_dialog_ctk.json')
        self.mock_json = self.json_patch.start()
        self.mock_json.load.return_value = []

        # Patch exists
        self.exists_patch = patch('batch_dialog_ctk.Path.exists', return_value=True)
        self.mock_exists = self.exists_patch.start()

        self.dialog = batch_dialog.BatchDialog(self.mock_parent, self.organizer)

    def tearDown(self):
        self.json_patch.stop()
        self.exists_patch.stop()

    def test_init(self):
        mock_ctk.CTkToplevel.assert_called_once()
        self.assertEqual(self.dialog.batch_folders, [])

    def test_add_folder(self):
        with patch('batch_dialog_ctk.filedialog.askdirectory', return_value="/tmp/new_folder"):
            self.dialog.add_folder()

        self.assertEqual(len(self.dialog.batch_folders), 1)
        self.assertEqual(self.dialog.batch_folders[0]["path"], "/tmp/new_folder")

        # Verify it triggered UI refresh (destroyed children of scroll frame)
        self.dialog.scroll_frame.winfo_children.assert_called()

    def test_add_duplicate_folder(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]

        with patch('batch_dialog_ctk.filedialog.askdirectory', return_value="/tmp/folder"):
            self.dialog.add_folder()

        self.assertEqual(len(self.dialog.batch_folders), 1)

    def test_remove_folder(self):
        self.dialog.batch_folders = [
            {"path": "/tmp/folder1", "settings": None},
            {"path": "/tmp/folder2", "settings": None}
        ]

        self.dialog.remove_folder(0)

        self.assertEqual(len(self.dialog.batch_folders), 1)
        self.assertEqual(self.dialog.batch_folders[0]["path"], "/tmp/folder2")

    def test_clear_all(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]

        with patch('batch_dialog_ctk.messagebox.askyesno', return_value=True):
            self.dialog.clear_all()

        self.assertEqual(self.dialog.batch_folders, [])

    def test_configure_folder(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]

        mock_ctk.CTkToplevel.reset_mock()

        self.dialog.configure_folder(0)

        mock_ctk.CTkToplevel.assert_called_once()

        save_btn_call = None
        # Since we use side_effect for CTkButton, each call returns unique mock.
        # But we don't have easy access to all return values from here unless we check side_effect logic.
        # But side_effect returns MagicMock().

        # We can scan all mocks created? No.
        # But mock_ctk.CTkButton is called.

        # Filter call args
        for call_args in mock_ctk.CTkButton.call_args_list:
            if call_args[1].get('text') == "Save":
                save_btn_call = call_args
                break

        self.assertIsNotNone(save_btn_call)
        save_command = save_btn_call[1]['command']

        # To test values, we need to mock BooleanVar properly for this test
        # Since we reloaded module, it uses mock_ctk.BooleanVar

        with patch('customtkinter.BooleanVar') as mock_bool:
            mock_bool.return_value.get.return_value = True

            # Re-run configure to bind vars
            self.dialog.configure_folder(0)

            save_btn_call = [c for c in mock_ctk.CTkButton.call_args_list if c[1].get('text') == "Save"][-1]
            save_command = save_btn_call[1]['command']

            save_command()

        self.assertIsNotNone(self.dialog.batch_folders[0]["settings"])
        self.assertTrue(self.dialog.batch_folders[0]["settings"]["recursive"])

    def test_run_batch_empty(self):
        with patch('batch_dialog_ctk.messagebox.showwarning') as mock_warn:
            self.dialog.run_batch()
            mock_warn.assert_called_with("Warning", "No folders to process.")

    def test_run_batch_execution(self):
        self.dialog.batch_folders = [{"path": "/tmp/folder", "settings": None}]

        with patch('batch_dialog_ctk.messagebox.askyesno', return_value=True):
            with patch('threading.Thread') as mock_thread:
                self.dialog.run_batch()
                mock_thread.assert_called_once()

                target = mock_thread.call_args[1].get('target')

                self.dialog.window.after = MagicMock()
                self.organizer.organize_files = MagicMock()

                target()

                self.organizer.organize_files.assert_called_with(Path("/tmp/folder"), recursive=False, date_sort=False, del_empty=False, dry_run=False)

                self.assertTrue(self.dialog.window.after.called)

if __name__ == "__main__":
    unittest.main()
