import unittest
from unittest.mock import MagicMock, patch
import shutil
import tempfile
import os
import json
from pathlib import Path
from pro_file_organizer.core.organizer import FileOrganizer

class TestFileOrganizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content="test"):
        path = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return Path(path)

    def test_get_unique_path(self):
        self.create_file("test.txt")
        p = Path(self.test_dir) / "test.txt"
        unique_p = self.organizer.get_unique_path(p)
        self.assertEqual(unique_p, Path(self.test_dir) / "test_1.txt")

    def test_organize_basic(self):
        self.create_file("image.jpg")
        self.create_file("doc.pdf")

        stats = self.organizer.organize_files(Path(self.test_dir))

        self.assertEqual(stats["moved"], 2)
        self.assertTrue((Path(self.test_dir) / "Images" / "image.jpg").exists())
        self.assertTrue((Path(self.test_dir) / "Documents" / "doc.pdf").exists())

    def test_dry_run(self):
        self.create_file("image.jpg")

        stats = self.organizer.organize_files(Path(self.test_dir), dry_run=True)

        self.assertEqual(stats["moved"], 1)
        # File should NOT have moved
        self.assertTrue((Path(self.test_dir) / "image.jpg").exists())
        self.assertFalse((Path(self.test_dir) / "Images" / "image.jpg").exists())

    def test_recursive(self):
        self.create_file("sub/image.png")

        self.organizer.organize_files(Path(self.test_dir), recursive=True)

        self.assertTrue((Path(self.test_dir) / "Images" / "image.png").exists())

    def test_date_sort(self):
        f = self.create_file("photo.jpg")
        ts = 1672574400 # 2023-01-01
        os.utime(f, (ts, ts))

        self.organizer.organize_files(Path(self.test_dir), date_sort=True)

        self.assertTrue((Path(self.test_dir) / "Images" / "2023").exists())

    def test_delete_empty(self):
        os.makedirs(os.path.join(self.test_dir, "empty"))
        self.organizer.organize_files(Path(self.test_dir), del_empty=True)
        self.assertFalse((Path(self.test_dir) / "empty").exists())

    def test_undo(self):
        self.create_file("doc.txt")
        self.organizer.organize_files(Path(self.test_dir))

        self.assertFalse((Path(self.test_dir) / "doc.txt").exists())

        self.organizer.undo_changes()

        self.assertTrue((Path(self.test_dir) / "doc.txt").exists())

    def test_custom_config(self):
        config = {"Custom": [".xyz"]}
        config_path = os.path.join(self.test_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        self.organizer.load_config(config_path)
        self.create_file("test.xyz")

        self.organizer.organize_files(Path(self.test_dir))

        self.assertTrue((Path(self.test_dir) / "Custom" / "test.xyz").exists())

    def test_stop_cancellation(self):
        self.create_file("file1.txt")
        self.create_file("file2.txt")
        self.create_file("file3.txt")

        # Stop after 1st file
        processed_count = 0
        def check_stop():
            nonlocal processed_count
            processed_count += 1
            return processed_count > 1

        stats = self.organizer.organize_files(Path(self.test_dir), check_stop=check_stop)

        # Should have moved at most 1 file because check_stop runs at start of loop
        self.assertEqual(stats["moved"], 1)

    def test_rollback_on_error(self):
        self.create_file("file1.txt")
        self.create_file("file2.txt")
        
        # Mock shutil.move to fail on the second file
        original_move = shutil.move
        def side_effect(src, dst):
            if "file2.txt" in str(src):
                raise PermissionError("Access Denied")
            return original_move(src, dst)
        
        import unittest.mock as mock
        with mock.patch("shutil.move", side_effect=side_effect):
            stats = self.organizer.organize_files(Path(self.test_dir), rollback_on_error=True)
            self.assertTrue(stats.get("rolled_back", False))
            
            # Both files should be back in the root
            self.assertTrue((Path(self.test_dir) / "file1.txt").exists())
            self.assertTrue((Path(self.test_dir) / "file2.txt").exists())

    def test_deep_collision(self):
        # Create many files that would collide
        for i in range(5):
            self.create_file("test.txt")
            # Move it to Documents manually to simulate collision
            dest = Path(self.test_dir) / "Documents" / "test.txt"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if i == 0:
                os.rename(os.path.join(self.test_dir, "test.txt"), dest)
            else:
                unique_dest = self.organizer.get_unique_path(dest)
                os.rename(os.path.join(self.test_dir, "test.txt"), unique_dest)

        # Now organize a new file with same name
        self.create_file("test.txt")
        self.organizer.organize_files(Path(self.test_dir))
        
        # Should have test_5.txt
        self.assertTrue((Path(self.test_dir) / "Documents" / "test_5.txt").exists())

    def test_undo_nested(self):
        # Test undo with date sorting (deep nesting)
        f = self.create_file("photo.jpg")
        ts = 1672574400 # 2023-01-01
        os.utime(f, (ts, ts))
        
        self.organizer.organize_files(Path(self.test_dir), date_sort=True)
        self.assertTrue((Path(self.test_dir) / "Images" / "2023" / "January" / "photo.jpg").exists())
        
        self.organizer.undo_changes()
        self.assertTrue((Path(self.test_dir) / "photo.jpg").exists())
        # The folders should be cleaned up
        self.assertFalse((Path(self.test_dir) / "Images").exists())

    def test_validate_config_errors(self):
        self.organizer.directories[""] = [".ext"] # Empty category
        self.organizer.directories["Bad/Cat"] = [".ext2"] # Path separator
        errors = self.organizer.validate_config()
        self.assertTrue(any("empty" in e.lower() for e in errors))
        self.assertTrue(any("separator" in e.lower() for e in errors))

    def test_organize_with_ml(self):
        self.create_file("unknown.ext")
        mock_ml = MagicMock()
        mock_ml.models_loaded = True
        mock_ml.smart_categorize.return_value = ("Images", 0.9, "image-ml")
        
        # Patch where it is IMPORTED from, as it is a local import in organizer.py
        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer', return_value=mock_ml):
            self.organizer.organize_files(Path(self.test_dir), use_ml=True)
            self.assertTrue((Path(self.test_dir) / "Images" / "unknown.ext").exists())

    def test_recursive_exclusions(self):
        self.create_file(".git/config")
        self.create_file("venv/activate")
        self.create_file("source.txt")
        
        # Scan files should NOT return files in .git or venv
        files = list(self.organizer.scan_files(Path(self.test_dir), recursive=True))
        filenames = [f.name for f in files]
        self.assertIn("source.txt", filenames)
        self.assertNotIn("config", filenames)
        self.assertNotIn("activate", filenames)

    def test_event_callbacks(self):
        self.create_file("test.txt")
        callback = MagicMock()
        self.organizer.organize_files(Path(self.test_dir), event_callback=callback)
        
        # Verify callback was called with move data
        callback.assert_called()
        last_call_args = callback.call_args[0][0]
        self.assertEqual(last_call_args["type"], "move")
        self.assertEqual(last_call_args["file"], "test.txt")

    def test_load_save_config_robust(self):
        # Malformed JSON
        config_path = os.path.join(self.test_dir, "bad.json")
        with open(config_path, "w") as f:
            f.write("{ invalid json }")
        
        self.assertFalse(self.organizer.load_config(config_path))
        
        # Successful save/load path
        config_path = os.path.join(self.test_dir, "good.json")
        # Ensure organizer is in a clean state (in case other tests polluted shared DEFAULT_DIRECTORIES)
        from pro_file_organizer.core.constants import DEFAULT_DIRECTORIES
        self.organizer.directories = DEFAULT_DIRECTORIES.copy()
        
        self.assertTrue(self.organizer.save_config(config_path))
        self.assertTrue(self.organizer.load_config(config_path))

    def test_dry_run_no_undo(self):
        self.create_file("test.txt")
        self.organizer.organize_files(Path(self.test_dir), dry_run=True)
        # Undo stack should be empty
        self.assertEqual(len(self.organizer.undo_stack), 0)

    def test_progress_callback(self):
        self.create_file("f1.txt")
        self.create_file("f2.txt")
        progress = []
        def callback(curr, total, msg):
            progress.append((curr, total))
        
        self.organizer.organize_files(Path(self.test_dir), progress_callback=callback)
        self.assertIn((1, 2), progress)
        self.assertIn((2, 2), progress)

    def test_cleanup_empty_dirs(self):
        d = Path(self.test_dir) / "to_delete"
        d.mkdir()
        self.create_file("to_delete/file.txt")
        
        # Organize should move file and delete 'to_delete'
        self.organizer.organize_files(Path(self.test_dir), del_empty=True, recursive=True)
        # If it failed, check if it's actually empty
        if d.exists():
             contents = list(d.iterdir())
             print(f"DEBUG: to_delete exists and contains: {contents}")
        self.assertFalse(d.exists())

    def test_get_category_ml_fallback(self):
        # Test ML failure falling back to extension
        mock_ml = MagicMock()
        mock_ml.smart_categorize.return_value = (None, 0.0, "ml-fail")
        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer', return_value=mock_ml):
            cat, conf, method = self.organizer.get_category(Path("test.txt"), use_ml=True)
            self.assertEqual(cat, "Documents")
            self.assertEqual(method, "extension")

if __name__ == "__main__":
    unittest.main()
