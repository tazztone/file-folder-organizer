import unittest
from unittest.mock import MagicMock
import sys

# Mock everything before import
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()

import app

class DebugTest(unittest.TestCase):
    def test_init(self):
        try:
            a = app.OrganizerApp()
            print("Init success")
        except StopIteration:
            print("Init failed with StopIteration")
            raise
        except Exception as e:
            print(f"Init failed with {e}")
            raise

if __name__ == "__main__":
    unittest.main()
