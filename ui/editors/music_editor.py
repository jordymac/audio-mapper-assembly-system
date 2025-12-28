#!/usr/bin/env python3
"""
Music Editor Component - Music composition editor

Self-contained editor component for Music markers.
Extracted from PromptEditorWindow as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import messagebox
from color_scheme import COLORS
from ui.editors.music_section_editor import MusicSectionEditorWindow


class MusicEditor:
    """Editor component for Music markers"""

    def __init__(self, parent_frame, marker, parent_window):
        """
        Initialize Music editor

        Args:
            parent_frame: Frame to create UI in
            marker: Marker dictionary to edit
            parent_window: Parent window (for messagebox parent and modal dialogs)
        """
        self.parent_frame = parent_frame
        self.marker = marker
        self.parent_window = parent_window
        self.music_positive_styles = None
        self.music_negative_styles = None
        self.music_sections_listbox = None

        self.create_ui()

    def create_ui(self):
        """Create Music editor UI"""
        # Ensure prompt_data exists with music structure
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        prompt_data = self.marker["prompt_data"]

        # Global Positive Styles
        tk.Label(
            self.parent_frame,
            text="Global Positive Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.music_positive_styles = tk.Text(
            self.parent_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.music_positive_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing positive styles
        positive_styles = prompt_data.get("positiveGlobalStyles", [])
        if positive_styles:
            self.music_positive_styles.insert("1.0", ", ".join(positive_styles))

        # Set focus to show cursor
        self.music_positive_styles.focus_set()

        # Hint for positive styles
        tk.Label(
            self.parent_frame,
            text="Comma-separated styles (e.g., 'electronic, fast-paced, energetic')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Global Negative Styles
        tk.Label(
            self.parent_frame,
            text="Global Negative Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.music_negative_styles = tk.Text(
            self.parent_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.music_negative_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing negative styles
        negative_styles = prompt_data.get("negativeGlobalStyles", [])
        if negative_styles:
            self.music_negative_styles.insert("1.0", ", ".join(negative_styles))

        # Hint for negative styles
        tk.Label(
            self.parent_frame,
            text="Comma-separated styles to avoid (e.g., 'acoustic, slow, ambient')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Sections
        tk.Label(
            self.parent_frame,
            text="Sections:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Sections listbox
        sections_frame = tk.Frame(self.parent_frame)
        sections_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.music_sections_listbox = tk.Listbox(
            sections_frame,
            height=4,
            font=("Arial", 10)
        )
        self.music_sections_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for sections
        scrollbar = tk.Scrollbar(sections_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.music_sections_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.music_sections_listbox.yview)

        # Double-click to edit section
        self.music_sections_listbox.bind("<Double-Button-1>", self.on_section_double_click)

        # Load existing sections
        self.update_sections_list()

        # Section buttons
        section_buttons_frame = tk.Frame(self.parent_frame)
        section_buttons_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            section_buttons_frame,
            text="+ Add Section",
            command=self.add_section,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            section_buttons_frame,
            text="Remove Section",
            command=self.remove_section,
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

    def update_sections_list(self):
        """Update the sections listbox display"""
        self.music_sections_listbox.delete(0, tk.END)

        sections = self.marker["prompt_data"].get("sections", [])
        for section in sections:
            name = section.get("sectionName", "Unnamed")
            duration = section.get("durationMs", 0)
            display = f"{name} - {duration}ms"
            self.music_sections_listbox.insert(tk.END, display)

    def add_section(self):
        """Add a new placeholder section"""
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        sections = self.marker["prompt_data"].get("sections", [])
        section_num = len(sections) + 1

        new_section = {
            "sectionName": f"Section {section_num}",
            "durationMs": 1000,
            "positiveLocalStyles": [],
            "negativeLocalStyles": [],
            "lines": []
        }

        sections.append(new_section)
        self.marker["prompt_data"]["sections"] = sections
        self.update_sections_list()

    def remove_section(self):
        """Remove selected section"""
        selection = self.music_sections_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "No Selection",
                "Please select a section to remove",
                parent=self.parent_window
            )
            return

        index = selection[0]
        sections = self.marker["prompt_data"].get("sections", [])
        sections.pop(index)
        self.marker["prompt_data"]["sections"] = sections
        self.update_sections_list()

    def on_section_double_click(self, event):
        """Handle double-click on section - open section editor"""
        selection = self.music_sections_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        sections = self.marker["prompt_data"].get("sections", [])
        if index >= len(sections):
            return

        section = sections[index]
        # Open nested section editor
        editor = MusicSectionEditorWindow(
            parent=self.parent_window,
            section=section,
            section_index=index,
            on_save_callback=self.on_section_edited
        )

    def on_section_edited(self, updated_section, index):
        """Callback when section is edited and saved"""
        sections = self.marker["prompt_data"].get("sections", [])
        sections[index] = updated_section
        self.marker["prompt_data"]["sections"] = sections
        self.update_sections_list()
        print(f"✓ Updated section at index {index}: {updated_section['sectionName']}")

    def validate_and_save(self):
        """
        Validate and save Music data to marker

        Returns:
            bool: True if valid and saved, False otherwise
        """
        try:
            # Get text from positive/negative styles fields
            positive_text = self.music_positive_styles.get("1.0", "end-1c").strip()
            negative_text = self.music_negative_styles.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read music data:\n{str(e)}",
                parent=self.parent_window
            )
            return False

        # Parse comma-separated styles into lists
        positive_styles = []
        if positive_text:
            positive_styles = [s.strip() for s in positive_text.split(",") if s.strip()]

        negative_styles = []
        if negative_text:
            negative_styles = [s.strip() for s in negative_text.split(",") if s.strip()]

        # Validation: At least one positive style should be provided
        if not positive_styles:
            messagebox.showwarning(
                "Validation Error",
                "Please provide at least one positive style for the music",
                parent=self.parent_window
            )
            return False

        # Save to marker (sections are already in prompt_data from add/remove operations)
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        self.marker["prompt_data"]["positiveGlobalStyles"] = positive_styles
        self.marker["prompt_data"]["negativeGlobalStyles"] = negative_styles
        # sections are already updated by add/remove methods
        return True
