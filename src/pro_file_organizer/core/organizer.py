import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional, TypedDict, Union

from .constants import (
    DEFAULT_CATEGORY,
    DEFAULT_CONFIG_FILE,
    DEFAULT_DIRECTORIES,
    DEFAULT_ML_CATEGORIES,
    DEFAULT_UNDO_STACK_FILE,
    EXCLUDED_NAMES,
    MAX_UNDO_STACK,
    init_app_dirs,
)
from .logger import logger


class OrganizationResult(TypedDict, total=False):
    moved: int
    errors: int
    renamed: int
    duplicates: int
    rolled_back: bool
    report: list[dict]


@dataclass
class OrganizationOptions:
    """Options for the organization process."""

    source_path: Path
    recursive: bool = False
    date_sort: bool = False
    del_empty: bool = False
    dry_run: bool = False
    use_ml: bool = False
    detect_duplicates: bool = False
    rollback_on_error: bool = False
    progress_callback: Optional[Callable] = None
    log_callback: Optional[Callable] = None
    event_callback: Optional[Callable] = None
    check_stop: Optional[Callable] = None


class FileOrganizer:
    def __init__(self):
        self.directories = DEFAULT_DIRECTORIES.copy()
        self.ml_categories = DEFAULT_ML_CATEGORIES.copy()
        self.extension_map = self._build_extension_map()
        # undo_stack is a list of history records. Each record is a tuple: (history_list, last_source_path)
        # history_list is [(new_path, old_path), ...]
        self.undo_stack = []
        self.max_undo_stack = MAX_UNDO_STACK
        self.theme_mode = "System"
        self.ml_categorizer = None
        self.ml_confidence = 0.3

        # Exclusions
        self.excluded_names = EXCLUDED_NAMES.copy()
        self.excluded_extensions = set()  # e.g., {".tmp", ".log"}
        self.excluded_folders = EXCLUDED_NAMES.copy()

        # Ensure app directories exist on init
        init_app_dirs()
        self._load_undo_stack()

    def _build_extension_map(self) -> dict[str, str]:
        return {ext: category for category, exts in self.directories.items() for ext in exts}

    def _load_undo_stack(self):
        """Loads the undo stack from a JSON file."""
        if os.path.exists(DEFAULT_UNDO_STACK_FILE):
            try:
                with open(DEFAULT_UNDO_STACK_FILE, "r") as f:
                    data = json.load(f)
                    self.undo_stack = []
                    for item in data:
                        history = [(Path(p1), Path(p2)) for p1, p2 in item["history"]]
                        self.undo_stack.append({"history": history, "source_path": Path(item["source_path"])})
            except Exception as e:
                logger.error(f"Error loading undo stack: {e}")
                self.undo_stack = []

    def _save_undo_stack(self):
        """Saves the undo stack to a JSON file."""
        try:
            data = []
            for item in self.undo_stack:
                history = [(str(p1), str(p2)) for p1, p2 in item["history"]]
                data.append({"history": history, "source_path": str(item["source_path"])})
            with open(DEFAULT_UNDO_STACK_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving undo stack: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculates SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in 64KB chunks
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""

    def validate_config(self) -> list[str]:
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
        all_exts: dict[str, str] = {}
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

    def load_config(self, config_path: Union[str, Path] = DEFAULT_CONFIG_FILE) -> bool:
        """Loads configuration from a JSON file."""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)

                    if "directories" in data:
                        self.directories = data.get("directories", DEFAULT_DIRECTORIES.copy())
                        self.ml_categories = data.get("ml_categories", DEFAULT_ML_CATEGORIES.copy())
                        self.excluded_names = set(data.get("excluded_names", EXCLUDED_NAMES.copy()))
                        self.excluded_extensions = set(data.get("excluded_extensions", []))
                        self.excluded_folders = set(data.get("excluded_folders", EXCLUDED_NAMES.copy()))
                        self.theme_mode = data.get("theme_mode", "System")
                        self.ml_confidence = data.get("ml_confidence", 0.3)
                        self.max_undo_stack = data.get("max_undo_stack", MAX_UNDO_STACK)
                    else:
                        # Fallback for old format
                        self.directories = data

                self.extension_map = self._build_extension_map()
                return True
            except Exception as e:
                logger.error(f"Error loading config (resetting to defaults): {e}")
                # Reset to defaults on corruption
                self.directories = DEFAULT_DIRECTORIES.copy()
                self.ml_categories = DEFAULT_ML_CATEGORIES.copy()
                self.excluded_names = EXCLUDED_NAMES.copy()
                self.excluded_extensions = set()
                self.excluded_folders = EXCLUDED_NAMES.copy()
                self.extension_map = self._build_extension_map()
                return False
        return False

    def save_config(self, config_path: Union[str, Path] = DEFAULT_CONFIG_FILE) -> bool:
        """Saves current configuration to a JSON file."""
        # Block save if config is invalid (validate_config returns a non-empty error list)
        errors = self.validate_config()
        if errors:
            logger.error(f"Config validation failed, not saving: {errors}")
            return False
        try:
            p = Path(config_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as f:
                json.dump(
                    {
                        "directories": self.directories,
                        "ml_categories": self.ml_categories,
                        "excluded_names": list(self.excluded_names),
                        "excluded_extensions": list(self.excluded_extensions),
                        "excluded_folders": list(self.excluded_folders),
                        "theme_mode": self.theme_mode,
                        "ml_confidence": self.ml_confidence,
                        "max_undo_stack": self.max_undo_stack,
                    },
                    f,
                    indent=4,
                )
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def export_config_file(self, path: str) -> bool:
        """Exports the current configuration to a specified path."""
        return self.save_config(path)

    def import_config_file(self, path: str) -> bool:
        """Imports configuration from a specified path."""
        return self.load_config(path)

    def get_theme_mode(self) -> str:
        return self.theme_mode

    def save_theme_mode(self, mode: str) -> None:
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

    def scan_files(self, source_path: Path, recursive: bool = False) -> Iterable[Path]:
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

    def get_category(self, file_path: Path, use_ml: bool = False) -> tuple[str, float, str, Optional[str], float, str]:
        """
        Determines the target category for a file.
        Returns: (effective_category, confidence, method, ai_category, ai_confidence, extension_category)
        """
        # 1. Get Extension Category (always needed as fallback)
        ext = file_path.suffix.lower()
        ext_category = self.extension_map.get(ext, DEFAULT_CATEGORY)

        ai_category = None
        ai_confidence = 0.0
        ai_method = "extension"

        # 2. Try ML if enabled
        if use_ml:
            if not self.ml_categorizer:
                from .ml_organizer import MultimodalFileOrganizer
                self.ml_categorizer = MultimodalFileOrganizer(self.ml_categories)

            ai_category, ai_confidence, ai_method = self.ml_categorizer.smart_categorize(file_path, threshold=0.0)

            # If ML returned a valid result and meets current threshold
            if ai_category and ai_method != "extension" and ai_method != "ml-not-loaded":
                if ai_confidence >= self.ml_confidence:
                    return ai_category, ai_confidence, ai_method, ai_category, ai_confidence, ext_category

        # 3. Fallback to Extension
        return ext_category, 1.0, "extension", ai_category, ai_confidence, ext_category

    def organize_files(self, options: OrganizationOptions) -> OrganizationResult:
        """
        Organizes files based on provided options.
        """
        source_path = options.source_path
        recursive = options.recursive
        date_sort = options.date_sort
        del_empty = options.del_empty
        dry_run = options.dry_run
        use_ml = options.use_ml
        detect_duplicates = options.detect_duplicates
        rollback_on_error = options.rollback_on_error
        progress_callback = options.progress_callback
        log_callback = options.log_callback
        event_callback = options.event_callback
        check_stop = options.check_stop

        current_history = []
        report: list[dict] = []
        moved_count = 0
        renamed_count = 0
        errors = 0
        duplicates_count = 0

        # Known file hashes in the target tree to detect duplicates
        known_hashes: dict[str, Path] = {}

        # Pre-hash destination tree if requested
        if detect_duplicates:
            if log_callback:
                log_callback("Pre-scanning destination for duplicates...")

            for category in self.directories.keys():
                target_dir = source_path / category
                if target_dir.is_dir():
                    # Scan recursively for existing files
                    for root, _, files in os.walk(target_dir):
                        for file in files:
                            if file in self.excluded_names:
                                continue
                            file_path = Path(root) / file
                            if file_path.suffix.lower() in self.excluded_extensions:
                                continue

                            f_hash = self._get_file_hash(file_path)
                            if f_hash:
                                known_hashes[f_hash] = file_path

        # Ensure ML is ready if requested
        if use_ml and not self.ml_categorizer:
            # Lazy init
            from .ml_organizer import MultimodalFileOrganizer

            self.ml_categorizer = MultimodalFileOrganizer(self.ml_categories)
            if not self.ml_categorizer.models_loaded:
                if log_callback:
                    log_callback("Initializing ML models (this may take a while)...")

                def _ml_progress(msg, val=None):
                    if log_callback:
                        log_callback(f"[ML Init] {msg}")
                    if progress_callback and val is not None:
                        progress_callback(val, 1.0, f"Loading AI Models: {int(val * 100)}%")

                try:
                    self.ml_categorizer.load_models(progress_callback=_ml_progress)
                except Exception as e:
                    if log_callback:
                        log_callback(f"Failed to load ML models: {e}. Falling back to extension mode.")
                    use_ml = False

        if log_callback:
            log_callback(f"--- Starting {'Dry Run ' if dry_run else ''}Organization ---")

        # Collect files into a list once — avoids double directory scan
        try:
            all_files = list(self.scan_files(source_path, recursive))
        except Exception as e:
            if log_callback:
                log_callback(f"Error scanning files: {e}")
            return {"moved": 0, "errors": 1}

        total_files = len(all_files)

        for i, item in enumerate(all_files, 1):
            if check_stop and check_stop():
                if log_callback:
                    log_callback("Operation stopped by user.")
                break

            if progress_callback:
                progress_callback(i, total_files, item.name)

            try:
                # Get Category Logic
                category, confidence, method, ai_cat, ai_conf, ext_cat = self.get_category(item, use_ml)

                # DUPLICATE DETECTION
                if detect_duplicates:
                    file_hash = self._get_file_hash(item)
                    if file_hash:
                        if file_hash in known_hashes:
                            duplicates_count += 1
                            orig_path = known_hashes[file_hash]
                            if log_callback:
                                log_callback(f"SKIP DUPLICATE: {item.name} (already at {orig_path.name})")

                            report.append(
                                {
                                    "file": item.name,
                                    "status": "duplicate",
                                    "source": str(item),
                                    "duplicate_of": str(orig_path),
                                }
                            )

                            if event_callback:
                                event_callback(
                                    {
                                        "type": "duplicate",
                                        "file": item.name,
                                        "source": str(item),
                                        "duplicate_of": str(orig_path),
                                    }
                                )
                            continue
                        else:
                            known_hashes[file_hash] = item

                # If ML is used, category might be a nested path string "Images/Personal"
                target_dir = source_path / category

                # Calculate relative destination dir to allow UI to rebuild paths
                relative_dir_parts = []
                if date_sort:
                    try:
                        mtime = item.stat().st_mtime
                        dt = datetime.fromtimestamp(mtime)
                        year = dt.strftime("%Y")
                        month = dt.strftime("%B")
                        target_dir = target_dir / year / month
                        relative_dir_parts = [year, month]
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Date error for {item.name}: {e}")

                relative_dir = "/".join(relative_dir_parts) if relative_dir_parts else ""

                # SAFETY CHECK: Ensure the target directory is WITHIN the source_path
                try:
                    target_dir.resolve().relative_to(source_path.resolve())
                except ValueError:
                    msg = f"SAFETY BREACH: Target {target_dir} is outside source {source_path}. Skipping {item.name}."
                    if log_callback:
                        log_callback(msg)
                    logger.error(msg)
                    errors += 1
                    continue

                # SKIP ALREADY ORGANIZED FILES
                if item.parent.resolve() == target_dir.resolve():
                    continue

                dest_path = target_dir / item.name

                # Determine final path
                if dry_run:
                    final_dest_path = dest_path
                else:
                    # Ensure target directory exists
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    # Calculate unique path once right before the move
                    final_dest_path = self.get_unique_path(dest_path)

                # Show relative path for logging
                rel_dest: Union[Path, str]
                try:
                    rel_dest = final_dest_path.relative_to(source_path)
                except ValueError:
                    rel_dest = final_dest_path.name

                log_prefix = "[Dry Run] " if dry_run else ""
                log_suffix = f" (ML: {method}, {confidence:.2f})" if use_ml and method != "extension" else ""

                event_data = {
                    "type": "move",
                    "file": item.name,
                    "source": str(item),
                    "destination": str(final_dest_path),
                    "relative_dir": relative_dir,
                    "category": category,
                    "method": method,
                    "confidence": confidence,
                    "dry_run": dry_run,
                    "renamed": final_dest_path.name != item.name,
                    "ai_category": ai_cat,
                    "ai_confidence": ai_conf,
                    "ai_method": method if method != "extension" else "ml",
                    "ext_category": ext_cat,
                }

                if dry_run:
                    if log_callback:
                        log_callback(f"{log_prefix}would move: {item.name} -> {rel_dest}{log_suffix}")
                    if event_callback:
                        event_callback(event_data)

                    report.append(
                        {
                            "file": item.name,
                            "status": "dry_run",
                            "source": str(item),
                            "destination": str(final_dest_path),
                            "category": category,
                            "method": method,
                            "confidence": confidence,
                            "ai_category": ai_cat,
                            "ai_confidence": ai_conf,
                            "ext_category": ext_cat,
                        }
                    )
                else:
                    shutil.move(str(item), final_dest_path)
                    current_history.append((final_dest_path, item))

                    if final_dest_path.name != item.name:
                        event_data["new_name"] = final_dest_path.name
                        renamed_count += 1

                    if log_callback:
                        msg = f"Moved: {item.name} -> {rel_dest}{log_suffix}"
                        if final_dest_path.name != item.name:
                            msg = f"Renamed & Moved: {item.name} -> {final_dest_path.name} (in {rel_dest}){log_suffix}"
                        log_callback(msg)

                    if event_callback:
                        event_callback(event_data)

                    report.append(
                        {
                            "file": item.name,
                            "status": "moved",
                            "source": str(item),
                            "destination": str(final_dest_path),
                            "category": category,
                            "method": method,
                            "confidence": confidence,
                            "renamed": final_dest_path.name != item.name,
                        }
                    )

                moved_count += 1

            except PermissionError as e:
                errors += 1
                msg = f"PERMISSION ERROR: Cannot move {item.name} (file may be in use): {e}"
                if log_callback:
                    log_callback(msg)
                logger.error(msg)

                report.append({"file": item.name, "status": "error", "error_type": "PermissionError", "error": str(e)})

                if event_callback:
                    event_callback(
                        {"type": "error", "file": item.name, "error": str(e), "error_type": "PermissionError"}
                    )

                if rollback_on_error and not dry_run:
                    if log_callback:
                        log_callback("Critical error encountered. Rolling back changes...")
                    self._undo_history(current_history, source_path, log_callback)
                    return {
                        "moved": moved_count,
                        "errors": errors,
                        "renamed": renamed_count,
                        "duplicates": duplicates_count,
                        "rolled_back": True,
                        "report": report,
                    }

            except OSError as e:
                errors += 1
                msg = f"OS ERROR moving {item.name}: {e}"
                if log_callback:
                    log_callback(msg)
                logger.error(msg)

                report.append({"file": item.name, "status": "error", "error_type": "OSError", "error": str(e)})

                if event_callback:
                    event_callback({"type": "error", "file": item.name, "error": str(e), "error_type": "OSError"})

                if rollback_on_error and not dry_run:
                    if log_callback:
                        log_callback("Critical error encountered. Rolling back changes...")
                    self._undo_history(current_history, source_path, log_callback)
                    return {
                        "moved": moved_count,
                        "errors": errors,
                        "renamed": renamed_count,
                        "duplicates": duplicates_count,
                        "rolled_back": True,
                        "report": report,
                    }

            except Exception as e:
                errors += 1
                msg = f"UNEXPECTED ERROR moving {item.name}: {type(e).__name__}: {e}"
                if log_callback:
                    log_callback(msg)
                logger.error(msg)

                report.append({"file": item.name, "status": "error", "error_type": type(e).__name__, "error": str(e)})

                if event_callback:
                    event_callback(
                        {"type": "error", "file": item.name, "error": str(e), "error_type": type(e).__name__}
                    )

                if rollback_on_error and not dry_run:
                    if log_callback:
                        log_callback("Critical error encountered. Rolling back changes...")
                    # Rollback only current partial history
                    self._undo_history(current_history, source_path, log_callback)
                    return {
                        "moved": moved_count,
                        "errors": errors,
                        "renamed": renamed_count,
                        "duplicates": duplicates_count,
                        "rolled_back": True,
                        "report": report,
                    }

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
                        # Convert to absolute path to be safe
                        d_path = Path(d).resolve()
                        if d_path.is_dir() and not any(d_path.iterdir()):
                            os.rmdir(d)
                            deleted_folders += 1
                    except Exception:
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
            self.undo_stack.append({"history": current_history, "source_path": source_path})
            # Enforce max undo stack size
            if len(self.undo_stack) > self.max_undo_stack:
                self.undo_stack.pop(0)
            self._save_undo_stack()

        return {
            "moved": moved_count,
            "errors": errors,
            "renamed": renamed_count,
            "duplicates": duplicates_count,
            "report": report,
        }

    def undo_changes(self, log_callback: Optional[Callable] = None) -> int:
        """Reverses the last organization run."""
        if not self.undo_stack:
            if log_callback:
                log_callback("Nothing to undo.")
            return 0

        # Pop the last operation
        last_op = self.undo_stack.pop()
        result = self._undo_history(last_op["history"], last_op["source_path"], log_callback)
        self._save_undo_stack()
        return result

    def _undo_history(self, history: list, source_path: Path, log_callback: Optional[Callable] = None) -> int:
        """Internal helper to reverse a list of file operations."""
        if log_callback:
            log_callback("\n--- Undoing Changes ---")

        count = 0
        folders_to_check = set()

        # Process in reverse order
        for current_path, original_path in reversed(history):
            try:
                # SAFETY CHECK: Ensure the original path is WITHIN the source_path
                try:
                    original_path.resolve().relative_to(source_path.resolve())
                except ValueError:
                    msg = f"SAFETY BREACH during Undo: {original_path} is outside source {source_path}. Skipping."
                    if log_callback:
                        log_callback(msg)
                    logger.error(msg)
                    continue

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
                while curr.exists() and (not source_path or curr.resolve() != source_path.resolve()):
                    if not any(curr.iterdir()):
                        curr.rmdir()
                        cleaned_folders += 1
                        curr = curr.parent
                    else:
                        break
            except Exception as e:
                if log_callback:
                    log_callback(f"Folder cleanup error for {folder}: {e}")
                logger.error(f"Folder cleanup error for {folder}: {e}")

        if cleaned_folders > 0 and log_callback:
            log_callback(f"Cleaned up {cleaned_folders} empty folders during undo.")

        if log_callback:
            log_callback(f"--- Undo Complete. Restored {count} files. ---")
        return count
