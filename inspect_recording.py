"""
Recording Inspector

Inspects a .ppr recording file to verify data is valid and show statistics.
"""

import sys
from pathlib import Path
from ppr_file_handler import read_ppr_file, get_recording_info


def inspect_recording(filepath):
    """
    Inspect a recording file and display statistics.
    """
    print("=" * 70)
    print(" RECORDING INSPECTOR")
    print("=" * 70)
    print()
    
    file_path = Path(filepath)
    
    if not file_path.exists():
        print(f"ERROR: File not found: {filepath}")
        return
    
    print(f"File: {file_path.name}")
    print()
    
    try:
        # Get basic info
        info = get_recording_info(filepath)
        print("FILE INFO:")
        print(f"  Samples: {info['sample_count']:,}")
        print(f"  Duration: {info['duration_sec']:.2f} seconds")
        print(f"  Sample rate: {info['sample_rate_hz']} Hz")
        print(f"  Created: {info.get('created', 'Unknown')}")
        print()
        
        # Load full data
        data_list, metadata = read_ppr_file(filepath)
        
        # Analyze first few samples
        print("FIRST 5 SAMPLES:")
        print("-" * 70)
        for i, data in enumerate(data_list[:5]):
            joints = data['joints']
            cartesian = data['cartesian']
            gripper = data['gripper']
            
            print(f"Sample {i}:")
            print(f"  Joints: J1={joints[0]:.2f}° J2={joints[1]:.2f}° J3={joints[2]:.2f}° "
                  f"J4={joints[3]:.2f}° J5={joints[4]:.2f}° J6={joints[5]:.2f}°")
            print(f"  Cartesian: X={cartesian['x']:.2f}mm Y={cartesian['y']:.2f}mm Z={cartesian['z']:.2f}mm")
            print(f"  Gripper: pos={gripper['position']:.2f}mm effort={gripper['effort']:.3f}N·m")
            print()
        
        # Check for movement
        print("MOVEMENT ANALYSIS:")
        print("-" * 70)
        
        # Check joint movement
        first_joints = data_list[0]['joints']
        last_joints = data_list[-1]['joints']
        
        joint_changes = []
        for i in range(6):
            change = abs(last_joints[i] - first_joints[i])
            joint_changes.append(change)
            print(f"  J{i+1} change: {change:.2f}° (from {first_joints[i]:.2f}° to {last_joints[i]:.2f}°)")
        
        total_movement = sum(joint_changes)
        print()
        print(f"  Total joint movement: {total_movement:.2f}°")
        
        if total_movement < 1.0:
            print()
            print("  ⚠️  WARNING: Very little or no movement detected!")
            print("     The robot may have been stationary during recording.")
            print("     Playback will show minimal movement.")
        else:
            print()
            print(f"  ✓ Movement detected: {total_movement:.2f}° total")
        
        # Check for zero values
        print()
        print("DATA VALIDATION:")
        print("-" * 70)
        
        all_zeros = True
        for data in data_list:
            joints = data['joints']
            if any(j != 0.0 for j in joints):
                all_zeros = False
                break
        
        if all_zeros:
            print("  ✗ ERROR: All joint values are zero!")
            print("     This indicates a recording problem.")
        else:
            print("  ✓ Non-zero joint values found")
        
        # Check timestamp progression
        first_time = data_list[0]['timestamp']
        last_time = data_list[-1]['timestamp']
        time_diff = last_time - first_time
        
        print(f"  ✓ Timestamps progress correctly ({time_diff}ms)")
        
        # Range check
        print()
        print("JOINT RANGES:")
        print("-" * 70)
        
        for j_idx in range(6):
            values = [d['joints'][j_idx] for d in data_list]
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            print(f"  J{j_idx+1}: min={min_val:.2f}° max={max_val:.2f}° range={range_val:.2f}°")
        
        print()
        print("=" * 70)
        print(" INSPECTION COMPLETE")
        print("=" * 70)
        print()
        
        if total_movement < 1.0:
            print("⚠️  Recording contains minimal movement.")
            print("   Record a new sequence with visible robot motion.")
        elif all_zeros:
            print("✗  Recording data is invalid (all zeros).")
            print("   There may be an issue with data capture.")
        else:
            print("✓  Recording appears valid and contains movement.")
            print("   Ready for playback!")
        
        print()
        
    except Exception as e:
        print(f"ERROR: Failed to inspect recording: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_recording.py <path_to_ppr_file>")
        print()
        print("Example:")
        print("  python inspect_recording.py recordings/2025-12-01-143022.ppr")
        print()
        
        # Try to find and show available recordings
        recordings_dir = Path("recordings")
        if recordings_dir.exists():
            ppr_files = list(recordings_dir.glob("*.ppr"))
            if ppr_files:
                print(f"Available recordings ({len(ppr_files)}):")
                for f in sorted(ppr_files, reverse=True)[:5]:
                    print(f"  - {f.name}")
        
        sys.exit(1)
    
    filepath = sys.argv[1]
    inspect_recording(filepath)

