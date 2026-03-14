import os
import shutil
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QProgressBar, QTextEdit, QPushButton, QFileDialog
)
from PySide6.QtGui import QFont, QColor

from ..themes.themes import COLORS, FONTS, RADII, get_font_style


class FileCard(QFrame):
    """
    A card representing a file operation (move, rename, error).
    """

    def __init__(self, event_data: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.event = event_data

        # Initial state (dimmed)
        self.executed = False

        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.layout.setSpacing(10)

        # Left Accent Stripe & Badge Logic
        method = event_data.get("method", "extension")
        confidence = event_data.get("confidence", 1.0)
        etype = event_data.get("type", "move")

        accent_color = COLORS["accent"]
        badge_text = "EXT"

        if method != "extension" and method != "ml-not-loaded":
            accent_color = "#9C27B0"  # AI Purple
            badge_text = f"AI {int(confidence * 100)}%"

        if etype == "error":
            accent_color = COLORS["danger"]
            badge_text = "ERR"
        elif etype == "duplicate":
            accent_color = COLORS["warning"]
            badge_text = "DUP"

        # Accent Stripe
        self.stripe = QFrame(self)
        self.stripe.setFixedWidth(4)
        self.stripe.setStyleSheet(f"background-color: {accent_color}; border-radius: 0px;")
        self.layout.addWidget(self.stripe)

        # Content Layout
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 5, 0, 5)
        self.content_layout.setSpacing(2)
        self.layout.addLayout(self.content_layout, 1)

        # Filename
        filename = event_data.get("file", "Unknown")
        self.lbl_name = QLabel(filename)
        self.lbl_name.setStyleSheet(get_font_style("label"))
        self.content_layout.addWidget(self.lbl_name)

        # Destination / Error Message
        dest = event_data.get("destination", "")
        try:
            dest_path = Path(dest)
            display_dest = f"→ {dest_path.parent.name}/{dest_path.name}"
        except Exception:
            display_dest = f"→ {dest}"

        if etype == "error":
            display_dest = f"Error: {event_data.get('error')}"

        if etype == "duplicate":
            dup_of = event_data.get("duplicate_of", "another file")
            try:
                display_dest = f"Duplicate of: {Path(dup_of).name}"
            except Exception:
                display_dest = f"Duplicate of: {dup_of}"

        self.lbl_dest = QLabel(display_dest)
        self.lbl_dest.setObjectName("dimmed")
        self.lbl_dest.setStyleSheet(get_font_style("small"))
        self.content_layout.addWidget(self.lbl_dest)

        # Badge
        self.lbl_badge = QLabel(badge_text)
        self.lbl_badge.setFixedSize(65, 22)
        self.lbl_badge.setAlignment(Qt.AlignCenter)
        self.lbl_badge.setStyleSheet(f"""
            background-color: {accent_color};
            color: white;
            border-radius: {RADII['badge']}px;
            {get_font_style('small')}
        """)
        self.layout.addWidget(self.lbl_badge)

        self.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: {RADII['card']}px;")
        self._apply_appearance()

    def set_executed(self):
        """Transition card to fully opaque executed state."""
        self.executed = True
        self._apply_appearance()

    def _apply_appearance(self):
        if not self.executed:
            self.lbl_name.setStyleSheet(f"{get_font_style('label')} color: {COLORS['text_dimmed']};")
        else:
            self.lbl_name.setStyleSheet(f"{get_font_style('label')} color: {COLORS['text_main']};")


class DownloadSignals(QObject):
    log_emitted = Signal(str)
    progress_updated = Signal(float)
    finished = Signal(bool, str)


class RedirectedStderr:
    """Redirects stderr to a PySide6 signal."""

    def __init__(self, signals: DownloadSignals):
        self.signals = signals

    def write(self, string):
        if string.strip():
            self.signals.log_emitted.emit(string)

    def flush(self):
        pass


