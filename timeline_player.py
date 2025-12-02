"""
Timeline Playback Engine for Piper Robot Automation System V2.

Simplified approach: Plays recordings sequentially using the existing V1 player.
Timeline serves as a visual organizer for Program 1, Program 2, Program 3, etc.
"""

import time
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import threading

try:
    from piper_sdk import C_PiperInterface_V2
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from timeline import Timeline, TimelineClip
from player import PiperPlayer


logger = logging.getLogger(__name__)


class TimelinePlayer:
    """
    Timeline playback engine.
    
    Simplified approach:
    - Plays each recording file sequentially
    - Uses existing PiperPlayer (proven to work)
    - Handles gaps by waiting
    - Timeline is visual organizer
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
        self.should_stop = False
        self.current_position = 0.0  # seconds
        self.current_clip_index = 0
        
        self.logger = logging.getLogger(__name__)
    
    def play_sync(self, start_position: float = 0.0):
        """
        Play the timeline (synchronous version for threading).
        
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
        self.should_stop = False
        self.current_position = start_position
        
        self.logger.info(f"Starting timeline playback from {start_position:.2f}s")
        
        try:
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
                        self._play_gap(gap_duration, previous_clip.end_time)
                        if self.should_stop:
                            break
                
                # Play the clip using V1 player
                self._play_clip(clip)
                if self.should_stop:
                    break
            
            # Playback complete
            self.is_playing = False
            self.logger.info("Timeline playback completed")
            
            if self.on_complete:
                self.on_complete()
                
        except Exception as e:
            self.logger.error(f"Error during timeline playback: {e}")
            import traceback
            traceback.print_exc()
            self.is_playing = False
            raise
    
    def _play_clip(self, clip: TimelineClip):
        """
        Play a single clip using the V1 player.
        
        Args:
            clip: Clip to play
        """
        self.logger.info(f"Playing clip: {clip.name} (speed: {clip.speed_multiplier}x)")
        
        # Load recording data
        if not Path(clip.recording_file).exists():
            self.logger.error(f"Recording file not found: {clip.recording_file}")
            return
        
        try:
            # Create V1 player for this clip
            player = PiperPlayer(
                self.piper,
                clip.recording_file,
                speed_multiplier=clip.speed_multiplier
            )
            
            # Load the recording
            player.load_recording()
            
            # Apply trims if needed
            # TODO: Add trim support to V1 player or filter data here
            
            # Start playback (synchronous)
            player.play()
            
            # Wait for playback to complete
            while player.is_playing():
                if self.should_stop:
                    player.stop()
                    break
                
                # Update progress
                progress_info = player.get_playback_info()
                samples_played = progress_info.get('current_sample', 0)
                total_samples = progress_info.get('total_samples', 1)
                
                if total_samples > 0:
                    clip_progress = samples_played / total_samples
                    self.current_position = clip.start_time + (clip_progress * clip.duration)
                    
                    if self.on_progress:
                        self.on_progress(self.current_position, clip.name)
                
                time.sleep(0.05)  # Check every 50ms
            
        except Exception as e:
            self.logger.error(f"Error playing clip {clip.name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _play_gap(self, duration: float, gap_start_time: float):
        """
        Play a gap (hold current position).
        
        Args:
            duration: Gap duration in seconds
            gap_start_time: Timeline position where gap starts
        """
        self.logger.info(f"Playing gap: {duration:.2f}s")
        
        # Simply wait for the gap duration
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            if self.should_stop:
                break
            
            # Update progress during gap
            elapsed = time.time() - start_time
            self.current_position = gap_start_time + elapsed
            
            if self.on_progress:
                self.on_progress(self.current_position, "Gap (holding position)")
            
            time.sleep(0.1)  # Update every 100ms
    
    def stop(self):
        """Stop playback."""
        self.should_stop = True
        self.is_playing = False
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
            'current_clip_index': self.current_clip_index
        }
