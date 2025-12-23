"""File operations for move and compress."""

import os
import shutil
import zipfile
from typing import Callable, Optional
from datetime import datetime


def move_files(
    files: list,
    destination: str,
    keep_structure: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> dict:
    """
    Move files to a destination folder.

    Args:
        files: List of file dicts from analyzer
        destination: Destination folder path
        keep_structure: If True, maintain folder structure
        progress_callback: Optional callback(filename, current, total)
        stop_flag: Optional callable that returns True to stop

    Returns:
        Dict with stats: moved, failed, total_size
    """
    stats = {'moved': 0, 'failed': 0, 'total_size': 0, 'errors': []}

    if not os.path.isdir(destination):
        try:
            os.makedirs(destination)
        except OSError as e:
            stats['errors'].append(f"Cannot create destination: {e}")
            return stats

    total = len(files)

    for i, file_dict in enumerate(files):
        if stop_flag and stop_flag():
            break

        file_info = file_dict['file_info']
        src_path = file_info.path

        if progress_callback:
            progress_callback(file_info.name, i + 1, total)

        try:
            if keep_structure:
                # Maintain folder structure
                # Get relative path from drive root
                drive, rel_path = os.path.splitdrive(src_path)
                rel_path = rel_path.lstrip(os.sep)
                dest_path = os.path.join(destination, rel_path)

                # Create parent directories
                dest_dir = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            else:
                # Flat move
                dest_path = os.path.join(destination, file_info.name)

                # Handle name conflicts
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(file_info.name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(
                            destination,
                            f"{base}_{counter}{ext}"
                        )
                        counter += 1

            shutil.move(src_path, dest_path)
            stats['moved'] += 1
            stats['total_size'] += file_info.size

        except (OSError, shutil.Error) as e:
            stats['failed'] += 1
            stats['errors'].append(f"{file_info.name}: {e}")

    return stats


def compress_files(
    files: list,
    archive_path: str,
    compression: int = zipfile.ZIP_DEFLATED,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None
) -> dict:
    """
    Compress files into a ZIP archive.

    Args:
        files: List of file dicts from analyzer
        archive_path: Path for the ZIP file
        compression: ZIP compression method
        progress_callback: Optional callback(filename, current, total)
        stop_flag: Optional callable that returns True to stop

    Returns:
        Dict with stats: compressed, failed, original_size, archive_size
    """
    stats = {
        'compressed': 0,
        'failed': 0,
        'original_size': 0,
        'archive_size': 0,
        'errors': []
    }

    # Ensure .zip extension
    if not archive_path.lower().endswith('.zip'):
        archive_path += '.zip'

    total = len(files)

    try:
        with zipfile.ZipFile(archive_path, 'w', compression) as zf:
            for i, file_dict in enumerate(files):
                if stop_flag and stop_flag():
                    break

                file_info = file_dict['file_info']

                if progress_callback:
                    progress_callback(file_info.name, i + 1, total)

                try:
                    # Use relative path as archive name
                    drive, rel_path = os.path.splitdrive(file_info.path)
                    arcname = rel_path.lstrip(os.sep)

                    zf.write(file_info.path, arcname)
                    stats['compressed'] += 1
                    stats['original_size'] += file_info.size

                except (OSError, zipfile.BadZipFile) as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"{file_info.name}: {e}")

        # Get archive size
        if os.path.exists(archive_path):
            stats['archive_size'] = os.path.getsize(archive_path)

    except (OSError, zipfile.BadZipFile) as e:
        stats['errors'].append(f"Cannot create archive: {e}")

    return stats


def export_file_list(
    files: list,
    output_path: str,
    format: str = 'csv'
) -> bool:
    """
    Export file list to CSV or HTML.

    Args:
        files: List of file dicts from analyzer
        output_path: Output file path
        format: 'csv' or 'html'

    Returns:
        True if successful, False otherwise
    """
    try:
        if format.lower() == 'csv':
            return _export_csv(files, output_path)
        elif format.lower() == 'html':
            return _export_html(files, output_path)
        else:
            return False
    except Exception:
        return False


def _export_csv(files: list, output_path: str) -> bool:
    """Export files to CSV format."""
    import csv

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Size (bytes)', 'Size', 'Category', 'Last Accessed', 'Path'])

        for file_dict in files:
            fi = file_dict['file_info']
            from utils import format_size, format_date
            writer.writerow([
                fi.name,
                fi.size,
                format_size(fi.size),
                file_dict['category'],
                format_date(fi.last_accessed),
                fi.path
            ])

    return True


def _export_html(files: list, output_path: str) -> bool:
    """Export files to HTML format."""
    from utils import format_size, format_date

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Disk Space Analysis Report</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4a90d9; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        .size { text-align: right; }
        .stats { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Disk Space Analysis Report</h1>
    <div class="stats">
        <p><strong>Generated:</strong> {date}</p>
        <p><strong>Total Files:</strong> {total_files}</p>
        <p><strong>Total Size:</strong> {total_size}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Size</th>
                <th>Category</th>
                <th>Last Accessed</th>
                <th>Path</th>
            </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
    </table>
</body>
</html>"""

    rows = []
    total_size = 0

    for file_dict in files:
        fi = file_dict['file_info']
        total_size += fi.size
        rows.append(f"""            <tr>
                <td>{fi.name}</td>
                <td class="size">{format_size(fi.size)}</td>
                <td>{file_dict['category']}</td>
                <td>{format_date(fi.last_accessed)}</td>
                <td>{fi.path}</td>
            </tr>""")

    html = html.format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_files=len(files),
        total_size=format_size(total_size),
        rows='\n'.join(rows)
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return True
