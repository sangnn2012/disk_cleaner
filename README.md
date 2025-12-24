# Disk Space Analyzer

A Python desktop application for analyzing disk usage and cleaning up unused files on Windows.

## Features

- **Drive Scanning** - Scan entire drives or specific folders recursively
- **File Categorization** - Automatically categorize files (Video, Audio, Image, Document, Archive, Code, Game)
- **Smart Filtering** - Filter by category, minimum size, and last access date
- **Search** - Search files by name or path
- **Duplicate Finder** - Find duplicate files using MD5 hash comparison
- **Smart Analysis** - Detect temp files, old downloads, and large folders
- **Visualizations** - Pie charts, treemaps, and folder size views
- **File Operations** - Move, compress, and safely delete files to Recycle Bin
- **Export** - Export file lists to CSV or HTML reports
- **Dark Mode** - Toggle between light and dark themes
- **Filter Profiles** - Save and load filter presets
- **Exclusion List** - Protect specific paths from scanning

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- send2trash (for safe deletion)

## Installation

```bash
# Clone the repository
git clone git@github.com:sangnn2012/disk_cleaner.git
cd disk_cleaner

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Usage

```bash
# Run directly
python main.py

# Or if installed as a package
disk-cleaner
```

### Quick Start

1. Click **Scan Drives** to select drives to analyze
2. Wait for the scan to complete
3. Use filters to narrow down results (category, size, age)
4. Select files and use **Delete Selected** to move them to Recycle Bin

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Scan |
| `Ctrl+A` | Select All |
| `F5` | Refresh/Apply Filters |
| `Delete` | Delete Selected |

## Project Structure

```
disk_cleaner/
├── main.py              # Entry point
├── scanner.py           # File system scanning
├── analyzer.py          # File categorization
├── utils.py             # Utility functions
├── duplicate_finder.py  # Duplicate detection
├── file_operations.py   # Move, compress, export
├── smart_analysis.py    # Temp files, old downloads
├── theme_manager.py     # Dark/light mode
├── ui/                  # UI components
│   ├── main_window.py
│   ├── file_table.py
│   ├── preview_pane.py
│   ├── dialogs.py
│   ├── visualizations.py
│   ├── duplicate_view.py
│   └── smart_analysis_view.py
└── tests/               # Unit tests
```

## Running Tests

```bash
# Using the test runner
python run_tests.py

# Using pytest
pytest

# Run with verbose output
pytest -v
```

## License

MIT
