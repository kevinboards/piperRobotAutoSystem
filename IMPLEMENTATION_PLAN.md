# Piper Automation System - Implementation Plan

## Project Overview
Create a recording and playback system for the Piper robotic arm that allows users to:
1. Record robot movements while manually moving the arm or during automated sequences
2. Save recordings in a custom G-code-like format (*.ppr files)
3. Load and replay recorded movements with high fidelity

---

## File Format Specification

### File Extension
- `.ppr` (Piper Program Recording)

### File Naming Convention
- Format: `YYYY-MM-DD-HHMMSS.ppr`
- Example: `2025-10-01-213045.ppr`
- Based on datetime when recording starts

### Data Format (G-code-like syntax)

Each line represents one timestamped snapshot of robot state:

```
t<epoch_ms> x<X> y<Y> z<Z> a<RX> b<RY> c<RZ> J6[<j1>,<j2>,<j3>,<j4>,<j5>,<j6>] Grp[<pos>,<effort>,<status>]
```

**Field Definitions:**

| Field | Description | Units | Example |
|-------|-------------|-------|---------|
| `t<value>` | Timestamp (epoch milliseconds) | ms | `t1701453045123` |
| `x<value>` | X position | mm | `x150.523` |
| `y<value>` | Y position | mm | `y-50.342` |
| `z<value>` | Z position | mm | `z180.000` |
| `a<value>` | RX rotation (roll) | degrees | `a-179.900` |
| `b<value>` | RY rotation (pitch) | degrees | `b0.000` |
| `c<value>` | RZ rotation (yaw) | degrees | `c-179.900` |
| `J6[...]` | Joint angles array [j1,j2,j3,j4,j5,j6] | degrees | `J6[0.0,45.0,-30.0,0.0,0.0,0.0]` |
| `Grp[...]` | Gripper data [position,effort,code] | mm, N·m, code | `Grp[80.0,1.5,1]` |

**Example Line:**
```
t1701453045123 x150.523 y-50.342 z180.000 a-179.900 b0.000 c-179.900 J6[0.0,45.0,-30.0,0.0,0.0,0.0] Grp[80.0,1.5,1]
```

**Conversion Notes:**
- SDK provides data in 0.001 units (0.001mm, 0.001 degrees)
- File format stores in standard units (mm, degrees)
- Divide SDK values by 1000 for recording
- Multiply by 1000 for playback

---

## System Architecture

### Module Structure

```
PiperAutomationSystem/
├── main.py                     # GUI application (existing)
├── recorder.py                 # Recording module (NEW)
├── player.py                   # Playback module (NEW)
├── ppr_file_handler.py         # File I/O operations (NEW)
├── recordings/                 # Directory for saved recordings (NEW)
│   └── *.ppr files
├── Available Tools.md          # SDK reference (existing)
├── IMPLEMENTATION_PLAN.md      # This document
└── README.md                   # Project readme
```

---

## Implementation Tasks

### Phase 1: File Handler Module ✓
**File:** `ppr_file_handler.py`

**Purpose:** Handle reading/writing of .ppr files

**Functions:**
- `create_ppr_filename()` → Generate filename from current datetime
- `write_ppr_header(file_handle, metadata)` → Write file header with metadata
- `write_ppr_line(file_handle, timestamp, cartesian, joints, gripper)` → Write single data line
- `read_ppr_file(filepath)` → Parse .ppr file and return list of data dictionaries
- `parse_ppr_line(line)` → Parse single line into data dictionary

**Implementation Details:**
```python
# Data structure for each recorded point
{
    'timestamp': 1701453045123,  # epoch milliseconds
    'cartesian': {
        'x': 150.523,  # mm
        'y': -50.342,  # mm
        'z': 180.000,  # mm
        'a': -179.900, # degrees (RX)
        'b': 0.000,    # degrees (RY)
        'c': -179.900  # degrees (RZ)
    },
    'joints': [0.0, 45.0, -30.0, 0.0, 0.0, 0.0],  # degrees
    'gripper': {
        'position': 80.0,   # mm
        'effort': 1.5,      # N·m
        'code': 1           # status code
    }
}
```

