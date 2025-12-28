#!/usr/bin/env python3
"""Test waveform manager extraction"""

import tkinter as tk
import numpy as np
from managers.waveform_manager import WaveformManager


def test_waveform_manager_init():
    """Test waveform manager initialization"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=80)

    # Create manager
    manager = WaveformManager(canvas, canvas_height=80)

    assert manager.canvas == canvas
    assert manager.canvas_height == 80
    assert manager.waveform_data is None
    assert manager.duration_ms == 0
    assert not manager.has_data()

    root.destroy()
    print("✓ Initialization test passed")


def test_waveform_calculation():
    """Test waveform data calculation"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=80)
    manager = WaveformManager(canvas)

    # Create fake audio array (1 second of sine wave at 22050 Hz)
    t = np.linspace(0, 1, 22050)
    audio_array = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

    # Calculate waveform
    manager._calculate_waveform_data(audio_array, target_width=100)

    assert manager.waveform_data is not None
    assert len(manager.waveform_data) == 100
    assert all(0 <= val <= 1 for val in manager.waveform_data)
    assert manager.has_data()

    root.destroy()
    print("✓ Waveform calculation test passed")


def test_waveform_callbacks():
    """Test waveform callbacks"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=80)
    canvas.pack()  # Pack to give it a size
    root.update()  # Update to realize the geometry

    # Track callback calls
    seek_called = []
    deselect_called = []

    def on_seek(time_ms):
        seek_called.append(time_ms)

    def on_deselect():
        deselect_called.append(True)

    manager = WaveformManager(
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

    # Click at middle of canvas (should seek to 50% of duration)
    event = FakeEvent(x=600, y=40)
    manager._handle_click(event)

    # Should have called on_seek and on_deselect
    assert len(seek_called) > 0, "Seek callback not called"
    assert len(deselect_called) > 0, "Deselect callback not called"
    # Time should be around 5000ms (50% of 10000ms)
    assert 4500 <= seek_called[0] <= 5500, f"Unexpected seek time: {seek_called[0]}"

    root.destroy()
    print("✓ Callback test passed")


def test_clear():
    """Test clearing waveform"""
    root = tk.Tk()
    canvas = tk.Canvas(root, width=1200, height=80)
    manager = WaveformManager(canvas)

    # Add some data
    manager.waveform_data = [0.5] * 100
    manager.duration_ms = 10000

    assert manager.has_data()

    # Clear
    manager.clear()

    assert not manager.has_data()
    assert manager.duration_ms == 0
    assert manager.waveform_data is None

    root.destroy()
    print("✓ Clear test passed")


if __name__ == "__main__":
    print("Testing waveform_manager.py...")
    test_waveform_manager_init()
    test_waveform_calculation()
    test_waveform_callbacks()
    test_clear()
    print("\n✅ All waveform manager tests passed!")
