#!/usr/bin/env python3
"""Test filmstrip manager extraction"""

import tkinter as tk
from filmstrip_manager import FilmstripManager


def test_filmstrip_init():
    """Test filmstrip manager initialization"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=60)

    manager = FilmstripManager(
        canvas,
        canvas_height=60,
        thumb_width=80,
        thumb_height=45
    )

    assert manager.canvas == canvas
    assert manager.canvas_height == 60
    assert manager.thumb_width == 80
    assert manager.thumb_height == 45
    assert len(manager.frames) == 0
    assert len(manager.frame_times) == 0
    assert manager.duration_ms == 0
    assert not manager.has_data()

    root.destroy()
    print("✓ Initialization test passed")


def test_filmstrip_callbacks():
    """Test filmstrip callbacks"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=60)
    canvas.pack()
    root.update()

    seek_called = []
    deselect_called = []

    def on_seek(time_ms):
        seek_called.append(time_ms)

    def on_deselect():
        deselect_called.append(True)

    manager = FilmstripManager(
        canvas,
        on_seek=on_seek,
        on_deselect_marker=on_deselect
    )

    # Set duration to enable seeking
    manager.duration_ms = 10000

    # Simulate click event
    class FakeEvent:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    # Click at middle of canvas
    event = FakeEvent(x=600, y=30)
    manager._handle_click(event)

    # Should have called callbacks
    assert len(seek_called) > 0
    assert len(deselect_called) > 0
    # Time should be around 5000ms (50% of 10000ms)
    assert 4500 <= seek_called[0] <= 5500

    root.destroy()
    print("✓ Callback test passed")


def test_clear():
    """Test clearing filmstrip"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=60)
    manager = FilmstripManager(canvas)

    # Add some fake data
    manager.frames = [None, None, None]  # Fake frames
    manager.frame_times = [0, 5000, 10000]
    manager.duration_ms = 10000

    assert manager.has_data()
    assert manager.get_frame_count() == 3

    # Clear
    manager.clear()

    assert not manager.has_data()
    assert manager.get_frame_count() == 0
    assert manager.duration_ms == 0

    root.destroy()
    print("✓ Clear test passed")


def test_update_position():
    """Test position indicator update"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=60)
    canvas.pack()
    root.update()

    manager = FilmstripManager(canvas)

    # Set up fake data
    manager.frames = [None, None]
    manager.frame_times = [0, 10000]
    manager.duration_ms = 10000

    # Update position to midpoint
    manager.update_position(5000)

    # Check that position indicator was created
    position_items = canvas.find_withtag("position")
    assert len(position_items) > 0

    root.destroy()
    print("✓ Position update test passed")


if __name__ == "__main__":
    print("Testing filmstrip_manager.py...")
    test_filmstrip_init()
    test_filmstrip_callbacks()
    test_clear()
    test_update_position()
    print("\n✅ All filmstrip manager tests passed!")
