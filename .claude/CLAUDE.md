# Disk Space Analyzer

A Python desktop application for analyzing disk usage and cleaning up unused files.

## Tech Stack

- **Language**: Python 3.8+
- **GUI**: tkinter + ttk (standard library)
- **Testing**: unittest (standard library), pytest compatible
- **Dependencies**: send2trash (optional, for safe deletion to recycle bin)

## Project Structure

```
disk_cleaner/
├── main.py              # Entry point
├── scanner.py           # File system scanning
├── analyzer.py          # File categorization and analysis
├── utils.py             # Utility functions (formatting, dates)
├── duplicate_finder.py  # Duplicate file detection
├── file_operations.py   # Move, compress, export operations
├── smart_analysis.py    # Temp files, old downloads detection
├── theme_manager.py     # Dark/light mode theming
├── ui/                  # UI components
│   ├── main_window.py   # Main application window
│   ├── file_table.py    # File list treeview
│   ├── preview_pane.py  # File preview panel
│   ├── dialogs.py       # Dialog windows
│   ├── visualizations.py
│   ├── duplicate_view.py
│   └── smart_analysis_view.py
├── tests/               # Unit tests
│   ├── conftest.py      # Pytest configuration
│   └── test_*.py        # Test modules
├── requirements.txt     # Dependencies
└── pyproject.toml       # Package configuration
```

## Running the Application

```bash
# Direct execution
python main.py

# Or as installed package
pip install -e .
disk-cleaner
```

## Running Tests

```bash
# Using the test runner
python run_tests.py

# Using pytest
pytest

# Run specific test file
pytest tests/test_analyzer.py -v
```

## Key Modules

- **scanner.py**: `FileInfo` dataclass, `scan_directory()` for recursive file discovery
- **analyzer.py**: `CATEGORIES` dict for file type mapping, `categorize_file()`, `filter_files()`
- **utils.py**: `format_size()`, `format_date()`, `days_since()`

## Configuration Files

- `settings.json` - User preferences (dark mode, window geometry)
- `exclusions.json` - Paths excluded from scanning
- `profiles.json` - Saved filter presets

## Code Conventions

- Type hints used throughout (Python 3.8+ style: `list[FileInfo]`)
- Docstrings for all public functions
- snake_case naming
- Classes use PascalCase
