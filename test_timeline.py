"""
Unit tests for Timeline System (V2).

Tests for timeline.py and ppt_file_handler.py functionality.
"""

import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from timeline import (
    TimelineClip, Timeline, TimelineManager,
    get_clip_color, CLIP_COLORS
)
from ppt_file_handler import (
    save_timeline, load_timeline, validate_timeline_file,
    get_timeline_info, list_timeline_files, create_backup
)


class TestTimelineClip(unittest.TestCase):
    """Test TimelineClip functionality."""
    
    def test_create_clip(self):
        """Test creating a basic clip."""
        clip = TimelineClip(
            id="test_001",
            recording_file="test.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0,
            name="Test Clip"
        )
        
        self.assertEqual(clip.id, "test_001")
        self.assertEqual(clip.name, "Test Clip")
        self.assertEqual(clip.duration, 10.0)
        self.assertEqual(clip.end_time, 10.0)
    
    def test_clip_with_trim(self):
        """Test clip with trimming."""
        clip = TimelineClip(
            id="test_002",
            recording_file="test.ppr",
            start_time=0.0,
            duration=8.0,
            trim_start=1.0,
            trim_end=1.0,
            original_duration=10.0,
            name="Trimmed Clip"
        )
        
        self.assertEqual(clip.trimmed_duration, 8.0)
        self.assertEqual(clip.trim_start, 1.0)
        self.assertEqual(clip.trim_end, 1.0)
    
    def test_invalid_speed(self):
        """Test that invalid speed raises error."""
        with self.assertRaises(ValueError):
            TimelineClip(
                id="test_003",
                recording_file="test.ppr",
                start_time=0.0,
                duration=10.0,
                original_duration=10.0,
                speed_multiplier=5.0  # Invalid: > 4.0
            )
    
    def test_negative_duration(self):
        """Test that negative duration raises error."""
        with self.assertRaises(ValueError):
            TimelineClip(
                id="test_004",
                recording_file="test.ppr",
                start_time=0.0,
                duration=-5.0,
                original_duration=10.0
            )
    
    def test_excessive_trim(self):
        """Test that trim exceeding duration raises error."""
        with self.assertRaises(ValueError):
            TimelineClip(
                id="test_005",
                recording_file="test.ppr",
                start_time=0.0,
                duration=0.0,
                trim_start=6.0,
                trim_end=6.0,
                original_duration=10.0
            )
    
    def test_clip_to_dict(self):
        """Test converting clip to dictionary."""
        clip = TimelineClip(
            id="test_006",
            recording_file="test.ppr",
            start_time=5.0,
            duration=10.0,
            original_duration=10.0,
            name="Dict Test"
        )
        
        clip_dict = clip.to_dict()
        self.assertIsInstance(clip_dict, dict)
        self.assertEqual(clip_dict['id'], "test_006")
        self.assertEqual(clip_dict['name'], "Dict Test")
        self.assertEqual(clip_dict['start_time'], 5.0)
    
    def test_clip_from_dict(self):
        """Test creating clip from dictionary."""
        clip_data = {
            'id': "test_007",
            'recording_file': "test.ppr",
            'start_time': 0.0,
            'duration': 10.0,
            'trim_start': 0.0,
            'trim_end': 0.0,
            'speed_multiplier': 1.0,
            'enabled': True,
            'name': "From Dict",
            'color': "#4CAF50",
            'original_duration': 10.0
        }
        
        clip = TimelineClip.from_dict(clip_data)
        self.assertEqual(clip.id, "test_007")
        self.assertEqual(clip.name, "From Dict")


