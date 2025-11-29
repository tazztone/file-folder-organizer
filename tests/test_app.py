import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Define a dummy CTk class
class DummyCTk:
    def __init__(self, *args, **kwargs):
        pass
    def title(self, *args): pass
    def geometry(self, *args): pass
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid_rowconfigure(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass
    def after(self, *args, **kwargs): pass
    def mainloop(self): pass

# Setup mocks before import
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

# We need to mock customtkinter module
mock_ctk = MagicMock()
mock_ctk.CTk = DummyCTk
mock_ctk.CTkFrame = MagicMock()
mock_ctk.CTkLabel = MagicMock()
mock_ctk.CTkButton = MagicMock()
mock_ctk.CTkEntry = MagicMock()
mock_ctk.CTkOptionMenu = MagicMock()
mock_ctk.CTkSwitch = MagicMock()
mock_ctk.CTkProgressBar = MagicMock()
mock_ctk.CTkTextbox = MagicMock()
mock_ctk.CTkFont = MagicMock()

sys.modules['customtkinter'] = mock_ctk

# Mock tkinterdnd2
mock_tkdnd = MagicMock()
class DummyDnDWrapper:
    pass
mock_tkdnd.DnDWrapper = DummyDnDWrapper
mock_tkdnd.TkinterDnD._require = MagicMock()
mock_tkdnd.DND_FILES = "DND_Files"
sys.modules['tkinterdnd2'] = mock_tkdnd

import app

class TestOrganizerApp(unittest.TestCase):
    def setUp(self):
        # Reset side effects
        mock_ctk.CTkButton.side_effect = None

        bool_var_mock = MagicMock()
        bool_var_mock.get.return_value = False
        mock_ctk.BooleanVar.return_value = bool_var_mock
        mock_ctk.BooleanVar.side_effect = None

        self.app = app.OrganizerApp()

        self.app.var_recursive = MagicMock()
        self.app.var_recursive.get.return_value = False

        self.app.var_date_sort = MagicMock()
        self.app.var_date_sort.get.return_value = False

        self.app.var_del_empty = MagicMock()
        self.app.var_del_empty.get.return_value = False

        self.app.var_dry_run = MagicMock()
        self.app.var_dry_run.get.return_value = False

        self.app.organizer = MagicMock()
        self.app.organizer.organize_files.return_value = {"moved": 0, "errors": 0}
        self.app.organizer.undo_stack = []

        self.app.selected_path = Path("/tmp/test")

        self.app.lbl_path = MagicMock()
        self.app.option_recent = MagicMock()
        self.app.btn_run = MagicMock()
        self.app.btn_preview = MagicMock()
        self.app.btn_undo = MagicMock()
        self.app.progress = MagicMock()
        self.app.log_area = MagicMock()
        self.app.after = MagicMock()
        self.app.recent_folders = []

    def test_start_thread_calls_organizer(self):
        # Patching app.messagebox because app.py imports it directly
        with patch('app.messagebox.askyesno', return_value=True) as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                mock_ask.assert_called_once()
                mock_thread.assert_called_once()

                call_args = mock_thread.call_args
                target = call_args[1].get('target') or call_args[0]
                args = call_args[1].get('args', ())
                target(*args)

                self.app.organizer.organize_files.assert_called_once()
                self.assertEqual(self.app.organizer.organize_files.call_args[1]['source_path'], Path("/tmp/test"))

    def test_start_thread_cancel(self):
        with patch('app.messagebox.askyesno', return_value=False) as mock_ask:
             with patch('threading.Thread') as mock_thread:
                self.app.start_thread()
                mock_ask.assert_called_once()
                mock_thread.assert_not_called()

    def test_run_preview(self):
        with patch('threading.Thread') as mock_thread:
            self.app.run_preview()

            mock_thread.assert_called_once()
            call_args = mock_thread.call_args
            target = call_args[1].get('target')
            args = call_args[1].get('args', ())

            self.assertTrue(args[0])

            target(*args)

            call_kwargs = self.app.organizer.organize_files.call_args[1]
            self.assertTrue(call_kwargs['dry_run'])

    def test_undo_changes(self):
        self.app.organizer.undo_stack = [{"history": [], "source_path": Path("/tmp")}]

        with patch('app.messagebox.askyesno', return_value=True) as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.undo_changes()

                mock_ask.assert_called_once()
                mock_thread.assert_called_once()

                target = mock_thread.call_args[1].get('target')
                target()

                self.app.organizer.undo_changes.assert_called_once()

    def test_dry_run_flag(self):
        self.app.var_dry_run.get.return_value = True

        with patch('app.messagebox.askyesno') as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                mock_ask.assert_not_called()
                mock_thread.assert_called_once()

                call_args = mock_thread.call_args
                target = call_args[1].get('target')
                args = call_args[1].get('args', ())
                target(*args)

                call_kwargs = self.app.organizer.organize_files.call_args[1]
                self.assertTrue(call_kwargs['dry_run'])

    def test_add_recent(self):
        with patch("app.open", new_callable=MagicMock):
             with patch("app.json.dump"):
                 self.app.add_recent(Path("/tmp/new"))

                 self.assertIn(str(Path("/tmp/new")), self.app.recent_folders)
                 self.assertEqual(self.app.recent_folders[0], str(Path("/tmp/new")))

                 self.app.option_recent.configure.assert_called()

    def test_add_recent_limit(self):
        self.app.recent_folders = [str(i) for i in range(10)]
        with patch("app.open", new_callable=MagicMock):
            with patch("app.json.dump"):
                self.app.add_recent(Path("11"))
                self.assertEqual(len(self.app.recent_folders), 10)
                self.assertEqual(self.app.recent_folders[0], "11")
                self.assertNotIn("9", self.app.recent_folders)

    def test_on_recent_select(self):
        with patch.object(self.app, 'add_recent') as mock_add_recent:
            self.app.on_recent_select("/tmp/recent_path")

            self.assertEqual(self.app.selected_path, Path("/tmp/recent_path"))
            self.app.lbl_path.configure.assert_called_with(text=str(Path("/tmp/recent_path")))
            self.app.btn_run.configure.assert_called_with(state="normal")
            mock_add_recent.assert_called_with(Path("/tmp/recent_path"))

    def test_on_recent_select_placeholder(self):
        self.app.on_recent_select("Recent...")
        self.assertEqual(self.app.selected_path, Path("/tmp/test"))

if __name__ == "__main__":
    unittest.main()
