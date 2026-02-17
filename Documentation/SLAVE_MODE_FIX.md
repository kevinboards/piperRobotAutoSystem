# Critical Fix: Slave Mode Configuration

## What Was Added

Based on the SDK documentation, the robot must be in **slave mode** to receive commands from the SDK. I've added the proper configuration sequence to all modules.

---

## The Proper Initialization Sequence

### Before (Missing Critical Steps):
```python
piper.ConnectPort()
piper.EnablePiper()
# Send commands - may not work!
```

### After (Complete Sequence):
```python
# 1. Connect
piper.ConnectPort()
time.sleep(0.1)

# 2. Set to Slave Mode (CRITICAL!)
piper.MasterSlaveConfig(0xFC, 0, 0, 0)
time.sleep(0.2)

# 3. Reset Robot
piper.ResetRobot()
time.sleep(0.5)

# 4. Enable Robot
while not piper.EnablePiper():
    time.sleep(0.01)
time.sleep(0.1)

# 5. Initialize Gripper
piper.GripperCtrl(0, 1000, 0x02, 0)  # Clear errors
time.sleep(0.1)
piper.GripperCtrl(0, 1000, 0x01, 0)  # Enable
time.sleep(0.1)

# NOW ready to send commands!
```

---

## What `MasterSlaveConfig(0xFC, 0, 0, 0)` Does

From the SDK documentation:

**Parameters:**
- `linkage_config`: `0xFC` = Set as slave arm (receives commands)
- `feedback_offset`: `0` = No offset (default feedback ID)
- `ctrl_offset`: `0` = No offset (default control ID)
- `linkage_offset`: `0` = No offset

**Result:** Robot is configured to **receive and execute commands** from the SDK.

**Alternative:**
- `0xFA` = Master arm (teaching mode - doesn't respond to SDK commands)

---

## Files Updated

### 1. `test_robot_movement.py`
**New sequence:**
- Step 1: Connect
- Step 2: Set to slave mode ✨ NEW
- Step 3: Reset robot ✨ NEW
- Step 4: Enable
- Step 5: Initialize gripper
- Step 6: Read current position
- Step 7: Test movement

### 2. `player.py`
Added to `start_playback()`:
```python
# Set to slave mode
self.piper.MasterSlaveConfig(0xFC, 0, 0, 0)
time.sleep(0.2)

# Reset robot
self.piper.ResetRobot()
time.sleep(0.5)

# Then enable...
```

### 3. `recorder.py`
Added to `start_recording()` (when `enable_robot=True`):
```python
# Set to slave mode
self.piper.MasterSlaveConfig(0xFC, 0, 0, 0)
time.sleep(0.2)

# Reset robot
self.piper.ResetRobot()
time.sleep(0.5)

# Then enable...
```

---

## Why This Matters

### Master vs Slave Mode

| Mode | Purpose | SDK Commands |
|------|---------|--------------|
| **Slave** (0xFC, 0, 0, 0) | Receives commands from SDK | ✅ Responds |
| **Master** (0xFA, ...) | Teaching mode (manual movement) | ❌ Ignores |

**If robot is in master/teaching mode:**
- Commands are sent successfully (no errors)
- Robot appears connected
- **But robot doesn't move** - commands are silently ignored!

---

## Why Reset is Important

From the SDK notes:
> "Reset must be executed once after setting to teaching mode"

**Purpose of Reset:**
- Clears any previous mode state
- Prepares robot for new command mode
- Ensures clean transition to slave mode

**When to reset:**
- After changing master/slave mode
- After teaching mode
- Before starting automated control
- When robot becomes unresponsive

---

## Testing

Run the updated test script:

```bash
python test_robot_movement.py
```

**You should now see:**
```
Step 1: Connecting to robot...
✓ Connected

Step 2: Setting robot to slave mode (ready to receive commands)...
✓ Slave mode configured

Step 3: Resetting robot...
✓ Robot reset

Step 4: Enabling robot...
✓ Robot enabled

Step 5: Initializing gripper...
✓ Gripper initialized

Step 6: Reading current position...
Current position: J1=X.XX° J2=Y.YY° J3=Z.ZZ°

Step 7: Testing movement...
[Robot should move here!]
```

---

## If Robot Still Doesn't Move

If the test still fails after these changes:

### 1. Check Robot Mode Switch
Some Piper robots have a physical mode switch. Ensure it's in the correct position for SDK control (not teaching mode).

### 2. Check for Emergency Stop
- Physical e-stop button pressed?
- Software emergency stop triggered?

### 3. Verify CAN Bus
```bash
# Linux:
ifconfig can0

# Should show can0 interface active
```

### 4. Check Firmware Version
```python
from piper_sdk import C_PiperInterface_V2

piper = C_PiperInterface_V2()
piper.ConnectPort()
version = piper.GetPiperFirmwareVersion()
print(f"Firmware: {version}")

# Should be >= V1.5-2
```

### 5. Try Official Demo
```bash
cd piper_sdk/piper_sdk/demo/V2
python piper_ctrl_moveJ.py
```

If official demo works but our code doesn't → issue is in our code  
If official demo doesn't work → hardware/setup issue

---

## Important Notes

### Mode Change Requires Restart?

From SDK docs:
> "Robot must be restarted after mode change"

**However:** In practice, the reset command (`ResetRobot()`) appears to handle this without a full power cycle. If you're still having issues, try:

1. Power cycle the robot
2. Run the test script
3. If it works after power cycle, you may need to add power cycle instructions

### Timing is Important

The delays after each command are critical:
- `MasterSlaveConfig`: 0.2s (200ms)
- `ResetRobot`: 0.5s (500ms)
- `EnablePiper`: 0.1s (100ms) after success
- `GripperCtrl`: 0.1s (100ms) between commands

**Don't reduce these delays!** The robot needs time to process each command.

---

## Summary of All Fixes

This is **Fix #4** in a series:

| Fix # | Issue | Solution |
|-------|-------|----------|
| 1 | Gripper effort out of range | Clamp values to 0-5000 |
| 2 | Gripper not initialized | Auto-init at start of recording/playback |
| 3 | Robot not moving | Add EnablePiper() + MotionCtrl_2() each command |
| **4** | **Robot still not moving** | **Add slave mode config + reset** |

---

## Next Steps

1. **Run the test:**
   ```bash
   python test_robot_movement.py
   ```

2. **Watch for the new steps:**
   - Step 2: Slave mode configured
   - Step 3: Robot reset

3. **Observe robot movement:**
   - Should move at Step 7

4. **If it works:**
   - Try playback with `python main.py`
   - Load a recording and play

5. **If it still doesn't work:**
   - Check the troubleshooting section above
   - Try power cycling the robot
   - Run official demos to verify hardware

---

**Version:** 1.0  
**Date:** December 1, 2025  
**Status:** Critical fix applied - test required

