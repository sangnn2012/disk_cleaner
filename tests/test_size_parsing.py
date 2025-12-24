"""Unit tests for size parsing in main_window."""

import unittest


class TestSizeParsing(unittest.TestCase):
    """Tests for _parse_size function."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Import tkinter and create hidden root
        import tkinter as tk
        cls.root = tk.Tk()
        cls.root.withdraw()

        # Create MainWindow instance for testing
        from ui.main_window import MainWindow
        cls.app = MainWindow.__new__(MainWindow)
        cls.app._parse_size = MainWindow._parse_size.__get__(cls.app, MainWindow)

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        cls.root.destroy()

    def test_zero(self):
        """Test parsing zero."""
        self.assertEqual(self.app._parse_size("0"), 0)

    def test_bytes(self):
        """Test parsing bytes."""
        self.assertEqual(self.app._parse_size("100 B"), 100)
        self.assertEqual(self.app._parse_size("1 B"), 1)

    def test_kilobytes(self):
        """Test parsing kilobytes."""
        self.assertEqual(self.app._parse_size("1 KB"), 1024)
        self.assertEqual(self.app._parse_size("100 KB"), 100 * 1024)
        self.assertEqual(self.app._parse_size("2.5 KB"), int(2.5 * 1024))

    def test_megabytes(self):
        """Test parsing megabytes."""
        self.assertEqual(self.app._parse_size("1 MB"), 1024 * 1024)
        self.assertEqual(self.app._parse_size("50 MB"), 50 * 1024 * 1024)
        self.assertEqual(self.app._parse_size("500 MB"), 500 * 1024 * 1024)
        self.assertEqual(self.app._parse_size("100 MB"), 100 * 1024 * 1024)

    def test_gigabytes(self):
        """Test parsing gigabytes."""
        self.assertEqual(self.app._parse_size("1 GB"), 1024 ** 3)
        self.assertEqual(self.app._parse_size("2 GB"), 2 * 1024 ** 3)
        self.assertEqual(self.app._parse_size("1.5 GB"), int(1.5 * 1024 ** 3))

    def test_terabytes(self):
        """Test parsing terabytes."""
        self.assertEqual(self.app._parse_size("1 TB"), 1024 ** 4)

    def test_case_insensitive(self):
        """Test case insensitivity."""
        self.assertEqual(self.app._parse_size("500 mb"), 500 * 1024 * 1024)
        self.assertEqual(self.app._parse_size("1 Gb"), 1024 ** 3)
        self.assertEqual(self.app._parse_size("100 KB"), 100 * 1024)

    def test_no_space(self):
        """Test parsing without space."""
        self.assertEqual(self.app._parse_size("500MB"), 500 * 1024 * 1024)
        self.assertEqual(self.app._parse_size("1GB"), 1024 ** 3)

    def test_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        self.assertEqual(self.app._parse_size("  500 MB  "), 500 * 1024 * 1024)
        self.assertEqual(self.app._parse_size("1  GB"), 1024 ** 3)

    def test_invalid_returns_zero(self):
        """Test invalid input returns zero."""
        self.assertEqual(self.app._parse_size("invalid"), 0)
        self.assertEqual(self.app._parse_size("MB"), 0)
        self.assertEqual(self.app._parse_size(""), 0)

    def test_mb_not_confused_with_b(self):
        """Test that MB is not confused with B (regression test)."""
        # This was the original bug - "500 MB" was matching 'B' suffix
        self.assertEqual(self.app._parse_size("500 MB"), 500 * 1024 * 1024)
        self.assertNotEqual(self.app._parse_size("500 MB"), 0)

    def test_all_dropdown_values(self):
        """Test all values from the dropdown menu."""
        dropdown_values = [
            ("0", 0),
            ("1 MB", 1024 * 1024),
            ("10 MB", 10 * 1024 * 1024),
            ("50 MB", 50 * 1024 * 1024),
            ("100 MB", 100 * 1024 * 1024),
            ("500 MB", 500 * 1024 * 1024),
            ("1 GB", 1024 ** 3),
        ]
        for input_str, expected in dropdown_values:
            with self.subTest(input=input_str):
                self.assertEqual(
                    self.app._parse_size(input_str),
                    expected,
                    f"Failed for input: {input_str}"
                )


class TestDaysParsing(unittest.TestCase):
    """Tests for _parse_days function."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        import tkinter as tk
        cls.root = tk.Tk()
        cls.root.withdraw()

        from ui.main_window import MainWindow
        cls.app = MainWindow.__new__(MainWindow)
        cls.app._parse_days = MainWindow._parse_days.__get__(cls.app, MainWindow)

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        cls.root.destroy()

    def test_zero_days(self):
        """Test parsing zero days."""
        self.assertEqual(self.app._parse_days("0 days"), 0)

    def test_various_days(self):
        """Test parsing various day values."""
        self.assertEqual(self.app._parse_days("7 days"), 7)
        self.assertEqual(self.app._parse_days("30 days"), 30)
        self.assertEqual(self.app._parse_days("90 days"), 90)
        self.assertEqual(self.app._parse_days("180 days"), 180)
        self.assertEqual(self.app._parse_days("365 days"), 365)

    def test_invalid_returns_zero(self):
        """Test invalid input returns zero."""
        self.assertEqual(self.app._parse_days("invalid"), 0)
        self.assertEqual(self.app._parse_days(""), 0)

    def test_all_dropdown_values(self):
        """Test all values from the dropdown menu."""
        dropdown_values = [
            ("0 days", 0),
            ("7 days", 7),
            ("30 days", 30),
            ("90 days", 90),
            ("180 days", 180),
            ("365 days", 365),
        ]
        for input_str, expected in dropdown_values:
            with self.subTest(input=input_str):
                self.assertEqual(self.app._parse_days(input_str), expected)


if __name__ == '__main__':
    unittest.main()
