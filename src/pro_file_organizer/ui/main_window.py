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

        self.controller = MainWindowController(self, self.organizer, self.ml_organizer)

        self._setup_ui()

        # Load initial state into UI
        self.update_recent_menu(self.controller.recent_folders)
        self.update_stats_display(self.controller.stats)

        theme = self.organizer.get_theme_mode()
        if theme:
            ctk.set_appearance_mode(theme)
            if hasattr(self, 'appearance_mode_menu'):
                self.appearance_mode_menu.set(theme)

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="PRO ORGANIZER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.frame_ai_toggle = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_ai_toggle.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="ew")

        self.lbl_ai = ctk.CTkLabel(self.frame_ai_toggle, text="✨ Smart AI", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_ai.pack(side="left", padx=10)

        self.switch_ai = ctk.CTkSwitch(
            self.frame_ai_toggle, text="",
            command=lambda: self.controller.toggle_ai(self.switch_ai.get() == 1), width=40
        )
        self.switch_ai.pack(side="right", padx=5)

        self.btn_batch = ctk.CTkButton(
            self.sidebar, text="Batch Mode", command=self.open_batch,
            fg_color="transparent", border_width=2
        )
        self.btn_batch.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            self.sidebar, text="Settings", command=self.open_settings,
            fg_color="transparent", border_width=2
        )
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"],
                                                      command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # --- Main Dashboard ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(2, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.frame_top = ctk.CTkFrame(self.main_area, height=120)
        self.frame_top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.frame_top.pack_propagate(False)

        try:
            self.frame_top.drop_target_register(DND_FILES)
            self.frame_top.dnd_bind('<<Drop>>', self.on_drop)
            self.frame_top.dnd_bind(
                '<<DragEnter>>',
                lambda e: self.frame_top.configure(border_width=2, border_color="#3B8ED0")
            )
            self.frame_top.dnd_bind('<<DragLeave>>', lambda e: self.frame_top.configure(border_width=0))
        except Exception:
            pass

        self.lbl_drop = ctk.CTkLabel(self.frame_top, text="Drag & Drop Folder Here", font=ctk.CTkFont(size=18))
        self.lbl_drop.pack(expand=True, side="left", padx=30)

        self.btn_browse = ctk.CTkButton(self.frame_top, text="Browse Folder", command=self.browse_folder, height=40)
        self.btn_browse.pack(side="right", padx=30)

        self.option_recent = ctk.CTkOptionMenu(
            self.frame_top, values=["Recent..."], command=self.controller.on_recent_select
        )
        self.option_recent.pack(side="right", padx=(0, 10))

        self.frame_controls = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))

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

        self.var_detect_duplicates = ctk.BooleanVar(value=False)
        self.chk_duplicates = ctk.CTkCheckBox(self.frame_options, text="Duplicates", variable=self.var_detect_duplicates)
        self.chk_duplicates.pack(side="left", padx=10, pady=10)

        self.frame_ai_conf = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        self.lbl_conf = ctk.CTkLabel(self.frame_ai_conf, text="AI Confidence:")
        self.lbl_conf.pack(side="left", padx=5)
        self.slider_conf = ctk.CTkSlider(self.frame_ai_conf, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_conf.set(0.3)
        self.slider_conf.pack(side="left", padx=5)

        self.btn_preview = ctk.CTkButton(
            self.frame_controls, text="PREVIEW", width=120,
            command=lambda: self.controller.run_organization(dry_run=True), state="disabled"
        )
        self.btn_preview.pack(side="right", padx=5)

        self.btn_run = ctk.CTkButton(
            self.frame_controls, text="ORGANIZE", width=120, fg_color="green",
            hover_color="darkgreen", command=self.controller.run_organization, state="disabled"
        )
        self.btn_run.pack(side="right", padx=5)

        self.lbl_results = ctk.CTkLabel(
            self.main_area, text="Preview / Results", anchor="w",
            font=ctk.CTkFont(weight="bold")
        )
        self.lbl_results.grid(row=2, column=0, sticky="w", pady=(10, 5))

        self.scroll_results = ctk.CTkScrollableFrame(self.main_area, label_text="Waiting for action...")
        self.scroll_results.grid(row=3, column=0, sticky="nsew")

        self.frame_status = ctk.CTkFrame(self.main_area, height=30, fg_color="transparent")
        self.frame_status.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Ready", anchor="w")
        self.lbl_status.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.frame_status)
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.progress_bar.set(0)

    # --- View Interface for Controller ---

    def update_folder_display(self, path_str):
        self.lbl_drop.configure(text=f"Selected: {os.path.basename(path_str)}")
        self.btn_preview.configure(state="normal")
        self.btn_run.configure(state="normal")

    def clear_results(self):
        for widget in self.scroll_results.winfo_children():
            widget.destroy()

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def confirm_action(self, title, message):
        return messagebox.askyesno(title, message)

    def update_recent_menu(self, recent_folders):
        values = ["Recent..."] + recent_folders
        self.option_recent.configure(values=values)
        self.option_recent.set("Recent...")

    def update_stats_display(self, stats):
        pass

    def show_model_download(self, callback):
        ModelDownloadModal(self, on_complete=callback)

    def show_settings(self, organizer):
        SettingsDialog(self, organizer)

    def show_batch(self, organizer):
        BatchDialog(self, organizer)

    def show_status(self, message):
        self.lbl_status.configure(text=message)

    def update_progress(self, current, total, filename):
        if total > 0:
            if isinstance(total, float): # ML loading percentage
                self.progress_bar.set(current)
                self.lbl_status.configure(text=f"{filename}")
            else:
                self.progress_bar.set(current / total)
                self.lbl_status.configure(text=f"Processing: {filename}")

    def after_main(self, ms, func):
        self.after(ms, func)

    def enable_ai_ui(self):
        self.frame_ai_conf.pack(side="left", padx=20)
        self.lbl_ai.configure(text_color="#9C27B0")

    def disable_ai_ui(self):
        self.frame_ai_conf.pack_forget()
        self.lbl_ai.configure(text_color="white" if ctk.get_appearance_mode()=="Dark" else "black")

    def set_ai_switch_state(self, state):
        if state:
            self.switch_ai.select()
        else:
            self.switch_ai.deselect()

    def set_running_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_run.configure(state=state)
        self.btn_preview.configure(state=state)
        if is_running:
            self.scroll_results.configure(label_text="Processing...")

    def get_ai_confidence(self):
        return self.slider_conf.get()

    def get_recursive_val(self):
        return self.var_recursive.get()

    def get_date_sort_val(self):
        return self.var_date_sort.get()

    def get_del_empty_val(self):
        return self.var_del_empty.get()

    def get_detect_duplicates_val(self):
        return self.var_detect_duplicates.get()

    def add_result_card(self, data):
        card = FileCard(self.scroll_results, data)
        card.pack(fill="x", pady=2, padx=5)

    def update_results_header(self, message):
        self.scroll_results.configure(label_text=message)

    # --- Event Handlers (Delegate to Controller) ---

    def browse_folder(self):
        self.controller.select_folder()

    def on_drop(self, event):
        self.frame_top.configure(border_width=0)
        if event.data:
            path = event.data
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            self.controller.set_folder(path)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.organizer.save_theme_mode(new_appearance_mode)

    def open_settings(self):
        self.controller.open_settings()

    def open_batch(self):
        self.controller.open_batch()

def main():
    app = OrganizerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
