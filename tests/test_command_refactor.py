#!/usr/bin/env python3
"""
Test script to verify command refactoring works correctly
Tests all command types with MarkerRepository
"""

import copy
from core.marker_repository import MarkerRepository
from core.commands import AddMarkerCommand, DeleteMarkerCommand, EditMarkerCommand, MoveMarkerCommand
from managers.history_manager import HistoryManager


def create_test_marker(time_ms=0, marker_type="sfx", name="Test Marker"):
    """Create a test marker for testing"""
    return {
        "time_ms": time_ms,
        "type": marker_type,
        "name": name,
        "prompt_data": {"description": "Test description"},
        "asset_slot": f"{marker_type}_0",
        "asset_file": f"{marker_type.upper()}_00000.mp3",
        "asset_id": None,
        "status": "not yet generated",
        "current_version": 1,
        "versions": []
    }


def test_add_marker():
    """Test AddMarkerCommand"""
    print("\n=== Testing AddMarkerCommand ===")
    repo = MarkerRepository()
    history = HistoryManager()

    # Track UI updates
    ui_update_count = [0]
    def on_change():
        ui_update_count[0] += 1
    repo.add_change_listener(on_change)

    # Create and execute command
    marker = create_test_marker(time_ms=1000, name="Test SFX")
    command = AddMarkerCommand(repo, marker)
    history.execute_command(command)

    # Verify
    assert repo.count() == 1, f"Expected 1 marker, got {repo.count()}"
    assert repo.markers[0]["time_ms"] == 1000
    assert ui_update_count[0] == 1, f"Expected 1 UI update, got {ui_update_count[0]}"
    print("✓ Add marker works")

    # Test undo
    history.undo()
    assert repo.count() == 0, f"Expected 0 markers after undo, got {repo.count()}"
    assert ui_update_count[0] == 2, f"Expected 2 UI updates, got {ui_update_count[0]}"
    print("✓ Undo add works")

    # Test redo
    history.redo()
    assert repo.count() == 1, f"Expected 1 marker after redo, got {repo.count()}"
    assert ui_update_count[0] == 3, f"Expected 3 UI updates, got {ui_update_count[0]}"
    print("✓ Redo add works")


def test_delete_marker():
    """Test DeleteMarkerCommand"""
    print("\n=== Testing DeleteMarkerCommand ===")
    repo = MarkerRepository()
    history = HistoryManager()

    # Setup: Add a marker first
    marker = create_test_marker(time_ms=2000, name="Test Voice")
    repo.add_marker(marker)

    # Track UI updates
    ui_update_count = [0]
    def on_change():
        ui_update_count[0] += 1
    repo.add_change_listener(on_change)

    # Delete it
    command = DeleteMarkerCommand(repo, marker, 0)
    history.execute_command(command)

    # Verify
    assert repo.count() == 0, f"Expected 0 markers, got {repo.count()}"
    assert ui_update_count[0] == 1
    print("✓ Delete marker works")

    # Test undo (should restore)
    history.undo()
    assert repo.count() == 1, f"Expected 1 marker after undo, got {repo.count()}"
    assert ui_update_count[0] == 2
    print("✓ Undo delete works")


def test_edit_marker():
    """Test EditMarkerCommand"""
    print("\n=== Testing EditMarkerCommand ===")
    repo = MarkerRepository()
    history = HistoryManager()

    # Setup: Add a marker first
    marker = create_test_marker(time_ms=3000, name="Original Name")
    repo.add_marker(marker)

    # Track UI updates
    ui_update_count = [0]
    def on_change():
        ui_update_count[0] += 1
    repo.add_change_listener(on_change)

    # Edit it - MUST use deepcopy to avoid shared nested dicts
    old_marker = copy.deepcopy(repo.markers[0])
    new_marker = copy.deepcopy(old_marker)
    new_marker["name"] = "Updated Name"
    new_marker["prompt_data"]["description"] = "Updated description"

    command = EditMarkerCommand(repo, 0, old_marker, new_marker)
    history.execute_command(command)

    # Verify
    assert repo.markers[0]["name"] == "Updated Name"
    assert repo.markers[0]["prompt_data"]["description"] == "Updated description"
    assert ui_update_count[0] == 1
    print("✓ Edit marker works")

    # Test undo
    history.undo()
    assert repo.markers[0]["name"] == "Original Name"
    assert repo.markers[0]["prompt_data"]["description"] == "Test description"
    assert ui_update_count[0] == 2
    print("✓ Undo edit works")


def test_move_marker():
    """Test MoveMarkerCommand"""
    print("\n=== Testing MoveMarkerCommand ===")
    repo = MarkerRepository()
    history = HistoryManager()

    # Setup: Add two markers
    marker1 = create_test_marker(time_ms=1000, name="Marker 1")
    marker2 = create_test_marker(time_ms=5000, name="Marker 2")
    repo.add_marker(marker1)
    repo.add_marker(marker2)

    # Track UI updates
    ui_update_count = [0]
    def on_change():
        ui_update_count[0] += 1
    repo.add_change_listener(on_change)

    # Move first marker to later time (should re-sort)
    command = MoveMarkerCommand(repo, 0, 1000, 3000)
    history.execute_command(command)

    # Verify - should be sorted and UI updated
    # After move and sort, markers should be at 3000 and 5000
    times = [m["time_ms"] for m in repo.markers]
    assert times == [3000, 5000], f"Expected [3000, 5000], got {times}"
    assert ui_update_count[0] == 2  # update + sort
    print("✓ Move marker works")

    # Test undo (should move back and re-sort)
    history.undo()
    times = [m["time_ms"] for m in repo.markers]
    assert times == [1000, 5000], f"Expected [1000, 5000] after undo, got {times}"
    print("✓ Undo move works")


def test_ui_callback_integration():
    """Test that UI callbacks are triggered correctly"""
    print("\n=== Testing UI Callback Integration ===")
    repo = MarkerRepository()

    # Track what operations triggered callbacks
    operations = []
    def on_change():
        operations.append("change")
    repo.add_change_listener(on_change)

    # Perform various operations
    marker1 = create_test_marker(time_ms=1000)
    marker2 = create_test_marker(time_ms=2000)

    repo.add_marker(marker1)
    assert len(operations) == 1

    repo.add_marker(marker2)
    assert len(operations) == 2

    repo.update_marker(0, marker1)
    assert len(operations) == 3

    repo.remove_marker_at(0)
    assert len(operations) == 4

    print(f"✓ UI callback triggered {len(operations)} times for {len(operations)} operations")


def run_all_tests():
    """Run all command tests"""
    print("=" * 60)
    print("Command Refactoring - Integration Tests")
    print("=" * 60)

    try:
        test_add_marker()
        test_delete_marker()
        test_edit_marker()
        test_move_marker()
        test_ui_callback_integration()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Command Refactoring Successful!")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ Commands no longer directly reference GUI")
        print("  ✓ MarkerRepository handles all data operations")
        print("  ✓ UI updates triggered via callback listener")
        print("  ✓ Undo/redo functionality preserved")
        print("  ✓ All command types (Add, Delete, Edit, Move) working")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
