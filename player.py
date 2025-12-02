"""
Piper Robot Player Module

Loads and replays recorded robot movements from PPR format files.
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

from ppr_file_handler import read_ppr_file, get_recording_info


# Constants
DEFAULT_SPEED_MULTIPLIER = 1.0
COMMAND_INTERVAL = 0.005  # 5ms = 200 Hz


class PiperPlayer:
    """
    Plays back recorded robot movements from PPR files.
    
    Features:
    - Accurate timing based on timestamps
    - Speed control (slow motion / fast forward)
    - Pause/resume capability
    - Progress tracking
    - Thread-safe operation
    """
    
    def __init__(self, piper_interface: 'C_PiperInterface_V2'):
        """
        Initialize the player with a Piper SDK interface.
        
        Args:
            piper_interface: Connected Piper robot interface instance
        """
        self.piper = piper_interface
        
        # State variables
        self._is_playing = False
        self._is_paused = False
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Loaded data
        self._data_list: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
        self._current_filepath: Optional[Path] = None
        
        # Playback parameters
        self._speed_multiplier = DEFAULT_SPEED_MULTIPLIER
        self._current_index = 0
        self._start_playback_time = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def _init_gripper(self):
        """
        Initialize gripper: clear errors and enable.
        Should be called before playback to ensure gripper responds properly.
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
    
    def load_recording(self, filepath: str) -> Dict[str, Any]:
        """
        Load a PPR recording file into memory.
        
        Args:
            filepath: Path to the .ppr file to load
        
        Returns:
            Dictionary with recording info (duration, sample_count, etc.)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if self._is_playing:
            raise RuntimeError("Cannot load file while playback is in progress")
        
        self.logger.info(f"Loading recording: {filepath}")
        
        try:
            # Load and parse file
            self._data_list, self._metadata = read_ppr_file(filepath)
            self._current_filepath = Path(filepath)
            
            # Get recording info
            info = get_recording_info(filepath)
            
            self.logger.info(f"Loaded {len(self._data_list)} samples, duration: {info['duration_sec']:.2f}s")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to load recording: {e}")
            raise
    
    def start_playback(self, speed_multiplier: float = DEFAULT_SPEED_MULTIPLIER, 
                      init_gripper: bool = True) -> None:
        """
        Start playing back the loaded recording.
        
        Args:
            speed_multiplier: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
            init_gripper: If True, initializes gripper before playback (recommended)
            
        Raises:
            RuntimeError: If no recording is loaded or already playing
        """
        if not self._data_list:
            raise RuntimeError("No recording loaded. Load a file first.")
        
        if self._is_playing:
            raise RuntimeError("Playback already in progress")
        
        # Verify robot is enabled and prepare for playback
        try:
            # Set to slave mode (ready to receive commands)
            self.logger.info("Setting robot to slave mode...")
            self.piper.MasterSlaveConfig(0xFC, 0, 0, 0)
            time.sleep(0.2)
            
            # Enable the robot (critical!)
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
            
            # Initialize gripper if requested
            if init_gripper:
                self._init_gripper()
            
        except Exception as e:
            self.logger.error(f"Failed to prepare robot: {e}")
            raise RuntimeError("Failed to prepare robot for playback. Is it connected and enabled?")
        
        self._speed_multiplier = speed_multiplier
        self._current_index = 0
        self._stop_event.clear()
        self._pause_event.clear()
        self._is_playing = True
        self._is_paused = False
        
        self.logger.info(f"Starting playback at {speed_multiplier}x speed")
        
        # Start playback thread
        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()
    
    def stop_playback(self) -> None:
        """
        Stop the current playback.
        """
        if not self._is_playing:
            return
        
        self.logger.info("Stopping playback")
        
        # Signal thread to stop
        self._stop_event.set()
        self._is_playing = False
        self._is_paused = False
        
        # Wait for thread to finish
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
    
    def pause_playback(self) -> None:
        """
        Pause the current playback.
        """
        if not self._is_playing or self._is_paused:
            return
        
        self.logger.info("Pausing playback")
        self._is_paused = True
        self._pause_event.set()
    
    def resume_playback(self) -> None:
        """
        Resume paused playback.
        """
        if not self._is_playing or not self._is_paused:
            return
        
        self.logger.info("Resuming playback")
        self._is_paused = False
        self._pause_event.clear()
    
    def _playback_loop(self):
        """
        Main playback loop - runs in separate thread.
        Sends recorded positions to robot at fixed rate (like the demos).
        """
        self.logger.info("Playback loop started")
        
        if not self._data_list:
            self.logger.error("No data to play back")
            return
        
        # Use fixed rate like demos (0.005 seconds = 200 Hz)
        # Adjust by speed multiplier
        base_interval = 0.005  # 5ms between commands (like demo)
        interval = base_interval / self._speed_multiplier
        
        self.logger.info(f"Playback interval: {interval*1000:.2f}ms ({1/interval:.1f} Hz)")
        
        try:
            for i, data_point in enumerate(self._data_list):
                # Check for stop signal
                if self._stop_event.is_set():
                    self.logger.info("Playback stopped by user")
                    break
                
                # Handle pause
                while self._pause_event.is_set():
                    time.sleep(0.1)
                    if self._stop_event.is_set():
                        break
                
                self._current_index = i
                
                # Send position command to robot
                self._send_position(data_point)
                
                # Fixed delay between commands (like the demo)
                time.sleep(interval)
            
            self.logger.info("Playback completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during playback: {e}")
        
        finally:
            self._is_playing = False
            self._is_paused = False
    
    def _send_position(self, data_point: Dict[str, Any]) -> None:
        """
        Send a position command to the robot.
        
        Args:
            data_point: Dictionary with cartesian, joints, and gripper data
        """
        try:
            # CRITICAL: Set motion control mode before EVERY command (as shown in demo)
            self.piper.MotionCtrl_2(
                ctrl_mode=0x01,  # CAN control
                move_mode=0x01,  # MOVE J (joint mode)
                move_spd_rate_ctrl=100,  # 100% speed for accurate playback
                is_mit_mode=0x00  # Normal mode
            )
            
            # Extract joint angles
            joints = data_point['joints']
            
            # Convert from degrees to SDK units (0.001 degrees)
            j1 = int(joints[0] * 1000)
            j2 = int(joints[1] * 1000)
            j3 = int(joints[2] * 1000)
            j4 = int(joints[3] * 1000)
            j5 = int(joints[4] * 1000)
            j6 = int(joints[5] * 1000)
            
            # Debug: Log first few commands to verify values
            if self._current_index < 5:
                self.logger.info(f"Sending position #{self._current_index}: J1={j1/1000:.2f}° J2={j2/1000:.2f}° J3={j3/1000:.2f}°")
            
            # Send joint control command
            self.piper.JointCtrl(j1, j2, j3, j4, j5, j6)
            
            # Extract gripper data
            gripper = data_point['gripper']
            gripper_pos = int(gripper['position'] * 1000)  # Convert mm to 0.001mm
            gripper_effort = int(gripper['effort'] * 1000)  # Convert N·m to 0.001 N·m
            gripper_code = int(gripper['code'])
            
            # Clamp gripper effort to valid range (0-5000)
            gripper_effort = max(0, min(abs(gripper_effort), 5000))
            
            # Send gripper command
            self.piper.GripperCtrl(
                gripper_angle=abs(gripper_pos),
                gripper_effort=gripper_effort,
                gripper_code=gripper_code,
                set_zero=0x00
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send position: {e}")
    
    def is_playing(self) -> bool:
        """
        Check if currently playing.
        
        Returns:
            True if playback is in progress
        """
        return self._is_playing
    
    def is_paused(self) -> bool:
        """
        Check if playback is paused.
        
        Returns:
            True if playback is paused
        """
        return self._is_paused
    
    def get_progress(self) -> float:
        """
        Get current playback progress.
        
        Returns:
            Progress as percentage (0.0 to 100.0)
        """
        if not self._data_list:
            return 0.0
        
        return (self._current_index / len(self._data_list)) * 100.0
    
    def get_playback_info(self) -> Dict[str, Any]:
        """
        Get current playback information.
        
        Returns:
            Dictionary with playback stats
        """
        if not self._data_list:
            return {'loaded': False}
        
        total_samples = len(self._data_list)
        progress_pct = (self._current_index / total_samples * 100.0) if total_samples > 0 else 0.0
        
        return {
            'loaded': True,
            'is_playing': self._is_playing,
            'is_paused': self._is_paused,
            'filename': self._current_filepath.name if self._current_filepath else "",
            'total_samples': total_samples,
            'current_sample': self._current_index,
            'progress_percent': progress_pct,
            'speed_multiplier': self._speed_multiplier
        }
    
    def set_speed(self, speed_multiplier: float) -> None:
        """
        Change playback speed (can be done during playback).
        
        Args:
            speed_multiplier: New speed multiplier (0.1 to 4.0)
        """
        if speed_multiplier < 0.1 or speed_multiplier > 4.0:
            raise ValueError("Speed multiplier must be between 0.1 and 4.0")
        
        self._speed_multiplier = speed_multiplier
        self.logger.info(f"Playback speed set to {speed_multiplier}x")
    
    def is_loaded(self) -> bool:
        """
        Check if a recording is loaded.
        
        Returns:
            True if a recording is loaded and ready to play
        """
        return len(self._data_list) > 0


# Example usage and testing
if __name__ == "__main__":
    """
    Test the player with a recorded file.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Piper Player Test")
    print("=" * 50)
    
    # Mock Piper interface for testing
    class MockPiperInterface:
        """Mock interface for testing without actual robot"""
        
        def MotionCtrl_2(self, ctrl_mode, move_mode, move_spd_rate_ctrl, is_mit_mode):
            print(f"Mock: Set mode - ctrl:{ctrl_mode:02x} move:{move_mode:02x}")
        
        def JointCtrl(self, j1, j2, j3, j4, j5, j6):
            print(f"Mock: Joint command - J1:{j1/1000:.1f}° J2:{j2/1000:.1f}° ...")
        
        def GripperCtrl(self, gripper_angle, gripper_effort, gripper_code, set_zero):
            print(f"Mock: Gripper - pos:{gripper_angle/1000:.1f}mm effort:{gripper_effort/1000:.2f}N·m")
    
    # First, check if a test recording exists
    from pathlib import Path
    test_file = Path("recordings/test_recording.ppr")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Run the recorder test first to create a test recording.")
        print("=" * 50)
        exit(1)
    
    # Create mock interface
    mock_piper = MockPiperInterface()
    
    # Create player
    player = PiperPlayer(mock_piper)
    
    # Load recording
    print(f"Loading recording: {test_file}")
    info = player.load_recording(str(test_file))
    print(f"  Samples: {info['sample_count']}")
    print(f"  Duration: {info['duration_sec']:.2f} seconds")
    print(f"  Sample Rate: {info['sample_rate_hz']} Hz")
    print()
    
    # Start playback at 2x speed for faster testing
    print("Starting playback at 2x speed...")
    player.start_playback(speed_multiplier=2.0)
    
    # Monitor progress
    while player.is_playing():
        time.sleep(0.5)
        progress = player.get_progress()
        info = player.get_playback_info()
        print(f"  Progress: {progress:.1f}% ({info['current_sample']}/{info['total_samples']})")
    
    print()
    print("Playback completed!")
    print("=" * 50)

