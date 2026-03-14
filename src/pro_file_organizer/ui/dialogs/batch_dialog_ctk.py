import json
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ...core.constants import DEFAULT_BATCH_CONFIG_FILE
from ..themes.themes import COLORS, RADII
from ..ui_utils import ToolTip


class BatchDialog:
    def __init__(self, parent, organizer, theme_name=None, on_complete_callback=None):
        self.parent = parent
        self.organizer = organizer
        self.on_complete_callback = on_complete_callback

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Batch Organization")
        self.window.geometry("800x600")
        self.window.configure(fg_color=COLORS["bg_main"])

        # Ensure it stays on top
        self.window.transient(parent)
        self.window.grab_set()

        self.batch_folders = []
        self._load_batch_config()

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        # Toolbar
        frame_toolbar = ctk.CTkFrame(self.window, fg_color="transparent")
        frame_toolbar.pack(fill="x", padx=20, pady=10)

        btn_add = ctk.CTkButton(
            frame_toolbar, text="Add Folder", command=self.add_folder,
            width=120, height=36, corner_radius=RADII["card"],
            fg_color=COLORS["accent"]
        )
        btn_add.pack(side="left", padx=5)

        btn_clear = ctk.CTkButton(
            frame_toolbar, text="Clear All", command=self.clear_all,
            width=120, height=36, corner_radius=RADII["card"],
            fg_color=COLORS["danger"], hover_color="#C0392B"
        )
        btn_clear.pack(side="right", padx=5)

        # Header for the list
        frame_header = ctk.CTkFrame(self.window, corner_radius=0, height=30, fg_color=COLORS["bg_sidebar"])
        frame_header.pack(fill="x", padx=20)

        lbl_path = ctk.CTkLabel(frame_header, text="Folder Path", anchor="w", font=("Arial", 12, "bold"))
        lbl_path.pack(side="left", padx=10, expand=True, fill="x")

        lbl_sets = ctk.CTkLabel(frame_header, text="Settings", width=150, anchor="center", font=("Arial", 12, "bold"))
        lbl_sets.pack(side="left", padx=5)

        lbl_status = ctk.CTkLabel(frame_header, text="Status", width=100, anchor="center", font=("Arial", 12, "bold"))
        lbl_status.pack(side="left", padx=5)

        lbl_action = ctk.CTkLabel(frame_header, text="Action", width=80, anchor="center", font=("Arial", 12, "bold"))
        lbl_action.pack(side="left", padx=5)

        # List Area (Scrollable Frame)
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.window, corner_radius=RADII["standard"],
            fg_color=COLORS["bg_card"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Bottom Actions
        frame_actions = ctk.CTkFrame(self.window, fg_color="transparent")
        frame_actions.pack(fill="x", padx=20, pady=20)

        self.progress = ctk.CTkProgressBar(frame_actions, progress_color=COLORS["accent"])
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.set(0)

        btn_run = ctk.CTkButton(
            frame_actions, text="Run Batch", command=self.run_batch,
            fg_color=COLORS["success"], hover_color="#27AE60",
            height=44, corner_radius=RADII["card"]
        )
        btn_run.pack(fill="x")

    def _load_batch_config(self):
        if Path(DEFAULT_BATCH_CONFIG_FILE).exists():
            try:
                with open(DEFAULT_BATCH_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if data and isinstance(data[0], str):
                        self.batch_folders = [{"path": p, "settings": None} for p in data]
                    else:
                        self.batch_folders = data
            except Exception:
                self.batch_folders = []

    def _save_batch_config(self):
        try:
            with open(DEFAULT_BATCH_CONFIG_FILE, "w") as f:
                json.dump(self.batch_folders, f)
        except Exception:
            pass

    def _refresh_list(self):
        # Clear existing children
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, item in enumerate(self.batch_folders):
            self._create_row(i, item)

    def _create_row(self, index, item):
        row_frame = ctk.CTkFrame(self.scroll_frame, corner_radius=RADII["card"])
        row_frame.pack(fill="x", pady=2)

        # Path
        lbl_path = ctk.CTkLabel(row_frame, text=item["path"], anchor="w")
        lbl_path.pack(side="left", padx=10, fill="x", expand=True)

        # Settings
        settings_str = "Default"
        if item.get("settings"):
             s = item["settings"]
             parts = []
             if s.get("recursive"): parts.append("Rec")
             if s.get("date_sort"): parts.append("Date")
             if s.get("del_empty"): parts.append("Del")
             if s.get("dry_run"): parts.append("Dry")
             settings_str = ",".join(parts) if parts else "Custom"

        lbl_sets = ctk.CTkLabel(row_frame, text=settings_str, width=150, anchor="center")
        lbl_sets.pack(side="left", padx=5)

        # Status
        status = item.get("last_status", "Pending")
        lbl_status = ctk.CTkLabel(row_frame, text=status, width=100, anchor="center")
        lbl_status.pack(side="left", padx=5)
        # Store label ref to update later
        item["status_label"] = lbl_status

        # Config Button
        btn_conf = ctk.CTkButton(
            row_frame, text="⚙", width=30, height=30,
            fg_color=COLORS["border"], text_color=COLORS["text_main"],
            hover_color=COLORS["accent"], corner_radius=RADII["badge"],
            command=lambda idx=index: self.configure_folder(idx)
        )
        btn_conf.pack(side="left", padx=2)

        # Remove Button
        btn_del = ctk.CTkButton(
            row_frame, text="X", width=30, height=30,
            fg_color=COLORS["danger"], hover_color="#C0392B",
            corner_radius=RADII["badge"],
            command=lambda idx=index: self.remove_folder(idx)
        )
        btn_del.pack(side="left", padx=5)

    def add_folder(self):
        path = filedialog.askdirectory()
        if path:
            if not any(f["path"] == path for f in self.batch_folders):
                self.batch_folders.append({"path": path, "settings": None})
                self._save_batch_config()
                self._refresh_list()

    def remove_folder(self, index):
        if 0 <= index < len(self.batch_folders):
            del self.batch_folders[index]
            self._save_batch_config()
            self._refresh_list()

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all folders from batch list?"):
            self.batch_folders = []
            self._save_batch_config()
            self._refresh_list()

    def configure_folder(self, index):
        folder_item = self.batch_folders[index]
        current_settings = folder_item.get("settings") or {
            "recursive": False, "date_sort": False, "del_empty": False, "dry_run": False
        }

        d = ctk.CTkToplevel(self.window)
        d.title("Folder Settings")
        d.geometry("300x250")
        d.transient(self.window)
        d.grab_set()

        var_rec = ctk.BooleanVar(value=current_settings.get("recursive", False))
        var_date = ctk.BooleanVar(value=current_settings.get("date_sort", False))
        var_del = ctk.BooleanVar(value=current_settings.get("del_empty", False))
        var_dry = ctk.BooleanVar(value=current_settings.get("dry_run", False))

        ctk.CTkSwitch(d, text="Include Subfolders", variable=var_rec).pack(anchor="w", padx=20, pady=10)
        ctk.CTkSwitch(d, text="Sort by Date", variable=var_date).pack(anchor="w", padx=20, pady=10)
        ctk.CTkSwitch(d, text="Delete Empty Folders", variable=var_del).pack(anchor="w", padx=20, pady=10)
        ctk.CTkSwitch(d, text="Dry Run", variable=var_dry).pack(anchor="w", padx=20, pady=10)

        def save():
            folder_item["settings"] = {
                "recursive": var_rec.get(),
                "date_sort": var_date.get(),
                "del_empty": var_del.get(),
                "dry_run": var_dry.get()
            }
            self._save_batch_config()
            self._refresh_list()
            d.destroy()

        ctk.CTkButton(d, text="Save", command=save, fg_color="green").pack(pady=20)

    def run_batch(self):
        if not self.batch_folders:
            messagebox.showwarning("Warning", "No folders to process.")
            return

        msg = f"Are you sure you want to process {len(self.batch_folders)} folders?"
        if not messagebox.askyesno("Confirm Batch", msg):
            return

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
        total = len(self.batch_folders)

        # Since we are in a thread, we can process sequentially, but must update UI via after
        for i, folder_item in enumerate(self.batch_folders):
            folder_path = folder_item["path"]
            settings = folder_item.get("settings")

            # Update status to Running
            self.window.after(0, lambda f=folder_item: f["status_label"].configure(
                text="Running...") if "status_label" in f else None)

            p = Path(folder_path)
            status_msg = ""

            if p.exists():
                try:
                    kwargs = {
                        "recursive": False,
                        "date_sort": False,
                        "del_empty": False,
                        "dry_run": False
                    }
                    if settings:
                        kwargs.update(settings)

                    self.organizer.organize_files(p, **kwargs)
                    status_msg = "Done"
                except Exception:
                    status_msg = "Error"
            else:
                status_msg = "Not Found"

            # Update status to Done/Error and progress
            def update_done(f=folder_item, msg=status_msg, val=(i + 1) / total):
                if "status_label" in f:
                    f["status_label"].configure(text=msg)
                self.progress.set(val)

            self.window.after(0, update_done)

        # All done
        self.window.after(0, lambda: messagebox.showinfo("Batch Complete", "Batch organization finished."))
        if self.on_complete_callback:
            self.window.after(0, self.on_complete_callback)
