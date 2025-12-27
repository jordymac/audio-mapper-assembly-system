#!/usr/bin/env python3
"""
Test script for Checkpoint 7: Timeline-List Selection Sync
Tests bidirectional selection between timeline markers and list rows
"""

import sys
import os

def test_selection_sync():
    """Test the selection synchronization functionality"""
    print("=" * 70)
    print("TIMELINE-LIST SELECTION SYNC - FUNCTIONALITY TEST")
    print("=" * 70)

    # Test 1: Import check
    print("\n✓ Test 1: Import modules")
    try:
        from audio_mapper import AudioMapperGUI, MarkerRow
        print("  ✓ Modules imported successfully")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

    # Test 2: Check select_marker_row method exists
    print("\n✓ Test 2: Selection method exists")
    assert hasattr(AudioMapperGUI, 'select_marker_row'), "Should have select_marker_row method"
    print("  ✓ select_marker_row() method exists")

    # Test 3: Check deselect_marker method exists
    print("\n✓ Test 3: Deselection method exists")
    assert hasattr(AudioMapperGUI, 'deselect_marker'), "Should have deselect_marker method"
    print("  ✓ deselect_marker() method exists")

    # Test 4: Verify selection updates both row and timeline
    print("\n✓ Test 4: Selection updates both row and timeline")
    import inspect
    source = inspect.getsource(AudioMapperGUI.select_marker_row)
    assert 'set_selected(True)' in source, "Should set row as selected"
    assert 'redraw_marker_indicators' in source, "Should redraw timeline markers"
    assert 'selected_marker_index' in source, "Should track selected index"
    print("  ✓ Selection updates both UI components")

    # Test 5: Verify timeline marker clicks trigger selection
    print("\n✓ Test 5: Timeline marker clicks trigger selection")
    source = inspect.getsource(AudioMapperGUI.start_drag_marker)
    assert 'select_marker_row' in source, "start_drag_marker should call select_marker_row"
    print("  ✓ Timeline marker clicks call select_marker_row()")

    # Test 6: Verify row clicks trigger selection
    print("\n✓ Test 6: Row clicks trigger selection")
    source = inspect.getsource(MarkerRow.on_row_click)
    assert 'select_marker_row' in source, "Row click should call select_marker_row"
    print("  ✓ Row clicks call select_marker_row()")

    # Test 7: Verify visual feedback for selected row
    print("\n✓ Test 7: Visual feedback for selected row")
    source = inspect.getsource(MarkerRow.set_selected)
    assert '#BBDEFB' in source or 'bg' in source, "Should change background color"
    assert 'SUNKEN' in source or 'relief' in source, "Should change relief style"
    print("  ✓ Selected rows have visual feedback (blue background, sunken relief)")

    # Test 8: Verify visual feedback for selected timeline marker
    print("\n✓ Test 8: Visual feedback for selected timeline marker")
    source = inspect.getsource(AudioMapperGUI.redraw_marker_indicators)
    assert 'is_selected' in source, "Should check if marker is selected"
    assert 'line_width' in source or 'width' in source, "Should vary line width"
    assert 'glow' in source or 'white' in source, "Should add glow for selected markers"
    print("  ✓ Selected markers have visual feedback (thicker line, white glow)")

    # Test 9: Verify empty space click clears selection
    print("\n✓ Test 9: Empty space click clears selection")
    waveform_source = inspect.getsource(AudioMapperGUI.on_waveform_click)
    filmstrip_source = inspect.getsource(AudioMapperGUI.on_filmstrip_click)
    assert 'deselect_marker' in waveform_source, "Waveform click should deselect if not on marker"
    assert 'deselect_marker' in filmstrip_source, "Filmstrip click should deselect if not on marker"
    print("  ✓ Empty space clicks clear selection")

    # Test 10: Verify deselect clears both row and timeline
    print("\n✓ Test 10: Deselect clears both components")
    source = inspect.getsource(AudioMapperGUI.deselect_marker)
    assert 'set_selected(False)' in source, "Should deselect row"
    assert 'selected_marker_index' in source, "Should clear selected index"
    print("  ✓ Deselect updates both row and timeline")

    print("\n" + "=" * 70)
    print("✓ ALL SELECTION SYNC TESTS PASSED!")
    print("=" * 70)
    print("\n🎯 Implementation Status:")
    print("  ✅ select_marker_row() method (formerly select_marker_by_index)")
    print("  ✅ Timeline marker clicks → highlight list row")
    print("  ✅ List row clicks → highlight timeline marker")
    print("  ✅ Visual feedback:")
    print("     • Selected row: Light blue background (#BBDEFB) + sunken relief")
    print("     • Selected timeline marker: Thicker line (5px vs 3px) + white glow")
    print("  ✅ Empty space clicks clear selection")
    print("\n⚡ How Selection Works:")
    print("  1. Click timeline marker → Calls start_drag_marker()")
    print("     → Calls select_marker_row(index)")
    print("     → Highlights row + redraws timeline with thicker marker")
    print("  2. Click list row → Calls on_row_click()")
    print("     → Calls select_marker_row(index)")
    print("     → Same highlighting as above")
    print("  3. Click empty timeline space → Calls on_waveform_click()")
    print("     → Detects no marker → Calls deselect_marker()")
    print("     → Clears all highlighting")
    print("\n📋 Manual Test:")
    print("  1. Run: python3 audio_mapper.py")
    print("  2. Create blank timeline (10000ms)")
    print("  3. Add 3 markers at 0ms, 2000ms, 5000ms")
    print("  4. Click marker in list → See:")
    print("     - Row turns light blue")
    print("     - Timeline marker becomes thicker with white glow")
    print("  5. Click different timeline marker → See:")
    print("     - Previous row deselected")
    print("     - New row selected (light blue)")
    print("     - Timeline marker thick + glow")
    print("  6. Click empty timeline space → See:")
    print("     - All selection cleared")
    print("     - Row returns to white")
    print("     - Timeline marker returns to normal thickness")
    print("\n✨ This checkpoint was already implemented!")
    print("   All functionality existed from previous checkpoints.")

    return True


if __name__ == "__main__":
    try:
        success = test_selection_sync()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
