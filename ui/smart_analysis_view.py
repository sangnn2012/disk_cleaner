"""Smart analysis viewer for disk cleanup recommendations."""

import tkinter as tk
from tkinter import ttk
import threading
import os
from utils import format_size, format_date, get_available_drives
from smart_analysis import (
    find_empty_folders, find_temp_files, find_large_folders,
    find_old_downloads, analyze_disk_usage
)
from ui.dialogs import ask_confirmation, show_info, show_error

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


class SmartAnalysisWindow:
    """Window for smart disk analysis and cleanup recommendations."""

    def __init__(self, parent, files: list):
        self.parent = parent
        self.files = files
        self.analysis_results = {}
        self.empty_folders = []

        self.window = tk.Toplevel(parent)
        self.window.title("Smart Analysis")
        self.window.geometry("900x600")
        self.window.transient(parent)

        self._create_widgets()
        self._run_analysis()

    def _create_widgets(self):
        """Create the window widgets."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Temp Files
        self._create_temp_files_tab()

        # Tab 2: Old Downloads
        self._create_old_downloads_tab()

        # Tab 3: Large Folders
        self._create_large_folders_tab()

        # Tab 4: Empty Folders
        self._create_empty_folders_tab()

        # Status bar
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Analyzing...")
        ttk.Label(
            status_frame,
            textvariable=self.status_var
        ).pack(side=tk.LEFT)

        ttk.Button(
            status_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side=tk.RIGHT)

    def _create_temp_files_tab(self):
        """Create the temporary files tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Temporary Files")

        # Header
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="Temporary and cache files that can be safely deleted",
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.temp_size_var = tk.StringVar(value="")
        ttk.Label(
            header,
            textvariable=self.temp_size_var,
            font=('Segoe UI', 10, 'bold')
        ).pack(side=tk.RIGHT)

        # Treeview
        columns = ('name', 'size', 'path')
        self.temp_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        self.temp_tree.heading('name', text='File Name')
        self.temp_tree.heading('size', text='Size')
        self.temp_tree.heading('path', text='Path')

        self.temp_tree.column('name', width=200)
        self.temp_tree.column('size', width=100)
        self.temp_tree.column('path', width=500)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.temp_tree.yview)
        self.temp_tree.configure(yscrollcommand=vsb.set)

        self.temp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.clean_temp_btn = ttk.Button(
            btn_frame,
            text="Clean Selected",
            command=lambda: self._delete_selected(self.temp_tree),
            state=tk.DISABLED
        )
        self.clean_temp_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clean_all_temp_btn = ttk.Button(
            btn_frame,
            text="Clean All Temp Files",
            command=lambda: self._delete_all('temp_files'),
            state=tk.DISABLED
        )
        self.clean_all_temp_btn.pack(side=tk.LEFT)

    def _create_old_downloads_tab(self):
        """Create the old downloads tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Old Downloads")

        # Header
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="Files in Downloads folder not accessed in 30+ days",
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.downloads_size_var = tk.StringVar(value="")
        ttk.Label(
            header,
            textvariable=self.downloads_size_var,
            font=('Segoe UI', 10, 'bold')
        ).pack(side=tk.RIGHT)

        # Treeview
        columns = ('name', 'size', 'accessed', 'path')
        self.downloads_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        self.downloads_tree.heading('name', text='File Name')
        self.downloads_tree.heading('size', text='Size')
        self.downloads_tree.heading('accessed', text='Last Accessed')
        self.downloads_tree.heading('path', text='Path')

        self.downloads_tree.column('name', width=200)
        self.downloads_tree.column('size', width=100)
        self.downloads_tree.column('accessed', width=120)
        self.downloads_tree.column('path', width=380)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.downloads_tree.yview)
        self.downloads_tree.configure(yscrollcommand=vsb.set)

        self.downloads_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.clean_downloads_btn = ttk.Button(
            btn_frame,
            text="Clean Selected",
            command=lambda: self._delete_selected(self.downloads_tree),
            state=tk.DISABLED
        )
        self.clean_downloads_btn.pack(side=tk.LEFT)

    def _create_large_folders_tab(self):
        """Create the large folders tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Large Folders")

        # Header
        ttk.Label(
            frame,
            text="Folders larger than 1 GB (review for cleanup)",
            font=('Segoe UI', 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview
        columns = ('folder', 'size', 'files')
        self.large_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        self.large_tree.heading('folder', text='Folder')
        self.large_tree.heading('size', text='Size')
        self.large_tree.heading('files', text='Files')

        self.large_tree.column('folder', width=500)
        self.large_tree.column('size', width=120)
        self.large_tree.column('files', width=80)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.large_tree.yview)
        self.large_tree.configure(yscrollcommand=vsb.set)

        self.large_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Button to open folder
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Open Selected Folder",
            command=self._open_large_folder
        ).pack(side=tk.LEFT)

    def _create_empty_folders_tab(self):
        """Create the empty folders tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Empty Folders")

        # Header
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="Empty folders that can be deleted",
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.empty_count_var = tk.StringVar(value="")
        ttk.Label(
            header,
            textvariable=self.empty_count_var,
            font=('Segoe UI', 10, 'bold')
        ).pack(side=tk.RIGHT)

        # Listbox
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.empty_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=('Consolas', 9)
        )
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.empty_listbox.yview)
        self.empty_listbox.configure(yscrollcommand=vsb.set)

        self.empty_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.scan_empty_btn = ttk.Button(
            btn_frame,
            text="Scan for Empty Folders",
            command=self._scan_empty_folders
        )
        self.scan_empty_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_empty_btn = ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self._delete_empty_selected,
            state=tk.DISABLED
        )
        self.delete_empty_btn.pack(side=tk.LEFT)

    def _run_analysis(self):
        """Run the analysis in background."""
        thread = threading.Thread(target=self._analysis_worker, daemon=True)
        thread.start()

    def _analysis_worker(self):
        """Background worker for analysis."""
        try:
            self.analysis_results = analyze_disk_usage(self.files)
            self.window.after(0, self._populate_results)
        except Exception as e:
            self.window.after(0, lambda: self.status_var.set(f"Error: {e}"))

    def _populate_results(self):
        """Populate all tabs with analysis results."""
        # Temp files
        temp_files = self.analysis_results.get('temp_files', [])
        for file_dict in temp_files[:500]:  # Limit to 500
            file_info = file_dict['file_info']
            self.temp_tree.insert('', tk.END, values=(
                file_info.name,
                format_size(file_info.size),
                file_info.path
            ))

        temp_size = self.analysis_results.get('temp_size', 0)
        self.temp_size_var.set(f"Total: {format_size(temp_size)}")

        # Old downloads
        old_downloads = self.analysis_results.get('old_downloads', [])
        for file_dict in old_downloads[:500]:
            file_info = file_dict['file_info']
            self.downloads_tree.insert('', tk.END, values=(
                file_info.name,
                format_size(file_info.size),
                format_date(file_info.last_accessed),
                file_info.path
            ))

        downloads_size = self.analysis_results.get('downloads_size', 0)
        self.downloads_size_var.set(f"Total: {format_size(downloads_size)}")

        # Large folders
        large_folders = self.analysis_results.get('large_folders', [])
        for folder, size, count in large_folders[:100]:
            self.large_tree.insert('', tk.END, values=(
                folder,
                format_size(size),
                count
            ))

        # Enable buttons
        if HAS_SEND2TRASH:
            if temp_files:
                self.clean_temp_btn.config(state=tk.NORMAL)
                self.clean_all_temp_btn.config(state=tk.NORMAL)
            if old_downloads:
                self.clean_downloads_btn.config(state=tk.NORMAL)

        # Update status
        potential = self.analysis_results.get('potential_savings', 0)
        self.status_var.set(
            f"Analysis complete. Potential savings: {format_size(potential)}"
        )

    def _delete_selected(self, tree):
        """Delete selected items from a tree."""
        if not HAS_SEND2TRASH:
            show_error(self.window, "Error", "send2trash not installed")
            return

        selected = tree.selection()
        if not selected:
            show_info(self.window, "No Selection", "Select items to delete.")
            return

        paths = []
        for item in selected:
            values = tree.item(item, 'values')
            path = values[-1]  # Path is last column
            if os.path.isfile(path):
                paths.append(path)

        if not paths:
            return

        total_size = sum(os.path.getsize(p) for p in paths if os.path.exists(p))

        if not ask_confirmation(self.window, paths, total_size):
            return

        deleted = 0
        for path in paths:
            try:
                send2trash(path)
                deleted += 1
            except Exception:
                pass

        show_info(self.window, "Done", f"Deleted {deleted} file(s)")

        # Remove from tree
        for item in selected:
            tree.delete(item)

    def _delete_all(self, category):
        """Delete all files in a category."""
        if not HAS_SEND2TRASH:
            show_error(self.window, "Error", "send2trash not installed")
            return

        files = self.analysis_results.get(category, [])
        if not files:
            return

        paths = [f['file_info'].path for f in files]
        total_size = sum(f['file_info'].size for f in files)

        if not ask_confirmation(self.window, paths, total_size):
            return

        deleted = 0
        for path in paths:
            try:
                if os.path.exists(path):
                    send2trash(path)
                    deleted += 1
            except Exception:
                pass

        show_info(
            self.window,
            "Done",
            f"Deleted {deleted} file(s), freed {format_size(total_size)}"
        )

        # Refresh
        self._run_analysis()

    def _open_large_folder(self):
        """Open selected large folder in explorer."""
        selected = self.large_tree.selection()
        if selected:
            values = self.large_tree.item(selected[0], 'values')
            folder = values[0]
            if os.path.isdir(folder):
                import subprocess
                subprocess.run(['explorer', folder], check=False)

    def _scan_empty_folders(self):
        """Scan for empty folders."""
        self.scan_empty_btn.config(state=tk.DISABLED)
        self.empty_listbox.delete(0, tk.END)
        self.empty_count_var.set("Scanning...")

        thread = threading.Thread(target=self._empty_scan_worker, daemon=True)
        thread.start()

    def _empty_scan_worker(self):
        """Background worker for empty folder scan."""
        drives = get_available_drives()

        def progress(path, count):
            self.window.after(0, lambda: self.empty_count_var.set(f"Scanning... {count}"))

        self.empty_folders = find_empty_folders(drives, progress)
        self.window.after(0, self._populate_empty_folders)

    def _populate_empty_folders(self):
        """Populate empty folders list."""
        self.empty_listbox.delete(0, tk.END)

        for folder in self.empty_folders[:1000]:
            self.empty_listbox.insert(tk.END, folder)

        self.empty_count_var.set(f"Found: {len(self.empty_folders)} empty folders")
        self.scan_empty_btn.config(state=tk.NORMAL)

        if self.empty_folders and HAS_SEND2TRASH:
            self.delete_empty_btn.config(state=tk.NORMAL)

    def _delete_empty_selected(self):
        """Delete selected empty folders."""
        if not HAS_SEND2TRASH:
            show_error(self.window, "Error", "send2trash not installed")
            return

        selected = list(self.empty_listbox.curselection())
        if not selected:
            show_info(self.window, "No Selection", "Select folders to delete.")
            return

        folders = [self.empty_listbox.get(i) for i in selected]

        if not ask_confirmation(self.window, folders, 0):
            return

        deleted = 0
        for folder in folders:
            try:
                if os.path.isdir(folder):
                    send2trash(folder)
                    deleted += 1
            except Exception:
                pass

        show_info(self.window, "Done", f"Deleted {deleted} empty folder(s)")

        # Remove from list
        for i in reversed(selected):
            self.empty_listbox.delete(i)
            if i < len(self.empty_folders):
                self.empty_folders.pop(i)
