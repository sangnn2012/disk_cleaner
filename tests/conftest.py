"""Pytest configuration - automatically adds project root to path."""

import sys
from pathlib import Path

# Add project root to path for test imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
