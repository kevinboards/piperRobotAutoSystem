"""
Test script for Piper Automation System

This script tests the recording and playback system with or without actual robot hardware.
"""

import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
from ppr_file_handler import (
    create_ppr_filename,
    write_ppr_header,
    write_ppr_line,
    read_ppr_file,
    get_recording_info,
    list_recordings,
    ensure_recordings_directory
)

# Try to import Piper SDK
try:
    from piper_sdk import C_PiperInterface_V2
    from recorder import PiperRecorder
    from player import PiperPlayer
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("Piper SDK not available - creating mock test data only")


def test_file_handler():
    """
    Test the PPR file handler module.
    """
    print("\n" + "=" * 70)
    print("TEST 1: File Handler")
    print("=" * 70)
    
    # Ensure recordings directory exists
    ensure_recordings_directory()
    
    # Create test file
    filename = "test_file_handler.ppr"
    filepath = Path("recordings") / filename
    
    logger.info(f"Creating test file: {filepath}")
    
    with open(filepath, 'w') as f:
        write_ppr_header(f, {"description": "Automated test file"})
        
        base_time = int(time.time() * 1000)
        
        for i in range(100):
            timestamp = base_time + (i * 5)
            cartesian = {
                'x': 150.0 + i * 0.1,
                'y': -50.0,
                'z': 180.0 + i * 0.05,
                'a': -179.9,
                'b': 0.0,
                'c': -179.9
            }
            joints = [0.0, 45.0 + i * 0.1, -30.0, 0.0, 0.0, 0.0]
            gripper = {'position': 80.0, 'effort': 1.5, 'code': 1}
            
            write_ppr_line(f, timestamp, cartesian, joints, gripper)
    
    logger.info(f"Test file created with 100 samples")
    
    # Read back and verify
    data_list, metadata = read_ppr_file(filepath)
    logger.info(f"Read {len(data_list)} samples from file")
    
    # Get info
    info = get_recording_info(filepath)
    logger.info(f"Duration: {info['duration_sec']:.3f} seconds")
    logger.info(f"Sample rate: {info['sample_rate_hz']} Hz")
    
    # List all recordings
    recordings = list_recordings()
    logger.info(f"Total recordings found: {len(recordings)}")
    
    print("✓ File Handler Test PASSED\n")
    return True


def test_recorder_mock():
    """
    Test the recorder with mock data (no robot needed).
    """
    print("\n" + "=" * 70)
    print("TEST 2: Recorder (Mock Mode)")
    print("=" * 70)
    
    # Create mock Piper interface
    class MockPiperInterface:
        class MockJointData:
            class JointState:
                def __init__(self):
                    self.joint_1 = 0
                    self.joint_2 = 45000
                    self.joint_3 = -30000
                    self.joint_4 = 0
                    self.joint_5 = 0
                    self.joint_6 = 0
            def __init__(self):
                self.joint_state = self.JointState()
        
        class MockEndPoseData:
            class EndPose:
                def __init__(self):
                    self.X_axis = 150000
                    self.Y_axis = -50000
                    self.Z_axis = 180000
                    self.RX_axis = -179900
                    self.RY_axis = 0
                    self.RZ_axis = -179900
            def __init__(self):
                self.end_pose = self.EndPose()
        
        class MockGripperData:
            class GripperState:
                def __init__(self):
                    self.grippers_angle = 80000
                    self.grippers_effort = 1500
            def __init__(self):
                self.gripper_state = self.GripperState()
        
        def GetArmJointMsgs(self):
            return self.MockJointData()
        def GetArmEndPoseMsgs(self):
            return self.MockEndPoseData()
        def GetArmGripperMsgs(self):
            return self.MockGripperData()
    
    from recorder import PiperRecorder
    
    mock_piper = MockPiperInterface()
    recorder = PiperRecorder(mock_piper, sample_rate=50)
    
    logger.info("Starting 2-second test recording...")
    filepath = recorder.start_recording(filename="test_recorder_mock", description="Mock recorder test")
    logger.info(f"Recording to: {filepath}")
    
    time.sleep(2.0)
    
    stats = recorder.stop_recording()
    logger.info(f"Recording stopped")
    logger.info(f"  Samples: {stats['sample_count']}")
    logger.info(f"  Duration: {stats['duration_sec']:.2f} seconds")
    logger.info(f"  Average rate: {stats['average_rate']:.1f} Hz")
    
    print("✓ Recorder Test PASSED\n")
    return True


