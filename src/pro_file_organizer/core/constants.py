import os

DEFAULT_DIRECTORIES = {
    "Images": [".jpeg", ".jpg", ".tiff", ".gif", ".bmp", ".png", ".bpg", ".svg", ".heif", ".psd"],
    "Videos": [".avi", ".flv", ".wmv", ".mov", ".mp4", ".webm", ".vob", ".mng", ".qt", ".mpg", ".mpeg", ".3gp"],
    "Documents": [".oxps", ".epub", ".pages", ".docx", ".doc", ".fdf", ".ods", ".odt", ".pwi", ".xsn", ".xps", ".dotx", ".docm", ".dox", ".rvg", ".rtf", ".rtfd", ".wpd", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".pdf", ".txt", ".md"],
    "Archives": [".a", ".ar", ".cpio", ".iso", ".tar", ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"],
    "Audio": [".aac", ".aa", ".aac", ".dvf", ".m4a", ".m4b", ".m4p", ".mp3", ".msv", ".ogg", ".oga", ".raw", ".vox", ".wav", ".wma"],
    "Code": [".py", ".js", ".html", ".css", ".php", ".c", ".cpp", ".h", ".java", ".cs"],
    "Executables": [".exe", ".msi", ".bat", ".sh"]
}

DEFAULT_ML_CATEGORIES = {
    "Images/Personal": {
        "text": "personal photos family vacation memories selfies",
        "visual": ["a photograph of people", "family photos", "vacation pictures", "selfie"]
    },
    "Images/Screenshots": {
        "text": "screenshot application software interface UI",
        "visual": ["a screenshot of software", "computer interface", "app screen"]
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

# Application defaults
DEFAULT_CONFIG_FILE = "config/config.json"
DEFAULT_BATCH_CONFIG_FILE = "config/batch_config.json"
DEFAULT_STATS_FILE = "config/stats.json"
DEFAULT_RECENT_FILE = "config/recent.json"

EXCLUDED_NAMES = {
    "app.py", "organizer.py", "config.json", "themes.py", "recent.json", 
    "batch_config.json", "venv", ".git", "__pycache__", "src", "config", "logs", "scripts"
}
