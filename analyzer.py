"""File categorization and analysis logic."""

from scanner import FileInfo
from utils import days_since

# File extension categories
CATEGORIES = {
    'Video': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.3gp'},
    'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'},
    'Image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.raw', '.psd'},
    'Document': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods'},
    'Archive': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'},
    'Game': {'.exe'},  # Will be further analyzed by path
    'Code': {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb', '.php'},
}

# Known game installation paths
GAME_PATHS = [
    'steam',
    'steamapps',
    'epic games',
    'origin',
    'ubisoft',
    'games',
    'riot games',
    'battle.net',
    'gog galaxy',
    'xbox',
]


def categorize_file(file_info: FileInfo) -> str:
    """
    Determine the category of a file based on extension and path.

    Returns one of: Video, Audio, Image, Document, Archive, Game, Code, Other
    """
    ext = file_info.extension.lower()
    path_lower = file_info.path.lower()

    # Check for games first (by path)
    if ext == '.exe':
        for game_path in GAME_PATHS:
            if game_path in path_lower:
                return 'Game'

    # Check by extension
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            if category == 'Game':
                continue  # Already handled above
            return category

    return 'Other'


def calculate_staleness_score(file_info: FileInfo) -> float:
    """
    Calculate a "staleness score" for a file.
    Higher score = more likely to be deletable (large + old).

    Formula: size_in_mb * days_since_access
    """
    size_mb = file_info.size / (1024 * 1024)
    days_old = days_since(file_info.last_accessed)
    return size_mb * days_old


def analyze_files(files: list[FileInfo]) -> list[dict]:
    """
    Analyze a list of files and add category and staleness info.

    Returns list of dicts with file info plus category and staleness_score.
    """
    analyzed = []
    for file_info in files:
        analyzed.append({
            'file_info': file_info,
            'category': categorize_file(file_info),
            'staleness_score': calculate_staleness_score(file_info),
        })
    return analyzed


def filter_files(
    analyzed_files: list[dict],
    categories: list[str] = None,
    min_size: int = 0,
    min_days_old: int = 0,
) -> list[dict]:
    """
    Filter analyzed files by criteria.

    Args:
        analyzed_files: List of analyzed file dicts
        categories: List of categories to include (None = all)
        min_size: Minimum file size in bytes
        min_days_old: Minimum days since last access

    Returns:
        Filtered list of analyzed file dicts
    """
    filtered = []
    for item in analyzed_files:
        file_info = item['file_info']

        # Category filter
        if categories and item['category'] not in categories:
            continue

        # Size filter
        if file_info.size < min_size:
            continue

        # Age filter
        if days_since(file_info.last_accessed) < min_days_old:
            continue

        filtered.append(item)

    return filtered


def sort_files(
    analyzed_files: list[dict],
    sort_by: str = 'size',
    reverse: bool = True
) -> list[dict]:
    """
    Sort analyzed files by a given criterion.

    Args:
        analyzed_files: List of analyzed file dicts
        sort_by: One of 'size', 'accessed', 'staleness', 'name', 'category'
        reverse: If True, sort descending (default for size)

    Returns:
        Sorted list of analyzed file dicts
    """
    if sort_by == 'size':
        key = lambda x: x['file_info'].size
    elif sort_by == 'accessed':
        key = lambda x: x['file_info'].last_accessed
    elif sort_by == 'staleness':
        key = lambda x: x['staleness_score']
    elif sort_by == 'name':
        key = lambda x: x['file_info'].name.lower()
    elif sort_by == 'category':
        key = lambda x: x['category']
    else:
        key = lambda x: x['file_info'].size

    return sorted(analyzed_files, key=key, reverse=reverse)
