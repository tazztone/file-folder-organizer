import os
import sys
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QLabel, QPushButton, QCheckBox, QComboBox, QSlider, 
    QProgressBar, QScrollArea, QFileDialog, QMessageBox, QGridLayout
)
from PySide6.QtGui import QPainter, QPen, QColor, QDragEnterEvent, QDropEvent, QIcon

from ..core.ml_organizer import MultimodalFileOrganizer
from ..core.organizer import FileOrganizer
from .components.ui_components import FileCard, ModelDownloadModal
from .dialogs.batch_dialog import BatchDialog
from .dialogs.settings_dialog import SettingsDialog
from .main_window_controller import MainWindowController
from .themes.themes import COLORS, FONTS, RADII, build_stylesheet, LIGHT_COLORS, DARK_COLORS, get_font_style


class DropZoneWidget(QFrame):
    dropped = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.hovered = False
        self.setObjectName("drop_zone")
        self.setFixedHeight(160)
        self.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: {RADII['standard']}px;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel("📤")
        self.lbl_icon.setStyleSheet("font-size: 48px; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_icon)

        self.lbl_text = QLabel("Drag & Drop Folder Here")
        self.lbl_text.setStyleSheet(f"{get_font_style('subtitle')} background: transparent;")
        self.lbl_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_text)

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0, 10, 0, 0)
        layout.addLayout(self.actions_layout)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = COLORS["accent"] if self.hovered else COLORS["border"]
        pen = QPen(QColor(color))
        pen.setWidth(2)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([10, 5])
        
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), RADII["standard"], RADII["standard"])

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.hovered = True
            self.update()

    def dragLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self.hovered = False
        self.update()
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.dropped.emit(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dropped.emit("__BROWSE__")


class OrganizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro File Organizer")
        self.resize(1100, 750)

        # Track results for state updates
        self.result_cards: List[FileCard] = []

        self.organizer = FileOrganizer()
        self.ml_organizer = MultimodalFileOrganizer()
        
        # Apply theme before UI setup
        theme_mode = self.organizer.get_theme_mode() or "Dark"
        self._apply_theme(theme_mode)

        self._setup_ui()
        
        self.controller = MainWindowController(self, self.organizer, self.ml_organizer)

        # Load initial state into UI
        self.update_recent_menu(self.controller.recent_folders)
        self.update_stats_display(self.controller.stats)
        
        if theme_mode and hasattr(self, "appearance_mode_menu"):
            self.appearance_mode_menu.setCurrentText(theme_mode)

    def _apply_theme(self, mode: str):
        colors = LIGHT_COLORS if mode == "Light" else DARK_COLORS
        QApplication.instance().setStyleSheet(build_stylesheet(colors))

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)
        main_layout.addWidget(self.sidebar)

        # Logo Area
        logo_layout = QHBoxLayout()
        sidebar_layout.addLayout(logo_layout)
        
        lbl_logo_icon = QLabel("📁")
        lbl_logo_icon.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(lbl_logo_icon)
        
        lbl_logo_text = QLabel("PRO ORGANIZER")
        lbl_logo_text.setStyleSheet(get_font_style("title"))
        logo_layout.addWidget(lbl_logo_text)
        logo_layout.addStretch()

        sidebar_layout.addSpacing(15)

        # AI Toggle
        ai_layout = QHBoxLayout()
        sidebar_layout.addLayout(ai_layout)
        
        self.lbl_ai = QLabel("✨ Smart AI")
        self.lbl_ai.setStyleSheet(get_font_style("label"))
        ai_layout.addWidget(self.lbl_ai)
        
        ai_layout.addStretch()
        
        self.switch_ai = QCheckBox() # Simple checkbox for now, can be styled as switch
        self.switch_ai.setFixedSize(40, 20)
        self.switch_ai.stateChanged.connect(lambda s: self.controller.toggle_ai(s == Qt.Checked))
        ai_layout.addWidget(self.switch_ai)

        # Main Buttons
        self.btn_batch = QPushButton("Batch Mode")
        self.btn_batch.setFixedHeight(40)
        self.btn_batch.clicked.connect(self.open_batch)
        sidebar_layout.addWidget(self.btn_batch)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setFixedHeight(40)
        self.btn_settings.clicked.connect(self.open_settings)
        sidebar_layout.addWidget(self.btn_settings)

        sidebar_layout.addSpacing(10)

        # Stats Bar
        self.stats_container = QVBoxLayout()
        sidebar_layout.addLayout(self.stats_container)
        
        self.lbl_stats_total = QLabel("Files: 0")
        self.lbl_stats_total.setObjectName("dimmed")
        self.lbl_stats_total.setStyleSheet(get_font_style("small"))
        self.stats_container.addWidget(self.lbl_stats_total)
        
        self.lbl_stats_last = QLabel("Last: Never")
        self.lbl_stats_last.setObjectName("dimmed")
        self.lbl_stats_last.setStyleSheet(get_font_style("small"))
        self.stats_container.addWidget(self.lbl_stats_last)

        sidebar_layout.addStretch()

        # Appearance Menu
        sidebar_layout.addWidget(QLabel("Appearance"))
        self.appearance_mode_menu = QComboBox()
        self.appearance_mode_menu.addItems(["Light", "Dark", "System"])
        self.appearance_mode_menu.currentTextChanged.connect(self.change_appearance_mode_event)
        sidebar_layout.addWidget(self.appearance_mode_menu)

        # --- Main Dashboard ---
        self.main_area = QWidget()
        main_area_layout = QVBoxLayout(self.main_area)
        main_area_layout.setContentsMargins(30, 30, 30, 30)
        main_area_layout.setSpacing(20)
        main_layout.addWidget(self.main_area, 1)

        # Drop Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.dropped.connect(self._handle_drop)
        main_area_layout.addWidget(self.drop_zone)

        # Drop Zone Actions (Browse & Recent)
        self.btn_browse = QPushButton("Browse Folder")
        self.btn_browse.setFixedWidth(140)
        self.btn_browse.clicked.connect(self.browse_folder)
        self.drop_zone.actions_layout.addStretch()
        self.drop_zone.actions_layout.addWidget(self.btn_browse)
        
        self.option_recent = QComboBox()
        self.option_recent.setFixedWidth(160)
        self.option_recent.addItem("Recent...")
        self.option_recent.currentTextChanged.connect(self._on_recent_select)
        self.drop_zone.actions_layout.addWidget(self.option_recent)
        self.drop_zone.actions_layout.addStretch()

        # Controls
        controls_layout = QHBoxLayout()
        main_area_layout.addLayout(controls_layout)

        options_layout = QHBoxLayout()
        controls_layout.addLayout(options_layout)

        self.chk_rec = QCheckBox("Recursive")
        options_layout.addWidget(self.chk_rec)

        self.chk_del = QCheckBox("Delete Empty")
        options_layout.addWidget(self.chk_del)

        self.chk_date = QCheckBox("Sort by Date")
        options_layout.addWidget(self.chk_date)

        self.chk_duplicates = QCheckBox("Duplicates")
        options_layout.addWidget(self.chk_duplicates)

        self.chk_watch = QCheckBox("Watch Folder")
        self.chk_watch.stateChanged.connect(lambda s: self.controller.toggle_watch(s == Qt.Checked))
        options_layout.addWidget(self.chk_watch)

        controls_layout.addStretch()

        # AI Confidence (Initially Hidden)
        self.ai_conf_container = QWidget()
        ai_conf_layout = QHBoxLayout(self.ai_conf_container)
        ai_conf_layout.setContentsMargins(0, 0, 0, 0)
        ai_conf_layout.addWidget(QLabel("AI Confidence:"))
        self.slider_conf = QSlider(Qt.Horizontal)
        self.slider_conf.setRange(1, 9)
        self.slider_conf.setValue(3)
        self.slider_conf.setFixedWidth(100)
        ai_conf_layout.addWidget(self.slider_conf)
        self.ai_conf_container.hide()
        controls_layout.addWidget(self.ai_conf_container)

        self.btn_preview = QPushButton("PREVIEW")
        self.btn_preview.setObjectName("secondary")
        self.btn_preview.setFixedSize(120, 40)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(lambda: self.controller.run_organization(dry_run=True))
        controls_layout.addWidget(self.btn_preview)

        self.btn_run = QPushButton("ORGANIZE")
        self.btn_run.setObjectName("success")
        self.btn_run.setFixedSize(120, 40)
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(lambda: self.controller.run_organization())
        controls_layout.addWidget(self.btn_run)

        # Results Area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setObjectName("card")
        self.results_scroll.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: {RADII['standard']}px;")
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(5)
        self.results_layout.addStretch()
        
        self.results_scroll.setWidget(self.results_container)
        main_area_layout.addWidget(self.results_scroll, 1)

        # Status Bar
        status_layout = QHBoxLayout()
        main_area_layout.addLayout(status_layout)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setObjectName("dimmed")
        self.lbl_status.setStyleSheet(get_font_style("small"))
        status_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        status_layout.addWidget(self.progress_bar)

    # --- View Interface for Controller ---

    def update_folder_display(self, path_str):
        self.drop_zone.lbl_text.setText(f"Selected: {os.path.basename(path_str)}")
        self.btn_preview.setEnabled(True)
        self.btn_run.setEnabled(True)

    def clear_results(self):
        # Safely clear widgets from the layout without risking infinite loops
        count = self.results_layout.count()
        for _ in range(count - 1): # keep the last stretch
            item = self.results_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
        self.result_cards.clear()

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def confirm_action(self, title, message):
        res = QMessageBox.question(self, title, message, QMessageBox.Yes | QMessageBox.No)
        return res == QMessageBox.Yes

    def update_recent_menu(self, recent_folders):
        self.option_recent.blockSignals(True)
        self.option_recent.clear()
        self.option_recent.addItem("Recent...")
        self.option_recent.addItems(recent_folders)
        self.option_recent.blockSignals(False)

    def update_stats_display(self, stats):
        total = stats.get("total_files", 0)
        last = stats.get("last_run", "Never")
        self.lbl_stats_total.setText(f"Files Organized: {total}")
        self.lbl_stats_last.setText(f"Last Run: {last}")

    def show_model_download(self, callback):
        modal = ModelDownloadModal(self, on_complete=callback)
        modal.exec()

    def show_settings(self, organizer):
        dialog = SettingsDialog(self, organizer)
        dialog.exec()

    def show_batch(self, organizer):
        dialog = BatchDialog(self, organizer)
        dialog.exec()

    def show_status(self, message):
        self.lbl_status.setText(message)

    def update_progress(self, current, total, filename):
        if total > 0:
            if isinstance(total, float):  # ML loading percentage
                self.progress_bar.setValue(int(current * 100))
                self.lbl_status.setText(f"{filename}")
            else:
                self.progress_bar.setValue(int((current / total) * 100))
                self.lbl_status.setText(f"Processing: {filename}")

    def after_main(self, ms, func):
        QTimer.singleShot(ms, func)

    def enable_ai_ui(self):
        self.ai_conf_container.show()
        self.lbl_ai.setStyleSheet(f"{get_font_style('label')} color: #9C27B0;")

    def disable_ai_ui(self):
        self.ai_conf_container.hide()
        self.lbl_ai.setStyleSheet(f"{get_font_style('label')} color: {COLORS['text_main']};")

    def set_ai_switch_state(self, state):
        self.switch_ai.blockSignals(True)
        self.switch_ai.setChecked(state)
        self.switch_ai.blockSignals(False)

    def set_watch_switch_state(self, state):
        self.chk_watch.blockSignals(True)
        self.chk_watch.setChecked(state)
        self.chk_watch.blockSignals(False)

    def set_running_state(self, is_running):
        self.btn_run.setEnabled(not is_running)
        self.btn_preview.setEnabled(not is_running)
        if not is_running:
            for card in self.result_cards:
                card.set_executed()

    def get_ai_confidence(self):
        return self.slider_conf.value() / 10.0

    def get_recursive_val(self):
        return self.chk_rec.isChecked()

    def get_date_sort_val(self):
        return self.chk_date.isChecked()

    def get_del_empty_val(self):
        return self.chk_del.isChecked()

    def get_detect_duplicates_val(self):
        return self.chk_duplicates.isChecked()

    def add_result_card(self, data):
        card = FileCard(data)
        self.results_layout.insertWidget(self.results_layout.count() - 1, card)
        self.result_cards.append(card)

    def update_results_header(self, message):
        # In this version, we don't have a specific header in the scroll area
        # but we can use the status label
        self.lbl_status.setText(message)

    # --- Event Handlers ---

    def _handle_drop(self, path):
        if path == "__BROWSE__":
            self.browse_folder()
        else:
            self.controller.set_folder(path)

    def browse_folder(self):
        initial = self.controller.selected_path if self.controller.selected_path else None
        path = QFileDialog.getExistingDirectory(self, "Select Folder", initial or "")
        if path:
            self.controller.set_folder(path)

    def _on_recent_select(self, val):
        if val != "Recent...":
            self.controller.on_recent_select(val)

    def change_appearance_mode_event(self, new_mode: str):
        self._apply_theme(new_mode)
        self.organizer.save_theme_mode(new_mode)

    def open_settings(self):
        self.controller.open_settings()

    def open_batch(self):
        self.controller.open_batch()


def main():
    app = QApplication(sys.argv)
    window = OrganizerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
