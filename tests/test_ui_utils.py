import unittest
import sys
import importlib
from unittest.mock import MagicMock

# Mock modules
if 'tkinter' not in sys.modules:
    sys.modules['tkinter'] = MagicMock()
if 'customtkinter' not in sys.modules:
    sys.modules['customtkinter'] = MagicMock()

import ui_utils

class TestToolTip(unittest.TestCase):
    def setUp(self):
        importlib.reload(ui_utils)
        self.mock_widget = MagicMock()
        self.mock_widget.winfo_rootx.return_value = 100
        self.mock_widget.winfo_rooty.return_value = 100
        self.mock_widget.winfo_height.return_value = 50

    def test_init_binds_events(self):
        tooltip = ui_utils.ToolTip(self.mock_widget, "Help Text")

        self.mock_widget.bind.assert_any_call("<Enter>", tooltip.show_tip)
        self.mock_widget.bind.assert_any_call("<Leave>", tooltip.hide_tip)

    def test_show_tip_creates_window(self):
        tooltip = ui_utils.ToolTip(self.mock_widget, "Help Text")

        # Simulate Enter
        tooltip.show_tip()

        # Should create Toplevel
        self.assertIsNotNone(tooltip.tip_window)
        # sys.modules['tkinter'].Toplevel should be called
        sys.modules['tkinter'].Toplevel.assert_called()

    def test_hide_tip_destroys_window(self):
        tooltip = ui_utils.ToolTip(self.mock_widget, "Help Text")
        tooltip.show_tip()

        mock_window = tooltip.tip_window

        tooltip.hide_tip()

        mock_window.destroy.assert_called_once()
        self.assertIsNone(tooltip.tip_window)

    def test_show_tip_no_text(self):
        tooltip = ui_utils.ToolTip(self.mock_widget, "")
        tooltip.show_tip()
        self.assertIsNone(tooltip.tip_window)

if __name__ == "__main__":
    unittest.main()
