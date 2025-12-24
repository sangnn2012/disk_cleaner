#!/usr/bin/env python
"""Run all unit tests for the disk cleaner application.

Usage:
    python run_tests.py          # Run with unittest
    pytest                       # Run with pytest (if installed)
"""

import unittest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Discover and run all tests."""
    tests_dir = project_root / 'tests'

    loader = unittest.TestLoader()
    suite = loader.discover(str(tests_dir), pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
