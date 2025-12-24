"""Unit tests for utils module."""

import unittest
import time
from datetime import datetime, timedelta

from utils import format_size, format_date, days_since, get_available_drives


class TestFormatSize(unittest.TestCase):
    """Tests for format_size function."""

    def test_bytes(self):
        """Test formatting bytes."""
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1), "1 B")
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1023), "1023 B")

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_size(1024)
        self.assertIn("KB", result)
        self.assertTrue(result.startswith("1"))

        result = format_size(1536)
        self.assertIn("KB", result)

        result = format_size(10240)
        self.assertIn("KB", result)
        self.assertTrue(result.startswith("10"))

    def test_megabytes(self):
        """Test formatting megabytes."""
        result = format_size(1024 * 1024)
        self.assertIn("MB", result)
        self.assertTrue(result.startswith("1"))

        result = format_size(1024 * 1024 * 5)
        self.assertIn("MB", result)
        self.assertTrue(result.startswith("5"))

        result = format_size(1024 * 1024 * 500)
        self.assertIn("MB", result)
        self.assertTrue(result.startswith("500"))

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        self.assertEqual(format_size(1024 ** 3), "1.00 GB")
        self.assertEqual(format_size(1024 ** 3 * 2.5), "2.50 GB")

    def test_terabytes(self):
        """Test formatting terabytes."""
        self.assertEqual(format_size(1024 ** 4), "1.00 TB")
        self.assertEqual(format_size(1024 ** 4 * 1.5), "1.50 TB")

    def test_negative_size(self):
        """Test that negative sizes are handled."""
        result = format_size(-100)
        self.assertIsInstance(result, str)


class TestFormatDate(unittest.TestCase):
    """Tests for format_date function."""

    def test_current_timestamp(self):
        """Test formatting current timestamp."""
        now = time.time()
        result = format_date(now)
        self.assertIsInstance(result, str)
        self.assertRegex(result, r'\d{4}-\d{2}-\d{2}')

    def test_old_timestamp(self):
        """Test formatting old timestamp."""
        old_time = time.time() - (365 * 24 * 60 * 60)  # 1 year ago
        result = format_date(old_time)
        self.assertIsInstance(result, str)

    def test_zero_timestamp(self):
        """Test formatting zero timestamp."""
        result = format_date(0)
        self.assertIsInstance(result, str)


class TestDaysSince(unittest.TestCase):
    """Tests for days_since function."""

    def test_current_time(self):
        """Test days since now should be 0."""
        now = time.time()
        self.assertEqual(days_since(now), 0)

    def test_one_day_ago(self):
        """Test days since yesterday."""
        one_day_ago = time.time() - (24 * 60 * 60)
        self.assertEqual(days_since(one_day_ago), 1)

    def test_one_week_ago(self):
        """Test days since one week ago."""
        one_week_ago = time.time() - (7 * 24 * 60 * 60)
        self.assertEqual(days_since(one_week_ago), 7)

    def test_30_days_ago(self):
        """Test days since 30 days ago."""
        thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
        self.assertEqual(days_since(thirty_days_ago), 30)


class TestGetAvailableDrives(unittest.TestCase):
    """Tests for get_available_drives function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_available_drives()
        self.assertIsInstance(result, list)

    def test_drives_are_strings(self):
        """Test that all drives are strings."""
        result = get_available_drives()
        for drive in result:
            self.assertIsInstance(drive, str)

    def test_drives_end_with_separator(self):
        """Test that drives end with path separator."""
        result = get_available_drives()
        for drive in result:
            self.assertTrue(drive.endswith('\\') or drive.endswith('/'))


if __name__ == '__main__':
    unittest.main()
