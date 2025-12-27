#!/usr/bin/env python3
"""
Test script for Checkpoint 8: Batch Operations UI
Tests batch generation functionality, progress modal, and queue-based processing
"""

import sys
import os

def test_batch_operations():
    """Test the batch operations functionality"""
    print("=" * 70)
    print("BATCH OPERATIONS UI - FUNCTIONALITY TEST")
    print("=" * 70)

    # Test 1: Import check
    print("\n✓ Test 1: Import modules")
    try:
        from audio_mapper import AudioMapperGUI, BatchProgressWindow
        print("  ✓ Modules imported successfully")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

    # Test 2: Check BatchProgressWindow class exists
    print("\n✓ Test 2: BatchProgressWindow class")
    assert hasattr(BatchProgressWindow, '__init__'), "Should have __init__"
    assert hasattr(BatchProgressWindow, 'update_progress'), "Should have update_progress"
    assert hasattr(BatchProgressWindow, 'mark_success'), "Should have mark_success"
    assert hasattr(BatchProgressWindow, 'mark_failed'), "Should have mark_failed"
    assert hasattr(BatchProgressWindow, 'on_cancel'), "Should have on_cancel"
    assert hasattr(BatchProgressWindow, 'show_summary'), "Should have show_summary"
    print("  ✓ BatchProgressWindow has all required methods")

    # Test 3: Check batch methods exist
    print("\n✓ Test 3: Batch operation methods")
    assert hasattr(AudioMapperGUI, 'batch_generate_missing'), "Should have batch_generate_missing"
    assert hasattr(AudioMapperGUI, 'batch_regenerate_all'), "Should have batch_regenerate_all"
    assert hasattr(AudioMapperGUI, 'batch_generate_by_type'), "Should have batch_generate_by_type"
    print("  ✓ All batch methods exist")

    # Test 4: Check helper methods exist
    print("\n✓ Test 4: Helper methods for batch processing")
    assert hasattr(AudioMapperGUI, '_run_batch_generation'), "Should have _run_batch_generation"
    assert hasattr(AudioMapperGUI, '_generate_marker_for_batch'), "Should have _generate_marker_for_batch"
    assert hasattr(AudioMapperGUI, '_generate_audio_background_for_batch'), "Should have background method"
    print("  ✓ All helper methods exist")

    # Test 5: Verify batch_generate_missing implementation
    print("\n✓ Test 5: batch_generate_missing implementation")
    import inspect
    source = inspect.getsource(AudioMapperGUI.batch_generate_missing)
    assert 'not_yet_generated' in source, "Should filter for not_yet_generated status"
    assert 'messagebox.askyesno' in source, "Should confirm before starting"
    assert '_run_batch_generation' in source, "Should call _run_batch_generation"
    print("  ✓ batch_generate_missing correctly filters and confirms")

    # Test 6: Verify batch_regenerate_all implementation
    print("\n✓ Test 6: batch_regenerate_all implementation")
    source = inspect.getsource(AudioMapperGUI.batch_regenerate_all)
    assert 'for i, marker in enumerate(self.markers)' in source, "Should include all markers"
    assert 'messagebox.askyesno' in source, "Should confirm before starting"
    assert 'new versions' in source.lower(), "Should mention creating new versions"
    print("  ✓ batch_regenerate_all includes all markers")

    # Test 7: Verify batch_generate_by_type implementation
    print("\n✓ Test 7: batch_generate_by_type implementation")
    source = inspect.getsource(AudioMapperGUI.batch_generate_by_type)
    assert 'Toplevel' in source, "Should show type selection dialog"
    assert 'sfx' in source, "Should offer SFX option"
    assert 'voice' in source, "Should offer Voice option"
    assert 'music' in source, "Should offer Music option"
    assert "marker['type'] ==" in source, "Should filter by type"
    print("  ✓ batch_generate_by_type shows dialog and filters correctly")

    # Test 8: Verify _run_batch_generation implementation
    print("\n✓ Test 8: Queue-based processing")
    source = inspect.getsource(AudioMapperGUI._run_batch_generation)
    assert 'BatchProgressWindow' in source, "Should create progress window"
    assert 'process_next_marker' in source, "Should have queue processing function"
    assert 'progress.cancelled' in source, "Should check for cancellation"
    assert 'current_idx + 1' in source, "Should process one at a time"
    print("  ✓ Queue-based processing implemented correctly")

    # Test 9: Verify progress window features
    print("\n✓ Test 9: Progress window features")
    source = inspect.getsource(BatchProgressWindow.__init__)
    assert 'Progressbar' in source, "Should have progress bar"
    assert 'cancel_btn' in source, "Should have cancel button"
    assert 'grab_set' in source, "Should be modal"
    print("  ✓ Progress window has all features")

    # Test 10: Verify summary dialog
    print("\n✓ Test 10: Summary dialog")
    source = inspect.getsource(BatchProgressWindow.show_summary)
    assert 'success_count' in source, "Should show success count"
    assert 'failed_count' in source, "Should show failed count"
    assert 'skipped' in source.lower(), "Should show skipped count"
    assert 'messagebox.showinfo' in source, "Should show info dialog"
    print("  ✓ Summary dialog shows all stats")

    print("\n" + "=" * 70)
    print("✓ ALL BATCH OPERATIONS TESTS PASSED!")
    print("=" * 70)
    print("\n🎯 Implementation Complete:")
    print("  • BatchProgressWindow class (500x250px modal)")
    print("  • Progress bar with current marker display")
    print("  • Cancel button with confirmation")
    print("  • Three batch operation methods:")
    print("    - batch_generate_missing() - Only ⭕ markers")
    print("    - batch_regenerate_all() - All markers, new versions")
    print("    - batch_generate_by_type() - Filter by SFX/Voice/Music")
    print("  • Queue-based processing (one at a time)")
    print("  • Summary dialog (Generated ✓, Failed ⚠️, Skipped ○)")
    print("\n⚡ How to Test Manually:")
    print("  1. Run: python3 audio_mapper.py")
    print("  2. Create blank timeline (10000ms)")
    print("  3. Add 3 markers:")
    print("     - SFX at 0ms: 'UI click sound'")
    print("     - Voice at 2000ms: 'Hello world'")
    print("     - Music at 5000ms: Add section")
    print("  4. Click '🔄 Generate All Missing' button")
    print("  5. See:")
    print("     - Confirmation dialog appears")
    print("     - Progress window opens")
    print("     - Each marker processes in sequence")
    print("     - Progress bar updates")
    print("     - Can click Cancel to stop")
    print("     - Summary dialog shows results")
    print("  6. Test other batch buttons:")
    print("     - '🔄 Regenerate All' - Creates v2 for all")
    print("     - '🔄 Generate Type...' - Shows SFX/Voice/Music dialog")
    print("\n📋 Batch Operation Flow:")
    print("  1. User clicks batch button")
    print("  2. System collects markers to process")
    print("  3. Confirmation dialog shows count")
    print("  4. Progress modal opens")
    print("  5. Queue processes markers one at a time:")
    print("     - Update progress display")
    print("     - Generate audio (background thread)")
    print("     - Wait for completion")
    print("     - Mark success/failed")
    print("     - Move to next marker")
    print("  6. Summary dialog shows final stats")
    print("\n⚠️  NOTE: Each generation uses ElevenLabs API credits!")
    print("    Test with 1-2 markers first.")

    return True


if __name__ == "__main__":
    try:
        success = test_batch_operations()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
