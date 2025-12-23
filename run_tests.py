#!/usr/bin/env python
"""Run all unit tests for the disk cleaner application."""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Discover and run all tests."""
    # Get the tests directory
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir, pattern='test_*.py')

    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
