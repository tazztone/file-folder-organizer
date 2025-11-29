import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk, simpledialog
import json
from pathlib import Path
from organizer import FileOrganizer
from themes import THEMES
from settings_dialog import SettingsDialog
from batch_dialog import BatchDialog
from ui_utils import ToolTip

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro File Organizer")
        self.root.geometry("600x700")

        self.organizer = FileOrganizer()
        # Try loading config
        if self.organizer.load_config():
            print("Loaded custom configuration.")

        # Load recent folders
        self.load_recent()

        self.current_theme = "dark"  # Default to dark mode
        self.colors = THEMES[self.current_theme]
        self.style = ttk.Style()
        self.selected_path = None
        self.is_running = False

        # Bind Shortcuts
        self.root.bind('<Return>', self.start_thread)
        self.root.bind('<Escape>', lambda e: self.stop_process())

        # 1. Folder Selection Area
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x", padx=10)

        self.lbl_path = tk.Label(frame_top, text="No folder selected", anchor="w", relief="sunken")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ToolTip(self.lbl_path, "Selected folder path")

        btn_browse = tk.Button(frame_top, text="Browse Folder", command=self.browse_folder)
        btn_browse.pack(side="right")
        ToolTip(btn_browse, "Select a folder to organize")

        # Recent Folders Combobox
        self.var_recent = tk.StringVar()
        self.opt_recent = ttk.Combobox(frame_top, textvariable=self.var_recent, values=self.recent_folders, state="readonly", width=3)
        self.opt_recent.set("...")
        self.opt_recent.pack(side="right", padx=5)
        self.opt_recent.bind("<<ComboboxSelected>>", self.on_recent_select)
        ToolTip(self.opt_recent, "Select from recently used folders")

        # Options Frame
        frame_options = tk.Frame(root, pady=5)
        frame_options.pack(fill="x", padx=10)

        # Recursive Checkbox
        self.var_recursive = tk.BooleanVar()
        chk_rec = tk.Checkbutton(frame_options, text="Include Subfolders", variable=self.var_recursive)
        chk_rec.pack(side="left", padx=5)
        ToolTip(chk_rec, "Search and organize files in subdirectories")

        # Date Sorting Checkbox
        self.var_date_sort = tk.BooleanVar()
        chk_date = tk.Checkbutton(frame_options, text="Sort by Date", variable=self.var_date_sort)
        chk_date.pack(side="left", padx=5)
        ToolTip(chk_date, "Organize files into Year/Month folders")

        # Delete Empty Folders Checkbox
        self.var_del_empty = tk.BooleanVar()
        chk_del = tk.Checkbutton(frame_options, text="Delete Empty Folders", variable=self.var_del_empty)
        chk_del.pack(side="left", padx=5)
        ToolTip(chk_del, "Remove empty folders after moving files")

        # Dry Run Checkbox
        self.var_dry_run = tk.BooleanVar()
        chk_dry = tk.Checkbutton(frame_options, text="Dry Run (Simulate)", variable=self.var_dry_run)
        chk_dry.pack(side="left", padx=5)
        ToolTip(chk_dry, "Simulate the organization without moving files")

        # Theme Toggle
        self.btn_theme = tk.Button(frame_options, text=f"Theme: {self.current_theme.title()}", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)
        ToolTip(self.btn_theme, "Toggle between Light and Dark themes")

        # Settings Button
        self.btn_settings = tk.Button(frame_options, text="Settings", command=self.open_settings)
        self.btn_settings.pack(side="right", padx=5)
        ToolTip(self.btn_settings, "Configure file categories and extensions")

        # Batch Button
        self.btn_batch = tk.Button(frame_options, text="Batch", command=self.open_batch)
        self.btn_batch.pack(side="right", padx=5)
        ToolTip(self.btn_batch, "Organize multiple folders")

        # 2. Action Buttons
        frame_actions = tk.Frame(root)
        frame_actions.pack(fill="x", padx=10, pady=5)

        self.btn_preview = tk.Button(frame_actions, text="Preview", command=self.run_preview, state="disabled", height=2)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ToolTip(self.btn_preview, "Preview the changes (Dry Run)")

        self.btn_run = tk.Button(frame_actions, text="Start Organizing", command=self.start_thread, state="disabled", height=2)
        self.btn_run.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ToolTip(self.btn_run, "Start the organization process")

        # Undo Button
        self.btn_undo = tk.Button(root, text="Undo Last Run", command=self.undo_changes, state="disabled")
        self.btn_undo.pack(fill="x", padx=10, pady=5)
        ToolTip(self.btn_undo, "Revert the last organization operation")

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # 3. Log Area
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

        # Apply initial theme
        self.apply_theme()

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = THEMES[self.current_theme]
        self.btn_theme.config(text=f"Theme: {self.current_theme.title()}")
        self.apply_theme()

    def apply_theme(self):
        c = self.colors
        self.root.config(bg=c["bg"])

        # Configure ttk styles
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background=c["success_bg"], troughcolor=c["btn_bg"], bordercolor=c["bg"], lightcolor=c["success_bg"], darkcolor=c["success_bg"])

        # Recursively update widget colors
        self.update_widget_colors(self.root, c)

        # Re-apply specific states if needed
        if self.selected_path:
             self.btn_run.config(bg=c["success_bg"], fg=c["success_fg"])
             self.btn_preview.config(bg=c["btn_bg"], fg=c["btn_fg"])
        else:
             self.btn_run.config(bg=c["disabled_bg"], fg=c["disabled_fg"])
             self.btn_preview.config(bg=c["disabled_bg"], fg=c["disabled_fg"])

        self.update_undo_button()


    def update_widget_colors(self, widget, c):
        try:
            w_type = widget.winfo_class()
            if w_type in ('Frame', 'Label', 'Checkbutton'):
                widget.config(bg=c["bg"], fg=c["fg"])
                if w_type == 'Checkbutton':
                    widget.config(selectcolor=c["select_bg"], activebackground=c["bg"], activeforeground=c["fg"])
            elif w_type == 'Button':
                widget.config(bg=c["btn_bg"], fg=c["btn_fg"], activebackground=c["select_bg"], activeforeground=c["select_fg"])
            elif w_type == 'Text':
                widget.config(bg=c["text_bg"], fg=c["text_fg"], insertbackground=c["fg"])
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self.update_widget_colors(child, c)

    def load_recent(self):
        self.recent_folders = []
        if os.path.exists("recent.json"):
            try:
                with open("recent.json", "r") as f:
                    self.recent_folders = json.load(f)
            except:
                pass

    def add_recent(self, path):
        str_path = str(path)
        if str_path in self.recent_folders:
            self.recent_folders.remove(str_path)
        self.recent_folders.insert(0, str_path)
        self.recent_folders = self.recent_folders[:10]

        self.opt_recent['values'] = self.recent_folders

        with open("recent.json", "w") as f:
            json.dump(self.recent_folders, f)

    def on_recent_select(self, event):
        selected = self.var_recent.get()
        if selected and selected != "...":
            self.selected_path = Path(selected)
            self.lbl_path.config(text=str(self.selected_path))
            self.enable_buttons()
            self.log("Selected (Recent): " + str(self.selected_path))
            self.add_recent(self.selected_path)
            self.opt_recent.set("...")

    def enable_buttons(self):
        self.btn_run.config(state="normal", bg=self.colors["success_bg"], fg=self.colors["success_fg"])
        self.btn_preview.config(state="normal", bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_path = Path(folder_selected)
            self.lbl_path.config(text=str(self.selected_path))
            self.enable_buttons()
            self.log("Selected: " + str(self.selected_path))

    def open_settings(self):
        SettingsDialog(self.root, self.organizer, self.colors)

    def open_batch(self):
        BatchDialog(self.root, self.organizer, self.colors, on_complete_callback=self.update_undo_button)

    def log(self, message):
        def _update():
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state='disabled')
        self.root.after(0, _update)

    def update_progress(self, current, total):
        def _update():
            if total > 0:
                self.progress["maximum"] = total
                self.progress["value"] = current
        self.root.after(0, _update)

    def start_thread(self, event=None):
        if not self.selected_path:
             messagebox.showwarning("Warning", "Please select a folder first.")
             return

        if not self.var_dry_run.get():
             if not messagebox.askyesno("Confirm", "Are you sure you want to organize files? This will move files to new directories."):
                 return

        self.run_organization(dry_run_override=None)

    def run_preview(self):
        self.run_organization(dry_run_override=True)

    def run_organization(self, dry_run_override=None):
        self.is_running = True
        self.btn_run.config(text="Stop", command=self.stop_process, bg=self.colors["undo_bg"], fg=self.colors["undo_fg"])
        self.btn_preview.config(state="disabled")
        self.btn_undo.config(state="disabled")
        self.progress["value"] = 0

        threading.Thread(target=self.organize_files, args=(dry_run_override,), daemon=True).start()

    def stop_process(self):
        if hasattr(self, 'is_running') and self.is_running:
            self.is_running = False
            self.btn_run.config(state="disabled", text="Stopping...")

    def organize_files(self, dry_run_override=None):
        if not self.selected_path:
            return

        dry_run = dry_run_override if dry_run_override is not None else self.var_dry_run.get()

        stats = self.organizer.organize_files(
            source_path=self.selected_path,
            recursive=self.var_recursive.get(),
            date_sort=self.var_date_sort.get(),
            del_empty=self.var_del_empty.get(),
            dry_run=dry_run,
            progress_callback=self.update_progress,
            log_callback=self.log,
            check_stop=lambda: not self.is_running
        )

        msg = f"Organization {'stopped' if not self.is_running else 'complete'}!\n{'Would move' if dry_run else 'Moved'} {stats['moved']} files."

        self.root.after(0, lambda: messagebox.showinfo("Result", msg))
        
        def reset_ui():
            self.btn_run.config(state="normal", text="Start Organizing", command=self.start_thread, bg=self.colors["success_bg"], fg=self.colors["success_fg"])
            self.btn_preview.config(state="normal", bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
            self.update_undo_button()

        self.root.after(0, reset_ui)

    def update_undo_button(self):
        stack_size = len(self.organizer.undo_stack)
        c = self.colors
        if stack_size > 0:
            self.btn_undo.config(state="normal", text=f"Undo Last Run ({stack_size})", bg=c["undo_bg"], fg=c["undo_fg"])
        else:
            self.btn_undo.config(state="disabled", text="Undo Last Run", bg=c["disabled_bg"], fg=c["disabled_fg"])

    def undo_changes(self):
        self.btn_undo.config(state="disabled")

        def _undo_thread():
            count = self.organizer.undo_changes(log_callback=self.log)
            messagebox.showinfo("Undo", f"Restored {count} files to their original locations.")
            self.root.after(0, self.update_undo_button)

        threading.Thread(target=_undo_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()
