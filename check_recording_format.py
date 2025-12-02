"""
Diagnostic script to check recording timestamps and duration.

This script reads a .ppr file and analyzes the timestamp format.
"""

import sys
from pathlib import Path
from ppr_file_handler import read_ppr_file


def analyze_recording(filepath: str):
    """Analyze a recording file."""
    print(f"\n{'='*70}")
    print(f"Analyzing: {filepath}")
    print(f"{'='*70}\n")
    
    try:
        data, metadata = read_ppr_file(filepath)
        
        if not data:
            print("❌ No data in file")
            return
        
        print(f"✅ Loaded {len(data)} data points\n")
        
        # Get timestamps
        first_ts = data[0]['timestamp']
        last_ts = data[-1]['timestamp']
        time_diff = last_ts - first_ts
        
        print(f"Timestamp Analysis:")
        print(f"  First timestamp: {first_ts}")
        print(f"  Last timestamp:  {last_ts}")
        print(f"  Difference:      {time_diff}")
        print()
        
        # Try different interpretations
        print(f"Duration Interpretations:")
        print(f"  As seconds:      {time_diff:.2f}s")
        print(f"  As milliseconds: {time_diff/1000:.2f}s")
        print(f"  As microseconds: {time_diff/1_000_000:.2f}s")
        print()
        
        # Determine most likely
        if time_diff < 100:
            likely_unit = "seconds"
            duration = time_diff
        elif time_diff < 100000:
            likely_unit = "milliseconds"
            duration = time_diff / 1000.0
        else:
            likely_unit = "microseconds"
            duration = time_diff / 1_000_000.0
        
        print(f"✅ Most likely: {likely_unit}")
        print(f"✅ Duration: {duration:.2f} seconds")
        print()
        
        # Sample rate
        sample_rate = len(data) / duration
        print(f"Sample rate: {sample_rate:.1f} Hz")
        print()
        
        # Show first few lines
        print(f"First 3 data points:")
        for i in range(min(3, len(data))):
            point = data[i]
            print(f"  {i+1}. t{point['timestamp']}")
            if 'joint_angles' in point:
                joints = point['joint_angles']
                print(f"     Joints: {list(joints.values())[:3]}...")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Analyze specified file
        analyze_recording(sys.argv[1])
    else:
        # Find and analyze recordings
        recordings_dir = Path("recordings")
        
        if not recordings_dir.exists():
            print("❌ recordings/ directory not found")
            print("\nUsage: python check_recording_format.py <recording.ppr>")
            sys.exit(1)
        
        recording_files = list(recordings_dir.glob("*.ppr"))
        
        if not recording_files:
            print("❌ No .ppr files found in recordings/")
            print("\nRecord something first using the V1 tab")
            sys.exit(1)
        
        print(f"\nFound {len(recording_files)} recording(s)")
        print("\nAnalyzing most recent recording...\n")
        
        # Analyze most recent
        most_recent = max(recording_files, key=lambda p: p.stat().st_mtime)
        analyze_recording(str(most_recent))

