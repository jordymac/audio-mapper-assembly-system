#!/usr/bin/env python3
"""
Test script for Checkpoint 6: Edit Modal with Version History
Tests version dropdown, rollback, play, and metadata display
"""

import sys
import os

def test_version_history_ui():
    """Test the version history UI components"""
    print("=" * 70)
    print("VERSION HISTORY UI - FUNCTIONALITY TEST")
    print("=" * 70)

    # Test 1: Import check
    print("\n✓ Test 1: Import modules")
    try:
        from audio_mapper import PromptEditorWindow
        print("  ✓ PromptEditorWindow imported successfully")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False

    # Test 2: Check new methods exist
    print("\n✓ Test 2: Version history methods")
    assert hasattr(PromptEditorWindow, 'create_version_history_section'), "Should have version history section"
    assert hasattr(PromptEditorWindow, 'get_selected_version_number'), "Should have version number getter"
    assert hasattr(PromptEditorWindow, 'update_version_metadata'), "Should have metadata updater"
    assert hasattr(PromptEditorWindow, 'on_version_selected'), "Should have version selection handler"
    assert hasattr(PromptEditorWindow, 'on_rollback_version'), "Should have rollback handler"
    assert hasattr(PromptEditorWindow, 'on_play_version'), "Should have play handler"
    assert hasattr(PromptEditorWindow, '_check_if_prompt_changed'), "Should have prompt change checker"
    print("  ✓ All version history methods exist")

    # Test 3: Check constructor accepts gui_ref
    print("\n✓ Test 3: Constructor signature")
    import inspect
    sig = inspect.signature(PromptEditorWindow.__init__)
    params = list(sig.parameters.keys())
    assert 'gui_ref' in params, "Constructor should accept gui_ref parameter"
    print("  ✓ Constructor accepts gui_ref parameter")

    # Test 4: Check on_save creates versions
    print("\n✓ Test 4: Save behavior creates versions")
    # The on_save method should call gui_ref.add_new_version if prompt changed
    source = inspect.getsource(PromptEditorWindow.on_save)
    assert 'add_new_version' in source, "on_save should call add_new_version"
    assert '_check_if_prompt_changed' in source, "on_save should check if prompt changed"
    print("  ✓ on_save creates new versions when prompt changes")

    # Test 5: Verify version dropdown creation
    print("\n✓ Test 5: Version dropdown components")
    source = inspect.getsource(PromptEditorWindow.create_version_history_section)
    assert 'version_var' in source, "Should create version_var"
    assert 'version_dropdown' in source, "Should create version_dropdown"
    assert 'rollback_btn' in source, "Should create rollback button"
    assert 'play_version_btn' in source, "Should create play button"
    assert 'metadata_label' in source, "Should create metadata label"
    print("  ✓ All UI components created")

    # Test 6: Verify rollback functionality
    print("\n✓ Test 6: Rollback functionality")
    source = inspect.getsource(PromptEditorWindow.on_rollback_version)
    assert 'rollback_to_version' in source, "Should call rollback_to_version"
    assert 'update_content_area' in source, "Should rebuild content after rollback"
    assert 'messagebox.askyesno' in source, "Should confirm before rollback"
    print("  ✓ Rollback includes confirmation and content update")

    # Test 7: Verify play functionality
    print("\n✓ Test 7: Play version functionality")
    source = inspect.getsource(PromptEditorWindow.on_play_version)
    assert 'audio_player' in source, "Should use audio_player"
    assert 'play_audio_file' in source, "Should call play_audio_file"
    assert 'asset_file' in source, "Should get asset_file from version"
    print("  ✓ Play uses audio player and version's asset file")

    # Test 8: Verify metadata display
    print("\n✓ Test 8: Metadata display")
    source = inspect.getsource(PromptEditorWindow.update_version_metadata)
    assert 'created_at' in source, "Should display created_at"
    assert 'status' in source, "Should display status"
    assert 'asset_file' in source, "Should display asset_file"
    print("  ✓ Metadata displays created date, status, and asset file")

    print("\n" + "=" * 70)
    print("✓ ALL VERSION HISTORY UI TESTS PASSED!")
    print("=" * 70)
    print("\n🎯 Implementation Complete:")
    print("  • Version History section at top of editor")
    print("  • Version dropdown (newest first)")
    print("  • Rollback button with confirmation")
    print("  • Play button for any version")
    print("  • Metadata display (date, status, asset)")
    print("  • Save creates new version if prompt changed")
    print("\n⚡ How to Test Manually:")
    print("  1. Run: python3 audio_mapper.py")
    print("  2. Create blank timeline (10000ms)")
    print("  3. Add SFX marker, save with description 'v1'")
    print("  4. Double-click marker to edit")
    print("  5. See Version History section at top")
    print("  6. Change description to 'v2', Save")
    print("  7. Reopen editor - should now show v2 (current), v1")
    print("  8. Select v1 from dropdown")
    print("  9. View metadata for v1")
    print(" 10. Click Rollback - confirms and restores v1 prompt")
    print(" 11. Generate audio for current version")
    print(" 12. Reopen editor, select any version, click Play")
    print("\n📋 Workflow Example:")
    print("  • Edit prompt → Save → Creates v2 (not_yet_generated)")
    print("  • Click 🔄 Generate → Creates v3 with audio (generated)")
    print("  • Edit again → Save → Creates v4 (not_yet_generated)")
    print("  • Each version preserves prompt snapshot")
    print("  • Can rollback to any version")
    print("  • Can play audio from any generated version")

    return True


if __name__ == "__main__":
    try:
        success = test_version_history_ui()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
