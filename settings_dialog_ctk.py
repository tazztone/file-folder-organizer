import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk # For Listbox/Text if needed, or replacements
from ui_utils import ToolTip

class SettingsDialog:
    def __init__(self, parent, organizer, theme_name=None):
        self.parent = parent
        self.organizer = organizer
        self.last_selected_cat = None

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Configuration")
        self.window.geometry("700x550")

        # Ensure it stays on top
        self.window.transient(parent)
        self.window.grab_set()

        self.tabview = ctk.CTkTabview(self.window)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tabview.add("Categories")
        self.tabview.add("Exclusions")
        self.tabview.add("Profiles")

        self._setup_categories_tab()
        self._setup_exclusions_tab()
        self._setup_profiles_tab()

        # Bottom Buttons
        self.btn_save = ctk.CTkButton(self.window, text="Save & Close", command=self.save_config, fg_color="green", hover_color="darkgreen")
        self.btn_save.pack(side="bottom", pady=20)
        ToolTip(self.btn_save, "Save changes to config.json and close")

    def _setup_categories_tab(self):
        tab = self.tabview.tab("Categories")
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Left: Category List (Using CTkScrollableFrame with Buttons effectively acting as list items)
        # Actually, using a standard Listbox is often easier for simple lists,
        # but let's try to be "pure" CTk or use a ScrollableFrame with selectable buttons.
        # For simplicity and robustness, I'll use CTkScrollableFrame.

        self.frame_list = ctk.CTkScrollableFrame(tab, width=200, label_text="Categories")
        self.frame_list.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right: Edit area
        self.frame_edit = ctk.CTkFrame(tab)
        self.frame_edit.grid(row=0, column=1, sticky="nsew")

        self.lbl_exts = ctk.CTkLabel(self.frame_edit, text="Extensions (comma separated):", anchor="w")
        self.lbl_exts.pack(fill="x", padx=10, pady=(10, 5))

        self.txt_exts = ctk.CTkTextbox(self.frame_edit, height=200)
        self.txt_exts.pack(fill="both", expand=True, padx=10, pady=5)

        # Action Buttons
        frame_btns = ctk.CTkFrame(self.frame_edit, fg_color="transparent")
        frame_btns.pack(fill="x", padx=10, pady=10)

        self.btn_add = ctk.CTkButton(frame_btns, text="Add Category", command=self.add_category, width=100)
        self.btn_add.pack(side="left", padx=(0, 5))

        self.btn_del = ctk.CTkButton(frame_btns, text="Delete Category", command=self.delete_category, width=100, fg_color="red", hover_color="darkred")
        self.btn_del.pack(side="left", padx=(5, 0))

        self.cat_buttons = {} # Map category name to button widget
        self.selected_cat_btn = None

        self._populate_cat_list()

    def _setup_exclusions_tab(self):
        tab = self.tabview.tab("Exclusions")

        lbl_exts = ctk.CTkLabel(tab, text="Excluded Extensions (e.g., .tmp, .log) - Comma separated:", anchor="w")
        lbl_exts.pack(fill="x", padx=10, pady=(10, 5))

        self.txt_excl_exts = ctk.CTkTextbox(tab, height=100)
        self.txt_excl_exts.pack(fill="x", padx=10, pady=5)
        self.txt_excl_exts.insert("1.0", ", ".join(self.organizer.excluded_extensions))

        lbl_folders = ctk.CTkLabel(tab, text="Excluded Folder Names (e.g., node_modules, .git) - Comma separated:", anchor="w")
        lbl_folders.pack(fill="x", padx=10, pady=(10, 5))

        self.txt_excl_folders = ctk.CTkTextbox(tab, height=100)
        self.txt_excl_folders.pack(fill="x", padx=10, pady=5)
        self.txt_excl_folders.insert("1.0", ", ".join(self.organizer.excluded_folders))

        # ML Threshold
        lbl_ml = ctk.CTkLabel(tab, text="AI Confidence Threshold (0.0 - 1.0):", anchor="w")
        lbl_ml.pack(fill="x", padx=10, pady=(20, 5))

        self.slider_ml = ctk.CTkSlider(tab, from_=0.0, to=1.0, number_of_steps=20)
        self.slider_ml.pack(fill="x", padx=10, pady=5)

        current_threshold = getattr(self.organizer, "ml_confidence", 0.3)
        self.slider_ml.set(current_threshold)

        self.lbl_ml_val = ctk.CTkLabel(tab, text=f"{current_threshold:.2f}")
        self.lbl_ml_val.pack()

        self.slider_ml.configure(command=lambda v: self.lbl_ml_val.configure(text=f"{v:.2f}"))

    def _setup_profiles_tab(self):
        tab = self.tabview.tab("Profiles")

        lbl_info = ctk.CTkLabel(tab, text="Import and Export Configuration Profiles")
        lbl_info.pack(pady=30)

        btn_export = ctk.CTkButton(tab, text="Export Configuration", command=self.export_profile)
        btn_export.pack(fill="x", padx=80, pady=10)

        btn_import = ctk.CTkButton(tab, text="Import Configuration", command=self.import_profile)
        btn_import.pack(fill="x", padx=80, pady=10)

    def _populate_cat_list(self):
        # Clear existing buttons
        for btn in self.cat_buttons.values():
            btn.destroy()
        self.cat_buttons.clear()

        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            btn = ctk.CTkButton(self.frame_list, text=cat, fg_color="transparent",
                                border_width=1, border_color="gray",
                                text_color=("black", "white"),
                                anchor="w",
                                command=lambda c=cat: self.on_cat_select(c))
            btn.pack(fill="x", pady=2)
            self.cat_buttons[cat] = btn

        # Select first if available
        if current_cats:
            self.on_cat_select(current_cats[0])

    def save_pending_cat_changes(self):
        if self.last_selected_cat:
            cat = self.last_selected_cat
            if cat in self.organizer.directories:
                raw_exts = self.txt_exts.get("1.0", "end").strip()
                ext_list = [e.strip() for e in raw_exts.split(',') if e.strip()]
                self.organizer.directories[cat] = ext_list

    def on_cat_select(self, cat_name):
        self.save_pending_cat_changes()

        # Update UI selection state
        if self.selected_cat_btn:
            self.selected_cat_btn.configure(fg_color="transparent")

        if cat_name in self.cat_buttons:
            self.selected_cat_btn = self.cat_buttons[cat_name]
            # Use theme color for selection
            self.selected_cat_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])

        self.last_selected_cat = cat_name
        exts = self.organizer.directories.get(cat_name, [])
        self.txt_exts.delete("1.0", "end")
        self.txt_exts.insert("end", ", ".join(exts))

    def add_category(self):
        dialog = ctk.CTkInputDialog(text="Enter category name:", title="New Category")
        new_cat = dialog.get_input()

        if new_cat:
            new_cat = new_cat.strip()
            if not new_cat:
                 messagebox.showerror("Error", "Category name cannot be empty.")
                 return
            if new_cat in self.organizer.directories:
                 messagebox.showerror("Error", "Category already exists.")
                 return

            self.organizer.directories[new_cat] = []

            # Refresh list
            self._populate_cat_list()
            self.on_cat_select(new_cat)

    def delete_category(self):
        if not self.last_selected_cat:
            return

        cat = self.last_selected_cat
        if messagebox.askyesno("Confirm", f"Delete category '{cat}'?"):
            del self.organizer.directories[cat]
            self.last_selected_cat = None
            self._populate_cat_list()
            self.txt_exts.delete("1.0", "end")

    def export_profile(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
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
                    self._populate_cat_list()
                    self.txt_excl_exts.delete("1.0", "end")
                    self.txt_excl_exts.insert("1.0", ", ".join(self.organizer.excluded_extensions))
                    self.txt_excl_folders.delete("1.0", "end")
                    self.txt_excl_folders.insert("1.0", ", ".join(self.organizer.excluded_folders))
                    messagebox.showinfo("Success", "Profile imported successfully.")
                else:
                    messagebox.showerror("Error", "Failed to import profile.")

    def _apply_exclusions(self):
        raw_exts = self.txt_excl_exts.get("1.0", "end").strip()
        self.organizer.excluded_extensions = {e.strip() for e in raw_exts.split(',') if e.strip()}

        raw_folders = self.txt_excl_folders.get("1.0", "end").strip()
        self.organizer.excluded_folders = {f.strip() for f in raw_folders.split(',') if f.strip()}

        # Save ML Threshold
        if hasattr(self, 'slider_ml'):
             self.organizer.ml_confidence = self.slider_ml.get()

    def save_config(self):
        self.save_pending_cat_changes()
        self._apply_exclusions()

        errors = self.organizer.validate_config()
        if errors:
            msg = "Configuration has errors:\n\n" + "\n".join(errors)
            messagebox.showerror("Invalid Configuration", msg)
            return

        if self.organizer.save_config():
            self.organizer.extension_map = self.organizer._build_extension_map()
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to save configuration.")
