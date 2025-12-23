"""Dialog windows for the disk cleaner app."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from utils import format_size, format_date, days_since


def ask_confirmation(parent, files_to_delete: list, total_size: int) -> bool:
    """
    Show confirmation dialog before deleting files.

    Args:
        parent: Parent window
        files_to_delete: List of file paths to delete
        total_size: Total size in bytes

    Returns:
        True if user confirms, False otherwise
    """
    count = len(files_to_delete)
    size_str = format_size(total_size)

    message = (
        f"Are you sure you want to delete {count} file(s)?\n\n"
        f"Total space to free: {size_str}\n\n"
        f"Files will be moved to the Recycle Bin."
    )

    return messagebox.askyesno(
        "Confirm Deletion",
        message,
        icon=messagebox.WARNING,
        parent=parent
    )


def show_error(parent, title: str, message: str):
    """Show an error message dialog."""
    messagebox.showerror(title, message, parent=parent)


def show_info(parent, title: str, message: str):
    """Show an info message dialog."""
    messagebox.showinfo(title, message, parent=parent)


def ask_folder(parent, title: str = "Select Folder") -> str:
    """
    Open a folder selection dialog.

    Returns:
        Selected folder path or empty string if cancelled
    """
    return filedialog.askdirectory(
        title=title,
        parent=parent
    )


def ask_save_file(parent, title: str, filetypes: list, default_ext: str = "") -> str:
    """
    Open a save file dialog.

    Args:
        parent: Parent window
        title: Dialog title
        filetypes: List of (description, pattern) tuples
        default_ext: Default extension

    Returns:
        Selected file path or empty string if cancelled
    """
    return filedialog.asksaveasfilename(
        title=title,
        parent=parent,
        filetypes=filetypes,
        defaultextension=default_ext
    )


class DriveSelectionDialog:
    """Dialog for selecting which drives to scan."""

    def __init__(self, parent, available_drives: list):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Drives to Scan")
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Instructions
        ttk.Label(
            self.dialog,
            text="Select drives to scan:",
            font=('Segoe UI', 10)
        ).pack(pady=(15, 10))

        # Drive checkboxes
        self.drive_vars = {}
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20)

        for drive in available_drives:
            var = tk.BooleanVar(value=True)
            self.drive_vars[drive] = var
            cb = ttk.Checkbutton(
                frame,
                text=drive,
                variable=var,
            )
            cb.pack(anchor=tk.W, pady=2)

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, pady=15, padx=20)

        ttk.Button(
            btn_frame,
            text="Scan Selected",
            command=self._on_ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT)

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.dialog.wait_window()

    def _on_ok(self):
        self.result = [
            drive for drive, var in self.drive_vars.items()
            if var.get()
        ]
        self.dialog.destroy()

    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()


class FilePropertiesDialog:
    """Dialog showing detailed file properties."""

    def __init__(self, parent, file_dict: dict):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("File Properties")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        file_info = file_dict['file_info']
        category = file_dict['category']

        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File name header
        name_label = ttk.Label(
            main_frame,
            text=file_info.name,
            font=('Segoe UI', 12, 'bold'),
            wraplength=400
        )
        name_label.pack(anchor=tk.W, pady=(0, 15))

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Properties grid
        props_frame = ttk.Frame(main_frame)
        props_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        properties = [
            ("Type:", category),
            ("Extension:", file_info.extension if file_info.extension else "(none)"),
            ("Size:", format_size(file_info.size)),
            ("Size (bytes):", f"{file_info.size:,}"),
            ("", ""),  # Spacer
            ("Location:", ""),
            ("", file_info.path),
            ("", ""),  # Spacer
            ("Last Accessed:", format_date(file_info.last_accessed)),
            ("Days Since Access:", f"{days_since(file_info.last_accessed)} days"),
            ("Last Modified:", format_date(file_info.last_modified)),
        ]

        # Try to get additional file attributes
        try:
            stat_info = os.stat(file_info.path)
            created_time = datetime.fromtimestamp(stat_info.st_ctime)
            properties.append(("Created:", created_time.strftime("%Y-%m-%d %H:%M")))

            # File attributes on Windows
            if hasattr(stat_info, 'st_file_attributes'):
                import stat
                attrs = []
                fa = stat_info.st_file_attributes
                if fa & 0x1:  # FILE_ATTRIBUTE_READONLY
                    attrs.append("Read-only")
                if fa & 0x2:  # FILE_ATTRIBUTE_HIDDEN
                    attrs.append("Hidden")
                if fa & 0x4:  # FILE_ATTRIBUTE_SYSTEM
                    attrs.append("System")
                if fa & 0x20:  # FILE_ATTRIBUTE_ARCHIVE
                    attrs.append("Archive")
                if attrs:
                    properties.append(("Attributes:", ", ".join(attrs)))
        except (OSError, ValueError):
            pass

        for i, (label, value) in enumerate(properties):
            if label:
                ttk.Label(
                    props_frame,
                    text=label,
                    font=('Segoe UI', 9, 'bold')
                ).grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)

            if value:
                value_label = ttk.Label(
                    props_frame,
                    text=value,
                    font=('Segoe UI', 9),
                    wraplength=300
                )
                value_label.grid(row=i, column=1, sticky=tk.W, pady=2)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            btn_frame,
            text="Open File",
            command=lambda: self._open_file(file_info.path)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Open Location",
            command=lambda: self._open_location(file_info.path)
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)

    def _open_file(self, path):
        try:
            os.startfile(path)
        except OSError as e:
            show_error(self.dialog, "Error", f"Cannot open file:\n{e}")

    def _open_location(self, path):
        import subprocess
        try:
            subprocess.run(['explorer', '/select,', path], check=False)
        except Exception as e:
            show_error(self.dialog, "Error", f"Cannot open location:\n{e}")


class ExclusionListDialog:
    """Dialog for managing exclusion list."""

    def __init__(self, parent, exclusions: list, on_save):
        self.result = None
        self.on_save = on_save
        self.exclusions = exclusions.copy()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Exclusion List")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        ttk.Label(
            main_frame,
            text="Files and folders in this list will be excluded from scan results:",
            font=('Segoe UI', 9)
        ).pack(anchor=tk.W, pady=(0, 10))

        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=('Consolas', 9)
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate listbox
        for exc in self.exclusions:
            self.listbox.insert(tk.END, exc)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Add File...",
            command=self._add_file
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Add Folder...",
            command=self._add_folder
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Remove Selected",
            command=self._remove_selected
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="Save",
            command=self._on_save
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)

    def _add_file(self):
        path = filedialog.askopenfilename(parent=self.dialog, title="Select File to Exclude")
        if path:
            if path not in self.exclusions:
                self.exclusions.append(path)
                self.listbox.insert(tk.END, path)

    def _add_folder(self):
        path = filedialog.askdirectory(parent=self.dialog, title="Select Folder to Exclude")
        if path:
            if path not in self.exclusions:
                self.exclusions.append(path)
                self.listbox.insert(tk.END, path)

    def _remove_selected(self):
        selected = list(self.listbox.curselection())
        for i in reversed(selected):
            self.listbox.delete(i)
            del self.exclusions[i]

    def _on_save(self):
        if self.on_save:
            self.on_save(self.exclusions)
        self.dialog.destroy()


class MoveFilesDialog:
    """Dialog for selecting destination to move files."""

    def __init__(self, parent, file_count: int, total_size: int):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Move Files")
        self.dialog.geometry("450x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Center
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Info
        ttk.Label(
            main_frame,
            text=f"Move {file_count} file(s) ({format_size(total_size)}) to:",
            font=('Segoe UI', 10)
        ).pack(anchor=tk.W, pady=(0, 15))

        # Destination selection
        dest_frame = ttk.Frame(main_frame)
        dest_frame.pack(fill=tk.X, pady=(0, 20))

        self.dest_var = tk.StringVar()
        self.dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=45)
        self.dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(
            dest_frame,
            text="Browse...",
            command=self._browse
        ).pack(side=tk.RIGHT)

        # Options
        self.keep_structure_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text="Keep folder structure",
            variable=self.keep_structure_var
        ).pack(anchor=tk.W)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Move",
            command=self._on_move
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT)

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.dialog.wait_window()

    def _browse(self):
        path = filedialog.askdirectory(parent=self.dialog, title="Select Destination Folder")
        if path:
            self.dest_var.set(path)

    def _on_move(self):
        dest = self.dest_var.get().strip()
        if dest and os.path.isdir(dest):
            self.result = {
                'destination': dest,
                'keep_structure': self.keep_structure_var.get()
            }
            self.dialog.destroy()
        else:
            show_error(self.dialog, "Invalid Path", "Please select a valid destination folder.")

    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()


class ProgressDialog:
    """Dialog showing progress for long operations."""

    def __init__(self, parent, title: str, message: str, maximum: int = 100):
        self.cancelled = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Center
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Message
        self.message_var = tk.StringVar(value=message)
        ttk.Label(
            main_frame,
            textvariable=self.message_var,
            font=('Segoe UI', 9)
        ).pack(anchor=tk.W, pady=(0, 10))

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=maximum,
            length=350
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Status
        self.status_var = tk.StringVar(value="")
        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 8)
        ).pack(anchor=tk.W)

        # Cancel button
        ttk.Button(
            main_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, pady=(10, 0))

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def update(self, value: int, status: str = None):
        """Update progress bar value and optional status text."""
        self.progress['value'] = value
        if status:
            self.status_var.set(status)
        self.dialog.update()

    def set_message(self, message: str):
        """Update the main message."""
        self.message_var.set(message)
        self.dialog.update()

    def _on_cancel(self):
        self.cancelled = True

    def close(self):
        """Close the dialog."""
        self.dialog.destroy()
