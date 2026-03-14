import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pro_file_organizer.core.watcher import FolderWatcher, FolderWatcherHandler


class TestWatcher(unittest.TestCase):
    def test_handler_dispatch(self):
        import time
        callback = MagicMock()
        handler = FolderWatcherHandler(callback, debounce=0.01)

        event = MagicMock()
        event.is_directory = False
        event.event_type = "created"

        # Test dispatch
        handler.dispatch(event)
        callback.assert_called_once()

        # Test debounce
        callback.reset_mock()
        handler.dispatch(event)
        callback.assert_not_called()

        time.sleep(0.02)
        handler.dispatch(event)
        callback.assert_called_once()

    def test_watcher_start_stop(self):
        callback = MagicMock()
        folder = Path("/tmp/fake_watch_dir")

        # Mock watchdog
        mock_observer_class = MagicMock()
        mock_handler_class = MagicMock()

        with patch.dict('sys.modules', {
            'watchdog.observers': MagicMock(Observer=mock_observer_class),
            'watchdog.events': MagicMock(FileSystemEventHandler=mock_handler_class)
        }):
            watcher = FolderWatcher(folder, callback)

            # Case: Folder doesn't exist
            with patch('pathlib.Path.exists', return_value=False):
                self.assertFalse(watcher.start())

            # Case: Folder exists
            with patch('pathlib.Path.exists', return_value=True):
                self.assertTrue(watcher.start(recursive=True))
                mock_observer_class.return_value.schedule.assert_called_with(
                    watcher.handler, str(folder), recursive=True
                )
                mock_observer_class.return_value.start.assert_called()

            watcher.stop()
            mock_observer_class.return_value.stop.assert_called()
            mock_observer_class.return_value.join.assert_called()

    def test_watcher_import_error(self):
        callback = MagicMock()
        folder = Path("/tmp/fake_watch_dir")

        with patch('pro_file_organizer.core.watcher.Path.exists', return_value=True):
            with patch('builtins.__import__', side_effect=ImportError):
                watcher = FolderWatcher(folder, callback)
                self.assertFalse(watcher.start())

if __name__ == '__main__':
    unittest.main()
