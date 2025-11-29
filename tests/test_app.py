import unittest
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock tkinter and its submodules BEFORE importing app
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()

import tkinter as tk
import app

class TestOrganizerApp(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()

        # Mocking variables
        self.mock_var_recursive = MagicMock()
        self.mock_var_recursive.get.return_value = False
        self.mock_var_date_sort = MagicMock()
        self.mock_var_date_sort.get.return_value = False
        self.mock_var_del_empty = MagicMock()
        self.mock_var_del_empty.get.return_value = False
        self.mock_var_dry_run = MagicMock()
        self.mock_var_dry_run.get.return_value = False

        self.app = app.OrganizerApp(self.root)

        # Inject mocks
        self.app.var_recursive = self.mock_var_recursive
        self.app.var_date_sort = self.mock_var_date_sort
        self.app.var_del_empty = self.mock_var_del_empty
        self.app.var_dry_run = self.mock_var_dry_run

        # Mock Organizer
        self.app.organizer = MagicMock()
        self.app.organizer.organize_files.return_value = {"moved": 0, "errors": 0}

        self.app.selected_path = Path("/tmp/test")

    def test_start_thread_calls_organizer(self):
        """Test that start_thread triggers organization."""
        # Mock confirmation to return True
        with patch('app.messagebox.askyesno', return_value=True) as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                # Check confirmation was asked (since default dry_run is False)
                mock_ask.assert_called_once()

                mock_thread.assert_called_once()
                # Get the target function passed to thread
                target = mock_thread.call_args[1]['target']
                args = mock_thread.call_args[1]['args']

                # Run it directly
                target(*args)

                # Check if organizer.organize_files was called
                self.app.organizer.organize_files.assert_called_once()

                # Verify arguments
                call_kwargs = self.app.organizer.organize_files.call_args[1]
                self.assertEqual(call_kwargs['source_path'], Path("/tmp/test"))
                self.assertEqual(call_kwargs['recursive'], False)
                self.assertEqual(call_kwargs['dry_run'], False)

    def test_start_thread_cancel(self):
        """Test that start_thread aborts if confirmation is No."""
        with patch('app.messagebox.askyesno', return_value=False) as mock_ask:
             with patch('threading.Thread') as mock_thread:
                self.app.start_thread()
                mock_ask.assert_called_once()
                mock_thread.assert_not_called()

    def test_run_preview(self):
        """Test that run_preview triggers dry run organization."""
        with patch('threading.Thread') as mock_thread:
            self.app.run_preview()

            mock_thread.assert_called_once()
            target = mock_thread.call_args[1]['target']
            args = mock_thread.call_args[1]['args']

            self.assertEqual(args[0], True) # dry_run_override=True

            # Execute target with args
            target(*args)

            call_kwargs = self.app.organizer.organize_files.call_args[1]
            self.assertEqual(call_kwargs['dry_run'], True)

    def test_undo_changes(self):
        """Test that undo_changes triggers organizer undo."""
        with patch('threading.Thread') as mock_thread:
            self.app.undo_changes()
            target = mock_thread.call_args[1]['target']
            target()

            self.app.organizer.undo_changes.assert_called_once()

    def test_dry_run_flag(self):
        """Test that dry run flag is passed correctly."""
        self.mock_var_dry_run.get.return_value = True

        with patch('app.messagebox.askyesno') as mock_ask:
            with patch('threading.Thread') as mock_thread:
                self.app.start_thread()

                # Should NOT ask for confirmation
                mock_ask.assert_not_called()

                target = mock_thread.call_args[1]['target']
                args = mock_thread.call_args[1].get('args', ())
                target(*args)

                call_kwargs = self.app.organizer.organize_files.call_args[1]
                self.assertTrue(call_kwargs['dry_run'])

if __name__ == "__main__":
    unittest.main()
