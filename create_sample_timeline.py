"""
Create sample timeline for testing and demonstration.

This script creates a sample timeline with multiple clips to demonstrate
the timeline system functionality.
"""

import os
from pathlib import Path
from timeline import Timeline, TimelineClip, TimelineManager, get_clip_color
from ppt_file_handler import save_timeline


def create_sample_timeline():
    """
    Create a sample timeline with multiple clips.
    
    Returns:
        Timeline instance
    """
    # Create timeline
    timeline = Timeline(name="Sample Assembly Sequence")
    timeline.metadata = {
        "description": "Example pick and place assembly operation",
        "author": "Demo User",
        "robot": "Piper",
        "workspace": "Assembly Station 1"
    }
    
    # Clip 1: Pick Part A
    clip1 = TimelineClip(
        id="clip_001",
        recording_file="recordings/pick_part_a.ppr",
        start_time=0.0,
        duration=9.8,
        trim_start=0.5,
        trim_end=0.2,
        speed_multiplier=1.0,
        enabled=True,
        name="Pick Part A",
        color=get_clip_color("pick"),
        original_duration=10.5
    )
    timeline.add_clip(clip1)
    
    # Gap: 5 seconds wait for sensor
    
    # Clip 2: Move to Assembly Station
    clip2 = TimelineClip(
        id="clip_002",
        recording_file="recordings/move_to_station.ppr",
        start_time=15.0,
        duration=5.5,
        trim_start=0.0,
        trim_end=0.0,
        speed_multiplier=2.0,  # Fast movement
        enabled=True,
        name="Move to Assembly Station",
        color=get_clip_color("move"),
        original_duration=5.5
    )
    timeline.add_clip(clip2)
    
    # Clip 3: Place Part A
    clip3 = TimelineClip(
        id="clip_003",
        recording_file="recordings/place_part_a.ppr",
        start_time=20.5,
        duration=8.0,
        trim_start=0.0,
        trim_end=0.0,
        speed_multiplier=0.5,  # Slow, precise placement
        enabled=True,
        name="Place Part A",
        color=get_clip_color("place"),
        original_duration=8.0
    )
    timeline.add_clip(clip3)
    
    # Clip 4: Return to Home
    clip4 = TimelineClip(
        id="clip_004",
        recording_file="recordings/return_home.ppr",
        start_time=28.5,
        duration=6.0,
        trim_start=0.0,
        trim_end=0.0,
        speed_multiplier=2.0,  # Fast return
        enabled=True,
        name="Return to Home",
        color=get_clip_color("home"),
        original_duration=6.0
    )
    timeline.add_clip(clip4)
    
    return timeline


def print_timeline_summary(timeline: Timeline):
    """
    Print a summary of the timeline.
    
    Args:
        timeline: Timeline to summarize
    """
    print(f"\n{'='*70}")
    print(f"Timeline: {timeline.name}")
    print(f"{'='*70}")
    print(f"Created: {timeline.created.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Duration: {timeline.total_duration:.1f} seconds")
    print(f"Number of Clips: {len(timeline.clips)}")
    print(f"\nMetadata:")
    for key, value in timeline.metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\n{'='*70}")
    print("Clips:")
    print(f"{'='*70}")
    
    for i, clip in enumerate(timeline.get_sorted_clips(), 1):
        print(f"\n{i}. {clip.name}")
        print(f"   ID: {clip.id}")
        print(f"   File: {clip.recording_file}")
        print(f"   Timeline Position: {clip.start_time:.1f}s - {clip.end_time:.1f}s")
        print(f"   Duration: {clip.duration:.1f}s (original: {clip.original_duration:.1f}s)")
        if clip.trim_start > 0 or clip.trim_end > 0:
            print(f"   Trim: start={clip.trim_start:.1f}s, end={clip.trim_end:.1f}s")
        print(f"   Speed: {clip.speed_multiplier}x")
        print(f"   Color: {clip.color}")
        print(f"   Enabled: {clip.enabled}")
    
    # Show gaps
    gaps = timeline.get_gaps()
    if gaps:
        print(f"\n{'='*70}")
        print("Gaps:")
        print(f"{'='*70}")
        for i, (start, end) in enumerate(gaps, 1):
            duration = end - start
            print(f"{i}. Gap: {start:.1f}s - {end:.1f}s (duration: {duration:.1f}s)")
    
    # Validate timeline
    is_valid, warnings = timeline.validate()
    if not is_valid:
        print(f"\n{'='*70}")
        print("Validation Warnings:")
        print(f"{'='*70}")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print(f"\n✅ Timeline validation passed!")
    
    print(f"\n{'='*70}\n")


def main():
    """Main function."""
    print("\n🎬 Creating Sample Timeline...")
    
    # Create sample timeline
    timeline = create_sample_timeline()
    
    # Print summary
    print_timeline_summary(timeline)
    
    # Save timeline
    manager = TimelineManager()
    filepath = manager.get_timeline_path(timeline.name)
    
    print(f"💾 Saving timeline to: {filepath}")
    success = save_timeline(timeline, str(filepath))
    
    if success:
        print(f"✅ Timeline saved successfully!")
        print(f"\nYou can load this timeline with:")
        print(f"  from ppt_file_handler import load_timeline")
        print(f"  timeline = load_timeline('{filepath}')")
    else:
        print(f"❌ Failed to save timeline")
    
    # Demonstrate timeline operations
    print(f"\n{'='*70}")
    print("Timeline Operations Demo:")
    print(f"{'='*70}")
    
    # Find clip at specific time
    time = 17.0
    clips_at_time = timeline.get_clips_at_time(time)
    print(f"\nAt {time}s:")
    if clips_at_time:
        for clip in clips_at_time:
            print(f"  • Playing: {clip.name}")
    else:
        print(f"  • In gap (no clip playing)")
    
    # Duplicate a clip
    print(f"\nDuplicating 'Pick Part A'...")
    duplicated = timeline.duplicate_clip("clip_001", offset=40.0)
    if duplicated:
        print(f"  ✅ Created: {duplicated.name} at {duplicated.start_time:.1f}s")
    
    # Update a clip trim
    print(f"\nUpdating trim for 'Place Part A'...")
    success = timeline.update_clip_trim("clip_003", trim_start=1.0, trim_end=0.5)
    if success:
        clip = timeline.get_clip_by_id("clip_003")
        print(f"  ✅ New duration: {clip.duration:.1f}s (was {clip.original_duration:.1f}s)")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()

