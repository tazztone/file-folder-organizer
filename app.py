import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
try:
    import tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD
    # Define DnDWrapper for mixin
    if hasattr(tkinterdnd2, 'DnDWrapper'):
        DnDWrapper = tkinterdnd2.DnDWrapper
    else:
        DnDWrapper = TkinterDnD.DnDWrapper
except (ImportError, AttributeError):
    # Fallback
    class DnDWrapper:
        def drop_target_register(self, *args): pass
        def dnd_bind(self, *args): pass
    DND_FILES = 'DND_Files'

import os
import threading
import json
import time
from datetime import datetime
from pathlib import Path
try:
    from PIL import Image, ImageTk, ImageDraw
except ImportError:
    Image = ImageTk = ImageDraw = None

from organizer import FileOrganizer
from settings_dialog_ctk import SettingsDialog
from batch_dialog_ctk import BatchDialog
from ui_utils import ToolTip
from ui_components import FileCard, ModelDownloadModal

# Set default theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class OrganizerApp(ctk.CTk, DnDWrapper):
    def __init__(self):
        super().__init__()
        # DnD Setup
        if hasattr(tkinterdnd2, 'TkinterDnD') and hasattr(self, 'TkdndVersion'):
             pass
        if 'tkinterdnd2' in globals():
             try:
                 tkinterdnd2.TkinterDnD._require(self)
             except:
                 pass

        self.title("Pro File Organizer")
        self.geometry("1000x700")

        self.organizer = FileOrganizer()
        if self.organizer.load_config():
            print("Loaded custom configuration.")

        # Load theme
        theme = self.organizer.get_theme_mode()
        if theme:
            ctk.set_appearance_mode(theme)

        self.selected_path = None
        self.is_running = False
        self.start_time = 0
        self.ai_enabled = False # Global toggle state
        self.recent_folders = []
        self.stats = {}

        # State control for download modal
        self._download_modal_open = False

        self.load_recent()
        self.load_stats()
        self._setup_ui()

        # Check if AI models are already present silently
        self._check_ai_models_silent()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar, text="PRO ORGANIZER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # AI Toggle (Prominent)
        self.frame_ai_toggle = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_ai_toggle.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="ew")

        self.lbl_ai = ctk.CTkLabel(self.frame_ai_toggle, text="✨ Smart AI", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_ai.pack(side="left", padx=10)

        self.switch_ai = ctk.CTkSwitch(self.frame_ai_toggle, text="", command=self.toggle_ai_mode, width=40)
        self.switch_ai.pack(side="right", padx=5)

        ToolTip(self.switch_ai, "Enable AI to categorize files by content (images & text) rather than just extension.")

        # Navigation Buttons (Optional, but kept for Batch/Settings)
        self.btn_batch = ctk.CTkButton(self.sidebar, text="Batch Mode", command=self.open_batch, fg_color="transparent", border_width=2, text_color=("gray10", "gray90"))
        self.btn_batch.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", command=self.open_settings, fg_color="transparent", border_width=2, text_color=("gray10", "gray90"))
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Theme
        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"],
                                                      command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=5, column=0, padx=20, pady=20, sticky="s")
        self.appearance_mode_menu.set(self.organizer.get_theme_mode() or "System")


        # --- Main Dashboard ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(2, weight=1) # Results expand
        self.main_area.grid_columnconfigure(0, weight=1)

        # 1. Top Section: Drop Zone & Folder Select
        self.frame_top = ctk.CTkFrame(self.main_area, height=120)
        self.frame_top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.frame_top.pack_propagate(False) # Force height

        # DnD
        try:
            self.frame_top.drop_target_register(DND_FILES)
            self.frame_top.dnd_bind('<<Drop>>', self.on_drop)
            self.frame_top.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.frame_top.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        except Exception as e:
            print(f"DnD setup failed: {e}")

        self.lbl_drop = ctk.CTkLabel(self.frame_top, text="Drag & Drop Folder Here", font=ctk.CTkFont(size=18))
        self.lbl_drop.pack(expand=True, side="left", padx=30)

        self.btn_browse = ctk.CTkButton(self.frame_top, text="Browse Folder", command=self.browse_folder, height=40)
        self.btn_browse.pack(side="right", padx=30)

        # Recent Folders Dropdown
        self.option_recent = ctk.CTkOptionMenu(self.frame_top, values=["Recent..."], command=self.on_recent_select)
        self.option_recent.pack(side="right", padx=(0, 10))
        self.update_recent_menu()


        # 2. Middle Section: Options & Actions
        self.frame_controls = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.frame_controls.grid_columnconfigure(0, weight=1) # Spacer

        # Options Container
        self.frame_options = ctk.CTkFrame(self.frame_controls)
        self.frame_options.pack(side="left", fill="y", padx=(0, 20))

        self.var_recursive = ctk.BooleanVar(value=False)
        self.chk_rec = ctk.CTkCheckBox(self.frame_options, text="Recursive", variable=self.var_recursive)
        self.chk_rec.pack(side="left", padx=10, pady=10)

        self.var_del_empty = ctk.BooleanVar(value=False)
        self.chk_del = ctk.CTkCheckBox(self.frame_options, text="Delete Empty", variable=self.var_del_empty)
        self.chk_del.pack(side="left", padx=10, pady=10)

        self.var_date_sort = ctk.BooleanVar(value=False)
        self.chk_date = ctk.CTkCheckBox(self.frame_options, text="Sort by Date", variable=self.var_date_sort)
        self.chk_date.pack(side="left", padx=10, pady=10)

        # AI Confidence Slider (Hidden by default)
        self.frame_ai_conf = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        # Packed only when AI is on

        self.lbl_conf = ctk.CTkLabel(self.frame_ai_conf, text="AI Confidence:")
        self.lbl_conf.pack(side="left", padx=5)
        self.slider_conf = ctk.CTkSlider(self.frame_ai_conf, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_conf.set(0.3)
        self.slider_conf.pack(side="left", padx=5)
        ToolTip(self.slider_conf, "Higher confidence means stricter AI matching. Lower values might guess more but be less accurate.")

        # Action Buttons
        self.btn_preview = ctk.CTkButton(self.frame_controls, text="PREVIEW", width=120, command=self.run_preview, state="disabled")
        self.btn_preview.pack(side="right", padx=5)

        self.btn_run = ctk.CTkButton(self.frame_controls, text="ORGANIZE", width=120, fg_color="green", hover_color="darkgreen", command=self.start_thread, state="disabled")
        self.btn_run.pack(side="right", padx=5)


        # 3. Bottom Section: Results Feed (Replacing Log)
        self.lbl_results = ctk.CTkLabel(self.main_area, text="Preview / Results", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_results.grid(row=2, column=0, sticky="w", pady=(10, 5))

        self.scroll_results = ctk.CTkScrollableFrame(self.main_area, label_text="Waiting for action...")
        self.scroll_results.grid(row=3, column=0, sticky="nsew")

        # Status Bar
        self.frame_status = ctk.CTkFrame(self.main_area, height=30, fg_color="transparent")
        self.frame_status.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Ready", anchor="w")
        self.lbl_status.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.frame_status)
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.progress_bar.set(0)


    def toggle_ai_mode(self):
        # Prevent multiple clicks or action if modal is open
        if self._download_modal_open:
            # Revert switch if user clicked it while modal is open (unlikely if modal is modal)
            # But good for safety
            if self.ai_enabled: self.switch_ai.select()
            else: self.switch_ai.deselect()
            return

        if self.switch_ai.get() == 1:
            # Enable AI
            self.ai_enabled = True
            # Check models
            self._check_and_load_models()
        else:
            # Disable AI
            self.ai_enabled = False
            self.frame_ai_conf.pack_forget()
            self.lbl_ai.configure(text_color="gray90" if ctk.get_appearance_mode()=="Dark" else "black")

    def _check_and_load_models(self):
        from ml_organizer import MultimodalFileOrganizer
        # Quick check first
        if not MultimodalFileOrganizer.are_models_present(MultimodalFileOrganizer):
            # Prompt download
            self._download_modal_open = True
            ModelDownloadModal(self, on_complete=self._on_model_download_complete)
        else:
            self._enable_ai_ui()

    def _check_ai_models_silent(self):
        """On startup, check if we should auto-enable AI or just update status"""
        pass

    def _on_model_download_complete(self, success):
        self._download_modal_open = False
        if success:
            self._enable_ai_ui()
        else:
            self.switch_ai.deselect()
            self.ai_enabled = False

    def _enable_ai_ui(self):
        self.frame_ai_conf.pack(side="left", padx=20)
        self.lbl_ai.configure(text_color="#9C27B0") # Purple
        # Also maybe pre-load models in background?
        threading.Thread(target=self._preload_models, daemon=True).start()

    def _preload_models(self):
        try:
             from ml_organizer import MultimodalFileOrganizer
             mo = MultimodalFileOrganizer()
             mo.load_models()
        except:
             pass

    # --- Standard App Logic ---

    def load_stats(self):
        self.stats = {"total_files": 0, "last_run": "Never"}
        if os.path.exists("stats.json"):
            try:
                with open("stats.json", "r") as f:
                    self.stats.update(json.load(f))
            except:
                pass

    def save_stats(self):
        try:
            with open("stats.json", "w") as f:
                json.dump(self.stats, f)
        except:
            pass

    def load_recent(self):
        self.recent_folders = []
        if os.path.exists("recent.json"):
            try:
                with open("recent.json", "r") as f:
                    self.recent_folders = json.load(f)
            except:
                pass

    def update_recent_menu(self):
        values = ["Recent..."] + self.recent_folders
        self.option_recent.configure(values=values)
        self.option_recent.set("Recent...")

    def add_recent(self, path):
        str_path = str(path)
        if str_path in self.recent_folders:
            self.recent_folders.remove(str_path)
        self.recent_folders.insert(0, str_path)
        self.recent_folders = self.recent_folders[:10]
        self.update_recent_menu()
        with open("recent.json", "w") as f:
            json.dump(self.recent_folders, f)

    def on_recent_select(self, selected):
        if selected and selected != "Recent...":
            self.set_folder(selected)
        else:
             self.option_recent.set("Recent...")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.set_folder(folder)

    def on_drag_enter(self, event):
        self.frame_top.configure(border_width=2, border_color="#3B8ED0")

    def on_drag_leave(self, event):
        self.frame_top.configure(border_width=0)

    def on_drop(self, event):
        self.on_drag_leave(event)
        if event.data:
            path = event.data
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            self.set_folder(path)

    def set_folder(self, path):
        if os.path.isdir(path):
            self.selected_path = Path(path)
            self.lbl_drop.configure(text=f"Selected: {self.selected_path.name}")
            self.btn_preview.configure(state="normal")
            self.btn_run.configure(state="normal")
            self.add_recent(self.selected_path)
            # Clear results
            self.clear_results()
        else:
            messagebox.showerror("Error", "Invalid folder path")

    def clear_results(self):
        for widget in self.scroll_results.winfo_children():
            widget.destroy()

    def open_settings(self):
        SettingsDialog(self, self.organizer)

    def open_batch(self):
        BatchDialog(self, self.organizer)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.organizer.save_theme_mode(new_appearance_mode)

    # --- Execution Logic ---

    def run_preview(self):
        self.run_organization(dry_run=True)

    def start_thread(self, event=None):
        if not self.selected_path: return
        if not messagebox.askyesno("Confirm", "Start organization?"): return
        self.run_organization(dry_run=False)

    def run_organization(self, dry_run=True):
        self.is_running = True
        self.start_time = time.time()
        self.btn_run.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        self.clear_results()
        self.scroll_results.configure(label_text="Processing...")

        # Set confidence if AI enabled
        if self.ai_enabled:
            self.organizer.ml_confidence = self.slider_conf.get()

        threading.Thread(target=self._organize_worker, args=(dry_run,), daemon=True).start()

    def _organize_worker(self, dry_run):

        def on_event(data):
            # Schedule UI update
            self.after(0, lambda: self._add_result_card(data))

        def on_progress(current, total, filename):
             self.after(0, lambda: self._update_progress(current, total, filename))

        stats = self.organizer.organize_files(
            source_path=self.selected_path,
            recursive=self.var_recursive.get(),
            date_sort=self.var_date_sort.get(),
            del_empty=self.var_del_empty.get(),
            dry_run=dry_run,
            progress_callback=on_progress,
            event_callback=on_event,
            check_stop=lambda: not self.is_running,
            use_ml=self.ai_enabled
        )

        self.after(0, lambda: self._on_complete(stats, dry_run))

    def _add_result_card(self, data):
        card = FileCard(self.scroll_results, data)
        card.pack(fill="x", pady=2, padx=5)
        # Auto scroll to bottom
        # self.scroll_results._parent_canvas.yview_moveto(1.0)

    def _update_progress(self, current, total, filename):
        if total > 0:
            if isinstance(total, float): # ML loading
                 self.progress_bar.set(current)
                 self.lbl_status.configure(text=f"{filename}")
            else:
                 self.progress_bar.set(current / total)
                 self.lbl_status.configure(text=f"Processing: {filename}")

    def _on_complete(self, stats, dry_run):
        self.is_running = False
        self.btn_run.configure(state="normal")
        self.btn_preview.configure(state="normal")
        self.progress_bar.set(1)

        msg = f"Done! {'Would move' if dry_run else 'Moved'} {stats['moved']} files."
        if stats.get('errors', 0) > 0:
            msg += f" ({stats['errors']} errors)"

        self.lbl_status.configure(text=msg)
        self.scroll_results.configure(label_text=msg)

        if not dry_run:
            self.stats["total_files"] = self.stats.get("total_files", 0) + stats["moved"]
            self.stats["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save_stats()
            messagebox.showinfo("Complete", msg)

if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
