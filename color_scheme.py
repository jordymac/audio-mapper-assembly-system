#!/usr/bin/env python3
"""
Color Scheme System - Dark Mode Support
Global color scheme that adapts to system dark mode
"""


class ColorScheme:
    """Global color scheme that adapts to system dark mode"""

    def __init__(self):
        self.is_dark_mode = self._detect_dark_mode()
        self._init_colors()

    def _detect_dark_mode(self):
        """Detect if macOS is in dark mode"""
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and 'Dark' in result.stdout
        except:
            return False

    def _init_colors(self):
        """Initialize color palettes for light and dark modes"""
        if self.is_dark_mode:
            # Dark Mode Colors
            self.bg_primary = "#1E1E1E"           # Main background
            self.bg_secondary = "#2C2C2C"         # Secondary background
            self.bg_tertiary = "#3C3C3C"          # Tertiary background
            self.bg_input = "#2C2C2C"             # Input field background
            self.bg_hover = "#404040"             # Hover state

            self.fg_primary = "#E0E0E0"           # Main text
            self.fg_secondary = "#B0B0B0"         # Secondary text
            self.fg_tertiary = "#808080"          # Tertiary text
            self.fg_input = "#E0E0E0"             # Input text

            self.border = "#404040"               # Borders
            self.divider = "#2C2C2C"              # Dividers

            # Accent colors (markers)
            self.sfx_bg = "#D32F2F"               # SFX red (darker)
            self.sfx_fg = "white"
            self.music_bg = "#1976D2"             # Music blue (darker)
            self.music_fg = "white"
            self.voice_bg = "#388E3C"             # Voice green (darker)
            self.voice_fg = "white"

            # Button colors
            self.btn_primary_bg = "#1976D2"       # Primary button (blue)
            self.btn_primary_fg = "white"
            self.btn_success_bg = "#388E3C"       # Success button (green)
            self.btn_success_fg = "white"
            self.btn_danger_bg = "#D32F2F"        # Danger button (red)
            self.btn_danger_fg = "white"
            self.btn_warning_bg = "#F57C00"       # Warning button (orange)
            self.btn_warning_fg = "white"
            self.btn_special_bg = "#7B1FA2"       # Special button (purple)
            self.btn_special_fg = "white"

            # Info/highlight backgrounds
            self.info_bg = "#0D47A1"              # Info background (dark blue)
            self.success_bg = "#1B5E20"           # Success background (dark green)
            self.warning_bg = "#E65100"           # Warning background (dark orange)
            self.selection_bg = "#1565C0"         # Selection highlight

        else:
            # Light Mode Colors
            self.bg_primary = "#FFFFFF"           # Main background
            self.bg_secondary = "#F5F5F5"         # Secondary background
            self.bg_tertiary = "#E0E0E0"          # Tertiary background
            self.bg_input = "#F5F5F5"             # Input field background
            self.bg_hover = "#E8E8E8"             # Hover state

            self.fg_primary = "#000000"           # Main text
            self.fg_secondary = "#424242"         # Secondary text
            self.fg_tertiary = "#666666"          # Tertiary text
            self.fg_input = "#000000"             # Input text

            self.border = "#CCCCCC"               # Borders
            self.divider = "#E0E0E0"              # Dividers

            # Accent colors (markers)
            self.sfx_bg = "#F44336"               # SFX red
            self.sfx_fg = "black"
            self.music_bg = "#2196F3"             # Music blue
            self.music_fg = "black"
            self.voice_bg = "#4CAF50"             # Voice green
            self.voice_fg = "black"

            # Button colors
            self.btn_primary_bg = "#2196F3"       # Primary button (blue)
            self.btn_primary_fg = "white"
            self.btn_success_bg = "#4CAF50"       # Success button (green)
            self.btn_success_fg = "white"
            self.btn_danger_bg = "#f44336"        # Danger button (red)
            self.btn_danger_fg = "white"
            self.btn_warning_bg = "#FF9800"       # Warning button (orange)
            self.btn_warning_fg = "white"
            self.btn_special_bg = "#9C27B0"       # Special button (purple)
            self.btn_special_fg = "white"

            # Info/highlight backgrounds
            self.info_bg = "#E3F2FD"              # Info background (light blue)
            self.success_bg = "#E8F5E9"           # Success background (light green)
            self.warning_bg = "#FFFFE0"           # Warning background (light yellow)
            self.selection_bg = "#BBDEFB"         # Selection highlight


# Global color scheme instance
COLORS = ColorScheme()
