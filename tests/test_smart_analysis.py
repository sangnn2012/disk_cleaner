"""Unit tests for smart_analysis module."""

import unittest
import time
import os

from scanner import FileInfo
from analyzer import analyze_files
from smart_analysis import (
    find_temp_files, find_large_folders, find_old_downloads,
    analyze_disk_usage, TEMP_PATTERNS, TEMP_EXTENSIONS, USER_TEMP_PATHS
)


class TestFindTempFiles(unittest.TestCase):
    """Tests for find_temp_files function."""

    def _make_analyzed(self, name, path, size=1000):
        """Helper to create analyzed file dict."""
        ext = os.path.splitext(name)[1].lower()
        fi = FileInfo(path, name, size, time.time(), time.time(), ext)
        return {'file_info': fi, 'category': 'Other', 'staleness_score': 0}

    def test_finds_temp_extension_files(self):
        """Test finding files with temp extensions."""
        files = [
            self._make_analyzed("file.tmp", "C:\\test\\file.tmp"),
            self._make_analyzed("file.bak", "C:\\test\\file.bak"),
            self._make_analyzed("file.log", "C:\\test\\file.log"),
            self._make_analyzed("file.txt", "C:\\test\\file.txt"),
        ]

        result = find_temp_files(files)

        temp_names = [f['file_info'].name for f in result]
        self.assertIn("file.tmp", temp_names)
        self.assertIn("file.bak", temp_names)
        self.assertIn("file.log", temp_names)
        self.assertNotIn("file.txt", temp_names)

    def test_finds_files_in_temp_folders(self):
        """Test finding files in temp folders."""
        files = [
            self._make_analyzed("data.json", "C:\\Users\\test\\AppData\\Local\\Temp\\data.json"),
            self._make_analyzed("cache.dat", "C:\\project\\.cache\\cache.dat"),
            self._make_analyzed("module.pyc", "C:\\project\\__pycache__\\module.pyc"),
            self._make_analyzed("normal.txt", "C:\\Documents\\normal.txt"),
        ]

        result = find_temp_files(files)

        self.assertEqual(len(result), 3)
        names = [f['file_info'].name for f in result]
        self.assertNotIn("normal.txt", names)

    def test_finds_node_modules(self):
        """Test finding files in node_modules."""
        files = [
            self._make_analyzed("index.js", "C:\\project\\node_modules\\lodash\\index.js"),
        ]

        result = find_temp_files(files)
        self.assertEqual(len(result), 1)

    def test_empty_list(self):
        """Test with empty file list."""
        result = find_temp_files([])
        self.assertEqual(result, [])


class TestFindLargeFolders(unittest.TestCase):
    """Tests for find_large_folders function."""

    def _make_analyzed(self, path, size):
        """Helper to create analyzed file dict."""
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        fi = FileInfo(path, name, size, time.time(), time.time(), ext)
        return {'file_info': fi, 'category': 'Other', 'staleness_score': 0}

    def test_finds_large_folders(self):
        """Test finding folders over 1GB."""
        # Create files that sum to > 1GB in one folder
        files = []
        for i in range(10):
            files.append(self._make_analyzed(
                f"C:\\LargeFolder\\file{i}.dat",
                200 * 1024 * 1024  # 200 MB each = 2 GB total
            ))

        # Add small folder
        files.append(self._make_analyzed("C:\\SmallFolder\\file.txt", 1000))

        result = find_large_folders(files, min_size_gb=1.0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "C:\\LargeFolder")
        self.assertEqual(result[0][2], 10)  # file count

    def test_sorted_by_size(self):
        """Test that results are sorted by size descending."""
        files = []
        # Folder A: 1.5 GB
        for i in range(15):
            files.append(self._make_analyzed(
                f"C:\\FolderA\\file{i}.dat",
                100 * 1024 * 1024
            ))
        # Folder B: 2 GB
        for i in range(20):
            files.append(self._make_analyzed(
                f"C:\\FolderB\\file{i}.dat",
                100 * 1024 * 1024
            ))

        result = find_large_folders(files, min_size_gb=1.0)

        self.assertEqual(len(result), 2)
        # Folder B should be first (larger)
        self.assertEqual(result[0][0], "C:\\FolderB")

    def test_custom_threshold(self):
        """Test with custom size threshold."""
        files = []
        for i in range(5):
            files.append(self._make_analyzed(
                f"C:\\Folder\\file{i}.dat",
                100 * 1024 * 1024  # 500 MB total
            ))

        # With 1GB threshold, should not find
        result = find_large_folders(files, min_size_gb=1.0)
        self.assertEqual(len(result), 0)

        # With 0.4GB threshold, should find
        result = find_large_folders(files, min_size_gb=0.4)
        self.assertEqual(len(result), 1)


