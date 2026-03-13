import tkinter as tk
from tkinter import ttk

# Palette definitions
PALETTES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "select_bg": "#a6a6a6",
        "select_fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "text_bg": "#ffffff",
        "text_fg": "#000000",
        "btn_bg": "#e0e0e0",
        "btn_fg": "#000000",
        "success": "#4CAF50",
        "warning": "#FFC107",
        "danger": "#D32F2F",
        "disabled": "#cccccc"
    },
    "dark": {
        "bg": "#2d2d2d",
        "fg": "#ffffff",
        "select_bg": "#555555",
        "select_fg": "#ffffff",
        "entry_bg": "#3d3d3d",
        "entry_fg": "#ffffff",
        "text_bg": "#1e1e1e",
        "text_fg": "#d4d4d4",
        "btn_bg": "#444444",
        "btn_fg": "#ffffff",
        "success": "#388E3C",
        "warning": "#FFA000",
        "danger": "#D32F2F",
        "disabled": "#555555"
    }
}

def setup_themes(style):
    """
    Configures the ttk.Style object with 'pro_light' and 'pro_dark' themes.
    """

    # ---------------------------------------------------------
    # Pro Light
    # ---------------------------------------------------------
    if "pro_light" not in style.theme_names():
        p = PALETTES["light"]
        style.theme_create("pro_light", parent="clam", settings={
            ".": {
                "configure": {
                    "background": p["bg"],
                    "foreground": p["fg"],
                    "troughcolor": p["bg"],
                    "selectbackground": p["select_bg"],
                    "selectforeground": p["select_fg"],
                    "fieldbackground": p["entry_bg"],
                    "borderwidth": 1,
                }
            },
            "TFrame": {"configure": {"background": p["bg"]}},
            "TLabel": {"configure": {"background": p["bg"], "foreground": p["fg"]}},
            "TButton": {
                "configure": {"background": p["btn_bg"], "foreground": p["btn_fg"], "borderwidth": 1},
                "map": {
                    "background": [("active", p["select_bg"]), ("disabled", p["disabled"])],
                    "foreground": [("disabled", "#888888")]
                }
            },
            "TEntry": {
                "configure": {"fieldbackground": p["entry_bg"], "foreground": p["entry_fg"]}
            },
            "TCheckbutton": {
                "configure": {"background": p["bg"], "foreground": p["fg"]},
                "map": {"background": [("active", p["bg"])]}
            },
            "TCombobox": {
                "configure": {"fieldbackground": p["entry_bg"], "foreground": p["entry_fg"], "arrowcolor": p["fg"]},
                "map": {"fieldbackground": [("readonly", p["entry_bg"])]}
            },
            "Treeview": {
                "configure": {"background": p["entry_bg"], "foreground": p["fg"], "fieldbackground": p["entry_bg"]},
                "map": {"background": [("selected", p["select_bg"])], "foreground": [("selected", p["select_fg"])]}
            },
            "Treeview.Heading": {
                "configure": {"background": p["btn_bg"], "foreground": p["btn_fg"], "relief": "flat"}
            },
            # Custom styles
            "Success.TButton": {
                "configure": {"background": p["success"], "foreground": "#ffffff"},
                "map": {"background": [("active", "#2E7D32"), ("disabled", p["disabled"])]}
            },
            "Danger.TButton": {
                 "configure": {"background": p["danger"], "foreground": "#ffffff"},
                 "map": {"background": [("active", "#B71C1C"), ("disabled", p["disabled"])]}
            }
        })

    # ---------------------------------------------------------
    # Pro Dark
    # ---------------------------------------------------------
    if "pro_dark" not in style.theme_names():
        p = PALETTES["dark"]
        style.theme_create("pro_dark", parent="clam", settings={
             ".": {
                "configure": {
                    "background": p["bg"],
                    "foreground": p["fg"],
                    "troughcolor": p["bg"],
                    "selectbackground": p["select_bg"],
                    "selectforeground": p["select_fg"],
                    "fieldbackground": p["entry_bg"],
                    "borderwidth": 1,
                    "bordercolor": p["bg"],
                }
            },
            "TFrame": {"configure": {"background": p["bg"]}},
            "TLabel": {"configure": {"background": p["bg"], "foreground": p["fg"]}},
            "TButton": {
                "configure": {"background": p["btn_bg"], "foreground": p["btn_fg"], "borderwidth": 1, "bordercolor": "#555555"},
                "map": {
                    "background": [("active", p["select_bg"]), ("disabled", p["disabled"])],
                    "foreground": [("disabled", "#888888")]
                }
            },
            "TEntry": {
                "configure": {"fieldbackground": p["entry_bg"], "foreground": p["entry_fg"], "insertcolor": p["fg"]}
            },
            "TCheckbutton": {
                "configure": {"background": p["bg"], "foreground": p["fg"], "indicatorbackground": p["entry_bg"], "indicatorforeground": p["fg"]},
                 "map": {"background": [("active", p["bg"])]}
            },
            "TCombobox": {
                "configure": {"fieldbackground": p["entry_bg"], "foreground": p["entry_fg"], "arrowcolor": p["fg"]},
                "map": {"fieldbackground": [("readonly", p["entry_bg"])]}
            },
            "Treeview": {
                "configure": {"background": p["entry_bg"], "foreground": p["fg"], "fieldbackground": p["entry_bg"]},
                "map": {"background": [("selected", p["select_bg"])], "foreground": [("selected", p["select_fg"])]}
            },
            "Treeview.Heading": {
                "configure": {"background": p["btn_bg"], "foreground": p["btn_fg"], "relief": "flat"}
            },
            "Success.TButton": {
                "configure": {"background": p["success"], "foreground": "#ffffff"},
                "map": {"background": [("active", "#43A047"), ("disabled", p["disabled"])]}
            },
            "Danger.TButton": {
                 "configure": {"background": p["danger"], "foreground": "#ffffff"},
                 "map": {"background": [("active", "#E53935"), ("disabled", p["disabled"])]}
            }
        })

def get_palette(theme_name):
    """Returns the color palette for manual coloring of non-ttk widgets"""
    name = theme_name.replace("pro_", "")
    return PALETTES.get(name, PALETTES["dark"])
