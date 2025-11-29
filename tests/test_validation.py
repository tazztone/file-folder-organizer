import unittest
from organizer import FileOrganizer

class TestOrganizerValidation(unittest.TestCase):
    def setUp(self):
        self.organizer = FileOrganizer()

    def test_validate_valid_config(self):
        directories = {
            "Images": [".jpg", ".png"],
            "Docs": [".txt"]
        }
        valid, errors = self.organizer.validate_config(directories)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_validate_empty_category(self):
        directories = {
            "": [".jpg"],
            "Docs": [".txt"]
        }
        valid, errors = self.organizer.validate_config(directories)
        self.assertFalse(valid)
        self.assertIn("Category name cannot be empty.", errors)

    def test_validate_invalid_extension_format(self):
        directories = {
            "Images": ["jpg", ".png"] # "jpg" missing dot
        }
        valid, errors = self.organizer.validate_config(directories)
        self.assertFalse(valid)
        self.assertTrue(any("Invalid extension format" in e for e in errors))

    def test_validate_duplicate_extensions(self):
        directories = {
            "Images": [".jpg", ".png"],
            "Photos": [".jpg"] # Duplicate .jpg
        }
        valid, errors = self.organizer.validate_config(directories)
        self.assertFalse(valid)
        self.assertTrue(any("Duplicate extension" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
