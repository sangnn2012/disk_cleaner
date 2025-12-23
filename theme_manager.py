"""Theme manager for dark/light mode support."""

import tkinter as tk
from tkinter import ttk


# Light theme colors
LIGHT_THEME = {
    'bg': '#ffffff',
    'fg': '#000000',
    'select_bg': '#0078d7',
    'select_fg': '#ffffff',
    'tree_bg': '#ffffff',
    'tree_fg': '#000000',
    'tree_select_bg': '#0078d7',
    'tree_select_fg': '#ffffff',
    'entry_bg': '#ffffff',
    'entry_fg': '#000000',
    'button_bg': '#e1e1e1',
    'frame_bg': '#f0f0f0',
    'label_bg': '#f0f0f0',
    'label_fg': '#000000',
    'canvas_bg': '#ffffff',
    'menu_bg': '#ffffff',
    'menu_fg': '#000000',
}

# Dark theme colors
DARK_THEME = {
    'bg': '#2d2d2d',
    'fg': '#e0e0e0',
    'select_bg': '#0078d7',
    'select_fg': '#ffffff',
    'tree_bg': '#1e1e1e',
    'tree_fg': '#e0e0e0',
    'tree_select_bg': '#264f78',
    'tree_select_fg': '#ffffff',
    'entry_bg': '#3c3c3c',
    'entry_fg': '#e0e0e0',
    'button_bg': '#3c3c3c',
    'frame_bg': '#2d2d2d',
    'label_bg': '#2d2d2d',
    'label_fg': '#e0e0e0',
    'canvas_bg': '#1e1e1e',
    'menu_bg': '#2d2d2d',
    'menu_fg': '#e0e0e0',
}


class ThemeManager:
    """Manages application theme (light/dark mode)."""

    def __init__(self, root):
        self.root = root
        self.is_dark = False
        self.theme = LIGHT_THEME

    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode."""
        self.is_dark = enabled
        self.theme = DARK_THEME if enabled else LIGHT_THEME
        self._apply_theme()

    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.set_dark_mode(not self.is_dark)

    def _apply_theme(self):
        """Apply the current theme to all widgets."""
        theme = self.theme

        # Configure ttk style
        style = ttk.Style()

        # Try different theme bases
        try:
            if self.is_dark:
                style.theme_use('clam')  # clam is easier to customize
            else:
                if 'vista' in style.theme_names():
                    style.theme_use('vista')
                elif 'clam' in style.theme_names():
                    style.theme_use('clam')
        except tk.TclError:
            pass

        # Configure frame
        style.configure('TFrame', background=theme['frame_bg'])

        # Configure label
        style.configure('TLabel',
            background=theme['label_bg'],
            foreground=theme['label_fg']
        )

        # Configure button
        style.configure('TButton',
            background=theme['button_bg'],
            foreground=theme['fg']
        )
        style.map('TButton',
            background=[('active', theme['select_bg'])],
            foreground=[('active', theme['select_fg'])]
        )

        # Configure entry
        style.configure('TEntry',
            fieldbackground=theme['entry_bg'],
            foreground=theme['entry_fg']
        )

        # Configure combobox
        style.configure('TCombobox',
            fieldbackground=theme['entry_bg'],
            foreground=theme['entry_fg'],
            background=theme['button_bg']
        )

        # Configure treeview
        style.configure('Treeview',
            background=theme['tree_bg'],
            foreground=theme['tree_fg'],
            fieldbackground=theme['tree_bg']
        )
        style.configure('Treeview.Heading',
            background=theme['button_bg'],
            foreground=theme['fg']
        )
        style.map('Treeview',
            background=[('selected', theme['tree_select_bg'])],
            foreground=[('selected', theme['tree_select_fg'])]
        )

        # Configure labelframe
        style.configure('TLabelframe',
            background=theme['frame_bg']
        )
        style.configure('TLabelframe.Label',
            background=theme['frame_bg'],
            foreground=theme['label_fg']
        )

        # Configure checkbutton
        style.configure('TCheckbutton',
            background=theme['frame_bg'],
            foreground=theme['label_fg']
        )

        # Configure notebook
        style.configure('TNotebook',
            background=theme['frame_bg']
        )
        style.configure('TNotebook.Tab',
            background=theme['button_bg'],
            foreground=theme['fg'],
            padding=[10, 5]
        )
        style.map('TNotebook.Tab',
            background=[('selected', theme['frame_bg'])],
            foreground=[('selected', theme['fg'])]
        )

        # Configure progressbar
        style.configure('TProgressbar',
            background=theme['select_bg']
        )

        # Configure scrollbar
        style.configure('TScrollbar',
            background=theme['button_bg'],
            troughcolor=theme['frame_bg']
        )

        # Configure separator
        style.configure('TSeparator',
            background=theme['fg']
        )

        # Update root window
        self.root.configure(bg=theme['frame_bg'])

        # Update all menus recursively
        self._update_menus(self.root, theme)

    def _update_menus(self, widget, theme):
        """Update menu colors recursively."""
        try:
            menu = self.root.nametowidget(self.root.cget('menu'))
            self._style_menu(menu, theme)
        except (tk.TclError, KeyError):
            pass

    def _style_menu(self, menu, theme):
        """Apply theme to a menu widget."""
        try:
            menu.configure(
                bg=theme['menu_bg'],
                fg=theme['menu_fg'],
                activebackground=theme['select_bg'],
                activeforeground=theme['select_fg']
            )
            # Update submenus
            last = menu.index('end')
            if last is not None:
                for i in range(last + 1):
                    try:
                        submenu = menu.nametowidget(menu.entrycget(i, 'menu'))
                        self._style_menu(submenu, theme)
                    except (tk.TclError, KeyError):
                        pass
        except tk.TclError:
            pass


def apply_dark_theme(root):
    """Apply dark theme to application."""
    manager = ThemeManager(root)
    manager.set_dark_mode(True)
    return manager


def apply_light_theme(root):
    """Apply light theme to application."""
    manager = ThemeManager(root)
    manager.set_dark_mode(False)
    return manager
