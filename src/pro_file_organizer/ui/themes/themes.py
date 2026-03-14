"""
Centralized UI constants for Pro File Organizer.
Uses customtkinter color tuples for automatic light/dark theme support.
"""

# Palette Definitions (Light, Dark)
COLORS = {
    "accent": ("#2F6FAD", "#3B8ED0"),
    "bg_main": ("#F5F6F8", "#1A1B1E"),
    "bg_sidebar": ("#EAEBED", "#111214"),
    "bg_card": ("#FFFFFF", "#25262B"),
    "bg_hover": ("#EBF5FF", "#1C2C3E"),  # Subtle blue tint for hover
    "text_main": ("#1A1B1E", "#C1C2C5"),
    "text_dimmed": ("#909296", "#5C5F66"),
    "success": ("#2DCC70", "#2DCC70"),
    "danger": ("#E03131", "#E03131"),
    "warning": ("#F08C00", "#F08C00"),
    "border": ("#CED4DA", "#373A40"),
    "separator": ("#DEE2E6", "#2C2E33"),
}

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


def get_font(key):
    """Fallback font handling if Inter is not available."""
    # CustomTkinter handles system font fallback well
    return FONTS.get(key, ("sans-serif", 13))
