import unittest

from pro_file_organizer.ui.themes import themes


class TestThemes(unittest.TestCase):
    def test_colors_exist(self):
        self.assertIn("bg_main", themes.COLORS)
        self.assertIn("accent", themes.COLORS)
        self.assertIn("text_main", themes.COLORS)

        # Verify color tuples
        self.assertIsInstance(themes.COLORS["bg_main"], tuple)
        self.assertEqual(len(themes.COLORS["bg_main"]), 2)

    def test_fonts_exist(self):
        self.assertIn("title", themes.FONTS)
        self.assertIn("main", themes.FONTS)

        # CustomTkinter requirement: tuples of len 2 to 6
        for name, font in themes.FONTS.items():
            self.assertIsInstance(font, tuple, f"Font '{name}' must be a tuple")
            self.assertGreaterEqual(len(font), 2, f"Font '{name}' tuple too short")
            self.assertLessEqual(len(font), 6, f"Font '{name}' tuple too long (max 6)")

    def test_radii_exist(self):
        self.assertIn("standard", themes.RADII)
        self.assertIn("card", themes.RADII)


if __name__ == "__main__":
    unittest.main()
