try:
    from tkinter import filedialog, messagebox
except ImportError:
    import tkinter.messagebox as messagebox
    filedialog = None # type: ignore

import customtkinter as ctk

try:
    import tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD
    if hasattr(tkinterdnd2, 'DnDWrapper'):
        DnDWrapper = tkinterdnd2.DnDWrapper # type: ignore
    else:
        DnDWrapper = TkinterDnD.DnDWrapper # type: ignore
except (ImportError, AttributeError):
    class DnDWrapper: # type: ignore
        def drop_target_register(self, *args): pass
        def dnd_bind(self, *args): pass
    DND_FILES = 'DND_Files'

import os

from ..core.ml_organizer import MultimodalFileOrganizer
from ..core.organizer import FileOrganizer
from .components.ui_components import FileCard, ModelDownloadModal
from .dialogs.batch_dialog_ctk import BatchDialog
from .dialogs.settings_dialog_ctk import SettingsDialog
from .main_window_controller import MainWindowController

# Set default theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class OrganizerApp(ctk.CTk, DnDWrapper): # type: ignore
    def __init__(self):
        super().__init__()
        # DnD Setup
        if 'tkinterdnd2' in globals():
             try:
                 tkinterdnd2.TkinterDnD._require(self) # type: ignore
             except Exception:
                 pass

        self.title("Pro File Organizer")
        self.geometry("1000x700")

        self.organizer = FileOrganizer()
        self.ml_organizer = MultimodalFileOrganizer()

        # Build UI
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Pro Organizer", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=(20, 10))

        self.btn_browse = ctk.CTkButton(self.sidebar, text="Select Directory", command=self.browse_directory)
        self.btn_browse.pack(pady=10, padx=20)

        self.btn_batch = ctk.CTkButton(self.sidebar, text="Batch Process", command=self.open_batch_dialog)
        self.btn_batch.pack(pady=10, padx=20)

        self.btn_settings = ctk.CTkButton(self.sidebar, text="Configuration", command=self.open_settings_dialog)
        self.btn_settings.pack(pady=10, padx=20)

        self.btn_undo = ctk.CTkButton(
            self.sidebar, text="Undo Last", command=self.undo_changes,
            fg_color="orange", hover_color="darkorange", text_color="black"
        )
        self.btn_undo.pack(pady=10, padx=20)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.pack(side="bottom", padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar, values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_optionemenu.pack(side="bottom", padx=20, pady=(0, 20))
        self.appearance_mode_optionemenu.set(self.organizer.get_theme_mode())

        # 2. Main Content
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Header Info
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.lbl_path = ctk.CTkLabel(self.header_frame, text="Current Directory: Not Selected", font=("Arial", 12))
        self.lbl_path.pack(side="left")

        # Options Area
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.check_recursive = ctk.CTkCheckBox(self.options_frame, text="Recursive Scan")
        self.check_recursive.pack(side="left", padx=10)

        self.check_date = ctk.CTkCheckBox(self.options_frame, text="Sort by Date")
        self.check_date.pack(side="left", padx=10)

        self.check_empty = ctk.CTkCheckBox(self.options_frame, text="Delete Empty Folders")
        self.check_empty.pack(side="left", padx=10)

        self.check_ml = ctk.CTkCheckBox(self.options_frame, text="AI Categorization")
        self.check_ml.pack(side="left", padx=10)

        # File List (Scrollable)
        self.file_scroll = ctk.CTkScrollableFrame(self.main_frame, label_text="Scan Preview")
        self.file_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(2, weight=3)

        # Progress / Log
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(3, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.log_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        self.txt_log = ctk.CTkTextbox(self.log_frame, height=100)
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=5)

        # Footer Buttons
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        self.btn_preview = ctk.CTkButton(self.footer_frame, text="Preview Scan", command=self.run_preview)
        self.btn_preview.pack(side="left", padx=10)

        self.btn_organize = ctk.CTkButton(
            self.footer_frame, text="Organize Now", command=self.run_organization,
            fg_color="green", hover_color="darkgreen"
        )
        self.btn_organize.pack(side="left", padx=10)

        self.btn_stop = ctk.CTkButton(
            self.footer_frame, text="Stop", command=self.stop_operation,
            fg_color="red", hover_color="darkred", state="disabled"
        )
        self.btn_stop.pack(side="right", padx=10)

        # Controller Init
        self.controller = MainWindowController(self, self.organizer)

        # Drag and Drop Registration
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
        except Exception:
            pass

    def on_drop(self, event):
        path = event.data
        if path.startswith('{') and path.endswith('}'):
             path = path[1:-1]
        self.controller.select_directory(path)

    def browse_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.controller.select_directory(path)

    def run_preview(self):
        self.controller.run_preview()

    def run_organization(self):
        self.controller.run_organization()

    def stop_operation(self):
        self.controller.stop_operation()

    def undo_changes(self):
        self.controller.undo_changes()

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.organizer.save_theme_mode(new_appearance_mode)

    def open_settings_dialog(self):
        SettingsDialog(self, self.organizer)

    def open_batch_dialog(self):
        BatchDialog(self, self.organizer)

    def show_model_download_modal(self, total_size, start_callback):
        return ModelDownloadModal(self, total_size, start_callback)

def main():
    app = OrganizerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
