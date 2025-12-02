"""
Timeline management for Piper Robot Automation System V2.

This module provides data structures and operations for managing timelines,
which are compositions of multiple recording clips arranged sequentially.
"""

import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TimelineClip:
    """
    Represents a recording segment on the timeline.
    
    Attributes:
        id: Unique clip identifier
        recording_file: Path to the .ppr recording file
        start_time: Start time on timeline in seconds
        duration: Clip duration in seconds (after trimming)
        trim_start: Seconds to trim from beginning of recording
        trim_end: Seconds to trim from end of recording
        speed_multiplier: Playback speed for this clip (0.1 to 4.0)
        enabled: Whether this clip is active during playback
        name: Display name for the clip
        color: Hex color code for visual representation
        original_duration: Original recording duration before trimming
    """
    id: str
    recording_file: str
    start_time: float
    duration: float
    trim_start: float = 0.0
    trim_end: float = 0.0
    speed_multiplier: float = 1.0
    enabled: bool = True
    name: str = ""
    color: str = "#4CAF50"
    original_duration: float = 0.0
    
    def __post_init__(self):
        """Validate clip data after initialization."""
        if self.duration < 0:
            raise ValueError("Clip duration cannot be negative")
        if self.trim_start < 0:
            raise ValueError("Trim start cannot be negative")
        if self.trim_end < 0:
            raise ValueError("Trim end cannot be negative")
        if self.speed_multiplier < 0.1 or self.speed_multiplier > 4.0:
            raise ValueError("Speed multiplier must be between 0.1 and 4.0")
        if self.trim_start + self.trim_end > self.original_duration:
            raise ValueError("Total trim exceeds original duration")
    
    @property
    def end_time(self) -> float:
        """Calculate the end time of this clip on the timeline."""
        return self.start_time + self.duration
    
    @property
    def trimmed_duration(self) -> float:
        """Calculate duration after trimming."""
        return max(0, self.original_duration - self.trim_start - self.trim_end)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert clip to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineClip':
        """Create clip from dictionary."""
        return cls(**data)
    
    def __repr__(self) -> str:
        """String representation of clip."""
        return (f"TimelineClip(name='{self.name}', start={self.start_time:.1f}s, "
                f"duration={self.duration:.1f}s, speed={self.speed_multiplier}x)")


