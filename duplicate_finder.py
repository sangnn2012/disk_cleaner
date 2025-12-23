"""Duplicate file finder using content hashing."""

import hashlib
import os
from collections import defaultdict
from typing import Callable, Optional
from scanner import FileInfo


def calculate_file_hash(filepath: str, chunk_size: int = 8192, partial: bool = False) -> str:
    """
    Calculate MD5 hash of a file.

    Args:
        filepath: Path to the file
        chunk_size: Size of chunks to read
        partial: If True, only hash first 4KB (for quick comparison)

    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.md5()

    try:
        with open(filepath, 'rb') as f:
            if partial:
                # Only read first 4KB for quick comparison
                data = f.read(4096)
                hasher.update(data)
            else:
                # Read entire file
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    hasher.update(data)
        return hasher.hexdigest()
    except (IOError, PermissionError, OSError):
        return ""


def find_duplicates(
    files: list,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> dict:
    """
    Find duplicate files based on content hash.

    Args:
        files: List of file dicts from analyzer
        progress_callback: Optional callback(stage, current, total)
        stop_flag: Optional callable that returns True to stop

    Returns:
        Dict mapping hash -> list of duplicate file dicts
    """
    duplicates = {}

    if not files:
        return duplicates

    # Stage 1: Group by size (files must be same size to be duplicates)
    if progress_callback:
        progress_callback("Grouping by size", 0, len(files))

    size_groups = defaultdict(list)
    for i, file_dict in enumerate(files):
        if stop_flag and stop_flag():
            return duplicates
        size = file_dict['file_info'].size
        if size > 0:  # Skip empty files
            size_groups[size].append(file_dict)

        if progress_callback and i % 100 == 0:
            progress_callback("Grouping by size", i, len(files))

    # Filter to only groups with 2+ files
    potential_duplicates = [
        group for group in size_groups.values()
        if len(group) >= 2
    ]

    if not potential_duplicates:
        return duplicates

    # Count total files to check
    total_to_check = sum(len(group) for group in potential_duplicates)
    checked = 0

    # Stage 2: Calculate partial hashes for quick comparison
    if progress_callback:
        progress_callback("Calculating partial hashes", 0, total_to_check)

    for size_group in potential_duplicates:
        if stop_flag and stop_flag():
            return duplicates

        partial_hash_groups = defaultdict(list)

        for file_dict in size_group:
            if stop_flag and stop_flag():
                return duplicates

            path = file_dict['file_info'].path
            partial_hash = calculate_file_hash(path, partial=True)

            if partial_hash:
                partial_hash_groups[partial_hash].append(file_dict)

            checked += 1
            if progress_callback and checked % 50 == 0:
                progress_callback("Calculating partial hashes", checked, total_to_check)

        # Stage 3: Full hash for files with matching partial hashes
        for partial_hash, matching_files in partial_hash_groups.items():
            if len(matching_files) < 2:
                continue

            if stop_flag and stop_flag():
                return duplicates

            full_hash_groups = defaultdict(list)

            for file_dict in matching_files:
                path = file_dict['file_info'].path
                full_hash = calculate_file_hash(path, partial=False)

                if full_hash:
                    full_hash_groups[full_hash].append(file_dict)

            # Add actual duplicates to results
            for full_hash, dup_files in full_hash_groups.items():
                if len(dup_files) >= 2:
                    duplicates[full_hash] = dup_files

    if progress_callback:
        progress_callback("Complete", total_to_check, total_to_check)

    return duplicates


def get_duplicate_stats(duplicates: dict) -> dict:
    """
    Calculate statistics about duplicates.

    Returns:
        Dict with stats: total_groups, total_files, wasted_space
    """
    total_groups = len(duplicates)
    total_files = sum(len(files) for files in duplicates.values())
    wasted_space = 0

    for files in duplicates.values():
        if len(files) >= 2:
            # Size of duplicates (keeping one original)
            file_size = files[0]['file_info'].size
            wasted_space += file_size * (len(files) - 1)

    return {
        'total_groups': total_groups,
        'total_files': total_files,
        'wasted_space': wasted_space
    }
