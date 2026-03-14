import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pro_file_organizer.core.organizer import FileOrganizer, OrganizationOptions


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

        stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))

        self.assertEqual(stats["moved"], 2)
        self.assertTrue((Path(self.test_dir) / "Images" / "image.jpg").exists())
        self.assertTrue((Path(self.test_dir) / "Documents" / "doc.pdf").exists())

    def test_dry_run(self):
        self.create_file("image.jpg")

        stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), dry_run=True))

        self.assertEqual(stats["moved"], 1)
        # File should NOT have moved
        self.assertTrue((Path(self.test_dir) / "image.jpg").exists())
        self.assertFalse((Path(self.test_dir) / "Images" / "image.jpg").exists())

    def test_recursive(self):
        self.create_file("sub/image.png")

        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), recursive=True))

        self.assertTrue((Path(self.test_dir) / "Images" / "image.png").exists())

    def test_date_sort(self):
        f = self.create_file("photo.jpg")
        ts = 1672574400 # 2023-01-01
        os.utime(f, (ts, ts))

        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), date_sort=True))

        self.assertTrue((Path(self.test_dir) / "Images" / "2023").exists())

    def test_delete_empty(self):
        os.makedirs(os.path.join(self.test_dir, "empty"))
        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), del_empty=True))
        self.assertFalse((Path(self.test_dir) / "empty").exists())

    def test_undo(self):
        self.create_file("doc.txt")
        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))

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

        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))

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

        stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), check_stop=check_stop))

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

        with patch("shutil.move", side_effect=side_effect):
            stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), rollback_on_error=True))
            self.assertTrue(stats.get("rolled_back", False))
            self.assertTrue((Path(self.test_dir) / "file1.txt").exists())
            self.assertTrue((Path(self.test_dir) / "file2.txt").exists())

    def test_deep_collision(self):
        for i in range(5):
            self.create_file("test.txt")
            dest = Path(self.test_dir) / "Documents" / "test.txt"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if i == 0:
                os.rename(os.path.join(self.test_dir, "test.txt"), dest)
            else:
                unique_dest = self.organizer.get_unique_path(dest)
                os.rename(os.path.join(self.test_dir, "test.txt"), unique_dest)

        self.create_file("test.txt")
        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))
        self.assertTrue((Path(self.test_dir) / "Documents" / "test_5.txt").exists())

    def test_undo_nested(self):
        f = self.create_file("photo.jpg")
        ts = 1672574400 # 2023-01-01
        os.utime(f, (ts, ts))

        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), date_sort=True))
        self.assertTrue((Path(self.test_dir) / "Images" / "2023" / "January" / "photo.jpg").exists())

        self.organizer.undo_changes()
        self.assertTrue((Path(self.test_dir) / "photo.jpg").exists())
        self.assertFalse((Path(self.test_dir) / "Images").exists())

    def test_validate_config_errors(self):
        self.organizer.directories = {"": [".ext"], "Bad/Cat": [".ext2"]}
        errors = self.organizer.validate_config()
        self.assertTrue(any("empty" in e.lower() for e in errors))
        self.assertTrue(any("separator" in e.lower() for e in errors))

    def test_organize_with_ml(self):
        self.create_file("unknown.ext")
        mock_ml = MagicMock()
        mock_ml.models_loaded = True
        mock_ml.smart_categorize.return_value = ("Images", 0.9, "image-ml")

        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer', return_value=mock_ml):
            self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), use_ml=True))
            self.assertTrue((Path(self.test_dir) / "Images" / "unknown.ext").exists())

    def test_recursive_exclusions(self):
        self.create_file(".git/config")
        self.create_file("venv/activate")
        self.create_file("source.txt")

        files = list(self.organizer.scan_files(Path(self.test_dir), recursive=True))
        filenames = [f.name for f in files]
        self.assertIn("source.txt", filenames)
        self.assertNotIn("config", filenames)
        self.assertNotIn("activate", filenames)

    def test_event_callbacks(self):
        self.create_file("test.txt")
        callback = MagicMock()
        self.organizer.organize_files(OrganizationOptions(Path(self.test_dir), event_callback=callback))
        callback.assert_called()

    def test_load_save_config_robust(self):
        config_path = os.path.join(self.test_dir, "bad.json")
        with open(config_path, "w") as f:
            f.write("{ invalid json }")
        self.assertFalse(self.organizer.load_config(config_path))

        config_path = os.path.join(self.test_dir, "good.json")
        from pro_file_organizer.core.constants import DEFAULT_DIRECTORIES
        self.organizer.directories = DEFAULT_DIRECTORIES.copy()
        self.assertTrue(self.organizer.save_config(config_path))
        self.assertTrue(self.organizer.load_config(config_path))

    def test_organize_with_ml_lazy_init(self):
        self.create_file("unknown.ext")
        mock_ml = MagicMock()
        mock_ml.models_loaded = False
        mock_ml.smart_categorize.return_value = ("Images", 0.9, "image-ml")

        log_cb = MagicMock()
        prog_cb = MagicMock()

        with patch('pro_file_organizer.core.ml_organizer.MultimodalFileOrganizer', return_value=mock_ml):
            self.organizer.organize_files(
                OrganizationOptions(
                    Path(self.test_dir),
                    use_ml=True,
                    log_callback=log_cb,
                    progress_callback=prog_cb
                )
            )
            _, kwargs = mock_ml.load_models.call_args
            prog_func = kwargs['progress_callback']
            prog_func("Loading...", 0.5)

            prog_cb.assert_called_with(0.5, 1.0, "Loading AI Models: 50%")
            log_cb.assert_any_call("[ML Init] Loading...")

    def test_scan_files_error(self):
        with patch.object(Path, 'iterdir', side_effect=Exception("Path Error")):
            stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))
            self.assertEqual(stats["moved"], 0)

    def test_duplicate_detection(self):
        self.create_file("file1.txt", content="same content")
        self.create_file("file2.txt", content="same content")
        self.create_file("file3.txt", content="different content")

        options = OrganizationOptions(Path(self.test_dir), detect_duplicates=True)
        stats = self.organizer.organize_files(options)

        self.assertEqual(stats["moved"], 2)
        self.assertEqual(stats["duplicates"], 1)
        
        # Check report
        report = stats.get("report", [])
        self.assertEqual(len(report), 3)
        statuses = [item["status"] for item in report]
        self.assertIn("duplicate", statuses)
        self.assertIn("moved", statuses)

    def test_reporting(self):
        self.create_file("image.jpg")
        self.create_file("doc.pdf")

        options = OrganizationOptions(Path(self.test_dir))
        stats = self.organizer.organize_files(options)

        self.assertIn("report", stats)
        report = stats["report"]
        self.assertEqual(len(report), 2)
        for entry in report:
            self.assertEqual(entry["status"], "moved")
            self.assertIn("file", entry)
            self.assertIn("source", entry)
            self.assertIn("destination", entry)

    def test_hashing_error(self):
        self.create_file("file.txt")
        # Mock open to fail for hashing
        with patch("builtins.open", side_effect=OSError("Read error")):
            # hashing is called inside organize_files if detect_duplicates=True
            h = self.organizer._get_file_hash(Path(self.test_dir) / "file.txt")
            self.assertEqual(h, "")

    def test_organize_permission_error(self):
        self.create_file("file.txt")
        with patch("shutil.move", side_effect=PermissionError("Permission Denied")):
            stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))
            self.assertEqual(stats["errors"], 1)
            self.assertEqual(stats["report"][0]["error_type"], "PermissionError")

    def test_organize_os_error(self):
        self.create_file("file.txt")
        with patch("shutil.move", side_effect=OSError("OS Error")):
            stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))
            self.assertEqual(stats["errors"], 1)
            self.assertEqual(stats["report"][0]["error_type"], "OSError")

    def test_mkdir_error(self):
        self.create_file("file.txt")
        with patch("pathlib.Path.mkdir", side_effect=Exception("Mkdir Error")):
            stats = self.organizer.organize_files(OrganizationOptions(Path(self.test_dir)))
            self.assertEqual(stats["errors"], 1)

if __name__ == "__main__":
    unittest.main()