---

### Phase 2: Recorder Module ✓
**File:** `recorder.py`

**Purpose:** Record robot movements in real-time

**Class:** `PiperRecorder`

**Methods:**
- `__init__(piper_interface)` → Initialize with Piper SDK interface
- `start_recording()` → Begin recording, create file
- `stop_recording()` → Stop recording, close file
- `record_loop()` → Main recording loop (runs in separate thread)
- `get_current_state()` → Read current robot state from SDK
- `is_recording()` → Return recording status

**Recording Strategy:**
- **Sample Rate:** 200 Hz (5ms intervals) - matches SDK's high-speed update rate
- **Threading:** Use separate thread to avoid blocking GUI
- **Data Collection:**
  - Read joint angles via `GetArmJointMsgs()`
  - Read Cartesian pose via `GetArmEndPoseMsgs()`
  - Read gripper state via `GetArmGripperMsgs()`
  - Get epoch timestamp in milliseconds
- **File Writing:** Buffer writes for performance (write every 10-20 samples)

**Implementation Considerations:**
- Handle SDK connection errors gracefully
- Validate data before writing (check for None/invalid values)
- Provide recording status (duration, sample count)
- Auto-create `recordings/` directory if it doesn't exist

---

### Phase 3: Player Module ✓
**File:** `player.py`

**Purpose:** Load and replay recorded movements

**Class:** `PiperPlayer`

**Methods:**
- `__init__(piper_interface)` → Initialize with Piper SDK interface
- `load_recording(filepath)` → Load .ppr file into memory
- `start_playback(speed_multiplier=1.0)` → Begin playback
- `stop_playback()` → Stop playback
- `pause_playback()` → Pause playback
- `resume_playback()` → Resume playback
- `playback_loop()` → Main playback loop (runs in separate thread)
- `send_position(data_point)` → Send position command to robot
- `is_playing()` → Return playback status
- `get_progress()` → Return current playback progress (0-100%)

**Playback Strategy:**
- **Timing:** Use timestamps from file to maintain original timing
- **Control Mode:** Use joint control (MOVE J) for high fidelity
- **Speed Control:** Allow speed multiplier (0.5x, 1.0x, 2.0x, etc.)
- **Threading:** Run in separate thread to avoid blocking GUI
- **Position Commands:**
  - Set mode: `MotionCtrl_2(0x01, 0x01, 50, 0x00)`
  - Send joints: `JointCtrl(j1, j2, j3, j4, j5, j6)`
  - Send gripper: `GripperCtrl(pos, effort, code, 0x00)`

**Implementation Considerations:**
- Pre-load entire file into memory (validate format)
- Handle timing between points accurately
- Provide progress feedback to GUI
- Allow emergency stop during playback
- Verify robot is enabled before starting playback

---

### Phase 4: GUI Integration ✓
**File:** `main.py` (modify existing)

**Changes Required:**

**1. Import New Modules:**
```python
from recorder import PiperRecorder
from player import PiperPlayer
from ppr_file_handler import create_ppr_filename
```

**2. Add Instance Variables:**
```python
self.recorder = None
self.player = None
self.current_recording_file = None
self.is_recording = False
self.is_playing = False
```

**3. Record Button Callback:**
```python
def on_record_button_clicked():
    if not self.is_recording:
        # Start recording
        self.recorder = PiperRecorder(self.piper)
        self.recorder.start_recording()
        self.is_recording = True
        # Update button text to "Stop Recording"
    else:
        # Stop recording
        self.recorder.stop_recording()
        self.is_recording = False
        # Update button text to "Record"
        # Show saved filename
```

