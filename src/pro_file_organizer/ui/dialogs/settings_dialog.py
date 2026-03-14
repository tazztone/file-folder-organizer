from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget, organizer):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.resize(700, 550)
        self.organizer = organizer
        self.last_selected_cat = None
        self.cat_buttons: dict[str, QPushButton] = {}  # Map category name to button widget
        self.selected_cat_btn: Optional[QPushButton] = None

        self._setup_ui()
        self._populate_cat_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self._setup_categories_tab()
        self._setup_exclusions_tab()
        self._setup_profiles_tab()

        # Bottom Buttons
        self.btn_save = QPushButton("Save & Close")
        self.btn_save.setObjectName("success")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setToolTip("Save changes to config.json and close")
        self.btn_save.clicked.connect(self.save_config)
        layout.addWidget(self.btn_save)

    def _setup_categories_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "Categories")
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(10)

        # Left: Category List
        self.scroll_list = QScrollArea()
        self.scroll_list.setFixedWidth(200)
        self.scroll_list.setWidgetResizable(True)
        self.scroll_list.setObjectName("card")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()

        self.scroll_list.setWidget(self.list_container)
        tab_layout.addWidget(self.scroll_list)

        # Right: Edit area
        self.edit_frame = QFrame()
        self.edit_frame.setObjectName("card")
        edit_layout = QVBoxLayout(self.edit_frame)
        tab_layout.addWidget(self.edit_frame, 1)

        edit_layout.addWidget(QLabel("Extensions (comma separated):"))

        self.txt_exts = QTextEdit()
        edit_layout.addWidget(self.txt_exts)

        # Action Buttons
        btns_layout = QHBoxLayout()
        edit_layout.addLayout(btns_layout)

        self.btn_add_cat = QPushButton("Add Category")
        self.btn_add_cat.clicked.connect(self.add_category)
        btns_layout.addWidget(self.btn_add_cat)

        self.btn_del_cat = QPushButton("Delete Category")
        self.btn_del_cat.setObjectName("danger")
        self.btn_del_cat.clicked.connect(self.delete_category)
        btns_layout.addWidget(self.btn_del_cat)

    def _setup_exclusions_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "Exclusions")
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        tab_layout.setSpacing(10)

        tab_layout.addWidget(QLabel("Excluded Extensions (e.g., .tmp, .log) - Comma separated:"))
        self.txt_excl_exts = QTextEdit()
        self.txt_excl_exts.setFixedHeight(80)
        self.txt_excl_exts.setPlainText(", ".join(self.organizer.excluded_extensions))
        tab_layout.addWidget(self.txt_excl_exts)

        tab_layout.addWidget(QLabel("Excluded Folder Names (e.g., node_modules, .git) - Comma separated:"))
        self.txt_excl_folders = QTextEdit()
        self.txt_excl_folders.setFixedHeight(80)
        self.txt_excl_folders.setPlainText(", ".join(self.organizer.excluded_folders))
        tab_layout.addWidget(self.txt_excl_folders)

        # ML Threshold
        tab_layout.addWidget(QLabel("AI Confidence Threshold (0.0 - 1.0):"))
        ml_layout = QHBoxLayout()
        tab_layout.addLayout(ml_layout)

        self.slider_ml = QSlider(Qt.Orientation.Horizontal)
        self.slider_ml.setRange(0, 100)
        current_threshold = getattr(self.organizer, "ml_confidence", 0.3)
        self.slider_ml.setValue(int(current_threshold * 100))
        ml_layout.addWidget(self.slider_ml)

        self.lbl_ml_val = QLabel(f"{current_threshold:.2f}")
        ml_layout.addWidget(self.lbl_ml_val)
        self.slider_ml.valueChanged.connect(lambda v: self.lbl_ml_val.setText(f"{v / 100:.2f}"))

        # Undo Stack Size
        tab_layout.addWidget(QLabel("Max Undo Stack Size:"))
        undo_layout = QHBoxLayout()
        tab_layout.addLayout(undo_layout)

        self.slider_undo = QSlider(Qt.Orientation.Horizontal)
        self.slider_undo.setRange(1, 50)
        current_undo = getattr(self.organizer, "max_undo_stack", 5)
        self.slider_undo.setValue(int(current_undo))
        undo_layout.addWidget(self.slider_undo)

        self.lbl_undo_val = QLabel(str(int(current_undo)))
        undo_layout.addWidget(self.lbl_undo_val)
        self.slider_undo.valueChanged.connect(lambda v: self.lbl_undo_val.setText(str(v)))

        tab_layout.addStretch()

    def _setup_profiles_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, "Profiles")
        tab_layout = QVBoxLayout(tab)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tab_layout.setSpacing(20)

        tab_layout.addWidget(QLabel("Import and Export Configuration Profiles"))

        btn_export = QPushButton("Export Configuration")
        btn_export.setFixedWidth(250)
        btn_export.clicked.connect(self.export_profile)
        tab_layout.addWidget(btn_export)

        btn_import = QPushButton("Import Configuration")
        btn_import.setFixedWidth(250)
        btn_import.clicked.connect(self.import_profile)
        tab_layout.addWidget(btn_import)

    def _populate_cat_list(self):
        # Clear existing buttons
        count = self.list_layout.count()
        for _ in range(count - 1):
            item = self.list_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
        self.cat_buttons.clear()

        current_cats = list(self.organizer.directories.keys())
        for cat in current_cats:
            btn = QPushButton(cat)
            btn.setObjectName("secondary")
            btn.setStyleSheet("text-align: left; padding-left: 10px;")
            btn.clicked.connect(lambda checked=False, c=cat: self.on_cat_select(c))
            self.list_layout.insertWidget(self.list_layout.count() - 1, btn)
            self.cat_buttons[cat] = btn

        if current_cats:
            self.on_cat_select(current_cats[0])

    def save_pending_cat_changes(self):
        if self.last_selected_cat:
            cat = self.last_selected_cat
            if cat in self.organizer.directories:
                raw_exts = self.txt_exts.toPlainText().strip()
                ext_list = [e.strip() for e in raw_exts.split(",") if e.strip()]
                self.organizer.directories[cat] = ext_list

    def on_cat_select(self, cat_name):
        self.save_pending_cat_changes()

        if self.selected_cat_btn:
            self.selected_cat_btn.setProperty("active", False)
            self.selected_cat_btn.style().unpolish(self.selected_cat_btn)
            self.selected_cat_btn.style().polish(self.selected_cat_btn)

        if cat_name in self.cat_buttons:
            self.selected_cat_btn = self.cat_buttons[cat_name]
            self.selected_cat_btn.setProperty("active", True)
            self.selected_cat_btn.style().unpolish(self.selected_cat_btn)
            self.selected_cat_btn.style().polish(self.selected_cat_btn)

        self.last_selected_cat = cat_name
        exts = self.organizer.directories.get(cat_name, [])
        self.txt_exts.setPlainText(", ".join(exts))

    def add_category(self):
        name, ok = QInputDialog.getText(self, "New Category", "Enter category name:")
        if ok and name.strip():
            new_cat = name.strip()
            if new_cat in self.organizer.directories:
                QMessageBox.critical(self, "Error", "Category already exists.")
                return

            self.organizer.directories[new_cat] = []
            self._populate_cat_list()
            self.on_cat_select(new_cat)

    def delete_category(self):
        if not self.last_selected_cat:
            return

        cat = self.last_selected_cat
        res = QMessageBox.question(
            self, "Confirm", f"Delete category '{cat}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            del self.organizer.directories[cat]
            self.last_selected_cat = None
            self._populate_cat_list()
            self.txt_exts.clear()

    def export_profile(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Configuration", "", "JSON Files (*.json)")
        if path:
            self._apply_exclusions()
            self.save_pending_cat_changes()

            if self.organizer.export_config_file(path):
                QMessageBox.information(self, "Success", "Profile exported successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to export profile.")

    def import_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Configuration", "", "JSON Files (*.json)")
        if path:
            res = QMessageBox.question(
                self,
                "Confirm",
                "Importing will overwrite current settings. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res == QMessageBox.StandardButton.Yes:
                if self.organizer.import_config_file(path):
                    self._populate_cat_list()
                    self.txt_excl_exts.setPlainText(", ".join(self.organizer.excluded_extensions))
                    self.txt_excl_folders.setPlainText(", ".join(self.organizer.excluded_folders))
                    QMessageBox.information(self, "Success", "Profile imported successfully.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to import profile.")

    def _apply_exclusions(self):
        raw_exts = self.txt_excl_exts.toPlainText().strip()
        self.organizer.excluded_extensions = {e.strip() for e in raw_exts.split(",") if e.strip()}

        raw_folders = self.txt_excl_folders.toPlainText().strip()
        self.organizer.excluded_folders = {f.strip() for f in raw_folders.split(",") if f.strip()}

        self.organizer.ml_confidence = self.slider_ml.value() / 100.0
        self.organizer.max_undo_stack = self.slider_undo.value()

    def save_config(self):
        self.save_pending_cat_changes()
        self._apply_exclusions()

        errors = self.organizer.validate_config()
        if errors:
            msg = "Configuration has errors:\n\n" + "\n".join(errors)
            QMessageBox.critical(self, "Invalid Configuration", msg)
            return

        if self.organizer.save_config():
            self.organizer.extension_map = self.organizer._build_extension_map()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save configuration.")
