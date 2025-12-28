"""
Audio Generation Service

Handles audio generation for markers using ElevenLabs API:
- Single marker generation with background threading
- Batch operations (generate missing, regenerate all, by type)
- Audio assembly from generated files
- Progress tracking and error handling
"""

import os
import threading
from datetime import datetime
from tkinter import messagebox
import tkinter as tk
from config.color_scheme import COLORS, create_colored_button
from tkinter import ttk

# Import ElevenLabs API functions
try:
    from services.elevenlabs_api import generate_sfx, generate_voice, generate_music
except ImportError:
    print("WARNING: elevenlabs_api.py not found. Audio generation will not work.")
    generate_sfx = None
    generate_voice = None
    generate_music = None


class BatchProgressWindow:
    """Modal window showing progress for batch audio generation"""

    def __init__(self, parent, operation_name, total_markers):
        self.parent = parent
        self.operation_name = operation_name
        self.total_markers = total_markers
        self.current_index = 0
        self.success_count = 0
        self.failed_count = 0
        self.cancelled = False

        # Create modal window
        self.window = tk.Toplevel(parent.root)
        self.window.title(f"Batch Generation - {operation_name}")
        self.window.geometry("500x250")
        self.window.resizable(False, False)
        self.window.transient(parent.root)
        self.window.grab_set()

        # Center on parent
        self.window.update_idletasks()
        x = parent.root.winfo_x() + (parent.root.winfo_width() // 2) - (500 // 2)
        y = parent.root.winfo_y() + (parent.root.winfo_height() // 2) - (250 // 2)
        self.window.geometry(f"+{x}+{y}")

        # Title
        tk.Label(
            self.window,
            text=operation_name,
            font=("Arial", 14, "bold")
        ).pack(pady=20)

        # Current marker label
        self.marker_label = tk.Label(
            self.window,
            text="Starting...",
            font=("Arial", 10)
        )
        self.marker_label.pack(pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.window,
            variable=self.progress_var,
            maximum=total_markers,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            self.window,
            text=f"0 / {total_markers} completed",
            font=("Arial", 9)
        )
        self.status_label.pack(pady=5)

        # Cancel button
        self.cancel_btn = create_colored_button(
            self.window,
            text="Cancel",
            command=self.cancel,
            bg_color=COLORS.btn_danger_bg,
            fg_color=COLORS.btn_danger_fg,
            font=("Arial", 10, "bold"),
            width=10,
            height=1
        )
        self.cancel_btn.pack(pady=10)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

    def update_progress(self, current_idx, marker_name, marker_type):
        """Update progress display for current marker"""
        self.current_index = current_idx
        self.progress_var.set(current_idx)

        self.marker_label.config(
            text=f"Generating {marker_type.upper()}: {marker_name}"
        )

        completed = self.success_count + self.failed_count
        self.status_label.config(
            text=f"{completed} / {self.total_markers} completed "
                 f"({self.success_count} success, {self.failed_count} failed)"
        )

    def mark_success(self):
        """Mark current marker as successfully generated"""
        self.success_count += 1

    def mark_failed(self):
        """Mark current marker as failed"""
        self.failed_count += 1

    def cancel(self):
        """Cancel batch operation"""
        self.cancelled = True
        self.close()

    def close(self):
        """Close the progress window"""
        try:
            self.window.destroy()
        except:
            pass

    def show_summary(self):
        """Show summary of batch operation"""
        if self.cancelled:
            messagebox.showinfo(
                "Batch Cancelled",
                f"Batch operation cancelled.\n\n"
                f"Completed: {self.success_count + self.failed_count} / {self.total_markers}\n"
                f"Success: {self.success_count}\n"
                f"Failed: {self.failed_count}"
            )
        else:
            if self.failed_count > 0:
                messagebox.showwarning(
                    "Batch Complete (With Errors)",
                    f"Batch generation completed with errors.\n\n"
                    f"Success: {self.success_count}\n"
                    f"Failed: {self.failed_count}"
                )
            else:
                messagebox.showinfo(
                    "Batch Complete",
                    f"All audio generated successfully!\n\n"
                    f"Generated: {self.success_count} markers"
                )


class AudioGenerationService:
    """
    Service for audio generation and assembly operations.

    Handles:
    - Single marker generation with threading
    - Batch generation operations
    - Audio file assembly
    - Progress tracking and error handling
    """

    def __init__(self, gui_ref):
        """
        Initialize audio generation service

        Args:
            gui_ref: Reference to AudioMapperGUI instance (for accessing markers, etc.)
        """
        self.gui = gui_ref

    def is_api_available(self):
        """Check if ElevenLabs API is available"""
        return generate_sfx is not None and generate_voice is not None and generate_music is not None

    # ========================================================================
    # SINGLE MARKER GENERATION
    # ========================================================================

    def generate_marker_audio(self, marker_index):
        """
        Generate audio for a marker using ElevenLabs API

        Args:
            marker_index: Index of marker to generate
        """
        if not (0 <= marker_index < len(self.gui.markers)):
            return

        # Check if API functions are available
        if not self.is_api_available():
            messagebox.showerror(
                "API Not Available",
                "ElevenLabs API module not found.\n\n"
                "Make sure elevenlabs_api.py exists and dependencies are installed."
            )
            return

        marker = self.gui.markers[marker_index]
        marker_type = marker['type']
        prompt_data = marker.get('prompt_data', {})

        # Store old state for undo
        old_marker_state = marker.copy()

        # Set status to generating
        current_version_data = self.gui.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'generating'

        # Update UI to show generating status (⏳)
        self.gui.update_marker_list()

        # Start generation in background thread
        thread = threading.Thread(
            target=self._generate_audio_background,
            args=(marker_index, marker_type, prompt_data, old_marker_state),
            daemon=True
        )
        thread.start()

    def _generate_audio_background(self, marker_index, marker_type, prompt_data, old_marker_state):
        """
        Background thread for audio generation (doesn't block UI)

        Args:
            marker_index: Index of marker
            marker_type: Type of marker (sfx/voice/music)
            prompt_data: Prompt data for generation
            old_marker_state: Marker state before generation (for undo)
        """
        try:
            marker = self.gui.markers[marker_index]

            # Create version when generation starts (not when marker is created)
            # This ensures version 1 is created on first generation, not before
            next_version = self.gui.add_new_version(marker, prompt_data)

            # Build output path
            marker_name = marker.get('name', f'{marker_type.upper()}_{marker_index:05d}')
            output_filename = f"{marker_name}_v{next_version}.mp3"
            output_path = os.path.join("generated_audio", marker_type, output_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Call appropriate API function
            result = None
            if marker_type == 'sfx':
                description = prompt_data.get('description', '')
                if not description:
                    raise ValueError("SFX description is required")
                result = generate_sfx(description=description, output_path=output_path)

            elif marker_type == 'voice':
                voice_profile = prompt_data.get('voice_profile', '')
                text = prompt_data.get('text', '')
                if not text:
                    raise ValueError("Voice text is required")
                result = generate_voice(voice_profile=voice_profile, text=text, output_path=output_path)

            elif marker_type == 'music':
                positive_styles = prompt_data.get('positiveGlobalStyles', [])
                negative_styles = prompt_data.get('negativeGlobalStyles', [])
                sections = prompt_data.get('sections', [])
                if not positive_styles:
                    raise ValueError("Music requires at least one positive style")
                result = generate_music(
                    positive_styles=positive_styles,
                    negative_styles=negative_styles,
                    sections=sections,
                    output_path=output_path
                )

            # Check if generation succeeded
            if result and result.get('success'):
                # Update version data with success
                current_version_data = self.gui.get_current_version_data(marker)
                if current_version_data:
                    current_version_data['status'] = 'generated'
                    current_version_data['asset_file'] = output_filename
                    current_version_data['asset_id'] = result.get('asset_id', f'{marker_type}_{next_version}')

                # Schedule UI update on main thread
                self.gui.root.after(0, lambda: self._on_generation_success(marker_index, old_marker_state))
            else:
                # Generation failed
                error_msg = result.get('error', 'Unknown error') if result else 'No response from API'
                self.gui.root.after(0, lambda: self._on_generation_failed(marker_index, error_msg))

        except Exception as e:
            # Handle any errors
            error_msg = str(e)
            self.gui.root.after(0, lambda: self._on_generation_failed(marker_index, error_msg))

    def _on_generation_success(self, marker_index, old_marker_state):
        """
        Called on main thread after successful generation

        Args:
            marker_index: Index of marker
            old_marker_state: State before generation (for undo)
        """
        from commands import GenerateAudioCommand

        # Create undo command
        command = GenerateAudioCommand(self.gui.marker_repository, marker_index, old_marker_state)
        command.new_marker_state = self.gui.markers[marker_index].copy()
        self.gui.history.execute_command(command)

        # Update UI
        self.gui.update_marker_list()

        # Show success message
        marker = self.gui.markers[marker_index]
        marker_name = marker.get('name', '(unnamed)')
        messagebox.showinfo(
            "Generation Complete",
            f"Audio generated successfully!\n\n"
            f"Marker: {marker_name}\n"
            f"Version: {marker.get('current_version', 1)}"
        )

        # Trigger auto-assembly if enabled
        self.auto_assemble_audio()

    def _on_generation_failed(self, marker_index, error_msg):
        """
        Called on main thread after generation failure

        Args:
            marker_index: Index of marker
            error_msg: Error message
        """
        # Update status to failed
        marker = self.gui.markers[marker_index]
        current_version_data = self.gui.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'failed'

        # Update UI
        self.gui.update_marker_list()

        # Show error message
        marker_name = marker.get('name', '(unnamed)')
        messagebox.showerror(
            "Generation Failed",
            f"Failed to generate audio for marker:\n{marker_name}\n\n"
            f"Error: {error_msg}"
        )

    # ========================================================================
    # BATCH GENERATION OPERATIONS
    # ========================================================================

    def batch_generate_missing(self):
        """Generate all markers that haven't been generated yet (status: not_yet_generated)"""
        # Collect markers to generate
        markers_to_generate = []
        for i, marker in enumerate(self.gui.markers):
            current_version_data = self.gui.get_current_version_data(marker)
            if current_version_data:
                status = current_version_data.get('status', 'not_yet_generated')
                if status == 'not_yet_generated':
                    markers_to_generate.append((i, marker))

        if not markers_to_generate:
            messagebox.showinfo(
                "No Markers to Generate",
                "All markers have already been generated.\n\n"
                "Use 'Regenerate All' to create new versions."
            )
            return

        # Confirm operation
        if not messagebox.askyesno(
            "Batch Generate Missing",
            f"Generate audio for {len(markers_to_generate)} marker(s)?\n\n"
            f"This will call the ElevenLabs API {len(markers_to_generate)} time(s)."
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            "Generate All Missing"
        )

    def batch_regenerate_all(self):
        """Regenerate all markers (creates new versions)"""
        if not self.gui.markers:
            messagebox.showinfo("No Markers", "Add some markers first.")
            return

        # Collect all markers
        markers_to_generate = [(i, marker) for i, marker in enumerate(self.gui.markers)]

        # Confirm operation
        if not messagebox.askyesno(
            "Batch Regenerate All",
            f"Regenerate audio for all {len(markers_to_generate)} marker(s)?\n\n"
            f"This will:\n"
            f"  • Create new versions for each marker\n"
            f"  • Call the ElevenLabs API {len(markers_to_generate)} time(s)\n"
            f"  • Preserve existing versions in history"
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            "Regenerate All"
        )

    def batch_generate_by_type(self):
        """Generate all markers of a specific type (SFX, Voice, or Music)"""
        if not self.gui.markers:
            messagebox.showinfo("No Markers", "Add some markers first.")
            return

        # Show type selection dialog
        type_dialog = tk.Toplevel(self.gui.root)
        type_dialog.title("Select Marker Type")
        type_dialog.geometry("300x200")
        type_dialog.resizable(False, False)
        type_dialog.transient(self.gui.root)
        type_dialog.grab_set()

        # Center dialog
        type_dialog.update_idletasks()
        x = self.gui.root.winfo_x() + (self.gui.root.winfo_width() // 2) - (300 // 2)
        y = self.gui.root.winfo_y() + (self.gui.root.winfo_height() // 2) - (200 // 2)
        type_dialog.geometry(f"+{x}+{y}")

        # Title
        tk.Label(
            type_dialog,
            text="Select marker type to generate:",
            font=("Arial", 11, "bold")
        ).pack(pady=20)

        selected_type = tk.StringVar()

        # Type buttons
        button_frame = tk.Frame(type_dialog)
        button_frame.pack(pady=10)

        create_colored_button(
            button_frame,
            text="SFX",
            command=lambda: [selected_type.set("sfx"), type_dialog.destroy()],
            bg_color=COLORS.sfx_bg,
            fg_color=COLORS.sfx_fg,
            font=("Arial", 10, "bold"),
            width=15,
            height=1
        ).pack(pady=5)

        create_colored_button(
            button_frame,
            text="Voice",
            command=lambda: [selected_type.set("voice"), type_dialog.destroy()],
            bg_color=COLORS.voice_bg,
            fg_color=COLORS.voice_fg,
            font=("Arial", 10, "bold"),
            width=15,
            height=1
        ).pack(pady=5)

        create_colored_button(
            button_frame,
            text="Music",
            command=lambda: [selected_type.set("music"), type_dialog.destroy()],
            bg_color=COLORS.music_bg,
            fg_color=COLORS.music_fg,
            font=("Arial", 10, "bold"),
            width=15,
            height=1
        ).pack(pady=5)

        # Wait for selection
        type_dialog.wait_window()

        if not selected_type.get():
            return  # User closed dialog

        # Collect markers of selected type
        marker_type = selected_type.get()
        markers_to_generate = [
            (i, marker) for i, marker in enumerate(self.gui.markers)
            if marker['type'] == marker_type
        ]

        if not markers_to_generate:
            messagebox.showinfo(
                "No Markers Found",
                f"No {marker_type.upper()} markers found in timeline."
            )
            return

        # Confirm operation
        if not messagebox.askyesno(
            f"Generate All {marker_type.upper()}",
            f"Generate audio for {len(markers_to_generate)} {marker_type.upper()} marker(s)?\n\n"
            f"This will call the ElevenLabs API {len(markers_to_generate)} time(s)."
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            f"Generate All {marker_type.upper()}"
        )

    def _run_batch_generation(self, markers_list, operation_name):
        """
        Run batch generation for a list of markers

        Args:
            markers_list: List of (index, marker) tuples to generate
            operation_name: Display name for the operation
        """
        # Create progress window
        progress = BatchProgressWindow(self.gui, operation_name, len(markers_list))

        # Process markers one at a time (queue-based)
        def process_next_marker(current_idx=0):
            # Check if cancelled
            if progress.cancelled:
                progress.show_summary()
                return

            # Check if done
            if current_idx >= len(markers_list):
                progress.close()
                progress.show_summary()

                # Trigger auto-assembly if enabled
                self.auto_assemble_audio()
                return

            # Get next marker
            marker_index, marker = markers_list[current_idx]
            marker_name = marker.get('name', '(unnamed)')
            marker_type = marker['type']

            # Update progress display
            progress.update_progress(current_idx, marker_name, marker_type)

            # Generate audio (synchronously in this context)
            def on_generation_complete(success):
                if success:
                    progress.mark_success()
                else:
                    progress.mark_failed()

                # Process next marker after a short delay
                self.gui.root.after(500, lambda: process_next_marker(current_idx + 1))

            # Start generation for this marker
            self._generate_marker_for_batch(marker_index, on_generation_complete)

        # Start processing first marker
        process_next_marker(0)

    def _generate_marker_for_batch(self, marker_index, completion_callback):
        """
        Generate audio for a single marker in batch mode

        Args:
            marker_index: Index of marker to generate
            completion_callback: Function to call with success/failure (bool)
        """
        if not (0 <= marker_index < len(self.gui.markers)):
            completion_callback(False)
            return

        # Check if API functions are available
        if not self.is_api_available():
            completion_callback(False)
            return

        marker = self.gui.markers[marker_index]
        marker_type = marker['type']
        prompt_data = marker.get('prompt_data', {})
        old_marker_state = marker.copy()

        # Set status to generating
        current_version_data = self.gui.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'generating'

        # Update UI to show generating status (⏳)
        self.gui.update_marker_list()

        # Start generation in background thread
        def on_success(marker_idx, asset_file, asset_id, size_bytes):
            self._on_batch_generation_success(marker_idx, asset_file, asset_id, size_bytes)
            completion_callback(True)

        def on_failed(marker_idx, error_msg):
            # Update status but don't show messagebox (batch mode)
            marker = self.gui.markers[marker_idx]
            current_version_data = self.gui.get_current_version_data(marker)
            if current_version_data:
                current_version_data['status'] = 'failed'
            self.gui.update_marker_list()
            completion_callback(False)

        thread = threading.Thread(
            target=self._generate_audio_background_for_batch,
            args=(marker_index, marker_type, prompt_data, old_marker_state, on_success, on_failed),
            daemon=True
        )
        thread.start()

    def _generate_audio_background_for_batch(self, marker_index, marker_type, prompt_data, old_marker_state, success_callback, failure_callback):
        """
        Background thread function for batch generation
        (Modified version that uses callbacks instead of root.after)
        """
        try:
            # Prepare output directory
            output_dir = os.path.join("generated_audio", marker_type)
            os.makedirs(output_dir, exist_ok=True)

            # Generate unique filename
            marker = self.gui.markers[marker_index]
            current_version = marker.get('current_version', 1)
            marker_name = marker.get('name', '(unnamed)')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{marker_type.upper()}_{marker_index:05d}_v{current_version}_{timestamp}.mp3"
            output_path = os.path.join(output_dir, base_filename)

            # Call appropriate API based on type
            result = None
            if marker_type == 'sfx':
                description = prompt_data.get('description', '')
                result = generate_sfx(description, output_path)

            elif marker_type == 'voice':
                voice_profile = prompt_data.get('voice_profile', '')
                text = prompt_data.get('text', '')
                result = generate_voice(voice_profile, text, output_path)

            elif marker_type == 'music':
                positive_styles = prompt_data.get('positiveGlobalStyles', [])
                negative_styles = prompt_data.get('negativeGlobalStyles', [])
                sections = prompt_data.get('sections', [])
                result = generate_music(positive_styles, negative_styles, sections, output_path)

            # Check result
            if result and result.get('success'):
                asset_file = base_filename
                asset_id = result.get('asset_id')
                size_bytes = result.get('size_bytes', 0)

                # Call success callback
                success_callback(marker_index, asset_file, asset_id, size_bytes)

            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                failure_callback(marker_index, error_msg)

        except Exception as e:
            error_msg = str(e)
            failure_callback(marker_index, error_msg)

    def _on_batch_generation_success(self, marker_idx, asset_file, asset_id, size_bytes):
        """
        Called after successful generation in batch mode
        (Does not show messagebox, just updates state)
        """
        # Update marker data
        marker = self.gui.markers[marker_idx]
        current_version_data = self.gui.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'generated'
            current_version_data['asset_file'] = asset_file
            current_version_data['asset_id'] = asset_id

        # Update UI
        self.gui.update_marker_list()

    # ========================================================================
    # AUDIO ASSEMBLY
    # ========================================================================

    def auto_assemble_audio(self):
        """
        Automatically assemble audio after generation completes
        (called if auto_assemble_enabled is True)
        """
        if not self.gui.auto_assemble_enabled.get():
            return

        # Only assemble if there are markers with generated audio
        has_audio = any(
            self.gui.get_current_version_data(m) and
            self.gui.get_current_version_data(m).get('status') == 'generated'
            for m in self.gui.markers
        )

        if not has_audio:
            return

        # Perform assembly
        self._assemble_audio_internal(auto=True)

    def manual_assemble_audio(self):
        """
        Manually assemble audio when user clicks 'Assemble Now' button
        """
        # Perform assembly
        self._assemble_audio_internal(auto=False)

    def _assemble_audio_internal(self, auto=False):
        """
        Internal method to assemble all marker audio files into a single output

        Args:
            auto: True if auto-triggered, False if manual
        """
        try:
            # Check if we have any markers
            if not self.gui.markers:
                messagebox.showinfo(
                    "No Markers",
                    "Add some markers with generated audio first."
                )
                return

            # Check if we have a duration
            duration = self.gui.video_player.get_duration()
            if duration <= 0:
                messagebox.showerror(
                    "No Timeline",
                    "Create a timeline first (Open Video or Create Blank Timeline)"
                )
                return

            # Import pydub here (only when needed)
            try:
                from pydub import AudioSegment
            except ImportError:
                messagebox.showerror(
                    "Missing Dependency",
                    "Pydub is required for audio assembly.\n\n"
                    "Install it with: pip install pydub\n"
                    "Also requires FFmpeg: brew install ffmpeg"
                )
                return

            # Collect markers with generated audio
            markers_with_audio = []
            for marker in self.gui.markers:
                current_version_data = self.gui.get_current_version_data(marker)
                if current_version_data:
                    status = current_version_data.get('status')
                    asset_file = current_version_data.get('asset_file')
                    if status == 'generated' and asset_file:
                        markers_with_audio.append((marker, asset_file))

            if not markers_with_audio:
                messagebox.showinfo(
                    "No Generated Audio",
                    "No markers have generated audio files.\n\n"
                    "Generate some audio first using the 🔄 buttons."
                )
                return

            # Create silent base track
            print(f"Creating silent base track ({duration}ms)...")
            assembled = AudioSegment.silent(duration=duration)

            # Overlay each marker's audio
            print(f"Assembling {len(markers_with_audio)} audio file(s)...")
            for marker, asset_file in markers_with_audio:
                marker_type = marker['type']
                time_ms = marker['time_ms']
                marker_name = marker.get('name', '(unnamed)')

                # Find audio file
                possible_paths = [
                    os.path.join("generated_audio", marker_type, asset_file),
                    os.path.join("generated_audio", asset_file),
                    asset_file
                ]

                audio_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        audio_path = path
                        break

                if not audio_path:
                    print(f"WARNING: Audio file not found for marker '{marker_name}': {asset_file}")
                    continue

                # Load and overlay audio
                try:
                    audio_segment = AudioSegment.from_file(audio_path)
                    assembled = assembled.overlay(audio_segment, position=time_ms)
                    print(f"  ✓ Overlayed {marker_type} at {time_ms}ms: {marker_name}")
                except Exception as e:
                    print(f"  ✗ Error loading {audio_path}: {e}")

            # Ensure output directory exists
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            template_name = self.gui.template_name.get() or "audio_map"
            output_filename = f"{template_name}_{timestamp}_assembled.wav"
            output_path = os.path.join(output_dir, output_filename)

            # Export assembled audio
            print(f"Exporting to {output_path}...")
            assembled.export(output_path, format="wav")
            print("✓ Assembly complete!")

            # Show success message (only if manual)
            if not auto:
                messagebox.showinfo(
                    "Assembly Complete",
                    f"Audio assembled successfully!\n\n"
                    f"Output: {output_path}\n"
                    f"Duration: {duration}ms\n"
                    f"Markers: {len(markers_with_audio)}"
                )

        except Exception as e:
            messagebox.showerror(
                "Assembly Failed",
                f"Failed to assemble audio:\n\n{str(e)}"
            )
