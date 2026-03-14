import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .logger import logger


class FolderWatcherHandler(FileSystemEventHandler):
    def __init__(self, callback, debounce=2.0):
        self.callback = callback
        self.debounce = debounce
        self.last_triggered = 0

    def on_modified(self, event):
        if not event.is_directory:
            self._trigger()

    def on_created(self, event):
        if not event.is_directory:
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
        self.observer = Observer()
        self.handler = FolderWatcherHandler(self.callback)

    def start(self):
        if not self.folder_path.exists():
            logger.error(f"Cannot watch non-existent folder: {self.folder_path}")
            return

        self.observer.schedule(self.handler, str(self.folder_path), recursive=False)
        self.observer.start()
        logger.info(f"Started watching folder: {self.folder_path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        logger.info(f"Stopped watching folder: {self.folder_path}")
