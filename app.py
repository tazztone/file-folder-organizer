import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path

# --- Configuration (Same as before) ---
DIRECTORIES = {
    "Images": [".jpeg", ".jpg", ".tiff", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".psd"],
    "Videos": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp"],
    "Documents": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwi", ".xsn", ".xps", ".dotx", ".docm", ".dox", ".rvg", ".rtf", ".rtfd", ".wpd", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".pdf", ".txt", ".md"],
    "Archives": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"],
    "Audio": [".aac", ".aa", ".aac", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".raw", ".vox", ".wav", ".wma"],
    "Code": [".py", ".js", ".html", ".css", ".php", ".c", ".cpp", ".h", ".java", ".cs"],
    "Executables": [".exe", ".msi", ".bat", ".sh"]
}

EXTENSION_MAP = {ext: category for category, exts in DIRECTORIES.items() for ext in exts}

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple File Organizer")
        self.root.geometry("500x400")

        # 1. Folder Selection Area
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x", padx=10)

        self.lbl_path = tk.Label(frame_top, text="No folder selected", fg="gray", anchor="w", relief="sunken")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse = tk.Button(frame_top, text="Browse Folder", command=self.browse_folder)
        btn_browse.pack(side="right")

        # 2. Action Button
        self.btn_run = tk.Button(root, text="Start Organizing", command=self.start_thread, state="disabled", bg="#dddddd", height=2)
        self.btn_run.pack(fill="x", padx=10, pady=5)

        # 3. Log Area
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.selected_path = None

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_path = Path(folder_selected)
            self.lbl_path.config(text=str(self.selected_path), fg="black")
            self.btn_run.config(state="normal", bg="#4CAF50", fg="white")
            self.log("Selected: " + str(self.selected_path))

    def log(self, message):
        """Thread-safe logging to the text box."""
        def _update():
            self.log_area.config(state='normal')
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state='disabled')
        self.root.after(0, _update)

    def start_thread(self):
        """Run logic in a separate thread so the GUI doesn't freeze."""
        self.btn_run.config(state="disabled", text="Running...")
        threading.Thread(target=self.organize_files, daemon=True).start()

    def get_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        counter = 1
        while True:
            new_path = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not new_path.exists():
                return new_path
            counter += 1

    def organize_files(self):
        if not self.selected_path:
            return

        self.log("--- Starting Organization ---")
        count = 0
        errors = 0

        try:
            for item in self.selected_path.iterdir():
                if not item.is_file() or item.name == Path(__file__).name:
                    continue

                category = EXTENSION_MAP.get(item.suffix.lower(), "Others")
                dest_folder = self.selected_path / category
                
                try:
                    dest_folder.mkdir(exist_ok=True)
                    dest_path = self.get_unique_path(dest_folder / item.name)
                    shutil.move(str(item), dest_path)
                    self.log(f"Moved: {item.name} -> {category}")
                    count += 1
                except Exception as e:
                    self.log(f"ERROR moving {item.name}: {e}")
                    errors += 1
            
            self.log(f"--- Done. Moved {count} files. ({errors} errors) ---")
            messagebox.showinfo("Success", f"Organization complete!\nMoved {count} files.")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", str(e))
        
        # Reset button state
        self.root.after(0, lambda: self.btn_run.config(state="normal", text="Start Organizing"))

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()
