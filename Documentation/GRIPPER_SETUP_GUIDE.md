# Gripper Setup Guide - Piper Automation System

## Overview
The Piper robot gripper requires proper initialization to function correctly. This guide explains the setup process and automatic initialization built into the system.

---

## Why Gripper Initialization Matters

Without proper initialization, the gripper may:
- ❌ Not respond to commands
- ❌ Not provide position/effort feedback
- ❌ Cause recording/playback failures
- ❌ Show "out of range" errors

With proper initialization:
- ✅ Gripper responds reliably
- ✅ Accurate position/effort readings
- ✅ Smooth recording and playback
- ✅ No unexpected errors

---

## Two Types of Initialization

### 1. First-Time Setup (Once Per Robot)
**When:** 
- First time using a new robot
- After replacing the gripper
- After factory reset

**What it does:**
- Configures gripper parameters (max travel: 70mm)
- Sets teaching pendant parameters
- Saves settings to robot (persistent)

**How to run:**
```bash
cd PiperAutomationSystem
python setup_gripper_first_time.py
```

**What you'll see:**
```
=======================================================================
 PIPER ROBOT - FIRST-TIME GRIPPER SETUP
=======================================================================

This script configures the gripper for first-time use.
You only need to run this ONCE per robot/gripper.

WARNING: Make sure the gripper is properly attached before proceeding!

Continue with gripper setup? (y/n): y

INFO - Connecting to robot...
INFO - Connected successfully!

INFO - STEP 1: Configuring gripper parameters...
INFO -   Teaching range: 100
INFO -   Max range: 70mm
INFO -   Teaching friction: 1
INFO - Configuration sent successfully!

INFO - STEP 2: Initializing gripper...
INFO - Gripper initialized successfully!

INFO - STEP 3: Testing gripper response...
INFO - Gripper status reading #1: 45.23mm
INFO - Gripper status reading #2: 45.24mm
INFO - Gripper status reading #3: 45.22mm

=======================================================================
 ✓ GRIPPER SETUP COMPLETE!
=======================================================================

The gripper is now configured and ready to use.
You do NOT need to run this script again unless:
  - You replace the gripper
  - You reset the robot to factory settings

You can now use the Piper Automation System:
  python main.py
```

---

### 2. Session Initialization (Every Time - AUTOMATIC)
**When:** 
- Every time you start recording
- Every time you start playback

**What it does:**
- Clears any previous errors
- Disables then re-enables gripper
- Ensures fresh start for the session

**How it works:**
The system does this **automatically** for you! No manual steps needed.

**Behind the scenes:**
```python
# Automatically called in recorder.start_recording()
# and player.start_playback()
def _init_gripper(self):
    # Clear errors and disable
    self.piper.GripperCtrl(0, 1000, 0x02, 0)
    time.sleep(0.1)
    
    # Enable gripper
    self.piper.GripperCtrl(0, 1000, 0x01, 0)
    time.sleep(0.1)
```

---

## Complete Setup Workflow

### Initial Robot Setup (Do Once):

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: First-time gripper configuration
python setup_gripper_first_time.py

# Step 3: You're ready! Start using the system
python main.py
```

### Daily Usage (Automatic):

```bash
# Just run the application - gripper initialization is automatic!
python main.py
```

The system handles gripper initialization automatically when you:
- Click "Record" button (GUI)
- Click "Play" button (GUI)
- Call `recorder.start_recording()` (code)
- Call `player.start_playback()` (code)

---

## Advanced: Disabling Automatic Initialization

If you need to disable automatic gripper initialization (e.g., gripper not installed):

### In GUI:
Not currently supported - initialization always runs for safety.

### In Code:
```python
# Recording without gripper init
recorder.start_recording(init_gripper=False)

# Playback without gripper init
player.start_playback(init_gripper=False)
```

---

## Troubleshooting

### Problem: "Gripper not responding"
**Solution:**
1. Run first-time setup: `python setup_gripper_first_time.py`
2. Restart robot and try again
3. Check gripper physical connection

### Problem: "No gripper feedback data"
**Solution:**
1. Ensure first-time setup was completed
2. Check that gripper is properly attached
3. Verify gripper cable connections

### Problem: "Gripper effort out of range" (Old issue - now fixed)
**Solution:**
- Update to latest version (includes automatic value clamping)
- System now handles negative/invalid values automatically
- No action needed!

### Problem: First-time setup fails
**Solution:**
1. Check CAN bus is configured
2. Verify robot is powered on
3. Ensure no hardware faults
4. Try disconnecting/reconnecting robot

---

## Technical Details

### Gripper Control Codes:
| Code | Meaning |
|------|---------|
| `0x00` | Disable |
| `0x01` | Enable |
| `0x02` | Disable and clear errors |
| `0x03` | Enable and clear errors |
| `0xAE` | Set current position as zero |

### Configuration Parameters:
| Parameter | Value | Range | Purpose |
|-----------|-------|-------|---------|
| `teaching_range_per` | 100 | [100-200] | Teaching pendant range coefficient |
| `max_range_config` | 70 | [0,70,100] | Max gripper travel (mm) |
| `teaching_friction` | 1 | - | Teaching mode friction |

### Initialization Timing:
- First-time setup: ~2-3 seconds
- Session initialization: ~0.2 seconds (automatic)
- Impact on recording start: Negligible
- Impact on playback start: Negligible

---

## Reference: Manual Gripper Control

If you need to manually control the gripper:

```python
from piper_sdk import C_PiperInterface_V2
import time

piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable robot
while not piper.EnablePiper():
    time.sleep(0.01)

# Initialize gripper
piper.GripperCtrl(0, 1000, 0x02, 0)  # Clear errors
time.sleep(0.1)
piper.GripperCtrl(0, 1000, 0x01, 0)  # Enable
time.sleep(0.1)

# Open gripper to 50mm
piper.GripperCtrl(50000, 1000, 0x01, 0)  # 50mm = 50000 in 0.001mm units

# Close gripper
piper.GripperCtrl(0, 1000, 0x01, 0)

# Read gripper status
status = piper.GetArmGripperMsgs()
position = status.gripper_state.grippers_angle * 0.001  # Convert to mm
effort = status.gripper_state.grippers_effort * 0.001  # Convert to N·m
print(f"Position: {position}mm, Effort: {effort}N·m")
```

---

## Summary

**Do once:**
```bash
python setup_gripper_first_time.py
```

**Then use normally - everything else is automatic:**
```bash
python main.py
```

The system handles all gripper initialization automatically during recording and playback!

---

**For more information:**
- See `Available Tools.md` for SDK gripper functions
- See `BUGFIXES.md` for bug fix history
- See demo scripts in `piper_sdk/demo/V2/piper_ctrl_gripper.py`

---

**Last Updated:** December 1, 2025  
**Version:** 1.1

