#!/usr/bin/env python3
"""
Disk Space Analyzer - Find and delete unused files to free up space.

Usage:
    python main.py

Requirements:
    - Python 3.8+
    - tkinter (usually included with Python)
    - send2trash (for safe deletion): pip install send2trash
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path

# Add project root to path for imports when running directly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow


def configure_styles():
    """Configure ttk styles for a modern look."""
    style = ttk.Style()

    # Try to use a modern theme
    available_themes = style.theme_names()
    if 'vista' in available_themes:
        style.theme_use('vista')
    elif 'clam' in available_themes:
        style.theme_use('clam')

    # Configure treeview
    style.configure(
        "Treeview",
        rowheight=25,
        font=('Segoe UI', 9)
    )
    style.configure(
        "Treeview.Heading",
        font=('Segoe UI', 9, 'bold')
    )


def main():
    """Main entry point."""
    root = tk.Tk()

    configure_styles()

    app = MainWindow(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')

    root.mainloop()


if __name__ == '__main__':
    main()