class ModelDownloadModal(QDialog):
    def __init__(self, parent: QWidget, on_complete: Optional[Callable[[bool], None]] = None):
        super().__init__(parent)
        self.setWindowTitle("Smart AI Setup")
        self.setFixedSize(500, 450)
        self.on_complete = on_complete
        self.download_started = False
        
        self.signals = DownloadSignals()
        self._setup_ui()
        
        self.signals.log_emitted.connect(self._append_log)
        self.signals.progress_updated.connect(self.progress_bar.setValue)
        self.signals.finished.connect(self._on_download_finished)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.frame = QFrame()
        self.frame.setObjectName("card")
        self.frame.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: {RADII['standard']}px;")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.frame)

        # Title
        self.lbl_title = QLabel("Download AI Models")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(get_font_style("subtitle"))
        frame_layout.addWidget(self.lbl_title)

        # Description
        desc_text = (
            "Smart Categorization requires advanced AI models to analyze your files.\n"
            "This involves a ~3GB one-time download."
        )
        self.lbl_desc = QLabel(desc_text)
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet(get_font_style("main"))
        frame_layout.addWidget(self.lbl_desc)

        # Details Area
        self.details_container = QWidget()
        details_layout = QVBoxLayout(self.details_container)
        frame_layout.addWidget(self.details_container)

        self._add_detail_row(details_layout, "Text Model:", "Qwen/Qwen3-Embedding-0.6B")
        self._add_detail_row(details_layout, "Image Model:", "google/siglip2-base-patch32-256")
        self._add_detail_row(details_layout, "Download Size:", "~3.0 GB")

        free_space_gb = self._get_free_space_gb()
        space_color = COLORS["success"] if free_space_gb > 5 else COLORS["warning"]
        if free_space_gb < 4:
            space_color = COLORS["danger"]

        self._add_detail_row(details_layout, "Free Space:", f"{free_space_gb:.2f} GB", value_color=space_color)

        # Progress & Log (Initially hidden in details mode)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        frame_layout.addWidget(self.progress_bar)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(f"font-family: 'Consolas'; font-size: 10px; background-color: {COLORS['bg_main']};")
        self.txt_log.hide()
        frame_layout.addWidget(self.txt_log)

        # Buttons
        btns_layout = QHBoxLayout()
        layout.addLayout(btns_layout)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("secondary")
        self.btn_cancel.clicked.connect(self.reject)
        btns_layout.addWidget(self.btn_cancel)

        self.btn_start = QPushButton("Download Models")
        self.btn_start.setObjectName("success")
        self.btn_start.clicked.connect(self.start_download)
        btns_layout.addWidget(self.btn_start)

        if free_space_gb < 4:
            self.lbl_warn = QLabel("⚠️ Low Disk Space")
            self.lbl_warn.setStyleSheet(f"color: {COLORS['danger']}; {get_font_style('small')}")
            self.lbl_warn.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(self.lbl_warn)

    def _add_detail_row(self, layout, label, value, value_color=None):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold;")
        lbl.setFixedWidth(120)
        row_layout.addWidget(lbl)
        
        val = QLabel(value)
        if value_color:
            val.setStyleSheet(f"color: {value_color};")
        row_layout.addWidget(val)
        
        layout.addWidget(row)

    def _get_free_space_gb(self):
        try:
            hf_home = os.environ.get("HF_HOME")
            if not hf_home:
                xdg = os.environ.get("XDG_CACHE_HOME")
                if xdg:
                    hf_home = os.path.join(xdg, "huggingface")
                else:
                    hf_home = os.path.expanduser("~/.cache/huggingface")

            check_path = hf_home
            if not os.path.exists(check_path):
                check_path = os.path.expanduser("~")

            total, used, free = shutil.disk_usage(check_path)
            return free / (1024**3)
        except Exception:
            return 0.0

    def start_download(self):
        if self.download_started:
            return
        self.download_started = True

        self.btn_start.setEnabled(False)
        self.btn_start.setText("Downloading...")
        self.btn_cancel.setEnabled(False)

        self.details_container.hide()
        self.lbl_desc.setText("Please wait. This may take a few minutes.")
        self.progress_bar.show()
        self.txt_log.show()
        self.txt_log.append("Initializing download...")

        threading.Thread(target=self._download_task, daemon=True).start()

    def _download_task(self):
        redirector = RedirectedStderr(self.signals)
        original_stderr = sys.stderr
        sys.stderr = redirector

        try:
            from ...core.ml_organizer import MultimodalFileOrganizer
            ml_org = MultimodalFileOrganizer()

            def cb(msg, val):
                if isinstance(val, (int, float)):
                    self.signals.progress_updated.emit(float(val) * 100 if val <= 1.0 else float(val))
                self.signals.log_emitted.emit(msg)

            ml_org.ensure_models(progress_callback=cb)
            self.signals.finished.emit(True, "")

        except Exception as e:
            self.signals.finished.emit(False, str(e))

        finally:
            sys.stderr = original_stderr

    def _append_log(self, text):
        self.txt_log.append(text)
        self.txt_log.ensureCursorVisible()

    def _on_download_finished(self, success, error_msg):
        if success:
            if self.on_complete:
                self.on_complete(True)
            self.accept()
        else:
            self.lbl_title.setText("Download Failed")
            self.lbl_title.setStyleSheet(f"color: {COLORS['danger']}; {get_font_style('subtitle')}")
            self.btn_cancel.setEnabled(True)
            self.btn_start.setEnabled(True)
            self.btn_start.setText("Retry")
            self.download_started = False
            if self.on_complete:
                self.on_complete(False)
            self.txt_log.append(f"\nError: {error_msg}")
