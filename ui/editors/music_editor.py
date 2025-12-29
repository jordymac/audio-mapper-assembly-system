#!/usr/bin/env python3
"""
Music Editor Component - Music composition editor

Self-contained editor component for Music markers.
Extracted from PromptEditorWindow as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import messagebox
import os
from config.color_scheme import COLORS
from ui.editors.music_section_editor import MusicSectionEditorWindow
from managers.waveform_manager import WaveformManager


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

        # Audio preview components
        self.waveform_canvas = None
        self.waveform_data = None
        self.audio_duration_ms = 0
        self.offset_indicator_id = None  # Canvas ID for offset line
        self.offset_ms_var = None  # StringVar for offset input
        self.fade_in_var = None
        self.fade_out_var = None

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

        # Audio Preview Section (only if audio is generated)
        if self.has_generated_audio():
            self.create_audio_preview_section()

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
            "durationMs": 30000,
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

        # Save assembly config if audio preview is active
        if self.has_generated_audio():
            self.save_assembly_config()

        return True

    # ========================================================================
    # AUDIO PREVIEW SECTION (Music Offset & Fades)
    # ========================================================================

    def has_generated_audio(self):
        """Check if this marker has generated audio"""
        # Check if marker has current_version > 0 (audio was generated)
        return self.marker.get("current_version", 0) > 0

    def create_audio_preview_section(self):
        """Create audio preview section with waveform and offset controls"""
        # Audio Preview Frame
        preview_frame = tk.LabelFrame(
            self.parent_frame,
            text="🎵 Audio Preview & Assembly Settings",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10,
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        )
        preview_frame.pack(fill=tk.X, pady=(0, 15))

        # Waveform Canvas (400px × 60px)
        self.waveform_canvas = tk.Canvas(
            preview_frame,
            width=400,
            height=60,
            bg=COLORS.bg_tertiary,
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        self.waveform_canvas.pack(pady=(0, 10))

        # Bind click event for offset selection
        self.waveform_canvas.bind("<Button-1>", self.on_waveform_click)

        # Load and draw waveform
        self.load_waveform()

        # Controls Frame
        controls_frame = tk.Frame(preview_frame, bg=COLORS.bg_secondary)
        controls_frame.pack(fill=tk.X)

        # Offset Control
        offset_frame = tk.Frame(controls_frame, bg=COLORS.bg_secondary)
        offset_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            offset_frame,
            text="Music Start Offset (MM:SS):",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.offset_ms_var = tk.StringVar(value="00:00")
        offset_entry = tk.Entry(
            offset_frame,
            textvariable=self.offset_ms_var,
            width=8,
            font=("Arial", 10),
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        offset_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Load existing offset
        assembly_config = self.marker.get("assemblyConfig", {})
        start_offset_ms = assembly_config.get("startOffsetMs", 0)
        self.offset_ms_var.set(self.format_time(start_offset_ms))

        # Update offset indicator when user types
        self.offset_ms_var.trace_add("write", lambda *args: self.on_offset_changed())

        tk.Label(
            offset_frame,
            text="(Click waveform to set)",
            font=("Arial", 8),
            fg=COLORS.placeholder_text,
            bg=COLORS.bg_secondary
        ).pack(side=tk.LEFT)

        # Fade Controls
        fade_frame = tk.Frame(controls_frame, bg=COLORS.bg_secondary)
        fade_frame.pack(side=tk.RIGHT)

        tk.Label(
            fade_frame,
            text="Fade In:",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.fade_in_var = tk.StringVar(value="50")
        fade_in_entry = tk.Entry(
            fade_frame,
            textvariable=self.fade_in_var,
            width=5,
            font=("Arial", 9),
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        fade_in_entry.pack(side=tk.LEFT, padx=(0, 2))

        tk.Label(
            fade_frame,
            text="ms",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            fade_frame,
            text="Fade Out:",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.fade_out_var = tk.StringVar(value="50")
        fade_out_entry = tk.Entry(
            fade_frame,
            textvariable=self.fade_out_var,
            width=5,
            font=("Arial", 9),
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        fade_out_entry.pack(side=tk.LEFT, padx=(0, 2))

        tk.Label(
            fade_frame,
            text="ms",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT)

        # Load existing fade values
        self.fade_in_var.set(str(assembly_config.get("fadeInMs", 50)))
        self.fade_out_var.set(str(assembly_config.get("fadeOutMs", 50)))

        # Draw initial offset indicator
        self.update_offset_indicator(start_offset_ms)

    def load_waveform(self):
        """Load waveform data from audio file"""
        # Get audio file path (check versions for current version)
        versions = self.marker.get("versions", [])
        current_version = self.marker.get("current_version", 0)

        if not versions or current_version == 0:
            self.draw_waveform_placeholder("No audio generated yet")
            return

        # Get current version data
        version_data = versions[current_version - 1]  # Versions are 1-indexed
        asset_file = version_data.get("asset_file")

        if not asset_file:
            self.draw_waveform_placeholder("No audio file")
            return

        # Find audio file path
        audio_path = None
        possible_paths = [
            os.path.join("generated_audio", asset_file),
            os.path.join("generated_audio", "music", asset_file),
            asset_file
        ]

        for path in possible_paths:
            if os.path.exists(path):
                audio_path = path
                break

        if not audio_path:
            self.draw_waveform_placeholder("Audio file not found")
            return

        # Extract waveform using WaveformManager
        self.waveform_data, self.audio_duration_ms = WaveformManager.extract_waveform_from_audio(
            audio_path,
            target_width=400  # Match canvas width
        )

        if self.waveform_data:
            self.draw_waveform()
        else:
            self.draw_waveform_placeholder("Failed to load waveform")

    def draw_waveform(self):
        """Draw waveform on canvas"""
        if not self.waveform_data or not self.waveform_canvas:
            return

        # Clear canvas
        self.waveform_canvas.delete("all")

        canvas_width = 400
        canvas_height = 60
        mid_y = canvas_height // 2

        # Draw waveform bars
        for i, amplitude in enumerate(self.waveform_data):
            x = int((i / len(self.waveform_data)) * canvas_width)
            height = int(amplitude * (canvas_height / 2) * 0.9)

            self.waveform_canvas.create_line(
                x, mid_y - height,
                x, mid_y + height,
                fill=COLORS.waveform_color,
                width=1,
                tags="waveform"
            )

        # Draw center line
        self.waveform_canvas.create_line(
            0, mid_y,
            canvas_width, mid_y,
            fill=COLORS.centerline,
            width=1,
            tags="centerline"
        )

    def draw_waveform_placeholder(self, text: str):
        """Draw placeholder text on waveform canvas"""
        if not self.waveform_canvas:
            return

        self.waveform_canvas.delete("all")
        self.waveform_canvas.create_text(
            200, 30,  # Center of 400×60 canvas
            text=text,
            fill=COLORS.placeholder_text,
            font=("Arial", 9),
            tags="placeholder"
        )

    def update_offset_indicator(self, offset_ms):
        """Draw/update offset indicator line on waveform"""
        if not self.waveform_canvas or not self.waveform_data:
            return

        # Remove old indicator
        self.waveform_canvas.delete("offset_indicator")

        if self.audio_duration_ms == 0:
            return

        # Calculate x position based on offset
        canvas_width = 400
        x_pos = int((offset_ms / self.audio_duration_ms) * canvas_width)

        # Draw vertical line at offset position
        self.offset_indicator_id = self.waveform_canvas.create_line(
            x_pos, 0,
            x_pos, 60,
            fill="#FF9800",  # Orange indicator
            width=2,
            tags="offset_indicator"
        )

        # Add small label
        self.waveform_canvas.create_text(
            x_pos, 5,
            text="▼",
            fill="#FF9800",
            font=("Arial", 8),
            tags="offset_indicator"
        )

    def on_waveform_click(self, event):
        """Handle click on waveform to set offset"""
        if not self.waveform_data or self.audio_duration_ms == 0:
            return

        canvas_width = 400
        x_pos = event.x

        # Calculate time from click position
        offset_ms = int((x_pos / canvas_width) * self.audio_duration_ms)

        # Clamp to valid range (0 to audio_duration)
        offset_ms = max(0, min(offset_ms, self.audio_duration_ms))

        # Update offset input field
        self.offset_ms_var.set(self.format_time(offset_ms))

        # Update indicator
        self.update_offset_indicator(offset_ms)

    def on_offset_changed(self):
        """Called when offset input changes (user types)"""
        try:
            offset_ms = self.parse_time(self.offset_ms_var.get())
            self.update_offset_indicator(offset_ms)
        except:
            pass  # Invalid format, ignore

    def format_time(self, ms: int) -> str:
        """Convert milliseconds to MM:SS format"""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def parse_time(self, time_str: str) -> int:
        """Convert MM:SS format to milliseconds"""
        parts = time_str.split(":")
        if len(parts) != 2:
            return 0
        minutes = int(parts[0])
        seconds = int(parts[1])
        return (minutes * 60 + seconds) * 1000

    def save_assembly_config(self):
        """Save assembly configuration to marker"""
        try:
            offset_ms = self.parse_time(self.offset_ms_var.get())
            fade_in_ms = int(self.fade_in_var.get())
            fade_out_ms = int(self.fade_out_var.get())

            assembly_config = {
                "startOffsetMs": offset_ms,
                "fadeInMs": fade_in_ms,
                "fadeOutMs": fade_out_ms,
                "targetDurationMs": None  # Reserved for future use
            }

            self.marker["assemblyConfig"] = assembly_config
            print(f"✓ Saved assembly config: offset={offset_ms}ms, fade_in={fade_in_ms}ms, fade_out={fade_out_ms}ms")

        except Exception as e:
            print(f"⚠ Failed to save assembly config: {e}")
