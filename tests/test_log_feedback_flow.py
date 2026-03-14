import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import threading

# Logic only tests, use mocks
from pro_file_organizer.ui.main_window_controller import MainWindowController
from pro_file_organizer.core.organizer import FileOrganizer, OrganizationOptions, OrganizationResult

class TestLogFeedbackFlow(unittest.TestCase):
    def setUp(self):
        self.view = MagicMock()
        self.organizer = MagicMock(spec=FileOrganizer)
        self.ml_organizer = MagicMock()
        
        # Mock view getters
        self.view.get_recursive_val.return_value = False
        self.view.get_date_sort_val.return_value = False
        self.view.get_del_empty_val.return_value = False
        self.view.get_detect_duplicates_val.return_value = False
        self.view.get_ai_confidence.return_value = 0.3
        
        # Mock after_main to execute immediately
        self.view.after_main.side_effect = lambda ms, func: func()

        self.controller = MainWindowController(self.view, self.organizer, self.ml_organizer)
        self.controller.selected_path = Path("/mock/source")

    def test_controller_passes_log_callback(self):
        """Verify that MainWindowController passes a working log_callback to organize_files."""
        
        # 1. Setup mock organize_files to capture options
        captured_options = None
        def mock_organize(options):
            nonlocal captured_options
            captured_options = options
            return {"moved": 1, "errors": 0}
        
        self.organizer.organize_files.side_effect = mock_organize
        
        # 2. Mock threading to run worker immediately
        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = mock_thread.return_value
            def start_side_effect():
                target = mock_thread.call_args[1].get("target")
                args = mock_thread.call_args[1].get("args", ())
                if target:
                    target(*args)
            mock_thread_instance.start.side_effect = start_side_effect
            
            # 3. Run organization
            self.controller.run_organization(dry_run=True)
            
        # 4. Verify organize_files was called
        self.organizer.organize_files.assert_called()
        self.assertIsNotNone(captured_options)
        self.assertIsNotNone(captured_options.log_callback)
        
        # 5. Verify calling log_callback updates the view
        test_msg = "Test log message"
        captured_options.log_callback(test_msg)
        
        # The view should have append_log called
        self.view.append_log.assert_called_with(test_msg)

    def test_view_clears_log_on_start(self):
        """Verify that the view clears results and log when organization starts."""
        self.organizer.organize_files.return_value = {"moved": 0, "errors": 0}
        self.controller.run_organization(dry_run=True)
        self.view.clear_results.assert_called()
        self.view.clear_log.assert_called()

    def test_after_main_uses_receiver(self):
        """Verify that after_main calls QTimer.singleShot with a receiver (self)."""
        from PySide6.QtCore import QTimer
        from pro_file_organizer.ui.main_window import OrganizerApp
        
        # We need a real OrganizerApp instance to test its after_main
        # But since it's a QWidget, we need to mock out its __init__ or use MagicMock
        # Alternatively, we can patch QTimer.singleShot and check how it's called
        with patch("PySide6.QtCore.QTimer.singleShot") as mock_single_shot:
            # We can't easily instantiate OrganizerApp without a real display/app
            # So let's mock the view object but call the real after_main method from the class
            mock_app = MagicMock(spec=OrganizerApp)
            mock_app.after_main = OrganizerApp.after_main.__get__(mock_app, OrganizerApp)
            
            test_func = lambda: None
            mock_app.after_main(100, test_func)
            
            # Verify singleShot was called with (ms, receiver, func)
            mock_single_shot.assert_called_with(100, mock_app, test_func)

if __name__ == "__main__":
    unittest.main()
