"""
Clip editing operations for Piper Robot Automation System V2.

This module provides functions for editing timeline clips, including trimming,
speed adjustment, and preview functionality.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from timeline import TimelineClip, Timeline
from ppr_file_handler import read_ppr_file


# Configure logging
logger = logging.getLogger(__name__)


class ClipEditor:
    """
    Handles clip editing operations including trimming and preview.
    
    Provides methods to apply trims, preview changes, and validate edits
    before committing them to the timeline.
    """
    
    def __init__(self, clip: TimelineClip):
        """
        Initialize clip editor.
        
        Args:
            clip: TimelineClip to edit
        """
        self.clip = clip
        self._cached_data = None
        self._cached_filepath = None
    
    def get_recording_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load recording data from the clip's source file.
        
        Returns:
            List of recording data points, or None if error
        """
        # Use cached data if available and filepath hasn't changed
        if self._cached_data and self._cached_filepath == self.clip.recording_file:
            return self._cached_data
        
        try:
            if not Path(self.clip.recording_file).exists():
                logger.error(f"Recording file not found: {self.clip.recording_file}")
                return None
            
            # read_ppr_file returns (data, metadata) tuple
            data, metadata = read_ppr_file(self.clip.recording_file)
            self._cached_data = data
            self._cached_filepath = self.clip.recording_file
            return data
            
        except Exception as e:
            logger.error(f"Failed to load recording data: {e}")
            return None
    
    def get_trimmed_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get recording data with trims applied.
        
        Returns:
            Trimmed recording data, or None if error
        """
        data = self.get_recording_data()
        if not data:
            return None
        
        return apply_trim_to_data(
            data,
            self.clip.trim_start,
            self.clip.trim_end
        )
    
    def preview_trim(self, trim_start: float, trim_end: float) -> Dict[str, Any]:
        """
        Preview the effect of trim values without applying them.
        
        Args:
            trim_start: Proposed trim from start (seconds)
            trim_end: Proposed trim from end (seconds)
            
        Returns:
            Dictionary with preview information
        """
        data = self.get_recording_data()
        
        preview = {
            "original_duration": self.clip.original_duration,
            "current_duration": self.clip.duration,
            "new_duration": max(0, self.clip.original_duration - trim_start - trim_end),
            "trim_start": trim_start,
            "trim_end": trim_end,
            "valid": True,
            "warnings": []
        }
        
        # Validate trim values
        if trim_start < 0:
            preview["valid"] = False
            preview["warnings"].append("Trim start cannot be negative")
        
        if trim_end < 0:
            preview["valid"] = False
            preview["warnings"].append("Trim end cannot be negative")
        
        if trim_start + trim_end > self.clip.original_duration:
            preview["valid"] = False
            preview["warnings"].append("Total trim exceeds clip duration")
        
        if trim_start + trim_end == self.clip.original_duration:
            preview["warnings"].append("Clip will be completely trimmed (duration = 0)")
        
        # Add sample counts if data available
        if data:
            preview["original_samples"] = len(data)
            trimmed_data = apply_trim_to_data(data, trim_start, trim_end)
            preview["new_samples"] = len(trimmed_data)
            preview["samples_removed"] = len(data) - len(trimmed_data)
        
        return preview
    
    def apply_trim(self, trim_start: float, trim_end: float) -> bool:
        """
        Apply trim values to the clip.
        
        Args:
            trim_start: Trim from start (seconds)
            trim_end: Trim from end (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        # Validate first
        preview = self.preview_trim(trim_start, trim_end)
        if not preview["valid"]:
            logger.error(f"Invalid trim values: {preview['warnings']}")
            return False
        
        # Apply trim
        self.clip.trim_start = trim_start
        self.clip.trim_end = trim_end
        self.clip.duration = preview["new_duration"]
        
        logger.info(f"Applied trim to clip '{self.clip.name}': start={trim_start:.2f}s, end={trim_end:.2f}s")
        return True
    
    def reset_trim(self) -> None:
        """Reset all trims to original values."""
        self.clip.trim_start = 0.0
        self.clip.trim_end = 0.0
        self.clip.duration = self.clip.original_duration
        logger.info(f"Reset trim for clip '{self.clip.name}'")
    
    def apply_speed(self, speed_multiplier: float) -> bool:
        """
        Apply speed multiplier to the clip.
        
        Args:
            speed_multiplier: Speed (0.1 to 4.0)
            
        Returns:
            True if successful, False otherwise
        """
        if speed_multiplier < 0.1 or speed_multiplier > 4.0:
            logger.error(f"Invalid speed multiplier: {speed_multiplier}")
            return False
        
        self.clip.speed_multiplier = speed_multiplier
        logger.info(f"Applied speed {speed_multiplier}x to clip '{self.clip.name}'")
        return True
    
    def get_clip_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the clip.
        
        Returns:
            Dictionary with clip statistics
        """
        data = self.get_recording_data()
        
        stats = {
            "name": self.clip.name,
            "recording_file": self.clip.recording_file,
            "original_duration": self.clip.original_duration,
            "current_duration": self.clip.duration,
            "trim_start": self.clip.trim_start,
            "trim_end": self.clip.trim_end,
            "speed_multiplier": self.clip.speed_multiplier,
            "trimmed_percentage": 0.0,
            "samples": 0,
            "sample_rate": 0.0
        }
        
        if self.clip.original_duration > 0:
            trimmed_duration = self.clip.trim_start + self.clip.trim_end
            stats["trimmed_percentage"] = (trimmed_duration / self.clip.original_duration) * 100
        
        if data:
            stats["samples"] = len(data)
            if self.clip.original_duration > 0:
                stats["sample_rate"] = len(data) / self.clip.original_duration
        
        return stats


def apply_trim_to_data(
    data: List[Dict[str, Any]],
    trim_start: float,
    trim_end: float
) -> List[Dict[str, Any]]:
    """
    Apply trim to recording data.
    
    Args:
        data: Recording data points
        trim_start: Seconds to trim from start
        trim_end: Seconds to trim from end
        
    Returns:
        Trimmed data list
    """
    if not data or (trim_start == 0 and trim_end == 0):
        return data
    
    # Get timestamp range
    first_timestamp = data[0]['timestamp']
    last_timestamp = data[-1]['timestamp']
    time_diff = last_timestamp - first_timestamp
    
    # Determine timestamp unit and calculate multiplier
    if time_diff > 100000:
        # Microseconds
        time_multiplier = 1_000_000.0
    elif time_diff > 1000:
        # Milliseconds
        time_multiplier = 1000.0
    else:
        # Seconds
        time_multiplier = 1.0
    
    # Calculate trim amounts in timestamp units
    trim_start_units = trim_start * time_multiplier
    trim_end_units = trim_end * time_multiplier
    
    start_timestamp = first_timestamp + trim_start_units
    end_timestamp = last_timestamp - trim_end_units
    
    # Filter data
    trimmed_data = [
        point for point in data
        if start_timestamp <= point['timestamp'] <= end_timestamp
    ]
    
    return trimmed_data


def validate_trim_values(
    original_duration: float,
    trim_start: float,
    trim_end: float
) -> Tuple[bool, List[str]]:
    """
    Validate trim values.
    
    Args:
        original_duration: Original clip duration
        trim_start: Proposed trim start
        trim_end: Proposed trim end
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if trim_start < 0:
        errors.append("Trim start cannot be negative")
    
    if trim_end < 0:
        errors.append("Trim end cannot be negative")
    
    if trim_start + trim_end > original_duration:
        errors.append(f"Total trim ({trim_start + trim_end:.2f}s) exceeds duration ({original_duration:.2f}s)")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def calculate_trim_percentage(
    original_duration: float,
    trim_start: float,
    trim_end: float
) -> float:
    """
    Calculate percentage of clip that will be trimmed.
    
    Args:
        original_duration: Original duration
        trim_start: Trim from start
        trim_end: Trim from end
        
    Returns:
        Percentage trimmed (0-100)
    """
    if original_duration <= 0:
        return 0.0
    
    total_trim = trim_start + trim_end
    percentage = (total_trim / original_duration) * 100
    return min(100.0, max(0.0, percentage))


def suggest_trim_values(
    data: List[Dict[str, Any]],
    remove_first_n_samples: int = 0,
    remove_last_n_samples: int = 0
) -> Tuple[float, float]:
    """
    Suggest trim values based on sample counts.
    
    Args:
        data: Recording data
        remove_first_n_samples: Number of samples to remove from start
        remove_last_n_samples: Number of samples to remove from end
        
    Returns:
        Tuple of (trim_start, trim_end) in seconds
    """
    if not data or len(data) <= 1:
        return 0.0, 0.0
    
    # Calculate time per sample
    first_timestamp = data[0]['timestamp']
    last_timestamp = data[-1]['timestamp']
    time_diff = last_timestamp - first_timestamp
    total_samples = len(data)
    
    # Determine timestamp unit
    if time_diff > 100000:
        # Microseconds
        time_per_sample = time_diff / (total_samples - 1) / 1_000_000.0
    elif time_diff > 1000:
        # Milliseconds
        time_per_sample = time_diff / (total_samples - 1) / 1000.0
    else:
        # Seconds
        time_per_sample = time_diff / (total_samples - 1)
    
    # Calculate trim values in seconds
    trim_start = remove_first_n_samples * time_per_sample
    trim_end = remove_last_n_samples * time_per_sample
    
    return trim_start, trim_end


def find_steady_state_trim(
    data: List[Dict[str, Any]],
    joint_tolerance: float = 0.5,
    window_size: int = 10
) -> Tuple[float, float]:
    """
    Automatically suggest trim values to remove non-steady-state portions.
    
    This finds the first and last points where the robot reaches a steady state,
    useful for trimming out startup/shutdown transients.
    
    Args:
        data: Recording data
        joint_tolerance: Maximum joint angle change (degrees) for steady state
        window_size: Number of samples to check for steady state
        
    Returns:
        Tuple of (trim_start, trim_end) in seconds
    """
    if not data or len(data) < window_size * 2:
        return 0.0, 0.0
    
    def is_steady_state(samples: List[Dict[str, Any]]) -> bool:
        """Check if a sequence of samples is in steady state."""
        if len(samples) < 2:
            return False
        
        # Check each joint angle
        for i in range(6):
            joint_key = f'joint_{i+1}'
            angles = [s['joint_angles'][joint_key] for s in samples if 'joint_angles' in s]
            
            if not angles:
                continue
            
            # Check if angles vary within tolerance
            max_angle = max(angles)
            min_angle = min(angles)
            if max_angle - min_angle > joint_tolerance:
                return False
        
        return True
    
    # Find steady state at start
    trim_start_samples = 0
    for i in range(len(data) - window_size):
        window = data[i:i+window_size]
        if is_steady_state(window):
            trim_start_samples = i
            break
    
    # Find steady state at end (search backwards)
    trim_end_samples = 0
    for i in range(len(data) - 1, window_size - 1, -1):
        window = data[i-window_size+1:i+1]
        if is_steady_state(window):
            trim_end_samples = len(data) - i - 1
            break
    
    # Convert to time
    trim_start, trim_end = suggest_trim_values(data, trim_start_samples, trim_end_samples)
    
    logger.info(f"Auto-trim suggestion: start={trim_start:.2f}s ({trim_start_samples} samples), "
                f"end={trim_end:.2f}s ({trim_end_samples} samples)")
    
    return trim_start, trim_end


def get_trim_positions(
    data: List[Dict[str, Any]],
    trim_start: float,
    trim_end: float
) -> Dict[str, Any]:
    """
    Get the robot positions at trim boundaries.
    
    Useful for showing where trims will occur.
    
    Args:
        data: Recording data
        trim_start: Trim from start (seconds)
        trim_end: Trim from end (seconds)
        
    Returns:
        Dictionary with position information
    """
    if not data:
        return {}
    
    # Calculate trim timestamps
    first_timestamp = data[0]['timestamp']
    last_timestamp = data[-1]['timestamp']
    
    trim_start_timestamp = first_timestamp + (trim_start * 1000)
    trim_end_timestamp = last_timestamp - (trim_end * 1000)
    
    # Find closest samples to trim points
    start_sample = None
    end_sample = None
    
    for sample in data:
        if start_sample is None and sample['timestamp'] >= trim_start_timestamp:
            start_sample = sample
        if sample['timestamp'] <= trim_end_timestamp:
            end_sample = sample
    
    result = {
        "trim_start_timestamp": trim_start_timestamp,
        "trim_end_timestamp": trim_end_timestamp,
        "start_position": start_sample,
        "end_position": end_sample
    }
    
    return result


# Utility functions for UI integration

def format_trim_display(trim_seconds: float) -> str:
    """
    Format trim value for display.
    
    Args:
        trim_seconds: Trim value in seconds
        
    Returns:
        Formatted string (e.g., "1.5s" or "500ms")
    """
    if trim_seconds >= 1.0:
        return f"{trim_seconds:.2f}s"
    else:
        return f"{int(trim_seconds * 1000)}ms"


def parse_trim_input(trim_string: str) -> Optional[float]:
    """
    Parse trim value from user input string.
    
    Args:
        trim_string: Input string (e.g., "1.5s", "500ms", "1.5")
        
    Returns:
        Trim value in seconds, or None if invalid
    """
    try:
        trim_string = trim_string.strip().lower()
        
        if trim_string.endswith('ms'):
            # Milliseconds
            value = float(trim_string[:-2])
            return value / 1000.0
        elif trim_string.endswith('s'):
            # Seconds
            return float(trim_string[:-1])
        else:
            # Assume seconds
            return float(trim_string)
    except ValueError:
        return None


def get_trim_slider_range(duration: float, max_trim_percentage: float = 50.0) -> Tuple[float, float]:
    """
    Calculate appropriate slider range for trim controls.
    
    Args:
        duration: Clip duration
        max_trim_percentage: Maximum percentage of clip that can be trimmed
        
    Returns:
        Tuple of (min_value, max_value) for slider
    """
    max_trim = (duration * max_trim_percentage) / 100.0
    return (0.0, max_trim)

