import tkinter as tk
import customtkinter as ctk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        except Exception:
            return

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Determine colors based on appearance mode to ensure visibility
        # or just rely on CTk default which handles it.

        frame = ctk.CTkFrame(tw, corner_radius=6, border_width=1)
        frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(frame, text=self.text, padx=10, pady=5, font=("Arial", 12))
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
