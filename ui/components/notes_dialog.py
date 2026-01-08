"""
Notes Dialog - Modal dialog for entering version notes

Prompts user to enter notes explaining why they're creating a new version.
Used during audio generation/regeneration.
"""

import tkinter as tk
from tkinter import ttk
from config.color_scheme import COLORS, create_colored_button


class NotesDialog:
    """Modal dialog for entering version notes"""

    def __init__(self, parent, marker, next_version_num, is_first_generation=False):
        """
        Initialize the notes dialog

        Args:
            parent: Parent tk window
            marker: The marker being generated
            next_version_num: The version number that will be created
            is_first_generation: Whether this is the first generation (v1)
        """
        self.parent = parent
        self.marker = marker
        self.next_version_num = next_version_num
        self.is_first_generation = is_first_generation
        self.result = None  # Will contain notes if OK clicked, None if cancelled

        # Create modal window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Version Notes - v{next_version_num}")
        self.window.geometry("500x300")

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Center on parent
        self.center_on_parent()

        # Handle window close (treat as cancel)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Build UI
        self.create_ui()

        # Focus on text entry
        self.notes_text.focus_set()

    def center_on_parent(self):
        """Center this window on the parent window"""
        self.window.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get this window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Build the dialog UI"""
        # Header section
        header_frame = tk.Frame(self.window, padx=20, pady=15, bg=COLORS.bg_secondary)
        header_frame.pack(fill=tk.X)

        # Title based on whether it's first generation or regeneration
        if self.is_first_generation:
            title_text = f"Creating Version {self.next_version_num}"
            subtitle_text = "This is the initial audio generation for this marker."
        else:
            title_text = f"Creating Version {self.next_version_num}"
            current_version = self.marker.get('current_version', 0)
            subtitle_text = f"Regenerating from v{current_version} → v{self.next_version_num}"

        tk.Label(
            header_frame,
            text=title_text,
            font=("Arial", 12, "bold"),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(anchor=tk.W)

        tk.Label(
            header_frame,
            text=subtitle_text,
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_tertiary
        ).pack(anchor=tk.W, pady=(5, 0))

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Notes input section
        notes_frame = tk.Frame(self.window, padx=20, pady=10)
        notes_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            notes_frame,
            text="Notes (optional):",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        tk.Label(
            notes_frame,
            text="Explain why you're creating this version (e.g., 'Updated prompt for clarity', 'Fixed timing issue')",
            font=("Arial", 8),
            fg=COLORS.fg_tertiary
        ).pack(anchor=tk.W, pady=(0, 5))

        # Text widget with scrollbar
        text_frame = tk.Frame(notes_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.notes_text = tk.Text(
            text_frame,
            font=("Arial", 10),
            bg=COLORS.bg_input,
            fg=COLORS.fg_input,
            wrap=tk.WORD,
            height=6,
            yscrollcommand=scrollbar.set
        )
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.notes_text.yview)

        # Add default placeholder text
        if self.is_first_generation:
            placeholder = "Initial audio generation"
        else:
            placeholder = "Audio regeneration"

        self.notes_text.insert("1.0", placeholder)
        self.notes_text.tag_add("sel", "1.0", "end")  # Select all text

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Buttons
        button_frame = tk.Frame(self.window, padx=20, pady=15)
        button_frame.pack(fill=tk.X)

        # Cancel button
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT, padx=5)

        # OK button
        create_colored_button(
            button_frame,
            text="Continue",
            command=self.on_ok,
            bg_color=COLORS.btn_primary_bg,
            fg_color=COLORS.btn_primary_fg,
            width=12,
            height=1,
            font=("Arial", 10, "bold")
        ).pack(side=tk.RIGHT, padx=5)

        # Bind Enter key to OK
        self.notes_text.bind("<Control-Return>", lambda e: self.on_ok())

    def on_ok(self):
        """OK button - save notes and close"""
        # Get notes text
        notes = self.notes_text.get("1.0", "end-1c").strip()

        # If empty, use default based on generation type
        if not notes:
            notes = "Initial audio generation" if self.is_first_generation else "Audio regeneration"

        self.result = notes
        self.window.destroy()

    def on_cancel(self):
        """Cancel button - close without generating"""
        self.result = None
        self.window.destroy()

    def show(self):
        """
        Show the dialog and wait for user response

        Returns:
            str: Notes entered by user, or None if cancelled
        """
        # Wait for window to close
        self.window.wait_window()
        return self.result
