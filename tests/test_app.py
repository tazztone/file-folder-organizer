import unittest
import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock tkinter and its submodules BEFORE importing app
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

import tkinter as tk # It's a mock now
import app

class TestOrganizerApp(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.root = MagicMock()

        # Setup specific mocks for tkinter variables needed by the app
        self.mock_var_recursive = MagicMock()
        self.mock_var_recursive.get.return_value = False

        self.mock_var_date_sort = MagicMock()
        self.mock_var_date_sort.get.return_value = False

        self.mock_var_del_empty = MagicMock()
        self.mock_var_del_empty.get.return_value = False

        # When BooleanVar() is called, return our mocks
        # The app creates 3 BooleanVars. We need to control which one is returned when.
        # But app.py instantiates them in __init__.
        # We can side_effect BooleanVar to return different mocks or just one that we configure later?
        # Simpler: After instantiation, we can replace the attributes on the instance.

        self.app = app.OrganizerApp(self.root)

        # Replace the BooleanVars with our controllable mocks
        self.app.var_recursive = self.mock_var_recursive
        self.app.var_date_sort = self.mock_var_date_sort
        self.app.var_del_empty = self.mock_var_del_empty

        # Set the selected path to our temp dir
        self.app.selected_path = Path(self.test_dir)

        # Mock the log method to avoid thread/GUI issues if any
        self.app.log = MagicMock()
        # Mock messagebox
        app.messagebox.showinfo = MagicMock()

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content="test"):
        path = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return Path(path)

    def test_get_unique_path_no_conflict(self):
        """Test getting a unique path when there is no conflict."""
        p = Path(self.test_dir) / "test.txt"
        unique_p = self.app.get_unique_path(p)
        self.assertEqual(p, unique_p)

    def test_get_unique_path_conflict(self):
        """Test getting a unique path when there is a conflict."""
        self.create_file("test.txt")
        p = Path(self.test_dir) / "test.txt"

        # Expected: test_1.txt
        expected = Path(self.test_dir) / "test_1.txt"
        unique_p = self.app.get_unique_path(p)
        self.assertEqual(unique_p, expected)

        # Create test_1.txt and try again
        self.create_file("test_1.txt")
        # Expected: test_2.txt
        expected_2 = Path(self.test_dir) / "test_2.txt"
        unique_p_2 = self.app.get_unique_path(p)
        self.assertEqual(unique_p_2, expected_2)

    def test_organize_basic(self):
        """Test basic organization of files into categories."""
        self.create_file("image.jpg")
        self.create_file("doc.pdf")
        self.create_file("script.py")
        self.create_file("unknown.xyz")

        self.app.organize_files()

        self.assertTrue((Path(self.test_dir) / "Images" / "image.jpg").exists())
        self.assertTrue((Path(self.test_dir) / "Documents" / "doc.pdf").exists())
        self.assertTrue((Path(self.test_dir) / "Code" / "script.py").exists())
        self.assertTrue((Path(self.test_dir) / "Others" / "unknown.xyz").exists())

    def test_organize_recursive(self):
        """Test recursive organization."""
        self.create_file("sub/image.png")
        self.app.var_recursive.get.return_value = True

        self.app.organize_files()

        # Should be moved to Images root folder (app logic flattens structure into categories)
        self.assertTrue((Path(self.test_dir) / "Images" / "image.png").exists())
        self.assertFalse((Path(self.test_dir) / "sub" / "image.png").exists())

    def test_organize_recursive_disabled(self):
        """Test that subfolders are ignored when recursive is disabled."""
        self.create_file("sub/image.png")
        self.app.var_recursive.get.return_value = False

        self.app.organize_files()

        # Should stay in subfolder
        self.assertTrue((Path(self.test_dir) / "sub" / "image.png").exists())
        self.assertFalse((Path(self.test_dir) / "Images" / "image.png").exists())

    def test_date_sorting(self):
        """Test sorting by date."""
        f = self.create_file("photo.jpg")

        # Set modification time to a known date (e.g., 2023-01-01)
        # Timestamp for 2023-01-01 12:00:00
        ts = 1672574400
        os.utime(f, (ts, ts))

        self.app.var_date_sort.get.return_value = True
        self.app.organize_files()

        # Expected path: Images/2023/January/photo.jpg
        # Note: Month name depends on locale, but usually English in standard envs.
        # Assuming English locale or "January"
        # Let's check safely by checking if year folder exists

        year_dir = Path(self.test_dir) / "Images" / "2023"
        self.assertTrue(year_dir.exists(), "Year folder not created")

        # Check if file is deeply nested
        # We can walk the directory to find it
        found = list(Path(self.test_dir).rglob("photo.jpg"))
        self.assertEqual(len(found), 1)
        self.assertTrue("Images" in found[0].parts)
        self.assertTrue("2023" in found[0].parts)
        # month check might be flaky if locale is different, but assuming standard environment
        # datetime.strftime("%B") uses locale's full month name.

    def test_delete_empty_folders(self):
        """Test deleting empty folders."""
        os.makedirs(os.path.join(self.test_dir, "empty_folder"))
        self.create_file("sub/file.txt") # This file will be moved, leaving "sub" empty

        self.app.var_recursive.get.return_value = True
        self.app.var_del_empty.get.return_value = True

        self.app.organize_files()

        self.assertFalse((Path(self.test_dir) / "empty_folder").exists())
        self.assertFalse((Path(self.test_dir) / "sub").exists())
        self.assertTrue((Path(self.test_dir) / "Documents" / "file.txt").exists())

    def test_undo_changes(self):
        """Test undo functionality."""
        self.create_file("doc.txt")
        original_path = Path(self.test_dir) / "doc.txt"

        # Run organization
        self.app.organize_files()
        moved_path = Path(self.test_dir) / "Documents" / "doc.txt"

        self.assertTrue(moved_path.exists())
        self.assertFalse(original_path.exists())

        # Run undo
        self.app.undo_changes()

        self.assertTrue(original_path.exists())
        self.assertFalse(moved_path.exists())

    def test_undo_recursive_cleanup(self):
        """Test undo with recursive move, ensuring original subfolders are recreated."""
        self.create_file("sub/video.mp4")
        original_path = Path(self.test_dir) / "sub" / "video.mp4"

        self.app.var_recursive.get.return_value = True
        self.app.var_del_empty.get.return_value = True # This deletes 'sub'

        self.app.organize_files()

        self.assertFalse(original_path.parent.exists()) # sub should be gone

        self.app.undo_changes()

        self.assertTrue(original_path.exists()) # sub should be recreated and file inside

    def test_organize_no_selection(self):
        """Test organize_files when no path is selected."""
        self.app.selected_path = None
        # Should just return without error
        self.app.organize_files()
        # Verify log wasn't called (or check some other side effect)
        # Logic: if not self.selected_path: return. So no logging "--- Starting Organization ---"
        self.app.log.assert_not_called()

if __name__ == "__main__":
    unittest.main()