class TestFindOldDownloads(unittest.TestCase):
    """Tests for find_old_downloads function."""

    def _make_analyzed(self, path, days_old):
        """Helper to create analyzed file dict."""
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()
        accessed = time.time() - (days_old * 24 * 60 * 60)
        fi = FileInfo(path, name, 1000, accessed, accessed, ext)
        return {'file_info': fi, 'category': 'Other', 'staleness_score': 0}

    def test_finds_old_downloads(self):
        """Test finding old files in Downloads folder."""
        files = [
            self._make_analyzed("C:\\Users\\test\\Downloads\\old.zip", 60),
            self._make_analyzed("C:\\Users\\test\\Downloads\\new.zip", 5),
            self._make_analyzed("C:\\Users\\test\\Documents\\old.doc", 60),
        ]

        result = find_old_downloads(files, days_old=30)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_info'].name, "old.zip")

    def test_custom_days_threshold(self):
        """Test with custom days threshold."""
        files = [
            self._make_analyzed("C:\\Downloads\\file1.zip", 15),
            self._make_analyzed("C:\\Downloads\\file2.zip", 45),
        ]

        # With 30 day threshold
        result = find_old_downloads(files, days_old=30)
        self.assertEqual(len(result), 1)

        # With 10 day threshold
        result = find_old_downloads(files, days_old=10)
        self.assertEqual(len(result), 2)

    def test_case_insensitive_path(self):
        """Test that Downloads path matching is case insensitive."""
        files = [
            self._make_analyzed("C:\\Users\\test\\DOWNLOADS\\file.zip", 60),
            self._make_analyzed("C:\\users\\test\\downloads\\file2.zip", 60),
        ]

        result = find_old_downloads(files, days_old=30)
        self.assertEqual(len(result), 2)


class TestAnalyzeDiskUsage(unittest.TestCase):
    """Tests for analyze_disk_usage function."""

    def test_returns_required_keys(self):
        """Test that result has all required keys."""
        result = analyze_disk_usage([])

        self.assertIn('temp_files', result)
        self.assertIn('large_folders', result)
        self.assertIn('old_downloads', result)
        self.assertIn('potential_savings', result)
        self.assertIn('temp_size', result)
        self.assertIn('downloads_size', result)

    def test_calculates_potential_savings(self):
        """Test that potential savings is calculated."""
        now = time.time()
        old = now - (60 * 24 * 60 * 60)

        files = [
            {
                'file_info': FileInfo(
                    "C:\\Temp\\file.tmp", "file.tmp", 1000000,
                    now, now, ".tmp"
                ),
                'category': 'Other',
                'staleness_score': 0
            },
            {
                'file_info': FileInfo(
                    "C:\\Downloads\\old.zip", "old.zip", 2000000,
                    old, old, ".zip"
                ),
                'category': 'Archive',
                'staleness_score': 0
            },
        ]

        result = analyze_disk_usage(files)

        self.assertEqual(result['temp_size'], 1000000)
        self.assertEqual(result['downloads_size'], 2000000)
        self.assertEqual(result['potential_savings'], 3000000)


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_temp_patterns_is_list(self):
        """Test that TEMP_PATTERNS is a list."""
        self.assertIsInstance(TEMP_PATTERNS, list)
        self.assertGreater(len(TEMP_PATTERNS), 0)

    def test_temp_extensions_is_set(self):
        """Test that TEMP_EXTENSIONS is a set."""
        self.assertIsInstance(TEMP_EXTENSIONS, set)
        self.assertGreater(len(TEMP_EXTENSIONS), 0)

    def test_temp_extensions_start_with_dot(self):
        """Test that all temp extensions start with dot."""
        for ext in TEMP_EXTENSIONS:
            self.assertTrue(ext.startswith('.'))

    def test_user_temp_paths_is_list(self):
        """Test that USER_TEMP_PATHS is a list."""
        self.assertIsInstance(USER_TEMP_PATHS, list)


if __name__ == '__main__':
    unittest.main()
