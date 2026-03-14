import os
try:
    from tkinter import filedialog, messagebox
except ImportError:
    import tkinter.messagebox as messagebox
    filedialog = None  # type: ignore

import customtkinter as ctk

try:
    import tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD
    if hasattr(tkinterdnd2, 'DnDWrapper'):
        DnDWrapper = tkinterdnd2.DnDWrapper  # type: ignore
    else:
        DnDWrapper = TkinterDnD.DnDWrapper  # type: ignore
except (ImportError, AttributeError):
    class DnDWrapper:  # type: ignore
        def drop_target_register(self, *args): pass
        def dnd_bind(self, *args): pass
    DND_FILES = 'DND_Files'

from ..core.ml_organizer import MultimodalFileOrganizer
from ..core.organizer import FileOrganizer
from .components.ui_components import FileCard, ModelDownloadModal
from .dialogs.batch_dialog_ctk import BatchDialog
from .dialogs.settings_dialog_ctk import SettingsDialog
from .main_window_controller import MainWindowController
from .themes.themes import COLORS, FONTS, RADII

# Set default appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue") # Keep blue as base for standard components

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
        self.geometry("1100x750") # Slightly larger default
        self.configure(fg_color=COLORS["bg_main"])

        self.organizer = FileOrganizer()
        self.ml_organizer = MultimodalFileOrganizer()

        self.controller = MainWindowController(self, self.organizer, self.ml_organizer)

        # Track results for state updates
        self.result_cards = []

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
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) # Push footer down

        # Logo Area
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="ew")

        self.logo_icon = ctk.CTkLabel(self.logo_frame, text="📁", font=("Inter", 24))
        self.logo_icon.pack(side="left", padx=(0, 10))

        self.logo_label = ctk.CTkLabel(self.logo_frame, text="PRO ORGANIZER", font=FONTS["title"])
        self.logo_label.pack(side="left")

        # AI Toggle
        self.frame_ai_toggle = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_ai_toggle.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="ew")

        self.lbl_ai = ctk.CTkLabel(self.frame_ai_toggle, text="✨ Smart AI", font=FONTS["label"])
        self.lbl_ai.pack(side="left", padx=10)

        self.switch_ai = ctk.CTkSwitch(
            self.frame_ai_toggle, text="",
            command=lambda: self.controller.toggle_ai(self.switch_ai.get() == 1),
            width=40, progress_color=COLORS["accent"]
        )
        self.switch_ai.pack(side="right", padx=5)

        # Main Buttons
        self.btn_batch = ctk.CTkButton(
            self.sidebar, text="Batch Mode", command=self.open_batch,
            fg_color="transparent", border_width=2, border_color=COLORS["accent"],
            hover_color=COLORS["bg_hover"], corner_radius=RADII["standard"]
        )
        self.btn_batch.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            self.sidebar, text="Settings", command=self.open_settings,
            fg_color="transparent", border_width=2, border_color=COLORS["accent"],
            hover_color=COLORS["bg_hover"], corner_radius=RADII["standard"]
        )
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Stats Bar (Mini)
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.stats_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.lbl_stats_total = ctk.CTkLabel(
            self.stats_frame, text="Files: 0", font=FONTS["small"],
            text_color=COLORS["text_dimmed"]
        )
        self.lbl_stats_total.pack(anchor="w")
        self.lbl_stats_last = ctk.CTkLabel(
            self.stats_frame, text="Last: Never", font=FONTS["small"],
            text_color=COLORS["text_dimmed"]
        )
        self.lbl_stats_last.pack(anchor="w")

        # Footer Separator
        self.sidebar_sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["separator"])
        self.sidebar_sep.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar, values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
            fg_color=COLORS["accent"], button_color=COLORS["accent"],
            dropdown_hover_color=COLORS["accent"], corner_radius=RADII["card"]
        )
        self.appearance_mode_menu.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # --- Main Dashboard ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_area.grid_rowconfigure(2, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # Drop Zone Frame
        self.frame_top = ctk.CTkFrame(
            self.main_area, height=160, corner_radius=RADII["standard"],
            fg_color=COLORS["bg_card"]
        )
        self.frame_top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.frame_top.grid_propagate(False) # Correct from pack_propagate
        self.frame_top.grid_columnconfigure(0, weight=1)
        self.frame_top.grid_rowconfigure(0, weight=1)

        # Canvas for Dashed Border
        self.drop_canvas = ctk.CTkCanvas(
            self.frame_top, bg=self._get_canvas_bg(), highlightthickness=0,
            bd=0, cursor="hand2"
        )
        self.drop_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        try:
            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind('<<Drop>>', self.on_drop)
            self.drop_canvas.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.drop_canvas.dnd_bind('<<DragLeave>>', self._on_drag_leave)
        except Exception:
            pass

        self.drop_canvas.bind("<Button-1>", lambda e: self.browse_folder())
        self.bind("<<AppearanceModeChanged>>", self._on_appearance_mode_changed)

        self.lbl_drop = ctk.CTkLabel(
            self.frame_top, text="Drag & Drop Folder Here",
            font=FONTS["subtitle"], text_color=COLORS["text_main"],
            fg_color="transparent"
        )
        self.lbl_drop.place(relx=0.5, rely=0.4, anchor="center")

        self.lbl_drop_icon = ctk.CTkLabel(
            self.frame_top, text="⬆", font=("Inter", 32), fg_color="transparent"
        )
        self.lbl_drop_icon.place(relx=0.5, rely=0.2, anchor="center")

        self.drop_actions_frame = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.drop_actions_frame.place(relx=0.5, rely=0.7, anchor="center")

        self.btn_browse = ctk.CTkButton(
            self.drop_actions_frame, text="Browse Folder",
            command=self.browse_folder, height=36, corner_radius=RADII["card"],
            fg_color=COLORS["accent"]
        )
        self.btn_browse.pack(side="left", padx=10)

        self.option_recent = ctk.CTkOptionMenu(
            self.drop_actions_frame, values=["Recent..."],
            command=self.controller.on_recent_select,
            height=36, corner_radius=RADII["card"],
            fg_color=COLORS["border"], text_color=COLORS["text_main"],
            button_color=COLORS["border"], button_hover_color=COLORS["accent"]
        )
        self.option_recent.pack(side="left", padx=10)

        # Controls
        self.frame_controls = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_controls.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        self.frame_options = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        self.frame_options.pack(side="left", fill="y")

        self.var_recursive = ctk.BooleanVar(value=False)
        self.chk_rec = ctk.CTkCheckBox(
            self.frame_options, text="Recursive", variable=self.var_recursive,
            corner_radius=6, border_width=2
        )
        self.chk_rec.pack(side="left", padx=(0, 15))

        self.var_del_empty = ctk.BooleanVar(value=False)
        self.chk_del = ctk.CTkCheckBox(
            self.frame_options, text="Delete Empty", variable=self.var_del_empty,
            corner_radius=6, border_width=2
        )
        self.chk_del.pack(side="left", padx=15)

        self.var_date_sort = ctk.BooleanVar(value=False)
        self.chk_date = ctk.CTkCheckBox(
            self.frame_options, text="Sort by Date", variable=self.var_date_sort,
            corner_radius=6, border_width=2
        )
        self.chk_date.pack(side="left", padx=15)

        self.var_detect_duplicates = ctk.BooleanVar(value=False)
        self.chk_duplicates = ctk.CTkCheckBox(
            self.frame_options, text="Duplicates", variable=self.var_detect_duplicates,
            corner_radius=6, border_width=2
        )
        self.chk_duplicates.pack(side="left", padx=15)

        self.var_watch_folder = ctk.BooleanVar(value=False)
        self.chk_watch = ctk.CTkCheckBox(
            self.frame_options, text="Watch Folder", variable=self.var_watch_folder,
            command=lambda: self.controller.toggle_watch(self.var_watch_folder.get()),
            corner_radius=6, border_width=2
        )
        self.chk_watch.pack(side="left", padx=15)

        self.frame_ai_conf = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        self.lbl_conf = ctk.CTkLabel(self.frame_ai_conf, text="AI Confidence:")
        self.lbl_conf.pack(side="left", padx=5)
        self.slider_conf = ctk.CTkSlider(self.frame_ai_conf, from_=0.1, to=0.9, number_of_steps=8)
        self.slider_conf.set(0.3)
        self.slider_conf.pack(side="left", padx=5)

        self.btn_preview = ctk.CTkButton(
            self.frame_controls, text="PREVIEW", width=120, height=40,
            command=lambda: self.controller.run_organization(dry_run=True),
            state="disabled", fg_color=COLORS["border"], text_color=COLORS["text_main"],
            hover_color=COLORS["accent"], corner_radius=RADII["card"]
        )
        self.btn_preview.pack(side="right", padx=5)

        self.btn_run = ctk.CTkButton(
            self.frame_controls, text="ORGANIZE", width=120, height=40,
            fg_color=COLORS["success"], hover_color="#27AE60",
            command=self.controller.run_organization, state="disabled",
            corner_radius=RADII["card"]
        )
        self.btn_run.pack(side="right", padx=5)

        self.scroll_results = ctk.CTkScrollableFrame(
            self.main_area, label_text="Waiting for action...",
            label_font=FONTS["label"], label_text_color=COLORS["accent"],
            corner_radius=RADII["standard"], fg_color=COLORS["bg_card"]
        )
        self.scroll_results.grid(row=3, column=0, sticky="nsew")

        self.frame_status = ctk.CTkFrame(self.main_area, height=30, fg_color="transparent")
        self.frame_status.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.lbl_status = ctk.CTkLabel(
            self.frame_status, text="Ready", font=FONTS["small"], text_color=COLORS["text_dimmed"]
        )
        self.lbl_status.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.frame_status, progress_color=COLORS["accent"])
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.progress_bar.set(0)

        self.after(100, self._draw_dashed_border)

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
        total = stats.get("total_files", 0)
        last = stats.get("last_run", "Never")
        self.lbl_stats_total.configure(text=f"Files Organized: {total}")
        self.lbl_stats_last.configure(text=f"Last Run: {last}")

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
        self.lbl_ai.configure(text_color=COLORS["text_main"])

    def set_ai_switch_state(self, state):
        if state:
            self.switch_ai.select()
        else:
            self.switch_ai.deselect()

    def set_watch_switch_state(self, state):
        if state:
            self.chk_watch.select()
        else:
            self.chk_watch.deselect()

    def set_running_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.btn_run.configure(state=state)
        self.btn_preview.configure(state=state)
        if is_running:
            self.scroll_results.configure(label_text="Processing...")
        else:
            # When finished, make cards opaque
            for card in self.result_cards:
                card.set_executed()

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
        self.result_cards.append(card)

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

    # --- Private Helpers ---

    def _get_canvas_bg(self):
        mode = ctk.get_appearance_mode()
        return COLORS["bg_card"][0] if mode == "Light" else COLORS["bg_card"][1]

    def _on_appearance_mode_changed(self, new_mode):
        self.after(100, self._draw_dashed_border)
        # Update specific non-automated components
        self.lbl_ai.configure(text_color=COLORS["text_main"])

    def _on_drag_enter(self, event):
        self.drop_canvas.configure(bg=self._get_color_str(COLORS["bg_hover"]))
        self._draw_dashed_border(color=self._get_color_str(COLORS["accent"]))

    def _on_drag_leave(self, event):
        self.drop_canvas.configure(bg=self._get_canvas_bg())
        self._draw_dashed_border()

    def _get_color_str(self, color_tuple):
        mode = ctk.get_appearance_mode()
        return color_tuple[0] if mode == "Light" else color_tuple[1]

    def _draw_dashed_border(self, color=None):
        if not hasattr(self, 'drop_canvas'):
            return
        self.drop_canvas.delete("border")
        w = self.drop_canvas.winfo_width()
        h = self.drop_canvas.winfo_height()
        if w < 10 or h < 10:
             self.after(100, self._draw_dashed_border)
             return

        if color is None:
            color = self._get_color_str(COLORS["border"])

        # Draw rect with dash
        self.drop_canvas.create_rectangle(
            5, 5, w-5, h-5, outline=color, width=2,
            dash=(10, 5), tags="border"
        )

def main():
    app = OrganizerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
