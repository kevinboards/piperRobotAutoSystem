# Piper Automation System - Quick Start Guide

## Overview
The Piper Automation System allows you to record and replay robot movements with high precision. The system captures joint angles, Cartesian positions, and gripper states at 200 Hz and stores them in an easy-to-read G-code-like format.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Piper Robot SDK installed (`pip install piper_sdk`)
- CAN bus interface configured (see SDK documentation)
- Piper robot connected and powered

### Setup
No installation required! All files are in the `PiperAutomationSystem` directory.

---

## File Structure

```
PiperAutomationSystem/
├── main.py                     # Main GUI application
├── recorder.py                 # Recording module
├── player.py                   # Playback module
├── ppr_file_handler.py         # File I/O operations
├── recordings/                 # Saved recordings directory
│   └── *.ppr files
├── test_system.py              # Test suite
├── Available Tools.md          # SDK reference guide
├── IMPLEMENTATION_PLAN.md      # Detailed implementation plan
├── QUICKSTART.md               # This file
└── README.md                   # Project overview
```

---

## Quick Start

### First-Time Setup (Important!)

**If this is your first time using the gripper**, run the setup script once:

```bash
python setup_gripper_first_time.py
```

This configures the gripper parameters. You only need to do this:
- Once per robot
- After replacing the gripper
- After factory reset

---

### Method 1: GUI Application (Recommended)

1. **Launch the application:**
   ```bash
   cd PiperAutomationSystem
   python main.py
   ```

2. **Record a movement:**
   - Click the **"Record"** button
   - Move the robot (manually in MIT mode or via programmed sequence)
   - Click **"Stop Recording"** when done
   - File is automatically saved with datetime stamp

3. **Play back a recording:**
   - Click **"Load New File"** to select a recording (or it auto-loads after recording)
   - Adjust playback speed with the slider (0.5x to 2.0x)
   - Click **"Play"** to start playback
   - Click **"Stop Playback"** to stop early (if needed)

### Method 2: Programmatic Usage

#### Recording Example:
```python
from piper_sdk import C_PiperInterface_V2
from recorder import PiperRecorder
import time

# Connect to robot
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Create recorder
recorder = PiperRecorder(piper, sample_rate=200)

# Start recording
filepath = recorder.start_recording(description="Test recording")
print(f"Recording to: {filepath}")

# Record for 10 seconds (robot can be moved during this time)
time.sleep(10.0)

# Stop and get stats
stats = recorder.stop_recording()
print(f"Recorded {stats['sample_count']} samples")
print(f"Duration: {stats['duration_sec']:.2f} seconds")
```

#### Playback Example:
```python
from piper_sdk import C_PiperInterface_V2
from player import PiperPlayer

# Connect to robot
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable robot
while not piper.EnablePiper():
    time.sleep(0.01)

# Create player and load file
player = PiperPlayer(piper)
info = player.load_recording("recordings/2025-12-01-143022.ppr")
print(f"Loaded {info['sample_count']} samples")

# Start playback
player.start_playback(speed_multiplier=1.0)

# Wait for completion
while player.is_playing():
    print(f"Progress: {player.get_progress():.1f}%")
    time.sleep(0.5)

print("Playback complete!")
```

---

## Testing

### Run the test suite:
```bash
python test_system.py
```

The test suite includes:
1. File handler functionality tests
2. Recorder tests (with mock data)
3. Player tests (with mock data)
4. Optional full cycle test with real robot

---

## File Format (.ppr)

### Example File:
```
; Piper Program Recording (PPR) File
; Created: 2025-12-01 14:30:22
; Version: 1.0
; Sample Rate: 200 Hz
;
; Format: t<epoch_ms> x<X> y<Y> z<Z> a<RX> b<RY> c<RZ> J6[j1,j2,j3,j4,j5,j6] Grp[pos,effort,code]
; Units: position(mm), rotation(degrees), gripper_position(mm), gripper_effort(N*m)
;
t1701453045123 x150.523 y-50.342 z180.000 a-179.900 b0.000 c-179.900 J6[0.000,45.000,-30.000,0.000,0.000,0.000] Grp[80.000,1.500,1]
t1701453045128 x150.528 y-50.342 z180.005 a-179.900 b0.000 c-179.900 J6[0.000,45.100,-30.000,0.000,0.000,0.000] Grp[80.000,1.500,1]
...
```

### Field Definitions:
- **t**: Timestamp in epoch milliseconds
- **x, y, z**: Cartesian position in mm
- **a, b, c**: Orientation (RX, RY, RZ) in degrees
- **J6[...]**: Joint angles [J1, J2, J3, J4, J5, J6] in degrees
- **Grp[...]**: Gripper [position(mm), effort(N·m), status_code]

