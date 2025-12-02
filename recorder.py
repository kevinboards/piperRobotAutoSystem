"""
Piper Robot Recorder Module

Records robot movements in real-time and saves to PPR format files.
"""

import time
import threading
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    from piper_sdk import C_PiperInterface_V2
except ImportError:
    # For testing without SDK
    C_PiperInterface_V2 = None

from ppr_file_handler import (
    create_ppr_filename,
    get_full_filepath,
    write_ppr_header,
    write_ppr_line,
    ensure_recordings_directory
)


# Constants
DEFAULT_SAMPLE_RATE = 200  # Hz
WRITE_BUFFER_SIZE = 20  # Write to disk every N samples


class PiperRecorder:
    """
    Records robot movements in real-time to PPR format files.
    
    Features:
    - Real-time recording at up to 200 Hz
    - Buffered writing for performance
    - Thread-safe operation
    - Automatic file management
    """
    
    def __init__(self, piper_interface: 'C_PiperInterface_V2', sample_rate: int = DEFAULT_SAMPLE_RATE):
        """
        Initialize the recorder with a Piper SDK interface.
        
        Args:
            piper_interface: Connected Piper robot interface instance
            sample_rate: Recording sample rate in Hz (default: 200)
        """
        self.piper = piper_interface
        self.sample_rate = sample_rate
        self.sample_interval = 1.0 / sample_rate
        
        # State variables
        self._is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # File handling
        self._current_file = None
        self._current_filepath: Optional[Path] = None
        self._write_buffer: List[tuple] = []
        
        # Statistics
        self._sample_count = 0
        self._start_time = 0
        self._recording_start_timestamp = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def _init_gripper(self):
        """
        Initialize gripper: clear errors and enable.
        Should be called at the start of each recording session.
        """
        try:
            import time
            self.logger.info("Initializing gripper...")
            
            # Clear errors and disable
            self.piper.GripperCtrl(0, 1000, 0x02, 0)
            time.sleep(0.1)
            
            # Enable gripper
            self.piper.GripperCtrl(0, 1000, 0x01, 0)
            time.sleep(0.1)
            
            self.logger.info("Gripper initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Gripper initialization failed (may not be critical): {e}")
        
    def start_recording(self, filename: Optional[str] = None, description: str = "", 
                       init_gripper: bool = True, enable_robot: bool = True) -> str:
        """
        Start recording robot movements.
        
        Args:
            filename: Optional custom filename (without extension). 
                     If None, generates timestamp-based filename.
            description: Optional description to include in file header
            init_gripper: If True, initializes gripper (clear errors and enable)
            enable_robot: If True, enables the robot before recording (recommended)
        
        Returns:
            Full path to the recording file
            
        Raises:
            RuntimeError: If already recording or if piper interface is not connected
        """
        if self._is_recording:
            raise RuntimeError("Already recording. Stop current recording first.")
        
        # Enable robot if requested (critical for robot responsiveness)
        if enable_robot:
            try:
                # Set to slave mode (ready to receive commands)
                self.logger.info("Setting robot to slave mode...")
                self.piper.MasterSlaveConfig(0xFC, 0, 0, 0)
                time.sleep(0.2)
                
                # Enable robot
                self.logger.info("Enabling robot...")
                enable_attempts = 0
                max_attempts = 100
                while not self.piper.EnablePiper():
                    time.sleep(0.01)
                    enable_attempts += 1
                    if enable_attempts >= max_attempts:
                        raise RuntimeError("Failed to enable robot after 100 attempts")
                self.logger.info("Robot enabled successfully")
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Failed to enable robot: {e}")
                raise
        
        # Initialize gripper if requested
        if init_gripper:
            self._init_gripper()
        
        # Ensure recordings directory exists
        ensure_recordings_directory()
        
        # Generate filename if not provided
        if filename is None:
            filename = create_ppr_filename()
        
        # Get full filepath
        self._current_filepath = get_full_filepath(filename)
        
        self.logger.info(f"Starting recording: {self._current_filepath}")
        
        # Open file and write header
        try:
            self._current_file = open(self._current_filepath, 'w')
            metadata = {
                "sample_rate_hz": self.sample_rate,
                "description": description
            }
            write_ppr_header(self._current_file, metadata)
            
        except Exception as e:
            self.logger.error(f"Failed to create recording file: {e}")
            raise
        
        # Initialize state
        self._sample_count = 0
        self._start_time = time.time()
        self._recording_start_timestamp = int(time.time() * 1000)
        self._stop_event.clear()
        self._is_recording = True
        self._write_buffer = []
        
        # Start recording thread
        self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._recording_thread.start()
        
        return str(self._current_filepath)
    
    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop the current recording and close the file.
        
        Returns:
            Dictionary with recording statistics:
                - filename: Name of the saved file
                - filepath: Full path to the file
                - sample_count: Number of samples recorded
                - duration_sec: Duration in seconds
                - average_rate: Actual average sample rate
        """
        if not self._is_recording:
            self.logger.warning("No recording in progress")
            return {}
        
        self.logger.info("Stopping recording...")
        
        # Signal thread to stop
        self._stop_event.set()
        self._is_recording = False
        
        # Wait for thread to finish
        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=2.0)
        
        # Flush any remaining buffered data
        self._flush_buffer()
        
        # Close file
        if self._current_file:
            self._current_file.close()
            self._current_file = None
        
        # Calculate statistics
        duration = time.time() - self._start_time
        avg_rate = self._sample_count / duration if duration > 0 else 0
        
        stats = {
            'filename': self._current_filepath.name if self._current_filepath else "",
            'filepath': str(self._current_filepath) if self._current_filepath else "",
            'sample_count': self._sample_count,
            'duration_sec': duration,
            'average_rate': avg_rate
        }
        
        self.logger.info(f"Recording stopped: {stats}")
        
        return stats
    
    def _record_loop(self):
        """
        Main recording loop - runs in separate thread.
        Continuously reads robot state and writes to file.
        """
        self.logger.info(f"Recording loop started at {self.sample_rate} Hz")
        
        next_sample_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Wait until it's time for next sample
                current_time = time.time()
                if current_time < next_sample_time:
                    sleep_time = next_sample_time - current_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                # Get current robot state
                state = self._get_current_state()
                
                if state:
                    # Add to write buffer
                    self._write_buffer.append(state)
                    self._sample_count += 1
                    
                    # Flush buffer if it's full
                    if len(self._write_buffer) >= WRITE_BUFFER_SIZE:
                        self._flush_buffer()
                
                # Schedule next sample
                next_sample_time += self.sample_interval
                
                # Prevent drift accumulation
                if time.time() > next_sample_time + self.sample_interval:
                    next_sample_time = time.time()
                
            except Exception as e:
                self.logger.error(f"Error in recording loop: {e}")
                # Continue recording despite errors
        
        self.logger.info("Recording loop ended")
    
    def _get_current_state(self) -> Optional[tuple]:
        """
        Read current robot state from Piper SDK.
        
        Returns:
            Tuple of (timestamp, cartesian, joints, gripper) or None if read fails
        """
        try:
            # Get current timestamp
            timestamp = int(time.time() * 1000)
            
            # Read joint angles
            joint_data = self.piper.GetArmJointMsgs()
            joints = [
                joint_data.joint_state.joint_1 * 0.001,  # Convert from 0.001 degrees to degrees
                joint_data.joint_state.joint_2 * 0.001,
                joint_data.joint_state.joint_3 * 0.001,
                joint_data.joint_state.joint_4 * 0.001,
                joint_data.joint_state.joint_5 * 0.001,
                joint_data.joint_state.joint_6 * 0.001,
            ]
            
            # Read end-effector pose
            end_pose_data = self.piper.GetArmEndPoseMsgs()
            cartesian = {
                'x': end_pose_data.end_pose.X_axis * 0.001,   # Convert from 0.001 mm to mm
                'y': end_pose_data.end_pose.Y_axis * 0.001,
                'z': end_pose_data.end_pose.Z_axis * 0.001,
                'a': end_pose_data.end_pose.RX_axis * 0.001,  # Convert from 0.001 degrees to degrees
                'b': end_pose_data.end_pose.RY_axis * 0.001,
                'c': end_pose_data.end_pose.RZ_axis * 0.001,
            }
            
            # Read gripper state
            gripper_data = self.piper.GetArmGripperMsgs()
            
            # Convert gripper values to standard units and ensure valid ranges
            gripper_position = gripper_data.gripper_state.grippers_angle * 0.001  # Convert to mm
            gripper_effort_raw = gripper_data.gripper_state.grippers_effort * 0.001  # Convert to N·m
            
            # Ensure gripper effort is positive (SDK may return negative values)
            gripper_effort = abs(gripper_effort_raw)
            
            gripper = {
                'position': gripper_position,
                'effort': gripper_effort,
                'code': 1  # Assume enabled if reading successfully
            }
            
            return (timestamp, cartesian, joints, gripper)
            
        except Exception as e:
            self.logger.error(f"Failed to read robot state: {e}")
            return None
    
    def _flush_buffer(self):
        """
        Write all buffered samples to disk.
        """
        if not self._write_buffer or not self._current_file:
            return
        
        try:
            for timestamp, cartesian, joints, gripper in self._write_buffer:
                write_ppr_line(self._current_file, timestamp, cartesian, joints, gripper)
            
            # Flush to disk
            self._current_file.flush()
            
            # Clear buffer
            self._write_buffer = []
            
        except Exception as e:
            self.logger.error(f"Failed to write buffer to disk: {e}")
    
    def is_recording(self) -> bool:
        """
        Check if currently recording.
        
        Returns:
            True if recording is in progress
        """
        return self._is_recording
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """
        Get current recording statistics.
        
        Returns:
            Dictionary with current stats (sample_count, duration, rate, etc.)
        """
        if not self._is_recording:
            return {}
        
        duration = time.time() - self._start_time
        current_rate = self._sample_count / duration if duration > 0 else 0
        
        return {
            'is_recording': True,
            'sample_count': self._sample_count,
            'duration_sec': duration,
            'current_rate': current_rate,
            'target_rate': self.sample_rate,
            'filename': self._current_filepath.name if self._current_filepath else ""
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Test the recorder with mock data (when SDK is not available).
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Piper Recorder Test")
    print("=" * 50)
    
    # Mock Piper interface for testing
    class MockPiperInterface:
        """Mock interface for testing without actual robot"""
        
        class MockJointData:
            class JointState:
                def __init__(self):
                    self.joint_1 = 0
                    self.joint_2 = 45000  # 45 degrees in 0.001 degree units
                    self.joint_3 = -30000
                    self.joint_4 = 0
                    self.joint_5 = 0
                    self.joint_6 = 0
            
            def __init__(self):
                self.joint_state = self.JointState()
        
        class MockEndPoseData:
            class EndPose:
                def __init__(self):
                    self.X_axis = 150000  # 150mm in 0.001mm units
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
                    self.grippers_angle = 80000  # 80mm in 0.001mm units
                    self.grippers_effort = 1500  # 1.5 N·m in 0.001 N·m units
            
            def __init__(self):
                self.gripper_state = self.GripperState()
        
        def GetArmJointMsgs(self):
            return self.MockJointData()
        
        def GetArmEndPoseMsgs(self):
            return self.MockEndPoseData()
        
        def GetArmGripperMsgs(self):
            return self.MockGripperData()
    
    # Create mock interface
    mock_piper = MockPiperInterface()
    
    # Create recorder
    recorder = PiperRecorder(mock_piper, sample_rate=50)  # Use lower rate for testing
    
    print("Starting 3-second test recording...")
    filepath = recorder.start_recording(filename="test_recording", description="Test recording with mock data")
    print(f"Recording to: {filepath}")
    print()
    
    # Record for 3 seconds, showing progress
    for i in range(3):
        time.sleep(1)
        stats = recorder.get_recording_stats()
        print(f"Recording... {i+1}s - Samples: {stats['sample_count']}, Rate: {stats['current_rate']:.1f} Hz")
    
    print()
    print("Stopping recording...")
    final_stats = recorder.stop_recording()
    
    print()
    print("Recording completed!")
    print(f"  File: {final_stats['filename']}")
    print(f"  Samples: {final_stats['sample_count']}")
    print(f"  Duration: {final_stats['duration_sec']:.2f} seconds")
    print(f"  Average Rate: {final_stats['average_rate']:.1f} Hz")
    
    print()
    print("=" * 50)
    print("Test complete! Check the recordings/ directory for the output file.")

