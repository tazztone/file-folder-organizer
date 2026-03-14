import unittest

from pro_file_organizer.ui.themes import themes


class TestThemes(unittest.TestCase):
    def test_colors_exist(self):
        self.assertIn("bg_main", themes.LIGHT_COLORS)
        self.assertIn("accent", themes.LIGHT_COLORS)
        self.assertIn("bg_main", themes.DARK_COLORS)
        self.assertIn("accent", themes.DARK_COLORS)

        # Verify hex strings
        self.assertTrue(themes.LIGHT_COLORS["bg_main"].startswith("#"))
        self.assertTrue(themes.DARK_COLORS["bg_main"].startswith("#"))

    def test_fonts_exist(self):
        self.assertIn("title", themes.FONTS)
        self.assertIn("main", themes.FONTS)

        for name, font in themes.FONTS.items():
            self.assertIsInstance(font, tuple, f"Font '{name}' must be a tuple")
            self.assertGreaterEqual(len(font), 2, f"Font '{name}' tuple too short")

    def test_radii_exist(self):
        self.assertIn("standard", themes.RADII)
        self.assertIn("card", themes.RADII)

    def test_build_stylesheet(self):
        qss = themes.build_stylesheet(themes.DARK_COLORS)
        self.assertIn("QMainWindow", qss)
        self.assertIn(themes.DARK_COLORS["bg_main"], qss)
        self.assertIn(str(themes.RADII["card"]), qss)

    def test_get_font_style(self):
        style = themes.get_font_style("title")
        self.assertIn("font-family: 'Inter'", style)
        self.assertIn("font-size: 20px", style)
        self.assertIn("font-weight: bold", style)


if __name__ == "__main__":
    unittest.main()
