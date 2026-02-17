# Troubleshooting: No Robot Movement During Playback

If your robot is not moving during playback, follow these diagnostic steps.

---

## 🔍 Quick Diagnostic Steps

### **Step 1: Test Basic Robot Movement**

Run the diagnostic script to verify the robot responds to basic commands:

```bash
python test_robot_movement.py
```

**What this does:**
- Connects to robot
- Enables robot
- Moves robot slightly (5 degrees)
- Returns to start position

**Expected result:** Robot should move visibly

**If robot moves:** ✅ Hardware is working, issue is in playback system  
**If robot doesn't move:** ❌ Hardware/connection issue (see Step 5)

---

### **Step 2: Inspect Your Recording**

Check if your recording contains actual movement data:

```bash
python inspect_recording.py recordings/your_file.ppr
```

**What to look for:**
- Total joint movement > 1.0 degrees
- Non-zero joint values
- Joints changing between first and last sample

**Example good output:**
```
MOVEMENT ANALYSIS:
  J1 change: 15.50° (from 0.00° to 15.50°)
  J2 change: 23.20° (from 45.00° to 68.20°)
  ...
  Total joint movement: 78.50°
  ✓ Movement detected
```

**Example bad output:**
```
MOVEMENT ANALYSIS:
  J1 change: 0.00°
  J2 change: 0.00°
  ...
  Total joint movement: 0.00°
  ⚠️  WARNING: Very little or no movement detected!
```

**If minimal movement:** Record a new sequence with visible motion  
**If good movement:** Proceed to Step 3

---

### **Step 3: Check Playback Logs**

Run playback and watch the console/terminal output:

```bash
python main.py
```

Load a file and click Play. Look for these log messages:

**Good signs:**
```
INFO - Enabling robot...
INFO - Robot enabled successfully
INFO - Gripper initialized successfully
INFO - Playback loop started
INFO - Playback interval: 5.00ms (200.0 Hz)
INFO - Sending position #0: J1=0.00° J2=45.00° J3=-30.00°
INFO - Sending position #1: J1=0.10° J2=45.05° J3=-30.02°
...
```

**Bad signs:**
```
ERROR - Failed to enable robot
WARNING - Gripper initialization failed
ERROR - Failed to send position
```

---

### **Step 4: Verify Robot State**

Before playback, manually check robot status:

```python
from piper_sdk import C_PiperInterface_V2

piper = C_PiperInterface_V2()
piper.ConnectPort()

# Check if robot enables
if piper.EnablePiper():
    print("✓ Robot enabled")
else:
    print("✗ Robot failed to enable")

# Check robot status
status = piper.GetArmStatus()
print(f"Control mode: 0x{status.arm_status.ctrl_mode:02x}")
print(f"Arm status: 0x{status.arm_status.arm_status:02x}")

# Should see:
# Control mode: 0x01 (CAN control)
# Arm status: 0x00 (Normal)
```

---

### **Step 5: Hardware Checklist**

If the diagnostic script (Step 1) fails, check:

| Item | Check | Fix |
|------|-------|-----|
| Power | LED lights on robot? | Power on robot |
| CAN Bus | Interface detected? | `ifconfig` (Linux) or Device Manager (Windows) |
| Emergency Stop | Button released? | Release e-stop button |
| Robot Mode | Switch position? | Check mode switch on robot |
| Cable | Properly connected? | Reseat CAN cable |
| Firmware | Up to date? | Check robot firmware version |

---

### **Step 6: Common Issues & Fixes**

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Robot doesn't move, no errors | Robot not enabled | Run `test_robot_movement.py` |
| "Running behind schedule" warnings | ✅ FIXED in latest version | Update code from repo |
| "Gripper effort out of range" | ✅ FIXED in latest version | Update code from repo |
| All joint values zero | Recording captured no movement | Record with robot moving |
| Commands sent but no movement | Mode not set correctly | ✅ FIXED - MotionCtrl_2() now called each time |

---

