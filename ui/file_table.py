"""File table widget with sorting and selection."""

import tkinter as tk
from tkinter import ttk
from utils import format_size, format_date


class FileTable(ttk.Frame):
    """A treeview table for displaying files with selection checkboxes."""

    COLUMNS = [
        ('name', 'Name', 250),
        ('size', 'Size', 100),
        ('accessed', 'Last Accessed', 130),
        ('category', 'Category', 80),
        ('path', 'Path', 400),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.files_data = []  # Store analyzed file dicts
        self.selected_items = set()
        self.sort_column = 'size'
        self.sort_reverse = True

        self._create_widgets()

    def _create_widgets(self):
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(
            self,
            columns=[col[0] for col in self.COLUMNS],
            show='headings',
            selectmode='extended'
        )

        # Configure columns
        for col_id, col_name, col_width in self.COLUMNS:
            self.tree.heading(
                col_id,
                text=col_name,
                command=lambda c=col_id: self._on_header_click(c)
            )
            self.tree.column(col_id, width=col_width, minwidth=50)

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change)

    def _on_header_click(self, column):
        """Handle column header click for sorting."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            # Default to descending for size, ascending for others
            self.sort_reverse = column in ('size', 'accessed')

        self._sort_and_refresh()

    def _sort_and_refresh(self):
        """Sort the data and refresh the display."""
        if not self.files_data:
            return

        # Define sort keys
        if self.sort_column == 'size':
            key = lambda x: x['file_info'].size
        elif self.sort_column == 'accessed':
            key = lambda x: x['file_info'].last_accessed
        elif self.sort_column == 'name':
            key = lambda x: x['file_info'].name.lower()
        elif self.sort_column == 'category':
            key = lambda x: x['category']
        elif self.sort_column == 'path':
            key = lambda x: x['file_info'].path.lower()
        else:
            key = lambda x: x['file_info'].size

        self.files_data.sort(key=key, reverse=self.sort_reverse)
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the treeview display with current data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert sorted data
        for i, item in enumerate(self.files_data):
            file_info = item['file_info']
            values = (
                file_info.name,
                format_size(file_info.size),
                format_date(file_info.last_accessed),
                item['category'],
                file_info.path,
            )
            self.tree.insert('', tk.END, iid=str(i), values=values)

    def _on_selection_change(self, event):
        """Handle selection change in treeview."""
        self.selected_items = set(self.tree.selection())

    def load_files(self, analyzed_files: list):
        """Load analyzed files into the table."""
        self.files_data = analyzed_files.copy()
        self._sort_and_refresh()

    def clear(self):
        """Clear all files from the table."""
        self.files_data = []
        self.selected_items = set()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_selected_files(self) -> list:
        """Get list of selected file dicts."""
        selected = []
        for iid in self.tree.selection():
            try:
                index = int(iid)
                if 0 <= index < len(self.files_data):
                    selected.append(self.files_data[index])
            except (ValueError, IndexError):
                continue
        return selected

    def select_all(self):
        """Select all items in the table."""
        items = self.tree.get_children()
        self.tree.selection_set(items)

    def deselect_all(self):
        """Deselect all items in the table."""
        self.tree.selection_remove(self.tree.selection())

    def get_total_count(self) -> int:
        """Get total number of files in table."""
        return len(self.files_data)

    def get_selected_count(self) -> int:
        """Get number of selected files."""
        return len(self.tree.selection())

    def get_selected_size(self) -> int:
        """Get total size of selected files in bytes."""
        total = 0
        for item in self.get_selected_files():
            total += item['file_info'].size
        return total
