#!/usr/bin/env python3
"""
Marker Selection Manager - Manages marker selection and navigation
Coordinates marker selection state and UI updates
"""

from typing import Optional, Callable, List


class MarkerSelectionManager:
    """
    Manages marker selection state and navigation.
    Handles selecting/deselecting markers and jumping to marker positions.
    """

    def __init__(
        self,
        markers: List[dict],
        marker_row_widgets: List,
        marker_canvas,
        on_seek: Callable[[int], None],
        on_redraw_indicators: Callable[[], None]
    ):
        """
        Initialize the marker selection manager.

        Args:
            markers: Reference to the markers list
            marker_row_widgets: List of marker row widget objects
            marker_canvas: Canvas containing marker rows (for scrolling)
            on_seek: Callback function to seek to a time (in milliseconds)
            on_redraw_indicators: Callback to redraw marker indicators
        """
        self.markers = markers
        self.marker_row_widgets = marker_row_widgets
        self.marker_canvas = marker_canvas
        self.on_seek = on_seek
        self.on_redraw_indicators = on_redraw_indicators
        self.selected_marker_index: Optional[int] = None

    def deselect_marker(self):
        """
        Deselect the currently selected marker.
        """
        if self.selected_marker_index is not None and self.selected_marker_index < len(self.marker_row_widgets):
            self.marker_row_widgets[self.selected_marker_index].set_selected(False)
            self.selected_marker_index = None
            self.on_redraw_indicators()

    def jump_to_marker(self):
        """
        Jump to the currently selected marker's time position.
        """
        if self.selected_marker_index is not None and 0 <= self.selected_marker_index < len(self.markers):
            marker = self.markers[self.selected_marker_index]
            self.on_seek(marker['time_ms'])

    def select_marker_row(self, marker_index: int):
        """
        Select a marker row and update visual state.

        Args:
            marker_index: Index of marker to select
        """
        # Deselect previous selection
        if self.selected_marker_index is not None and self.selected_marker_index < len(self.marker_row_widgets):
            self.marker_row_widgets[self.selected_marker_index].set_selected(False)

        # Select new row
        if 0 <= marker_index < len(self.marker_row_widgets):
            self.selected_marker_index = marker_index
            self.marker_row_widgets[marker_index].set_selected(True)

            # Scroll to make selected row visible
            self.marker_canvas.yview_moveto(marker_index / len(self.marker_row_widgets))

            # Also highlight corresponding timeline marker
            self.on_redraw_indicators()

    def get_selected_index(self) -> Optional[int]:
        """
        Get the currently selected marker index.

        Returns:
            Index of selected marker or None if no selection
        """
        return self.selected_marker_index

    def set_selected_index(self, index: Optional[int]):
        """
        Set the selected marker index directly.

        Args:
            index: Index to set as selected (or None to clear)
        """
        self.selected_marker_index = index
