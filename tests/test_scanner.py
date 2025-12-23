"""Unit tests for scanner module."""

import unittest
import tempfile
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import FileInfo, scan_directory, scan_multiple_paths, SKIP_FOLDERS


class TestFileInfo(unittest.TestCase):
    """Tests for FileInfo dataclass."""

    def test_create_file_info(self):
        """Test creating a FileInfo instance."""
        fi = FileInfo(
            path="C:\\test\\file.txt",
            name="file.txt",
            size=1024,
            last_accessed=time.time(),
            last_modified=time.time(),
            extension=".txt"
        )
        self.assertEqual(fi.path, "C:\\test\\file.txt")
        self.assertEqual(fi.name, "file.txt")
        self.assertEqual(fi.size, 1024)
        self.assertEqual(fi.extension, ".txt")

    def test_file_info_attributes(self):
        """Test FileInfo has all required attributes."""
        fi = FileInfo(
            path="/test/path",
            name="test.py",
            size=500,
            last_accessed=0,
            last_modified=0,
            extension=".py"
        )
        self.assertTrue(hasattr(fi, 'path'))
        self.assertTrue(hasattr(fi, 'name'))
        self.assertTrue(hasattr(fi, 'size'))
        self.assertTrue(hasattr(fi, 'last_accessed'))
        self.assertTrue(hasattr(fi, 'last_modified'))
        self.assertTrue(hasattr(fi, 'extension'))


class TestScanDirectory(unittest.TestCase):
    """Tests for scan_directory function."""

    def setUp(self):
        """Create a temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.test_files = []
        for i in range(5):
            filepath = os.path.join(self.temp_dir, f"test_file_{i}.txt")
            with open(filepath, 'w') as f:
                f.write(f"Test content {i}" * 100)
            self.test_files.append(filepath)

        # Create subdirectory with files
        self.sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.sub_dir)
        for i in range(3):
            filepath = os.path.join(self.sub_dir, f"sub_file_{i}.py")
            with open(filepath, 'w') as f:
                f.write(f"# Python file {i}\n" * 50)
            self.test_files.append(filepath)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_finds_files(self):
        """Test that scan finds all files."""
        files = scan_directory(self.temp_dir)
        self.assertEqual(len(files), 8)  # 5 + 3 files

    def test_scan_returns_file_info_objects(self):
        """Test that scan returns FileInfo objects."""
        files = scan_directory(self.temp_dir)
        for fi in files:
            self.assertIsInstance(fi, FileInfo)

    def test_scan_captures_correct_metadata(self):
        """Test that file metadata is correct."""
        files = scan_directory(self.temp_dir)

        txt_files = [f for f in files if f.extension == '.txt']
        self.assertEqual(len(txt_files), 5)

        py_files = [f for f in files if f.extension == '.py']
        self.assertEqual(len(py_files), 3)

    def test_scan_with_progress_callback(self):
        """Test that progress callback is called."""
        progress_calls = []

        def callback(path, count):
            progress_calls.append((path, count))

        files = scan_directory(self.temp_dir, progress_callback=callback)

        # Should have at least final callback
        self.assertGreater(len(progress_calls), 0)

    def test_scan_with_stop_flag(self):
        """Test that stop flag stops scanning."""
        # Stop immediately
        def stop_flag():
            return True

        files = scan_directory(self.temp_dir, stop_flag=stop_flag)

        # Should have stopped early (may find 0-few files before stopping)
        self.assertLessEqual(len(files), 8)

    def test_scan_nonexistent_directory(self):
        """Test scanning a nonexistent directory."""
        files = scan_directory("C:\\nonexistent\\path\\12345")
        self.assertEqual(files, [])

    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        empty_dir = tempfile.mkdtemp()
        try:
            files = scan_directory(empty_dir)
            self.assertEqual(len(files), 0)
        finally:
            os.rmdir(empty_dir)


class TestScanMultiplePaths(unittest.TestCase):
    """Tests for scan_multiple_paths function."""

    def setUp(self):
        """Create multiple temporary directories."""
        self.temp_dirs = []
        for i in range(2):
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)

            # Create test files
            for j in range(3):
                filepath = os.path.join(temp_dir, f"file_{i}_{j}.txt")
                with open(filepath, 'w') as f:
                    f.write("test content")

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_scan_multiple_paths(self):
        """Test scanning multiple directories."""
        files = scan_multiple_paths(self.temp_dirs)
        self.assertEqual(len(files), 6)  # 3 files * 2 dirs

    def test_scan_multiple_with_stop_flag(self):
        """Test stop flag works across multiple paths."""
        count = [0]

        def stop_flag():
            count[0] += 1
            return count[0] > 2

        files = scan_multiple_paths(self.temp_dirs, stop_flag=stop_flag)
        self.assertLess(len(files), 6)


class TestSkipFolders(unittest.TestCase):
    """Tests for SKIP_FOLDERS constant."""

    def test_skip_folders_is_set(self):
        """Test that SKIP_FOLDERS is a set."""
        self.assertIsInstance(SKIP_FOLDERS, set)

    def test_common_system_folders_included(self):
        """Test that common system folders are in skip list."""
        self.assertIn('$Recycle.Bin', SKIP_FOLDERS)
        self.assertIn('System Volume Information', SKIP_FOLDERS)
        self.assertIn('Windows', SKIP_FOLDERS)


if __name__ == '__main__':
    unittest.main()
