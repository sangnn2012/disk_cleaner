"""Smart analysis for finding cleanable items."""

import os
from pathlib import Path
from typing import Callable, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from scanner import FileInfo


# Common temporary/cache folders
TEMP_PATTERNS = [
    'temp', 'tmp', 'cache', 'caches', '.cache',
    'temporary', '__pycache__', 'node_modules',
    '.npm', '.yarn', '.nuget', 'obj', 'bin',
    'thumbs.db', 'desktop.ini', '.ds_store',
]

# Temporary file extensions
TEMP_EXTENSIONS = {
    '.tmp', '.temp', '.bak', '.old', '.orig',
    '.log', '.dmp', '.crash', '.swp', '.swo',
}

# Windows user profile paths for temp
USER_TEMP_PATHS = [
    r'AppData\Local\Temp',
    r'AppData\Local\Microsoft\Windows\Temporary Internet Files',
    r'AppData\Local\Microsoft\Windows\INetCache',
    r'AppData\Local\Microsoft\Windows\WebCache',
    r'AppData\Local\Google\Chrome\User Data\Default\Cache',
    r'AppData\Local\Mozilla\Firefox\Profiles',
]


def find_empty_folders(
    root_paths: list,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> list:
    """
    Find empty folders that can be safely deleted.

    Returns:
        List of empty folder paths
    """
    empty_folders = []
    checked = 0

    for root_path in root_paths:
        if stop_flag and stop_flag():
            break

        try:
            for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
                if stop_flag and stop_flag():
                    break

                checked += 1
                if progress_callback and checked % 100 == 0:
                    progress_callback(dirpath, checked)

                # Skip system folders
                if any(skip in dirpath.lower() for skip in ['$recycle', 'system volume']):
                    continue

                # Check if folder is empty (no files, no subdirs with files)
                try:
                    if not filenames and not dirnames:
                        empty_folders.append(dirpath)
                    elif not filenames:
                        # Check if all subdirs are in our empty list
                        all_empty = all(
                            os.path.join(dirpath, d) in empty_folders
                            for d in dirnames
                        )
                        if all_empty:
                            empty_folders.append(dirpath)
                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            continue

    return empty_folders


def find_temp_files(files: list) -> list:
    """
    Find temporary/cache files that can be deleted.

    Args:
        files: List of file dicts from analyzer

    Returns:
        List of file dicts identified as temporary
    """
    temp_files = []

    for file_dict in files:
        file_info = file_dict['file_info']
        path_lower = file_info.path.lower()
        name_lower = file_info.name.lower()
        ext_lower = file_info.extension.lower()

        # Check extension
        if ext_lower in TEMP_EXTENSIONS:
            temp_files.append(file_dict)
            continue

        # Check path patterns
        if any(pattern in path_lower for pattern in TEMP_PATTERNS):
            temp_files.append(file_dict)
            continue

        # Check for user temp paths
        if any(temp_path.lower() in path_lower for temp_path in USER_TEMP_PATHS):
            temp_files.append(file_dict)
            continue

    return temp_files


def find_large_folders(files: list, min_size_gb: float = 1.0) -> list:
    """
    Find folders that exceed a size threshold.

    Args:
        files: List of file dicts from analyzer
        min_size_gb: Minimum size in GB to flag

    Returns:
        List of (folder_path, size, file_count) tuples
    """
    folder_stats = defaultdict(lambda: {'size': 0, 'count': 0})

    for file_dict in files:
        file_info = file_dict['file_info']
        folder = os.path.dirname(file_info.path)
        folder_stats[folder]['size'] += file_info.size
        folder_stats[folder]['count'] += 1

    min_size_bytes = min_size_gb * (1024 ** 3)

    large_folders = [
        (folder, stats['size'], stats['count'])
        for folder, stats in folder_stats.items()
        if stats['size'] >= min_size_bytes
    ]

    # Sort by size descending
    large_folders.sort(key=lambda x: x[1], reverse=True)

    return large_folders


def find_old_downloads(files: list, days_old: int = 30) -> list:
    """
    Find old files in download folders.

    Args:
        files: List of file dicts from analyzer
        days_old: Minimum age in days

    Returns:
        List of file dicts in Downloads folder older than threshold
    """
    cutoff = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff.timestamp()

    old_downloads = []

    for file_dict in files:
        file_info = file_dict['file_info']
        path_lower = file_info.path.lower()

        # Check if in Downloads folder
        if 'downloads' not in path_lower:
            continue

        # Check age
        if file_info.last_accessed < cutoff_timestamp:
            old_downloads.append(file_dict)

    return old_downloads


def analyze_disk_usage(files: list) -> dict:
    """
    Perform comprehensive disk usage analysis.

    Returns:
        Dict with analysis results
    """
    results = {
        'temp_files': find_temp_files(files),
        'large_folders': find_large_folders(files),
        'old_downloads': find_old_downloads(files),
    }

    # Calculate potential savings
    temp_size = sum(f['file_info'].size for f in results['temp_files'])
    downloads_size = sum(f['file_info'].size for f in results['old_downloads'])

    results['potential_savings'] = temp_size + downloads_size
    results['temp_size'] = temp_size
    results['downloads_size'] = downloads_size

    return results
