"""
Timeline file handler for Piper Robot Automation System V2.

Handles reading and writing timeline files (.ppt format).
Timeline files are JSON-based and contain clip arrangements, trims, and metadata.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from timeline import Timeline, TimelineClip


# Configure logging
logger = logging.getLogger(__name__)


def save_timeline(timeline: Timeline, filepath: str) -> bool:
    """
    Save a timeline to a .ppt file.
    
    Args:
        timeline: Timeline instance to save
        filepath: Path to save the timeline file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Update modification timestamp
        timeline.modified = datetime.now()
        
        # Convert timeline to dictionary
        data = timeline.to_dict()
        
        # Ensure parent directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file with pretty formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved timeline '{timeline.name}' to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save timeline to {filepath}: {e}")
        return False


def load_timeline(filepath: str) -> Optional[Timeline]:
    """
    Load a timeline from a .ppt file.
    
    Args:
        filepath: Path to the timeline file
        
    Returns:
        Timeline instance if successful, None otherwise
    """
    try:
        if not Path(filepath).exists():
            logger.error(f"Timeline file not found: {filepath}")
            return None
        
        # Read JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate version
        version = data.get("version", "1.0")
        if not version.startswith("2."):
            logger.warning(f"Timeline file has version {version}, expected 2.x")
        
        # Create timeline from dictionary
        timeline = Timeline.from_dict(data)
        
        logger.info(f"Loaded timeline '{timeline.name}' from {filepath} ({len(timeline.clips)} clips)")
        return timeline
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in timeline file {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load timeline from {filepath}: {e}")
        return None


def validate_timeline_file(filepath: str) -> tuple[bool, list[str]]:
    """
    Validate a timeline file without fully loading it.
    
    Args:
        filepath: Path to the timeline file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check file exists
    if not Path(filepath).exists():
        errors.append(f"File not found: {filepath}")
        return False, errors
    
    # Check file extension
    if not filepath.endswith('.ppt'):
        errors.append("File must have .ppt extension")
    
    try:
        # Try to parse JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ["version", "name", "clips"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check version format
        if "version" in data:
            version = data["version"]
            if not isinstance(version, str):
                errors.append("Version must be a string")
        
        # Check clips structure
        if "clips" in data:
            if not isinstance(data["clips"], list):
                errors.append("Clips must be a list")
            else:
                for i, clip in enumerate(data["clips"]):
                    if not isinstance(clip, dict):
                        errors.append(f"Clip {i} must be a dictionary")
                        continue
                    
                    # Check required clip fields
                    required_clip_fields = ["id", "recording_file", "start_time", "duration"]
                    for field in required_clip_fields:
                        if field not in clip:
                            errors.append(f"Clip {i} missing required field: {field}")
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def export_timeline_as_recording(timeline: Timeline, output_filepath: str) -> bool:
    """
    Export a timeline as a single .ppr recording file.
    
    This "bakes" the timeline into a single recording with all trims,
    gaps, and speed adjustments applied.
    
    Args:
        timeline: Timeline to export
        output_filepath: Path for output .ppr file
        
    Returns:
        True if successful, False otherwise
        
    Note:
        This function will be fully implemented in Phase 6 (Timeline Playback)
        when we integrate with the playback engine. For now, it's a placeholder.
    """
    logger.warning("Timeline export to .ppr not yet implemented (Phase 6)")
    # TODO: Implement in Phase 6 - Timeline Playback
    # Will need to:
    # 1. Load each clip's recording data
    # 2. Apply trims
    # 3. Apply speed adjustments
    # 4. Insert gaps (hold positions)
    # 5. Concatenate all data
    # 6. Write as single .ppr file
    return False


def create_backup(filepath: str) -> Optional[str]:
    """
    Create a backup copy of a timeline file.
    
    Args:
        filepath: Path to timeline file
        
    Returns:
        Path to backup file if successful, None otherwise
    """
    try:
        path = Path(filepath)
        if not path.exists():
            logger.error(f"Cannot backup non-existent file: {filepath}")
            return None
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"
        
        # Copy file
        import shutil
        shutil.copy2(filepath, backup_path)
        
        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"Failed to create backup of {filepath}: {e}")
        return None


def get_timeline_info(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Get basic information about a timeline file without fully loading it.
    
    Args:
        filepath: Path to timeline file
        
    Returns:
        Dictionary with timeline info, or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract key information
        info = {
            "name": data.get("name", "Unknown"),
            "version": data.get("version", "Unknown"),
            "created": data.get("created", "Unknown"),
            "modified": data.get("modified", "Unknown"),
            "clip_count": len(data.get("clips", [])),
            "file_size": Path(filepath).stat().st_size,
            "filepath": filepath
        }
        
        # Calculate total duration
        clips = data.get("clips", [])
        if clips:
            max_end_time = max(
                clip.get("start_time", 0) + clip.get("duration", 0)
                for clip in clips
            )
            info["total_duration"] = max_end_time
        else:
            info["total_duration"] = 0.0
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get info for {filepath}: {e}")
        return None


def migrate_timeline_version(filepath: str, target_version: str = "2.0") -> bool:
    """
    Migrate a timeline file to a different version.
    
    Args:
        filepath: Path to timeline file
        target_version: Target version string
        
    Returns:
        True if successful, False otherwise
        
    Note:
        Currently only supports 2.0 format. Future versions may need migration logic.
    """
    try:
        timeline = load_timeline(filepath)
        if not timeline:
            return False
        
        # Create backup before migration
        backup_path = create_backup(filepath)
        if not backup_path:
            logger.error("Failed to create backup before migration")
            return False
        
        # Update version
        timeline.version = target_version
        
        # Save with new version
        success = save_timeline(timeline, filepath)
        
        if success:
            logger.info(f"Migrated timeline to version {target_version}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to migrate timeline: {e}")
        return False


def list_timeline_files(directory: str = "timelines") -> list[Dict[str, Any]]:
    """
    List all timeline files in a directory with their metadata.
    
    Args:
        directory: Directory to search for timeline files
        
    Returns:
        List of dictionaries with timeline information
    """
    timeline_dir = Path(directory)
    if not timeline_dir.exists():
        return []
    
    timelines = []
    for filepath in timeline_dir.glob("*.ppt"):
        info = get_timeline_info(str(filepath))
        if info:
            timelines.append(info)
    
    # Sort by modification date (newest first)
    timelines.sort(key=lambda x: x.get("modified", ""), reverse=True)
    
    return timelines


def delete_timeline_file(filepath: str, create_backup_first: bool = True) -> bool:
    """
    Delete a timeline file.
    
    Args:
        filepath: Path to timeline file
        create_backup_first: Whether to create a backup before deleting
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(filepath)
        if not path.exists():
            logger.error(f"Cannot delete non-existent file: {filepath}")
            return False
        
        # Create backup if requested
        if create_backup_first:
            backup_path = create_backup(filepath)
            if not backup_path:
                logger.warning("Failed to create backup, proceeding with deletion anyway")
        
        # Delete file
        path.unlink()
        logger.info(f"Deleted timeline file: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete timeline file {filepath}: {e}")
        return False


# Example timeline file structure for reference
EXAMPLE_TIMELINE = {
    "version": "2.0",
    "name": "Example Assembly Sequence",
    "created": "2025-12-02T14:30:00",
    "modified": "2025-12-02T15:45:00",
    "metadata": {
        "description": "Pick and place assembly operation",
        "author": "User",
        "robot": "Piper"
    },
    "clips": [
        {
            "id": "clip_001",
            "recording_file": "recordings/2025-12-01-143022.ppr",
            "start_time": 0.0,
            "duration": 10.5,
            "trim_start": 0.5,
            "trim_end": 0.2,
            "speed_multiplier": 1.0,
            "enabled": True,
            "name": "Pick Part A",
            "color": "#4CAF50",
            "original_duration": 11.2
        },
        {
            "id": "clip_002",
            "recording_file": "recordings/2025-12-01-143045.ppr",
            "start_time": 15.0,
            "duration": 8.0,
            "trim_start": 0.0,
            "trim_end": 0.0,
            "speed_multiplier": 1.5,
            "enabled": True,
            "name": "Place Part A",
            "color": "#2196F3",
            "original_duration": 8.0
        }
    ]
}