**4. Play Button Callback:**
```python
def on_play_button_clicked():
    if not self.is_playing:
        # Open file dialog
        filepath = show_file_dialog("Open Recording", "*.ppr")
        if filepath:
            self.player = PiperPlayer(self.piper)
            self.player.load_recording(filepath)
            self.player.start_playback()
            self.is_playing = True
            # Update button text to "Stop"
    else:
        # Stop playback
        self.player.stop_playback()
        self.is_playing = False
        # Update button text to "Play"
```

**5. Status Updates:**
- Display recording duration/sample count
- Display playback progress bar
- Show current loaded file name
- Display robot connection status

**6. UI Elements to Add:**
- **Record Button:** Toggle between "Record" and "Stop Recording"
- **Play Button:** Open file and start playback
- **Stop Button:** Emergency stop for playback
- **Load Button:** Load file without playing
- **Status Label:** Show current operation status
- **Progress Bar:** Show playback progress
- **File Label:** Show currently loaded/recording file
- **Speed Slider:** Control playback speed (0.5x - 2.0x)

---

### Phase 5: Testing & Validation ✓

**Test Cases:**

**1. Recording Tests:**
- [ ] Record 10-second movement in MIT mode (manual teaching)
- [ ] Record 30-second automated sequence
- [ ] Verify file format is correct (valid syntax)
- [ ] Verify all data fields are populated
- [ ] Verify timestamps are monotonically increasing
- [ ] Test recording with gripper movements
- [ ] Test starting/stopping recording multiple times

**2. Playback Tests:**
- [ ] Load and play 10-second recording
- [ ] Verify robot follows recorded path accurately
- [ ] Test playback at 0.5x speed
- [ ] Test playback at 2.0x speed
- [ ] Test pause/resume functionality
- [ ] Test stop functionality (mid-playback)
- [ ] Test loading invalid file (error handling)

**3. File Format Tests:**
- [ ] Verify file can be opened in text editor
- [ ] Verify human-readable format
- [ ] Parse file and verify all fields
- [ ] Test with large files (5+ minutes)
- [ ] Test with edge cases (zero positions, negative values)

**4. Integration Tests:**
- [ ] Record → Save → Load → Playback full cycle
- [ ] Multiple recording sessions in one application session
- [ ] GUI remains responsive during recording/playback
- [ ] Error handling for disconnected robot
- [ ] File system error handling (permissions, disk space)

---

## Safety Considerations

### Recording Safety
- **MIT Mode Recommended:** Enable MIT mode for manual teaching to allow easy movement
- **Workspace Limits:** Ensure robot stays within safe workspace during recording
- **Emergency Stop:** User can stop recording at any time

### Playback Safety
- **Pre-Flight Checks:**
  - Verify robot is connected
  - Verify robot is enabled
  - Check starting position is safe
  - Verify workspace is clear of obstacles
- **Speed Limits:** Start with 50% speed for testing, allow user control
- **Emergency Stop:** Always allow immediate stop during playback
- **Position Validation:** Validate positions are within joint limits before sending

---

## Performance Considerations

### Recording Performance
- **Sample Rate:** 200 Hz (5ms between samples)
- **Expected File Size:** ~200 bytes/line × 200 Hz = 40 KB/second = 2.4 MB/minute
- **Buffered Writing:** Write in batches of 10-20 samples to reduce I/O overhead
- **Memory Usage:** Minimal - stream directly to file

### Playback Performance
- **Pre-loading:** Load entire file into memory before playback
- **Memory Usage:** ~2.4 MB/minute of recording
- **Timing Accuracy:** Use timestamp deltas for accurate timing
- **Command Rate:** Send commands at recorded rate (up to 200 Hz)

---

## Future Enhancements (Post-MVP)

### Phase 6: Advanced Features
- **Recording Trimming:** Edit start/end of recordings
- **Recording Preview:** 3D visualization of recorded path
- **Recording Metadata:** Add notes, tags, descriptions
- **Recording Library:** Browse and manage saved recordings
- **Loop Playback:** Repeat recording continuously
- **Waypoint Markers:** Add named waypoints during recording
- **Speed Profiles:** Adjust speed at different points in playback
- **Recording Merging:** Combine multiple recordings
- **Format Conversion:** Export to standard G-code or other formats

