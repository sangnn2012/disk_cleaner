"""Preview pane for showing file previews and information."""

import tkinter as tk
from tkinter import ttk
import os
from utils import format_size, format_date, days_since

# Check if PIL is available for image previews
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageTk = None


class PreviewPane(ttk.Frame):
    """A panel showing preview/info for selected files."""

    # Image extensions that can be previewed
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.ico'}

    # Video extensions (show placeholder)
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}

    def __init__(self, parent, width=300):
        super().__init__(parent, width=width)
        self.pack_propagate(False)  # Maintain fixed width

        self.current_file = None
        self.photo_image = None  # Keep reference to prevent garbage collection

        self._create_widgets()

    def _create_widgets(self):
        """Create the preview pane widgets."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            header_frame,
            text="Preview",
            font=('Segoe UI', 11, 'bold')
        ).pack(side=tk.LEFT)

        # Preview area (for images)
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Canvas for image preview
        self.canvas = tk.Canvas(
            self.preview_frame,
            bg='#f0f0f0',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Placeholder label (shown when no preview available)
        self.placeholder_label = ttk.Label(
            self.canvas,
            text="Select a file\nto preview",
            font=('Segoe UI', 10),
            justify=tk.CENTER,
            foreground='gray'
        )
        self.canvas.create_window(
            150, 100,
            window=self.placeholder_label,
            anchor=tk.CENTER
        )

        # Info section
        self.info_frame = ttk.LabelFrame(self, text="File Info", padding=10)
        self.info_frame.pack(fill=tk.X, padx=10, pady=10)

        # Info labels
        self.info_labels = {}
        info_items = ['Name:', 'Type:', 'Size:', 'Last Accessed:', 'Days Old:']

        for item in info_items:
            row = ttk.Frame(self.info_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(
                row,
                text=item,
                font=('Segoe UI', 9, 'bold'),
                width=12,
                anchor=tk.W
            ).pack(side=tk.LEFT)

            value_label = ttk.Label(
                row,
                text="-",
                font=('Segoe UI', 9),
                wraplength=180
            )
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.info_labels[item] = value_label

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.open_btn = ttk.Button(
            btn_frame,
            text="Open File",
            command=self._open_file,
            state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.location_btn = ttk.Button(
            btn_frame,
            text="Open Location",
            command=self._open_location,
            state=tk.DISABLED
        )
        self.location_btn.pack(side=tk.LEFT)

    def show_file(self, file_dict: dict):
        """Show preview for a file."""
        if not file_dict:
            self.clear()
            return

        self.current_file = file_dict
        file_info = file_dict['file_info']
        category = file_dict['category']

        # Update info labels
        self.info_labels['Name:'].config(text=file_info.name)
        self.info_labels['Type:'].config(text=category)
        self.info_labels['Size:'].config(text=format_size(file_info.size))
        self.info_labels['Last Accessed:'].config(text=format_date(file_info.last_accessed))
        self.info_labels['Days Old:'].config(text=f"{days_since(file_info.last_accessed)} days")

        # Enable buttons
        self.open_btn.config(state=tk.NORMAL)
        self.location_btn.config(state=tk.NORMAL)

        # Show preview based on file type
        ext = file_info.extension.lower()

        if HAS_PIL and ext in self.IMAGE_EXTENSIONS:
            self._show_image_preview(file_info.path)
        elif ext in self.VIDEO_EXTENSIONS:
            self._show_video_placeholder(file_info.name)
        else:
            self._show_file_icon(category)

    def _show_image_preview(self, path: str):
        """Show image preview."""
        try:
            # Load and resize image
            img = Image.open(path)

            # Calculate size to fit canvas
            canvas_width = self.canvas.winfo_width() or 280
            canvas_height = self.canvas.winfo_height() or 200

            # Maintain aspect ratio
            img_ratio = img.width / img.height
            canvas_ratio = canvas_width / canvas_height

            if img_ratio > canvas_ratio:
                new_width = min(canvas_width - 20, img.width)
                new_height = int(new_width / img_ratio)
            else:
                new_height = min(canvas_height - 20, img.height)
                new_width = int(new_height * img_ratio)

            # Resize
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(img)

            # Clear canvas and show image
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.photo_image,
                anchor=tk.CENTER
            )

        except Exception:
            self._show_file_icon("Image")

    def _show_video_placeholder(self, name: str):
        """Show video placeholder."""
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width() or 280
        canvas_height = self.canvas.winfo_height() or 200

        # Draw play button icon
        cx, cy = canvas_width // 2, canvas_height // 2

        # Background circle
        self.canvas.create_oval(
            cx - 40, cy - 40, cx + 40, cy + 40,
            fill='#666666',
            outline='#444444',
            width=2
        )

        # Play triangle
        self.canvas.create_polygon(
            cx - 15, cy - 25,
            cx - 15, cy + 25,
            cx + 25, cy,
            fill='white'
        )

        # Label
        self.canvas.create_text(
            cx, cy + 60,
            text="Video File",
            font=('Segoe UI', 10),
            fill='#666666'
        )

    def _show_file_icon(self, category: str):
        """Show generic file icon."""
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width() or 280
        canvas_height = self.canvas.winfo_height() or 200
        cx, cy = canvas_width // 2, canvas_height // 2

        # Draw file icon
        # Page shape
        self.canvas.create_polygon(
            cx - 30, cy - 45,
            cx + 15, cy - 45,
            cx + 30, cy - 30,
            cx + 30, cy + 45,
            cx - 30, cy + 45,
            fill='#e0e0e0',
            outline='#999999',
            width=2
        )

        # Folded corner
        self.canvas.create_polygon(
            cx + 15, cy - 45,
            cx + 15, cy - 30,
            cx + 30, cy - 30,
            fill='#cccccc',
            outline='#999999'
        )

        # Category label
        self.canvas.create_text(
            cx, cy + 65,
            text=category,
            font=('Segoe UI', 10),
            fill='#666666'
        )

    def clear(self):
        """Clear the preview pane."""
        self.current_file = None
        self.photo_image = None

        # Reset info labels
        for label in self.info_labels.values():
            label.config(text="-")

        # Disable buttons
        self.open_btn.config(state=tk.DISABLED)
        self.location_btn.config(state=tk.DISABLED)

        # Show placeholder
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width() or 280
        canvas_height = self.canvas.winfo_height() or 200

        self.canvas.create_text(
            canvas_width // 2,
            canvas_height // 2,
            text="Select a file\nto preview",
            font=('Segoe UI', 10),
            fill='gray',
            justify=tk.CENTER
        )

    def _open_file(self):
        """Open the current file."""
        if self.current_file:
            path = self.current_file['file_info'].path
            try:
                os.startfile(path)
            except OSError:
                pass

    def _open_location(self):
        """Open the file's location."""
        if self.current_file:
            import subprocess
            path = self.current_file['file_info'].path
            try:
                subprocess.run(['explorer', '/select,', path], check=False)
            except Exception:
                pass
