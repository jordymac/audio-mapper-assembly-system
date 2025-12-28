#!/usr/bin/env python3
"""
SFX Editor Component - Sound effect description editor

Self-contained editor component for SFX markers.
Extracted from PromptEditorWindow as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import messagebox
from config.color_scheme import COLORS


class SfxEditor:
    """Editor component for SFX markers"""

    def __init__(self, parent_frame, marker, parent_window):
        """
        Initialize SFX editor

        Args:
            parent_frame: Frame to create UI in
            marker: Marker dictionary to edit
            parent_window: Parent window (for messagebox parent)
        """
        self.parent_frame = parent_frame
        self.marker = marker
        self.parent_window = parent_window
        self.sfx_description = None

        self.create_ui()

    def create_ui(self):
        """Create SFX editor UI"""
        # Ensure prompt_data exists
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {"description": ""}

        prompt_data = self.marker["prompt_data"]

        # Label
        tk.Label(
            self.parent_frame,
            text="SFX Description:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Multi-line text entry
        self.sfx_description = tk.Text(
            self.parent_frame,
            height=4,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.sfx_description.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Load existing description
        description = prompt_data.get("description", "")
        if description:
            self.sfx_description.insert("1.0", description)

        # Set focus to show cursor
        self.sfx_description.focus_set()

        # Hint text
        tk.Label(
            self.parent_frame,
            text="Describe the sound effect to be generated (e.g., 'UI click, subtle, clean')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W)

    def validate_and_save(self):
        """
        Validate and save SFX data to marker

        Returns:
            bool: True if valid and saved, False otherwise
        """
        try:
            description = self.sfx_description.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read SFX description:\n{str(e)}",
                parent=self.parent_window
            )
            return False

        # Validation: description cannot be empty
        if not description:
            messagebox.showwarning(
                "Validation Error",
                "SFX description cannot be empty",
                parent=self.parent_window
            )
            return False

        # Save to marker
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {}
        self.marker["prompt_data"]["description"] = description
        return True
