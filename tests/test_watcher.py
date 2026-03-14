import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pro_file_organizer.core.watcher import FolderWatcher, FolderWatcherHandler


class TestWatcher(unittest.TestCase):
    def test_handler_trigger(self):
        import time
        callback = MagicMock()
        handler = FolderWatcherHandler(callback, debounce=0.01)

        event = MagicMock()
        event.is_directory = False

        # Test on_created
        handler.on_created(event)
        callback.assert_called_once()

        # Test on_modified
        time.sleep(0.02)
        callback.reset_mock()
        handler.on_modified(event)
        callback.assert_called_once()

    def test_handler_debounce(self):
        callback = MagicMock()
        handler = FolderWatcherHandler(callback, debounce=100) # Long debounce

        event = MagicMock()
        event.is_directory = False

        handler._trigger()
        handler._trigger()

        self.assertEqual(callback.call_count, 1)

    def test_watcher_start_stop(self):
        callback = MagicMock()
        folder = Path("/tmp/fake_watch_dir")

        with patch('pro_file_organizer.core.watcher.Observer') as mock_observer_class:
            mock_observer = mock_observer_class.return_value
            watcher = FolderWatcher(folder, callback)

            # Case: Folder doesn't exist
            with patch('pathlib.Path.exists', return_value=False):
                watcher.start()
                mock_observer.schedule.assert_not_called()

            # Case: Folder exists
            with patch('pathlib.Path.exists', return_value=True):
                watcher.start()
                mock_observer.schedule.assert_called()
                mock_observer.start.assert_called()

            watcher.stop()
            mock_observer.stop.assert_called()
            mock_observer.join.assert_called()

if __name__ == '__main__':
    unittest.main()
