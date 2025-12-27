#!/usr/bin/env python3
"""
Quick test script for enhanced marker rows
Creates a few test markers and displays them in the enhanced UI
"""

import tkinter as tk
from datetime import datetime

# Import the main GUI class
# We'll import after setting up the environment
import sys
sys.path.insert(0, '.')

# Quick visual test - just verify imports and basic structure
def test_marker_row_class():
    """Test that MarkerRow class exists and has expected methods"""
    from audio_mapper import MarkerRow, AudioMapperGUI

    print("=" * 70)
    print("ENHANCED MARKER ROW - STRUCTURE TEST")
    print("=" * 70)

    # Check MarkerRow class exists
    assert hasattr(MarkerRow, '__init__'), "MarkerRow class missing __init__"
    assert hasattr(MarkerRow, 'create_widgets'), "MarkerRow missing create_widgets"
    assert hasattr(MarkerRow, 'on_play_click'), "MarkerRow missing on_play_click"
    assert hasattr(MarkerRow, 'on_generate_click'), "MarkerRow missing on_generate_click"
    assert hasattr(MarkerRow, 'set_selected'), "MarkerRow missing set_selected"
    print("✓ MarkerRow class structure valid")

    # Check AudioMapperGUI has required methods
    assert hasattr(AudioMapperGUI, 'select_marker_row'), "GUI missing select_marker_row"
    assert hasattr(AudioMapperGUI, 'play_marker_audio'), "GUI missing play_marker_audio"
    assert hasattr(AudioMapperGUI, 'generate_marker_audio'), "GUI missing generate_marker_audio"
    print("✓ AudioMapperGUI has required stub methods")

    # Check status icon mapping
    row_instance = type('MockRow', (), {})()
    row_instance.get_status_icon = MarkerRow.get_status_icon.__get__(row_instance, type(row_instance))

    assert row_instance.get_status_icon("not yet generated") == "⭕"
    assert row_instance.get_status_icon("generating") == "⏳"
    assert row_instance.get_status_icon("generated") == "✓"
    assert row_instance.get_status_icon("failed") == "⚠️"
    print("✓ Status icon mapping correct")

    # Check type color mapping
    row_instance.get_type_color = MarkerRow.get_type_color.__get__(row_instance, type(row_instance))

    assert row_instance.get_type_color("sfx") == "#FFCDD2"
    assert row_instance.get_type_color("music") == "#BBDEFB"
    assert row_instance.get_type_color("voice") == "#C8E6C9"
    print("✓ Type color mapping correct")

    print("\n" + "=" * 70)
    print("✓ ALL STRUCTURE TESTS PASSED!")
    print("=" * 70)
    print("\nTo test visually, run:")
    print("  python3 audio_mapper.py")
    print("\nThen:")
    print("  1. Create blank timeline (File → Create Blank Timeline)")
    print("  2. Add markers using [SFX], [Music], [Voice] buttons")
    print("  3. Verify:")
    print("     - Each row has ▶ and 🔄 buttons")
    print("     - Status icons show ⭕ for new markers")
    print("     - Version badge shows v1")
    print("     - Clicking row selects it (blue background)")
    print("     - Double-clicking opens editor")
    print("     - Play button shows stub message")
    print("     - Generate button shows stub message")


if __name__ == "__main__":
    try:
        test_marker_row_class()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
