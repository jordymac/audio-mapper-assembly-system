#!/usr/bin/env python3
"""
Export Center Window - Metadata editing and export functionality
Based on METADATA_EXPORT_PLAN.md

METADATA ARCHITECTURE:
This window implements a two-level metadata structure:

1. ASSET METADATA (Global):
   - Stored in {AUDIO_FILE}_metadata.json
   - Properties: categories, title, notes, pro_tier, speaker_voice_id (voice)
   - Same for all templates that use this asset

2. TEMPLATE DATA (Per-Use):
   - Stored in usedInTemplates[] array within asset metadata
   - Each entry: {template_id, timestamp_ms, script_text (voice only)}
   - Varies per template

Key Points:
- timestamp_ms is template-specific (where asset is used in that template)
- script_text (voice) is template-specific (what's said in that template)
- speaker_voice_id (voice) is global (voice talent identifier)
- All categories and pro_tier are global (audio properties)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.models import Marker
from core.categories import (
    SFX_CATEGORIES,
    MUSIC_GENRES, MUSIC_KEYS, MUSIC_INSTRUMENTS, MUSIC_MOODS, MUSIC_INTENSITY_LEVELS,
    VOICE_GENDERS, VOICE_AGE_GROUPS, VOICE_ACCENTS, VOICE_TONES, VOICE_DELIVERY_STYLES,
    get_default_categories, validate_categories
)


class ExportCenterWindow:
    """
    Export Center UI - Metadata editing and file export

    Features:
    - Left panel: List of generated markers with checkmarks
    - Right panel: Metadata editor (title, categories, notes)
    - Type-specific category fields (SFX, Music, Voice)
    - Save Metadata button
    - Export All Files button
    """

    def __init__(
        self,
        parent,
        markers: List,
        template_id: str,
        template_name: str,
        duration_ms: int,
        video_reference: str,
        assembly_service,
        on_export_complete=None
    ):
        """
        Initialize Export Center window

        Args:
            parent: Parent Tk window
            markers: List of markers
            template_id: Template ID
            template_name: Template name
            duration_ms: Duration in milliseconds
            video_reference: Video filename
            assembly_service: Assembly service instance
            on_export_complete: Callback after export completes
        """
        self.parent = parent
        self.markers = markers
        self.template_id = template_id
        self.template_name = template_name
        self.duration_ms = duration_ms
        self.video_reference = video_reference
        self.assembly_service = assembly_service
        self.on_export_complete = on_export_complete

        # Current selected marker
        self.selected_marker = None
        self.selected_marker_index = None

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Export Center - {template_id}_{template_name}")
        self.window.geometry("1000x700")

        # Build UI
        self.create_ui()

        # Populate marker list
        self.populate_marker_list()

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

    def _get_marker_asset_file(self, marker) -> str:
        """Extract asset_file from marker, checking versions if available"""
        if isinstance(marker, dict):
            versions = marker.get('versions', [])
            if versions:
                current_version = marker.get('current_version', 1)
                current_version_data = next(
                    (v for v in versions if v.get('version') == current_version),
                    versions[-1] if versions else {}
                )
                return current_version_data.get('asset_file', '')
            return marker.get('asset_file', '')
        else:
            if marker.versions:
                current_version_data = next(
                    (v for v in marker.versions if v.version == marker.current_version),
                    marker.versions[-1] if marker.versions else None
                )
                return current_version_data.asset_file if current_version_data else marker.asset_file
            return marker.asset_file

    def create_ui(self):
        """Create the UI layout"""
        # Main container
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Two-panel layout
        left_panel = tk.Frame(main_frame, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)

        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # LEFT PANEL: Marker list
        self.create_marker_list_panel(left_panel)

        # RIGHT PANEL: Metadata editor
        self.create_metadata_editor_panel(right_panel)

        # BOTTOM: Export All button
        bottom_frame = tk.Frame(self.window)
        bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        export_all_btn = tk.Button(
            bottom_frame,
            text="📦 Export All Files",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="black",
            padx=20,
            pady=10,
            command=self.export_all_files
        )
        export_all_btn.pack()

    def create_marker_list_panel(self, parent):
        """Create left panel with marker list"""
        label = tk.Label(parent, text="Generated Audio", font=("Arial", 12, "bold"))
        label.pack(pady=(0, 10))

        # Scrollable listbox
        list_frame = tk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.marker_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            selectmode=tk.SINGLE
        )
        self.marker_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.marker_listbox.yview)

        # Bind selection
        self.marker_listbox.bind('<<ListboxSelect>>', self.on_marker_selected)

    def create_metadata_editor_panel(self, parent):
        """Create right panel with metadata editor"""
        label = tk.Label(parent, text="Metadata & Preview", font=("Arial", 12, "bold"))
        label.pack(pady=(0, 10))

        # Scrollable editor area
        canvas = tk.Canvas(parent)
        scrollbar = tk.Scrollbar(parent, command=canvas.yview)
        self.editor_frame = tk.Frame(canvas)

        canvas.create_window((0, 0), window=self.editor_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.editor_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Placeholder message
        self.no_selection_label = tk.Label(
            self.editor_frame,
            text="← Select a marker to edit metadata",
            font=("Arial", 11),
            fg="gray"
        )
        self.no_selection_label.pack(pady=50)

    def populate_marker_list(self):
        """Populate marker listbox"""
        self.marker_listbox.delete(0, tk.END)

        for i, marker in enumerate(self.markers):
            # Get marker data
            if isinstance(marker, dict):
                marker_type = marker.get('type', '').upper()
                name = marker.get('name', '') or marker.get('title', '')
            else:
                marker_type = marker.type.upper()
                name = marker.name or marker.title

            # Check if generated using helper method
            asset_file = self._get_marker_asset_file(marker)
            has_audio = bool(asset_file)
            checkmark = "✓" if has_audio else " "

            # Debug print
            print(f"Marker {i}: type={marker_type}, has_audio={has_audio}, asset_file={asset_file}")

            # Format label
            if marker_type == "MUSIC":
                emoji = "🎵"
            elif marker_type == "SFX":
                emoji = "🔊"
            elif marker_type == "VOICE":
                emoji = "🎤"
            else:
                emoji = "•"

            label = f"{checkmark} {emoji} {marker_type}"
            if name:
                label += f" - {name[:20]}"

            self.marker_listbox.insert(tk.END, label)

            # Gray out if no audio
            if not has_audio:
                self.marker_listbox.itemconfig(i, fg="gray")

    def on_marker_selected(self, event):
        """Handle marker selection"""
        selection = self.marker_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        marker = self.markers[index]

        # Check if marker has generated audio using helper method
        asset_file = self._get_marker_asset_file(marker)
        has_audio = bool(asset_file)

        if not has_audio:
            messagebox.showwarning(
                "No Audio",
                "This marker has not been generated yet.\nGenerate audio before editing metadata."
            )
            return

        self.selected_marker = marker
        self.selected_marker_index = index

        # Load metadata editor
        self.load_metadata_editor()

    def load_metadata_editor(self):
        """Load metadata editor for selected marker"""
        # Clear editor
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        if not self.selected_marker:
            return

        # Get marker data
        if isinstance(self.selected_marker, dict):
            marker_type = self.selected_marker.get('type', '')
            title = self.selected_marker.get('title', '') or self.selected_marker.get('name', '')
            categories = self.selected_marker.get('categories', {})
            notes = self.selected_marker.get('notes', '')
            time_ms = self.selected_marker.get('time_ms', 0)
            used_in = self.selected_marker.get('used_in_templates', [self.template_id])
        else:
            marker_type = self.selected_marker.type
            title = self.selected_marker.title or self.selected_marker.name
            categories = self.selected_marker.categories
            notes = self.selected_marker.notes
            time_ms = self.selected_marker.time_ms
            used_in = getattr(self.selected_marker, 'used_in_templates', [self.template_id])

        # Initialize categories if empty
        if not categories:
            categories = get_default_categories(marker_type)
            if isinstance(self.selected_marker, dict):
                self.selected_marker['categories'] = categories
            else:
                self.selected_marker.categories = categories

        # Asset file info
        asset_file = self._get_marker_asset_file(self.selected_marker)

        # Get audio duration if file exists
        duration_ms = 0
        if asset_file:
            # Try to find the audio file
            from pathlib import Path
            possible_paths = [
                Path("generated_audio") / marker_type / asset_file,
                Path("generated_audio") / asset_file,
                Path(asset_file)
            ]
            for path in possible_paths:
                if path.exists():
                    try:
                        from pydub.utils import mediainfo
                        info = mediainfo(str(path))
                        duration_ms = int(float(info.get('duration', 0)) * 1000)
                    except:
                        pass
                    break

        # Info Section (read-only metadata)
        info_frame = tk.Frame(self.editor_frame, bg="#E3F2FD", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        # File info
        if asset_file:
            tk.Label(info_frame, text=f"📁 {asset_file}", bg="#E3F2FD", font=("Arial", 9)).pack(anchor='w')

        # Timestamp and duration
        time_str = f"{time_ms // 60000}:{(time_ms // 1000) % 60:02d}.{time_ms % 1000:03d}"
        duration_str = f"{duration_ms / 1000:.1f}s" if duration_ms > 0 else "N/A"
        tk.Label(info_frame, text=f"⏱️ Position: {time_str}  |  Duration: {duration_str}",
                bg="#E3F2FD", font=("Arial", 9)).pack(anchor='w', pady=(2, 0))

        # Used in templates (new structure with timestamps)
        current_script_text = None  # For voice markers
        if used_in and isinstance(used_in, list) and len(used_in) > 0:
            if isinstance(used_in[0], dict):
                # New format: array of objects with template_id and timestamp_ms
                used_in_parts = []
                for usage in used_in:
                    template_id_in_usage = usage.get('template_id', '')
                    timestamp_ms = usage.get('timestamp_ms', 0)
                    time_str = f"{timestamp_ms // 60000}:{(timestamp_ms // 1000) % 60:02d}.{timestamp_ms % 1000:03d}"
                    used_in_parts.append(f"{template_id_in_usage} ({time_str})")

                    # Get script_text for current template (voice only)
                    if marker_type == "voice" and template_id_in_usage == self.template_id:
                        current_script_text = usage.get('script_text', '')

                used_in_str = ", ".join(used_in_parts)
            else:
                # Old format: just template IDs
                used_in_str = ", ".join(used_in)
        else:
            used_in_str = self.template_id
        tk.Label(info_frame, text=f"📋 Used in: {used_in_str}",
                bg="#E3F2FD", font=("Arial", 9)).pack(anchor='w', pady=(2, 0))

        # For voice markers: show script text for THIS template (read-only)
        if marker_type == "voice" and current_script_text:
            script_preview = current_script_text[:60] + "..." if len(current_script_text) > 60 else current_script_text
            tk.Label(info_frame, text=f"🎤 Script (this template): \"{script_preview}\"",
                    bg="#E3F2FD", font=("Arial", 9, "italic")).pack(anchor='w', pady=(2, 0))

        # Title field
        tk.Label(self.editor_frame, text="Title *", font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        self.title_entry = tk.Entry(self.editor_frame, font=("Arial", 10))
        self.title_entry.insert(0, title)
        self.title_entry.pack(fill=tk.X, pady=(0, 15))

        # Categories (type-specific)
        tk.Label(self.editor_frame, text="Categories *", font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))

        if marker_type == "sfx":
            self.create_sfx_category_editor(categories)
        elif marker_type == "music":
            self.create_music_category_editor(categories)
        elif marker_type == "voice":
            self.create_voice_category_editor(categories)

        # Notes field
        tk.Label(self.editor_frame, text="Notes (optional)", font=("Arial", 10, "bold")).pack(anchor='w', pady=(15, 5))
        self.notes_text = tk.Text(self.editor_frame, font=("Arial", 10), height=4, bg="#F5F5F5", wrap=tk.WORD)
        self.notes_text.insert("1.0", notes)
        self.notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Save button
        save_btn = tk.Button(
            self.editor_frame,
            text="Save Metadata",
            font=("Arial", 11),
            bg="#2196F3",
            fg="black",
            padx=20,
            pady=8,
            command=self.save_metadata
        )
        save_btn.pack(pady=10)

    def create_sfx_category_editor(self, categories):
        """Create SFX category multi-select (1-3 categories)"""
        frame = tk.Frame(self.editor_frame, bg="#F5F5F5", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(frame, text="Select 1-3 categories:", bg="#F5F5F5").pack(anchor='w')

        # Scrollable listbox with multi-select
        listbox_frame = tk.Frame(frame, bg="#F5F5F5")
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sfx_category_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.MULTIPLE,
            height=8,
            yscrollcommand=scrollbar.set,
            exportselection=False
        )
        self.sfx_category_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sfx_category_listbox.yview)

        # Populate categories
        selected_categories = categories.get("categories", [])
        for cat in SFX_CATEGORIES:
            self.sfx_category_listbox.insert(tk.END, cat)
            if cat in selected_categories:
                index = self.sfx_category_listbox.size() - 1
                self.sfx_category_listbox.selection_set(index)

        # Additional SFX fields
        tk.Label(frame, text="", bg="#F5F5F5").pack(pady=5)  # Spacer

        # Duration field
        duration_frame = tk.Frame(frame, bg="#F5F5F5")
        duration_frame.pack(fill=tk.X, pady=2)
        tk.Label(duration_frame, text="Duration (seconds):", bg="#F5F5F5").pack(side=tk.LEFT, padx=(0, 5))
        self.sfx_duration_var = tk.StringVar(value=str(categories.get("duration_s", 0.0)))
        duration_entry = tk.Entry(duration_frame, textvariable=self.sfx_duration_var, width=10)
        duration_entry.pack(side=tk.LEFT)

        # Pro/Free tier radio buttons
        tk.Label(frame, text="Tier:", bg="#F5F5F5").pack(anchor='w', pady=(5, 2))
        tier_frame = tk.Frame(frame, bg="#F5F5F5")
        tier_frame.pack(anchor='w', pady=(0, 5))

        self.sfx_pro_tier_var = tk.BooleanVar(value=categories.get("pro_tier", True))
        tk.Radiobutton(
            tier_frame,
            text="○ Free",
            variable=self.sfx_pro_tier_var,
            value=False,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(
            tier_frame,
            text="● Pro",
            variable=self.sfx_pro_tier_var,
            value=True,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT)

    def create_music_category_editor(self, categories):
        """Create Music category fields"""
        from core.categories import MUSIC_SUBGENRES

        frame = tk.Frame(self.editor_frame, bg="#F5F5F5", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Configure grid column to expand
        frame.grid_columnconfigure(1, weight=1)

        # Genre
        tk.Label(frame, text="Genre:", bg="#F5F5F5").grid(row=0, column=0, sticky='w', pady=2, padx=(0, 5))
        self.music_genre_var = tk.StringVar(value=categories.get("genre", ""))
        genre_combo = ttk.Combobox(frame, textvariable=self.music_genre_var, values=MUSIC_GENRES)
        genre_combo.grid(row=0, column=1, sticky='ew', pady=2)

        # Sub-Genre (dynamic based on genre)
        tk.Label(frame, text="Sub-Genre:", bg="#F5F5F5").grid(row=1, column=0, sticky='w', pady=2, padx=(0, 5))
        self.music_subgenre_var = tk.StringVar(value=categories.get("subGenre", ""))
        self.music_subgenre_combo = ttk.Combobox(frame, textvariable=self.music_subgenre_var)
        self.music_subgenre_combo.grid(row=1, column=1, sticky='ew', pady=2)

        # Update sub-genre options when genre changes
        def on_genre_change(*args):
            genre = self.music_genre_var.get()
            subgenres = MUSIC_SUBGENRES.get(genre, [])
            self.music_subgenre_combo['values'] = subgenres
            # Clear sub-genre if not applicable
            if not subgenres:
                self.music_subgenre_var.set("")

        self.music_genre_var.trace('w', on_genre_change)
        # Initialize sub-genre options
        on_genre_change()

        # Key
        tk.Label(frame, text="Key:", bg="#F5F5F5").grid(row=2, column=0, sticky='w', pady=2, padx=(0, 5))
        self.music_key_var = tk.StringVar(value=categories.get("key", "Unknown"))
        key_combo = ttk.Combobox(frame, textvariable=self.music_key_var, values=MUSIC_KEYS)
        key_combo.grid(row=2, column=1, sticky='ew', pady=2)

        # BPM
        tk.Label(frame, text="BPM:", bg="#F5F5F5").grid(row=3, column=0, sticky='w', pady=2, padx=(0, 5))
        self.music_bpm_var = tk.StringVar(value=str(categories.get("bpm", 120)))
        bpm_entry = tk.Entry(frame, textvariable=self.music_bpm_var)
        bpm_entry.grid(row=3, column=1, sticky='ew', pady=2)

        # Intensity
        tk.Label(frame, text="Intensity:", bg="#F5F5F5").grid(row=4, column=0, sticky='w', pady=2, padx=(0, 5))
        self.music_intensity_var = tk.StringVar(value=categories.get("intensity", "Moderate"))
        intensity_combo = ttk.Combobox(frame, textvariable=self.music_intensity_var, values=MUSIC_INTENSITY_LEVELS)
        intensity_combo.grid(row=4, column=1, sticky='ew', pady=2)

        # Instruments (multi-select, 1-5)
        tk.Label(frame, text="Instruments (1-5):", bg="#F5F5F5").grid(row=5, column=0, sticky='nw', pady=5, padx=(0, 5))
        inst_frame = tk.Frame(frame, bg="#F5F5F5")
        inst_frame.grid(row=5, column=1, sticky='ew', pady=5)

        scrollbar = tk.Scrollbar(inst_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.music_instruments_listbox = tk.Listbox(inst_frame, selectmode=tk.MULTIPLE, height=5, yscrollcommand=scrollbar.set, exportselection=False)
        self.music_instruments_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.music_instruments_listbox.yview)

        selected_instruments = categories.get("instruments", [])
        for inst in MUSIC_INSTRUMENTS:
            self.music_instruments_listbox.insert(tk.END, inst)
            if inst in selected_instruments:
                index = self.music_instruments_listbox.size() - 1
                self.music_instruments_listbox.selection_set(index)

        # Mood (multi-select, 1-3)
        tk.Label(frame, text="Mood (1-3):", bg="#F5F5F5").grid(row=6, column=0, sticky='nw', pady=5, padx=(0, 5))
        mood_frame = tk.Frame(frame, bg="#F5F5F5")
        mood_frame.grid(row=6, column=1, sticky='ew', pady=5)

        scrollbar2 = tk.Scrollbar(mood_frame)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

        self.music_mood_listbox = tk.Listbox(mood_frame, selectmode=tk.MULTIPLE, height=5, yscrollcommand=scrollbar2.set, exportselection=False)
        self.music_mood_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.music_mood_listbox.yview)

        selected_moods = categories.get("mood", [])
        for mood in MUSIC_MOODS:
            self.music_mood_listbox.insert(tk.END, mood)
            if mood in selected_moods:
                index = self.music_mood_listbox.size() - 1
                self.music_mood_listbox.selection_set(index)

        # Pro/Free tier radio buttons
        tk.Label(frame, text="Tier:", bg="#F5F5F5").grid(row=7, column=0, sticky='w', pady=5, padx=(0, 5))
        tier_frame = tk.Frame(frame, bg="#F5F5F5")
        tier_frame.grid(row=7, column=1, sticky='w', pady=5)

        self.music_pro_tier_var = tk.BooleanVar(value=categories.get("pro_tier", True))
        tk.Radiobutton(
            tier_frame,
            text="○ Free",
            variable=self.music_pro_tier_var,
            value=False,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(
            tier_frame,
            text="● Pro",
            variable=self.music_pro_tier_var,
            value=True,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT)

    def create_voice_category_editor(self, categories):
        """Create Voice category fields"""
        frame = tk.Frame(self.editor_frame, bg="#F5F5F5", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Configure grid column to expand
        frame.grid_columnconfigure(1, weight=1)

        # Gender
        tk.Label(frame, text="Gender:", bg="#F5F5F5").grid(row=0, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_gender_var = tk.StringVar(value=categories.get("gender", ""))
        gender_combo = ttk.Combobox(frame, textvariable=self.voice_gender_var, values=VOICE_GENDERS)
        gender_combo.grid(row=0, column=1, sticky='ew', pady=2)

        # Age
        tk.Label(frame, text="Age:", bg="#F5F5F5").grid(row=1, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_age_var = tk.StringVar(value=categories.get("age", ""))
        age_combo = ttk.Combobox(frame, textvariable=self.voice_age_var, values=VOICE_AGE_GROUPS)
        age_combo.grid(row=1, column=1, sticky='ew', pady=2)

        # Accent
        tk.Label(frame, text="Accent:", bg="#F5F5F5").grid(row=2, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_accent_var = tk.StringVar(value=categories.get("accent", ""))
        accent_combo = ttk.Combobox(frame, textvariable=self.voice_accent_var, values=VOICE_ACCENTS)
        accent_combo.grid(row=2, column=1, sticky='ew', pady=2)

        # Tone
        tk.Label(frame, text="Tone:", bg="#F5F5F5").grid(row=3, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_tone_var = tk.StringVar(value=categories.get("tone", ""))
        tone_combo = ttk.Combobox(frame, textvariable=self.voice_tone_var, values=VOICE_TONES)
        tone_combo.grid(row=3, column=1, sticky='ew', pady=2)

        # Delivery
        tk.Label(frame, text="Delivery:", bg="#F5F5F5").grid(row=4, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_delivery_var = tk.StringVar(value=categories.get("delivery", ""))
        delivery_combo = ttk.Combobox(frame, textvariable=self.voice_delivery_var, values=VOICE_DELIVERY_STYLES)
        delivery_combo.grid(row=4, column=1, sticky='ew', pady=2)

        # Speaker Voice ID (global property)
        tk.Label(frame, text="Speaker Voice ID:", bg="#F5F5F5").grid(row=5, column=0, sticky='w', pady=2, padx=(0, 5))
        self.voice_speaker_id_var = tk.StringVar(value=categories.get("speaker_voice_id", ""))
        speaker_id_entry = tk.Entry(frame, textvariable=self.voice_speaker_id_var)
        speaker_id_entry.grid(row=5, column=1, sticky='ew', pady=2)

        # Pro/Free tier radio buttons
        tk.Label(frame, text="Tier:", bg="#F5F5F5").grid(row=6, column=0, sticky='w', pady=5, padx=(0, 5))
        tier_frame = tk.Frame(frame, bg="#F5F5F5")
        tier_frame.grid(row=6, column=1, sticky='w', pady=5)

        self.voice_pro_tier_var = tk.BooleanVar(value=categories.get("pro_tier", True))
        tk.Radiobutton(
            tier_frame,
            text="○ Free",
            variable=self.voice_pro_tier_var,
            value=False,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(
            tier_frame,
            text="● Pro",
            variable=self.voice_pro_tier_var,
            value=True,
            bg="#F5F5F5"
        ).pack(side=tk.LEFT)

        # Note: script_text is template-specific, not stored in global categories
        # It's stored in usedInTemplates[].script_text instead

    def save_metadata(self):
        """Save metadata for selected marker"""
        if not self.selected_marker:
            return

        # Get title
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Validation Error", "Title is required")
            return

        # Get marker type
        if isinstance(self.selected_marker, dict):
            marker_type = self.selected_marker.get('type', '')
        else:
            marker_type = self.selected_marker.type

        # Build categories based on type
        categories = {}

        if marker_type == "sfx":
            selected_indices = self.sfx_category_listbox.curselection()
            selected_cats = [self.sfx_category_listbox.get(i) for i in selected_indices]
            if len(selected_cats) < 1 or len(selected_cats) > 3:
                messagebox.showerror("Validation Error", "SFX must have 1-3 categories selected")
                return

            # Get duration
            duration_str = self.sfx_duration_var.get().strip()
            try:
                duration_s = float(duration_str) if duration_str else 0.0
            except:
                messagebox.showerror("Validation Error", "Duration must be a number")
                return

            categories = {
                "categories": selected_cats,
                "duration_s": duration_s,
                "pro_tier": self.sfx_pro_tier_var.get()
            }

        elif marker_type == "music":
            # Validate and build music categories
            genre = self.music_genre_var.get()
            if not genre:
                messagebox.showerror("Validation Error", "Music genre is required")
                return

            bpm_str = self.music_bpm_var.get().strip()
            try:
                bpm = int(bpm_str)
            except:
                messagebox.showerror("Validation Error", "BPM must be a number")
                return

            instruments = [self.music_instruments_listbox.get(i) for i in self.music_instruments_listbox.curselection()]
            if len(instruments) < 1 or len(instruments) > 5:
                messagebox.showerror("Validation Error", "Music must have 1-5 instruments selected")
                return

            moods = [self.music_mood_listbox.get(i) for i in self.music_mood_listbox.curselection()]
            if len(moods) < 1 or len(moods) > 3:
                messagebox.showerror("Validation Error", "Music must have 1-3 moods selected")
                return

            categories = {
                "genre": genre,
                "subGenre": self.music_subgenre_var.get(),
                "key": self.music_key_var.get(),
                "bpm": bpm,
                "instruments": instruments,
                "mood": moods,
                "intensity": self.music_intensity_var.get(),
                "pro_tier": self.music_pro_tier_var.get()
            }

        elif marker_type == "voice":
            # Validate voice categories
            gender = self.voice_gender_var.get()
            age = self.voice_age_var.get()
            accent = self.voice_accent_var.get()
            tone = self.voice_tone_var.get()
            delivery = self.voice_delivery_var.get()

            if not all([gender, age, accent, tone, delivery]):
                messagebox.showerror("Validation Error", "All voice category fields are required")
                return

            # Get speaker ID (global property)
            speaker_voice_id = self.voice_speaker_id_var.get().strip()

            categories = {
                "gender": gender,
                "age": age,
                "accent": accent,
                "tone": tone,
                "delivery": delivery,
                "speaker_voice_id": speaker_voice_id,
                "pro_tier": self.voice_pro_tier_var.get()
            }
            # Note: script_text is NOT stored in categories
            # It's template-specific and goes in usedInTemplates[].script_text

        # Get notes
        notes = self.notes_text.get("1.0", tk.END).strip()

        # Save to marker
        if isinstance(self.selected_marker, dict):
            self.selected_marker['title'] = title
            self.selected_marker['categories'] = categories
            self.selected_marker['notes'] = notes
        else:
            self.selected_marker.title = title
            self.selected_marker.categories = categories
            self.selected_marker.notes = notes

        messagebox.showinfo("Metadata Saved", f"Metadata saved for {title}")

        # Update marker list display
        self.populate_marker_list()
        self.marker_listbox.selection_set(self.selected_marker_index)

    def export_all_files(self):
        """Export all files with metadata"""
        try:
            # Show progress
            progress_window = tk.Toplevel(self.window)
            progress_window.title("Exporting...")
            progress_window.geometry("400x100")
            progress_label = tk.Label(
                progress_window,
                text="Exporting files and metadata...\nThis may take a moment.",
                pady=20
            )
            progress_label.pack()
            progress_window.update()

            # Call export service
            result = self.assembly_service.export_with_metadata(
                markers=self.markers,
                duration_ms=self.duration_ms,
                template_id=self.template_id,
                template_name=self.template_name,
                video_reference=self.video_reference,
                output_dir="output"
            )

            # Close progress
            progress_window.destroy()

            # Show success
            message = f"✅ Export Complete!\n\n"
            message += f"Output: {result['output_dir']}\n\n"
            message += f"Created:\n"
            message += f"  • {len(result['exported_files'])} audio files\n"
            message += f"  • {len(result['exported_files'])} metadata files\n"
            message += f"  • 1 assembled multi-channel WAV\n"
            message += f"  • 1 assembled metadata JSON\n"
            message += f"  • 1 template JSON"

            messagebox.showinfo("Export Complete", message)

            # Callback
            if self.on_export_complete:
                self.on_export_complete(result)

            # Close window
            self.window.destroy()

        except Exception as e:
            try:
                progress_window.destroy()
            except:
                pass

            messagebox.showerror("Export Failed", f"An error occurred:\n\n{str(e)}")
            print(f"Export error: {e}")
            import traceback
            traceback.print_exc()
