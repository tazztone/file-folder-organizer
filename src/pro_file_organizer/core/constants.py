from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

# Application Metadata
APP_NAME = "pro-file-organizer"
APP_AUTHOR = "Tazztone"

# Resolve platform-specific paths
CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
LOG_DIR = DATA_DIR / "logs"

def init_app_dirs():
    """Ensure application directories exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

MAX_UNDO_STACK = 5

DEFAULT_CONFIG_FILE = str(CONFIG_DIR / "config.json")
DEFAULT_BATCH_CONFIG_FILE = str(CONFIG_DIR / "batch_config.json")
DEFAULT_STATS_FILE = str(DATA_DIR / "stats.json")
DEFAULT_RECENT_FILE = str(DATA_DIR / "recent.json")
DEFAULT_UNDO_STACK_FILE = str(DATA_DIR / "undo_stack.json")

DEFAULT_DIRECTORIES = {
    "Images": [
        ".jpeg", ".jpg", ".tiff", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".psd"
    ],
    "Videos": [
        ".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp"
    ],
    "Documents": [
        ".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwi", ".xsn",
        ".xps", ".dotx", ".docm", ".dox", ".rvg", ".rtf", ".rtfd", ".wpd", ".xls", ".xlsx",
        ".ppt", ".pptx", ".csv", ".pdf", ".txt", ".md"
    ],
    "Archives": [
        ".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"
    ],
    "Audio": [
        ".aac", ".aa", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".raw",
        ".vox", ".wav", ".wma"
    ],
    "Code": [".py", ".js", ".html", ".css", ".php", ".c", ".cpp", ".h", ".java", ".cs"],
    "Executables": [".exe", ".msi", ".bat", ".sh"]
}

DEFAULT_CATEGORY = "Others"

DEFAULT_ML_CATEGORIES = {
    "Images/Personal": {
        "text": "personal photos family vacation memories selfies",
        "visual": ["a photograph of people", "family photos", "vacation pictures", "selfie"],
        "threshold": 0.4
    },
    "Images/Screenshots": {
        "text": "screenshot application software interface UI",
        "visual": ["a screenshot of software", "computer interface", "app screen"],
        "threshold": 0.5
    },
    "Images/Diagrams": {
        "text": "diagram flowchart technical drawing architecture",
        "visual": ["a technical diagram", "flowchart", "architectural drawing"]
    },
    "Images/Design": {
        "text": "logo mockup design graphic illustration artwork",
        "visual": ["graphic design", "logo design", "mockup"]
    },
    "Documents/Code": {
        "text": "programming code python javascript html css",
        "visual": ["code snippet", "programming text"]
    },
    "Documents/Financial": {
        "text": "invoice receipt tax financial statement budget",
        "visual": ["invoice document", "financial statement"]
    },
    "Documents/Reports": {
        "text": "report analysis presentation business document",
        "visual": ["business report", "presentation slide"]
    }
}

# Names of files/folders that should never be moved by the organizer.
# These are generic exclusions common across systems.
EXCLUDED_NAMES = {
    "venv", ".git", "__pycache__", ".venv", "node_modules", ".ruff_cache", ".pytest_cache"
}
