"""
Piper Program Recording (PPR) File Handler

Handles reading and writing of .ppr files in G-code-like format.
File format: t<epoch_ms> x<X> y<Y> z<Z> a<RX> b<RY> c<RZ> J6[j1,j2,j3,j4,j5,j6] Grp[pos,effort,code]
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# Constants
RECORDINGS_DIR = "recordings"
FILE_EXTENSION = ".ppr"
DEFAULT_METADATA = {
    "version": "1.0",
    "created_by": "Piper Automation System",
    "sample_rate_hz": 200
}


def create_ppr_filename() -> str:
    """
    Generate a PPR filename based on current datetime.
    
    Returns:
        Filename in format: YYYY-MM-DD-HHMMSS.ppr
    
    Example:
        "2025-12-01-213045.ppr"
    """
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d-%H%M%S") + FILE_EXTENSION
    return filename


def ensure_recordings_directory() -> Path:
    """
    Create the recordings directory if it doesn't exist.
    
    Returns:
        Path object pointing to the recordings directory
    """
    recordings_path = Path(RECORDINGS_DIR)
    recordings_path.mkdir(exist_ok=True)
    return recordings_path


def get_full_filepath(filename: str) -> Path:
    """
    Get the full path for a recording file.
    
    Args:
        filename: Name of the file (with or without .ppr extension)
    
    Returns:
        Full Path object to the file in the recordings directory
    """
    ensure_recordings_directory()
    
    # Add extension if not present
    if not filename.endswith(FILE_EXTENSION):
        filename += FILE_EXTENSION
    
    return Path(RECORDINGS_DIR) / filename


def write_ppr_header(file_handle, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Write header comments to the PPR file with metadata.
    
    Args:
        file_handle: Open file handle for writing
        metadata: Optional dictionary of metadata to include in header
    """
    meta = DEFAULT_METADATA.copy()
    if metadata:
        meta.update(metadata)
    
    file_handle.write("; Piper Program Recording (PPR) File\n")
    file_handle.write(f"; Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    file_handle.write(f"; Version: {meta.get('version', '1.0')}\n")
    file_handle.write(f"; Sample Rate: {meta.get('sample_rate_hz', 200)} Hz\n")
    
    if 'description' in meta:
        file_handle.write(f"; Description: {meta['description']}\n")
    
    file_handle.write(";\n")
    file_handle.write("; Format: t<epoch_ms> x<X> y<Y> z<Z> a<RX> b<RY> c<RZ> J6[j1,j2,j3,j4,j5,j6] Grp[pos,effort,code]\n")
    file_handle.write("; Units: position(mm), rotation(degrees), gripper_position(mm), gripper_effort(N*m)\n")
    file_handle.write(";\n")


def write_ppr_line(
    file_handle,
    timestamp: int,
    cartesian: Dict[str, float],
    joints: List[float],
    gripper: Dict[str, float]
) -> None:
    """
    Write a single data line to the PPR file.
    
    Args:
        file_handle: Open file handle for writing
        timestamp: Epoch timestamp in milliseconds
        cartesian: Dictionary with keys: x, y, z, a, b, c (mm and degrees)
        joints: List of 6 joint angles in degrees [j1, j2, j3, j4, j5, j6]
        gripper: Dictionary with keys: position, effort, code
    
    Example:
        cartesian = {'x': 150.523, 'y': -50.342, 'z': 180.0, 'a': -179.9, 'b': 0.0, 'c': -179.9}
        joints = [0.0, 45.0, -30.0, 0.0, 0.0, 0.0]
        gripper = {'position': 80.0, 'effort': 1.5, 'code': 1}
    """
    # Format cartesian coordinates
    x = cartesian.get('x', 0.0)
    y = cartesian.get('y', 0.0)
    z = cartesian.get('z', 0.0)
    a = cartesian.get('a', 0.0)
    b = cartesian.get('b', 0.0)
    c = cartesian.get('c', 0.0)
    
    # Format joint array
    j1, j2, j3, j4, j5, j6 = joints[0:6]
    
    # Format gripper data
    grp_pos = gripper.get('position', 0.0)
    grp_eff = gripper.get('effort', 0.0)
    grp_code = int(gripper.get('code', 0))
    
    # Write line in G-code-like format
    line = (
        f"t{timestamp} "
        f"x{x:.3f} y{y:.3f} z{z:.3f} "
        f"a{a:.3f} b{b:.3f} c{c:.3f} "
        f"J6[{j1:.3f},{j2:.3f},{j3:.3f},{j4:.3f},{j5:.3f},{j6:.3f}] "
        f"Grp[{grp_pos:.3f},{grp_eff:.3f},{grp_code}]\n"
    )
    
    file_handle.write(line)


def parse_ppr_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single line from a PPR file into a data dictionary.
    
    Args:
        line: String line from PPR file
    
    Returns:
        Dictionary with parsed data, or None if line is invalid/comment
    
    Example returned dict:
        {
            'timestamp': 1701453045123,
            'cartesian': {'x': 150.523, 'y': -50.342, 'z': 180.0, 'a': -179.9, 'b': 0.0, 'c': -179.9},
            'joints': [0.0, 45.0, -30.0, 0.0, 0.0, 0.0],
            'gripper': {'position': 80.0, 'effort': 1.5, 'code': 1}
        }
    """
    # Skip empty lines and comments
    line = line.strip()
    if not line or line.startswith(';'):
        return None
    
    try:
        # Parse timestamp
        timestamp_match = re.search(r't(\d+)', line)
        if not timestamp_match:
            return None
        timestamp = int(timestamp_match.group(1))
        
        # Parse cartesian coordinates
        x_match = re.search(r'x([-\d.]+)', line)
        y_match = re.search(r'y([-\d.]+)', line)
        z_match = re.search(r'z([-\d.]+)', line)
        a_match = re.search(r'a([-\d.]+)', line)
        b_match = re.search(r'b([-\d.]+)', line)
        c_match = re.search(r'c([-\d.]+)', line)
        
        cartesian = {
            'x': float(x_match.group(1)) if x_match else 0.0,
            'y': float(y_match.group(1)) if y_match else 0.0,
            'z': float(z_match.group(1)) if z_match else 0.0,
            'a': float(a_match.group(1)) if a_match else 0.0,
            'b': float(b_match.group(1)) if b_match else 0.0,
            'c': float(c_match.group(1)) if c_match else 0.0,
        }
        
        # Parse joint array J6[...]
        joint_match = re.search(r'J6\[([-\d.,]+)\]', line)
        if not joint_match:
            return None
        joint_values = joint_match.group(1).split(',')
        joints = [float(v) for v in joint_values[:6]]
        
        # Ensure we have exactly 6 joints
        while len(joints) < 6:
            joints.append(0.0)
        
        # Parse gripper array Grp[...]
        gripper_match = re.search(r'Grp\[([-\d.,]+)\]', line)
        if not gripper_match:
            return None
        gripper_values = gripper_match.group(1).split(',')
        
        gripper = {
            'position': float(gripper_values[0]) if len(gripper_values) > 0 else 0.0,
            'effort': float(gripper_values[1]) if len(gripper_values) > 1 else 0.0,
            'code': int(float(gripper_values[2])) if len(gripper_values) > 2 else 0,
        }
        
        return {
            'timestamp': timestamp,
            'cartesian': cartesian,
            'joints': joints,
            'gripper': gripper
        }
        
    except (ValueError, AttributeError, IndexError) as e:
        # Invalid line format
        return None


def read_ppr_file(filepath: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Read and parse a complete PPR file.
    
    Args:
        filepath: Path to the .ppr file
    
    Returns:
        Tuple of (data_list, metadata):
            - data_list: List of parsed data dictionaries (one per line)
            - metadata: Dictionary of metadata from header
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    file_path = Path(filepath)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Recording file not found: {filepath}")
    
    data_list = []
    metadata = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            # Parse header metadata
            if line.startswith(';'):
                # Extract metadata from comments
                if 'Version:' in line:
                    metadata['version'] = line.split('Version:')[1].strip()
                elif 'Sample Rate:' in line:
                    rate_str = line.split('Sample Rate:')[1].strip().split()[0]
                    metadata['sample_rate_hz'] = int(rate_str)
                elif 'Created:' in line:
                    metadata['created'] = line.split('Created:')[1].strip()
                elif 'Description:' in line:
                    metadata['description'] = line.split('Description:')[1].strip()
                continue
            
            # Parse data line
            parsed_data = parse_ppr_line(line)
            if parsed_data:
                data_list.append(parsed_data)
    
    if not data_list:
        raise ValueError(f"No valid data found in file: {filepath}")
    
    return data_list, metadata


def get_recording_info(filepath: str) -> Dict[str, Any]:
    """
    Get summary information about a recording file without loading all data.
    
    Args:
        filepath: Path to the .ppr file
    
    Returns:
        Dictionary with recording info: duration, sample_count, start_time, end_time, etc.
    """
    try:
        data_list, metadata = read_ppr_file(filepath)
        
        if not data_list:
            return {'error': 'No data in file'}
        
        start_timestamp = data_list[0]['timestamp']
        end_timestamp = data_list[-1]['timestamp']
        duration_ms = end_timestamp - start_timestamp
        duration_sec = duration_ms / 1000.0
        
        return {
            'filename': Path(filepath).name,
            'sample_count': len(data_list),
            'duration_sec': duration_sec,
            'duration_ms': duration_ms,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'sample_rate_hz': metadata.get('sample_rate_hz', 'Unknown'),
            'created': metadata.get('created', 'Unknown'),
            'version': metadata.get('version', '1.0'),
        }
    except Exception as e:
        return {'error': str(e)}


def list_recordings() -> List[str]:
    """
    List all available PPR recording files in the recordings directory.
    
    Returns:
        List of filenames (without path)
    """
    ensure_recordings_directory()
    recordings_path = Path(RECORDINGS_DIR)
    
    # Get all .ppr files
    ppr_files = sorted(recordings_path.glob(f"*{FILE_EXTENSION}"), reverse=True)
    
    return [f.name for f in ppr_files]


# Example usage and testing
if __name__ == "__main__":
    """
    Test the PPR file handler with sample data.
    """
    print("Testing PPR File Handler...")
    print("-" * 50)
    
    # Create sample data
    test_filename = create_ppr_filename()
    print(f"Generated filename: {test_filename}")
    
    # Write test file
    test_filepath = get_full_filepath("test_recording.ppr")
    print(f"Writing test file to: {test_filepath}")
    
    with open(test_filepath, 'w') as f:
        # Write header
        write_ppr_header(f, {"description": "Test recording"})
        
        # Write sample data points
        import time
        base_time = int(time.time() * 1000)
        
        for i in range(10):
            timestamp = base_time + (i * 5)  # 5ms intervals
            cartesian = {
                'x': 150.0 + i * 0.5,
                'y': -50.0,
                'z': 180.0,
                'a': -179.9,
                'b': 0.0,
                'c': -179.9
            }
            joints = [0.0, 45.0 + i, -30.0, 0.0, 0.0, 0.0]
            gripper = {'position': 80.0, 'effort': 1.5, 'code': 1}
            
            write_ppr_line(f, timestamp, cartesian, joints, gripper)
    
    print("Test file written successfully!")
    print()
    
    # Read test file
    print("Reading test file...")
    data_list, metadata = read_ppr_file(test_filepath)
    print(f"Loaded {len(data_list)} data points")
    print(f"Metadata: {metadata}")
    print()
    
    # Show first data point
    if data_list:
        print("First data point:")
        print(f"  Timestamp: {data_list[0]['timestamp']}")
        print(f"  Cartesian: {data_list[0]['cartesian']}")
        print(f"  Joints: {data_list[0]['joints']}")
        print(f"  Gripper: {data_list[0]['gripper']}")
    print()
    
    # Get recording info
    info = get_recording_info(test_filepath)
    print("Recording info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # List all recordings
    recordings = list_recordings()
    print(f"Available recordings ({len(recordings)}):")
    for recording in recordings[:5]:  # Show first 5
        print(f"  - {recording}")
    
    print("-" * 50)
    print("PPR File Handler test complete!")

