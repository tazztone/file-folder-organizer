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
from pathlib import Path
from organizer import FileOrganizer
from settings_dialog_ctk import SettingsDialog
from batch_dialog_ctk import BatchDialog
from ui_utils import ToolTip

# Set default theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class OrganizerApp(ctk.CTk, DnDWrapper):
    def __init__(self):
        super().__init__()
        if hasattr(tkinterdnd2, 'TkinterDnD') and hasattr(self, 'TkdndVersion'):
             pass

        if 'tkinterdnd2' in globals():
             try:
                 tkinterdnd2.TkinterDnD._require(self)
             except:
                 pass

        self.title("Pro File Organizer")
        self.geometry("900x700")

        # Icon setup
        try:
             # Create a simple icon
             from PIL import Image, ImageTk, ImageDraw
             icon_size = 32
             icon_img = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
             draw = ImageDraw.Draw(icon_img)
             # Draw a folder-like shape
             draw.rectangle([2, 6, 30, 28], fill="#3B8ED0", outline="#1F6AA5")
             draw.rectangle([2, 2, 14, 6], fill="#3B8ED0", outline="#1F6AA5")

             # Convert to PhotoImage for Tkinter
             # ctk.CTk uses standard tkinter iconphoto
             self.icon_photo = ImageTk.PhotoImage(icon_img)
             self.iconphoto(False, self.icon_photo)
        except Exception as e:
             print(f"Failed to set icon: {e}")

        self.organizer = FileOrganizer()
        if self.organizer.load_config():
            print("Loaded custom configuration.")

        # Load theme from config if available
        theme = self.organizer.get_theme_mode()
        if theme:
            ctk.set_appearance_mode(theme)

        self.load_recent()
        self.selected_path = None
        self.is_running = False
        self.start_time = 0

        # --- Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Push bottom items down

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Pro Organizer", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_btn_home = ctk.CTkButton(self.sidebar_frame, text="Home", command=self.show_home)
        self.sidebar_btn_home.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_btn_org = ctk.CTkButton(self.sidebar_frame, text="Organizer", command=self.show_organizer)
        self.sidebar_btn_org.grid(row=2, column=0, padx=20, pady=10)

        self.sidebar_btn_batch = ctk.CTkButton(self.sidebar_frame, text="Batch Mode", command=self.open_batch)
        self.sidebar_btn_batch.grid(row=3, column=0, padx=20, pady=10)

        self.sidebar_btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=self.open_settings)
        self.sidebar_btn_settings.grid(row=4, column=0, padx=20, pady=10)

        # Theme Switcher
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

        current_mode = self.organizer.get_theme_mode() or "System"
        self.appearance_mode_optionemenu.set(current_mode)
        ctk.set_appearance_mode(current_mode)

        # 2. Main Area Containers
        # We use a container frame to hold views
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize Views
        self._init_home_frame()
        self._init_organizer_frame()

        # Show Home by default
        self.show_home()

        # Check models availability in background on startup
        self.check_ml_status()

    def _init_home_frame(self):
        self.frame_home = ctk.CTkFrame(self.container, fg_color="transparent")

        lbl_welcome = ctk.CTkLabel(self.frame_home, text="Welcome to Pro File Organizer", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_welcome.pack(pady=(40, 20))

        # Quick Actions
        frame_actions = ctk.CTkFrame(self.frame_home)
        frame_actions.pack(fill="x", padx=40, pady=20)

        lbl_actions = ctk.CTkLabel(frame_actions, text="Quick Actions", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_actions.pack(anchor="w", padx=20, pady=10)

        btn_start = ctk.CTkButton(frame_actions, text="Start New Organization", command=self.show_organizer, height=40)
        btn_start.pack(padx=20, pady=10, fill="x")

        btn_batch = ctk.CTkButton(frame_actions, text="Batch Processing", command=self.open_batch, height=40)
        btn_batch.pack(padx=20, pady=10, fill="x")

        # Recent
        frame_recent = ctk.CTkFrame(self.frame_home)
        frame_recent.pack(fill="both", expand=True, padx=40, pady=20)

        lbl_recent = ctk.CTkLabel(frame_recent, text="Recent Folders", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_recent.pack(anchor="w", padx=20, pady=10)

        self.scroll_recent = ctk.CTkScrollableFrame(frame_recent, fg_color="transparent")
        self.scroll_recent.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh_recent_home()

    def refresh_recent_home(self):
        for w in self.scroll_recent.winfo_children():
            w.destroy()

        if not self.recent_folders:
            ctk.CTkLabel(self.scroll_recent, text="No recent folders.").pack(pady=10)
            return

        for folder in self.recent_folders:
            btn = ctk.CTkButton(self.scroll_recent, text=folder, anchor="w", fg_color="transparent",
                                border_width=1, border_color="gray", text_color=("black", "white"),
                                command=lambda f=folder: self.load_folder_and_show(f))
            btn.pack(fill="x", pady=2)

    def load_folder_and_show(self, path):
        self.set_folder(path)
        self.show_organizer()

    def _init_organizer_frame(self):
        self.frame_organizer = ctk.CTkFrame(self.container, fg_color="transparent")

        # Path Selection
        self.frame_path = ctk.CTkFrame(self.frame_organizer)
        self.frame_path.pack(fill="x", pady=(0, 20))

        # Drag and Drop support
        try:
            self.frame_path.drop_target_register(DND_FILES)
            self.frame_path.dnd_bind('<<Drop>>', self.on_drop)
            self.frame_path.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.frame_path.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        except Exception as e:
            print(f"DnD setup failed: {e}")

        self.lbl_path = ctk.CTkLabel(self.frame_path, text="No folder selected (Drag & Drop here)", anchor="w", fg_color="transparent")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        self.btn_browse = ctk.CTkButton(self.frame_path, text="Browse", command=self.browse_folder, width=100)
        self.btn_browse.pack(side="right", padx=10, pady=10)

        # Recent (Dropdown in Organizer view)
        self.option_recent = ctk.CTkOptionMenu(self.frame_path, values=["Recent..."], command=self.on_recent_select, width=150)
        self.option_recent.pack(side="right", padx=(0, 10), pady=10)
        self.update_recent_menu()

        # Options
        self.frame_options = ctk.CTkFrame(self.frame_organizer)
        self.frame_options.pack(fill="x", pady=(0, 20))

        self.var_recursive = ctk.BooleanVar(value=False)
        self.switch_rec = ctk.CTkSwitch(self.frame_options, text="Include Subfolders", variable=self.var_recursive)
        self.switch_rec.pack(side="left", padx=20, pady=10)
        ToolTip(self.switch_rec, "Search and organize files in subdirectories")

        self.var_date_sort = ctk.BooleanVar(value=False)
        self.switch_date = ctk.CTkSwitch(self.frame_options, text="Sort by Date", variable=self.var_date_sort)
        self.switch_date.pack(side="left", padx=20, pady=10)
        ToolTip(self.switch_date, "Organize files into Year/Month folders")

        self.var_del_empty = ctk.BooleanVar(value=False)
        self.switch_del = ctk.CTkSwitch(self.frame_options, text="Delete Empty", variable=self.var_del_empty)
        self.switch_del.pack(side="left", padx=20, pady=10)

        self.var_dry_run = ctk.BooleanVar(value=False)
        self.switch_dry = ctk.CTkSwitch(self.frame_options, text="Dry Run", variable=self.var_dry_run)
        self.switch_dry.pack(side="left", padx=20, pady=10)

        self.var_rollback = ctk.BooleanVar(value=True)
        self.switch_rollback = ctk.CTkSwitch(self.frame_options, text="Rollback on Error", variable=self.var_rollback)
        self.switch_rollback.pack(side="left", padx=20, pady=10)

        # ML Categorization
        self.var_ml_categorize = tk.BooleanVar(value=False)
        self.chk_ml = ctk.CTkSwitch(self.frame_options, text="Smart Categorization (AI)", variable=self.var_ml_categorize)
        self.chk_ml.pack(side="left", padx=20, pady=10)
        ToolTip(self.chk_ml, "Use AI to understand file content for better organization\n(Will download models on first run)")


        # Actions
        self.frame_actions = ctk.CTkFrame(self.frame_organizer, fg_color="transparent")
        self.frame_actions.pack(fill="x", pady=(0, 20))

        self.btn_preview = ctk.CTkButton(self.frame_actions, text="Preview", command=self.run_preview, state="disabled")
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_run = ctk.CTkButton(self.frame_actions, text="Start Organizing", command=self.start_thread, state="disabled", fg_color="green", hover_color="darkgreen")
        self.btn_run.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_undo = ctk.CTkButton(self.frame_actions, text="Undo Last Run", command=self.undo_changes, state="disabled", fg_color="red", hover_color="darkred")
        self.btn_undo.pack(side="left", fill="x", expand=True)

        # Progress
        self.lbl_progress = ctk.CTkLabel(self.frame_organizer, text="", anchor="w", height=20)
        self.lbl_progress.pack(fill="x", padx=5)

        self.progress = ctk.CTkProgressBar(self.frame_organizer)
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.set(0)

        # Logs
        self.frame_logs = ctk.CTkFrame(self.frame_organizer, fg_color="transparent")
        self.frame_logs.pack(fill="both", expand=True, pady=(0, 10))

        # Log Toolbar
        self.frame_log_tools = ctk.CTkFrame(self.frame_logs, height=30)
        self.frame_log_tools.pack(fill="x", pady=(0, 5))

        self.entry_search = ctk.CTkEntry(self.frame_log_tools, placeholder_text="Search logs...", width=200)
        self.entry_search.pack(side="left", padx=5, pady=2)

        self.btn_search = ctk.CTkButton(self.frame_log_tools, text="Find", width=60, command=self.search_log)
        self.btn_search.pack(side="left", padx=5, pady=2)

        self.btn_export_log = ctk.CTkButton(self.frame_log_tools, text="Export Log", width=100, command=self.export_log)
        self.btn_export_log.pack(side="right", padx=5, pady=2)

        self.log_area = ctk.CTkTextbox(self.frame_logs, state="disabled")
        self.log_area.pack(fill="both", expand=True)

        # Tags for coloring (CTkTextbox uses underlying tk.Text)
        try:
             self.log_area._textbox.tag_config("category", foreground="#3B8ED0") # Blueish
             self.log_area._textbox.tag_config("error", foreground="red")
             self.log_area._textbox.tag_config("success", foreground="green")
             self.log_area._textbox.tag_config("ml", foreground="purple")
        except:
             pass

        # Shortcuts
        self.bind('<Return>', self.start_thread)
        self.bind('<Escape>', lambda e: self.stop_process())

    def show_home(self):
        self.frame_organizer.pack_forget()
        self.frame_home.pack(fill="both", expand=True)
        self.refresh_recent_home()
        self.sidebar_btn_home.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.sidebar_btn_org.configure(fg_color="transparent")

    def show_organizer(self):
        self.frame_home.pack_forget()
        self.frame_organizer.pack(fill="both", expand=True)
        self.sidebar_btn_home.configure(fg_color="transparent")
        self.sidebar_btn_org.configure(fg_color=["#3B8ED0", "#1F6AA5"])

    def check_ml_status(self):
        """Checks if ML models are present and updates UI hint if needed."""
        def _check():
            try:
                from ml_organizer import MultimodalFileOrganizer
                present = MultimodalFileOrganizer.are_models_present(MultimodalFileOrganizer)
                if not present:
                    self.after(0, lambda: ToolTip(self.chk_ml, "Models missing. Will download (~2GB) on first run."))
            except ImportError:
                pass

        threading.Thread(target=_check, daemon=True).start()

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
            self.selected_path = Path(selected)
            self.lbl_path.configure(text=str(self.selected_path))
            self.enable_buttons()
            self.log("Selected (Recent): " + str(self.selected_path))
            self.add_recent(self.selected_path)
        else:
             self.option_recent.set("Recent...")

    def on_drag_enter(self, event):
        self.frame_path.configure(border_width=2, border_color="#3B8ED0")

    def on_drag_leave(self, event):
        self.frame_path.configure(border_width=0) # Or default

    def on_drop(self, event):
        self.on_drag_leave(event) # Reset border
        if event.data:
            path = event.data
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            self.set_folder(path)

    def set_folder(self, path):
        if os.path.isdir(path):
            self.selected_path = Path(path)
            self.lbl_path.configure(text=str(self.selected_path))
            self.enable_buttons()
            self.log("Selected: " + str(self.selected_path))
            self.add_recent(self.selected_path)
        else:
             self.log("Dropped item is not a folder: " + path)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.set_folder(folder_selected)

    def enable_buttons(self):
        self.btn_run.configure(state="normal")
        self.btn_preview.configure(state="normal")

    def open_settings(self):
        SettingsDialog(self, self.organizer)

    def open_batch(self):
        BatchDialog(self, self.organizer, on_complete_callback=self.update_undo_button)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.organizer.save_theme_mode(new_appearance_mode)

    def log(self, message):
        def _update():
            self.log_area.configure(state='normal')

            # Simple heuristic for coloring
            tags = []
            if "ERROR" in message or "Error" in message:
                tags.append("error")
            elif "Moved:" in message or "Renamed & Moved:" in message:
                tags.append("success")
            elif "[ML Init]" in message or "ML:" in message:
                tags.append("ml")

            # We use the underlying widget to insert with tags
            # CTkTextbox.insert doesn't support tags directly usually
            try:
                self.log_area._textbox.insert("end", message + "\n", tuple(tags))
            except:
                self.log_area.insert("end", message + "\n")

            self.log_area.see("end")
            self.log_area.configure(state='disabled')
        self.after(0, _update)

        try:
            with open("organizer.log", "a") as f:
                 f.write(message + "\n")
        except:
            pass

    def update_progress(self, current, total, filename=""):
        def _update():
            if total > 0:
                self.progress.set(current / total)

                # Speed & ETA
                elapsed = time.time() - self.start_time
                if elapsed > 0 and current > 0:
                    speed = current / elapsed
                    remaining_files = total - current
                    eta = remaining_files / speed if speed > 0 else 0

                    status_text = f"Processing: {filename} ({speed:.1f} files/s, ETA: {eta:.0f}s)"
                else:
                    status_text = f"Processing: {filename}"

                self.lbl_progress.configure(text=status_text)
            else:
                # Indeterminate or just message (e.g. ML loading)
                self.lbl_progress.configure(text=f"Status: {filename}" if filename else "")

        self.after(0, _update)

    def start_thread(self, event=None):
        if not self.selected_path:
             messagebox.showwarning("Warning", "Please select a folder first.")
             return

        if not self.var_dry_run.get():
             if not messagebox.askyesno("Confirm", "Are you sure you want to organize files?"):
                 return

        # Additional check for ML Download
        if self.var_ml_categorize.get():
             from ml_organizer import MultimodalFileOrganizer
             if not MultimodalFileOrganizer.are_models_present(MultimodalFileOrganizer):
                  if not messagebox.askyesno("Download ML Models",
                                             "Smart Categorization requires downloading AI models (~2GB).\n"
                                             "This will happen automatically now and may take a few minutes.\n\n"
                                             "Do you want to proceed?"):
                       return

        self.run_organization(dry_run_override=None)

    def run_preview(self):
        self.run_organization(dry_run_override=True)

    def search_log(self):
        query = self.entry_search.get()
        if not query:
            return

        # Clear previous tags if any
        try:
             # Access underlying text widget safely
             text_widget = self.log_area._textbox
             text_widget.tag_remove('found', '1.0', tk.END)

             if query:
                idx = '1.0'
                while 1:
                    idx = text_widget.search(query, idx, nocase=1, stopindex=tk.END)
                    if not idx: break
                    lastidx = '%s+%dc' % (idx, len(query))
                    text_widget.tag_add('found', idx, lastidx)
                    idx = lastidx

                text_widget.tag_config('found', foreground='red', background='yellow')
        except Exception as e:
             print(f"Search error: {e}")

    def export_log(self):
        content = self.log_area.get("1.0", "end")
        if not content.strip():
             messagebox.showinfo("Info", "Log is empty.")
             return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
             try:
                 with open(path, "w") as f:
                      f.write(content)
                 messagebox.showinfo("Success", "Log exported successfully.")
             except Exception as e:
                 messagebox.showerror("Error", f"Failed to save log: {e}")

    def run_organization(self, dry_run_override=None):
        self.is_running = True
        self.start_time = time.time() # Reset start time
        self.btn_run.configure(text="Stop", fg_color="red", hover_color="darkred", command=self.stop_process)
        self.btn_preview.configure(state="disabled")
        self.btn_undo.configure(state="disabled")
        self.progress.set(0)

        threading.Thread(target=self.organize_files, args=(dry_run_override,), daemon=True).start()

    def stop_process(self):
        if hasattr(self, 'is_running') and self.is_running:
            self.is_running = False
            self.btn_run.configure(state="disabled", text="Stopping...")

    def organize_files(self, dry_run_override=None):
        if not self.selected_path:
            return

        dry_run = dry_run_override if dry_run_override is not None else self.var_dry_run.get()
        use_ml = self.var_ml_categorize.get()

        stats = self.organizer.organize_files(
            source_path=self.selected_path,
            recursive=self.var_recursive.get(),
            date_sort=self.var_date_sort.get(),
            del_empty=self.var_del_empty.get(),
            dry_run=dry_run,
            progress_callback=self.update_progress,
            log_callback=self.log,
            check_stop=lambda: not self.is_running,
            rollback_on_error=self.var_rollback.get(),
            use_ml=use_ml
        )

        msg = f"Organization {'stopped' if not self.is_running else 'complete'}!\n{'Would move' if dry_run else 'Moved'} {stats['moved']} files."
        if stats.get('rolled_back'):
             msg += "\n\nOperation was ROLLED BACK due to errors."

        self.after(0, lambda: messagebox.showinfo("Result", msg))
        
        def reset_ui():
            self.btn_run.configure(state="normal", text="Start Organizing", fg_color="green", hover_color="darkgreen", command=self.start_thread)
            self.btn_preview.configure(state="normal")
            self.lbl_progress.configure(text="")
            self.progress.set(0)
            self.update_undo_button()

        self.after(0, reset_ui)

    def update_undo_button(self):
        stack_size = len(self.organizer.undo_stack)
        if stack_size > 0:
            self.btn_undo.configure(state="normal", text=f"Undo Last Run ({stack_size})")
        else:
            self.btn_undo.configure(state="disabled", text="Undo Last Run")

    def undo_changes(self):
        stack_size = len(self.organizer.undo_stack)
        if stack_size == 0:
            return

        last_op = self.organizer.undo_stack[-1]
        history_len = len(last_op.get("history", []))

        if not messagebox.askyesno("Confirm Undo", f"Undo last operation?\nThis will restore {history_len} files."):
             return

        self.btn_undo.configure(state="disabled")

        def _undo_thread():
            count = self.organizer.undo_changes(log_callback=self.log)
            self.after(0, lambda: messagebox.showinfo("Undo", f"Restored {count} files."))
            self.after(0, self.update_undo_button)

        threading.Thread(target=_undo_thread, daemon=True).start()

if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
