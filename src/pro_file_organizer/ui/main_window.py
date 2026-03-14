import os
import sys
from typing import List, Optional

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDropEvent, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.ml_organizer import MultimodalFileOrganizer
from ..core.organizer import FileOrganizer
from .components.ui_components import FileCard, ModelDownloadModal
from .dialogs.batch_dialog import BatchDialog
from .dialogs.settings_dialog import SettingsDialog
from .main_window_controller import MainWindowController
from .themes.themes import COLORS, RADII, apply_theme, build_stylesheet, get_font_style


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None, track_radius=10, thumb_radius=8):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._track_radius = track_radius
        self._thumb_radius = thumb_radius

        self._margin = 2
        self._base_width = 40
        self._base_height = 20

        self._thumb_pos = self._margin
        self._animation = QPropertyAnimation(self, b"thumb_pos", self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutExpo)

        self.setFixedSize(self._base_width, self._base_height)

    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    thumb_pos = Property(float, get_thumb_pos, set_thumb_pos)

    def sizeHint(self):
        return QSize(self._base_width, self._base_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw track
        track_color = QColor(COLORS["accent"]) if self.isChecked() else QColor(COLORS["border"])
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self._track_radius, self._track_radius)

        # Draw thumb
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(
            self._thumb_pos, self._margin, self.height() - 2 * self._margin, self.height() - 2 * self._margin
        )

    def nextCheckState(self):
        super().nextCheckState()
        self._animation.stop()
        if self.isChecked():
            self._animation.setEndValue(self.width() - self.height() + self._margin)
        else:
            self._animation.setEndValue(self._margin)
        self._animation.start()

    def setChecked(self, checked):
        super().setChecked(checked)
        self._thumb_pos = (self.width() - self.height() + self._margin) if checked else self._margin
        self.update()


