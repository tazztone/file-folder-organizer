import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path
from datetime import datetime

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
        self.root.title("Pro File Organizer")
        self.root.geometry("600x550")

        # 1. Folder Selection Area
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x", padx=10)

        self.lbl_path = tk.Label(frame_top, text="No folder selected", fg="gray", anchor="w", relief="sunken")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse = tk.Button(frame_top, text="Browse Folder", command=self.browse_folder)
        btn_browse.pack(side="right")

        # Options Frame
        frame_options = tk.Frame(root, pady=5)
        frame_options.pack(fill="x", padx=10)

        # NEW: Recursive Checkbox
        self.var_recursive = tk.BooleanVar()
        chk_rec = tk.Checkbutton(frame_options, text="Include Subfolders", variable=self.var_recursive)
        chk_rec.pack(side="left", padx=5)

        # NEW: Date Sorting Checkbox
        self.var_date_sort = tk.BooleanVar()
        chk_date = tk.Checkbutton(frame_options, text="Sort by Date", variable=self.var_date_sort)
        chk_date.pack(side="left", padx=5)

        # NEW: Delete Empty Folders Checkbox
        self.var_del_empty = tk.BooleanVar()
        chk_del = tk.Checkbutton(frame_options, text="Delete Empty Folders", variable=self.var_del_empty)
        chk_del.pack(side="left", padx=5)

        # 2. Action Buttons
        self.btn_run = tk.Button(root, text="Start Organizing", command=self.start_thread, state="disabled", bg="#dddddd", height=2)
        self.btn_run.pack(fill="x", padx=10, pady=5)

        # NEW: Undo Button
        self.btn_undo = tk.Button(root, text="Undo Last Run", command=self.undo_changes, state="disabled", bg="#ffcccc")
        self.btn_undo.pack(fill="x", padx=10, pady=5)

        # 3. Log Area
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.selected_path = None
        self.history = []  # Store moves here: [(new_path, old_path), ...]

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
        self.btn_undo.config(state="disabled")
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

        self.history.clear() # Clear previous history on new run
        self.log("--- Starting Organization ---")
        count = 0
        errors = 0

        # Check recursive option
        is_recursive = self.var_recursive.get()
        if is_recursive:
            iterator = self.selected_path.rglob('*')
        else:
            iterator = self.selected_path.iterdir()

        # Collect files to move first to avoid iterator issues
        try:
            files_to_move = [item for item in iterator if item.is_file() and item.name != Path(__file__).name]
        except Exception as e:
            self.log(f"Error scanning files: {e}")
            self.root.after(0, lambda: self.btn_run.config(state="normal", text="Start Organizing"))
            return

        for item in files_to_move:
            category = EXTENSION_MAP.get(item.suffix.lower(), "Others")
            target_dir = self.selected_path / category

            # Date-Based Sorting
            if self.var_date_sort.get():
                try:
                    mtime = item.stat().st_mtime
                    dt = datetime.fromtimestamp(mtime)
                    year = dt.strftime("%Y")
                    month = dt.strftime("%B")
                    target_dir = target_dir / year / month
                except Exception as e:
                    self.log(f"Date error for {item.name}: {e}")

            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                dest_path = self.get_unique_path(target_dir / item.name)

                shutil.move(str(item), dest_path)
                self.history.append((dest_path, item))  # Save paths for undo

                # Show relative path for cleaner log
                try:
                    rel_dest = dest_path.relative_to(self.selected_path)
                except ValueError:
                    rel_dest = dest_path.name

                self.log(f"Moved: {item.name} -> {rel_dest}")
                count += 1
            except Exception as e:
                self.log(f"ERROR moving {item.name}: {e}")
                errors += 1

        # Delete Empty Folders
        if self.var_del_empty.get():
            self.log("Cleaning up empty folders...")
            deleted_folders = 0
            for root_dir, dirs, files in os.walk(self.selected_path, topdown=False):
                for name in dirs:
                    d = os.path.join(root_dir, name)
                    try:
                        os.rmdir(d) # Only works if empty
                        deleted_folders += 1
                    except OSError:
                        pass
            if deleted_folders > 0:
                self.log(f"Removed {deleted_folders} empty folders.")
            
        self.log(f"--- Done. Moved {count} files. ({errors} errors) ---")
        messagebox.showinfo("Success", f"Organization complete!\nMoved {count} files.")

        # Enable Undo if we moved anything
        if self.history:
            self.root.after(0, lambda: self.btn_undo.config(state="normal"))
        
        # Reset run button
        self.root.after(0, lambda: self.btn_run.config(state="normal", text="Start Organizing"))

    def undo_changes(self):
        """Reverses the last organization run."""
        if not self.history: return

        count = 0
        self.log("\n--- Undoing Changes ---")

        # Process in reverse order (LIFO)
        for current_path, original_path in reversed(self.history):
            try:
                if current_path.exists():
                    # Ensure original directory exists (in case we deleted it)
                    original_path.parent.mkdir(parents=True, exist_ok=True)

                    shutil.move(str(current_path), str(original_path))
                    count += 1
            except Exception as e:
                self.log(f"Failed to undo {current_path.name}: {e}")

        self.history.clear()
        self.btn_undo.config(state="disabled")
        self.log(f"--- Undo Complete. Restored {count} files. ---")
        messagebox.showinfo("Undo", f"Restored {count} files to their original locations.")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()
