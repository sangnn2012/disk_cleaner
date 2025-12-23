"""Utility functions for the disk cleaner app."""

from datetime import datetime


def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    elif size_bytes < 1024 ** 4:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    else:
        return f"{size_bytes / (1024 ** 4):.2f} TB"


def format_date(timestamp: float) -> str:
    """Convert timestamp to readable date string."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError):
        return "Unknown"


def days_since(timestamp: float) -> int:
    """Calculate days since a timestamp."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        delta = datetime.now() - dt
        return delta.days
    except (ValueError, OSError):
        return 0


def get_available_drives() -> list:
    """Get list of available drive letters on Windows."""
    import string
    import os

    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives
