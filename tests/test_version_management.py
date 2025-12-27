#!/usr/bin/env python3
"""
Test script for version management functionality
Tests creation, versioning, rollback, and JSON export/import
"""

import json
import sys
from datetime import datetime

# Simple mock for testing without GUI
class MockVersionManager:
    def __init__(self):
        self.markers = []

    def create_default_prompt_data(self, marker_type):
        """Create empty but valid prompt_data structure for a given marker type"""
        if marker_type == "sfx":
            return {"description": ""}
        elif marker_type == "voice":
            return {"voice_profile": "", "text": ""}
        elif marker_type == "music":
            return {"positiveGlobalStyles": [], "negativeGlobalStyles": [], "sections": []}
        else:
            return {"description": ""}

    def get_current_version_data(self, marker):
        """Get the current version object from a marker"""
        if "versions" not in marker or not marker["versions"]:
            return None

        current_version = marker.get("current_version", 1)
        for version_obj in marker["versions"]:
            if version_obj["version"] == current_version:
                return version_obj
        return marker["versions"][-1] if marker["versions"] else None

    def add_new_version(self, marker, prompt_data):
        """Create a new version for a marker"""
        if "versions" not in marker:
            marker["versions"] = []

        if marker["versions"]:
            next_version = max(v["version"] for v in marker["versions"]) + 1
        else:
            next_version = 1

        type_prefix_map = {"music": "MUS", "sfx": "SFX", "voice": "VOX"}
        prefix = type_prefix_map.get(marker["type"], "ASSET")
        marker_count = int(marker.get("asset_slot", "0").split("_")[-1])
        asset_file = f"{prefix}_{marker_count:05d}_v{next_version}.mp3"

        version_obj = {
            "version": next_version,
            "asset_file": asset_file,
            "asset_id": None,
            "created_at": datetime.now().isoformat(),
            "status": "not yet generated",
            "prompt_data_snapshot": prompt_data.copy()
        }

        marker["versions"].append(version_obj)
        marker["current_version"] = next_version
        marker["asset_file"] = asset_file
        marker["prompt_data"] = prompt_data.copy()
        marker["status"] = "not yet generated"
        marker["asset_id"] = None

        return next_version

    def rollback_to_version(self, marker, version_num):
        """Roll back a marker to a specific version"""
        if "versions" not in marker or not marker["versions"]:
            return False

        target_version = None
        for version_obj in marker["versions"]:
            if version_obj["version"] == version_num:
                target_version = version_obj
                break

        if not target_version:
            return False

        marker["current_version"] = version_num
        marker["asset_file"] = target_version["asset_file"]
        marker["asset_id"] = target_version["asset_id"]
        marker["status"] = target_version["status"]
        marker["prompt_data"] = target_version["prompt_data_snapshot"].copy()

        return True

    def create_marker_with_version(self, marker_type):
        """Create a new marker with initial version structure"""
        prompt_data = self.create_default_prompt_data(marker_type)

        type_prefix_map = {"music": "MUS", "sfx": "SFX", "voice": "VOX"}
        prefix = type_prefix_map.get(marker_type, "ASSET")
        marker_count = len([m for m in self.markers if m["type"] == marker_type])
        asset_file = f"{prefix}_{marker_count:05d}_v1.mp3"

        version_obj = {
            "version": 1,
            "asset_file": asset_file,
            "asset_id": None,
            "created_at": datetime.now().isoformat(),
            "status": "not yet generated",
            "prompt_data_snapshot": prompt_data.copy()
        }

        marker = {
            "time_ms": 0,
            "type": marker_type,
            "name": f"Test {marker_type.upper()}",
            "prompt_data": prompt_data,
            "asset_slot": f"{marker_type}_{marker_count}",
            "asset_file": asset_file,
            "asset_id": None,
            "status": "not yet generated",
            "current_version": 1,
            "versions": [version_obj]
        }

        self.markers.append(marker)
        return marker


