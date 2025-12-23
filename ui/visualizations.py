"""Visualization components for disk usage analysis."""

import tkinter as tk
from tkinter import ttk
import math
from collections import defaultdict
import os
from utils import format_size


class CategoryPieChart(ttk.Frame):
    """Pie chart showing file distribution by category."""

    COLORS = [
        '#FF6B6B',  # Red - Video
        '#4ECDC4',  # Teal - Audio
        '#45B7D1',  # Blue - Image
        '#96CEB4',  # Green - Document
        '#FFEAA7',  # Yellow - Archive
        '#DDA0DD',  # Plum - Game
        '#98D8C8',  # Mint - Code
        '#B0B0B0',  # Gray - Other
    ]

    def __init__(self, parent, width=400, height=300):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.data = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create the pie chart canvas and legend."""
        # Title
        ttk.Label(
            self,
            text="Files by Category",
            font=('Segoe UI', 11, 'bold')
        ).pack(pady=(0, 10))

        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # Canvas for pie chart
        self.canvas = tk.Canvas(
            container,
            width=self.width - 150,
            height=self.height,
            bg='white',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Legend
        self.legend_frame = ttk.Frame(container)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

    def set_data(self, category_sizes: dict):
        """Set the data and redraw the chart."""
        self.data = category_sizes
        self._draw_chart()

    def _draw_chart(self):
        """Draw the pie chart."""
        self.canvas.delete("all")

        # Clear legend
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        if not self.data:
            self.canvas.create_text(
                self.canvas.winfo_width() // 2 or 125,
                self.canvas.winfo_height() // 2 or 150,
                text="No data",
                font=('Segoe UI', 10),
                fill='gray'
            )
            return

        # Calculate total
        total = sum(self.data.values())
        if total == 0:
            return

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width() or (self.width - 150)
        canvas_height = self.canvas.winfo_height() or self.height

        # Pie dimensions
        cx = canvas_width // 2
        cy = canvas_height // 2
        radius = min(cx, cy) - 20

        # Draw pie slices
        start_angle = 0
        categories = sorted(self.data.items(), key=lambda x: x[1], reverse=True)

        for i, (category, size) in enumerate(categories):
            if size == 0:
                continue

            # Calculate angle
            angle = (size / total) * 360
            color = self.COLORS[i % len(self.COLORS)]

            # Draw arc
            self.canvas.create_arc(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                start=start_angle,
                extent=angle,
                fill=color,
                outline='white',
                width=2
            )

            # Add legend entry
            legend_row = ttk.Frame(self.legend_frame)
            legend_row.pack(fill=tk.X, pady=2)

            # Color box
            color_box = tk.Canvas(legend_row, width=16, height=16, highlightthickness=0)
            color_box.pack(side=tk.LEFT, padx=(0, 5))
            color_box.create_rectangle(0, 0, 16, 16, fill=color, outline='')

            # Category name and size
            percent = (size / total) * 100
            text = f"{category}: {format_size(size)} ({percent:.1f}%)"
            ttk.Label(
                legend_row,
                text=text,
                font=('Segoe UI', 9)
            ).pack(side=tk.LEFT)

            start_angle += angle


class FolderSizeView(ttk.Frame):
    """Treeview showing folder sizes."""

    def __init__(self, parent):
        super().__init__(parent)
        self.folder_data = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create the folder size treeview."""
        # Title
        ttk.Label(
            self,
            text="Folders by Size",
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview
        columns = ('folder', 'size', 'files', 'percent')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=15)

        self.tree.heading('folder', text='Folder')
        self.tree.heading('size', text='Size')
        self.tree.heading('files', text='Files')
        self.tree.heading('percent', text='%')

        self.tree.column('folder', width=300)
        self.tree.column('size', width=100)
        self.tree.column('files', width=60)
        self.tree.column('percent', width=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def set_data(self, files: list):
        """Analyze files and show folder sizes."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not files:
            return

        # Aggregate by folder
        folder_stats = defaultdict(lambda: {'size': 0, 'count': 0})

        for file_dict in files:
            file_info = file_dict['file_info']
            folder = os.path.dirname(file_info.path)
            folder_stats[folder]['size'] += file_info.size
            folder_stats[folder]['count'] += 1

        # Calculate total
        total_size = sum(f['size'] for f in folder_stats.values())

        # Sort by size descending
        sorted_folders = sorted(
            folder_stats.items(),
            key=lambda x: x[1]['size'],
            reverse=True
        )

        # Show top 100 folders
        for folder, stats in sorted_folders[:100]:
            percent = (stats['size'] / total_size * 100) if total_size > 0 else 0
            self.tree.insert('', tk.END, values=(
                folder,
                format_size(stats['size']),
                stats['count'],
                f"{percent:.1f}%"
            ))


class TreemapView(ttk.Frame):
    """Treemap visualization of file/folder sizes."""

    COLORS = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
        '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
        '#BB8FCE', '#85C1E9', '#82E0AA', '#F8B500'
    ]

    def __init__(self, parent, width=600, height=400):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.rectangles = []

        self._create_widgets()

    def _create_widgets(self):
        """Create the treemap canvas."""
        # Title
        ttk.Label(
            self,
            text="Size Treemap (by Category)",
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))

        # Canvas
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg='white',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind hover for tooltip
        self.canvas.bind('<Motion>', self._on_hover)

        # Tooltip
        self.tooltip = None
        self.tooltip_id = None

    def set_data(self, category_sizes: dict):
        """Draw treemap from category sizes."""
        self.canvas.delete("all")
        self.rectangles = []

        if not category_sizes or sum(category_sizes.values()) == 0:
            self.canvas.create_text(
                self.width // 2, self.height // 2,
                text="No data",
                font=('Segoe UI', 10),
                fill='gray'
            )
            return

        # Get canvas size
        w = self.canvas.winfo_width() or self.width
        h = self.canvas.winfo_height() or self.height

        # Sort by size descending
        sorted_data = sorted(category_sizes.items(), key=lambda x: x[1], reverse=True)
        total = sum(category_sizes.values())

        # Simple treemap layout (squarified algorithm simplified)
        self._draw_treemap(sorted_data, 0, 0, w, h, total)

    def _draw_treemap(self, data, x, y, w, h, total, depth=0):
        """Draw treemap rectangles recursively."""
        if not data or w < 10 or h < 10:
            return

        if len(data) == 1:
            category, size = data[0]
            color = self.COLORS[depth % len(self.COLORS)]
            rect_id = self.canvas.create_rectangle(
                x + 1, y + 1, x + w - 1, y + h - 1,
                fill=color,
                outline='white',
                width=2
            )
            self.rectangles.append({
                'id': rect_id,
                'category': category,
                'size': size,
                'x': x, 'y': y, 'w': w, 'h': h
            })

            # Add label if space permits
            if w > 60 and h > 30:
                self.canvas.create_text(
                    x + w // 2, y + h // 2,
                    text=f"{category}\n{format_size(size)}",
                    font=('Segoe UI', 9),
                    fill='white',
                    justify=tk.CENTER
                )
            return

        # Split data into two groups
        mid = len(data) // 2
        left_data = data[:mid]
        right_data = data[mid:]

        left_total = sum(item[1] for item in left_data)
        right_total = sum(item[1] for item in right_data)

        if left_total + right_total == 0:
            return

        # Decide split direction
        if w > h:
            # Vertical split
            left_w = int(w * left_total / (left_total + right_total))
            self._draw_treemap(left_data, x, y, left_w, h, left_total, depth)
            self._draw_treemap(right_data, x + left_w, y, w - left_w, h, right_total, depth + 1)
        else:
            # Horizontal split
            top_h = int(h * left_total / (left_total + right_total))
            self._draw_treemap(left_data, x, y, w, top_h, left_total, depth)
            self._draw_treemap(right_data, x, y + top_h, w, h - top_h, right_total, depth + 1)

    def _on_hover(self, event):
        """Show tooltip on hover."""
        # Find rectangle under cursor
        for rect in self.rectangles:
            if (rect['x'] <= event.x <= rect['x'] + rect['w'] and
                rect['y'] <= event.y <= rect['y'] + rect['h']):

                # Show tooltip
                if self.tooltip_id:
                    self.canvas.delete(self.tooltip_id)

                text = f"{rect['category']}: {format_size(rect['size'])}"
                self.tooltip_id = self.canvas.create_text(
                    event.x + 10, event.y - 10,
                    text=text,
                    font=('Segoe UI', 9),
                    fill='black',
                    anchor=tk.NW
                )
                return

        # No rectangle found, hide tooltip
        if self.tooltip_id:
            self.canvas.delete(self.tooltip_id)
            self.tooltip_id = None


class VisualizationWindow:
    """Window containing all visualization components."""

    def __init__(self, parent, files: list):
        self.window = tk.Toplevel(parent)
        self.window.title("Disk Usage Visualization")
        self.window.geometry("900x600")
        self.window.transient(parent)

        self.files = files

        self._create_widgets()
        self._populate_data()

    def _create_widgets(self):
        """Create the visualization tabs."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Pie Chart
        pie_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(pie_frame, text="Category Breakdown")
        self.pie_chart = CategoryPieChart(pie_frame)
        self.pie_chart.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Folder Sizes
        folder_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(folder_frame, text="Folder Sizes")
        self.folder_view = FolderSizeView(folder_frame)
        self.folder_view.pack(fill=tk.BOTH, expand=True)

        # Tab 3: Treemap
        treemap_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(treemap_frame, text="Treemap")
        self.treemap = TreemapView(treemap_frame)
        self.treemap.pack(fill=tk.BOTH, expand=True)

        # Close button
        ttk.Button(
            self.window,
            text="Close",
            command=self.window.destroy
        ).pack(pady=(0, 10))

    def _populate_data(self):
        """Populate all visualizations with data."""
        if not self.files:
            return

        # Calculate category sizes
        category_sizes = defaultdict(int)
        for file_dict in self.files:
            category = file_dict['category']
            size = file_dict['file_info'].size
            category_sizes[category] += size

        # Update visualizations
        self.pie_chart.set_data(dict(category_sizes))
        self.folder_view.set_data(self.files)
        self.treemap.set_data(dict(category_sizes))
