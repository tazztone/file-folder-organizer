import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# Default Configuration
DEFAULT_DIRECTORIES = {
    "Images": [".jpeg", ".jpg", ".tiff", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".psd"],
    "Videos": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp"],
    "Documents": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwi", ".xsn", ".xps", ".dotx", ".docm", ".dox", ".rvg", ".rtf", ".rtfd", ".wpd", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".pdf", ".txt", ".md"],
    "Archives": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"],
    "Audio": [".aac", ".aa", ".aac", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".raw", ".vox", ".wav", ".wma"],
    "Code": [".py", ".js", ".html", ".css", ".php", ".c", ".cpp", ".h", ".java", ".cs"],
    "Executables": [".exe", ".msi", ".bat", ".sh"]
}

class FileOrganizer:
    def __init__(self):
        self.directories = DEFAULT_DIRECTORIES.copy()
        self.extension_map = self._build_extension_map()
        self.history = []  # Stores [(new_path, old_path), ...]
        self.last_source_path = None
        self.excluded_names = {"app.py", "organizer.py", "config.json", "themes.py", "recent.json"}

    def _build_extension_map(self):
        return {ext: category for category, exts in self.directories.items() for ext in exts}

    def load_config(self, config_path="config.json"):
        """Loads configuration from a JSON file."""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    # Check if new format (has "directories" key)
                    if "directories" in data:
                        self.directories = data.get("directories", DEFAULT_DIRECTORIES)
                        self.excluded_names = set(data.get("excluded_names", self.excluded_names))
                    else:
                        # Fallback for old format
                        self.directories = data
                self.extension_map = self._build_extension_map()
                return True
            except Exception as e:
                print(f"Error loading config: {e}")
                return False
        return False

    def save_config(self, config_path="config.json"):
        """Saves current configuration to a JSON file."""
        try:
            with open(config_path, 'w') as f:
                json.dump({
                    "directories": self.directories,
                    "excluded_names": list(self.excluded_names)
                }, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_unique_path(self, path: Path) -> Path:
        """Generates a unique path by appending a counter if the file exists."""
        if not path.exists():
            return path
        counter = 1
        while True:
            new_path = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not new_path.exists():
                return new_path
            counter += 1

    def scan_files(self, source_path: Path, recursive=False):
        """Scans for files to process."""
        if recursive:
            iterator = source_path.rglob('*')
        else:
            iterator = source_path.iterdir()

        for item in iterator:
            if item.is_file() and item.name not in self.excluded_names:
                yield item

    def organize_files(self, source_path: Path, recursive=False, date_sort=False, del_empty=False, dry_run=False, progress_callback=None, log_callback=None):
        """
        Organizes files from source_path.

        Args:
            source_path (Path): The directory to organize.
            recursive (bool): Whether to look into subdirectories.
            date_sort (bool): Whether to sort by date (Year/Month).
            del_empty (bool): Whether to delete empty folders after moving.
            dry_run (bool): If True, only simulate moves.
            progress_callback (callable): Function(current, total)
            log_callback (callable): Function(message)

        Returns:
            dict: Statistics {"moved": int, "errors": int}
        """
        if not dry_run:
            self.history.clear()
            self.last_source_path = source_path

        if log_callback:
            log_callback(f"--- Starting {'Dry Run ' if dry_run else ''}Organization ---")

        # 1. Collect files first to know total count for progress bar
        try:
            files_to_move = list(self.scan_files(source_path, recursive))
            total_files = len(files_to_move)
        except Exception as e:
            if log_callback:
                log_callback(f"Error scanning files: {e}")
            return {"moved": 0, "errors": 1}

        moved_count = 0
        errors = 0

        for i, item in enumerate(files_to_move, 1):
            if progress_callback:
                progress_callback(i, total_files)

            try:
                category = self.extension_map.get(item.suffix.lower(), "Others")
                target_dir = source_path / category

                if date_sort:
                    try:
                        mtime = item.stat().st_mtime
                        dt = datetime.fromtimestamp(mtime)
                        year = dt.strftime("%Y")
                        month = dt.strftime("%B")
                        target_dir = target_dir / year / month
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Date error for {item.name}: {e}")

                # SKIP ALREADY ORGANIZED FILES
                # Resolve paths to handle potential relative/absolute mismatches
                if item.parent.resolve() == target_dir.resolve():
                     continue

                dest_path = target_dir / item.name

                # Determine final unique path
                final_dest_path = dest_path
                if not dry_run:
                    final_dest_path = self.get_unique_path(dest_path)

                # Show relative path for logging
                try:
                    rel_dest = final_dest_path.relative_to(source_path)
                except ValueError:
                    rel_dest = final_dest_path.name

                if dry_run:
                    if log_callback:
                        log_callback(f"[Dry Run] would move: {item.name} -> {rel_dest}")
                else:
                    final_dest_path.parent.mkdir(parents=True, exist_ok=True)
                    # Recalculate unique path right before move to be safe against race conditions (though single threaded logic)
                    final_dest_path = self.get_unique_path(final_dest_path)

                    shutil.move(str(item), final_dest_path)
                    self.history.append((final_dest_path, item))
                    if log_callback:
                        log_callback(f"Moved: {item.name} -> {rel_dest}")

                moved_count += 1

            except Exception as e:
                errors += 1
                if log_callback:
                    log_callback(f"ERROR moving {item.name}: {e}")

        # Delete Empty Folders
        if del_empty and not dry_run:
            if log_callback:
                log_callback("Cleaning up empty folders...")
            deleted_folders = 0
            for root_dir, dirs, files in os.walk(source_path, topdown=False):
                for name in dirs:
                    d = os.path.join(root_dir, name)
                    try:
                        os.rmdir(d)  # Only works if empty
                        deleted_folders += 1
                    except OSError:
                        pass
            if deleted_folders > 0 and log_callback:
                log_callback(f"Removed {deleted_folders} empty folders.")

        if log_callback:
            log_callback(f"--- Done. {'Would move' if dry_run else 'Moved'} {moved_count} files. ({errors} errors) ---")

        return {"moved": moved_count, "errors": errors}

    def undo_changes(self, log_callback=None):
        """Reverses the last organization run."""
        if not self.history:
            return 0

        if log_callback:
            log_callback("\n--- Undoing Changes ---")

        count = 0
        folders_to_check = set()

        # Process in reverse order
        for current_path, original_path in reversed(self.history):
            try:
                if current_path.exists():
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(current_path), str(original_path))
                    folders_to_check.add(current_path.parent)
                    count += 1
            except Exception as e:
                if log_callback:
                    log_callback(f"Failed to undo {current_path.name}: {e}")

        # Cleanup empty folders created/left by undo
        cleaned_folders = 0
        # Sort folders by path length descending to handle nested structures (like Date Sort)
        sorted_folders = sorted(folders_to_check, key=lambda p: len(str(p)), reverse=True)

        for folder in sorted_folders:
            try:
                curr = folder
                # Recursively delete empty parent folders, but stop at source_path
                while curr.exists() and (not self.last_source_path or curr != self.last_source_path):
                     # Check emptiness safely
                     if not any(curr.iterdir()):
                         curr.rmdir()
                         cleaned_folders += 1
                         curr = curr.parent
                     else:
                         break
            except OSError:
                pass

        if cleaned_folders > 0 and log_callback:
             log_callback(f"Cleaned up {cleaned_folders} empty folders during undo.")

        self.history.clear()
        if log_callback:
            log_callback(f"--- Undo Complete. Restored {count} files. ---")
        return count
