"""Dialog windows for the disk cleaner app."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils import format_size


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
