import time
from pathlib import Path

from .logger import logger


class FolderWatcherHandler:
    """Logic for handling file system events."""

    def __init__(self, callback, debounce=2.0):
        self.callback = callback
        self.debounce = debounce
        self.last_triggered = 0.0

    def dispatch(self, event):
        """Called by watchdog."""
        if not event.is_directory:
            if event.event_type in ("modified", "created"):
                self._trigger()

    def _trigger(self):
        current_time = time.time()
        if current_time - self.last_triggered > self.debounce:
            self.last_triggered = current_time
            self.callback()


class FolderWatcher:
    def __init__(self, folder_path, callback):
        self.folder_path = Path(folder_path)
        self.callback = callback
        self.observer = None
        self.handler = None

    def start(self, recursive=False):
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            if not self.folder_path.exists():
                logger.error(f"Cannot watch non-existent folder: {self.folder_path}")
                return False

            # Use composition: Create a real FileSystemEventHandler that delegates to our logic
            our_logic = FolderWatcherHandler(self.callback)

            class BridgeHandler(FileSystemEventHandler):
                def on_any_event(self, event):
                    our_logic.dispatch(event)

            self.handler = BridgeHandler()
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.folder_path), recursive=recursive)
            self.observer.start()
            logger.info(f"Started watching folder: {self.folder_path} (recursive={recursive})")
            return True
        except ImportError:
            logger.error("Watchdog library not installed. Install with 'pip install pro-file-organizer[watch]'")
            return False

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info(f"Stopped watching folder: {self.folder_path}")
