# Robot Command Sequence - Proper Order

Based on official Piper demo scripts, this document shows the correct sequence for robot operations.

---

## 🔄 Standard Operation Sequence

### **1. Connect to Robot**
```python
from piper_sdk import C_PiperInterface_V2

piper = C_PiperInterface_V2()
piper.ConnectPort()
time.sleep(0.1)  # Allow connection to settle
```

### **2. Enable Robot** ⚠️ CRITICAL
```python
# Robot MUST be enabled before it will respond to commands
while not piper.EnablePiper():
    time.sleep(0.01)

print("Robot enabled!")
```

**Why:** Without enabling, the robot silently ignores all movement commands.

### **3. Initialize Gripper** (If Using Gripper)
```python
# Clear errors and disable
piper.GripperCtrl(0, 1000, 0x02, 0)
time.sleep(0.1)

# Enable gripper
piper.GripperCtrl(0, 1000, 0x01, 0)
time.sleep(0.1)
```

### **4. Send Commands** ⚠️ IMPORTANT PATTERN
```python
# For EACH position command, follow this pattern:

# Step A: Set motion control mode
piper.MotionCtrl_2(
    ctrl_mode=0x01,   # CAN control
    move_mode=0x01,   # MOVE J (joint mode)
    move_spd_rate_ctrl=100,  # Speed percentage
    is_mit_mode=0x00  # Normal mode (0xAD for MIT mode)
)

# Step B: Send joint command
piper.JointCtrl(j1, j2, j3, j4, j5, j6)

# Step C: Send gripper command (if needed)
piper.GripperCtrl(position, effort, 0x01, 0)

# Step D: Small delay before next command
time.sleep(0.005)  # 5ms = 200Hz rate

# REPEAT for each command!
```

**Why:** The demo `piper_ctrl_moveJ.py` shows `MotionCtrl_2()` is called **before EVERY** joint command, not just once!

### **5. Disable Robot** (When Done)
```python
while piper.DisablePiper():
    time.sleep(0.01)

print("Robot disabled!")
```

---

## 📝 Complete Example: Moving Robot

```python
#!/usr/bin/env python3
import time
from piper_sdk import C_PiperInterface_V2

# 1. Connect
piper = C_PiperInterface_V2()
piper.ConnectPort()
time.sleep(0.1)

# 2. Enable robot
print("Enabling robot...")
while not piper.EnablePiper():
    time.sleep(0.01)
print("Robot enabled!")

# 3. Initialize gripper
piper.GripperCtrl(0, 1000, 0x02, 0)  # Clear errors
time.sleep(0.1)
piper.GripperCtrl(0, 1000, 0x01, 0)  # Enable
time.sleep(0.1)

# 4. Move robot (example: simple back-and-forth)
positions = [
    [0, 0, 0, 0, 0, 0],           # Home position
    [11459, 11459, -11459, 0, 0, 0],  # Position 2 (in 0.001 degrees)
    [0, 0, 0, 0, 0, 0],           # Back to home
]

for pos in positions:
    # Set mode before EACH command!
    piper.MotionCtrl_2(0x01, 0x01, 50, 0x00)
    
    # Send joint command
    piper.JointCtrl(pos[0], pos[1], pos[2], pos[3], pos[4], pos[5])
    
    # Send gripper command
    piper.GripperCtrl(0, 1000, 0x01, 0)
    
    # Wait before next command
    time.sleep(2.0)  # 2 seconds at each position

# 5. Disable robot
print("Disabling robot...")
while piper.DisablePiper():
    time.sleep(0.01)
print("Robot disabled!")
```

---

## ⚠️ Common Mistakes

### ❌ WRONG: MotionCtrl_2() Only Once
```python
# WRONG!
piper.EnablePiper()
piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)  # Called once

for position in positions:
    piper.JointCtrl(...)  # Won't work reliably!
```

### ✅ CORRECT: MotionCtrl_2() Before Each Command
```python
# CORRECT!
piper.EnablePiper()

for position in positions:
    piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)  # Called each time
    piper.JointCtrl(...)  # Works!
```

### ❌ WRONG: Not Enabling Robot
```python
# WRONG!
piper.ConnectPort()
piper.MotionCtrl_2(...)
piper.JointCtrl(...)  # Commands ignored - robot not enabled!
```

### ✅ CORRECT: Always Enable First
```python
# CORRECT!
piper.ConnectPort()
while not piper.EnablePiper():  # Enable first!
    time.sleep(0.01)
piper.MotionCtrl_2(...)
piper.JointCtrl(...)  # Works!
```

---

## 🎯 Control Modes

### MotionCtrl_2() Parameters:

**ctrl_mode:**
- `0x00` - Standby mode
- `0x01` - CAN control mode ← **Use this for commands**
- `0x02` - Teaching mode
- `0x03` - Ethernet control
- `0x04` - WiFi control
- `0x07` - Offline trajectory

**move_mode:**
- `0x00` - MOVE P (Position/Cartesian)
- `0x01` - MOVE J (Joint) ← **Use this for joint commands**
- `0x02` - MOVE L (Linear)
- `0x03` - MOVE C (Circular)
- `0x04` - MOVE M (MIT)
- `0x05` - MOVE CPV

**is_mit_mode:**
- `0x00` - Normal position/velocity control ← **Use this normally**
- `0xAD` - MIT mode (for force control/manual teaching)
- `0xFF` - Invalid

---

## 🔧 Special Modes

### MIT Mode (Manual Teaching):
```python
# Enable MIT mode for manual movement
piper.EnablePiper()
piper.MotionCtrl_2(0x01, 0x01, 100, 0xAD)  # is_mit_mode=0xAD

# Now you can manually move the robot with low resistance
# Good for recording manual teaching sequences
```

### Reset After MIT Mode:
```python
# After using MIT or teaching mode, reset before normal control
piper.MotionCtrl_1(0x02, 0, 0)  # Reset/recover
time.sleep(0.5)

# Then enable again
while not piper.EnablePiper():
    time.sleep(0.01)
```

---

## 📊 Timing Recommendations

| Operation | Recommended Delay |
|-----------|-------------------|
| After ConnectPort() | 0.1 seconds |
| After EnablePiper() | 0.1 seconds |
| After gripper init | 0.1 seconds each step |
| Between position commands | 0.005 seconds (200Hz) |
| After mode changes | 0.1 seconds |
| After reset | 0.5 seconds |

---

## 🎓 Key Takeaways

1. ✅ **Always enable robot first** - `while not EnablePiper(): time.sleep(0.01)`
2. ✅ **Call MotionCtrl_2() before EVERY command** - Not just once!
3. ✅ **Initialize gripper** before use
4. ✅ **Use consistent timing** between commands
5. ✅ **Disable when done** for safety

---

## 📚 Reference Demo Scripts

All patterns based on official demos in `piper_sdk/demo/V2/`:
- `piper_ctrl_enable.py` - Enable sequence
- `piper_ctrl_moveJ.py` - Joint control pattern
- `piper_ctrl_gripper.py` - Gripper usage
- `piper_ctrl_reset.py` - Reset command
- `piper_set_mit.py` - MIT mode

---

**Version:** 1.0  
**Based on:** Piper SDK V2 demos  
**Last Updated:** December 1, 2025

