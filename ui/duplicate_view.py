"""Duplicate files viewer and manager."""

import tkinter as tk
from tkinter import ttk
import threading
import os
from utils import format_size, format_date
from duplicate_finder import find_duplicates, get_duplicate_stats
from ui.dialogs import ask_confirmation, show_info, show_error

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


class DuplicateFinderWindow:
    """Window for finding and managing duplicate files."""

    def __init__(self, parent, files: list):
        self.parent = parent
        self.files = files
        self.duplicates = {}
        self.stop_scan = False

        self.window = tk.Toplevel(parent)
        self.window.title("Duplicate File Finder")
        self.window.geometry("1000x600")
        self.window.transient(parent)

        self._create_widgets()

        # Start finding duplicates
        self._start_scan()

    def _create_widgets(self):
        """Create the window widgets."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with stats
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Duplicate Files",
            font=('Segoe UI', 12, 'bold')
        ).pack(side=tk.LEFT)

        self.stats_var = tk.StringVar(value="Scanning...")
        ttk.Label(
            header_frame,
            textvariable=self.stats_var,
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT, padx=20)

        # Progress bar
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.StringVar(value="")
        ttk.Label(
            self.progress_frame,
            textvariable=self.progress_var
        ).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=300
        )
        self.progress.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(
            self.progress_frame,
            text="Stop",
            command=self._stop_scan
        )
        self.stop_btn.pack(side=tk.LEFT)

        # Duplicate groups treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('name', 'size', 'path', 'accessed')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')

        self.tree.heading('#0', text='Group')
        self.tree.heading('name', text='File Name')
        self.tree.heading('size', text='Size')
        self.tree.heading('path', text='Path')
        self.tree.heading('accessed', text='Last Accessed')

        self.tree.column('#0', width=80)
        self.tree.column('name', width=200)
        self.tree.column('size', width=100)
        self.tree.column('path', width=400)
        self.tree.column('accessed', width=120)

        # Scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.delete_btn = ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self._delete_selected,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.keep_newest_btn = ttk.Button(
            btn_frame,
            text="Keep Newest in Each Group",
            command=self._keep_newest,
            state=tk.DISABLED
        )
        self.keep_newest_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.keep_oldest_btn = ttk.Button(
            btn_frame,
            text="Keep Oldest in Each Group",
            command=self._keep_oldest,
            state=tk.DISABLED
        )
        self.keep_oldest_btn.pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side=tk.RIGHT)

        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self._start_scan
        ).pack(side=tk.RIGHT, padx=5)

    def _start_scan(self):
        """Start scanning for duplicates."""
        self.stop_scan = False
        self.duplicates = {}
        self.tree.delete(*self.tree.get_children())

        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress['value'] = 0

        # Disable buttons during scan
        self.delete_btn.config(state=tk.DISABLED)
        self.keep_newest_btn.config(state=tk.DISABLED)
        self.keep_oldest_btn.config(state=tk.DISABLED)

        # Run scan in background
        thread = threading.Thread(target=self._scan_worker, daemon=True)
        thread.start()

    def _scan_worker(self):
        """Background worker for finding duplicates."""
        def progress_callback(stage, current, total):
            self.window.after(0, lambda: self._update_progress(stage, current, total))

        def stop_flag():
            return self.stop_scan

        try:
            self.duplicates = find_duplicates(
                self.files,
                progress_callback,
                stop_flag
            )
            self.window.after(0, self._scan_complete)
        except Exception as e:
            self.window.after(0, lambda: self._scan_error(str(e)))

    def _update_progress(self, stage, current, total):
        """Update progress bar."""
        self.progress_var.set(f"{stage}...")
        if total > 0:
            self.progress['value'] = (current / total) * 100

    def _scan_complete(self):
        """Called when scan is complete."""
        self.progress_frame.pack_forget()

        # Get stats
        stats = get_duplicate_stats(self.duplicates)
        self.stats_var.set(
            f"Found {stats['total_groups']} groups, "
            f"{stats['total_files']} files, "
            f"{format_size(stats['wasted_space'])} wasted"
        )

        # Populate tree
        self._populate_tree()

        # Enable buttons
        if self.duplicates and HAS_SEND2TRASH:
            self.delete_btn.config(state=tk.NORMAL)
            self.keep_newest_btn.config(state=tk.NORMAL)
            self.keep_oldest_btn.config(state=tk.NORMAL)

    def _scan_error(self, error_msg):
        """Called on scan error."""
        self.progress_frame.pack_forget()
        self.stats_var.set(f"Error: {error_msg}")
        show_error(self.window, "Scan Error", error_msg)

    def _stop_scan(self):
        """Stop the scan."""
        self.stop_scan = True

    def _populate_tree(self):
        """Populate the tree with duplicate groups."""
        self.tree.delete(*self.tree.get_children())

        for i, (hash_val, files) in enumerate(self.duplicates.items(), 1):
            # Create group node
            size = files[0]['file_info'].size
            group_id = self.tree.insert(
                '', tk.END,
                text=f"Group {i}",
                values=('', format_size(size), f"{len(files)} files", ''),
                open=True
            )

            # Add files to group
            for file_dict in files:
                file_info = file_dict['file_info']
                self.tree.insert(
                    group_id, tk.END,
                    text='',
                    values=(
                        file_info.name,
                        format_size(file_info.size),
                        file_info.path,
                        format_date(file_info.last_accessed)
                    ),
                    tags=('file',)
                )

    def _get_selected_files(self) -> list:
        """Get list of selected file paths."""
        selected = []
        for item in self.tree.selection():
            values = self.tree.item(item, 'values')
            if values and values[2] and os.path.isfile(values[2]):
                selected.append(values[2])
        return selected

    def _delete_selected(self):
        """Delete selected files."""
        if not HAS_SEND2TRASH:
            show_error(self.window, "Error", "send2trash not installed")
            return

        selected = self._get_selected_files()
        if not selected:
            show_info(self.window, "No Selection", "Select files to delete.")
            return

        total_size = sum(os.path.getsize(p) for p in selected if os.path.exists(p))

        if not ask_confirmation(self.window, selected, total_size):
            return

        deleted = 0
        for path in selected:
            try:
                send2trash(path)
                deleted += 1
            except Exception:
                pass

        show_info(self.window, "Done", f"Deleted {deleted} file(s)")
        self._start_scan()  # Refresh

    def _keep_newest(self):
        """Keep only the newest file in each group."""
        self._keep_by_criteria(newest=True)

    def _keep_oldest(self):
        """Keep only the oldest file in each group."""
        self._keep_by_criteria(newest=False)

    def _keep_by_criteria(self, newest=True):
        """Delete all but one file in each group based on criteria."""
        if not HAS_SEND2TRASH:
            show_error(self.window, "Error", "send2trash not installed")
            return

        files_to_delete = []

        for files in self.duplicates.values():
            if len(files) < 2:
                continue

            # Sort by access time
            sorted_files = sorted(
                files,
                key=lambda x: x['file_info'].last_accessed,
                reverse=newest
            )

            # Keep first (newest/oldest), delete rest
            for file_dict in sorted_files[1:]:
                files_to_delete.append(file_dict['file_info'].path)

        if not files_to_delete:
            show_info(self.window, "Nothing to Delete", "No duplicate files to remove.")
            return

        total_size = sum(
            os.path.getsize(p) for p in files_to_delete
            if os.path.exists(p)
        )

        action = "newest" if newest else "oldest"
        if not ask_confirmation(self.window, files_to_delete, total_size):
            return

        deleted = 0
        for path in files_to_delete:
            try:
                send2trash(path)
                deleted += 1
            except Exception:
                pass

        show_info(
            self.window,
            "Done",
            f"Kept {action} file in each group.\n"
            f"Deleted {deleted} file(s), freed {format_size(total_size)}"
        )
        self._start_scan()  # Refresh