class TestTimeline(unittest.TestCase):
    """Test Timeline functionality."""
    
    def setUp(self):
        """Set up test timeline."""
        self.timeline = Timeline(name="Test Timeline")
        
        self.clip1 = TimelineClip(
            id="clip_001",
            recording_file="test1.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0,
            name="Clip 1"
        )
        
        self.clip2 = TimelineClip(
            id="clip_002",
            recording_file="test2.ppr",
            start_time=15.0,
            duration=8.0,
            original_duration=8.0,
            name="Clip 2"
        )
    
    def test_create_timeline(self):
        """Test creating an empty timeline."""
        self.assertEqual(self.timeline.name, "Test Timeline")
        self.assertEqual(len(self.timeline.clips), 0)
        self.assertEqual(self.timeline.total_duration, 0.0)
    
    def test_add_clip(self):
        """Test adding clips to timeline."""
        self.timeline.add_clip(self.clip1)
        self.assertEqual(len(self.timeline.clips), 1)
        
        self.timeline.add_clip(self.clip2)
        self.assertEqual(len(self.timeline.clips), 2)
    
    def test_total_duration(self):
        """Test calculating total timeline duration."""
        self.timeline.add_clip(self.clip1)
        self.timeline.add_clip(self.clip2)
        
        # clip2 ends at 15.0 + 8.0 = 23.0
        self.assertEqual(self.timeline.total_duration, 23.0)
    
    def test_get_clip_by_id(self):
        """Test finding clip by ID."""
        self.timeline.add_clip(self.clip1)
        
        found = self.timeline.get_clip_by_id("clip_001")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Clip 1")
        
        not_found = self.timeline.get_clip_by_id("nonexistent")
        self.assertIsNone(not_found)
    
    def test_remove_clip(self):
        """Test removing clip from timeline."""
        self.timeline.add_clip(self.clip1)
        self.timeline.add_clip(self.clip2)
        
        self.assertTrue(self.timeline.remove_clip("clip_001"))
        self.assertEqual(len(self.timeline.clips), 1)
        
        self.assertFalse(self.timeline.remove_clip("clip_001"))  # Already removed
    
    def test_move_clip(self):
        """Test moving clip to new time."""
        self.timeline.add_clip(self.clip1)
        
        self.assertTrue(self.timeline.move_clip("clip_001", 5.0))
        self.assertEqual(self.clip1.start_time, 5.0)
    
    def test_update_trim(self):
        """Test updating clip trim values."""
        self.timeline.add_clip(self.clip1)
        
        self.assertTrue(self.timeline.update_clip_trim("clip_001", 1.0, 2.0))
        self.assertEqual(self.clip1.trim_start, 1.0)
        self.assertEqual(self.clip1.trim_end, 2.0)
        self.assertEqual(self.clip1.duration, 7.0)  # 10 - 1 - 2
    
    def test_duplicate_clip(self):
        """Test duplicating a clip."""
        self.timeline.add_clip(self.clip1)
        
        new_clip = self.timeline.duplicate_clip("clip_001")
        self.assertIsNotNone(new_clip)
        self.assertEqual(len(self.timeline.clips), 2)
        self.assertNotEqual(new_clip.id, self.clip1.id)
        self.assertEqual(new_clip.recording_file, self.clip1.recording_file)
    
    def test_get_sorted_clips(self):
        """Test getting clips sorted by start time."""
        # Add clips out of order
        self.timeline.add_clip(self.clip2)  # starts at 15.0
        self.timeline.add_clip(self.clip1)  # starts at 0.0
        
        sorted_clips = self.timeline.get_sorted_clips()
        self.assertEqual(sorted_clips[0].id, "clip_001")
        self.assertEqual(sorted_clips[1].id, "clip_002")
    
    def test_get_clips_at_time(self):
        """Test finding clips at specific time."""
        self.timeline.add_clip(self.clip1)  # 0.0 - 10.0
        self.timeline.add_clip(self.clip2)  # 15.0 - 23.0
        
        # Time 5.0 should find clip1
        clips_at_5 = self.timeline.get_clips_at_time(5.0)
        self.assertEqual(len(clips_at_5), 1)
        self.assertEqual(clips_at_5[0].id, "clip_001")
        
        # Time 12.0 should find no clips (gap)
        clips_at_12 = self.timeline.get_clips_at_time(12.0)
        self.assertEqual(len(clips_at_12), 0)
        
        # Time 20.0 should find clip2
        clips_at_20 = self.timeline.get_clips_at_time(20.0)
        self.assertEqual(len(clips_at_20), 1)
        self.assertEqual(clips_at_20[0].id, "clip_002")
    
    def test_get_gaps(self):
        """Test finding gaps between clips."""
        self.timeline.add_clip(self.clip1)  # 0.0 - 10.0
        self.timeline.add_clip(self.clip2)  # 15.0 - 23.0
        
        gaps = self.timeline.get_gaps()
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0], (10.0, 15.0))
    
    def test_validate_empty_timeline(self):
        """Test validation of empty timeline."""
        is_valid, warnings = self.timeline.validate()
        self.assertFalse(is_valid)
        self.assertIn("no clips", warnings[0].lower())
    
    def test_timeline_to_dict(self):
        """Test converting timeline to dictionary."""
        self.timeline.add_clip(self.clip1)
        
        timeline_dict = self.timeline.to_dict()
        self.assertIsInstance(timeline_dict, dict)
        self.assertEqual(timeline_dict['name'], "Test Timeline")
        self.assertEqual(len(timeline_dict['clips']), 1)
    
    def test_timeline_from_dict(self):
        """Test creating timeline from dictionary."""
        data = {
            "version": "2.0",
            "name": "Loaded Timeline",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "clips": [
                {
                    'id': "clip_001",
                    'recording_file': "test.ppr",
                    'start_time': 0.0,
                    'duration': 10.0,
                    'trim_start': 0.0,
                    'trim_end': 0.0,
                    'speed_multiplier': 1.0,
                    'enabled': True,
                    'name': "Test",
                    'color': "#4CAF50",
                    'original_duration': 10.0
                }
            ],
            "metadata": {}
        }
        
        timeline = Timeline.from_dict(data)
        self.assertEqual(timeline.name, "Loaded Timeline")
        self.assertEqual(len(timeline.clips), 1)


