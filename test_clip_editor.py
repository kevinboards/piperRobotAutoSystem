"""
Unit tests for Clip Editing and Trimming functionality (V2 Phase 3).

Tests for clip_editor.py functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path

from timeline import TimelineClip
from clip_editor import (
    ClipEditor, apply_trim_to_data, validate_trim_values,
    calculate_trim_percentage, suggest_trim_values, get_trim_positions,
    format_trim_display, parse_trim_input, get_trim_slider_range
)


class TestClipEditor(unittest.TestCase):
    """Test ClipEditor functionality."""
    
    def setUp(self):
        """Set up test clip."""
        self.clip = TimelineClip(
            id="test_001",
            recording_file="test.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0,
            name="Test Clip"
        )
        self.editor = ClipEditor(self.clip)
    
    def test_create_editor(self):
        """Test creating a clip editor."""
        self.assertEqual(self.editor.clip, self.clip)
        self.assertIsNone(self.editor._cached_data)
    
    def test_preview_trim_valid(self):
        """Test previewing valid trim."""
        preview = self.editor.preview_trim(1.0, 2.0)
        
        self.assertTrue(preview["valid"])
        self.assertEqual(preview["original_duration"], 10.0)
        self.assertEqual(preview["new_duration"], 7.0)
        self.assertEqual(preview["trim_start"], 1.0)
        self.assertEqual(preview["trim_end"], 2.0)
        self.assertEqual(len(preview["warnings"]), 0)
    
    def test_preview_trim_invalid_negative(self):
        """Test previewing invalid trim (negative)."""
        preview = self.editor.preview_trim(-1.0, 0.0)
        
        self.assertFalse(preview["valid"])
        self.assertGreater(len(preview["warnings"]), 0)
    
    def test_preview_trim_exceeds_duration(self):
        """Test previewing trim that exceeds duration."""
        preview = self.editor.preview_trim(6.0, 6.0)
        
        self.assertFalse(preview["valid"])
        self.assertIn("exceeds", preview["warnings"][0].lower())
    
    def test_apply_trim(self):
        """Test applying valid trim."""
        success = self.editor.apply_trim(1.0, 2.0)
        
        self.assertTrue(success)
        self.assertEqual(self.clip.trim_start, 1.0)
        self.assertEqual(self.clip.trim_end, 2.0)
        self.assertEqual(self.clip.duration, 7.0)
    
    def test_apply_trim_invalid(self):
        """Test applying invalid trim."""
        success = self.editor.apply_trim(-1.0, 0.0)
        
        self.assertFalse(success)
        # Clip should remain unchanged
        self.assertEqual(self.clip.trim_start, 0.0)
        self.assertEqual(self.clip.trim_end, 0.0)
    
    def test_reset_trim(self):
        """Test resetting trim."""
        self.editor.apply_trim(1.0, 2.0)
        self.assertEqual(self.clip.duration, 7.0)
        
        self.editor.reset_trim()
        
        self.assertEqual(self.clip.trim_start, 0.0)
        self.assertEqual(self.clip.trim_end, 0.0)
        self.assertEqual(self.clip.duration, 10.0)
    
    def test_apply_speed(self):
        """Test applying speed multiplier."""
        success = self.editor.apply_speed(2.0)
        
        self.assertTrue(success)
        self.assertEqual(self.clip.speed_multiplier, 2.0)
    
    def test_apply_speed_invalid(self):
        """Test applying invalid speed."""
        success = self.editor.apply_speed(5.0)  # Too high
        
        self.assertFalse(success)
        self.assertEqual(self.clip.speed_multiplier, 1.0)  # Unchanged
    
    def test_get_clip_stats(self):
        """Test getting clip statistics."""
        stats = self.editor.get_clip_stats()
        
        self.assertEqual(stats["name"], "Test Clip")
        self.assertEqual(stats["original_duration"], 10.0)
        self.assertEqual(stats["current_duration"], 10.0)
        self.assertEqual(stats["trimmed_percentage"], 0.0)


class TestTrimDataOperations(unittest.TestCase):
    """Test trim data manipulation functions."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample recording data
        self.test_data = []
        for i in range(100):
            self.test_data.append({
                "timestamp": 1000 + (i * 5),  # 5ms intervals = 200 Hz
                "cartesian": {"x": 0.0, "y": 0.0, "z": 0.0},
                "joint_angles": {f"joint_{j+1}": 0.0 for j in range(6)},
                "gripper": {"angle": 0.0, "effort": 0, "status": 0}
            })
    
    def test_apply_trim_no_trim(self):
        """Test applying no trim (should return original data)."""
        trimmed = apply_trim_to_data(self.test_data, 0.0, 0.0)
        
        self.assertEqual(len(trimmed), len(self.test_data))
    
    def test_apply_trim_start(self):
        """Test trimming from start."""
        # Trim 0.1 seconds from start (20 samples at 200 Hz)
        trimmed = apply_trim_to_data(self.test_data, 0.1, 0.0)
        
        self.assertLess(len(trimmed), len(self.test_data))
        # First timestamp should be later
        self.assertGreater(trimmed[0]["timestamp"], self.test_data[0]["timestamp"])
    
    def test_apply_trim_end(self):
        """Test trimming from end."""
        # Trim 0.1 seconds from end
        trimmed = apply_trim_to_data(self.test_data, 0.0, 0.1)
        
        self.assertLess(len(trimmed), len(self.test_data))
        # Last timestamp should be earlier
        self.assertLess(trimmed[-1]["timestamp"], self.test_data[-1]["timestamp"])
    
    def test_apply_trim_both(self):
        """Test trimming from both ends."""
        trimmed = apply_trim_to_data(self.test_data, 0.1, 0.1)
        
        self.assertLess(len(trimmed), len(self.test_data))
        # Should be trimmed from both ends
        self.assertGreater(trimmed[0]["timestamp"], self.test_data[0]["timestamp"])
        self.assertLess(trimmed[-1]["timestamp"], self.test_data[-1]["timestamp"])


