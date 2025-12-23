"""Unit tests for duplicate_finder module."""

import unittest
import tempfile
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import FileInfo
from analyzer import analyze_files
from duplicate_finder import calculate_file_hash, find_duplicates, get_duplicate_stats


class TestCalculateFileHash(unittest.TestCase):
    """Tests for calculate_file_hash function."""

    def setUp(self):
        """Create temporary test files."""
        self.temp_dir = tempfile.mkdtemp()

        # Create file with known content
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Hello World!" * 1000)

        # Create duplicate file
        self.duplicate_file = os.path.join(self.temp_dir, "duplicate.txt")
        with open(self.duplicate_file, 'w') as f:
            f.write("Hello World!" * 1000)

        # Create different file
        self.different_file = os.path.join(self.temp_dir, "different.txt")
        with open(self.different_file, 'w') as f:
            f.write("Different content!" * 1000)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_hash_returns_string(self):
        """Test that hash returns a string."""
        result = calculate_file_hash(self.test_file)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_partial_hash_returns_string(self):
        """Test that partial hash returns a string."""
        result = calculate_file_hash(self.test_file, partial=True)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_same_hash_for_identical_files(self):
        """Test that identical files have same hash."""
        hash1 = calculate_file_hash(self.test_file)
        hash2 = calculate_file_hash(self.duplicate_file)
        self.assertEqual(hash1, hash2)

    def test_different_hash_for_different_files(self):
        """Test that different files have different hash."""
        hash1 = calculate_file_hash(self.test_file)
        hash2 = calculate_file_hash(self.different_file)
        self.assertNotEqual(hash1, hash2)

    def test_partial_hash_same_for_identical_files(self):
        """Test that identical files have same partial hash."""
        hash1 = calculate_file_hash(self.test_file, partial=True)
        hash2 = calculate_file_hash(self.duplicate_file, partial=True)
        self.assertEqual(hash1, hash2)

    def test_nonexistent_file_returns_empty(self):
        """Test that nonexistent file returns empty string."""
        result = calculate_file_hash("nonexistent_file_12345.xyz")
        self.assertEqual(result, "")

    def test_hash_is_md5_format(self):
        """Test that hash is 32 character hex string (MD5)."""
        result = calculate_file_hash(self.test_file)
        self.assertEqual(len(result), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in result))


class TestFindDuplicates(unittest.TestCase):
    """Tests for find_duplicates function."""

    def setUp(self):
        """Create temporary test files."""
        self.temp_dir = tempfile.mkdtemp()

        # Create set of duplicate files
        content = "Duplicate content!" * 1000
        self.dup_files = []
        for i in range(3):
            filepath = os.path.join(self.temp_dir, f"dup_{i}.txt")
            with open(filepath, 'w') as f:
                f.write(content)
            self.dup_files.append(filepath)

        # Create unique files
        self.unique_files = []
        for i in range(2):
            filepath = os.path.join(self.temp_dir, f"unique_{i}.txt")
            with open(filepath, 'w') as f:
                f.write(f"Unique content {i}!" * 1000)
            self.unique_files.append(filepath)

        # Create FileInfo objects
        all_paths = self.dup_files + self.unique_files
        self.file_infos = []
        for path in all_paths:
            stat = os.stat(path)
            fi = FileInfo(
                path=path,
                name=os.path.basename(path),
                size=stat.st_size,
                last_accessed=stat.st_atime,
                last_modified=stat.st_mtime,
                extension=".txt"
            )
            self.file_infos.append(fi)

        self.analyzed = analyze_files(self.file_infos)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_duplicates_returns_dict(self):
        """Test that find_duplicates returns a dictionary."""
        result = find_duplicates(self.analyzed)
        self.assertIsInstance(result, dict)

    def test_finds_duplicate_group(self):
        """Test that duplicate group is found."""
        result = find_duplicates(self.analyzed)

        # Should have at least one group of duplicates
        self.assertGreater(len(result), 0)

        # At least one group should have 3 files
        has_three = any(len(files) == 3 for files in result.values())
        self.assertTrue(has_three)

    def test_unique_files_not_duplicates(self):
        """Test that unique files are not marked as duplicates."""
        result = find_duplicates(self.analyzed)

        # Unique files should not be in any group
        all_dup_paths = []
        for files in result.values():
            for f in files:
                all_dup_paths.append(f['file_info'].path)

        for unique_path in self.unique_files:
            self.assertNotIn(unique_path, all_dup_paths)

    def test_progress_callback_called(self):
        """Test that progress callback is called."""
        progress_calls = []

        def callback(msg, current, total):
            progress_calls.append((msg, current, total))

        find_duplicates(self.analyzed, progress_callback=callback)

        self.assertGreater(len(progress_calls), 0)

    def test_empty_list(self):
        """Test with empty file list."""
        result = find_duplicates([])
        self.assertEqual(result, {})


class TestGetDuplicateStats(unittest.TestCase):
    """Tests for get_duplicate_stats function."""

    def test_empty_duplicates(self):
        """Test stats for empty duplicates."""
        result = get_duplicate_stats({})
        self.assertEqual(result['total_groups'], 0)
        self.assertEqual(result['total_files'], 0)
        self.assertEqual(result['wasted_space'], 0)

    def test_calculates_wasted_space(self):
        """Test that wasted space is calculated correctly."""
        # Create mock duplicates
        fi1 = FileInfo("a.txt", "a.txt", 1000, 0, 0, ".txt")
        fi2 = FileInfo("b.txt", "b.txt", 1000, 0, 0, ".txt")
        fi3 = FileInfo("c.txt", "c.txt", 1000, 0, 0, ".txt")

        duplicates = {
            'hash1': [
                {'file_info': fi1},
                {'file_info': fi2},
                {'file_info': fi3},
            ]
        }

        result = get_duplicate_stats(duplicates)

        self.assertEqual(result['total_groups'], 1)
        self.assertEqual(result['total_files'], 3)
        # Wasted = size * (count - 1) = 1000 * 2 = 2000
        self.assertEqual(result['wasted_space'], 2000)


if __name__ == '__main__':
    unittest.main()