def test_version_management():
    """Run comprehensive tests"""
    print("=" * 70)
    print("VERSION MANAGEMENT TESTS")
    print("=" * 70)

    vm = MockVersionManager()

    # Test 1: Create marker with version structure
    print("\n✓ Test 1: Create SFX marker with version structure")
    marker = vm.create_marker_with_version("sfx")
    assert "versions" in marker, "Missing 'versions' field"
    assert "current_version" in marker, "Missing 'current_version' field"
    assert marker["current_version"] == 1, "Current version should be 1"
    assert len(marker["versions"]) == 1, "Should have 1 version"
    assert marker["asset_file"] == "SFX_00000_v1.mp3", f"Incorrect asset_file: {marker['asset_file']}"
    print(f"  ✓ Created marker with version: {marker['current_version']}")
    print(f"  ✓ Asset file: {marker['asset_file']}")

    # Test 2: Get current version data
    print("\n✓ Test 2: Get current version data")
    current_version_data = vm.get_current_version_data(marker)
    assert current_version_data is not None, "Should return version data"
    assert current_version_data["version"] == 1, "Version should be 1"
    print(f"  ✓ Current version: v{current_version_data['version']}")
    print(f"  ✓ Status: {current_version_data['status']}")

    # Test 3: Add new version
    print("\n✓ Test 3: Add new version (v2)")
    new_prompt_data = {"description": "Updated description for v2"}
    v2 = vm.add_new_version(marker, new_prompt_data)
    assert v2 == 2, "Should return version 2"
    assert marker["current_version"] == 2, "Current version should be 2"
    assert len(marker["versions"]) == 2, "Should have 2 versions"
    assert marker["asset_file"] == "SFX_00000_v2.mp3", f"Incorrect v2 asset_file: {marker['asset_file']}"
    print(f"  ✓ Created version v{v2}")
    print(f"  ✓ Asset file: {marker['asset_file']}")

    # Test 4: Add third version
    print("\n✓ Test 4: Add third version (v3)")
    v3_prompt_data = {"description": "Updated description for v3"}
    v3 = vm.add_new_version(marker, v3_prompt_data)
    assert v3 == 3, "Should return version 3"
    assert marker["current_version"] == 3, "Current version should be 3"
    assert len(marker["versions"]) == 3, "Should have 3 versions"
    assert marker["asset_file"] == "SFX_00000_v3.mp3", f"Incorrect v3 asset_file: {marker['asset_file']}"
    print(f"  ✓ Created version v{v3}")
    print(f"  ✓ Total versions: {len(marker['versions'])}")

    # Test 5: Rollback to v1
    print("\n✓ Test 5: Rollback to v1")
    success = vm.rollback_to_version(marker, 1)
    assert success, "Rollback should succeed"
    assert marker["current_version"] == 1, "Current version should be 1"
    assert marker["asset_file"] == "SFX_00000_v1.mp3", f"Asset file should be v1: {marker['asset_file']}"
    assert marker["prompt_data"]["description"] == "", "Should restore v1 prompt data"
    print(f"  ✓ Rolled back to v1")
    print(f"  ✓ Asset file: {marker['asset_file']}")

    # Test 6: Rollback to v2
    print("\n✓ Test 6: Rollback to v2")
    success = vm.rollback_to_version(marker, 2)
    assert success, "Rollback to v2 should succeed"
    assert marker["current_version"] == 2, "Current version should be 2"
    assert marker["asset_file"] == "SFX_00000_v2.mp3", "Asset file should be v2"
    assert marker["prompt_data"]["description"] == "Updated description for v2", "Should restore v2 prompt data"
    print(f"  ✓ Rolled back to v2")
    print(f"  ✓ Prompt data restored: {marker['prompt_data']['description']}")

    # Test 7: JSON export/import
    print("\n✓ Test 7: JSON export and import")
    template = {
        "template_id": "TEST01",
        "template_name": "Test Template",
        "duration_ms": 10000,
        "markers": vm.markers
    }

    json_str = json.dumps(template, indent=2)
    print(f"  ✓ Exported to JSON ({len(json_str)} bytes)")

    # Re-import
    imported = json.loads(json_str)
    imported_marker = imported["markers"][0]

    assert "versions" in imported_marker, "Imported marker should have versions"
    assert imported_marker["current_version"] == 2, "Current version should be preserved"
    assert len(imported_marker["versions"]) == 3, "All versions should be preserved"
    print(f"  ✓ Imported from JSON")
    print(f"  ✓ Preserved {len(imported_marker['versions'])} versions")
    print(f"  ✓ Current version: v{imported_marker['current_version']}")

    # Test 8: Create multiple marker types
    print("\n✓ Test 8: Create multiple marker types")
    voice_marker = vm.create_marker_with_version("voice")
    music_marker = vm.create_marker_with_version("music")

    assert voice_marker["asset_file"] == "VOX_00000_v1.mp3", "Voice asset file incorrect"
    assert music_marker["asset_file"] == "MUS_00000_v1.mp3", "Music asset file incorrect"
    print(f"  ✓ Voice marker: {voice_marker['asset_file']}")
    print(f"  ✓ Music marker: {music_marker['asset_file']}")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_version_management()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
