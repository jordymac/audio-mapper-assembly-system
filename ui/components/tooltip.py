#!/usr/bin/env python3
"""
ToolTip - Simple tooltip widget
Displays helpful tooltips when hovering over widgets
"""

import tkinter as tk
from config.color_scheme import COLORS


class ToolTip:
    """Simple tooltip class for hovering over widgets"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        """Show tooltip on mouse enter"""
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background=COLORS.warning_bg,
            foreground=COLORS.fg_primary,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=3
        )
        label.pack()

    def on_leave(self, event=None):
        """Hide tooltip on mouse leave"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
