import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from ui_utils import ToolTip

class SettingsDialog:
    def __init__(self, parent, organizer, colors):
        self.parent = parent
        self.organizer = organizer
        self.colors = colors
        self.last_selected_cat = None

        self.window = tk.Toplevel(parent)
        self.window.title("Configuration")
        self.window.geometry("600x500")
        self.window.config(bg=colors["bg"])

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Categories
        self.tab_categories = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(self.tab_categories, text="Categories")
        self._setup_categories_tab()

        # Tab 2: Exclusions
        self.tab_exclusions = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(self.tab_exclusions, text="Exclusions")
        self._setup_exclusions_tab()

        # Tab 3: Profiles
        self.tab_profiles = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(self.tab_profiles, text="Profiles")
        self._setup_profiles_tab()

        # Bottom Buttons
        frame_bottom = tk.Frame(self.window, bg=colors["bg"], pady=10)
        frame_bottom.pack(fill="x", side="bottom")

        btn_save = tk.Button(frame_bottom, text="Save & Close", bg=colors["success_bg"], fg=colors["success_fg"], command=self.save_config)
        btn_save.pack(side="right", padx=10)
        ToolTip(btn_save, "Save changes to config.json and close")

    def _setup_categories_tab(self):
        c = self.colors
        frame = self.tab_categories

        # Left: List of categories
        frame_list = tk.Frame(frame, bg=c["bg"])
        frame_list.pack(side="left", fill="y", padx=10, pady=10)

        lbl_cats = tk.Label(frame_list, text="Categories", bg=c["bg"], fg=c["fg"])
        lbl_cats.pack(anchor="w")

        self.listbox = tk.Listbox(frame_list, bg=c["entry_bg"], fg=c["entry_fg"], selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_cat_select)

        # Right: Edit area
        frame_edit = tk.Frame(frame, bg=c["bg"])
        frame_edit.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        lbl_exts = tk.Label(frame_edit, text="Extensions (comma separated)", bg=c["bg"], fg=c["fg"])
        lbl_exts.pack(anchor="w")

        self.txt_exts = tk.Text(frame_edit, height=10, bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"])
        self.txt_exts.pack(fill="x")

        # Buttons
        frame_btns = tk.Frame(frame_edit, bg=c["bg"], pady=10)
        frame_btns.pack(fill="x")

        btn_add = tk.Button(frame_btns, text="Add Category", bg=c["btn_bg"], fg=c["btn_fg"], command=self.add_category)
        btn_add.pack(side="left", padx=5)

        btn_del = tk.Button(frame_btns, text="Delete Category", bg=c["btn_bg"], fg=c["btn_fg"], command=self.delete_category)
        btn_del.pack(side="left", padx=5)

        self._populate_cat_list()

    def _setup_exclusions_tab(self):
        c = self.colors
        frame = self.tab_exclusions

        # Excluded Extensions
        lbl_exts = tk.Label(frame, text="Excluded Extensions (e.g., .tmp, .log) - Comma separated", bg=c["bg"], fg=c["fg"])
        lbl_exts.pack(anchor="w", padx=10, pady=(10, 0))

        self.txt_excl_exts = tk.Text(frame, height=5, bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"])
        self.txt_excl_exts.pack(fill="x", padx=10, pady=5)
        self.txt_excl_exts.insert("1.0", ", ".join(self.organizer.excluded_extensions))

        # Excluded Folders
        lbl_folders = tk.Label(frame, text="Excluded Folder Names (e.g., node_modules, .git) - Comma separated", bg=c["bg"], fg=c["fg"])
        lbl_folders.pack(anchor="w", padx=10, pady=(10, 0))

        self.txt_excl_folders = tk.Text(frame, height=5, bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"])
        self.txt_excl_folders.pack(fill="x", padx=10, pady=5)
        self.txt_excl_folders.insert("1.0", ", ".join(self.organizer.excluded_folders))

    def _setup_profiles_tab(self):
        c = self.colors
        frame = self.tab_profiles

        lbl_info = tk.Label(frame, text="Import and Export Configuration Profiles", bg=c["bg"], fg=c["fg"])
        lbl_info.pack(pady=20)

        btn_export = tk.Button(frame, text="Export Configuration", command=self.export_profile, bg=c["btn_bg"], fg=c["btn_fg"], height=2)
        btn_export.pack(fill="x", padx=50, pady=10)

        btn_import = tk.Button(frame, text="Import Configuration", command=self.import_profile, bg=c["btn_bg"], fg=c["btn_fg"], height=2)
        btn_import.pack(fill="x", padx=50, pady=10)

    def _populate_cat_list(self):
        self.listbox.delete(0, tk.END)
        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            self.listbox.insert(tk.END, cat)

    def save_pending_cat_changes(self):
        if self.last_selected_cat:
            cat = self.last_selected_cat
            if cat in self.organizer.directories:
                raw_exts = self.txt_exts.get("1.0", tk.END).strip()
                ext_list = [e.strip() for e in raw_exts.split(',') if e.strip()]
                self.organizer.directories[cat] = ext_list

    def on_cat_select(self, event):
        self.save_pending_cat_changes()
        selection = self.listbox.curselection()
        if selection:
            cat = self.listbox.get(selection[0])
            self.last_selected_cat = cat
            exts = self.organizer.directories.get(cat, [])
            self.txt_exts.delete("1.0", tk.END)
            self.txt_exts.insert(tk.END, ", ".join(exts))
        else:
            self.last_selected_cat = None
            self.txt_exts.delete("1.0", tk.END)

    def add_category(self):
        new_cat = simpledialog.askstring("New Category", "Enter category name:", parent=self.window)
        if new_cat:
            new_cat = new_cat.strip()
            if not new_cat:
                 messagebox.showerror("Error", "Category name cannot be empty.")
                 return
            if new_cat in self.organizer.directories:
                 messagebox.showerror("Error", "Category already exists.")
                 return

            self.organizer.directories[new_cat] = []
            self.listbox.insert(tk.END, new_cat)
            idx = self.listbox.size() - 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.on_cat_select(None)

    def delete_category(self):
        selection = self.listbox.curselection()
        if selection:
            cat = self.listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete category '{cat}'?"):
                del self.organizer.directories[cat]
                self.listbox.delete(selection[0])
                self.txt_exts.delete("1.0", tk.END)
                self.last_selected_cat = None

    def export_profile(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            # We need to save current in-memory changes before export
            self._apply_exclusions()
            self.save_pending_cat_changes()

            if self.organizer.export_config_file(path):
                messagebox.showinfo("Success", "Profile exported successfully.")
            else:
                messagebox.showerror("Error", "Failed to export profile.")

    def import_profile(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            if messagebox.askyesno("Confirm", "Importing will overwrite current settings. Continue?"):
                if self.organizer.import_config_file(path):
                    # Refresh UI
                    self._populate_cat_list()
                    self.txt_exts.delete("1.0", tk.END)
                    self.txt_excl_exts.delete("1.0", tk.END)
                    self.txt_excl_exts.insert("1.0", ", ".join(self.organizer.excluded_extensions))
                    self.txt_excl_folders.delete("1.0", tk.END)
                    self.txt_excl_folders.insert("1.0", ", ".join(self.organizer.excluded_folders))
                    messagebox.showinfo("Success", "Profile imported successfully.")
                else:
                    messagebox.showerror("Error", "Failed to import profile.")

    def _apply_exclusions(self):
        # Update organizer with values from exclusion fields
        raw_exts = self.txt_excl_exts.get("1.0", tk.END).strip()
        self.organizer.excluded_extensions = {e.strip() for e in raw_exts.split(',') if e.strip()}

        raw_folders = self.txt_excl_folders.get("1.0", tk.END).strip()
        self.organizer.excluded_folders = {f.strip() for f in raw_folders.split(',') if f.strip()}

    def save_config(self):
        self.save_pending_cat_changes()
        self._apply_exclusions()

        # Validate
        errors = self.organizer.validate_config()
        if errors:
            msg = "Configuration has errors:\n\n" + "\n".join(errors)
            messagebox.showerror("Invalid Configuration", msg)
            return

        if self.organizer.save_config():
            self.organizer.extension_map = self.organizer._build_extension_map()
            messagebox.showinfo("Success", "Configuration saved!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to save configuration.")
