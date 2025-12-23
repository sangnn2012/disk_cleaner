"""Unit tests for analyzer module."""

import unittest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import FileInfo
from analyzer import (
    categorize_file, calculate_staleness_score, analyze_files,
    filter_files, sort_files, CATEGORIES, GAME_PATHS
)


class TestCategorizeFile(unittest.TestCase):
    """Tests for categorize_file function."""

    def _make_file_info(self, name, path=None, size=1000):
        """Helper to create FileInfo objects."""
        if path is None:
            path = f"C:\\test\\{name}"
        ext = os.path.splitext(name)[1].lower()
        return FileInfo(
            path=path,
            name=name,
            size=size,
            last_accessed=time.time(),
            last_modified=time.time(),
            extension=ext
        )

    def test_video_files(self):
        """Test video file categorization."""
        for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
            fi = self._make_file_info(f"video{ext}")
            self.assertEqual(categorize_file(fi), 'Video')

    def test_audio_files(self):
        """Test audio file categorization."""
        for ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            fi = self._make_file_info(f"audio{ext}")
            self.assertEqual(categorize_file(fi), 'Audio')

    def test_image_files(self):
        """Test image file categorization."""
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            fi = self._make_file_info(f"image{ext}")
            self.assertEqual(categorize_file(fi), 'Image')

    def test_document_files(self):
        """Test document file categorization."""
        for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']:
            fi = self._make_file_info(f"document{ext}")
            self.assertEqual(categorize_file(fi), 'Document')

    def test_archive_files(self):
        """Test archive file categorization."""
        for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            fi = self._make_file_info(f"archive{ext}")
            self.assertEqual(categorize_file(fi), 'Archive')

    def test_code_files(self):
        """Test code file categorization."""
        for ext in ['.py', '.js', '.ts', '.java', '.cpp']:
            fi = self._make_file_info(f"code{ext}")
            self.assertEqual(categorize_file(fi), 'Code')

    def test_game_files_by_path(self):
        """Test game file categorization by path."""
        fi = self._make_file_info(
            "game.exe",
            path="C:\\Program Files\\Steam\\steamapps\\common\\Game\\game.exe"
        )
        self.assertEqual(categorize_file(fi), 'Game')

    def test_exe_not_in_game_path(self):
        """Test that exe outside game paths is Other."""
        fi = self._make_file_info(
            "app.exe",
            path="C:\\Users\\test\\Downloads\\app.exe"
        )
        self.assertEqual(categorize_file(fi), 'Other')

    def test_unknown_extension(self):
        """Test unknown extension returns Other."""
        fi = self._make_file_info("file.xyz")
        self.assertEqual(categorize_file(fi), 'Other')

    def test_no_extension(self):
        """Test file with no extension."""
        fi = FileInfo(
            path="C:\\test\\noext",
            name="noext",
            size=100,
            last_accessed=time.time(),
            last_modified=time.time(),
            extension=""
        )
        self.assertEqual(categorize_file(fi), 'Other')


class TestCalculateStalenessScore(unittest.TestCase):
    """Tests for calculate_staleness_score function."""

    def test_new_small_file(self):
        """Test that new small file has low staleness."""
        fi = FileInfo(
            path="test",
            name="test.txt",
            size=1024,  # 1 KB
            last_accessed=time.time(),
            last_modified=time.time(),
            extension=".txt"
        )
        score = calculate_staleness_score(fi)
        self.assertLess(score, 1)

    def test_old_large_file(self):
        """Test that old large file has high staleness."""
        old_time = time.time() - (365 * 24 * 60 * 60)  # 1 year ago
        fi = FileInfo(
            path="test",
            name="test.mp4",
            size=1024 * 1024 * 1024,  # 1 GB
            last_accessed=old_time,
            last_modified=old_time,
            extension=".mp4"
        )
        score = calculate_staleness_score(fi)
        self.assertGreater(score, 100000)  # Should be very high

    def test_staleness_increases_with_size(self):
        """Test that larger files have higher staleness."""
        old_time = time.time() - (30 * 24 * 60 * 60)  # 30 days ago

        small_file = FileInfo(
            path="test", name="small.txt", size=1024 * 1024,  # 1 MB
            last_accessed=old_time, last_modified=old_time, extension=".txt"
        )
        large_file = FileInfo(
            path="test", name="large.txt", size=1024 * 1024 * 100,  # 100 MB
            last_accessed=old_time, last_modified=old_time, extension=".txt"
        )

        self.assertGreater(
            calculate_staleness_score(large_file),
            calculate_staleness_score(small_file)
        )


class TestAnalyzeFiles(unittest.TestCase):
    """Tests for analyze_files function."""

    def setUp(self):
        """Create test FileInfo objects."""
        self.files = [
            FileInfo("C:\\test\\video.mp4", "video.mp4", 1000000, time.time(), time.time(), ".mp4"),
            FileInfo("C:\\test\\doc.pdf", "doc.pdf", 50000, time.time(), time.time(), ".pdf"),
            FileInfo("C:\\test\\code.py", "code.py", 1000, time.time(), time.time(), ".py"),
        ]

    def test_analyze_returns_list(self):
        """Test that analyze returns a list."""
        result = analyze_files(self.files)
        self.assertIsInstance(result, list)

    def test_analyze_returns_dicts(self):
        """Test that analyze returns list of dicts."""
        result = analyze_files(self.files)
        for item in result:
            self.assertIsInstance(item, dict)

    def test_analyzed_has_required_keys(self):
        """Test that analyzed items have required keys."""
        result = analyze_files(self.files)
        for item in result:
            self.assertIn('file_info', item)
            self.assertIn('category', item)
            self.assertIn('staleness_score', item)

    def test_analyze_preserves_file_info(self):
        """Test that original FileInfo is preserved."""
        result = analyze_files(self.files)
        self.assertEqual(result[0]['file_info'].name, "video.mp4")
        self.assertEqual(result[1]['file_info'].name, "doc.pdf")

    def test_analyze_assigns_categories(self):
        """Test that categories are assigned correctly."""
        result = analyze_files(self.files)
        categories = [item['category'] for item in result]
        self.assertIn('Video', categories)
        self.assertIn('Document', categories)
        self.assertIn('Code', categories)


