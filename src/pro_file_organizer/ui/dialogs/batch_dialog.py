import json
import threading
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...core.constants import DEFAULT_BATCH_CONFIG_FILE
from ..themes.themes import COLORS, RADII


class BatchSignals(QObject):
    status_updated = Signal(int, str)
    progress_updated = Signal(float)
    finished = Signal()


class BatchDialog(QDialog):
    def __init__(self, parent: QWidget, organizer, on_complete_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.setWindowTitle("Batch Organization")
        self.resize(800, 600)
        self.organizer = organizer
        self.on_complete_callback = on_complete_callback

        self.batch_folders: list[dict] = []
        self._load_batch_config()

        self.signals = BatchSignals()
        self._setup_ui()

        self.signals.status_updated.connect(self._update_row_status)
        self.signals.progress_updated.connect(self.progress.setValue)
        self.signals.finished.connect(self._on_batch_finished)
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Toolbar
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)

        self.btn_add = QPushButton("Add Folder")
        self.btn_add.clicked.connect(self.add_folder)
        toolbar.addWidget(self.btn_add)

        toolbar.addStretch()

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self.clear_all)
        toolbar.addWidget(self.btn_clear)

        # Header
        header_frame = QFrame()
        header_frame.setFixedHeight(40)
        header_frame.setStyleSheet(f"background-color: {COLORS['bg_sidebar']}; border-radius: 0px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(header_frame)

        lbl_path = QLabel("Folder Path")
        lbl_path.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(lbl_path, 1)

        lbl_sets = QLabel("Settings")
        lbl_sets.setFixedWidth(150)
        lbl_sets.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sets.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(lbl_sets)

        lbl_status = QLabel("Status")
        lbl_status.setFixedWidth(100)
        lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_status.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(lbl_status)

        lbl_action = QLabel("Action")
        lbl_action.setFixedWidth(80)
        lbl_action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_action.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(lbl_action)

        # List Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: {RADII['standard']}px;")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

        # Bottom Actions
        footer = QVBoxLayout()
        layout.addLayout(footer)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        footer.addWidget(self.progress)

        self.btn_run = QPushButton("Run Batch")
        self.btn_run.setObjectName("success")
        self.btn_run.setFixedHeight(44)
        self.btn_run.clicked.connect(self.run_batch)
        footer.addWidget(self.btn_run)

    def _load_batch_config(self):
        if Path(DEFAULT_BATCH_CONFIG_FILE).exists():
            try:
                with open(DEFAULT_BATCH_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if data and isinstance(data[0], str):
                        self.batch_folders = [{"path": p, "settings": None} for p in data]
                    else:
                        self.batch_folders = data
            except Exception:
                self.batch_folders = []

    def _save_batch_config(self):
        try:
            with open(DEFAULT_BATCH_CONFIG_FILE, "w") as f:
                json.dump(self.batch_folders, f, indent=4)
        except Exception:
            pass

    def _refresh_list(self):
        # Clear existing rows (except the stretch at the end)
        count = self.list_layout.count()
        for _ in range(count - 1):
            item = self.list_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        for i, folder_item in enumerate(self.batch_folders):
            self._create_row(i, folder_item)

    def _create_row(self, index, item):
        row_frame = QFrame()
        row_frame.setFixedHeight(50)
        row_frame.setStyleSheet(f"background-color: {COLORS['bg_main']}; border-radius: {RADII['card']}px;")
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(10, 5, 10, 5)

        # Path
        lbl_path = QLabel(item["path"])
        lbl_path.setToolTip(item["path"])
        row_layout.addWidget(lbl_path, 1)

        # Settings
        settings_str = "Default"
        if item.get("settings"):
            s = item["settings"]
            parts = []
            if s.get("recursive"): parts.append("Rec")
            if s.get("date_sort"): parts.append("Date")
            if s.get("del_empty"): parts.append("Del")
            if s.get("dry_run"): parts.append("Dry")
            settings_str = ",".join(parts) if parts else "Custom"

        lbl_sets = QLabel(settings_str)
        lbl_sets.setFixedWidth(150)
        lbl_sets.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(lbl_sets)

        # Status
        status = item.get("last_status", "Pending")
        lbl_status = QLabel(status)
        lbl_status.setFixedWidth(100)
        lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(lbl_status)
        item["status_label"] = lbl_status

        # Config Button
        btn_conf = QPushButton("⚙")
        btn_conf.setFixedSize(30, 30)
        btn_conf.setObjectName("secondary")
        btn_conf.clicked.connect(lambda: self.configure_folder(index))
        row_layout.addWidget(btn_conf)

        # Remove Button
        btn_del = QPushButton("X")
        btn_del.setFixedSize(30, 30)
        btn_del.setObjectName("danger")
        btn_del.clicked.connect(lambda: self.remove_folder(index))
        row_layout.addWidget(btn_del)

        self.list_layout.insertWidget(self.list_layout.count() - 1, row_frame)

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            if not any(f["path"] == path for f in self.batch_folders):
                self.batch_folders.append({"path": path, "settings": None})
                self._save_batch_config()
                self._refresh_list()

    def remove_folder(self, index):
        if 0 <= index < len(self.batch_folders):
            del self.batch_folders[index]
            self._save_batch_config()
            self._refresh_list()

    def clear_all(self):
        res = QMessageBox.question(self, "Confirm", "Clear all folders from batch list?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            self.batch_folders = []
            self._save_batch_config()
            self._refresh_list()

    def configure_folder(self, index):
        folder_item = self.batch_folders[index]
        current_settings = folder_item.get("settings") or {
            "recursive": False,
            "date_sort": False,
            "del_empty": False,
            "dry_run": False,
        }

        d = QDialog(self)
        d.setWindowTitle("Folder Settings")
        d.setFixedSize(300, 300)
        d_layout = QVBoxLayout(d)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(10)

        chk_rec = QCheckBox("Include Subfolders")
        chk_rec.setChecked(current_settings.get("recursive", False))
        d_layout.addWidget(chk_rec)

        chk_date = QCheckBox("Sort by Date")
        chk_date.setChecked(current_settings.get("date_sort", False))
        d_layout.addWidget(chk_date)

        chk_del = QCheckBox("Delete Empty Folders")
        chk_del.setChecked(current_settings.get("del_empty", False))
        d_layout.addWidget(chk_del)

        chk_dry = QCheckBox("Dry Run")
        chk_dry.setChecked(current_settings.get("dry_run", False))
        d_layout.addWidget(chk_dry)

        def save():
            folder_item["settings"] = {
                "recursive": chk_rec.isChecked(),
                "date_sort": chk_date.isChecked(),
                "del_empty": chk_del.isChecked(),
                "dry_run": chk_dry.isChecked(),
            }
            self._save_batch_config()
            self._refresh_list()
            d.accept()

        btn_save = QPushButton("Save")
        btn_save.setObjectName("success")
        btn_save.clicked.connect(save)
        d_layout.addStretch()
        d_layout.addWidget(btn_save)

        d.exec()

    def run_batch(self):
        if not self.batch_folders:
            QMessageBox.warning(self, "Warning", "No folders to process.")
            return

        msg = f"Are you sure you want to process {len(self.batch_folders)} folders?"
        res = QMessageBox.question(self, "Confirm Batch", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res != QMessageBox.StandardButton.Yes:
            return

        self.btn_run.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.btn_clear.setEnabled(False)

        threading.Thread(target=self._process_batch, daemon=True).start()

    def _process_batch(self):
        total = len(self.batch_folders)

        for i, folder_item in enumerate(self.batch_folders):
            folder_path = folder_item["path"]
            settings = folder_item.get("settings")

            self.signals.status_updated.emit(i, "Running...")

            p = Path(folder_path)
            status_msg = ""

            if p.exists():
                try:
                    kwargs = {"recursive": False, "date_sort": False, "del_empty": False, "dry_run": False}
                    if settings:
                        kwargs.update(settings)

                    self.organizer.organize_files(p, **kwargs)
                    status_msg = "Done"
                except Exception:
                    status_msg = "Error"
            else:
                status_msg = "Not Found"

            self.signals.status_updated.emit(i, status_msg)
            self.signals.progress_updated.emit((i + 1) / total * 100)

        self.signals.finished.emit()

    def _update_row_status(self, index, status):
        if 0 <= index < len(self.batch_folders):
            item = self.batch_folders[index]
            if "status_label" in item:
                item["status_label"].setText(status)
                if status == "Done":
                    item["status_label"].setStyleSheet(f"color: {COLORS['success']};")
                elif status == "Error" or status == "Not Found":
                    item["status_label"].setStyleSheet(f"color: {COLORS['danger']};")

    def _on_batch_finished(self):
        QMessageBox.information(self, "Batch Complete", "Batch organization finished.")
        self.btn_run.setEnabled(True)
        self.btn_add.setEnabled(True)
        self.btn_clear.setEnabled(True)
        if self.on_complete_callback:
            self.on_complete_callback()
