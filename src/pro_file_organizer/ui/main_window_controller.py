import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from pro_file_organizer.core.organizer import OrganizationOptions
from pro_file_organizer.core.watcher import FolderWatcher


class MainWindowController:
    """
    Controller that handles the logic for the Pro File Organizer UI.
    Decoupled from customtkinter widgets for testability.
    """

    def __init__(self, view: Any, organizer: Any, ml_organizer: Any):
        self.view = view
        self.organizer = organizer
        self.ml_organizer = ml_organizer

        self.selected_path: Optional[Path] = None
        self.is_running = False
        self.ai_enabled = False
        self.watcher: Optional[FolderWatcher] = None
        self.recent_folders: List[str] = []
        self.stats = {"total_files": 0, "last_run": "Never"}
        self._cached_preview: List[dict] = []
        self._source_path_for_preview: Optional[Path] = None

        self.load_stats()
        self.load_recent()

    def set_folder(self, path_str):
        if not path_str:
            return
        path = Path(path_str)
        if path.is_dir():
            self.selected_path = path
            self.add_recent(str(path))
            self.view.update_folder_display(str(path))
            self.view.clear_results()
            self.view.clear_log()
        else:
            self.view.show_error("Invalid Directory", f"The path {path_str} is not a valid directory.")

    def add_recent(self, path):
        if path in self.recent_folders:
            self.recent_folders.remove(path)
        self.recent_folders.insert(0, path)
        self.recent_folders = self.recent_folders[:10]
        self.save_recent()
        self.view.update_recent_menu(self.recent_folders)

    def load_recent(self):
        try:
            recent_file = Path("config/recent.json")
            if recent_file.exists():
                with open(recent_file, "r") as f:
                    self.recent_folders = json.load(f)
        except Exception:
            self.recent_folders = []

    def save_recent(self):
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/recent.json", "w") as f:
                # Save as strings
                json.dump([str(p) for p in self.recent_folders], f)
        except Exception:
            pass

    def on_recent_select(self, folder):
        if folder != "Recent...":
            self.set_folder(folder)

    def undo_action(self):
        if self.organizer.undo_stack:
            if self.view.confirm_action("Undo?", "Rollback last organization?"):
                self.organizer.undo_changes(log_callback=lambda m: self.view.show_status(m))
                self.view.show_info("Undo complete", "Last operation was rolled back.")
                self.view.clear_results()
        else:
            self.view.show_error("Nothing to undo", "The undo stack is empty.")

    def open_settings(self):
        self.view.show_settings(self.organizer)

    def open_batch(self):
        self.view.show_batch(self.organizer)

    def load_stats(self):
        try:
            stats_file = Path("config/stats.json")
            if stats_file.exists():
                with open(stats_file, "r") as f:
                    self.stats = json.load(f)
        except Exception:
            pass
        self.view.update_stats_display(self.stats)

    def save_stats(self):
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/stats.json", "w") as f:
                json.dump(self.stats, f)
        except Exception:
            pass

    def toggle_ai(self, enabled):
        if enabled:
            # Check if models exist
            if not self.ml_organizer.models_exist():
                if self.view.confirm_action("Download Models?", "AI models (~2GB) need to be downloaded. Continue?"):
                    self.view.show_model_download(self._on_model_download_complete)
                    return  # Will enable after download
                else:
                    self.ai_enabled = False
                    self.view.set_ai_switch_state(False)
                    return

            # Models exist, try to load
            self.view.show_status("Loading AI Models...")

            def load_task():
                def thread_safe_progress(msg, pct):
                    self.view.after_main(0, lambda: self.view.update_progress(pct, 1.0, msg))

                success = self.ml_organizer.load_models(progress_callback=thread_safe_progress)
                if success:
                    self.ai_enabled = True
                    self.view.after_main(0, self.view.enable_ai_ui)
                    self.view.after_main(0, lambda: self.view.show_status("AI Ready"))
                else:
                    self.ai_enabled = False
                    self.view.after_main(0, lambda: self.view.set_ai_switch_state(False))
                    self.view.after_main(0, lambda: self.view.show_error("AI Error", "Failed to load models."))

            threading.Thread(target=load_task, daemon=True).start()
        else:
            self.ai_enabled = False
            self.view.disable_ai_ui()
            self.view.show_status("AI Disabled")

    def _on_model_download_complete(self, success):
        if success:
            self.toggle_ai(True)
        else:
            self.ai_enabled = False
            self.view.set_ai_switch_state(False)
            self.view.show_error("Download Failed", "Could not download AI models.")

    def toggle_watch(self, enabled):
        if enabled:
            if not self.selected_path:
                self.view.show_error("No Folder", "Select a folder to watch first.")
                self.view.set_watch_switch_state(False)
                return

            self.watcher = FolderWatcher(self.selected_path, lambda: self.view.after_main(0, self._on_watch_trigger))
            if self.watcher.start(recursive=self.view.get_recursive_val()):
                self.view.show_status(f"Watching: {self.selected_path.name}")
            else:
                self.view.show_error(
                    "Feature Not Installed",
                    "The 'watchdog' library is required for this feature.\n"
                    "Install it with: pip install pro-file-organizer[watch]",
                )
                self.view.set_watch_switch_state(False)
                self.watcher = None
        else:
            if self.watcher:
                self.watcher.stop()
                self.watcher = None
            self.view.show_status("Watcher disabled")

    def _on_watch_trigger(self):
        if not self.is_running:
            self.run_organization(dry_run=False, from_watcher=True)

    def run_organization(self, dry_run=False, from_watcher=False):
        if not self.selected_path:
            self.view.show_error("No Folder", "Please select a folder first.")
            return

        if self.is_running:
            return

        if (
            not dry_run
            and not from_watcher
            and not self.view.confirm_action("Confirm", f"Organize files in {self.selected_path}?")
        ):
            return

        self.is_running = True
        self.view.set_running_state(True)
        self.view.clear_results()
        self.view.clear_log()
        self.view.show_status("Organizing..." if not dry_run else "Previewing...")

        # Set confidence if AI enabled
        if self.ai_enabled:
            self.organizer.ml_confidence = self.view.get_ai_confidence()

        threading.Thread(target=self._organize_worker, args=(dry_run,), daemon=True).start()

    def _organize_worker(self, dry_run: bool):
        if not self.selected_path:
            return

        self._cached_preview = []
        self._source_path_for_preview = self.selected_path

        try:
            def on_event(data):
                if dry_run:
                    self._cached_preview.append(data)
                self.view.after_main(0, lambda: self.view.add_result_card(data))

            def on_progress(current, total, filename):
                self.view.after_main(0, lambda: self.view.update_progress(current, total, filename))

            def on_log(msg):
                self.view.after_main(0, lambda: self.view.append_log(msg))

            options = OrganizationOptions(
                source_path=self.selected_path,
                recursive=self.view.get_recursive_val(),
                date_sort=self.view.get_date_sort_val(),
                del_empty=self.view.get_del_empty_val(),
                detect_duplicates=self.view.get_detect_duplicates_val(),
                dry_run=dry_run,
                use_ml=self.ai_enabled,
                progress_callback=on_progress,
                log_callback=on_log,
                event_callback=on_event,
                check_stop=lambda: not self.is_running,
            )
            stats = self.organizer.organize_files(options)
            self.view.after_main(0, lambda: self._on_complete(stats, dry_run))
        except Exception as e:
            err_msg = str(e)
            import traceback
            traceback.print_exc()
            self.view.after_main(0, lambda: self.view.show_error("Operation Failed", f"An unexpected error occurred: {err_msg}"))
            self.view.after_main(0, lambda: self._on_complete({"moved": 0, "errors": 1}, dry_run))

    def _on_complete(self, stats, dry_run):
        self.is_running = False
        self.view.set_running_state(False)
        self.view.update_progress(1, 1, "Complete")

        msg = f"Done! {'Would move' if dry_run else 'Moved'} {stats['moved']} files."
        if stats.get("renamed", 0) > 0:
            msg += f" ({stats['renamed']} renamed)"
        if stats.get("duplicates", 0) > 0:
            msg += f" ({stats['duplicates']} duplicates skipped)"
        if stats.get("errors", 0) > 0:
            msg += f" ({stats['errors']} errors)"

        self.view.show_status(msg)
        self.view.update_results_header(msg)

        if not dry_run:
            if not isinstance(self.stats, dict):
                self.stats = {"total_files": 0, "last_run": "Never"}
            self.stats["total_files"] = self.stats.get("total_files", 0) + stats["moved"]
            self.stats["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save_stats()
            self.view.update_stats_display(self.stats)

    def on_confidence_changed(self, value):
        """Called when the AI confidence slider moves."""
        self.organizer.ml_confidence = value / 10.0
        self.view.update_ai_confidence_label(value)
        if self._cached_preview:
            # Re-run preview categories without re-scanning files
            self._refresh_preview()

    def _refresh_preview(self):
        """Update existing preview results based on new threshold."""
        threshold = self.organizer.ml_confidence
        self.view.clear_results()
        category_counts = {}

        for entry in self._cached_preview:
            # Re-decide which category to use based on new threshold
            ai_cat = entry.get("ai_category")
            ai_conf = entry.get("ai_confidence", 0.0)
            ext_cat = entry.get("ext_category", "Others")

            if ai_cat and ai_conf >= threshold:
                entry["category"] = ai_cat
                entry["method"] = entry.get("ai_method", "ml")
                entry["confidence"] = ai_conf
            else:
                entry["category"] = ext_cat
                entry["method"] = "extension"
                entry["confidence"] = 1.0

            # Rebuild destination path (needed for FileCard display)
            if self._source_path_for_preview:
                dest = self._source_path_for_preview / entry["category"] / entry["file"]
                entry["destination"] = str(dest)

            self.view.add_result_card(entry)

            # Update counts for breakdown
            cat_name = entry["category"].split("/")[0]
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

        # Update UI headers and breakdown
        ai_count = sum(1 for e in self._cached_preview
                       if e.get("ai_category") and e.get("ai_confidence", 0.0) >= threshold)
        msg = f"Done! Would move {len(self._cached_preview)} files ({ai_count} AI-categorized)."
        self.view.update_results_header(msg)
        self.view.update_category_breakdown(category_counts)
