"""
Robot Movement Test Script

Simple script to verify the robot responds to basic movement commands.
Use this to diagnose if the robot is working properly before using playback.
"""

import time
import logging

try:
    from piper_sdk import C_PiperInterface_V2
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("ERROR: Piper SDK not installed. Run: pip install piper_sdk")
    exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_movement():
    """
    Test basic robot movement with simple back-and-forth motion.
    """
    print("=" * 70)
    print(" ROBOT MOVEMENT TEST")
    print("=" * 70)
    print()
    print("This script will test if the robot responds to basic commands.")
    print("The robot will move slightly back and forth.")
    print()
    print("⚠️  WARNING: Make sure the workspace is clear!")
    print()
    
    response = input("Continue with movement test? (y/n): ").lower()
    if response != 'y':
        print("Test cancelled.")
        return
    
    try:
        # Step 1: Connect
        print()
        logger.info("Step 1: Connecting to robot...")
        piper = C_PiperInterface_V2()
        piper.ConnectPort()
        time.sleep(0.1)
        logger.info("✓ Connected")
        
        # Step 2: Set to slave mode (ready to receive commands)
        print()
        logger.info("Step 2: Setting robot to slave mode (ready to receive commands)...")
        piper.MasterSlaveConfig(0xFC, 0, 0, 0)
        time.sleep(0.2)
        logger.info("✓ Slave mode configured")
        
        # Step 3: Reset robot
        print()
        logger.info("Step 3: Resetting robot...")
        piper.ResetRobot()
        time.sleep(0.5)  # Wait for reset to complete
        logger.info("✓ Robot reset")
        
        # Step 4: Enable
        print()
        logger.info("Step 4: Enabling robot...")
        enable_attempts = 0
        while not piper.EnablePiper():
            time.sleep(0.01)
            enable_attempts += 1
            if enable_attempts >= 100:
                logger.error("Failed to enable robot!")
                return
        logger.info("✓ Robot enabled")
        time.sleep(0.1)
        
        # Step 5: Initialize gripper
        print()
        logger.info("Step 5: Initializing gripper...")
        piper.GripperCtrl(0, 1000, 0x02, 0)  # Clear errors
        time.sleep(0.1)
        piper.GripperCtrl(0, 1000, 0x01, 0)  # Enable
        time.sleep(0.1)
        logger.info("✓ Gripper initialized")
        
        # Step 6: Read current position
        print()
        logger.info("Step 6: Reading current position...")
        joint_data = piper.GetArmJointMsgs()
        current_j1 = joint_data.joint_state.joint_1
        current_j2 = joint_data.joint_state.joint_2
        current_j3 = joint_data.joint_state.joint_3
        logger.info(f"Current position: J1={current_j1/1000:.2f}° J2={current_j2/1000:.2f}° J3={current_j3/1000:.2f}°")
        
        # Step 7: Test movement
        print()
        logger.info("Step 7: Testing movement...")
        logger.info("The robot will move slightly and return to starting position")
        
        # Position 1: Current position (no movement yet)
        logger.info("Position 1: Current position (holding)")
        for i in range(10):
            piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)  # 30% speed
            piper.JointCtrl(current_j1, current_j2, current_j3, 0, 0, 0)
            piper.GripperCtrl(0, 1000, 0x01, 0)
            
            if i == 0:  # Log status only once
                status = piper.GetArmStatus()
                logger.info(f"  Status: ctrl_mode={status.arm_status.ctrl_mode} arm_status={status.arm_status.arm_status}")
            
            time.sleep(0.1)
        
        # Position 2: Move J1 by 5 degrees
        logger.info("Position 2: Moving J1 by +5 degrees...")
        target_j1 = current_j1 + 5000  # +5 degrees in 0.001 degree units
        for _ in range(50):
            piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)  # 30% speed
            piper.JointCtrl(target_j1, current_j2, current_j3, 0, 0, 0)
            piper.GripperCtrl(0, 1000, 0x01, 0)
            time.sleep(0.1)
        
        logger.info("Waiting 2 seconds at position...")
        time.sleep(2)
        
        # Position 3: Return to original
        logger.info("Position 3: Returning to original position...")
        for _ in range(50):
            piper.MotionCtrl_2(0x01, 0x01, 30, 0x00)  # 30% speed
            piper.JointCtrl(current_j1, current_j2, current_j3, 0, 0, 0)
            piper.GripperCtrl(0, 1000, 0x01, 0)
            time.sleep(0.1)
        
        # Step 8: Verify final position
        print()
        logger.info("Step 8: Verifying final position...")
        time.sleep(0.5)
        final_joint_data = piper.GetArmJointMsgs()
        final_j1 = final_joint_data.joint_state.joint_1
        logger.info(f"Final position: J1={final_j1/1000:.2f}°")
        
        # Step 9: Disable
        print()
        logger.info("Step 9: Disabling robot...")
        while piper.DisablePiper():
            time.sleep(0.01)
        logger.info("✓ Robot disabled")
        
        # Success
        print()
        print("=" * 70)
        print(" ✓ MOVEMENT TEST COMPLETE!")
        print("=" * 70)
        print()
        print("If the robot moved:")
        print("  ✓ Robot is working properly")
        print("  ✓ Issue is likely in playback system")
        print()
        print("If the robot did NOT move:")
        print("  ✗ Check robot hardware")
        print("  ✗ Check CAN bus connection")
        print("  ✗ Check robot is powered on")
        print("  ✗ Check for emergency stop")
        print()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 70)
        print(" ✗ TEST FAILED")
        print("=" * 70)
        print()
        print("Common issues:")
        print("  - Robot not connected")
        print("  - CAN bus not configured")
        print("  - Robot in emergency stop")
        print("  - Hardware fault")
        print()


if __name__ == "__main__":
    test_basic_movement()

