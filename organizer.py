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
        # undo_stack is a list of history records. Each record is a tuple: (history_list, last_source_path)
        # history_list is [(new_path, old_path), ...]
        self.undo_stack = []
        self.max_undo_stack = 5
        self.theme_mode = "System"

        # Exclusions
        self.excluded_names = {"app.py", "organizer.py", "config.json", "themes.py", "recent.json", "batch_config.json"}
        self.excluded_extensions = set() # e.g., {".tmp", ".log"}
        self.excluded_folders = set() # e.g., {"node_modules", ".git"}

    def _build_extension_map(self):
        return {ext: category for category, exts in self.directories.items() for ext in exts}

    def validate_config(self):
        """
        Validates the current configuration.
        Returns a list of error messages. If list is empty, config is valid.
        """
        errors = []

        # Check for empty category names
        for cat in self.directories:
            if not cat or not cat.strip():
                errors.append("Category name cannot be empty.")
            # Ensure category names do not contain path separators
            if os.sep in cat or (os.altsep and os.altsep in cat):
                 errors.append(f"Category name '{cat}' cannot contain path separators.")

        # Check for invalid extensions and duplicates
        all_exts = {}
        for cat, exts in self.directories.items():
            for ext in exts:
                if not ext.startswith("."):
                    errors.append(f"Invalid extension '{ext}' in category '{cat}': Must start with '.'")

                if ext in all_exts:
                    other_cat = all_exts[ext]
                    errors.append(f"Duplicate extension '{ext}' found in '{cat}' and '{other_cat}'")
                else:
                    all_exts[ext] = cat

        return errors

    def load_config(self, config_path="config.json"):
        """Loads configuration from a JSON file."""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)

                    if "directories" in data:
                        self.directories = data.get("directories", DEFAULT_DIRECTORIES)
                        self.excluded_names = set(data.get("excluded_names", self.excluded_names))
                        self.excluded_extensions = set(data.get("excluded_extensions", []))
                        self.excluded_folders = set(data.get("excluded_folders", []))
                        self.theme_mode = data.get("theme_mode", "System")
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
        if self.validate_config():
            return False
        try:
            with open(config_path, 'w') as f:
                json.dump({
                    "directories": self.directories,
                    "excluded_names": list(self.excluded_names),
                    "excluded_extensions": list(self.excluded_extensions),
                    "excluded_folders": list(self.excluded_folders),
                    "theme_mode": self.theme_mode
                }, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def export_config_file(self, path):
        """Exports the current configuration to a specified path."""
        return self.save_config(path)

    def import_config_file(self, path):
        """Imports configuration from a specified path."""
        return self.load_config(path)

    def get_theme_mode(self):
        return self.theme_mode

    def save_theme_mode(self, mode):
        self.theme_mode = mode
        self.save_config()

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
        """Scans for files to process, respecting exclusions."""
        # Check if source_path itself is excluded (though unlikely to be passed if selected by user, good safety)
        if source_path.name in self.excluded_folders:
            return

        if recursive:
            # use os.walk to properly exclude directories
            for root, dirs, files in os.walk(source_path):
                # Filter dirs in-place to prevent walking into excluded directories
                dirs[:] = [d for d in dirs if d not in self.excluded_folders]

                for file in files:
                    if file in self.excluded_names:
                        continue

                    file_path = Path(root) / file
                    if file_path.suffix.lower() in self.excluded_extensions:
                        continue

                    yield file_path
        else:
            for item in source_path.iterdir():
                if item.is_file():
                    if item.name in self.excluded_names:
                        continue
                    if item.suffix.lower() in self.excluded_extensions:
                        continue
                    yield item

    def organize_files(self, source_path: Path, recursive=False, date_sort=False, del_empty=False, dry_run=False, progress_callback=None, log_callback=None, check_stop=None, rollback_on_error=False):
        """
        Organizes files from source_path.
        """
        current_history = []

        if log_callback:
            log_callback(f"--- Starting {'Dry Run ' if dry_run else ''}Organization ---")

        # 1. Count files first (to allow large dirs without full list in memory)
        total_files = 0
        try:
             # Just count first
             for _ in self.scan_files(source_path, recursive):
                 total_files += 1
        except Exception as e:
             if log_callback:
                 log_callback(f"Error scanning files: {e}")
             return {"moved": 0, "errors": 1}

        moved_count = 0
        renamed_count = 0
        errors = 0

        # 2. Iterate again to process
        for i, item in enumerate(self.scan_files(source_path, recursive), 1):
            if check_stop and check_stop():
                if log_callback:
                    log_callback("Operation stopped by user.")
                break

            if progress_callback:
                progress_callback(i, total_files, item.name)

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
                    # Recalculate unique path right before move to be safe against race conditions
                    final_dest_path_unique = self.get_unique_path(final_dest_path)

                    shutil.move(str(item), final_dest_path_unique)
                    current_history.append((final_dest_path_unique, item))
                    if log_callback:
                        msg = f"Moved: {item.name} -> {rel_dest}"
                        if final_dest_path_unique != final_dest_path:
                             msg = f"Renamed & Moved: {item.name} -> {final_dest_path_unique.name} (in {rel_dest})"
                             renamed_count += 1
                        log_callback(msg)

                moved_count += 1

            except Exception as e:
                errors += 1
                if log_callback:
                    log_callback(f"ERROR moving {item.name}: {e}")

                if rollback_on_error and not dry_run:
                     if log_callback:
                         log_callback("Critical error encountered. Rolling back changes...")
                     # Add partial history to undo stack to allow undo
                     self.undo_stack.append({
                        "history": current_history,
                        "source_path": source_path
                     })
                     self.undo_changes(log_callback)
                     return {"moved": moved_count, "errors": errors, "renamed": renamed_count, "rolled_back": True}

        # Delete Empty Folders
        if del_empty and not dry_run:
            if log_callback:
                log_callback("Cleaning up empty folders...")
            deleted_folders = 0
            for root_dir, dirs, files in os.walk(source_path, topdown=False):
                for name in dirs:
                    # Don't delete excluded folders even if empty (though we shouldn't have entered them)
                    if name in self.excluded_folders:
                        continue

                    d = os.path.join(root_dir, name)
                    try:
                        os.rmdir(d)  # Only works if empty
                        deleted_folders += 1
                    except OSError:
                        pass
            if deleted_folders > 0 and log_callback:
                log_callback(f"Removed {deleted_folders} empty folders.")

        if log_callback:
            summary = f"--- Done. {'Would move' if dry_run else 'Moved'} {moved_count} files."
            if renamed_count > 0:
                summary += f" ({renamed_count} renamed)"
            summary += f". ({errors} errors) ---"
            log_callback(summary)

        if not dry_run and moved_count > 0:
            self.undo_stack.append({
                "history": current_history,
                "source_path": source_path
            })
            # Enforce max undo stack size
            if len(self.undo_stack) > self.max_undo_stack:
                self.undo_stack.pop(0)

        return {"moved": moved_count, "errors": errors, "renamed": renamed_count}

    def undo_changes(self, log_callback=None):
        """Reverses the last organization run."""
        if not self.undo_stack:
            if log_callback:
                log_callback("Nothing to undo.")
            return 0

        # Pop the last operation
        last_op = self.undo_stack.pop()
        history = last_op["history"]
        source_path = last_op["source_path"]

        if log_callback:
            log_callback("\n--- Undoing Changes ---")

        count = 0
        folders_to_check = set()

        # Process in reverse order
        for current_path, original_path in reversed(history):
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
        sorted_folders = sorted(folders_to_check, key=lambda p: len(str(p)), reverse=True)

        for folder in sorted_folders:
            try:
                curr = folder
                # Recursively delete empty parent folders, but stop at source_path
                while curr.exists() and (not source_path or curr != source_path):
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

        if log_callback:
            log_callback(f"--- Undo Complete. Restored {count} files. ---")
        return count
