#!/usr/bin/env python3
"""
Music Section Editor Window - Modal editor for music sections

Nested modal window for editing individual music sections within a music marker.
Extracted from audio_mapper.py as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.color_scheme import COLORS


class MusicSectionEditorWindow:
    """Modal pop-up window for editing a music section"""

    def __init__(self, parent, section, section_index, on_save_callback):
        """
        Initialize the section editor window

        Args:
            parent: Parent tk window (the PromptEditorWindow)
            section: The section dict to edit
            section_index: Index of section in sections list
            on_save_callback: Function to call when Save is clicked
        """
        self.parent = parent
        self.section = section.copy()  # Work on a copy
        self.section_index = section_index
        self.on_save_callback = on_save_callback

        # Create modal window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit Section: {section.get('sectionName', 'Unnamed')}")
        self.window.geometry("550x600")

        # Make modal on top of parent
        self.window.transient(parent)
        self.window.grab_set()

        # Center on parent
        self.center_on_parent()

        # Handle window close (treat as cancel)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Build UI
        self.create_ui()

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
        """Build the section editor UI"""
        content_frame = tk.Frame(self.window, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Section Name
        tk.Label(
            content_frame,
            text="Section Name:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.section_name_entry = tk.Entry(
            content_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.section_name_entry.pack(fill=tk.X, pady=(0, 15))
        section_name = self.section.get("sectionName", "")
        if section_name:
            self.section_name_entry.insert(0, section_name)

        # Set focus to show cursor
        self.section_name_entry.focus_set()

        # Duration (ms)
        tk.Label(
            content_frame,
            text="Duration (ms):",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.duration_entry = tk.Entry(
            content_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.duration_entry.pack(fill=tk.X, pady=(0, 5))
        self.duration_entry.insert(0, str(self.section.get("durationMs", 1000)))

        tk.Label(
            content_frame,
            text="Duration in milliseconds (e.g., 3000 = 3 seconds)",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Positive Local Styles
        tk.Label(
            content_frame,
            text="Positive Local Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.positive_styles = tk.Text(
            content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.positive_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing positive styles
        positive = self.section.get("positiveLocalStyles", [])
        if positive:
            self.positive_styles.insert("1.0", ", ".join(positive))

        tk.Label(
            content_frame,
            text="Comma-separated (e.g., 'rising synth arpeggio, energetic')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Negative Local Styles
        tk.Label(
            content_frame,
            text="Negative Local Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.negative_styles = tk.Text(
            content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.negative_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing negative styles
        negative = self.section.get("negativeLocalStyles", [])
        if negative:
            self.negative_styles.insert("1.0", ", ".join(negative))

        tk.Label(
            content_frame,
            text="Comma-separated styles to avoid (e.g., 'soft pads, ambient')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Buttons
        button_frame = tk.Frame(self.window, padx=20, pady=15)
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            button_frame,
            text="Save",
            command=self.on_save,
            bg=COLORS.btn_primary_bg,
            fg=COLORS.btn_primary_fg,
            width=12,
            font=("Arial", 10, "bold")
        ).pack(side=tk.RIGHT, padx=5)

    def on_cancel(self):
        """Cancel button - close without saving"""
        try:
            self.window.destroy()
        except Exception as e:
            print(f"Warning: Error closing section editor window: {e}")

    def on_save(self):
        """Save button - validate and save changes"""
        try:
            # Get section name
            section_name = self.section_name_entry.get().strip()
            if not section_name:
                messagebox.showwarning(
                    "Validation Error",
                    "Section name cannot be empty",
                    parent=self.window
                )
                return

            # Get and validate duration
            try:
                duration = int(self.duration_entry.get().strip())
                if duration <= 0:
                    raise ValueError("Duration must be positive")
            except ValueError:
                messagebox.showwarning(
                    "Validation Error",
                    "Duration must be a positive number in milliseconds",
                    parent=self.window
                )
                return

            # Get styles
            positive_text = self.positive_styles.get("1.0", "end-1c").strip()
            positive_list = [s.strip() for s in positive_text.split(",") if s.strip()] if positive_text else []

            negative_text = self.negative_styles.get("1.0", "end-1c").strip()
            negative_list = [s.strip() for s in negative_text.split(",") if s.strip()] if negative_text else []

            # Update section
            self.section["sectionName"] = section_name
            self.section["durationMs"] = duration
            self.section["positiveLocalStyles"] = positive_list
            self.section["negativeLocalStyles"] = negative_list

            # Call callback and close
            try:
                self.on_save_callback(self.section, self.section_index)
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save section:\n{str(e)}",
                    parent=self.window
                )
                return

            try:
                self.window.destroy()
            except Exception as e:
                print(f"Warning: Error closing section editor window: {e}")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred:\n{str(e)}",
                parent=self.window
            )
            print(f"Error in section editor on_save: {e}")
            import traceback
            traceback.print_exc()
