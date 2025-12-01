# Piper Robot SDK - Available Tools for Recording and Playback System

## Overview
This document provides a comprehensive reference for using the Piper SDK to implement a recording and playback system. The SDK provides methods to read joint angles, Cartesian positions, and control the robot for playback.

---

## Table of Contents
1. [Initialization and Connection](#initialization-and-connection)
2. [Reading Robot State (Recording)](#reading-robot-state-recording)
3. [Control Modes](#control-modes)
4. [Sending Commands (Playback)](#sending-commands-playback)
5. [Data Formats and Units](#data-formats-and-units)
6. [Example Code Patterns](#example-code-patterns)
7. [Important Notes](#important-notes)

---

## Initialization and Connection

### Creating Interface Instance
```python
from piper_sdk import *

# Create interface with default CAN port (can0)
piper = C_PiperInterface_V2()

# Or specify a custom CAN port
piper = C_PiperInterface_V2("can0")
```

### Connecting to Robot
```python
# Connect to the robot via CAN bus
piper.ConnectPort()

# Wait briefly for connection to establish
time.sleep(0.1)
```

### Enabling/Disabling Robot
```python
# Enable the robot (required before sending motion commands)
while not piper.EnablePiper():
    time.sleep(0.01)
print("Robot enabled successfully")

# Disable the robot (useful for manual teaching mode)
while piper.DisablePiper():
    time.sleep(0.01)
print("Robot disabled successfully")
```

---

## Reading Robot State (Recording)

### 1. Reading Joint Angles

#### Method: `GetArmJointMsgs()`
Returns joint angles for all 6 joints plus timestamp and frequency information.

**Returns:**
- `ArmJoint` object containing:
  - `time_stamp`: Timestamp of the reading (float)
  - `Hz`: Update frequency (float)
  - `joint_state`: Object containing:
    - `joint_1` through `joint_6` (int): Joint angles in **0.001 degrees**

**Example:**
```python
joint_data = piper.GetArmJointMsgs()

# Access individual joints (units: 0.001 degrees)
j1 = joint_data.joint_state.joint_1  # Returns integer, e.g., 45000 = 45.0 degrees
j2 = joint_data.joint_state.joint_2
j3 = joint_data.joint_state.joint_3
j4 = joint_data.joint_state.joint_4
j5 = joint_data.joint_state.joint_5
j6 = joint_data.joint_state.joint_6

# Get timestamp and frequency
timestamp = joint_data.time_stamp
hz = joint_data.Hz

# Convert to degrees
j1_degrees = j1 * 0.001
```

**Joint Limits:**
| Joint | Limit (degrees) | Limit (radians) |
|-------|----------------|-----------------|
| Joint 1 | [-150.0, 150.0] | [-2.6179, 2.6179] |
| Joint 2 | [0, 180.0] | [0, 3.14] |
| Joint 3 | [-170, 0] | [-2.967, 0] |
| Joint 4 | [-100.0, 100.0] | [-1.745, 1.745] |
| Joint 5 | [-70.0, 70.0] | [-1.22, 1.22] |
| Joint 6 | [-120.0, 120.0] | [-2.09439, 2.09439] |

---

### 2. Reading End-Effector Pose (Cartesian Position)

#### Method: `GetArmEndPoseMsgs()`
Returns the end-effector pose in Cartesian coordinates (X, Y, Z) and orientation (RX, RY, RZ).

**Returns:**
- `ArmEndPose` object containing:
  - `time_stamp`: Timestamp of the reading (float)
  - `Hz`: Update frequency (float)
  - `end_pose`: Object containing:
    - `X_axis`, `Y_axis`, `Z_axis` (int): Position in **0.001 mm**
    - `RX_axis`, `RY_axis`, `RZ_axis` (int): Orientation in **0.001 degrees** (Euler angles, XYZ rotation order)

**Example:**
```python
end_pose_data = piper.GetArmEndPoseMsgs()

# Access position and orientation (units: 0.001 mm and 0.001 degrees)
x = end_pose_data.end_pose.X_axis  # e.g., 150000 = 150.0 mm
y = end_pose_data.end_pose.Y_axis
z = end_pose_data.end_pose.Z_axis
rx = end_pose_data.end_pose.RX_axis  # Rotation about X
ry = end_pose_data.end_pose.RY_axis  # Rotation about Y
rz = end_pose_data.end_pose.RZ_axis  # Rotation about Z

# Convert to standard units
x_mm = x * 0.001  # Convert to mm
rx_degrees = rx * 0.001  # Convert to degrees
```

**Note:** The pose represents the J6 (end joint) position. If you need TCP (Tool Center Point) with a tool offset, use the calculation provided in `piper_read_tcp_pose.py`.

---

### 3. Reading Gripper State

#### Method: `GetArmGripperMsgs()`
Returns gripper position and effort information.

**Returns:**
- `ArmGripper` object containing:
  - `time_stamp`: Timestamp (float)
  - `Hz`: Update frequency (float)
  - `gripper_state`: Object containing:
    - `grippers_angle` (int): Gripper position in **0.001 mm**
    - `grippers_effort` (int): Gripper effort/torque in **0.001 N·m**
    - `foc_status`: Status flags (voltage, temperature, errors, etc.)

**Example:**
```python
gripper_data = piper.GetArmGripperMsgs()

# Access gripper position and effort
gripper_pos = gripper_data.gripper_state.grippers_angle  # 0.001 mm units
gripper_effort = gripper_data.gripper_state.grippers_effort  # 0.001 N·m units

# Convert to standard units
gripper_pos_mm = gripper_pos * 0.001
gripper_effort_nm = gripper_effort * 0.001
```

---

### 4. Reading High-Speed Motor Information

#### Method: `GetArmHighSpdInfoMsgs()`
Returns detailed high-speed feedback for all motors including position, speed, current, and effort.

**Returns:**
- `ArmMotorDriverInfoHighSpd` object containing:
  - `motor_1` through `motor_6`: Each with:
    - `pos` (int): Position in **0.001 radians**
    - `motor_speed` (int): Speed in **0.001 rad/s**
    - `current` (int): Current in **0.001 A**
    - `effort` (int): Effort/torque in **0.001 N·m**

**Example:**
```python
high_spd_data = piper.GetArmHighSpdInfoMsgs()

# Access motor 1 data
motor1_pos = high_spd_data.motor_1.pos  # 0.001 radians
motor1_speed = high_spd_data.motor_1.motor_speed  # 0.001 rad/s
motor1_current = high_spd_data.motor_1.current  # 0.001 A
motor1_effort = high_spd_data.motor_1.effort  # 0.001 N·m

# Convert to standard units
motor1_pos_rad = motor1_pos * 0.001
motor1_speed_rad_s = motor1_speed * 0.001
```

---

### 5. Reading Robot Status

#### Method: `GetArmStatus()`
Returns current robot control mode, arm status, motion status, and error flags.

**Returns:**
- `ArmStatus` object containing:
  - `arm_status`: Object with:
    - `ctrl_mode` (int): Control mode (0x00=Standby, 0x01=CAN, 0x02=Teaching, etc.)
    - `arm_status` (int): Arm status (0x00=Normal, 0x01=Emergency stop, etc.)
    - `mode_feed` (int): Current move mode (0x00=MOVE_P, 0x01=MOVE_J, etc.)
    - `motion_status` (int): Motion status (0x00=Reached, 0x01=Moving)
    - `err_status`: Error flags for each joint

**Example:**
```python
status = piper.GetArmStatus()

ctrl_mode = status.arm_status.ctrl_mode
arm_status = status.arm_status.arm_status
motion_status = status.arm_status.motion_status

# Check if robot is in CAN control mode
if ctrl_mode == 0x01:
    print("Robot is in CAN control mode")

# Check if motion is complete
if motion_status == 0x00:
    print("Robot has reached target position")
```

---

## Control Modes

### Control Modes (`ctrl_mode`)
- `0x00`: Standby mode
- `0x01`: CAN command control mode
- `0x02`: Teaching mode (for manual movement)
- `0x03`: Ethernet control mode
- `0x04`: WiFi control mode
- `0x05`: Remote control mode
- `0x06`: Linkage teaching input mode
- `0x07`: Offline trajectory mode

### Movement Modes (`move_mode`)
- `0x00`: MOVE P (Position mode - end-effector position control)
- `0x01`: MOVE J (Joint mode - joint angle control)
- `0x02`: MOVE L (Linear mode - straight line motion)
- `0x03`: MOVE C (Circular mode - circular arc motion)
- `0x04`: MOVE M (MIT mode)
- `0x05`: MOVE CPV (Continuous path velocity mode)

### MIT Mode
MIT mode provides the **fastest response** for real-time control. It's useful for:
- Manual teaching/dragging
- Force control applications
- Real-time trajectory following

---

## Sending Commands (Playback)

### 1. Setting Control Mode

#### Method: `MotionCtrl_2()`
Sets the robot's control and movement mode.

**Parameters:**
- `ctrl_mode`: Control mode (0x01 for CAN control)
- `move_mode`: Movement mode (0x01 for MOVE J, 0x00 for MOVE P, 0x02 for MOVE L)
- `move_spd_rate_ctrl`: Speed percentage (0-100)
- `is_mit_mode`: MIT mode flag (0x00=normal, 0xAD=MIT mode)
- `residence_time`: Dwell time at point (0-254 seconds, 255=terminate)
- `installation_pos`: Installation position (0x00=invalid, 0x01=horizontal, 0x02=left side, 0x03=right side)

**Example:**
```python
# Set to CAN control, MOVE J mode, 50% speed, normal mode
piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=50, is_mit_mode=0x00)

# Set to MIT mode for manual teaching
piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=100, is_mit_mode=0xAD)
```

---

### 2. Sending Joint Commands

#### Method: `JointCtrl()`
Controls all 6 joints simultaneously. **Must be in joint control mode (MOVE J) first.**

**Parameters:**
- `joint_1` through `joint_6` (int): Joint angles in **0.001 degrees**

**Example:**
```python
# First, set to joint control mode
piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=50, is_mit_mode=0x00)

# Send joint angles (all in 0.001 degree units)
piper.JointCtrl(
    joint_1=0,      # 0 degrees
    joint_2=45000,  # 45 degrees
    joint_3=-30000, # -30 degrees
    joint_4=0,
    joint_5=0,
    joint_6=0
)
```

---

### 3. Sending End-Effector Commands

#### Method: `EndPoseCtrl()`
Controls the end-effector position and orientation. **Must be in position control mode (MOVE P) first.**

**Parameters:**
- `X_axis`, `Y_axis`, `Z_axis` (int): Position in **0.001 mm**
- `RX_axis`, `RY_axis`, `RZ_axis` (int): Orientation in **0.001 degrees**

**Example:**
```python
# First, set to position control mode
piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x00, move_spd_rate_ctrl=50, is_mit_mode=0x00)

# Send end-effector pose
piper.EndPoseCtrl(
    X_axis=150000,   # 150 mm
    Y_axis=-50000,   # -50 mm
    Z_axis=150000,   # 150 mm
    RX_axis=-179900, # -179.9 degrees
    RY_axis=0,
    RZ_axis=-179900
)
```

---

### 4. Controlling Gripper

#### Method: `GripperCtrl()`
Controls gripper position and effort.

**Parameters:**
- `gripper_angle` (int): Gripper opening in **0.001 mm**
- `gripper_effort` (int): Gripper torque in **0.001 N·m** (range: 0-5000 = 0-5 N·m)
- `gripper_code` (int): Control code
  - `0x00`: Disable
  - `0x01`: Enable
  - `0x02`: Disable and clear error
  - `0x03`: Enable and clear error
- `set_zero` (int): Set zero point
  - `0x00`: Invalid/no action
  - `0xAE`: Set current position as zero

**Example:**
```python
# Open gripper to 80mm with 1 N·m effort
piper.GripperCtrl(
    gripper_angle=80000,  # 80 mm
    gripper_effort=1000,  # 1 N·m
    gripper_code=0x01,    # Enable
    set_zero=0x00         # No zero setting
)
```

---

## Data Formats and Units

### Summary Table

| Data Type | Method | Field | Units | Conversion |
|-----------|--------|-------|-------|------------|
| Joint Angle | `GetArmJointMsgs()` | `joint_1` to `joint_6` | 0.001 degrees | `degrees = value * 0.001` |
| Cartesian Position | `GetArmEndPoseMsgs()` | `X_axis`, `Y_axis`, `Z_axis` | 0.001 mm | `mm = value * 0.001` |
| Cartesian Orientation | `GetArmEndPoseMsgs()` | `RX_axis`, `RY_axis`, `RZ_axis` | 0.001 degrees | `degrees = value * 0.001` |
| Motor Position | `GetArmHighSpdInfoMsgs()` | `pos` | 0.001 radians | `radians = value * 0.001` |
| Motor Speed | `GetArmHighSpdInfoMsgs()` | `motor_speed` | 0.001 rad/s | `rad_s = value * 0.001` |
| Motor Current | `GetArmHighSpdInfoMsgs()` | `current` | 0.001 A | `amperes = value * 0.001` |
| Motor Effort | `GetArmHighSpdInfoMsgs()` | `effort` | 0.001 N·m | `nm = value * 0.001` |
| Gripper Position | `GetArmGripperMsgs()` | `grippers_angle` | 0.001 mm | `mm = value * 0.001` |
| Gripper Effort | `GetArmGripperMsgs()` | `grippers_effort` | 0.001 N·m | `nm = value * 0.001` |

### Important Conversion Factor
For converting radians to the SDK's 0.001 degree format:
```python
factor = 57295.7795  # 1000 * 180 / π
sdk_value = radians * factor
```

---

## Example Code Patterns

### Example 1: Recording Joint Angles in a Loop
```python
import time
from piper_sdk import *

# Initialize
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Recording loop
recorded_data = []
recording_duration = 10  # seconds
recording_rate = 200  # Hz (5ms interval)

start_time = time.time()
while time.time() - start_time < recording_duration:
    # Read current state
    joint_data = piper.GetArmJointMsgs()
    end_pose_data = piper.GetArmEndPoseMsgs()
    gripper_data = piper.GetArmGripperMsgs()
    
    # Store timestamp and data
    record = {
        'timestamp': joint_data.time_stamp,
        'joints': [
            joint_data.joint_state.joint_1,
            joint_data.joint_state.joint_2,
            joint_data.joint_state.joint_3,
            joint_data.joint_state.joint_4,
            joint_data.joint_state.joint_5,
            joint_data.joint_state.joint_6
        ],
        'cartesian': [
            end_pose_data.end_pose.X_axis,
            end_pose_data.end_pose.Y_axis,
            end_pose_data.end_pose.Z_axis,
            end_pose_data.end_pose.RX_axis,
            end_pose_data.end_pose.RY_axis,
            end_pose_data.end_pose.RZ_axis
        ],
        'gripper': gripper_data.gripper_state.grippers_angle
    }
    
    recorded_data.append(record)
    time.sleep(1.0 / recording_rate)  # 5ms = 200 Hz

print(f"Recorded {len(recorded_data)} data points")
```

### Example 2: Playing Back Recorded Joint Positions
```python
import time
from piper_sdk import *

# Initialize
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable robot
while not piper.EnablePiper():
    time.sleep(0.01)

# Set to joint control mode
piper.MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=50, is_mit_mode=0x00)

# Playback loop (assuming recorded_data exists)
for record in recorded_data:
    # Send joint command
    piper.JointCtrl(
        joint_1=record['joints'][0],
        joint_2=record['joints'][1],
        joint_3=record['joints'][2],
        joint_4=record['joints'][3],
        joint_5=record['joints'][4],
        joint_6=record['joints'][5]
    )
    
    # Send gripper command
    piper.GripperCtrl(
        gripper_angle=record['gripper'],
        gripper_effort=1000,
        gripper_code=0x01,
        set_zero=0x00
    )
    
    # Maintain playback rate
    time.sleep(0.005)  # 5ms = 200 Hz
```

### Example 3: Enabling MIT Mode for Manual Teaching
```python
import time
from piper_sdk import *

# Initialize
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable robot
while not piper.EnablePiper():
    time.sleep(0.01)

# Set to MIT mode (allows manual movement with low resistance)
piper.MotionCtrl_2(
    ctrl_mode=0x01,
    move_mode=0x01,
    move_spd_rate_ctrl=100,
    is_mit_mode=0xAD  # MIT mode enabled
)

print("Robot is now in MIT mode - you can move it manually")
print("Recording will capture positions as you move the arm")

# Now record while in MIT mode
while True:
    joint_data = piper.GetArmJointMsgs()
    print(f"J1: {joint_data.joint_state.joint_1 * 0.001:.2f}°")
    time.sleep(0.1)
```

---

## Important Notes

### 1. Update Rates
- **High-speed messages**: Joint state, end pose, high-speed motor info
  - Can be read at up to **200 Hz** (5ms intervals)
  - Typical usage: 100-200 Hz for recording
  
- **Low-speed messages**: Motor temperatures, voltages, status flags
  - Updated at lower rates (10-50 Hz typical)
  - Not critical for recording/playback

### 2. Control Loop Timing
- When sending commands, maintain consistent timing (e.g., 5ms = 200 Hz)
- Use `time.sleep()` to control loop rate
- The robot controller interpolates between commanded positions

### 3. Mode Switching
- Always call `MotionCtrl_2()` before sending position commands to set the appropriate mode
- Wait briefly after mode changes for the robot to respond
- After setting to teaching mode, you must reset and re-enable before normal control

### 4. Safety
- Always check robot status before sending commands
- Monitor for errors using `GetArmStatus()`
- Respect joint limits (see joint limits table above)
- Use appropriate speed percentages (start with 30-50% for testing)

### 5. CAN Bus Requirements
- Ensure CAN bus is properly configured before running (see `can_config.MD`)
- Use `detect_arm.py` to verify robot connection
- CAN port name is typically `can0` on Linux, varies on Windows

### 6. Data Storage Considerations
- At 200 Hz, you'll generate ~200 records per second
- Each record contains: 6 joints + 6 pose values + 1 gripper = 13 values
- Consider using efficient storage formats (numpy arrays, HDF5, etc.)
- For long recordings, implement data compression or sampling strategies

### 7. Coordinate Systems
- Joint angles follow standard robotic conventions
- Cartesian coordinates are relative to the robot base
- Euler angles use XYZ rotation order (Roll-Pitch-Yaw)
- Gripper position is the opening distance (0 = closed, max = fully open)

---

## Additional Resources

### SDK Files Reference
- **Interface**: `piper_sdk/interface/piper_interface_v2.py` - Main API
- **Messages**: `piper_sdk/piper_msgs/msg_v2/` - Message definitions
- **Demos**: `piper_sdk/demo/V2/` - Example scripts
- **Documentation**: `piper_sdk/asserts/V2/INTERFACE_V2.MD` - Detailed interface docs

### Key Demo Files for Reference
- `detect_arm.py` - Real-time robot monitoring and status display
- `piper_read_joint_state.py` - Reading joint angles
- `piper_read_end_pose.py` - Reading end-effector pose
- `piper_read_tcp_pose.py` - TCP offset calculations
- `piper_ctrl_joint.py` - Joint control example
- `piper_set_mit.py` - MIT mode configuration

---

## Quick Reference: Essential Methods

```python
# Connection
piper = C_PiperInterface_V2()
piper.ConnectPort()

# Enable/Disable
piper.EnablePiper()
piper.DisablePiper()

# Reading (Recording)
joint_data = piper.GetArmJointMsgs()
end_pose = piper.GetArmEndPoseMsgs()
gripper = piper.GetArmGripperMsgs()
status = piper.GetArmStatus()
high_spd = piper.GetArmHighSpdInfoMsgs()

# Control Mode
piper.MotionCtrl_2(ctrl_mode, move_mode, speed_percent, is_mit_mode)

# Sending Commands (Playback)
piper.JointCtrl(j1, j2, j3, j4, j5, j6)
piper.EndPoseCtrl(x, y, z, rx, ry, rz)
piper.GripperCtrl(angle, effort, code, set_zero)

# Version Info
sdk_ver = piper.GetCurrentSDKVersion()
interface_ver = piper.GetCurrentInterfaceVersion()
firmware_ver = piper.GetPiperFirmwareVersion()
```

---

**Document Version:** 1.0  
**Last Updated:** December 1, 2025  
**SDK Version:** 0.6.1+  
**Interface Version:** V2


