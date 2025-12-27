#!/usr/bin/env python3
"""Test file handler extraction"""

import json
import tempfile
from pathlib import Path
from file_handler import FileHandler


def test_export_and_import():
    """Test round-trip export and import"""
    # Create test data
    markers = [
        {
            "time_ms": 0,
            "type": "music",
            "name": "Background Music",
            "prompt_data": {
                "positiveGlobalStyles": ["upbeat", "electronic"],
                "negativeGlobalStyles": ["slow"],
                "sections": []
            },
            "asset_slot": "music_0",
            "asset_file": "MUS_00000_v1.mp3",
            "asset_id": None,
            "status": "not yet generated",
            "current_version": 1,
            "versions": []
        },
        {
            "time_ms": 1500,
            "type": "sfx",
            "name": "Door Slam",
            "prompt_data": {"description": "Heavy door slam"},
            "asset_slot": "sfx_0",
            "asset_file": "SFX_00000_v1.mp3",
            "asset_id": None,
            "status": "not yet generated",
            "current_version": 1,
            "versions": []
        }
    ]

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        # Export
        success, error = FileHandler.export_to_json(
            temp_path,
            markers,
            template_id="TEST01",
            template_name="Test Template",
            duration_ms=10000
        )

        assert success, f"Export failed: {error}"

        # Import
        success, data, error = FileHandler.import_from_json(temp_path)

        assert success, f"Import failed: {error}"
        assert data is not None
        assert data["template_id"] == "TEST01"
        assert data["template_name"] == "Test Template"
        assert data["duration_ms"] == 10000
        assert len(data["markers"]) == 2

        print("✓ Export and import test passed")

    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def test_migrate_old_format():
    """Test migration from old prompt format to new prompt_data format"""
    old_marker = {
        "time_ms": 1000,
        "type": "sfx",
        "prompt": "Door slam sound",
        "asset_file": "SFX_00000.mp3"
    }

    # Migrate
    new_marker = FileHandler.migrate_marker_to_new_format(old_marker)

    assert "prompt" not in new_marker
    assert "prompt_data" in new_marker
    assert new_marker["prompt_data"]["description"] == "Door slam sound"

    print("✓ Old format migration test passed")


def test_migrate_voice_format():
    """Test migration of voice marker with colon separator"""
    old_marker = {
        "time_ms": 2000,
        "type": "voice",
        "prompt": "Narrator: Hello world",
        "asset_file": "VOX_00000.mp3"
    }

    new_marker = FileHandler.migrate_marker_to_new_format(old_marker)

    assert new_marker["prompt_data"]["voice_profile"] == "Narrator"
    assert new_marker["prompt_data"]["text"] == "Hello world"

    print("✓ Voice format migration test passed")


def test_migrate_to_version_format():
    """Test migration to version tracking format"""
    marker = {
        "time_ms": 1000,
        "type": "sfx",
        "prompt_data": {"description": "Test sound"},
        "asset_file": "SFX_00000.mp3",
        "asset_id": "test_id_123",
        "status": "generated"
    }

    # Migrate
    versioned = FileHandler.migrate_marker_to_version_format(marker)

    assert "versions" in versioned
    assert "current_version" in versioned
    assert versioned["current_version"] == 1
    assert len(versioned["versions"]) == 1
    assert versioned["versions"][0]["version"] == 1
    assert versioned["versions"][0]["asset_id"] == "test_id_123"
    assert versioned["versions"][0]["status"] == "generated"
    # Should have added _v1 suffix
    assert "_v1" in versioned["asset_file"]

    print("✓ Version format migration test passed")


def test_validate_template_data():
    """Test template data validation"""
    # Valid data
    valid_data = {
        "markers": [
            {"time_ms": 0, "type": "sfx", "prompt_data": {}}
        ]
    }

    is_valid, error = FileHandler.validate_template_data(valid_data)
    assert is_valid
    assert error is None

    # Missing markers field
    invalid_data1 = {"duration_ms": 10000}
    is_valid, error = FileHandler.validate_template_data(invalid_data1)
    assert not is_valid
    assert "markers" in error

    # Invalid marker type
    invalid_data2 = {
        "markers": [
            {"time_ms": 0, "type": "invalid_type"}
        ]
    }
    is_valid, error = FileHandler.validate_template_data(invalid_data2)
    assert not is_valid
    assert "invalid type" in error.lower()

    print("✓ Validation test passed")


def test_import_with_negative_values():
    """Test import handles negative values correctly"""
    # Create temp file with negative values
    bad_data = {
        "template_id": "TEST",
        "duration_ms": -5000,  # Negative duration
        "markers": [
            {
                "time_ms": -100,  # Negative time
                "type": "sfx",
                "prompt_data": {"description": "Test"}
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(bad_data, f)
        temp_path = f.name

    try:
        # Import should succeed but fix negative values
        success, data, error = FileHandler.import_from_json(temp_path)

        assert success
        assert data["duration_ms"] == 0  # Should be fixed to 0
        assert data["markers"][0]["time_ms"] == 0  # Should be fixed to 0

        print("✓ Negative values handling test passed")

    finally:
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("Testing file_handler.py...")
    test_export_and_import()
    test_migrate_old_format()
    test_migrate_voice_format()
    test_migrate_to_version_format()
    test_validate_template_data()
    test_import_with_negative_values()
    print("\n✅ All file handler tests passed!")
