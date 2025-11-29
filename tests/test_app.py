import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 1. Mock modules BEFORE import
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()

import app

class TestOrganizerApp(unittest.TestCase):
    def setUp(self):
        # 2. Reset global mock if needed, or rely on patching instance
        # Ensure BooleanVar returns a new mock with .get() returning False by default
        bool_var_mock = MagicMock()
        bool_var_mock.get.return_value = False
        app.ctk.BooleanVar.return_value = bool_var_mock

        # Instantiate
        self.app = app.OrganizerApp()

        # 3. Setup Instance Mocks
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

        # Mock UI update methods to prevent errors
        self.app.after = MagicMock()
        self.app.btn_run = MagicMock()
        self.app.btn_preview = MagicMock()
        self.app.btn_undo = MagicMock()
        self.app.progress = MagicMock()
        self.app.log_area = MagicMock()

    def test_start_thread_calls_organizer(self):
        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                # Verify confirmation asked
                mock_ask.assert_called_once()

                # Verify thread started
                mock_thread.assert_called_once()

                # Execute the thread target manually
                call_args = mock_thread.call_args
                target = call_args[1].get('target') or call_args[0]
                args = call_args[1].get('args', ())
                target(*args)

                # Verify organizer called
                self.app.organizer.organize_files.assert_called_once()
                self.assertEqual(self.app.organizer.organize_files.call_args[1]['source_path'], Path("/tmp/test"))

    def test_start_thread_cancel(self):
        with patch('tkinter.messagebox.askyesno', return_value=False) as mock_ask:
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

            # dry_run_override should be True
            self.assertTrue(args[0])

            target(*args)

            call_kwargs = self.app.organizer.organize_files.call_args[1]
            self.assertTrue(call_kwargs['dry_run'])

    def test_undo_changes(self):
        self.app.organizer.undo_stack = [{"history": [], "source_path": Path("/tmp")}]

        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.undo_changes()

                mock_ask.assert_called_once()
                mock_thread.assert_called_once()

                target = mock_thread.call_args[1].get('target')
                target()

                self.app.organizer.undo_changes.assert_called_once()

    def test_dry_run_flag(self):
        # Set dry_run to True
        self.app.var_dry_run.get.return_value = True

        with patch('tkinter.messagebox.askyesno') as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                # Should NOT ask for confirmation
                mock_ask.assert_not_called()

                # Thread should start
                mock_thread.assert_called_once()

                call_args = mock_thread.call_args
                target = call_args[1].get('target')
                args = call_args[1].get('args', ())
                target(*args)

                # Organizer should receive dry_run=True (from var)
                call_kwargs = self.app.organizer.organize_files.call_args[1]
                self.assertTrue(call_kwargs['dry_run'])

if __name__ == "__main__":
    unittest.main()
