import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Logic only tests, no need for UI mocks here
from pro_file_organizer.core.ml_organizer import MultimodalFileOrganizer
from pro_file_organizer.core.organizer import FileOrganizer
from pro_file_organizer.ui.main_window_controller import MainWindowController


class TestMainWindowController(unittest.TestCase):
    def setUp(self):
        self.view = MagicMock()
        self.organizer = MagicMock(spec=FileOrganizer)
        self.ml_organizer = MagicMock(spec=MultimodalFileOrganizer)

        # Default return values for view getters
        self.view.confirm_action.return_value = True
        self.view.get_recursive_val.return_value = False
        self.view.get_date_sort_val.return_value = False
        self.view.get_del_empty_val.return_value = False
        self.view.get_ai_confidence.return_value = 0.3

        def side_effect(path, mode="r", *args, **kwargs):
            p_str = str(path)
            if "stats.json" in p_str:
                return mock_open(read_data='{"total_files": 10, "last_run": "2026-03-13"}')()
            if "recent.json" in p_str:
                return mock_open(read_data='["/tmp/recent1"]')()
            return mock_open()()

        with patch("builtins.open", side_effect=side_effect):
            with patch("pathlib.Path.exists", return_value=True):
                self.controller = MainWindowController(self.view, self.organizer, self.ml_organizer)

    def test_init_load_errors(self):
        # Test exception path for load_stats and load_recent
        with patch("builtins.open", side_effect=Exception("IO Error")):
            c = MainWindowController(self.view, self.organizer, self.ml_organizer)
            self.assertEqual(c.recent_folders, [])

    def test_save_stats_error(self):
        with patch("os.makedirs", side_effect=Exception("Disk full")):
            self.controller.save_stats()  # Should not raise

    def test_save_recent_error(self):
        with patch("os.makedirs", side_effect=Exception("Perm Error")):
            self.controller.save_recent()  # Should not raise

    def test_undo_action_logic(self):
        # Empty stack
        self.organizer.undo_stack = []
        self.controller.undo_action()
        self.view.show_error.assert_called_with("Nothing to undo", "The undo stack is empty.")

        # With stack - confirmed
        self.view.show_error.reset_mock()
        self.organizer.undo_stack = [MagicMock()]
        self.view.confirm_action.return_value = True
        self.controller.undo_action()
        self.organizer.undo_changes.assert_called()
        self.view.show_info.assert_called()

        # With stack - cancelled
        self.organizer.undo_changes.reset_mock()
        self.view.confirm_action.return_value = False
        self.controller.undo_action()
        self.organizer.undo_changes.assert_not_called()

    def test_toggle_ai_download_needed(self):
        # User confirms download
        self.ml_organizer.models_exist.return_value = False
        self.view.confirm_action.return_value = True
        self.controller.toggle_ai(True)
        self.view.show_model_download.assert_called()

        # User cancels download
        self.view.confirm_action.return_value = False
        self.controller.toggle_ai(True)
        self.assertFalse(self.controller.ai_enabled)
        self.view.set_ai_switch_state.assert_called_with(False)

    def test_toggle_ai_load_success(self):
        self.ml_organizer.models_exist.return_value = True
        self.ml_organizer.load_models.return_value = True

        with patch("threading.Thread") as mock_thread_class:
            mock_thread_instance = MagicMock()
            mock_thread_class.return_value = mock_thread_instance

            def side_effect():
                target = mock_thread_class.call_args[1].get("target")
                if target:
                    target()

            mock_thread_instance.start.side_effect = side_effect

            self.view.after_main.side_effect = lambda t, f: f()

            self.controller.toggle_ai(True)
            self.assertTrue(self.controller.ai_enabled)
            self.view.enable_ai_ui.assert_called()

    def test_toggle_ai_load_fail(self):
        self.ml_organizer.models_exist.return_value = True
        self.ml_organizer.load_models.return_value = False

        with patch("threading.Thread") as mock_thread_class:
            mock_thread_instance = MagicMock()
            mock_thread_class.return_value = mock_thread_instance

            def side_effect():
                target = mock_thread_class.call_args[1].get("target")
                if target:
                    target()

            mock_thread_instance.start.side_effect = side_effect

            self.view.after_main.side_effect = lambda t, f: f()

            self.controller.toggle_ai(True)
            self.assertFalse(self.controller.ai_enabled)
            self.view.show_error.assert_called_with("AI Error", "Failed to load models.")

    def test_on_model_download_complete(self):
        # Success
        self.ml_organizer.models_exist.return_value = True
        self.controller._on_model_download_complete(True)
        self.ml_organizer.models_exist.assert_called()

        # Failure
        self.controller._on_model_download_complete(False)
        self.assertFalse(self.controller.ai_enabled)
        self.view.show_error.assert_called_with("Download Failed", "Could not download AI models.")

    def test_run_organization_validation(self):
        # No folder
        self.controller.selected_path = None
        self.controller.run_organization()
        self.view.show_error.assert_called_with("No Folder", "Please select a folder first.")

        # Already running
        self.controller.selected_path = Path("/tmp")
        self.controller.is_running = True
        self.view.set_running_state.reset_mock()
        self.controller.run_organization()
        self.view.set_running_state.assert_not_called()

        # Confirmed vs Cancelled
        self.controller.is_running = False
        self.view.confirm_action.return_value = False
        self.controller.run_organization(dry_run=False)
        self.view.set_running_state.assert_not_called()

    def test_run_organization_logic(self):
        self.controller.selected_path = Path("/tmp")
        self.controller.ai_enabled = True
        self.view.get_ai_confidence.return_value = 0.5

        with patch("threading.Thread") as mock_thread_class:
            mock_thread_instance = MagicMock()
            mock_thread_class.return_value = mock_thread_instance

            def side_effect():
                target = mock_thread_class.call_args[1].get("target")
                args = mock_thread_class.call_args[1].get("args", ())
                if target:
                    target(*args)

            mock_thread_instance.start.side_effect = side_effect

            self.view.after_main.side_effect = lambda t, f: f()
            self.organizer.organize_files.return_value = {"moved": 1}

            self.controller.run_organization(dry_run=True)
            self.assertFalse(self.controller.is_running)

            # Verify callbacks captured and called
            options = self.organizer.organize_files.call_args[0][0]

            on_event = options.event_callback
            on_event({"file": "test"})
            self.view.add_result_card.assert_called()

            on_progress = options.progress_callback
            on_progress(1, 10, "f")
            self.view.update_progress.assert_called()

    def test_on_complete_branches_extended(self):
        # Case 1: Success path
        stats = {"moved": 5}
        self.controller._on_complete(stats, dry_run=False)
        self.view.show_status.assert_called_with("Done! Moved 5 files.")

        # Case 2: Success with error count
        stats = {"moved": 5, "errors": 2}
        self.controller._on_complete(stats, dry_run=False)
        self.view.show_status.assert_called_with("Done! Moved 5 files. (2 errors)")

        # Case 3: Stats not a dict
        self.controller.stats = None
        self.controller._on_complete({"moved": 1}, dry_run=False)
        self.assertEqual(self.controller.stats["total_files"], 1)

    def test_on_recent_select(self):
        with patch("pathlib.Path.is_dir", return_value=True):
            self.controller.on_recent_select("/tmp/dir2")
            self.assertEqual(self.controller.selected_path, Path("/tmp/dir2"))

        # Ignore Recent...
        self.controller.selected_path = None
        self.controller.on_recent_select("Recent...")
        self.assertIsNone(self.controller.selected_path)

    def test_toggle_watch(self):
        # Case 1: No path selected
        self.controller.selected_path = None
        self.controller.toggle_watch(True)
        self.view.show_error.assert_called_with("No Folder", "Select a folder to watch first.")
        self.view.set_watch_switch_state.assert_called_with(False)

        # Case: Path selected, start watcher
        self.controller.selected_path = Path("/tmp")
        self.view.get_recursive_val.return_value = True
        with patch("pro_file_organizer.ui.main_window_controller.FolderWatcher") as mock_watcher_class:
            mock_watcher = mock_watcher_class.return_value
            self.controller.toggle_watch(True)
            mock_watcher.start.assert_called_with(recursive=True)
            self.assertEqual(self.controller.watcher, mock_watcher)

            # Case 3: Stop watcher
            self.controller.toggle_watch(False)
            mock_watcher.stop.assert_called()
            self.assertIsNone(self.controller.watcher)

    def test_on_watch_trigger(self):
        self.controller.selected_path = Path("/tmp")
        self.controller.is_running = False

        with patch.object(self.controller, "run_organization") as mock_run:
            self.controller._on_watch_trigger()
            mock_run.assert_called_with(dry_run=False, from_watcher=True)

            # Case: already running
            mock_run.reset_mock()
            self.controller.is_running = True
            self.controller._on_watch_trigger()
            mock_run.assert_not_called()

    def test_on_category_toggle(self):
        """Test toggling category visibility updates state and triggers refresh."""
        self.controller._cached_preview = [{"category": "Images"}]
        with patch.object(self.controller, "_refresh_preview") as mock_refresh:
            # Hide category
            self.controller.on_category_toggle("Images", False)
            self.assertIn("Images", self.controller._hidden_categories)
            mock_refresh.assert_called_once()

            mock_refresh.reset_mock()

            # Show category
            self.controller.on_category_toggle("Images", True)
            self.assertNotIn("Images", self.controller._hidden_categories)
            mock_refresh.assert_called_once()

    def test_on_sort_changed(self):
        """Test changing sort key updates state and triggers refresh."""
        self.controller._cached_preview = [{"category": "Images"}]
        with patch.object(self.controller, "_refresh_preview") as mock_refresh:
            self.controller.on_sort_changed("name")
            self.assertEqual(self.controller._sort_key, "name")
            mock_refresh.assert_called_once()


if __name__ == "__main__":
    unittest.main()
