import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk, simpledialog
import json
from pathlib import Path
from organizer import FileOrganizer
from themes import THEMES

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro File Organizer")
        self.root.geometry("600x700") # Increased height slightly

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

        # Bind Shortcuts
        self.root.bind('<Return>', self.start_thread)
        self.root.bind('<Escape>', lambda e: self.stop_process())

        # 1. Folder Selection Area
        frame_top = tk.Frame(root, pady=10)
        frame_top.pack(fill="x", padx=10)

        self.lbl_path = tk.Label(frame_top, text="No folder selected", anchor="w", relief="sunken")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ToolTip(self.lbl_path, "Selected folder path")

        btn_browse = tk.Button(frame_top, text="Browse Folder", command=self.browse_folder)
        btn_browse.pack(side="right")
        ToolTip(btn_browse, "Select a folder to organize")

        # Recent Folders Combobox
        self.var_recent = tk.StringVar()
        self.opt_recent = ttk.Combobox(frame_top, textvariable=self.var_recent, values=self.recent_folders, state="readonly", width=3)
        self.opt_recent.set("...")
        self.opt_recent.pack(side="right", padx=5)
        self.opt_recent.bind("<<ComboboxSelected>>", self.on_recent_select)
        ToolTip(self.opt_recent, "Select from recently used folders")

        # Options Frame
        frame_options = tk.Frame(root, pady=5)
        frame_options.pack(fill="x", padx=10)

        # Recursive Checkbox
        self.var_recursive = tk.BooleanVar()
        chk_rec = tk.Checkbutton(frame_options, text="Include Subfolders", variable=self.var_recursive)
        chk_rec.pack(side="left", padx=5)
        ToolTip(chk_rec, "Search and organize files in subdirectories")

        # Date Sorting Checkbox
        self.var_date_sort = tk.BooleanVar()
        chk_date = tk.Checkbutton(frame_options, text="Sort by Date", variable=self.var_date_sort)
        chk_date.pack(side="left", padx=5)
        ToolTip(chk_date, "Organize files into Year/Month folders")

        # Delete Empty Folders Checkbox
        self.var_del_empty = tk.BooleanVar()
        chk_del = tk.Checkbutton(frame_options, text="Delete Empty Folders", variable=self.var_del_empty)
        chk_del.pack(side="left", padx=5)
        ToolTip(chk_del, "Remove empty folders after moving files")

        # Dry Run Checkbox
        self.var_dry_run = tk.BooleanVar()
        chk_dry = tk.Checkbutton(frame_options, text="Dry Run (Simulate)", variable=self.var_dry_run)
        chk_dry.pack(side="left", padx=5)
        ToolTip(chk_dry, "Simulate the organization without moving files")

        # Theme Toggle
        self.btn_theme = tk.Button(frame_options, text=f"Theme: {self.current_theme.title()}", command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)
        ToolTip(self.btn_theme, "Toggle between Light and Dark themes")

        # Settings Button
        self.btn_settings = tk.Button(frame_options, text="Settings", command=self.open_settings)
        self.btn_settings.pack(side="right", padx=5)
        ToolTip(self.btn_settings, "Configure file categories and extensions")

        # 2. Action Buttons
        frame_actions = tk.Frame(root)
        frame_actions.pack(fill="x", padx=10, pady=5)

        self.btn_preview = tk.Button(frame_actions, text="Preview", command=self.run_preview, state="disabled", height=2)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ToolTip(self.btn_preview, "Preview the changes (Dry Run)")

        self.btn_run = tk.Button(frame_actions, text="Start Organizing", command=self.start_thread, state="disabled", height=2)
        self.btn_run.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ToolTip(self.btn_run, "Start the organization process")

        # Undo Button
        self.btn_undo = tk.Button(root, text="Undo Last Run", command=self.undo_changes, state="disabled")
        self.btn_undo.pack(fill="x", padx=10, pady=5)
        ToolTip(self.btn_undo, "Revert the last organization operation")

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
        self.btn_theme.config(text=f"Theme: {self.current_theme.title()}")
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
             self.btn_preview.config(bg=c["btn_bg"], fg=c["btn_fg"]) # Standard button color
        else:
             self.btn_run.config(bg=c["disabled_bg"], fg=c["disabled_fg"])
             self.btn_preview.config(bg=c["disabled_bg"], fg=c["disabled_fg"])

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
            self.enable_buttons()
            self.log("Selected (Recent): " + str(self.selected_path))
            # Move to top of recent list
            self.add_recent(self.selected_path)
            self.opt_recent.set("...") # Reset text to dot dot dot

    def enable_buttons(self):
        self.btn_run.config(state="normal", bg=self.colors["success_bg"], fg=self.colors["success_fg"])
        self.btn_preview.config(state="normal", bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_path = Path(folder_selected)
            self.lbl_path.config(text=str(self.selected_path))
            self.enable_buttons()
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

        # Add ToolTips for Settings
        ToolTip(btn_add, "Create a new category")
        ToolTip(btn_del, "Remove selected category")
        ToolTip(btn_save, "Save changes to config.json")


        # Logic
        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            listbox.insert(tk.END, cat)

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

        def save_config():
            # Force save current selection first
            if self.last_selected_index is not None:
                 on_select_improved(None)

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
                on_select_improved(None)

        def delete_category():
            selection = listbox.curselection()
            if selection:
                cat = listbox.get(selection[0])
                if messagebox.askyesno("Confirm", f"Delete category '{cat}'?"):
                    del self.organizer.directories[cat]
                    listbox.delete(selection[0])
                    txt_exts.delete("1.0", tk.END)
                    self.last_selected_index = None

        btn_save.config(command=save_config)
        btn_add.config(command=add_category)
        btn_del.config(command=delete_category)


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

    def start_thread(self, event=None):
        """Run logic in a separate thread so the GUI doesn't freeze."""
        if not self.selected_path:
             messagebox.showwarning("Warning", "Please select a folder first.")
             return

        if not self.var_dry_run.get():
             if not messagebox.askyesno("Confirm", "Are you sure you want to organize files? This will move files to new directories."):
                 return

        self.run_organization(dry_run_override=None)

    def run_preview(self):
        """Runs a dry run (preview)."""
        self.run_organization(dry_run_override=True)

    def run_organization(self, dry_run_override=None):
        self.is_running = True
        self.btn_run.config(text="Stop", command=self.stop_process, bg=self.colors["undo_bg"], fg=self.colors["undo_fg"])
        self.btn_preview.config(state="disabled")
        self.btn_undo.config(state="disabled")
        self.progress["value"] = 0

        threading.Thread(target=self.organize_files, args=(dry_run_override,), daemon=True).start()

    def stop_process(self):
        """Signals the running thread to stop."""
        if hasattr(self, 'is_running') and self.is_running:
            self.is_running = False
            self.btn_run.config(state="disabled", text="Stopping...")

    def organize_files(self, dry_run_override=None):
        if not self.selected_path:
            return

        dry_run = dry_run_override if dry_run_override is not None else self.var_dry_run.get()

        stats = self.organizer.organize_files(
            source_path=self.selected_path,
            recursive=self.var_recursive.get(),
            date_sort=self.var_date_sort.get(),
            del_empty=self.var_del_empty.get(),
            dry_run=dry_run,
            progress_callback=self.update_progress,
            log_callback=self.log,
            check_stop=lambda: not self.is_running
        )

        msg = f"Organization {'stopped' if not self.is_running else 'complete'}!\n{'Would move' if dry_run else 'Moved'} {stats['moved']} files."

        # Show message box in main thread
        self.root.after(0, lambda: messagebox.showinfo("Result", msg))

        # Enable Undo if we moved anything and it wasn't a dry run
        if stats['moved'] > 0 and not dry_run:
            self.root.after(0, lambda: self.btn_undo.config(state="normal"))
        
        # Reset run button
        def reset_ui():
            self.btn_run.config(state="normal", text="Start Organizing", command=self.start_thread, bg=self.colors["success_bg"], fg=self.colors["success_fg"])
            self.btn_preview.config(state="normal", bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])

        self.root.after(0, reset_ui)

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