class TestFilterFiles(unittest.TestCase):
    """Tests for filter_files function."""

    def setUp(self):
        """Create analyzed test data."""
        now = time.time()
        old = now - (60 * 24 * 60 * 60)  # 60 days ago

        self.files = [
            FileInfo("C:\\test\\big_video.mp4", "big_video.mp4", 500 * 1024 * 1024, old, old, ".mp4"),
            FileInfo("C:\\test\\small_video.mp4", "small_video.mp4", 10 * 1024 * 1024, now, now, ".mp4"),
            FileInfo("C:\\test\\old_doc.pdf", "old_doc.pdf", 1 * 1024 * 1024, old, old, ".pdf"),
            FileInfo("C:\\test\\new_doc.pdf", "new_doc.pdf", 2 * 1024 * 1024, now, now, ".pdf"),
        ]
        self.analyzed = analyze_files(self.files)

    def test_filter_by_category(self):
        """Test filtering by category."""
        result = filter_files(self.analyzed, categories=['Video'])
        self.assertEqual(len(result), 2)
        for item in result:
            self.assertEqual(item['category'], 'Video')

    def test_filter_by_multiple_categories(self):
        """Test filtering by multiple categories."""
        result = filter_files(self.analyzed, categories=['Video', 'Document'])
        self.assertEqual(len(result), 4)

    def test_filter_by_min_size(self):
        """Test filtering by minimum size."""
        result = filter_files(self.analyzed, min_size=100 * 1024 * 1024)  # 100 MB
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_info'].name, "big_video.mp4")

    def test_filter_by_min_days(self):
        """Test filtering by minimum days old."""
        result = filter_files(self.analyzed, min_days_old=30)
        self.assertEqual(len(result), 2)  # big_video and old_doc

    def test_filter_combined(self):
        """Test combining multiple filters."""
        result = filter_files(
            self.analyzed,
            categories=['Video'],
            min_size=100 * 1024 * 1024,
            min_days_old=30
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_info'].name, "big_video.mp4")

    def test_filter_no_match(self):
        """Test filter that matches nothing."""
        result = filter_files(self.analyzed, min_size=10 * 1024 * 1024 * 1024)  # 10 GB
        self.assertEqual(len(result), 0)

    def test_filter_all_categories(self):
        """Test filtering with categories=None returns all."""
        result = filter_files(self.analyzed, categories=None)
        self.assertEqual(len(result), 4)


class TestSortFiles(unittest.TestCase):
    """Tests for sort_files function."""

    def setUp(self):
        """Create analyzed test data."""
        now = time.time()
        old = now - (30 * 24 * 60 * 60)

        self.files = [
            FileInfo("C:\\a.mp4", "a.mp4", 100, now, now, ".mp4"),
            FileInfo("C:\\b.mp4", "b.mp4", 300, old, old, ".mp4"),
            FileInfo("C:\\c.mp4", "c.mp4", 200, now, now, ".mp4"),
        ]
        self.analyzed = analyze_files(self.files)

    def test_sort_by_size_descending(self):
        """Test sorting by size descending."""
        result = sort_files(self.analyzed, sort_by='size', reverse=True)
        sizes = [item['file_info'].size for item in result]
        self.assertEqual(sizes, [300, 200, 100])

    def test_sort_by_size_ascending(self):
        """Test sorting by size ascending."""
        result = sort_files(self.analyzed, sort_by='size', reverse=False)
        sizes = [item['file_info'].size for item in result]
        self.assertEqual(sizes, [100, 200, 300])

    def test_sort_by_name(self):
        """Test sorting by name."""
        result = sort_files(self.analyzed, sort_by='name', reverse=False)
        names = [item['file_info'].name for item in result]
        self.assertEqual(names, ['a.mp4', 'b.mp4', 'c.mp4'])

    def test_sort_by_staleness(self):
        """Test sorting by staleness score."""
        result = sort_files(self.analyzed, sort_by='staleness', reverse=True)
        # b.mp4 should be first (old + larger)
        self.assertEqual(result[0]['file_info'].name, 'b.mp4')


class TestCategories(unittest.TestCase):
    """Tests for CATEGORIES constant."""

    def test_categories_is_dict(self):
        """Test that CATEGORIES is a dictionary."""
        self.assertIsInstance(CATEGORIES, dict)

    def test_all_categories_have_extensions(self):
        """Test all categories have extension sets."""
        for cat, extensions in CATEGORIES.items():
            self.assertIsInstance(extensions, set)
            self.assertGreater(len(extensions), 0)

    def test_extensions_start_with_dot(self):
        """Test all extensions start with dot."""
        for cat, extensions in CATEGORIES.items():
            for ext in extensions:
                self.assertTrue(ext.startswith('.'), f"{ext} doesn't start with dot")


if __name__ == '__main__':
    unittest.main()