class DropZoneWidget(QFrame):
    dropped = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hovered = False
        self.setObjectName("drop_zone")
        self.setFixedHeight(160)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_icon = QLabel("📤")
        self.lbl_icon.setStyleSheet("font-size: 48px; background: transparent;")
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_icon)

        self.lbl_text = QLabel("Drag & Drop Folder Here")
        self.lbl_text.setStyleSheet(f"{get_font_style('subtitle')} background: transparent;")
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_text)

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0, 10, 0, 0)
        layout.addLayout(self.actions_layout)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = COLORS["accent"] if self.hovered else COLORS["border"]
        pen = QPen(QColor(color))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
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
        if event.button() == Qt.MouseButton.LeftButton:
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
        if mode == "System":
            is_dark = QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128
            apply_theme("Dark" if is_dark else "Light")
        else:
            apply_theme(mode)

        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(build_stylesheet(COLORS))

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

        self.switch_ai = ToggleSwitch()
        self.switch_ai.clicked.connect(lambda: self.controller.toggle_ai(self.switch_ai.isChecked()))
        ai_layout.addWidget(self.switch_ai)

        self.lbl_ai_warn = QLabel("~3GB download on first use")
        self.lbl_ai_warn.setObjectName("dimmed")
        self.lbl_ai_warn.setStyleSheet(get_font_style("small"))
        sidebar_layout.addWidget(self.lbl_ai_warn)

        # Main Buttons
        self.btn_batch = QPushButton("Batch Mode")
        self.btn_batch.setFixedHeight(40)
        self.btn_batch.clicked.connect(self.open_batch)
        sidebar_layout.addWidget(self.btn_batch)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setFixedHeight(40)
        self.btn_settings.clicked.connect(self.open_settings)
        sidebar_layout.addWidget(self.btn_settings)

        self.btn_undo = QPushButton("Undo Last")
        self.btn_undo.setFixedHeight(40)
        self.btn_undo.setObjectName("secondary")
        self.btn_undo.clicked.connect(lambda: self.controller.undo_action())
        sidebar_layout.addWidget(self.btn_undo)

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
        self.main_area.setObjectName("main_dashboard")
        self.main_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
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
        self.chk_rec.setToolTip("Process all subfolders recursively.")
        options_layout.addWidget(self.chk_rec)

        self.chk_del = QCheckBox("Delete Empty")
        self.chk_del.setToolTip("Delete empty folders after organizing. Warning: Destructive.")
        options_layout.addWidget(self.chk_del)

        self.chk_date = QCheckBox("Sort by Date")
        self.chk_date.setToolTip("Sort files into Year/Month subfolders.")
        options_layout.addWidget(self.chk_date)

        self.chk_duplicates = QCheckBox("Duplicates")
        self.chk_duplicates.setToolTip("Detect and handle duplicate files automatically.")
        options_layout.addWidget(self.chk_duplicates)

        self.chk_watch = QCheckBox("Watch Folder")
        self.chk_watch.setToolTip("Continuously monitor and organize files as they arrive.")
        self.chk_watch.stateChanged.connect(lambda s: self.controller.toggle_watch(s == Qt.CheckState.Checked))
        options_layout.addWidget(self.chk_watch)

        controls_layout.addStretch()

        # AI Confidence (Initially Hidden)
        self.ai_conf_container = QWidget()
        ai_conf_layout = QHBoxLayout(self.ai_conf_container)
        ai_conf_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_ai_conf = QLabel("AI Confidence: 30%")
        ai_conf_layout.addWidget(self.lbl_ai_conf)
        self.slider_conf = QSlider(Qt.Orientation.Horizontal)
        self.slider_conf.setRange(1, 10)
        self.slider_conf.setValue(3)
        self.slider_conf.setFixedWidth(100)
        self.slider_conf.valueChanged.connect(self._on_confidence_slider_changed)
        self._conf_debounce_timer = QTimer()
        self._conf_debounce_timer.setSingleShot(True)
        self._conf_debounce_timer.timeout.connect(self._apply_confidence_change)
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

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setFixedSize(120, 40)
        self.btn_stop.hide()
        self.btn_stop.clicked.connect(lambda: setattr(self.controller, "is_running", False))
        controls_layout.addWidget(self.btn_stop)

        # Results Area Header + Sort Options
        results_header_layout = QHBoxLayout()
        main_area_layout.addLayout(results_header_layout)

        self.results_header = QLabel("Waiting for action...")
        self.results_header.setStyleSheet(get_font_style("label"))
        results_header_layout.addWidget(self.results_header)

        results_header_layout.addStretch()

        self.sort_container = QWidget()
        sort_layout = QHBoxLayout(self.sort_container)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_sort = QLabel("Sort:")
        self.lbl_sort.setStyleSheet(get_font_style("small"))
        sort_layout.addWidget(self.lbl_sort)
        self.combo_sort = QComboBox()
        self.combo_sort.addItems(["None", "Name \u2191", "Confidence \u2193", "Type A-Z"])
        self.combo_sort.currentTextChanged.connect(self._on_sort_changed)
        sort_layout.addWidget(self.combo_sort)
        self.sort_container.hide()
        results_header_layout.addWidget(self.sort_container)

        # Category Breakdown Bar
        self.breakdown_container = QWidget()
        self.breakdown_layout = QHBoxLayout(self.breakdown_container)
        self.breakdown_layout.setContentsMargins(0, 0, 0, 0)
        try:
            self.breakdown_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        except AttributeError:
            # Fallback for mocked Qt in tests
            pass
        self.breakdown_container.hide()
        main_area_layout.addWidget(self.breakdown_container)

        # Results & Log area with Tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setObjectName("results_tabs")
        main_area_layout.addWidget(self.results_tabs, 1)

        # Tab 1: Results (Cards)
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setObjectName("card")

        self.results_container = QWidget()
        self.results_container.setObjectName("results_content")
        self.results_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(5)
        self.results_layout.addStretch()

        self.results_scroll.setWidget(self.results_container)
        self.results_tabs.addTab(self.results_scroll, "Results")

        # Tab 2: Raw Log
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(f"{get_font_style('mono')}")
        self.results_tabs.addTab(self.log_view, "Log View")

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
        self.drop_zone.lbl_icon.hide()
        self.drop_zone.lbl_text.setText(f"Selected: {os.path.basename(path_str)}")
        self.btn_preview.setEnabled(True)
        self.btn_run.setEnabled(True)

    def clear_cards(self):
        """Clears only the result cards without resetting other UI state."""
        # Safely clear widgets from the layout without risking infinite loops
        count = self.results_layout.count()
        for _ in range(count - 1):  # keep the last stretch
            item = self.results_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
        self.result_cards.clear()

    def clear_results(self):
        """Perform a full reset of the results area including toggles and sorts."""
        self.clear_cards()
        self.sort_container.hide()
        self.breakdown_container.hide()
        self.combo_sort.blockSignals(True)
        self.combo_sort.setCurrentIndex(0)
        self.combo_sort.blockSignals(False)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def confirm_action(self, title, message):
        res = QMessageBox.question(self, title, message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return res == QMessageBox.StandardButton.Yes

    def update_recent_menu(self, recent_folders):
        self.option_recent.blockSignals(True)
        self.option_recent.clear()
        self.option_recent.addItem("Recent...")
        self.option_recent.addItems(recent_folders)
        self.option_recent.blockSignals(False)

    def update_stats_display(self, stats):
        total = stats.get("total_files", 0)
        last = stats.get("last_run", "Never")
        if total == 0:
            self.lbl_stats_total.setText("Organize your first folder!")
            self.lbl_stats_last.setText("")
        else:
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
        QTimer.singleShot(ms, self, func)

    def enable_ai_ui(self):
        self.ai_conf_container.show()
        self.lbl_ai.setStyleSheet(f"{get_font_style('label')} color: #9C27B0;")

    def disable_ai_ui(self):
        self.ai_conf_container.hide()
        self.lbl_ai.setStyleSheet(f"{get_font_style('label')} color: {COLORS['text_main']};")

    def set_ai_switch_state(self, state):
        self.switch_ai.setChecked(state)

    def set_watch_switch_state(self, state):
        self.chk_watch.blockSignals(True)
        self.chk_watch.setChecked(state)
        self.chk_watch.blockSignals(False)

    def set_running_state(self, is_running):
        self.btn_run.setEnabled(not is_running)
        self.btn_preview.setEnabled(not is_running)
        if is_running:
            self.btn_run.hide()
            self.btn_preview.hide()
            self.btn_stop.show()
        else:
            self.btn_stop.hide()
            self.btn_run.show()
            self.btn_preview.show()
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
        self.results_header.setText(message)

    def append_log(self, message):
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {message}")
        # Always scroll to bottom
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def clear_log(self):
        self.log_view.clear()

    def update_ai_confidence_label(self, value):
        self.lbl_ai_conf.setText(f"AI Confidence: {value * 10}%")

    def update_category_breakdown(self, counts, hidden_categories=None):
        if hidden_categories is None:
            hidden_categories = set()

        if not counts:
            self.breakdown_container.hide()
            # Clear layout if hiding
            while self.breakdown_layout.count():
                item = self.breakdown_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            return

        # Find existing buttons to update them without losing focus
        existing_buttons = {}
        for i in range(self.breakdown_layout.count()):
            widget = self.breakdown_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                # We stored the category name as object name
                cat_name = widget.property("category_name")
                if cat_name:
                    existing_buttons[cat_name] = widget

        # Remove buttons for categories that no longer exist
        for cat_name, btn in list(existing_buttons.items()):
            if cat_name not in counts:
                btn.deleteLater()
                existing_buttons.pop(cat_name)

        # Update or create buttons
        for cat, count in sorted(counts.items()):
            text = f"{cat}: {count}"
            should_be_checked = cat not in hidden_categories

            if cat in existing_buttons:
                btn = existing_buttons[cat]
                btn.setText(text)
                btn.blockSignals(True)
                btn.setChecked(should_be_checked)
                btn.blockSignals(False)
            else:
                btn = QPushButton(text)
                btn.setProperty("category_name", cat)
                btn.setCheckable(True)
                btn.setChecked(should_be_checked)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_dimmed']};
                        border: 1px solid {COLORS['border']};
                        border-radius: {RADII['badge']}px;
                        padding: 2px 8px;
                        {get_font_style('small')}
                    }}
                    QPushButton:checked {{
                        background-color: {COLORS['accent']}40;
                        color: {COLORS['text_main']};
                        border: 1px solid {COLORS['accent']};
                    }}
                """)
                btn.toggled.connect(lambda checked, c=cat: self.controller.on_category_toggle(c, checked))
                self.breakdown_layout.addWidget(btn)

        self.breakdown_container.show()
        self.sort_container.show()

    def _on_confidence_slider_changed(self, value):
        # Update label immediately but debounce controller update
        self.update_ai_confidence_label(value)
        self._conf_debounce_timer.start(150)

    def _apply_confidence_change(self):
        value = self.slider_conf.value()
        self.controller.on_confidence_changed(value)

    def _on_sort_changed(self, text):
        mapping = {
            "None": "none",
            "Name \u2191": "name",
            "Confidence \u2193": "confidence",
            "Type A-Z": "type"
        }
        self.controller.on_sort_changed(mapping.get(text, "none"))

    # --- Event Handlers ---

    def _handle_drop(self, path):
        if path == "__BROWSE__":
            self.browse_folder()
        else:
            self.controller.set_folder(path)

    def browse_folder(self):
        initial = str(self.controller.selected_path) if self.controller.selected_path else ""
        path = QFileDialog.getExistingDirectory(self, "Select Folder", initial)
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