class TestTrimValidation(unittest.TestCase):
    """Test trim validation functions."""
    
    def test_validate_trim_valid(self):
        """Test validating valid trim."""
        is_valid, errors = validate_trim_values(10.0, 1.0, 2.0)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_trim_negative_start(self):
        """Test validating negative trim start."""
        is_valid, errors = validate_trim_values(10.0, -1.0, 0.0)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("negative", errors[0].lower())
    
    def test_validate_trim_negative_end(self):
        """Test validating negative trim end."""
        is_valid, errors = validate_trim_values(10.0, 0.0, -1.0)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_trim_exceeds_duration(self):
        """Test validating trim that exceeds duration."""
        is_valid, errors = validate_trim_values(10.0, 6.0, 6.0)
        
        self.assertFalse(is_valid)
        self.assertIn("exceeds", errors[0].lower())
    
    def test_validate_trim_edge_case(self):
        """Test validating trim at exact duration (valid but warning)."""
        is_valid, errors = validate_trim_values(10.0, 5.0, 5.0)
        
        # This is technically valid (duration = 0) but should warn
        self.assertTrue(is_valid)


class TestTrimCalculations(unittest.TestCase):
    """Test trim calculation functions."""
    
    def test_calculate_trim_percentage_none(self):
        """Test calculating percentage with no trim."""
        percentage = calculate_trim_percentage(10.0, 0.0, 0.0)
        
        self.assertEqual(percentage, 0.0)
    
    def test_calculate_trim_percentage_half(self):
        """Test calculating percentage with 50% trim."""
        percentage = calculate_trim_percentage(10.0, 3.0, 2.0)
        
        self.assertEqual(percentage, 50.0)
    
    def test_calculate_trim_percentage_full(self):
        """Test calculating percentage with 100% trim."""
        percentage = calculate_trim_percentage(10.0, 5.0, 5.0)
        
        self.assertEqual(percentage, 100.0)
    
    def test_suggest_trim_values(self):
        """Test suggesting trim values from sample counts."""
        # Create test data with known sample rate
        test_data = [
            {"timestamp": 1000 + (i * 5)} for i in range(100)
        ]
        
        # Remove first 10 and last 10 samples
        trim_start, trim_end = suggest_trim_values(test_data, 10, 10)
        
        # Should be approximately 0.05s each (10 samples * 5ms)
        self.assertAlmostEqual(trim_start, 0.05, places=2)
        self.assertAlmostEqual(trim_end, 0.05, places=2)


class TestTrimFormatting(unittest.TestCase):
    """Test trim display and parsing functions."""
    
    def test_format_trim_seconds(self):
        """Test formatting trim value in seconds."""
        formatted = format_trim_display(1.5)
        
        self.assertEqual(formatted, "1.50s")
    
    def test_format_trim_milliseconds(self):
        """Test formatting trim value in milliseconds."""
        formatted = format_trim_display(0.5)
        
        self.assertIn("ms", formatted)
    
    def test_parse_trim_seconds(self):
        """Test parsing trim value from seconds string."""
        value = parse_trim_input("1.5s")
        
        self.assertAlmostEqual(value, 1.5)
    
    def test_parse_trim_milliseconds(self):
        """Test parsing trim value from milliseconds string."""
        value = parse_trim_input("500ms")
        
        self.assertAlmostEqual(value, 0.5)
    
    def test_parse_trim_plain_number(self):
        """Test parsing trim value from plain number."""
        value = parse_trim_input("1.5")
        
        self.assertAlmostEqual(value, 1.5)
    
    def test_parse_trim_invalid(self):
        """Test parsing invalid trim value."""
        value = parse_trim_input("invalid")
        
        self.assertIsNone(value)
    
    def test_get_trim_slider_range(self):
        """Test calculating slider range."""
        min_val, max_val = get_trim_slider_range(10.0, max_trim_percentage=50.0)
        
        self.assertEqual(min_val, 0.0)
        self.assertEqual(max_val, 5.0)  # 50% of 10.0


class TestTrimIntegration(unittest.TestCase):
    """Integration tests for trim functionality."""
    
    def test_trim_workflow(self):
        """Test complete trim workflow."""
        # Create clip
        clip = TimelineClip(
            id="test_001",
            recording_file="test.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0,
            name="Test Clip"
        )
        
        # Create editor
        editor = ClipEditor(clip)
        
        # Preview trim
        preview = editor.preview_trim(1.0, 2.0)
        self.assertTrue(preview["valid"])
        self.assertEqual(preview["new_duration"], 7.0)
        
        # Apply trim
        success = editor.apply_trim(1.0, 2.0)
        self.assertTrue(success)
        self.assertEqual(clip.duration, 7.0)
        
        # Get stats
        stats = editor.get_clip_stats()
        self.assertEqual(stats["trimmed_percentage"], 30.0)  # 3/10 = 30%
        
        # Reset
        editor.reset_trim()
        self.assertEqual(clip.duration, 10.0)
        self.assertEqual(clip.trim_start, 0.0)
        self.assertEqual(clip.trim_end, 0.0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()

