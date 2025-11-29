import tkinter as tk
from tkinter import messagebox, simpledialog
from ui_utils import ToolTip

class SettingsDialog:
    def __init__(self, parent, organizer, colors):
        self.parent = parent
        self.organizer = organizer
        self.colors = colors
        self.last_selected_cat = None # Track by NAME instead of index for robustness

        self.window = tk.Toplevel(parent)
        self.window.title("Configuration")
        self.window.geometry("500x400")
        self.window.config(bg=colors["bg"])

        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        c = self.colors

        # UI Layout for Settings
        # Top: List of categories
        frame_list = tk.Frame(self.window, bg=c["bg"])
        frame_list.pack(side="left", fill="y", padx=10, pady=10)

        lbl_cats = tk.Label(frame_list, text="Categories", bg=c["bg"], fg=c["fg"])
        lbl_cats.pack(anchor="w")

        self.listbox = tk.Listbox(frame_list, bg=c["entry_bg"], fg=c["entry_fg"], selectbackground=c["select_bg"], selectforeground=c["select_fg"])
        self.listbox.pack(fill="y", expand=True)

        # Right: Edit area
        frame_edit = tk.Frame(self.window, bg=c["bg"])
        frame_edit.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        lbl_exts = tk.Label(frame_edit, text="Extensions (comma separated)", bg=c["bg"], fg=c["fg"])
        lbl_exts.pack(anchor="w")

        self.txt_exts = tk.Text(frame_edit, height=10, bg=c["entry_bg"], fg=c["entry_fg"], insertbackground=c["fg"])
        self.txt_exts.pack(fill="x")

        # Buttons for Add/Delete Category
        frame_btns = tk.Frame(frame_edit, bg=c["bg"], pady=10)
        frame_btns.pack(fill="x")

        btn_add = tk.Button(frame_btns, text="Add Category", bg=c["btn_bg"], fg=c["btn_fg"], command=self.add_category)
        btn_add.pack(side="left", padx=5)

        btn_del = tk.Button(frame_btns, text="Delete Category", bg=c["btn_bg"], fg=c["btn_fg"], command=self.delete_category)
        btn_del.pack(side="left", padx=5)

        btn_save = tk.Button(frame_edit, text="Save Configuration", bg=c["success_bg"], fg=c["success_fg"], command=self.save_config)
        btn_save.pack(side="bottom", pady=10)

        # Add ToolTips for Settings
        ToolTip(btn_add, "Create a new category")
        ToolTip(btn_del, "Remove selected category")
        ToolTip(btn_save, "Save changes to config.json")

        self.listbox.bind('<<ListboxSelect>>', self.on_select)

    def _populate_list(self):
        self.listbox.delete(0, tk.END)
        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            self.listbox.insert(tk.END, cat)

    def save_pending_changes(self):
        """Saves changes from text box to memory for the PREVIOUS category."""
        if self.last_selected_cat:
            cat = self.last_selected_cat
            if cat in self.organizer.directories:
                raw_exts = self.txt_exts.get("1.0", tk.END).strip()
                # Split and clean
                ext_list = [e.strip() for e in raw_exts.split(',') if e.strip()]
                self.organizer.directories[cat] = ext_list

    def on_select(self, event):
        # 1. Save changes for the category we are LEAVING
        self.save_pending_changes()

        # 2. Load the new category
        selection = self.listbox.curselection()
        if selection:
            cat = self.listbox.get(selection[0])
            self.last_selected_cat = cat # Update tracker

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

            # Select the new item
            idx = self.listbox.size() - 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.on_select(None) # Trigger load

    def delete_category(self):
        selection = self.listbox.curselection()
        if selection:
            cat = self.listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete category '{cat}'?"):
                del self.organizer.directories[cat]
                self.listbox.delete(selection[0])
                self.txt_exts.delete("1.0", tk.END)
                self.last_selected_cat = None

    def save_config(self):
        # Save pending edits first
        self.save_pending_changes()

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