---

## Tips & Best Practices

### For Recording:
1. **Enable MIT Mode** for manual teaching:
   ```python
   piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, 
                     move_spd_rate_ctrl=100, is_mit_mode=0xAD)
   ```
   This makes the robot easier to move by hand.

2. **Sample Rate**: Default is 200 Hz (5ms intervals). Adjust based on your needs:
   - 50-100 Hz: Slow, smooth movements
   - 200 Hz: Fast, precise movements (default)

3. **File Size**: ~40 KB/second at 200 Hz, ~2.4 MB/minute

### For Playback:
1. **Speed Control**: 
   - Start with 0.5x speed for testing
   - Use 1.0x for normal playback
   - Up to 2.0x for faster replay

2. **Safety**:
   - Always verify workspace is clear before playback
   - Use emergency stop if needed
   - Start with short recordings to test

3. **Enable Robot**: Always enable the robot before playback:
   ```python
   while not piper.EnablePiper():
       time.sleep(0.01)
   ```

---

## Troubleshooting

### Robot not connecting:
- Check CAN bus is configured (`ifconfig` on Linux, check device manager on Windows)
- Verify robot is powered on
- Check CAN cable connections
- Try restarting the robot

### Recording fails:
- Ensure robot is connected before starting
- Check disk space (recordings can be large)
- Verify write permissions in `recordings/` directory

### Playback doesn't match recording:
- Check playback speed (should be 1.0x for accurate replay)
- Verify robot is enabled
- Ensure robot starts from similar position as recording
- Check for joint limit warnings in logs

### "Gripper effort out of range" errors:
- **Fixed in latest version!** The system now handles negative gripper values automatically
- If using older recordings, the system will clamp values to valid range (0-5000)
- No action needed - system handles this internally

### GUI not responding:
- Recording and playback run in separate threads
- Check terminal/console for error messages
- Restart application if needed

---

## Advanced Usage

### Custom Sample Rate:
```python
recorder = PiperRecorder(piper, sample_rate=100)  # 100 Hz instead of 200 Hz
```

### Manual File Parsing:
```python
from ppr_file_handler import read_ppr_file, parse_ppr_line

# Read entire file
data_list, metadata = read_ppr_file("recordings/myfile.ppr")

# Or parse line by line
with open("recordings/myfile.ppr", 'r') as f:
    for line in f:
        data = parse_ppr_line(line)
        if data:
            print(f"Timestamp: {data['timestamp']}")
            print(f"Joints: {data['joints']}")
```

### Get Recording Info Without Loading:
```python
from ppr_file_handler import get_recording_info

info = get_recording_info("recordings/myfile.ppr")
print(f"Duration: {info['duration_sec']} seconds")
print(f"Samples: {info['sample_count']}")
```

---

## Support & Documentation

- **SDK Reference**: See `Available Tools.md` for complete SDK documentation
- **Implementation Details**: See `IMPLEMENTATION_PLAN.md` for system architecture
- **Piper SDK Docs**: Check `piper_sdk/` directory for official SDK documentation

---

## Examples

### Example 1: Record Manual Teaching
```python
from piper_sdk import C_PiperInterface_V2
from recorder import PiperRecorder
import time

piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable MIT mode for easy manual movement
piper.MotionCtrl_2(0x01, 0x01, 100, 0xAD)

print("Robot in MIT mode - move it manually!")
print("Recording will start in 3 seconds...")
time.sleep(3)

recorder = PiperRecorder(piper)
filepath = recorder.start_recording(description="Manual teaching")

print("Recording... Move the robot!")
time.sleep(30)  # Record for 30 seconds

stats = recorder.stop_recording()
print(f"Saved to: {stats['filename']}")
```

### Example 2: Loop Playback
```python
from piper_sdk import C_PiperInterface_V2
from player import PiperPlayer
import time

piper = C_PiperInterface_V2()
piper.ConnectPort()

while not piper.EnablePiper():
    time.sleep(0.01)

player = PiperPlayer(piper)
player.load_recording("recordings/my_sequence.ppr")

# Play 5 times
for i in range(5):
    print(f"Playing iteration {i+1}/5...")
    player.start_playback()
    
    while player.is_playing():
        time.sleep(0.1)
    
    time.sleep(2)  # Wait 2 seconds between loops

print("Loop complete!")
```

---

**Version:** 1.0  
**Last Updated:** December 1, 2025  
**Status:** Production Ready ✓

