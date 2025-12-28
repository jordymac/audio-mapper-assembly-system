#!/usr/bin/env python3
"""
Voice Editor Component - Voice narration editor

Self-contained editor component for Voice markers.
Extracted from PromptEditorWindow as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import messagebox
from config.color_scheme import COLORS


class VoiceEditor:
    """Editor component for Voice markers"""

    def __init__(self, parent_frame, marker, parent_window):
        """
        Initialize Voice editor

        Args:
            parent_frame: Frame to create UI in
            marker: Marker dictionary to edit
            parent_window: Parent window (for messagebox parent)
        """
        self.parent_frame = parent_frame
        self.marker = marker
        self.parent_window = parent_window
        self.voice_profile_entry = None
        self.voice_text = None

        self.create_ui()

    def create_ui(self):
        """Create Voice editor UI"""
        # Ensure prompt_data exists
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {"voice_profile": "", "text": ""}

        prompt_data = self.marker["prompt_data"]

        # Voice Profile field
        tk.Label(
            self.parent_frame,
            text="Voice Profile:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.voice_profile_entry = tk.Entry(
            self.parent_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.voice_profile_entry.pack(fill=tk.X, pady=(0, 5))

        # Load existing voice profile
        voice_profile = prompt_data.get("voice_profile", "")
        if voice_profile:
            self.voice_profile_entry.insert(0, voice_profile)

        # Hint for voice profile
        tk.Label(
            self.parent_frame,
            text="Optional: e.g., 'Warm female narrator, Australian accent'",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Text to speak field
        tk.Label(
            self.parent_frame,
            text="Text to Speak:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.voice_text = tk.Text(
            self.parent_frame,
            height=4,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.voice_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Load existing text
        text = prompt_data.get("text", "")
        if text:
            self.voice_text.insert("1.0", text)

        # Set focus to show cursor (text field is required, so focus here)
        self.voice_text.focus_set()

        # Hint for text
        tk.Label(
            self.parent_frame,
            text="Required: The exact words to be spoken",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W)

    def validate_and_save(self):
        """
        Validate and save Voice data to marker

        Returns:
            bool: True if valid and saved, False otherwise
        """
        try:
            voice_profile = self.voice_profile_entry.get().strip()
            text = self.voice_text.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read voice data:\n{str(e)}",
                parent=self.parent_window
            )
            return False

        # Validation: text cannot be empty
        if not text:
            messagebox.showwarning(
                "Validation Error",
                "Text to speak cannot be empty",
                parent=self.parent_window
            )
            return False

        # Save to marker (voice_profile is optional, can be empty)
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {}
        self.marker["prompt_data"]["voice_profile"] = voice_profile
        self.marker["prompt_data"]["text"] = text
        return True