class TestTimelineManager(unittest.TestCase):
    """Test TimelineManager functionality."""
    
    def setUp(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TimelineManager(timelines_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_timeline(self):
        """Test creating a new timeline."""
        timeline = self.manager.create_timeline("My Timeline")
        self.assertEqual(timeline.name, "My Timeline")
        self.assertEqual(len(timeline.clips), 0)
    
    def test_get_timeline_path(self):
        """Test getting timeline file path."""
        path = self.manager.get_timeline_path("Test Timeline")
        self.assertTrue(str(path).endswith(".ppt"))
        self.assertIn("Test Timeline", str(path))
    
    def test_list_timelines(self):
        """Test listing timeline files."""
        # Create some test timeline files
        timeline1 = self.manager.create_timeline("Timeline 1")
        timeline2 = self.manager.create_timeline("Timeline 2")
        
        save_timeline(timeline1, str(self.manager.get_timeline_path("Timeline 1")))
        save_timeline(timeline2, str(self.manager.get_timeline_path("Timeline 2")))
        
        timelines = self.manager.list_timelines()
        self.assertEqual(len(timelines), 2)
        self.assertIn("Timeline 1", timelines)
        self.assertIn("Timeline 2", timelines)


class TestFileHandling(unittest.TestCase):
    """Test file handling functions."""
    
    def setUp(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_timeline(self):
        """Test saving and loading timeline files."""
        # Create timeline
        timeline = Timeline(name="Save Test")
        clip = TimelineClip(
            id="clip_001",
            recording_file="test.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0,
            name="Test Clip"
        )
        timeline.add_clip(clip)
        
        # Save
        filepath = os.path.join(self.temp_dir, "test_timeline.ppt")
        success = save_timeline(timeline, filepath)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        
        # Load
        loaded_timeline = load_timeline(filepath)
        self.assertIsNotNone(loaded_timeline)
        self.assertEqual(loaded_timeline.name, "Save Test")
        self.assertEqual(len(loaded_timeline.clips), 1)
        self.assertEqual(loaded_timeline.clips[0].name, "Test Clip")
    
    def test_validate_timeline_file(self):
        """Test timeline file validation."""
        # Create valid timeline file
        timeline = Timeline(name="Valid Timeline")
        filepath = os.path.join(self.temp_dir, "valid.ppt")
        save_timeline(timeline, filepath)
        
        is_valid, errors = validate_timeline_file(filepath)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid file (doesn't exist)
        is_valid, errors = validate_timeline_file("nonexistent.ppt")
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_get_timeline_info(self):
        """Test getting timeline metadata."""
        timeline = Timeline(name="Info Test")
        clip = TimelineClip(
            id="clip_001",
            recording_file="test.ppr",
            start_time=0.0,
            duration=10.0,
            original_duration=10.0
        )
        timeline.add_clip(clip)
        
        filepath = os.path.join(self.temp_dir, "info_test.ppt")
        save_timeline(timeline, filepath)
        
        info = get_timeline_info(filepath)
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], "Info Test")
        self.assertEqual(info['clip_count'], 1)
        self.assertEqual(info['total_duration'], 10.0)
    
    def test_create_backup(self):
        """Test creating backup file."""
        timeline = Timeline(name="Backup Test")
        filepath = os.path.join(self.temp_dir, "backup_test.ppt")
        save_timeline(timeline, filepath)
        
        backup_path = create_backup(filepath)
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        self.assertIn("backup", backup_path)
    
    def test_list_timeline_files(self):
        """Test listing all timeline files in directory."""
        # Create multiple timeline files
        for i in range(3):
            timeline = Timeline(name=f"Timeline {i}")
            filepath = os.path.join(self.temp_dir, f"timeline_{i}.ppt")
            save_timeline(timeline, filepath)
        
        timelines = list_timeline_files(self.temp_dir)
        self.assertEqual(len(timelines), 3)


class TestClipColors(unittest.TestCase):
    """Test clip color functionality."""
    
    def test_get_clip_color(self):
        """Test getting predefined colors."""
        self.assertEqual(get_clip_color("pick"), CLIP_COLORS["pick"])
        self.assertEqual(get_clip_color("place"), CLIP_COLORS["place"])
        self.assertEqual(get_clip_color("move"), CLIP_COLORS["move"])
    
    def test_get_clip_color_case_insensitive(self):
        """Test that color lookup is case-insensitive."""
        self.assertEqual(get_clip_color("PICK"), CLIP_COLORS["pick"])
        self.assertEqual(get_clip_color("Place"), CLIP_COLORS["place"])
    
    def test_get_clip_color_unknown(self):
        """Test getting color for unknown operation."""
        color = get_clip_color("unknown_operation")
        self.assertEqual(color, CLIP_COLORS["custom"])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()

