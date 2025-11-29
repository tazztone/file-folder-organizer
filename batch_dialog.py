import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import threading
from pathlib import Path
from themes import get_palette

class BatchDialog:
    def __init__(self, parent, organizer, theme_name, on_complete_callback=None):
        self.parent = parent
        self.organizer = organizer
        self.theme_name = theme_name
        self.palette = get_palette(theme_name)
        self.on_complete_callback = on_complete_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Batch Organization")
        self.window.geometry("700x500")
        self.window.config(bg=self.palette["bg"])

        # batch_folders is list of dicts: {"path": str, "settings": dict or None}
        self.batch_folders = []
        self._load_batch_config()

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        c = self.palette

        # Toolbar
        frame_toolbar = ttk.Frame(self.window, padding=5)
        frame_toolbar.pack(fill="x", padx=10)

        btn_add = ttk.Button(frame_toolbar, text="Add Folder", command=self.add_folder)
        btn_add.pack(side="left", padx=5)

        btn_remove = ttk.Button(frame_toolbar, text="Remove Selected", command=self.remove_folder)
        btn_remove.pack(side="left", padx=5)

        btn_config = ttk.Button(frame_toolbar, text="Configure Folder", command=self.configure_folder)
        btn_config.pack(side="left", padx=5)

        btn_clear = ttk.Button(frame_toolbar, text="Clear All", command=self.clear_all)
        btn_clear.pack(side="left", padx=5)

        # List
        self.tree = ttk.Treeview(self.window, columns=("path", "settings", "status"), show="headings", selectmode="extended")
        self.tree.heading("path", text="Folder Path")
        self.tree.heading("settings", text="Settings")
        self.tree.heading("status", text="Status")
        self.tree.column("path", width=350)
        self.tree.column("settings", width=150)
        self.tree.column("status", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Bottom Actions
        frame_actions = ttk.Frame(self.window, padding=10)
        frame_actions.pack(fill="x", padx=10)

        self.progress = ttk.Progressbar(frame_actions, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 5))

        btn_run = ttk.Button(frame_actions, text="Run Batch", command=self.run_batch, style="Success.TButton")
        btn_run.pack(fill="x")

    def _load_batch_config(self):
        if Path("batch_config.json").exists():
            try:
                with open("batch_config.json", "r") as f:
                    data = json.load(f)
                    # Migrate old list of strings to list of dicts if needed
                    if data and isinstance(data[0], str):
                        self.batch_folders = [{"path": p, "settings": None} for p in data]
                    else:
                        self.batch_folders = data
            except:
                self.batch_folders = []

    def _save_batch_config(self):
        try:
            with open("batch_config.json", "w") as f:
                json.dump(self.batch_folders, f)
        except:
            pass

    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.batch_folders:
            settings_str = "Default"
            if item.get("settings"):
                 s = item["settings"]
                 parts = []
                 if s.get("recursive"): parts.append("Rec")
                 if s.get("date_sort"): parts.append("Date")
                 if s.get("del_empty"): parts.append("Del")
                 if s.get("dry_run"): parts.append("Dry")
                 settings_str = ",".join(parts) if parts else "Custom"

            self.tree.insert("", "end", values=(item["path"], settings_str, "Pending"))

    def add_folder(self):
        path = filedialog.askdirectory()
        if path:
            # Check if exists
            if not any(f["path"] == path for f in self.batch_folders):
                self.batch_folders.append({"path": path, "settings": None})
                self._save_batch_config()
                self._refresh_list()

    def remove_folder(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # Get indices to remove
        # Treeview returns item IDs, we need to map to index or path
        paths_to_remove = []
        for item in selected_items:
            vals = self.tree.item(item)['values']
            paths_to_remove.append(vals[0])

        self.batch_folders = [f for f in self.batch_folders if f["path"] not in paths_to_remove]

        self._save_batch_config()
        self._refresh_list()

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all folders from batch list?"):
            self.batch_folders = []
            self._save_batch_config()
            self._refresh_list()

    def configure_folder(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Select a folder to configure.")
            return

        if len(selected_items) > 1:
            messagebox.showwarning("Warning", "Select only one folder to configure.")
            return

        item_id = selected_items[0]
        vals = self.tree.item(item_id)['values']
        path = vals[0]

        # Find item in list
        folder_item = next((f for f in self.batch_folders if f["path"] == path), None)
        if not folder_item: return

        # Open simplified settings dialog
        current_settings = folder_item.get("settings") or {
            "recursive": False, "date_sort": False, "del_empty": False, "dry_run": False
        }

        self._open_config_dialog(folder_item, current_settings)

    def _open_config_dialog(self, folder_item, current_settings):
        d = tk.Toplevel(self.window)
        d.title("Folder Settings")
        d.config(bg=self.palette["bg"])

        var_rec = tk.BooleanVar(value=current_settings.get("recursive", False))
        var_date = tk.BooleanVar(value=current_settings.get("date_sort", False))
        var_del = tk.BooleanVar(value=current_settings.get("del_empty", False))
        var_dry = tk.BooleanVar(value=current_settings.get("dry_run", False))

        chk_rec = ttk.Checkbutton(d, text="Include Subfolders", variable=var_rec)
        chk_rec.pack(anchor="w", padx=10, pady=5)

        chk_date = ttk.Checkbutton(d, text="Sort by Date", variable=var_date)
        chk_date.pack(anchor="w", padx=10, pady=5)

        chk_del = ttk.Checkbutton(d, text="Delete Empty Folders", variable=var_del)
        chk_del.pack(anchor="w", padx=10, pady=5)

        chk_dry = ttk.Checkbutton(d, text="Dry Run", variable=var_dry)
        chk_dry.pack(anchor="w", padx=10, pady=5)

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

        btn_save = ttk.Button(d, text="Save", command=save, style="Success.TButton")
        btn_save.pack(pady=10)

    def run_batch(self):
        if not self.batch_folders:
            messagebox.showwarning("Warning", "No folders to process.")
            return

        details = "\n".join([f"- {f['path']}" for f in self.batch_folders[:5]])
        if len(self.batch_folders) > 5:
            details += f"\n...and {len(self.batch_folders) - 5} more"

        msg = f"Are you sure you want to process these {len(self.batch_folders)} folders?\n\n{details}"

        if not messagebox.askyesno("Confirm Batch", msg):
            return

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
        total = len(self.batch_folders)

        # Helper to update UI safely
        def update_ui(idx, status, progress_val):
            if idx is not None:
                # Treeview indices might match assuming no sorting/filtering happened
                # Safer to find by children index
                children = self.tree.get_children()
                if 0 <= idx < len(children):
                    item_id = children[idx]
                    # Preserve path and settings columns, update status
                    current_vals = self.tree.item(item_id)['values']
                    self.tree.item(item_id, values=(current_vals[0], current_vals[1], status))

            if progress_val is not None:
                self.progress["maximum"] = total
                self.progress["value"] = progress_val

        # Initial UI reset
        self.window.after(0, lambda: update_ui(None, None, 0))

        for i, folder_item in enumerate(self.batch_folders):
            folder_path = folder_item["path"]
            settings = folder_item.get("settings")

            self.window.after(0, lambda i=i: update_ui(i, "Running...", None))

            p = Path(folder_path)
            status_msg = ""

            if p.exists():
                try:
                    # Determine settings to use
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
                except Exception as e:
                    status_msg = f"Error: {str(e)}"
            else:
                status_msg = "Not Found"

            self.window.after(0, lambda i=i, s=status_msg: update_ui(i, s, i + 1))

        def finish():
             messagebox.showinfo("Batch Complete", "Batch organization finished.")
             if self.on_complete_callback:
                 self.on_complete_callback()

        self.window.after(0, finish)
