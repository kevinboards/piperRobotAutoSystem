"""
Timeline Playback Engine for Piper Robot Automation System V2.

Plays entire timeline sequences with:
- Sequential clip playback
- Gap handling (robot holds position)
- Trim application
- Per-clip speed multipliers
- Progress tracking
"""

import asyncio
import time
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

try:
    from piper_sdk import C_PiperInterface_V2
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from timeline import Timeline, TimelineClip
from ppr_file_handler import read_ppr_file
from clip_editor import apply_trim_to_data


logger = logging.getLogger(__name__)


class TimelinePlayer:
    """
    Timeline playback engine.
    
    Plays timeline sequences by:
    1. Loading each clip's recording data
    2. Applying trims
    3. Playing at specified speed
    4. Handling gaps (holding position)
    5. Tracking progress
    """
    
    def __init__(
        self,
        piper_interface: Optional[C_PiperInterface_V2],
        timeline: Timeline,
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """
        Initialize timeline player.
        
        Args:
            piper_interface: Piper robot interface (None for simulation)
            timeline: Timeline to play
            on_progress: Callback for progress updates (position, clip_name)
            on_complete: Callback when playback completes
        """
        self.piper = piper_interface
        self.timeline = timeline
        self.on_progress = on_progress
        self.on_complete = on_complete
        
        # Playback state
        self.is_playing = False
        self.is_paused = False
        self.should_stop = False
        self.current_position = 0.0  # seconds
        self.current_clip_index = 0
        
        self.logger = logging.getLogger(__name__)
    
    async def play(self, start_position: float = 0.0):
        """
        Play the timeline from a specific position.
        
        Args:
            start_position: Starting position in seconds
        """
        if not self.piper and SDK_AVAILABLE:
            self.logger.error("No robot interface available")
            return
        
        if not self.timeline.enabled_clips:
            self.logger.warning("No clips to play in timeline")
            return
        
        self.is_playing = True
        self.is_paused = False
        self.should_stop = False
        self.current_position = start_position
        
        self.logger.info(f"Starting timeline playback from {start_position:.2f}s")
        
        try:
            # Initialize robot if available
            if self.piper:
                await self._initialize_robot()
            
            # Get sorted clips
            clips = self.timeline.get_sorted_clips()
            
            # Play each clip in sequence
            for i, clip in enumerate(clips):
                if self.should_stop:
                    break
                
                if not clip.enabled:
                    continue
                
                self.current_clip_index = i
                
                # Check if we should play this clip (based on start_position)
                if clip.end_time < start_position:
                    continue  # Skip clips before start position
                
                # Handle gap before this clip
                if i > 0:
                    previous_clip = clips[i - 1]
                    if clip.start_time > previous_clip.end_time:
                        gap_duration = clip.start_time - previous_clip.end_time
                        await self._play_gap(gap_duration)
                        if self.should_stop:
                            break
                
                # Play the clip
                await self._play_clip(clip)
                if self.should_stop:
                    break
            
            # Playback complete
            self.is_playing = False
            self.logger.info("Timeline playback completed")
            
            if self.on_complete:
                self.on_complete()
                
        except Exception as e:
            self.logger.error(f"Error during timeline playback: {e}")
            self.is_playing = False
            raise
    
    async def _initialize_robot(self):
        """Initialize robot for playback."""
        self.logger.info("Initializing robot for timeline playback")
        
        # Set to slave mode
        self.piper.MasterSlaveConfig(0xFC, 0, 0, 0)
        await asyncio.sleep(0.2)
        
        # Enable robot
        enable_attempts = 0
        while not self.piper.EnablePiper():
            await asyncio.sleep(0.01)
            enable_attempts += 1
            if enable_attempts >= 100:
                raise RuntimeError("Failed to enable robot")
        
        await asyncio.sleep(0.1)
        
        # Initialize gripper
        self.piper.GripperCtrl(0, 1000, 0x02, 0)  # Clear errors
        await asyncio.sleep(0.1)
        self.piper.GripperCtrl(0, 1000, 0x01, 0)  # Enable
        await asyncio.sleep(0.1)
        
        self.logger.info("Robot initialized successfully")
    
    async def _play_clip(self, clip: TimelineClip):
        """
        Play a single clip.
        
        Args:
            clip: Clip to play
        """
        self.logger.info(f"Playing clip: {clip.name} (speed: {clip.speed_multiplier}x)")
        
        # Load recording data
        if not Path(clip.recording_file).exists():
            self.logger.error(f"Recording file not found: {clip.recording_file}")
            return
        
        try:
            data, metadata = read_ppr_file(clip.recording_file)
            if not data:
                self.logger.error(f"No data in recording: {clip.recording_file}")
                return
            
            # Apply trims
            if clip.trim_start > 0 or clip.trim_end > 0:
                data = apply_trim_to_data(data, clip.trim_start, clip.trim_end)
                self.logger.info(f"Applied trims: start={clip.trim_start:.2f}s, end={clip.trim_end:.2f}s")
            
            # Calculate playback interval based on speed
            base_interval = 0.005  # 5ms = 200 Hz
            interval = base_interval / clip.speed_multiplier
            
            # Play each data point
            for i, point in enumerate(data):
                if self.should_stop:
                    break
                
                # Handle pause
                while self.is_paused and not self.should_stop:
                    await asyncio.sleep(0.1)
                
                if self.should_stop:
                    break
                
                # Send position to robot
                if self.piper:
                    await self._send_position(point)
                
                # Update progress
                self.current_position = clip.start_time + (i / len(data)) * clip.duration
                if self.on_progress:
                    self.on_progress(self.current_position, clip.name)
                
                # Wait for next point
                await asyncio.sleep(interval)
                
        except Exception as e:
            self.logger.error(f"Error playing clip {clip.name}: {e}")
            raise
    
    async def _send_position(self, point: Dict[str, Any]):
        """
        Send position command to robot.
        
        Args:
            point: Data point with joint angles and gripper state
        """
        try:
            # Set control mode before every command (critical!)
            self.piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
            
            # Send joint angles
            joints = point.get('joint_angles', {})
            j1 = joints.get('joint_1', 0.0)
            j2 = joints.get('joint_2', 0.0)
            j3 = joints.get('joint_3', 0.0)
            j4 = joints.get('joint_4', 0.0)
            j5 = joints.get('joint_5', 0.0)
            j6 = joints.get('joint_6', 0.0)
            
            self.piper.JointCtrl(j1, j2, j3, j4, j5, j6)
            
            # Send gripper command
            gripper = point.get('gripper', {})
            gripper_angle = gripper.get('angle', 0.0)
            gripper_effort = max(0, min(abs(gripper.get('effort', 1000)), 5000))
            gripper_code = gripper.get('status', 0x01)
            
            self.piper.GripperCtrl(gripper_angle, gripper_effort, gripper_code, 0)
            
        except Exception as e:
            self.logger.error(f"Error sending position: {e}")
            # Continue playback even if one position fails
    
    async def _play_gap(self, duration: float):
        """
        Play a gap (hold current position).
        
        Args:
            duration: Gap duration in seconds
        """
        self.logger.info(f"Playing gap: {duration:.2f}s")
        
        # Hold position for the gap duration
        start_time = time.time()
        interval = 0.005  # 5ms
        
        while (time.time() - start_time) < duration:
            if self.should_stop:
                break
            
            # Handle pause
            while self.is_paused and not self.should_stop:
                await asyncio.sleep(0.1)
            
            if self.should_stop:
                break
            
            # Update progress
            elapsed = time.time() - start_time
            # Position during gap is the start of the gap
            if self.on_progress:
                gap_position = self.current_position + elapsed
                self.on_progress(gap_position, "Gap (holding position)")
            
            await asyncio.sleep(interval)
        
        self.current_position += duration
    
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self.is_paused = True
            self.logger.info("Timeline playback paused")
    
    def resume(self):
        """Resume playback."""
        if self.is_playing and self.is_paused:
            self.is_paused = False
            self.logger.info("Timeline playback resumed")
    
    def stop(self):
        """Stop playback."""
        self.should_stop = True
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0
        self.logger.info("Timeline playback stopped")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current playback progress.
        
        Returns:
            Dictionary with progress info
        """
        total_duration = self.timeline.total_duration
        progress_percent = (self.current_position / total_duration * 100) if total_duration > 0 else 0
        
        return {
            'current_position': self.current_position,
            'total_duration': total_duration,
            'progress_percent': progress_percent,
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_clip_index': self.current_clip_index
        }

