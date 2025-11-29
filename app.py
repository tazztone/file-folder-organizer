import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from pathlib import Path
from organizer import FileOrganizer

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro File Organizer")
        self.root.geometry("600x600")

        self.organizer = FileOrganizer()
        # Try loading config
        if self.organizer.load_config():
            print("Loaded custom configuration.")

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

        # Recursive Checkbox
        self.var_recursive = tk.BooleanVar()
        chk_rec = tk.Checkbutton(frame_options, text="Include Subfolders", variable=self.var_recursive)
        chk_rec.pack(side="left", padx=5)

        # Date Sorting Checkbox
        self.var_date_sort = tk.BooleanVar()
        chk_date = tk.Checkbutton(frame_options, text="Sort by Date", variable=self.var_date_sort)
        chk_date.pack(side="left", padx=5)

        # Delete Empty Folders Checkbox
        self.var_del_empty = tk.BooleanVar()
        chk_del = tk.Checkbutton(frame_options, text="Delete Empty Folders", variable=self.var_del_empty)
        chk_del.pack(side="left", padx=5)

        # Dry Run Checkbox
        self.var_dry_run = tk.BooleanVar()
        chk_dry = tk.Checkbutton(frame_options, text="Dry Run (Simulate)", variable=self.var_dry_run)
        chk_dry.pack(side="left", padx=5)

        # 2. Action Buttons
        self.btn_run = tk.Button(root, text="Start Organizing", command=self.start_thread, state="disabled", bg="#dddddd", height=2)
        self.btn_run.pack(fill="x", padx=10, pady=5)

        # Undo Button
        self.btn_undo = tk.Button(root, text="Undo Last Run", command=self.undo_changes, state="disabled", bg="#ffcccc")
        self.btn_undo.pack(fill="x", padx=10, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

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

    def update_progress(self, current, total):
        """Thread-safe progress bar update."""
        def _update():
            if total > 0:
                self.progress["maximum"] = total
                self.progress["value"] = current
        self.root.after(0, _update)

    def start_thread(self):
        """Run logic in a separate thread so the GUI doesn't freeze."""
        self.btn_run.config(state="disabled", text="Running...")
        self.btn_undo.config(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self.organize_files, daemon=True).start()

    def organize_files(self):
        if not self.selected_path:
            return

        dry_run = self.var_dry_run.get()

        stats = self.organizer.organize_files(
            source_path=self.selected_path,
            recursive=self.var_recursive.get(),
            date_sort=self.var_date_sort.get(),
            del_empty=self.var_del_empty.get(),
            dry_run=dry_run,
            progress_callback=self.update_progress,
            log_callback=self.log
        )

        messagebox.showinfo("Success", f"Organization complete!\n{'Would move' if dry_run else 'Moved'} {stats['moved']} files.")

        # Enable Undo if we moved anything and it wasn't a dry run
        if stats['moved'] > 0 and not dry_run:
            self.root.after(0, lambda: self.btn_undo.config(state="normal"))
        
        # Reset run button
        self.root.after(0, lambda: self.btn_run.config(state="normal", text="Start Organizing"))

    def undo_changes(self):
        """Reverses the last organization run."""
        self.btn_undo.config(state="disabled")

        def _undo_thread():
            count = self.organizer.undo_changes(log_callback=self.log)
            messagebox.showinfo("Undo", f"Restored {count} files to their original locations.")

        threading.Thread(target=_undo_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.mainloop()