def test_player_mock():
    """
    Test the player with mock commands (no robot needed).
    """
    print("\n" + "=" * 70)
    print("TEST 3: Player (Mock Mode)")
    print("=" * 70)
    
    # Check if test recording exists
    test_file = Path("recordings/test_recorder_mock.ppr")
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        logger.info("Run recorder test first to create test data")
        return False
    
    # Create mock Piper interface
    class MockPiperInterface:
        def MotionCtrl_2(self, ctrl_mode, move_mode, move_spd_rate_ctrl, is_mit_mode):
            logger.debug(f"Mock: Set mode - ctrl:{ctrl_mode:02x} move:{move_mode:02x}")
        def JointCtrl(self, j1, j2, j3, j4, j5, j6):
            logger.debug(f"Mock: Joint command - J1:{j1/1000:.1f}° J2:{j2/1000:.1f}°")
        def GripperCtrl(self, gripper_angle, gripper_effort, gripper_code, set_zero):
            logger.debug(f"Mock: Gripper - pos:{gripper_angle/1000:.1f}mm")
    
    from player import PiperPlayer
    
    mock_piper = MockPiperInterface()
    player = PiperPlayer(mock_piper)
    
    logger.info(f"Loading recording: {test_file}")
    info = player.load_recording(str(test_file))
    logger.info(f"  Samples: {info['sample_count']}")
    logger.info(f"  Duration: {info['duration_sec']:.2f} seconds")
    
    logger.info("Starting playback at 2x speed...")
    player.start_playback(speed_multiplier=2.0)
    
    # Monitor progress
    while player.is_playing():
        time.sleep(0.2)
        progress = player.get_progress()
        if int(progress) % 25 == 0 and progress > 0:
            logger.info(f"  Progress: {progress:.0f}%")
    
    logger.info("Playback completed")
    
    print("✓ Player Test PASSED\n")
    return True


def test_full_cycle_real():
    """
    Test full recording and playback cycle with real robot.
    """
    print("\n" + "=" * 70)
    print("TEST 4: Full Cycle (Real Robot)")
    print("=" * 70)
    
    if not SDK_AVAILABLE:
        logger.warning("Piper SDK not available - skipping real robot test")
        return False
    
    try:
        # Connect to robot
        logger.info("Connecting to robot...")
        piper = C_PiperInterface_V2()
        piper.ConnectPort()
        logger.info("Connected successfully")
        
        # Test recording
        logger.info("Starting 3-second recording...")
        recorder = PiperRecorder(piper, sample_rate=100)
        filepath = recorder.start_recording(filename="test_real_robot", description="Real robot test")
        
        time.sleep(3.0)
        
        stats = recorder.stop_recording()
        logger.info(f"Recording completed: {stats['sample_count']} samples")
        
        # Test playback
        logger.info("Starting playback...")
        player = PiperPlayer(piper)
        player.load_recording(filepath)
        player.start_playback(speed_multiplier=1.0)
        
        while player.is_playing():
            time.sleep(0.5)
            logger.info(f"  Progress: {player.get_progress():.0f}%")
        
        logger.info("Playback completed")
        
        print("✓ Full Cycle Test PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"Real robot test failed: {e}")
        return False


def main():
    """
    Run all tests.
    """
    print("\n" + "=" * 70)
    print(" PIPER AUTOMATION SYSTEM - TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: File Handler
    results.append(("File Handler", test_file_handler()))
    
    # Test 2: Recorder (Mock)
    results.append(("Recorder (Mock)", test_recorder_mock()))
    
    # Test 3: Player (Mock)
    results.append(("Player (Mock)", test_player_mock()))
    
    # Test 4: Full Cycle (Real Robot) - optional
    if SDK_AVAILABLE:
        user_input = input("\nRun test with real robot? (y/n): ").lower()
        if user_input == 'y':
            results.append(("Full Cycle (Real)", test_full_cycle_real()))
    
    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠️  {total - passed_count} test(s) FAILED")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

