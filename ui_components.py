import customtkinter as ctk
import tkinter as tk
from pathlib import Path
import threading

class FileCard(ctk.CTkFrame):
    """
    A card representing a file operation (move, rename, error).
    """
    def __init__(self, master, event_data, **kwargs):
        super().__init__(master, **kwargs)
        self.event = event_data

        # Colors
        self.configure(fg_color=("gray95", "gray20"))

        # Layout
        self.grid_columnconfigure(1, weight=1)

        # Icon / Method Badge
        method = event_data.get("method", "extension")
        confidence = event_data.get("confidence", 1.0)

        badge_color = "#3B8ED0" # Blue for Extension
        badge_text = "EXT"

        if method != "extension" and method != "ml-not-loaded":
            badge_color = "#9C27B0" # Purple for AI
            badge_text = f"AI {int(confidence*100)}%"

        if event_data.get("type") == "error":
            badge_color = "#D32F2F"
            badge_text = "ERR"

        self.lbl_badge = ctk.CTkLabel(self, text=badge_text, width=60, height=24,
                                      fg_color=badge_color, text_color="white", corner_radius=6,
                                      font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_badge.grid(row=0, column=0, rowspan=2, padx=10, pady=5)

        # Filename
        filename = event_data.get("file", "Unknown")
        self.lbl_name = ctk.CTkLabel(self, text=filename, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.lbl_name.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(5, 0))

        # Destination
        dest = event_data.get("destination", "")
        # Try to show relative path if possible, or just parent folder
        try:
             # This is tricky without knowing source root context in the card,
             # but we can try to show just the parent dir name
             dest_path = Path(dest)
             display_dest = f"→ {dest_path.parent.name}/{dest_path.name}"
        except:
             display_dest = f"→ {dest}"

        if event_data.get("type") == "error":
            display_dest = f"Error: {event_data.get('error')}"

        self.lbl_dest = ctk.CTkLabel(self, text=display_dest, font=ctk.CTkFont(size=12), text_color=("gray50", "gray70"), anchor="w")
        self.lbl_dest.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 5))


class ModelDownloadModal(ctk.CTkToplevel):
    def __init__(self, master, on_complete=None):
        super().__init__(master)
        self.title("Downloading AI Models")
        self.geometry("400x250")
        self.resizable(False, False)
        self.on_complete = on_complete

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.lbl_title = ctk.CTkLabel(self.frame, text="Setting up Smart AI", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(pady=(20, 10))

        self.lbl_desc = ctk.CTkLabel(self.frame, text="Downloading models (~2GB).\nThis only happens once.", text_color=("gray50", "gray70"))
        self.lbl_desc.pack(pady=(0, 20))

        self.progress = ctk.CTkProgressBar(self.frame)
        self.progress.pack(fill="x", padx=40, pady=10)
        self.progress.set(0)

        self.lbl_status = ctk.CTkLabel(self.frame, text="Initializing...")
        self.lbl_status.pack(pady=5)

        # Center the window
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (400 // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (250 // 2)
        self.geometry(f"+{x}+{y}")

        # Start download
        self.start_download()

        # Modal
        self.grab_set()

    def start_download(self):
        threading.Thread(target=self._download_task, daemon=True).start()

    def _download_task(self):
        try:
            from ml_organizer import MultimodalFileOrganizer
            # Mock organizer to reuse load_models logic
            ml_org = MultimodalFileOrganizer()

            def cb(msg, val):
                self.after(0, lambda: self._update_ui(msg, val))

            ml_org.ensure_models(progress_callback=cb)

            self.after(0, self._finish_success)
        except Exception as e:
            self.after(0, lambda: self._finish_error(str(e)))

    def _update_ui(self, msg, val):
        self.lbl_status.configure(text=msg)
        if val is not None:
            self.progress.set(val)

    def _finish_success(self):
        if self.on_complete:
            self.on_complete(True)
        self.destroy()

    def _finish_error(self, error_msg):
        self.lbl_status.configure(text=f"Error: {error_msg}", text_color="red")
        # Keep open for a moment or add button?
        # For now just close after 2s
        self.after(2000, self.destroy)
        if self.on_complete:
            self.on_complete(False)