## 🔧 Manual Testing Commands

If you want to test manually:

```python
import time
from piper_sdk import C_PiperInterface_V2

# Connect and enable
piper = C_PiperInterface_V2()
piper.ConnectPort()
time.sleep(0.1)

# Enable (critical!)
while not piper.EnablePiper():
    time.sleep(0.01)

# Initialize gripper
piper.GripperCtrl(0, 1000, 0x02, 0)
time.sleep(0.1)
piper.GripperCtrl(0, 1000, 0x01, 0)
time.sleep(0.1)

# Move robot - THIS SHOULD WORK
for i in range(100):
    # Set mode BEFORE each command
    piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)  # 30% speed
    
    # Send position (small movement)
    piper.JointCtrl(
        0,      # J1: 0°
        5000,   # J2: 5°
        -5000,  # J3: -5°
        0,      # J4: 0°
        0,      # J5: 0°
        0       # J6: 0°
    )
    
    # Send gripper
    piper.GripperCtrl(0, 1000, 0x01, 0)
    
    # Wait
    time.sleep(0.1)

print("If robot moved, hardware is working!")
```

---

## 📊 Expected Values

### Joint Commands (in 0.001 degree units):
```python
# 0 degrees = 0
# 45 degrees = 45000
# -30 degrees = -30000
```

### Gripper Commands (in 0.001 mm units):
```python
# Closed (0mm) = 0
# Half open (35mm) = 35000  
# Fully open (70mm) = 70000
```

### Status Codes:
| Code | Meaning |
|------|---------|
| ctrl_mode=0x00 | Standby (bad - robot won't move) |
| ctrl_mode=0x01 | CAN control (good) |
| arm_status=0x00 | Normal (good) |
| arm_status=0x01 | Emergency stop (bad) |

---

## 🎯 Latest Fixes Applied

### Fix 1: Robot Enable
- ✅ Added `while not EnablePiper()` loop before playback
- ✅ Waits up to 1 second for enable to succeed

### Fix 2: MotionCtrl_2() Frequency
- ✅ Now called BEFORE EVERY command (like demos)
- ✅ Previously only called once (incorrect)

### Fix 3: Timing Method
- ✅ Simplified to fixed 5ms delays (like demos)
- ✅ Previously used complex timestamp calculations (too slow)

### Fix 4: Gripper Effort
- ✅ Values now clamped to 0-5000 range
- ✅ Negative values now handled properly

---

## 📝 Full Diagnostic Checklist

Run through this checklist in order:

- [ ] Run `test_robot_movement.py` - Does robot move?
- [ ] Run `inspect_recording.py recordings/file.ppr` - Is data valid?
- [ ] Check console logs during playback - Any errors?
- [ ] Verify robot enables (check logs for "Robot enabled successfully")
- [ ] Check CAN bus is configured and working
- [ ] Verify robot is not in emergency stop
- [ ] Check robot mode switch is in correct position
- [ ] Try manual command test (code above) - Does it work?

---

## 🆘 Still Not Working?

If you've tried all the above:

1. **Capture logs:**
   ```bash
   python main.py 2>&1 | tee playback_log.txt
   ```

2. **Check SDK version:**
   ```bash
   pip show piper_sdk
   ```

3. **Try a demo script:**
   ```bash
   cd piper_sdk/piper_sdk/demo/V2
   python piper_ctrl_moveJ.py
   ```
   If this works, the SDK is fine. If it doesn't, reinstall SDK.

4. **Contact support** with:
   - Log output
   - Recording file
   - SDK version
   - What diagnostic steps you tried

---

## ✅ Success Criteria

You should see:
- ✅ "Robot enabled successfully" in logs
- ✅ "Sending position #0: J1=X J2=Y J3=Z" messages
- ✅ No "Failed to send position" errors
- ✅ Robot physically moving during playback
- ✅ No "running behind schedule" warnings

---

**Last Updated:** December 1, 2025  
**Version:** 1.1 (includes all critical fixes)

