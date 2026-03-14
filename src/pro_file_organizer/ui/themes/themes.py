"""
Centralized UI constants for Pro File Organizer.
Adapts to PySide6 with QSS support.
"""

from typing import Dict, Tuple

# Palette Definitions
LIGHT_COLORS = {
    "accent": "#2F6FAD",
    "bg_main": "#F5F6F8",
    "bg_sidebar": "#EAEBED",
    "bg_card": "#FFFFFF",
    "bg_hover": "#EBF5FF",
    "text_main": "#1A1B1E",
    "text_dimmed": "#909296",
    "success": "#2DCC70",
    "danger": "#E03131",
    "warning": "#F08C00",
    "border": "#CED4DA",
    "separator": "#DEE2E6",
}

DARK_COLORS = {
    "accent": "#3B8ED0",
    "bg_main": "#1A1B1E",
    "bg_sidebar": "#111214",
    "bg_card": "#25262B",
    "bg_hover": "#1C2C3E",
    "text_main": "#C1C2C5",
    "text_dimmed": "#5C5F66",
    "success": "#2DCC70",
    "danger": "#E03131",
    "warning": "#F08C00",
    "border": "#373A40",
    "separator": "#2C2E33",
}

# Default to DARK_COLORS for backwards compatibility where tuple-less COLORS is needed
COLORS = DARK_COLORS

# Typography
FONTS = {
    "title": ("Inter", 20, "bold"),
    "subtitle": ("Inter", 16, "bold"),
    "label": ("Inter", 13, "bold"),
    "main": ("Inter", 13),
    "small": ("Inter", 11),
    "mono": ("Consolas", 11),
}

# Radii
RADII = {
    "standard": 12,
    "card": 10,
    "badge": 6,
}


def build_stylesheet(colors: Dict[str, str]) -> str:
    """Generates a QSS stylesheet based on the color palette."""
    return f"""
    QMainWindow, QDialog {{
        background-color: {colors['bg_main']};
        color: {colors['text_main']};
    }}

    QFrame {{
        background-color: transparent;
    }}

    QFrame#sidebar {{
        background-color: {colors['bg_sidebar']};
        border-right: 1px solid {colors['separator']};
    }}

    QFrame#card {{
        background-color: {colors['bg_card']};
        border-radius: {RADII['card']}px;
    }}

    QLabel {{
        color: {colors['text_main']};
    }}

    QLabel#dimmed {{
        color: {colors['text_dimmed']};
    }}

    QPushButton {{
        background-color: {colors['accent']};
        color: white;
        border-radius: {RADII['card']}px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {colors['bg_hover']};
        color: {colors['accent']};
        border: 1px solid {colors['accent']};
    }}

    QPushButton#secondary {{
        background-color: transparent;
        border: 1px solid {colors['border']};
        color: {colors['text_main']};
    }}

    QPushButton#danger {{
        background-color: {colors['danger']};
    }}

    QPushButton#success {{
        background-color: {colors['success']};
    }}

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADII['badge']}px;
        color: {colors['text_main']};
        padding: 5px;
    }}

    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        border: none;
        background: {colors['bg_main']};
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {colors['border']};
        min-height: 20px;
        border-radius: 5px;
    }}

    QProgressBar {{
        border: 1px solid {colors['border']};
        border-radius: {RADII['badge']}px;
        text-align: center;
        background-color: {colors['bg_card']};
    }}

    QProgressBar::chunk {{
        background-color: {colors['accent']};
        border-radius: {RADII['badge']}px;
    }}

    QCheckBox {{
        color: {colors['text_main']};
    }}

    QComboBox {{
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: {RADII['badge']}px;
        padding: 5px;
        color: {colors['text_main']};
    }}

    QTabWidget::pane {{
        border: 1px solid {colors['separator']};
        background-color: {colors['bg_main']};
        border-radius: {RADII['standard']}px;
    }}

    QTabBar::tab {{
        background-color: {colors['bg_sidebar']};
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: {RADII['badge']}px;
        border-top-right-radius: {RADII['badge']}px;
        color: {colors['text_dimmed']};
    }}

    QTabBar::tab:selected {{
        background-color: {colors['accent']};
        color: white;
    }}
    """


def get_font_style(key: str) -> str:
    """Returns a CSS font-family/size string."""
    name, size, *weight = FONTS[key]
    weight_str = "bold" if weight else "normal"
    return f"font-family: '{name}'; font-size: {size}px; font-weight: {weight_str};"
