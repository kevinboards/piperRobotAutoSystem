"""
First-Time Gripper Setup Utility

Run this script ONCE when setting up a new Piper robot or after replacing the gripper.
This configures the gripper parameters required for proper operation.

Usage:
    python setup_gripper_first_time.py

Note: Only needs to be run once per robot/gripper. The settings are saved in the robot.
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


def setup_gripper_parameters(piper, teaching_range_per=100, max_range_config=70, teaching_friction=1):
    """
    Configure gripper parameters for first-time use.
    
    Args:
        piper: Connected Piper interface
        teaching_range_per: Teaching pendant range coefficient [100-200], default: 100
        max_range_config: Max control travel limit [0,70,100], default: 70 (70mm)
        teaching_friction: Teaching friction, default: 1
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Configuring gripper parameters...")
        logger.info(f"  Teaching range: {teaching_range_per}")
        logger.info(f"  Max range: {max_range_config}mm")
        logger.info(f"  Teaching friction: {teaching_friction}")
        
        # Send configuration command
        piper.GripperTeachingPendantParamConfig(
            teaching_range_per=teaching_range_per,
            max_range_config=max_range_config,
            teaching_friction=teaching_friction
        )
        
        time.sleep(0.5)
        
        # Request parameter feedback
        piper.ArmParamEnquiryAndConfig(4)
        
        time.sleep(0.5)
        
        # Verify configuration
        feedback = piper.GetGripperTeachingPendantParamFeedback()
        logger.info(f"Configuration sent successfully!")
        logger.info(f"Feedback: {feedback}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure gripper: {e}")
        return False


def initialize_gripper(piper):
    """
    Initialize gripper after configuration: clear errors and enable.
    
    Args:
        piper: Connected Piper interface
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Initializing gripper...")
        
        # Clear errors and disable
        piper.GripperCtrl(0, 1000, 0x02, 0)
        time.sleep(0.2)
        
        # Enable gripper
        piper.GripperCtrl(0, 1000, 0x01, 0)
        time.sleep(0.2)
        
        logger.info("Gripper initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize gripper: {e}")
        return False


def main():
    """
    Main setup routine.
    """
    print("=" * 70)
    print(" PIPER ROBOT - FIRST-TIME GRIPPER SETUP")
    print("=" * 70)
    print()
    print("This script configures the gripper for first-time use.")
    print("You only need to run this ONCE per robot/gripper.")
    print()
    print("WARNING: Make sure the gripper is properly attached before proceeding!")
    print()
    
    response = input("Continue with gripper setup? (y/n): ").lower()
    if response != 'y':
        print("Setup cancelled.")
        return
    
    print()
    logger.info("Connecting to robot...")
    
    try:
        # Connect to robot
        piper = C_PiperInterface_V2()
        piper.ConnectPort()
        logger.info("Connected successfully!")
        
        time.sleep(0.5)
        
        # Step 1: Configure gripper parameters
        print()
        logger.info("STEP 1: Configuring gripper parameters...")
        if not setup_gripper_parameters(piper):
            logger.error("Configuration failed!")
            return
        
        # Step 2: Initialize gripper
        print()
        logger.info("STEP 2: Initializing gripper...")
        if not initialize_gripper(piper):
            logger.error("Initialization failed!")
            return
        
        # Step 3: Test gripper
        print()
        logger.info("STEP 3: Testing gripper response...")
        
        for i in range(3):
            try:
                gripper_status = piper.GetArmGripperMsgs()
                logger.info(f"Gripper status reading #{i+1}: {gripper_status.gripper_state.grippers_angle * 0.001:.2f}mm")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not read gripper status: {e}")
        
        # Success!
        print()
        print("=" * 70)
        print(" ✓ GRIPPER SETUP COMPLETE!")
        print("=" * 70)
        print()
        print("The gripper is now configured and ready to use.")
        print("You do NOT need to run this script again unless:")
        print("  - You replace the gripper")
        print("  - You reset the robot to factory settings")
        print()
        print("You can now use the Piper Automation System:")
        print("  python main.py")
        print()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print()
        print("=" * 70)
        print(" ✗ SETUP FAILED")
        print("=" * 70)
        print()
        print("Please check:")
        print("  - Robot is powered on")
        print("  - CAN interface is configured")
        print("  - Gripper is properly connected")
        print("  - No hardware errors")
        print()


if __name__ == "__main__":
    main()

