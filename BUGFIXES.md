# Bug Fixes Log - Piper Automation System

This document tracks bugs found and fixed in the system.

---

## Bug #1: Gripper Effort Value Out of Range
**Date:** December 1, 2025  
**Severity:** High (Prevents playback)  
**Status:** ✅ FIXED

### Problem:
During playback, every position command failed with error:
```
ERROR - Failed to send position: 'grippers_effort' Value -45 out of range 0-5000
```

### Root Cause:
The Piper SDK sometimes returns negative values for `grippers_effort` (possibly indicating direction or other state). However, the `GripperCtrl()` function only accepts values in the range 0-5000.

When we recorded these negative values and tried to play them back, the SDK rejected them.

### Solution:
**Fixed in:** `recorder.py` and `player.py`

1. **Recorder (`recorder.py`):** Now takes absolute value of gripper effort before recording:
   ```python
   gripper_effort_raw = gripper_data.gripper_state.grippers_effort * 0.001
   gripper_effort = abs(gripper_effort_raw)  # Always positive
   ```

2. **Player (`player.py`):** Added clamping to ensure values are in valid range:
   ```python
   gripper_effort = max(0, min(abs(gripper_effort), 5000))  # Clamp to 0-5000
   ```

### Testing:
- ✅ Recordings now store only positive effort values
- ✅ Playback clamps values to valid range as safety net
- ✅ Old recordings with negative values will be corrected during playback

### Impact:
- **Breaking Change:** No - old recordings will still work (clamped during playback)
- **Performance:** None
- **Compatibility:** Fully backwards compatible

---

## Bug #2: Gripper Initialization Required
**Date:** December 1, 2025  
**Severity:** Medium (Can cause gripper malfunction)  
**Status:** ✅ FIXED

### Problem:
Gripper may not respond or provide feedback during recording/playback if not properly initialized at session start.

### Root Cause:
The Piper SDK requires:
1. **First-time setup** (once per robot): Configure gripper parameters with `GripperTeachingPendantParamConfig(100, 70, 1)`
2. **Session initialization** (every time): Clear errors and enable gripper before use

Without these initializations, the gripper may:
- Not respond to commands
- Not provide position/effort feedback
- Cause recording/playback failures

### Solution:
**Fixed in:** `recorder.py`, `player.py`, and new utility script

1. **Added `_init_gripper()` method** to both Recorder and Player:
   ```python
   def _init_gripper(self):
       # Clear errors and disable
       self.piper.GripperCtrl(0, 1000, 0x02, 0)
       time.sleep(0.1)
       # Enable gripper
       self.piper.GripperCtrl(0, 1000, 0x01, 0)
       time.sleep(0.1)
   ```

2. **Automatic initialization** in `start_recording()` and `start_playback()` (can be disabled with `init_gripper=False`)

3. **Created utility script** `setup_gripper_first_time.py` for first-time configuration

### Testing:
- ✅ Gripper initializes automatically before recording
- ✅ Gripper initializes automatically before playback
- ✅ Can be disabled if needed with `init_gripper=False` parameter
- ✅ First-time setup script tested and working

### Impact:
- **Breaking Change:** No - initialization is automatic but optional
- **Performance:** Adds ~0.2 seconds to startup (negligible)
- **Compatibility:** Fully backwards compatible

### Usage:
**First-time setup (once):**
```bash
python setup_gripper_first_time.py
```

**Normal use (automatic):**
```python
# Initialization happens automatically
recorder.start_recording()  # Gripper init included
player.start_playback()     # Gripper init included
```

---

## Future Issues

Please document any new bugs found here following the same format:
- Date
- Severity (Low/Medium/High/Critical)
- Status (Open/In Progress/Fixed)
- Problem description
- Root cause
- Solution
- Testing results
- Impact assessment

---

**Last Updated:** December 1, 2025

