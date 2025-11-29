import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk, simpledialog
import json
from pathlib import Path
from organizer import FileOrganizer
from themes import THEMES

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro File Organizer")
        self.root.geometry("600x650")

        self.organizer = FileOrganizer()
        # Try loading config
        if self.organizer.load_config():
            print("Loaded custom configuration.")

        # Load recent folders
        self.load_recent()

        self.current_theme = "dark"  # Default to dark mode
        self.colors = THEMES[self.current_theme]
        self.style = ttk.Style()
        self.selected_path = None

        # 1. Folder Selection Area
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x", padx=10)

        self.lbl_path = tk.Label(frame_top, text="No folder selected", anchor="w", relief="sunken")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse = tk.Button(frame_top, text="Browse Folder", command=self.browse_folder)
        btn_browse.pack(side="right")

        # Recent Folders Combobox
        self.var_recent = tk.StringVar()
        self.opt_recent = ttk.Combobox(frame_top, textvariable=self.var_recent, values=self.recent_folders, state="readonly", width=3)
        self.opt_recent.set("...")
        self.opt_recent.pack(side="right", padx=5)
        self.opt_recent.bind("<<ComboboxSelected>>", self.on_recent_select)

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

        # Theme Toggle
        self.btn_theme = tk.Button(frame_options, text="Theme", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)

        # Settings Button
        self.btn_settings = tk.Button(frame_options, text="Settings", command=self.open_settings)
        self.btn_settings.pack(side="right", padx=5)

        # 2. Action Buttons
        self.btn_run = tk.Button(root, text="Start Organizing", command=self.start_thread, state="disabled", height=2)
        self.btn_run.pack(fill="x", padx=10, pady=5)

        # Undo Button
        self.btn_undo = tk.Button(root, text="Undo Last Run", command=self.undo_changes, state="disabled")
        self.btn_undo.pack(fill="x", padx=10, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 5))

        # 3. Log Area
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

        # Apply initial theme
        self.apply_theme()

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = THEMES[self.current_theme]
        self.apply_theme()

    def apply_theme(self):
        c = self.colors
        self.root.config(bg=c["bg"])

        # Configure ttk styles
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background=c["success_bg"], troughcolor=c["btn_bg"], bordercolor=c["bg"], lightcolor=c["success_bg"], darkcolor=c["success_bg"])

        # Recursively update widget colors
        self.update_widget_colors(self.root, c)

        # Re-apply specific states if needed
        if self.selected_path:
             self.btn_run.config(bg=c["success_bg"], fg=c["success_fg"])
        else:
             self.btn_run.config(bg=c["disabled_bg"], fg=c["disabled_fg"])

        if self.btn_undo["state"] == "normal":
             self.btn_undo.config(bg=c["undo_bg"], fg=c["undo_fg"])
        else:
             self.btn_undo.config(bg=c["disabled_bg"], fg=c["disabled_fg"])

    def update_widget_colors(self, widget, c):
        try:
            w_type = widget.winfo_class()
            if w_type in ('Frame', 'Label', 'Checkbutton'):
                widget.config(bg=c["bg"], fg=c["fg"])
                if w_type == 'Checkbutton':
                    widget.config(selectcolor=c["select_bg"], activebackground=c["bg"], activeforeground=c["fg"])
            elif w_type == 'Button':
                widget.config(bg=c["btn_bg"], fg=c["btn_fg"], activebackground=c["select_bg"], activeforeground=c["select_fg"])
            elif w_type == 'Text': # ScrolledText contains a Text widget
                widget.config(bg=c["text_bg"], fg=c["text_fg"], insertbackground=c["fg"])
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self.update_widget_colors(child, c)

    def load_recent(self):
        self.recent_folders = []
        if os.path.exists("recent.json"):
            try:
                with open("recent.json", "r") as f:
                    self.recent_folders = json.load(f)
            except:
                pass

    def add_recent(self, path):
        str_path = str(path)
        if str_path in self.recent_folders:
            self.recent_folders.remove(str_path)
        self.recent_folders.insert(0, str_path)
        self.recent_folders = self.recent_folders[:10] # Keep last 10

        # Update UI
        self.opt_recent['values'] = self.recent_folders

        with open("recent.json", "w") as f:
            json.dump(self.recent_folders, f)

    def on_recent_select(self, event):
        selected = self.var_recent.get()
        if selected and selected != "...":
            self.selected_path = Path(selected)
            self.lbl_path.config(text=str(self.selected_path))
            self.btn_run.config(state="normal", bg=self.colors["success_bg"], fg=self.colors["success_fg"])
            self.log("Selected (Recent): " + str(self.selected_path))
            # Move to top of recent list
            self.add_recent(self.selected_path)
            self.opt_recent.set("...") # Reset text to dot dot dot

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_path = Path(folder_selected)
            self.lbl_path.config(text=str(self.selected_path))
            self.btn_run.config(state="normal", bg=self.colors["success_bg"], fg=self.colors["success_fg"])
            self.log("Selected: " + str(self.selected_path))

    def open_settings(self):
        """Opens a window to configure file extensions and categories."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Configuration")
        settings_win.geometry("500x400")

        # Apply current theme to new window
        c = self.colors
        settings_win.config(bg=c["bg"])

        # UI Layout for Settings
        # Top: List of categories
        frame_list = tk.Frame(settings_win, bg=c["bg"])
        frame_list.pack(side="left", fill="y", padx=10, pady=10)

        lbl_cats = tk.Label(frame_list, text="Categories", bg=c["bg"], fg=c["fg"])
        lbl_cats.pack(anchor="w")

        listbox = tk.Listbox(frame_list, bg=c["entry_bg"], fg=c["entry_fg"], selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        listbox.pack(fill="y", expand=True)

        # Right: Edit area
        frame_edit = tk.Frame(settings_win, bg=c["bg"])
        frame_edit.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        lbl_exts = tk.Label(frame_edit, text="Extensions (comma separated)", bg=c["bg"], fg=c["fg"])
        lbl_exts.pack(anchor="w")

        txt_exts = tk.Text(frame_edit, height=10, bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"])
        txt_exts.pack(fill="x")

        # Buttons for Add/Delete Category
        frame_btns = tk.Frame(frame_edit, bg=c["bg"], pady=10)
        frame_btns.pack(fill="x")

        btn_add = tk.Button(frame_btns, text="Add Category", bg=c["btn_bg"], fg=c["btn_fg"])
        btn_add.pack(side="left", padx=5)

        btn_del = tk.Button(frame_btns, text="Delete Category", bg=c["btn_bg"], fg=c["btn_fg"])
        btn_del.pack(side="left", padx=5)

        btn_save = tk.Button(frame_edit, text="Save Configuration", bg=c["success_bg"], fg=c["success_fg"])
        btn_save.pack(side="bottom", pady=10)

        # Logic
        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            listbox.insert(tk.END, cat)

        def on_select(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                cat = listbox.get(index)
                exts = self.organizer.directories.get(cat, [])
                txt_exts.delete("1.0", tk.END)
                txt_exts.insert(tk.END, ", ".join(exts))

        listbox.bind('<<ListboxSelect>>', on_select)

        def save_current_edit():
            selection = listbox.curselection()
            if selection:
                cat = listbox.get(selection[0])
                raw_exts = txt_exts.get("1.0", tk.END).strip()
                if raw_exts:
                    ext_list = [e.strip() for e in raw_exts.split(',') if e.strip()]
                    self.organizer.directories[cat] = ext_list

        def save_config():
            save_current_edit() # Save pending changes in text box
            if self.organizer.save_config():
                self.organizer.extension_map = self.organizer._build_extension_map()
                messagebox.showinfo("Success", "Configuration saved!")
                settings_win.destroy()
            else:
                messagebox.showerror("Error", "Failed to save configuration.")

        def add_category():
            new_cat = simpledialog.askstring("New Category", "Enter category name:", parent=settings_win)
            if new_cat and new_cat not in self.organizer.directories:
                self.organizer.directories[new_cat] = []
                listbox.insert(tk.END, new_cat)
                listbox.selection_clear(0, tk.END)
                listbox.selection_set(tk.END)
                on_select(None)

        def delete_category():
            selection = listbox.curselection()
            if selection:
                cat = listbox.get(selection[0])
                if messagebox.askyesno("Confirm", f"Delete category '{cat}'?"):
                    del self.organizer.directories[cat]
                    listbox.delete(selection[0])
                    txt_exts.delete("1.0", tk.END)
                    self.last_selected_index = None # Prevent saving cleared state to wrong category

        btn_save.config(command=save_config)
        btn_add.config(command=add_category)
        btn_del.config(command=delete_category)

        # Ensure we also save changes when switching list items
        def on_select_wrapper(event):
            # Try to save previous selection first?
            # It's tricky because we don't know what was previously selected easily without tracking.
            # For simplicity, we only save when "Save Configuration" is clicked,
            # BUT we need to update the internal dict when switching away from a category.
            # Let's track last selected index.
            pass
            # Actually, standard UX: clicking another item discards unsaved changes in details view
            # unless we auto-save to memory.
            # Let's auto-save to memory (self.organizer.directories) when selection changes.

        self.last_selected_index = None

        def on_select_improved(event):
            # Save previous if any
            if self.last_selected_index is not None:
                try:
                    prev_cat = listbox.get(self.last_selected_index)
                    # Check if it still exists (might have been deleted)
                    if prev_cat in self.organizer.directories:
                        raw_exts = txt_exts.get("1.0", tk.END).strip()
                        ext_list = [e.strip() for e in raw_exts.split(',') if e.strip()]
                        self.organizer.directories[prev_cat] = ext_list
                except tk.TclError:
                    pass # Index might be out of bounds if deletion happened

            selection = listbox.curselection()
            if selection:
                index = selection[0]
                self.last_selected_index = index
                cat = listbox.get(index)
                exts = self.organizer.directories.get(cat, [])
                txt_exts.delete("1.0", tk.END)
                txt_exts.insert(tk.END, ", ".join(exts))
            else:
                self.last_selected_index = None

        listbox.bind('<<ListboxSelect>>', on_select_improved)


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
