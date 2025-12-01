import customtkinter as ctk
import tkinter as tk
from pathlib import Path
import threading
import sys
import shutil
import os

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


class RedirectedStderr:
    """Redirects stderr to a Tkinter text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stderr = sys.stderr

    def write(self, string):
        # We can update the UI here. Since write might be called from a thread,
        # we should use after() to be thread safe, but for simple text appending
        # usually direct modification works or we can schedule it.
        # To be safe:
        try:
            self.text_widget.after(0, lambda: self._append(string))
        except:
            pass # Widget might be destroyed

    def _append(self, string):
        try:
            self.text_widget.configure(state="normal")
            # Handle carriage return for progress bars (replace last line if starts with \r)
            # Simplification: Just append for now, but if string contains \r, delete last line?
            # tqdm sends \r then the text.
            if '\r' in string:
                # This is a bit complex to handle perfectly for multiple progress bars.
                # Simple approach: Replace \r with \n for log view, or just append.
                # Better approach for "log_": Just append.
                pass

            self.text_widget.insert("end", string)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except:
            pass

    def flush(self):
        pass

class ModelDownloadModal(ctk.CTkToplevel):
    def __init__(self, master, on_complete=None):
        super().__init__(master)
        self.title("Smart AI Setup")
        self.geometry("500x400")
        self.resizable(False, False)
        self.on_complete = on_complete
        self.download_started = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.lbl_title = ctk.CTkLabel(self.frame, text="Download AI Models", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(pady=(20, 10))

        # Description
        desc_text = (
            "Smart Categorization requires advanced AI models to analyze your files.\n"
            "This involves a one-time download."
        )
        self.lbl_desc = ctk.CTkLabel(self.frame, text=desc_text, justify="center")
        self.lbl_desc.pack(pady=(0, 20))

        # Details Frame
        self.frame_details = ctk.CTkFrame(self.frame, fg_color=("gray90", "gray25"))
        self.frame_details.pack(fill="x", padx=20, pady=(0, 20))

        self._add_detail_row(self.frame_details, "Text Model:", "Qwen/Qwen3-Embedding-0.6B")
        self._add_detail_row(self.frame_details, "Image Model:", "google/siglip2-base-patch32-256")
        self._add_detail_row(self.frame_details, "Download Size:", "~3.0 GB")

        # Disk Space Check
        free_space_gb = self._get_free_space_gb()
        space_color = "green" if free_space_gb > 5 else "orange"
        if free_space_gb < 4: space_color = "red"

        self._add_detail_row(self.frame_details, "Free Space:", f"{free_space_gb:.2f} GB", value_color=space_color)

        # Log/Progress Area (Initially Hidden or Small)
        self.txt_log = ctk.CTkTextbox(self.frame, height=100, font=("Consolas", 10))
        # We pack it later or now?
        # Let's pack it but empty.
        # self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Buttons
        self.frame_btns = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.frame_btns.pack(fill="x", padx=20, pady=10, side="bottom")

        self.btn_cancel = ctk.CTkButton(self.frame_btns, text="Cancel", fg_color="transparent", border_width=1,
                                        text_color=("gray10", "gray90"), command=self.on_cancel)
        self.btn_cancel.pack(side="left", expand=True, padx=5)

        self.btn_start = ctk.CTkButton(self.frame_btns, text="Download Models", fg_color="green", hover_color="darkgreen",
                                       command=self.start_download)
        self.btn_start.pack(side="right", expand=True, padx=5)

        if free_space_gb < 4:
            self.lbl_warn = ctk.CTkLabel(self.frame, text="⚠️ Low Disk Space", text_color="red")
            self.lbl_warn.pack(side="bottom", pady=5)
            # Optional: Disable start button? Use discretion.
            # self.btn_start.configure(state="disabled")

        # Center the window
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (500 // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")

        # Modal
        self.grab_set()

    def _add_detail_row(self, parent, label, value, value_color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=2)

        l = ctk.CTkLabel(row, text=label, font=ctk.CTkFont(weight="bold"), width=100, anchor="w")
        l.pack(side="left")

        v = ctk.CTkLabel(row, text=value, text_color=value_color if value_color else ("black", "white"), anchor="w")
        v.pack(side="left", fill="x", expand=True)

    def _get_free_space_gb(self):
        try:
            # Check HF_HOME or default
            hf_home = os.environ.get("HF_HOME")
            if not hf_home:
                xdg = os.environ.get("XDG_CACHE_HOME")
                if xdg:
                    hf_home = os.path.join(xdg, "huggingface")
                else:
                    hf_home = os.path.expanduser("~/.cache/huggingface")

            # Ensure dir exists for check or check parent
            check_path = hf_home
            if not os.path.exists(check_path):
                check_path = os.path.expanduser("~")

            total, used, free = shutil.disk_usage(check_path)
            return free / (1024**3)
        except:
            return 0.0

    def start_download(self):
        if self.download_started: return
        self.download_started = True

        # Disable buttons
        self.btn_start.configure(state="disabled", text="Downloading...")
        self.btn_cancel.configure(state="disabled")

        # Show Log Area
        self.frame_details.pack_forget() # Hide details to make room
        self.lbl_desc.configure(text="Please wait. This may take a few minutes depending on your connection.")
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.txt_log.insert("1.0", "Initializing download...\n")

        threading.Thread(target=self._download_task, daemon=True).start()

    def on_cancel(self):
        if self.on_complete:
            self.on_complete(False)
        self.destroy()

    def _download_task(self):
        # Redirect stderr
        redirector = RedirectedStderr(self.txt_log)
        original_stderr = sys.stderr
        sys.stderr = redirector

        success = False
        error_msg = ""

        try:
            from ml_organizer import MultimodalFileOrganizer
            # Mock organizer to reuse load_models logic
            ml_org = MultimodalFileOrganizer()

            # We don't need a callback if we are capturing stderr/tqdm
            # But the original code used one. Let's pass a dummy one or one that logs to our text box too.
            def cb(msg, val):
                # Only log messages, ignore float progress since tqdm handles it
                # or write to redirector
                sys.stderr.write(f"\n[System] {msg}\n")

            ml_org.ensure_models(progress_callback=cb)
            success = True

        except Exception as e:
            error_msg = str(e)
            sys.stderr.write(f"\nError: {error_msg}\n")

        finally:
            sys.stderr = original_stderr
            if success:
                self.after(0, self._finish_success)
            else:
                # self.after(0, lambda: self._finish_error(error_msg))
                # Instead of closing, let the user see the error log?
                # For now, close with failure
                self.after(2000, lambda: self._finish_error(error_msg))

    def _finish_success(self):
        if self.on_complete:
            self.on_complete(True)
        self.destroy()

    def _finish_error(self, error_msg):
        if self.on_complete:
            self.on_complete(False)
        self.destroy()
