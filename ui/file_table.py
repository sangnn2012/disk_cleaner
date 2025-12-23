"""File table widget with sorting, selection, and context menu."""

import tkinter as tk
from tkinter import ttk
import os
import subprocess
from utils import format_size, format_date


class FileTable(ttk.Frame):
    """A treeview table for displaying files with selection and context menu."""

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

        # Callbacks for context menu actions
        self.on_exclude_file = None  # Callback(file_path)
        self.on_show_properties = None  # Callback(file_dict)
        self.on_delete_files = None  # Callback(file_dicts)

        self._create_widgets()
        self._create_context_menu()

    def _create_widgets(self):
        """Create the treeview and scrollbars."""
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

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change)
        self.tree.bind('<Button-3>', self._on_right_click)  # Right-click
        self.tree.bind('<Double-1>', self._on_double_click)  # Double-click to open

    def _create_context_menu(self):
        """Create the right-click context menu."""
        self.context_menu = tk.Menu(self, tearoff=0)

        self.context_menu.add_command(
            label="Open File",
            command=self._open_selected_file
        )
        self.context_menu.add_command(
            label="Open File Location",
            command=self._open_file_location
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Copy Path",
            command=self._copy_path
        )
        self.context_menu.add_command(
            label="Copy Filename",
            command=self._copy_filename
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Properties...",
            command=self._show_properties
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Add to Exclusion List",
            command=self._add_to_exclusion
        )
        self.context_menu.add_command(
            label="Exclude This Folder",
            command=self._exclude_folder
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Delete Selected",
            command=self._delete_selected
        )

    def _on_right_click(self, event):
        """Handle right-click to show context menu."""
        # Select the item under cursor if not already selected
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)

            # Update menu state based on selection
            selection = self.tree.selection()
            has_selection = len(selection) > 0
            single_selection = len(selection) == 1

            # Enable/disable menu items
            state_single = tk.NORMAL if single_selection else tk.DISABLED
            state_any = tk.NORMAL if has_selection else tk.DISABLED

            self.context_menu.entryconfig("Open File", state=state_single)
            self.context_menu.entryconfig("Open File Location", state=state_single)
            self.context_menu.entryconfig("Copy Path", state=state_any)
            self.context_menu.entryconfig("Copy Filename", state=state_any)
            self.context_menu.entryconfig("Properties...", state=state_single)
            self.context_menu.entryconfig("Add to Exclusion List", state=state_any)
            self.context_menu.entryconfig("Exclude This Folder", state=state_single)
            self.context_menu.entryconfig("Delete Selected", state=state_any)

            # Show context menu
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _on_double_click(self, event):
        """Handle double-click to open file."""
        item = self.tree.identify_row(event.y)
        if item:
            self._open_selected_file()

    def _get_file_at_index(self, iid: str):
        """Get file dict for a treeview item id."""
        try:
            index = int(iid)
            if 0 <= index < len(self.files_data):
                return self.files_data[index]
        except (ValueError, IndexError):
            pass
        return None

    def _open_selected_file(self):
        """Open the selected file with its default application."""
        selected = self.tree.selection()
        if selected:
            file_dict = self._get_file_at_index(selected[0])
            if file_dict:
                path = file_dict['file_info'].path
                try:
                    os.startfile(path)
                except OSError as e:
                    from ui.dialogs import show_error
                    show_error(self.winfo_toplevel(), "Error", f"Cannot open file:\n{e}")

    def _open_file_location(self):
        """Open the file's folder in File Explorer and select it."""
        selected = self.tree.selection()
        if selected:
            file_dict = self._get_file_at_index(selected[0])
            if file_dict:
                path = file_dict['file_info'].path
                try:
                    # Use explorer /select to open folder and highlight the file
                    subprocess.run(['explorer', '/select,', path], check=False)
                except Exception as e:
                    from ui.dialogs import show_error
                    show_error(self.winfo_toplevel(), "Error", f"Cannot open location:\n{e}")

    def _copy_path(self):
        """Copy full path(s) of selected file(s) to clipboard."""
        selected = self.get_selected_files()
        if selected:
            paths = [f['file_info'].path for f in selected]
            text = '\n'.join(paths)
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()  # Required for clipboard to persist

    def _copy_filename(self):
        """Copy filename(s) of selected file(s) to clipboard."""
        selected = self.get_selected_files()
        if selected:
            names = [f['file_info'].name for f in selected]
            text = '\n'.join(names)
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()

    def _show_properties(self):
        """Show properties dialog for selected file."""
        if self.on_show_properties:
            selected = self.tree.selection()
            if selected:
                file_dict = self._get_file_at_index(selected[0])
                if file_dict:
                    self.on_show_properties(file_dict)

    def _add_to_exclusion(self):
        """Add selected files to exclusion list."""
        if self.on_exclude_file:
            selected = self.get_selected_files()
            for file_dict in selected:
                self.on_exclude_file(file_dict['file_info'].path)

    def _exclude_folder(self):
        """Add the folder containing selected file to exclusion list."""
        if self.on_exclude_file:
            selected = self.tree.selection()
            if selected:
                file_dict = self._get_file_at_index(selected[0])
                if file_dict:
                    folder = os.path.dirname(file_dict['file_info'].path)
                    self.on_exclude_file(folder)

    def _delete_selected(self):
        """Delete selected files (calls external handler)."""
        if self.on_delete_files:
            selected = self.get_selected_files()
            if selected:
                self.on_delete_files(selected)

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

    def get_file_by_path(self, path: str):
        """Get file dict by path."""
        for file_dict in self.files_data:
            if file_dict['file_info'].path == path:
                return file_dict
        return None

    def remove_file(self, file_dict):
        """Remove a file from the table."""
        if file_dict in self.files_data:
            self.files_data.remove(file_dict)
            self._refresh_display()

    def remove_files(self, file_dicts: list):
        """Remove multiple files from the table."""
        for file_dict in file_dicts:
            if file_dict in self.files_data:
                self.files_data.remove(file_dict)
        self._refresh_display()

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