@dataclass
class Timeline:
    """
    Main timeline composition containing multiple clips.
    
    Attributes:
        name: Timeline project name
        clips: List of clips on the timeline
        created: Creation timestamp
        modified: Last modification timestamp
        version: Timeline format version
        metadata: Additional metadata (extensible)
    """
    name: str
    clips: List[TimelineClip] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    version: str = "2.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_duration(self) -> float:
        """
        Calculate total timeline duration (end of last clip).
        
        Returns:
            Total duration in seconds
        """
        if not self.clips:
            return 0.0
        return max(clip.end_time for clip in self.clips)
    
    @property
    def enabled_clips(self) -> List[TimelineClip]:
        """Get list of enabled clips only."""
        return [clip for clip in self.clips if clip.enabled]
    
    def get_clip_by_id(self, clip_id: str) -> Optional[TimelineClip]:
        """
        Find clip by ID.
        
        Args:
            clip_id: Clip identifier
            
        Returns:
            TimelineClip if found, None otherwise
        """
        for clip in self.clips:
            if clip.id == clip_id:
                return clip
        return None
    
    def get_clips_at_time(self, time: float) -> List[TimelineClip]:
        """
        Get all clips that are active at a specific time.
        
        Args:
            time: Time in seconds
            
        Returns:
            List of clips active at that time
        """
        active_clips = []
        for clip in self.enabled_clips:
            if clip.start_time <= time < clip.end_time:
                active_clips.append(clip)
        return active_clips
    
    def get_sorted_clips(self) -> List[TimelineClip]:
        """
        Get clips sorted by start time.
        
        Returns:
            List of clips in chronological order
        """
        return sorted(self.clips, key=lambda c: c.start_time)
    
    def add_clip(self, clip: TimelineClip) -> None:
        """
        Add a clip to the timeline.
        
        Args:
            clip: TimelineClip to add
        """
        self.clips.append(clip)
        self.modified = datetime.now()
        logger.info(f"Added clip '{clip.name}' to timeline '{self.name}'")
    
    def remove_clip(self, clip_id: str) -> bool:
        """
        Remove a clip from the timeline.
        
        Args:
            clip_id: ID of clip to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                removed_clip = self.clips.pop(i)
                self.modified = datetime.now()
                logger.info(f"Removed clip '{removed_clip.name}' from timeline '{self.name}'")
                return True
        return False
    
    def move_clip(self, clip_id: str, new_start_time: float) -> bool:
        """
        Move a clip to a new start time.
        
        Args:
            clip_id: ID of clip to move
            new_start_time: New start time in seconds
            
        Returns:
            True if moved, False if not found
        """
        clip = self.get_clip_by_id(clip_id)
        if clip:
            clip.start_time = max(0, new_start_time)  # Can't go before 0
            self.modified = datetime.now()
            logger.info(f"Moved clip '{clip.name}' to {new_start_time:.1f}s")
            return True
        return False
    
    def update_clip_trim(self, clip_id: str, trim_start: float, trim_end: float) -> bool:
        """
        Update trim values for a clip.
        
        Args:
            clip_id: ID of clip to update
            trim_start: New trim start value
            trim_end: New trim end value
            
        Returns:
            True if updated, False if not found or invalid
        """
        clip = self.get_clip_by_id(clip_id)
        if not clip:
            return False
        
        # Validate trim values
        if trim_start < 0 or trim_end < 0:
            logger.error("Trim values cannot be negative")
            return False
        
        if trim_start + trim_end > clip.original_duration:
            logger.error("Total trim exceeds original duration")
            return False
        
        clip.trim_start = trim_start
        clip.trim_end = trim_end
        clip.duration = clip.trimmed_duration
        self.modified = datetime.now()
        logger.info(f"Updated trim for clip '{clip.name}': start={trim_start:.2f}s, end={trim_end:.2f}s")
        return True
    
    def duplicate_clip(self, clip_id: str, offset: float = 0.0) -> Optional[TimelineClip]:
        """
        Duplicate a clip.
        
        Args:
            clip_id: ID of clip to duplicate
            offset: Time offset for duplicated clip (default: place after original)
            
        Returns:
            New TimelineClip if successful, None otherwise
        """
        original = self.get_clip_by_id(clip_id)
        if not original:
            return None
        
        # Create new clip with unique ID
        new_clip = TimelineClip(
            id=str(uuid.uuid4()),
            recording_file=original.recording_file,
            start_time=original.start_time + offset if offset else original.end_time + 1.0,
            duration=original.duration,
            trim_start=original.trim_start,
            trim_end=original.trim_end,
            speed_multiplier=original.speed_multiplier,
            enabled=original.enabled,
            name=f"{original.name} (copy)",
            color=original.color,
            original_duration=original.original_duration
        )
        
        self.add_clip(new_clip)
        logger.info(f"Duplicated clip '{original.name}'")
        return new_clip
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the timeline for potential issues.
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check for empty timeline
        if not self.clips:
            warnings.append("Timeline has no clips")
        
        # Check for overlapping clips
        sorted_clips = self.get_sorted_clips()
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            if current.end_time > next_clip.start_time:
                warnings.append(
                    f"Clips '{current.name}' and '{next_clip.name}' overlap "
                    f"({current.end_time:.1f}s > {next_clip.start_time:.1f}s)"
                )
        
        # Check for missing recording files
        for clip in self.clips:
            if not os.path.exists(clip.recording_file):
                warnings.append(f"Recording file not found for clip '{clip.name}': {clip.recording_file}")
        
        # Check for invalid durations
        for clip in self.clips:
            if clip.duration <= 0:
                warnings.append(f"Clip '{clip.name}' has invalid duration: {clip.duration:.2f}s")
        
        # Check for excessive trims
        for clip in self.clips:
            if clip.trim_start + clip.trim_end >= clip.original_duration:
                warnings.append(f"Clip '{clip.name}' is completely trimmed out")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    def get_gaps(self) -> List[tuple[float, float]]:
        """
        Find gaps between clips on the timeline.
        
        Returns:
            List of (gap_start, gap_end) tuples
        """
        gaps = []
        sorted_clips = self.get_sorted_clips()
        
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            
            if next_clip.start_time > current.end_time:
                gaps.append((current.end_time, next_clip.start_time))
        
        return gaps
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert timeline to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "name": self.name,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "clips": [clip.to_dict() for clip in self.clips],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Timeline':
        """
        Create timeline from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Timeline instance
        """
        clips = [TimelineClip.from_dict(clip_data) for clip_data in data.get("clips", [])]
        
        return cls(
            name=data.get("name", "Untitled Timeline"),
            clips=clips,
            created=datetime.fromisoformat(data.get("created", datetime.now().isoformat())),
            modified=datetime.fromisoformat(data.get("modified", datetime.now().isoformat())),
            version=data.get("version", "2.0"),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        """String representation of timeline."""
        return (f"Timeline(name='{self.name}', clips={len(self.clips)}, "
                f"duration={self.total_duration:.1f}s)")


class TimelineManager:
    """
    Manager for timeline operations and file handling.
    
    Provides high-level operations for creating, loading, and managing timelines.
    """
    
    def __init__(self, timelines_dir: str = "timelines"):
        """
        Initialize timeline manager.
        
        Args:
            timelines_dir: Directory for storing timeline files
        """
        self.timelines_dir = Path(timelines_dir)
        self.timelines_dir.mkdir(exist_ok=True)
        logger.info(f"TimelineManager initialized with directory: {self.timelines_dir}")
    
    def create_timeline(self, name: str) -> Timeline:
        """
        Create a new empty timeline.
        
        Args:
            name: Timeline name
            
        Returns:
            New Timeline instance
        """
        timeline = Timeline(name=name)
        logger.info(f"Created new timeline: '{name}'")
        return timeline
    
    def create_clip_from_recording(
        self,
        recording_file: str,
        start_time: float = 0.0,
        name: Optional[str] = None,
        color: str = "#4CAF50"
    ) -> TimelineClip:
        """
        Create a timeline clip from a recording file.
        
        Args:
            recording_file: Path to .ppr recording file
            start_time: Start time on timeline
            name: Clip name (defaults to filename)
            color: Clip color
            
        Returns:
            New TimelineClip instance
        """
        # Get recording metadata (duration, sample count, etc.)
        # For now, we'll estimate - later we'll read the actual .ppr file
        if not os.path.exists(recording_file):
            raise FileNotFoundError(f"Recording file not found: {recording_file}")
        
        # Estimate duration from file (will be refined when we load actual data)
        # For now, use a placeholder - this will be replaced with actual duration
        # when we integrate with ppr_file_handler
        duration = self._estimate_recording_duration(recording_file)
        
        if name is None:
            name = Path(recording_file).stem
        
        clip = TimelineClip(
            id=str(uuid.uuid4()),
            recording_file=recording_file,
            start_time=start_time,
            duration=duration,
            original_duration=duration,
            name=name,
            color=color
        )
        
        logger.info(f"Created clip '{name}' from recording: {recording_file}")
        return clip
    
    def _estimate_recording_duration(self, recording_file: str) -> float:
        """
        Estimate recording duration by reading the .ppr file.
        
        Args:
            recording_file: Path to .ppr file
            
        Returns:
            Estimated duration in seconds
        """
        try:
            # Import here to avoid circular dependency
            from ppr_file_handler import read_ppr_file
            
            data = read_ppr_file(recording_file)
            if not data or len(data) < 2:
                logger.warning(f"Recording has insufficient data: {recording_file}")
                return 0.0
            
            # Get first and last timestamps
            first_timestamp = data[0]['timestamp']
            last_timestamp = data[-1]['timestamp']
            
            # Calculate raw difference
            time_diff = last_timestamp - first_timestamp
            
            # Determine timestamp unit based on magnitude
            # If difference > 1000, likely milliseconds or microseconds
            # If difference < 100, likely seconds
            if time_diff > 100000:
                # Likely microseconds (time.time() * 1000000)
                duration = time_diff / 1_000_000.0
            elif time_diff > 1000:
                # Likely milliseconds (time.time() * 1000)
                duration = time_diff / 1000.0
            else:
                # Likely seconds
                duration = time_diff
            
            logger.info(f"Recording duration: {duration:.2f}s ({len(data)} samples, time_diff={time_diff})")
            return duration
            
        except Exception as e:
            logger.warning(f"Could not read recording duration from {recording_file}: {e}")
            # Return a default duration if we can't read the file
            return 10.0
    
    def get_timeline_path(self, timeline_name: str) -> Path:
        """
        Get file path for a timeline.
        
        Args:
            timeline_name: Timeline name
            
        Returns:
            Path to timeline file
        """
        # Sanitize filename
        safe_name = "".join(c for c in timeline_name if c.isalnum() or c in (' ', '-', '_')).strip()
        return self.timelines_dir / f"{safe_name}.ppt"
    
    def list_timelines(self) -> List[str]:
        """
        List all saved timeline files.
        
        Returns:
            List of timeline names
        """
        timeline_files = list(self.timelines_dir.glob("*.ppt"))
        return [f.stem for f in timeline_files]
    
    def timeline_exists(self, timeline_name: str) -> bool:
        """
        Check if a timeline file exists.
        
        Args:
            timeline_name: Timeline name
            
        Returns:
            True if exists, False otherwise
        """
        return self.get_timeline_path(timeline_name).exists()


# Predefined color palette for clips
CLIP_COLORS = {
    "pick": "#4CAF50",      # Green
    "place": "#2196F3",     # Blue
    "move": "#FF9800",      # Orange
    "home": "#F44336",      # Red
    "inspect": "#9C27B0",   # Purple
    "wait": "#607D8B",      # Gray
    "custom": "#00BCD4"     # Cyan
}


def get_clip_color(operation_type: str) -> str:
    """
    Get color for a clip based on operation type.
    
    Args:
        operation_type: Type of operation (pick, place, move, etc.)
        
    Returns:
        Hex color code
    """
    return CLIP_COLORS.get(operation_type.lower(), CLIP_COLORS["custom"])