### Phase 7: Advanced Playback
- **Trajectory Smoothing:** Optional smoothing of recorded path
- **Position Offset:** Shift entire recording in 3D space
- **Orientation Adjustment:** Rotate/mirror recordings
- **Conditional Playback:** Play different paths based on conditions
- **Force Feedback:** Use force data during playback

---

## File Format Rationale

### Why G-code-like Format?
- **Human Readable:** Easy to debug and manually edit
- **Industry Standard:** Familiar to users with CNC/3D printing experience
- **Simple Parsing:** Easy to implement parser
- **Extensible:** Can add new fields without breaking existing files
- **Version Control Friendly:** Text format works well with git

### Why Separate Timestamp Field?
- **Flexibility:** Allows variable time intervals
- **Accuracy:** Millisecond precision for timing
- **Debugging:** Easy to see timing issues
- **Resampling:** Can easily resample to different rates

### Why Include Both Joint and Cartesian Data?
- **Redundancy:** If one fails to parse, have backup
- **Flexibility:** Can play back using joint or Cartesian control
- **Validation:** Cross-check consistency between joint/Cartesian
- **Analysis:** Can analyze both joint and task space movements

---

## Implementation Timeline

### Day 1: Foundation
- [x] Create plan document (this file)
- [ ] Create `ppr_file_handler.py` with all I/O functions
- [ ] Test file writing/reading with sample data
- [ ] Create `recordings/` directory structure

### Day 2: Recording
- [ ] Create `recorder.py` module
- [ ] Implement recording loop with threading
- [ ] Test recording with robot in MIT mode
- [ ] Validate file format output

### Day 3: Playback
- [ ] Create `player.py` module
- [ ] Implement playback loop with threading
- [ ] Test playback of recorded files
- [ ] Implement speed control

### Day 4: GUI Integration
- [ ] Integrate recorder into main.py
- [ ] Integrate player into main.py
- [ ] Add UI elements (buttons, status, progress)
- [ ] Test full recording → playback cycle

### Day 5: Testing & Polish
- [ ] Run all test cases
- [ ] Fix bugs and edge cases
- [ ] Add error handling
- [ ] Documentation and code comments
- [ ] User testing

---

## Success Criteria

The system is considered complete when:

1. ✅ User can press "Record" button and record robot movements
2. ✅ Recording saves to properly formatted .ppr file with datetime name
3. ✅ File contains all necessary data: timestamps, positions, joints, gripper
4. ✅ File is human-readable and follows G-code-like syntax
5. ✅ User can load a .ppr file
6. ✅ User can press "Play" button and robot replays recorded movements
7. ✅ Playback accurately reproduces original movements
8. ✅ Recording and playback work at 200 Hz sample rate
9. ✅ GUI remains responsive during recording/playback
10. ✅ System handles errors gracefully (disconnections, invalid files, etc.)

---

## Code Style Guidelines

- **Function Comments:** Include docstring for all public functions explaining purpose, parameters, and return values
- **Type Hints:** Use type hints for all function parameters and return values
- **Error Handling:** Use try/except blocks for all SDK calls and file operations
- **Logging:** Use logging module for debugging (not print statements)
- **Constants:** Define magic numbers as named constants at top of file
- **Threading:** Use threading.Event for clean thread shutdown
- **Resource Cleanup:** Use context managers (with statements) for file operations

---

## Dependencies

### Required Python Packages
- `piper_sdk` - Piper robot SDK (already installed)
- `python-can` - CAN bus communication (already installed)
- Standard library: `threading`, `time`, `datetime`, `os`, `json`, `logging`

### System Requirements
- CAN bus interface configured
- Piper robot connected and powered
- Sufficient disk space for recordings (~2.4 MB per minute)

---

**Document Version:** 1.0  
**Created:** December 1, 2025  
**Status:** Ready for Implementation

