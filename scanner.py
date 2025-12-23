"""File system scanner for finding files and their metadata."""

import os
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Stores information about a scanned file."""
    path: str
    name: str
    size: int
    last_accessed: float
    last_modified: float
    extension: str


# System folders to skip during scanning
SKIP_FOLDERS = {
    '$Recycle.Bin',
    'System Volume Information',
    'Windows',
    'ProgramData',
    'Program Files',
    'Program Files (x86)',
    'Recovery',
    'PerfLogs',
    '$WinREAgent',
    'Config.Msi',
    'Documents and Settings',
    'MSOCache',
    'Intel',
    'AMD',
    'NVIDIA',
    'AppData',  # Skip user AppData folders
}


def scan_directory(
    root_path: str,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> list[FileInfo]:
    """
    Recursively scan a directory and collect file information.

    Args:
        root_path: Path to start scanning from
        progress_callback: Optional callback(current_path, file_count) for progress updates
        stop_flag: Optional callable that returns True to stop scanning

    Returns:
        List of FileInfo objects for all files found
    """
    files = []
    file_count = 0

    try:
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            # Check if scanning should stop
            if stop_flag and stop_flag():
                break

            # Filter out system folders
            dirnames[:] = [d for d in dirnames if d not in SKIP_FOLDERS and not d.startswith('.')]

            for filename in filenames:
                if stop_flag and stop_flag():
                    break

                filepath = os.path.join(dirpath, filename)

                try:
                    stat = os.stat(filepath)
                    file_info = FileInfo(
                        path=filepath,
                        name=filename,
                        size=stat.st_size,
                        last_accessed=stat.st_atime,
                        last_modified=stat.st_mtime,
                        extension=Path(filename).suffix.lower()
                    )
                    files.append(file_info)
                    file_count += 1

                    # Update progress every 100 files
                    if progress_callback and file_count % 100 == 0:
                        progress_callback(dirpath, file_count)

                except (PermissionError, OSError, FileNotFoundError):
                    # Skip files we can't access
                    continue

    except (PermissionError, OSError):
        # Skip directories we can't access
        pass

    # Final progress update
    if progress_callback:
        progress_callback("Scan complete", file_count)

    return files


def scan_multiple_paths(
    paths: list[str],
    progress_callback: Optional[Callable[[str, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> list[FileInfo]:
    """Scan multiple directories/drives and combine results."""
    all_files = []
    total_count = 0

    for path in paths:
        if stop_flag and stop_flag():
            break

        def wrapped_callback(current_path, count):
            if progress_callback:
                progress_callback(current_path, total_count + count)

        files = scan_directory(path, wrapped_callback, stop_flag)
        total_count += len(files)
        all_files.extend(files)

    return all_files
