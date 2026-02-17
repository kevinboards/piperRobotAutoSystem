# Piper SDK Functionality Reference for AI Agents

This document provides a comprehensive overview of the Piper Robot Arm SDK capabilities for quick reference.

---

## Table of Contents
1. [SDK Installation](#sdk-installation)
2. [Basic Setup](#basic-setup)
3. [Core Interface Methods](#core-interface-methods)
4. [Motion Control](#motion-control)
5. [Reading Robot State](#reading-robot-state)
6. [Configuration & Settings](#configuration--settings)
7. [Gripper Control](#gripper-control)
8. [Advanced Features](#advanced-features)
9. [Common Usage Patterns](#common-usage-patterns)

---

## SDK Installation

```bash
# Install dependencies
pip3 install python-can

# Install piper_sdk
pip3 install piper_sdk

# Or install from source
git clone https://github.com/agilexrobotics/piper_sdk.git
cd piper_sdk
pip3 install .
```

---

## Basic Setup

### Initialize Interface

```python
from piper_sdk import *
import time

# Create interface instance
piper = C_PiperInterface_V2(
    can_name="can0",              # CAN port name
    judge_flag=False,              # Set False for non-official CAN modules
    can_auto_init=True,            # Auto-initialize CAN bus
    dh_is_offset=1,                # 1 for firmware >= S-V1.6-3, 0 for older
    start_sdk_joint_limit=False,   # Enable SDK joint limits
    start_sdk_gripper_limit=False, # Enable SDK gripper limits
    logger_level=LogLevel.WARNING, # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL, SILENT)
    log_to_file=False,             # Enable file logging
    log_file_path=None             # Custom log file path
)

# Connect to robot
piper.ConnectPort()

# Enable robot (required before control)
while not piper.EnablePiper():
    time.sleep(0.01)
```

---

## Core Interface Methods

### Connection & Enable/Disable

| Method | Description | Example |
|--------|-------------|---------|
| `ConnectPort()` | Enable CAN send/receive threads | `piper.ConnectPort()` |
| `DisconnectPort()` | Disconnect from robot | `piper.DisconnectPort()` |
| `EnablePiper()` | Enable robot for control | `piper.EnablePiper()` |
| `DisablePiper()` | Disable robot | `piper.DisablePiper()` |
| `ResetRobot()` | Reset robot (required after teaching mode) | `piper.ResetRobot()` |
| `StopRobot()` | Emergency stop | `piper.StopRobot()` |

### Master/Slave Mode

```python
# Set to slave mode (for receiving commands)
piper.MasterSlaveConfig(0xFC, 0, 0, 0)

# Set to master mode (teaching mode)
piper.MasterSlaveConfig(0xFC, 1, 0, 0)
```

**Note**: Robot must be restarted after mode change.

---

## Motion Control

### Joint Control

Control individual joints (angles in radians, converted to internal units):

```python
# Conversion factor: radians to internal units
factor = 57295.7795  # 1000*180/π

# Set joint positions (in radians)
joint_angles = [0.2, 0.2, -0.2, 0.3, -0.2, 0.5]
j0 = round(joint_angles[0] * factor)
j1 = round(joint_angles[1] * factor)
j2 = round(joint_angles[2] * factor)
j3 = round(joint_angles[3] * factor)
j4 = round(joint_angles[4] * factor)
j5 = round(joint_angles[5] * factor)

# Set motion parameters and send joint command
piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)  # (mode, coord, velocity, user_frame)
piper.JointCtrl(j0, j1, j2, j3, j4, j5)
```

### Motion Planning Commands

| Method | Description | Parameters |
|--------|-------------|------------|
| `MotionCtrl_2()` | Set motion control parameters | mode, coord_type, velocity, user_frame |
| `JointCtrl()` | Control joint angles | j0, j1, j2, j3, j4, j5 |
| `EndPoseCtrl()` | Control end-effector pose | x, y, z, roll, pitch, yaw |
| `MoveJ()` | Joint space motion | target_joint_angles, speed |
| `MoveL()` | Linear motion in Cartesian space | target_pose, speed |
| `MoveC()` | Circular arc motion | via_pose, target_pose, speed |
| `MoveP()` | End-effector position control | x, y, z, rx, ry, rz |

### Go to Zero Position

```python
# Move robot to zero/home position
piper.GotoZeroPos()
```

---

## Reading Robot State

### Joint State

```python
# Read joint angles and states
joint_msg = piper.GetArmJointMsgs()
print(f"Time: {joint_msg.time_stamp}")
print(f"Frequency: {joint_msg.Hz} Hz")
print(f"Joints: {joint_msg.joint_state}")
```

### End-Effector Pose

```python
# Read end-effector pose (x, y, z, roll, pitch, yaw)
end_pose = piper.GetArmEndPoseMsgs()
print(f"Position: {end_pose.end_pose}")
```

### Robot Status

```python
# Read overall robot status
status = piper.GetArmStatus()
print(f"Status: {status}")
```

### Gripper State

```python
# Read gripper status
gripper_status = piper.GetArmGripperMsgs()
print(f"Gripper: {gripper_status}")
```

### Forward Kinematics

```python
# Calculate forward kinematics for given joint angles
fk_result = piper.GetArmFK(joint_angles)
```

### Firmware & Version Info

```python
# Get firmware version
firmware_version = piper.GetPiperFirmwareVersion()

# Get SDK version
sdk_version = PiperSDKVersion
```

### High/Low-Speed Messages

```python
# Read high-frequency messages (joint states, end pose, etc.)
high_msg = piper.GetArmHighSpdFeedBackMsgs()

# Read low-frequency messages (status, parameters, etc.)
low_msg = piper.GetArmLowSpdFeedBackMsgs()
```

---

## Configuration & Settings

### Motor Limits

```python
# Set maximum motor speed
piper.SetMotorMaxSpeed(joint_id, max_speed)

# Set maximum motor acceleration
piper.SetMotorMaxAcc(joint_id, max_acc)

# Set motor angle limits
piper.SetMotorAngleLimit(joint_id, min_angle, max_angle)

# Read motor limits
max_speed_limits = piper.GetMotorMaxSpeed()
max_acc_limits = piper.GetMotorMaxAcc()
angle_limits = piper.GetMotorAngleLimit()
```

### End Load Configuration

```python
# Set end-effector load parameters (mass, center of mass)
piper.SetEndLoad(mass, cx, cy, cz)
```

### Installation Position

```python
# Set installation position/orientation
piper.SetInstallationPosition(position_code)
```

### Collision Protection

```python
# Read collision protection level
collision_level = piper.GetCrashProtectionLevel()
```

### SDK Parameters

```python
# Enable/disable SDK joint limits
piper.SetSDKJointLimit(enable=True)

# Enable/disable SDK gripper limits
piper.SetSDKGripperLimit(enable=True)
```

### Logging

```python
# Set log level dynamically
piper.SetLogLevel(LogLevel.DEBUG)

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL, SILENT
```

---

## Gripper Control

### Basic Gripper Control

```python
# Control gripper
# position: 0-1000 (0=open, 1000=closed)
# speed: gripper speed
# force: gripper force
# wait: wait for completion (0x00 or 0x01)
piper.GripperCtrl(position=500, speed=1000, force=0x01, wait=0)

# Examples:
piper.GripperCtrl(0, 1000, 0x01, 0)      # Open gripper
piper.GripperCtrl(1000, 1000, 0x01, 0)   # Close gripper
piper.GripperCtrl(500, 1000, 0x01, 0)    # Half-open
```

### Gripper Calibration

```python
# Set gripper zero position
piper.SetGripperZero()
```

### Gripper Parameters (V2)

```python
# Set gripper parameters
piper.SetGripperParams(param_dict)

# Read gripper parameter feedback
gripper_params = piper.GetGripperParams()
```

---

## Advanced Features

### MIT Mode Control

**⚠️ WARNING**: MIT mode is an advanced feature. Misuse can damage the robot!

```python
# Enable MIT mode for individual joint (fastest response)
piper.SetMITMode(joint_id, enable=True)

# Control joint in MIT mode
piper.JointCtrlMIT(joint_id, position, velocity, kp, kd, torque)
```

### Multi-Robot Support

```python
# Create multiple interface instances for multiple robots
piper_left = C_PiperInterface_V2("can_left")
piper_right = C_PiperInterface_V2("can_right")

piper_left.ConnectPort()
piper_right.ConnectPort()

# Control independently
piper_left.EnablePiper()
piper_right.EnablePiper()
```

### CAN Bus Configuration

```python
# Set CAN parameters
piper.SetCANParams(param_dict)
```

---

## Common Usage Patterns

### Basic Control Loop (200Hz)

```python
from piper_sdk import *
import time

piper = C_PiperInterface_V2("can0")
piper.ConnectPort()

while not piper.EnablePiper():
    time.sleep(0.01)

factor = 57295.7795

while True:
    # Set desired joint positions
    joint_angles = [0.2, 0.1, -0.1, 0.0, 0.1, 0.2]
    
    j0 = round(joint_angles[0] * factor)
    j1 = round(joint_angles[1] * factor)
    j2 = round(joint_angles[2] * factor)
    j3 = round(joint_angles[3] * factor)
    j4 = round(joint_angles[4] * factor)
    j5 = round(joint_angles[5] * factor)
    
    piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
    piper.JointCtrl(j0, j1, j2, j3, j4, j5)
    
    # Read current state
    status = piper.GetArmStatus()
    joint_state = piper.GetArmJointMsgs()
    
    time.sleep(0.005)  # 200Hz control loop
```

### Read-Only Monitoring

```python
from piper_sdk import *
import time

# Initialize in slave mode for reading
piper = C_PiperInterface_V2("can0")
piper.ConnectPort()

# Ensure robot is in slave mode
piper.MasterSlaveConfig(0xFC, 0, 0, 0)

while True:
    # Read various states
    joints = piper.GetArmJointMsgs()
    end_pose = piper.GetArmEndPoseMsgs()
    status = piper.GetArmStatus()
    gripper = piper.GetArmGripperMsgs()
    
    print(f"Joints: {joints.joint_state}")
    print(f"End Pose: {end_pose.end_pose}")
    print(f"Status: {status.arm_status}")
    
    time.sleep(0.005)  # 200Hz
```

### Pick and Place Example

```python
from piper_sdk import *
import time

piper = C_PiperInterface_V2("can0")
piper.ConnectPort()

while not piper.EnablePiper():
    time.sleep(0.01)

factor = 57295.7795

# Open gripper
piper.GripperCtrl(0, 1000, 0x01, 0)
time.sleep(1.0)

# Move to pick position
pick_position = [0.2, 0.3, -0.1, 0.0, 0.2, 0.1]
j0 = round(pick_position[0] * factor)
j1 = round(pick_position[1] * factor)
j2 = round(pick_position[2] * factor)
j3 = round(pick_position[3] * factor)
j4 = round(pick_position[4] * factor)
j5 = round(pick_position[5] * factor)

piper.MotionCtrl_2(0x01, 0x01, 50, 0x00)
piper.JointCtrl(j0, j1, j2, j3, j4, j5)
time.sleep(2.0)

# Close gripper
piper.GripperCtrl(1000, 1000, 0x01, 0)
time.sleep(1.0)

# Move to place position
place_position = [0.1, 0.2, -0.2, 0.0, 0.1, 0.2]
j0 = round(place_position[0] * factor)
j1 = round(place_position[1] * factor)
j2 = round(place_position[2] * factor)
j3 = round(place_position[3] * factor)
j4 = round(place_position[4] * factor)
j5 = round(place_position[5] * factor)

piper.MotionCtrl_2(0x01, 0x01, 50, 0x00)
piper.JointCtrl(j0, j1, j2, j3, j4, j5)
time.sleep(2.0)

# Open gripper
piper.GripperCtrl(0, 1000, 0x01, 0)
time.sleep(1.0)

# Return to zero
piper.GotoZeroPos()
```

### Safe Shutdown

```python
# Disable robot
piper.DisablePiper()

# Disconnect
piper.DisconnectPort()
```

---

## Key Notes for AI Agents

1. **Always enable the robot** before sending control commands: `piper.EnablePiper()`

2. **Unit conversions**:
   - Joint angles: radians → multiply by `57295.7795` (1000*180/π)
   - Gripper position: 0-1000 (0=open, 1000=closed)

3. **Control frequency**: Typically 200Hz (5ms sleep between commands)

4. **Master/Slave mode**: 
   - Slave mode (0): Robot receives commands from SDK
   - Master mode (1): Teaching mode, robot doesn't respond to SDK
   - **Restart required** after mode change

5. **First message is default**: The first feedback message after connection contains default values (usually zeros)

6. **CAN setup required**: Ensure CAN interface is properly configured and activated before using SDK

7. **Motion control sequence**:
   ```python
   piper.MotionCtrl_2(mode, coord, velocity, frame)  # Set motion parameters
   piper.JointCtrl(j0, j1, j2, j3, j4, j5)          # Send joint command
   ```

8. **Error handling**: Check return values and status messages for errors

9. **Thread safety**: The SDK handles CAN communication in separate threads

10. **Resource cleanup**: Always call `DisconnectPort()` when done

---

## Quick Reference - Method Categories

### Connection Management
- `ConnectPort()`, `DisconnectPort()`

### Enable/Disable
- `EnablePiper()`, `DisablePiper()`, `ResetRobot()`, `StopRobot()`

### Motion Control
- `JointCtrl()`, `EndPoseCtrl()`, `MoveJ()`, `MoveL()`, `MoveC()`, `MoveP()`, `GotoZeroPos()`

### State Reading
- `GetArmJointMsgs()`, `GetArmEndPoseMsgs()`, `GetArmStatus()`, `GetArmGripperMsgs()`

### Gripper
- `GripperCtrl()`, `SetGripperZero()`, `GetGripperParams()`, `SetGripperParams()`

### Configuration
- `SetMotorMaxSpeed()`, `SetMotorMaxAcc()`, `SetMotorAngleLimit()`, `SetEndLoad()`, `SetInstallationPosition()`

### Mode Control
- `MasterSlaveConfig()`, `SetMITMode()`, `JointCtrlMIT()`

### Version/Info
- `GetPiperFirmwareVersion()`, `PiperSDKVersion`

---

## Demo Files Reference

All demo files are located in: `piper_sdk/piper_sdk/demo/V2/`

Run demos after installing SDK:
```bash
python3 piper_ctrl_enable.py
python3 piper_read_joint_state.py
```

See [Demo README](piper_sdk/demo/V2/README.MD) for complete list of available examples.

---

## Additional Resources

- **Interface Documentation**: [INTERFACE_V2.MD](asserts/V2/INTERFACE_V2.MD)
- **Changelog**: [CHANGELOG.MD](CHANGELOG.MD)
- **Q&A**: [Q&A.MD](asserts/Q&A.MD)
- **CAN Configuration**: [can_config.MD](asserts/can_config.MD)
- **Dual Robot Setup**: [double_piper.MD](asserts/double_piper.MD)

---

**Version**: Compatible with firmware >= V1.5-2  
**SDK Version**: 0.1.9+  
**Python**: 3.6, 3.8, 3.10 tested  
**Platform**: Ubuntu 18.04, 20.04, 22.04 (Windows support via appropriate CAN drivers)
