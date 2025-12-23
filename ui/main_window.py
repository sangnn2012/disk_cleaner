"""Main application window for the disk cleaner."""

import tkinter as tk
from tkinter import ttk
import threading
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import format_size, get_available_drives
from scanner import scan_multiple_paths
from analyzer import analyze_files, filter_files, CATEGORIES
from ui.file_table import FileTable
from ui.preview_pane import PreviewPane
from ui.visualizations import VisualizationWindow
from ui.duplicate_view import DuplicateFinderWindow
from ui.smart_analysis_view import SmartAnalysisWindow
from ui.dialogs import (
    DriveSelectionDialog, ask_confirmation, show_info, show_error,
    FilePropertiesDialog, ExclusionListDialog
)

from file_operations import move_files, compress_files, export_file_list
from theme_manager import ThemeManager

# Try to import send2trash for safe deletion
try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


class MainWindow:
    """Main application window."""

    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
    EXCLUSIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exclusions.json')
    PROFILES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'profiles.json')

    def __init__(self, root):
        self.root = root
        self.root.title("Disk Space Analyzer")
        self.root.geometry("1200x700")
        self.root.minsize(800, 500)

        self.all_files = []  # All scanned files
        self.filtered_files = []  # Currently displayed files
        self.exclusions = []  # Excluded paths
        self.scan_thread = None
        self.stop_scan = False

        # Load settings
        self._load_exclusions()
        self._load_settings()
        self._load_profiles()

        # Initialize theme manager
        self.theme_manager = ThemeManager(root)

        self._create_widgets()
        self._create_menu()
        self._setup_callbacks()

        # Apply theme after widgets are created
        if self.is_dark_mode:
            self.theme_manager.set_dark_mode(True)

    def _load_exclusions(self):
        """Load exclusion list from file."""
        try:
            if os.path.exists(self.EXCLUSIONS_FILE):
                with open(self.EXCLUSIONS_FILE, 'r') as f:
                    self.exclusions = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.exclusions = []

    def _save_exclusions(self):
        """Save exclusion list to file."""
        try:
            with open(self.EXCLUSIONS_FILE, 'w') as f:
                json.dump(self.exclusions, f, indent=2)
        except IOError as e:
            show_error(self.root, "Error", f"Could not save exclusions: {e}")

    def _load_settings(self):
        """Load application settings from file."""
        self.is_dark_mode = False
        self.window_geometry = None
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.is_dark_mode = settings.get('dark_mode', False)
                    self.window_geometry = settings.get('geometry', None)
                    if self.window_geometry:
                        self.root.geometry(self.window_geometry)
        except (json.JSONDecodeError, IOError):
            pass

    def _save_settings(self):
        """Save application settings to file."""
        try:
            settings = {
                'dark_mode': self.is_dark_mode,
                'geometry': self.root.geometry()
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except IOError:
            pass

    def _load_profiles(self):
        """Load filter profiles from file."""
        self.profiles = {}
        try:
            if os.path.exists(self.PROFILES_FILE):
                with open(self.PROFILES_FILE, 'r') as f:
                    self.profiles = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.profiles = {}

    def _save_profiles(self):
        """Save filter profiles to file."""
        try:
            with open(self.PROFILES_FILE, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except IOError:
            pass

    def _setup_callbacks(self):
        """Set up callbacks for file table."""
        self.file_table.on_exclude_file = self._add_to_exclusion
        self.file_table.on_show_properties = self._show_file_properties
        self.file_table.on_delete_files = self._delete_files

    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Scan", command=self._on_scan, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV...", command=self._export_csv)
        file_menu.add_command(label="Export to HTML...", command=self._export_html)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Select All", command=self.file_table.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Deselect All", command=self.file_table.deselect_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Move Selected...", command=self._move_selected)
        edit_menu.add_command(label="Compress Selected...", command=self._compress_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Exclusion List...", command=self._show_exclusion_list)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self._apply_filters, accelerator="F5")
        view_menu.add_separator()
        self.preview_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(
            label="Preview Pane",
            variable=self.preview_var,
            command=self._toggle_preview
        )
        self.dark_mode_var = tk.BooleanVar(value=self.is_dark_mode)
        view_menu.add_checkbutton(
            label="Dark Mode",
            variable=self.dark_mode_var,
            command=self._toggle_dark_mode
        )
        view_menu.add_separator()
        view_menu.add_command(label="Visualizations...", command=self._show_visualizations)
        view_menu.add_separator()
        view_menu.add_command(label="Reset Filters", command=self._reset_filters)

        # Profiles menu
        self.profiles_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Profiles", menu=self.profiles_menu)
        self.profiles_menu.add_command(label="Save Current as Profile...", command=self._save_profile)
        self.profiles_menu.add_command(label="Manage Profiles...", command=self._manage_profiles)
        self.profiles_menu.add_separator()
        self._rebuild_profiles_menu()

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Find Duplicates...", command=self._find_duplicates)
        tools_menu.add_command(label="Smart Analysis...", command=self._smart_analysis)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._on_scan())
        self.root.bind('<Control-a>', lambda e: self.file_table.select_all())
        self.root.bind('<F5>', lambda e: self._apply_filters())
        self.root.bind('<Delete>', lambda e: self._on_delete())

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Content area (file table + preview pane) - create first for toolbar references
        content_frame = ttk.Frame(main_frame)

        # Create file table first (needed by toolbar)
        self.file_table = FileTable(content_frame)

        # Create preview pane (initially visible)
        self.preview_pane = PreviewPane(content_frame, width=300)
        self.preview_visible = True

        # Now create toolbar and filters (they reference file_table)
        self._create_toolbar(main_frame)
        self._create_filters(main_frame)

        # Pack content area after toolbar/filters
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.file_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview_pane.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Bind file selection to preview update
        self.file_table.tree.bind('<<TreeviewSelect>>', self._on_file_select)

        # Bottom status bar
        self._create_statusbar(main_frame)

    def _create_toolbar(self, parent):
        """Create the top toolbar."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Scan button
        self.scan_btn = ttk.Button(
            toolbar,
            text="Scan Drives",
            command=self._on_scan
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Stop button (initially disabled)
        self.stop_btn = ttk.Button(
            toolbar,
            text="Stop",
            command=self._on_stop,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 20))

        # Selection buttons
        ttk.Button(
            toolbar,
            text="Select All",
            command=self.file_table.select_all
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Deselect All",
            command=self.file_table.deselect_all
        ).pack(side=tk.LEFT, padx=(0, 20))

        # Delete button
        self.delete_btn = ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self._on_delete
        )
        self.delete_btn.pack(side=tk.LEFT)

        if not HAS_SEND2TRASH:
            self.delete_btn.config(state=tk.DISABLED)
            ttk.Label(
                toolbar,
                text="(Install send2trash for safe deletion)",
                foreground='gray'
            ).pack(side=tk.LEFT, padx=10)

    def _create_filters(self, parent):
        """Create the filter controls."""
        filter_frame = ttk.LabelFrame(parent, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X)

        # Search bar (top row)
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40
        )
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        self.search_var.trace_add('write', lambda *args: self._on_search_change())

        ttk.Button(
            search_frame,
            text="Clear",
            command=self._clear_search,
            width=8
        ).pack(side=tk.LEFT)

        # Filter row
        filter_row = ttk.Frame(filter_frame)
        filter_row.pack(fill=tk.X)

        # Category filter
        ttk.Label(filter_row, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="All")
        categories = ["All"] + list(CATEGORIES.keys()) + ["Other"]
        category_combo = ttk.Combobox(
            filter_row,
            textvariable=self.category_var,
            values=categories,
            state='readonly',
            width=12
        )
        category_combo.pack(side=tk.LEFT, padx=(5, 20))
        category_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # Minimum size filter
        ttk.Label(filter_row, text="Min Size:").pack(side=tk.LEFT)
        self.min_size_var = tk.StringVar(value="0")
        sizes = ["0", "1 MB", "10 MB", "50 MB", "100 MB", "500 MB", "1 GB"]
        size_combo = ttk.Combobox(
            filter_row,
            textvariable=self.min_size_var,
            values=sizes,
            state='readonly',
            width=10
        )
        size_combo.pack(side=tk.LEFT, padx=(5, 20))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # Days since access filter
        ttk.Label(filter_row, text="Not accessed for:").pack(side=tk.LEFT)
        self.min_days_var = tk.StringVar(value="0 days")
        days = ["0 days", "7 days", "30 days", "90 days", "180 days", "365 days"]
        days_combo = ttk.Combobox(
            filter_row,
            textvariable=self.min_days_var,
            values=days,
            state='readonly',
            width=10
        )
        days_combo.pack(side=tk.LEFT, padx=(5, 20))
        days_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # Apply button
        ttk.Button(
            filter_row,
            text="Apply Filters",
            command=self._apply_filters
        ).pack(side=tk.LEFT, padx=10)

        # Reset button
        ttk.Button(
            filter_row,
            text="Reset",
            command=self._reset_filters
        ).pack(side=tk.LEFT)

    def _create_statusbar(self, parent):
        """Create the bottom status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.LEFT, padx=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Ready. Click 'Scan Drives' to start.")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Selection info
        self.selection_var = tk.StringVar(value="")
        ttk.Label(
            status_frame,
            textvariable=self.selection_var
        ).pack(side=tk.RIGHT)

        # Bind selection update
        self.file_table.tree.bind('<<TreeviewSelect>>', self._update_selection_info)

    def _add_to_exclusion(self, path: str):
        """Add a path to the exclusion list."""
        if path not in self.exclusions:
            self.exclusions.append(path)
            self._save_exclusions()
            show_info(self.root, "Exclusion Added", f"Added to exclusion list:\n{path}")
            # Refresh to hide excluded files
            self._apply_filters()

    def _show_exclusion_list(self):
        """Show the exclusion list management dialog."""
        def on_save(new_exclusions):
            self.exclusions = new_exclusions
            self._save_exclusions()
            self._apply_filters()

        ExclusionListDialog(self.root, self.exclusions, on_save)

    def _show_file_properties(self, file_dict: dict):
        """Show properties dialog for a file."""
        FilePropertiesDialog(self.root, file_dict)

    def _delete_files(self, file_dicts: list):
        """Delete files (called from context menu)."""
        if not HAS_SEND2TRASH:
            show_error(
                self.root,
                "Missing Dependency",
                "Please install send2trash: pip install send2trash"
            )
            return

        if not file_dicts:
            return

        total_size = sum(f['file_info'].size for f in file_dicts)
        paths = [f['file_info'].path for f in file_dicts]

        if not ask_confirmation(self.root, paths, total_size):
            return

        deleted_count = 0
        failed_count = 0

        for file_dict in file_dicts:
            path = file_dict['file_info'].path
            try:
                send2trash(path)
                deleted_count += 1
                if file_dict in self.all_files:
                    self.all_files.remove(file_dict)
            except Exception:
                failed_count += 1

        self._apply_filters()

        if failed_count == 0:
            show_info(
                self.root,
                "Deletion Complete",
                f"Successfully moved {deleted_count} file(s) to Recycle Bin.\n"
                f"Freed: {format_size(total_size)}"
            )
        else:
            show_info(
                self.root,
                "Deletion Complete",
                f"Moved {deleted_count} file(s) to Recycle Bin.\n"
                f"Failed to delete {failed_count} file(s)."
            )

    def _is_excluded(self, path: str) -> bool:
        """Check if a path is in the exclusion list."""
        path_lower = path.lower()
        for exc in self.exclusions:
            exc_lower = exc.lower()
            if path_lower == exc_lower or path_lower.startswith(exc_lower + os.sep):
                return True
        return False

    def _on_scan(self):
        """Handle scan button click."""
        drives = get_available_drives()
        if not drives:
            show_error(self.root, "Error", "No drives found!")
            return

        dialog = DriveSelectionDialog(self.root, drives)
        if not dialog.result:
            return

        selected_drives = dialog.result
        if not selected_drives:
            show_info(self.root, "Info", "No drives selected.")
            return

        self.stop_scan = False
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.file_table.clear()
        self.all_files = []
        self.progress.start(10)
        self.status_var.set("Scanning...")

        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(selected_drives,),
            daemon=True
        )
        self.scan_thread.start()

    def _scan_worker(self, drives):
        """Worker thread for scanning."""
        def progress_callback(path, count):
            self.root.after(0, lambda: self.status_var.set(
                f"Scanning... {count:,} files found. Current: {path[:50]}..."
            ))

        def stop_flag():
            return self.stop_scan

        try:
            files = scan_multiple_paths(drives, progress_callback, stop_flag)
            analyzed = analyze_files(files)
            self.root.after(0, lambda: self._scan_complete(analyzed))
        except Exception as e:
            self.root.after(0, lambda: self._scan_error(str(e)))

    def _scan_complete(self, analyzed_files):
        """Called when scan is complete."""
        self.progress.stop()
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.all_files = analyzed_files
        self.filtered_files = analyzed_files

        total_size = sum(f['file_info'].size for f in analyzed_files)

        self.status_var.set(
            f"Scan complete! Found {len(analyzed_files):,} files "
            f"({format_size(total_size)} total)"
        )

        self._apply_filters()

    def _scan_error(self, error_msg):
        """Called when scan encounters an error."""
        self.progress.stop()
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Scan error: {error_msg}")
        show_error(self.root, "Scan Error", error_msg)

    def _on_stop(self):
        """Handle stop button click."""
        self.stop_scan = True
        self.status_var.set("Stopping scan...")

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.strip().upper()
        if size_str == "0":
            return 0

        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
        }

        for suffix, mult in multipliers.items():
            if size_str.endswith(suffix):
                num = size_str[:-len(suffix)].strip()
                try:
                    return int(float(num) * mult)
                except ValueError:
                    return 0
        return 0

    def _parse_days(self, days_str: str) -> int:
        """Parse days string to integer."""
        try:
            return int(days_str.split()[0])
        except (ValueError, IndexError):
            return 0

    def _on_search_change(self):
        """Handle search text change with debounce."""
        # Cancel previous timer if exists
        if hasattr(self, '_search_timer') and self._search_timer:
            self.root.after_cancel(self._search_timer)
        # Debounce: wait 300ms before applying filter
        self._search_timer = self.root.after(300, self._apply_filters)

    def _clear_search(self):
        """Clear the search box."""
        self.search_var.set("")
        self._apply_filters()

    def _apply_filters(self):
        """Apply current filters to the file list."""
        if not self.all_files:
            return

        category = self.category_var.get()
        categories = None if category == "All" else [category]
        min_size = self._parse_size(self.min_size_var.get())
        min_days = self._parse_days(self.min_days_var.get())
        search_term = self.search_var.get().strip().lower()

        # Apply standard filters
        self.filtered_files = filter_files(
            self.all_files,
            categories=categories,
            min_size=min_size,
            min_days_old=min_days
        )

        # Apply exclusion filter
        self.filtered_files = [
            f for f in self.filtered_files
            if not self._is_excluded(f['file_info'].path)
        ]

        # Apply search filter
        if search_term:
            self.filtered_files = [
                f for f in self.filtered_files
                if search_term in f['file_info'].name.lower()
                or search_term in f['file_info'].path.lower()
            ]

        self.file_table.load_files(self.filtered_files)

        total_size = sum(f['file_info'].size for f in self.filtered_files)
        self.status_var.set(
            f"Showing {len(self.filtered_files):,} files "
            f"({format_size(total_size)} total)"
        )

    def _reset_filters(self):
        """Reset all filters to default."""
        self.category_var.set("All")
        self.min_size_var.set("0")
        self.min_days_var.set("0 days")
        self.search_var.set("")
        self._apply_filters()

    def _update_selection_info(self, event=None):
        """Update the selection info in status bar."""
        count = self.file_table.get_selected_count()
        size = self.file_table.get_selected_size()
        if count > 0:
            self.selection_var.set(f"Selected: {count} files ({format_size(size)})")
        else:
            self.selection_var.set("")

    def _on_delete(self):
        """Handle delete button click."""
        selected = self.file_table.get_selected_files()
        if selected:
            self._delete_files(selected)
        else:
            show_info(self.root, "No Selection", "Please select files to delete.")

    def _show_about(self):
        """Show about dialog."""
        show_info(
            self.root,
            "About Disk Space Analyzer",
            "Disk Space Analyzer v2.0\n\n"
            "A tool to find and delete unused files.\n\n"
            "Features:\n"
            "- Scan entire drives\n"
            "- Filter by category, size, and age\n"
            "- Right-click context menu\n"
            "- Preview pane for images\n"
            "- Exclusion list\n"
            "- Safe deletion to Recycle Bin"
        )

    def _toggle_preview(self):
        """Toggle the preview pane visibility."""
        if self.preview_var.get():
            self.preview_pane.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
            self.preview_visible = True
        else:
            self.preview_pane.pack_forget()
            self.preview_visible = False

    def _toggle_dark_mode(self):
        """Toggle dark mode on/off."""
        self.is_dark_mode = self.dark_mode_var.get()
        self.theme_manager.set_dark_mode(self.is_dark_mode)
        self._save_settings()

    def _on_file_select(self, event=None):
        """Handle file selection - update preview pane."""
        # Update selection info
        self._update_selection_info()

        # Update preview pane if visible
        if self.preview_visible:
            selected = self.file_table.get_selected_files()
            if len(selected) == 1:
                self.preview_pane.show_file(selected[0])
            else:
                self.preview_pane.clear()

    def _show_visualizations(self):
        """Show the visualization window."""
        if not self.all_files:
            show_info(self.root, "No Data", "Please scan drives first to see visualizations.")
            return
        VisualizationWindow(self.root, self.filtered_files)

    def _find_duplicates(self):
        """Open the duplicate file finder."""
        if not self.all_files:
            show_info(self.root, "No Data", "Please scan drives first to find duplicates.")
            return
        DuplicateFinderWindow(self.root, self.filtered_files)

    def _smart_analysis(self):
        """Open the smart analysis window."""
        if not self.all_files:
            show_info(self.root, "No Data", "Please scan drives first for analysis.")
            return
        SmartAnalysisWindow(self.root, self.all_files)

    def _move_selected(self):
        """Move selected files to a new location."""
        from ui.dialogs import MoveFilesDialog

        selected = self.file_table.get_selected_files()
        if not selected:
            show_info(self.root, "No Selection", "Please select files to move.")
            return

        total_size = sum(f['file_info'].size for f in selected)
        dialog = MoveFilesDialog(self.root, len(selected), total_size)

        if dialog.result:
            dest = dialog.result['destination']
            keep_structure = dialog.result['keep_structure']

            # Run move in background
            import threading

            def do_move():
                stats = move_files(selected, dest, keep_structure)
                self.root.after(0, lambda: self._move_complete(stats, selected))

            threading.Thread(target=do_move, daemon=True).start()

    def _move_complete(self, stats, moved_files):
        """Called when move operation completes."""
        if stats['moved'] > 0:
            # Remove moved files from list
            for file_dict in moved_files[:stats['moved']]:
                if file_dict in self.all_files:
                    self.all_files.remove(file_dict)
            self._apply_filters()

        show_info(
            self.root,
            "Move Complete",
            f"Moved: {stats['moved']}\n"
            f"Failed: {stats['failed']}\n"
            f"Size: {format_size(stats['total_size'])}"
        )

    def _compress_selected(self):
        """Compress selected files into a ZIP archive."""
        from tkinter import filedialog

        selected = self.file_table.get_selected_files()
        if not selected:
            show_info(self.root, "No Selection", "Please select files to compress.")
            return

        # Ask for archive location
        archive_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Archive As",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )

        if not archive_path:
            return

        # Run compression in background
        import threading

        def do_compress():
            stats = compress_files(selected, archive_path)
            self.root.after(0, lambda: self._compress_complete(stats))

        threading.Thread(target=do_compress, daemon=True).start()

    def _compress_complete(self, stats):
        """Called when compression completes."""
        if stats['compressed'] > 0:
            savings = stats['original_size'] - stats['archive_size']
            ratio = (1 - stats['archive_size'] / stats['original_size']) * 100 if stats['original_size'] > 0 else 0

            show_info(
                self.root,
                "Compression Complete",
                f"Compressed: {stats['compressed']} files\n"
                f"Original size: {format_size(stats['original_size'])}\n"
                f"Archive size: {format_size(stats['archive_size'])}\n"
                f"Saved: {format_size(savings)} ({ratio:.1f}%)"
            )
        else:
            show_error(
                self.root,
                "Compression Failed",
                "Failed to compress files.\n" + "\n".join(stats['errors'][:5])
            )

    def _export_csv(self):
        """Export file list to CSV."""
        if not self.filtered_files:
            show_info(self.root, "No Data", "No files to export.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if path:
            if export_file_list(self.filtered_files, path, 'csv'):
                show_info(self.root, "Export Complete", f"Exported to:\n{path}")
            else:
                show_error(self.root, "Export Failed", "Could not export file list.")

    def _export_html(self):
        """Export file list to HTML."""
        if not self.filtered_files:
            show_info(self.root, "No Data", "No files to export.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export to HTML",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )

        if path:
            if export_file_list(self.filtered_files, path, 'html'):
                show_info(self.root, "Export Complete", f"Exported to:\n{path}")
                # Optionally open in browser
                import webbrowser
                webbrowser.open(f'file://{path}')
            else:
                show_error(self.root, "Export Failed", "Could not export file list.")

    def _rebuild_profiles_menu(self):
        """Rebuild the profiles menu with saved profiles."""
        # Remove existing profile entries (after separator)
        try:
            last = self.profiles_menu.index('end')
            if last is not None and last >= 3:
                for i in range(last, 2, -1):
                    self.profiles_menu.delete(i)
        except tk.TclError:
            pass

        # Add saved profiles
        if self.profiles:
            for name in sorted(self.profiles.keys()):
                self.profiles_menu.add_command(
                    label=f"Load: {name}",
                    command=lambda n=name: self._load_profile(n)
                )

    def _save_profile(self):
        """Save current filter settings as a profile."""
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Save Profile",
            "Enter profile name:",
            parent=self.root
        )

        if not name:
            return

        name = name.strip()
        if not name:
            return

        # Save current filter values
        profile = {
            'category': self.category_var.get(),
            'min_size': self.min_size_var.get(),
            'min_days': self.min_days_var.get(),
            'search': self.search_var.get()
        }

        self.profiles[name] = profile
        self._save_profiles()
        self._rebuild_profiles_menu()

        show_info(self.root, "Profile Saved", f"Profile '{name}' has been saved.")

    def _load_profile(self, name: str):
        """Load a saved profile."""
        if name not in self.profiles:
            return

        profile = self.profiles[name]

        # Apply profile settings
        self.category_var.set(profile.get('category', 'All'))
        self.min_size_var.set(profile.get('min_size', '0'))
        self.min_days_var.set(profile.get('min_days', '0 days'))
        self.search_var.set(profile.get('search', ''))

        self._apply_filters()
        self.status_var.set(f"Loaded profile: {name}")

    def _manage_profiles(self):
        """Open profile management dialog."""
        ProfileManagerDialog(self.root, self.profiles, self._on_profiles_changed)

    def _on_profiles_changed(self, new_profiles: dict):
        """Called when profiles are modified in the manager."""
        self.profiles = new_profiles
        self._save_profiles()
        self._rebuild_profiles_menu()


class ProfileManagerDialog:
    """Dialog for managing saved filter profiles."""

    def __init__(self, parent, profiles: dict, on_save):
        self.profiles = profiles.copy()
        self.on_save = on_save

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Profiles")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # List of profiles
        ttk.Label(
            main_frame,
            text="Saved Profiles:",
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor=tk.W)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.profile_list = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            font=('Consolas', 10)
        )
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profile_list.yview)
        self.profile_list.configure(yscrollcommand=vsb.set)

        self.profile_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate list
        for name in sorted(self.profiles.keys()):
            self.profile_list.insert(tk.END, name)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self._delete_selected
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Delete All",
            command=self._delete_all
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="Close",
            command=self._close
        ).pack(side=tk.RIGHT)

    def _delete_selected(self):
        """Delete the selected profile."""
        selection = self.profile_list.curselection()
        if not selection:
            return

        name = self.profile_list.get(selection[0])
        if name in self.profiles:
            del self.profiles[name]
            self.profile_list.delete(selection[0])

    def _delete_all(self):
        """Delete all profiles."""
        self.profiles.clear()
        self.profile_list.delete(0, tk.END)

    def _close(self):
        """Close the dialog and save changes."""
        self.on_save(self.profiles)
        self.dialog.destroy()
