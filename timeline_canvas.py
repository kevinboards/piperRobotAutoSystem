"""
Timeline Canvas - Visual timeline editor for Piper Robot Automation System V2.

Provides a visual, interactive timeline canvas for arranging and editing clips.
Inspired by video/audio editing software like Adobe Premiere Pro and Audacity.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Tuple, Dict, Any
import logging

from timeline import Timeline, TimelineClip


logger = logging.getLogger(__name__)


class TimelineCanvas(tk.Canvas):
    """
    Interactive timeline canvas for visual clip arrangement.
    
    Features:
    - Visual clip representation with colors
    - Drag-and-drop clip positioning
    - Playhead indicator
    - Time ruler
    - Zoom and pan
    - Clip selection
    - Gap visualization
    """
    
    # Visual constants
    RULER_HEIGHT = 30
    CLIP_TRACK_HEIGHT = 80
    CLIP_MARGIN = 5
    PIXELS_PER_SECOND = 50  # Default zoom level
    MIN_PIXELS_PER_SECOND = 10
    MAX_PIXELS_PER_SECOND = 200
    
    def __init__(
        self,
        parent,
        timeline: Optional[Timeline] = None,
        on_clip_select: Optional[Callable[[Optional[TimelineClip]], None]] = None,
        on_clip_move: Optional[Callable[[str, float], None]] = None,
        on_playhead_change: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        """
        Initialize timeline canvas.
        
        Args:
            parent: Parent widget
            timeline: Timeline to display
            on_clip_select: Callback when clip is selected (clip or None)
            on_clip_move: Callback when clip is moved (clip_id, new_start_time)
            on_playhead_change: Callback when playhead position changes
        """
        # Set default canvas properties
        kwargs.setdefault('bg', '#2E2E2E')
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('relief', 'flat')
        
        super().__init__(parent, **kwargs)
        
        self.timeline = timeline or Timeline(name="New Timeline")
        self.on_clip_select = on_clip_select
        self.on_clip_move = on_clip_move
        self.on_playhead_change = on_playhead_change
        
        # Visual state
        self.pixels_per_second = self.PIXELS_PER_SECOND
        self.scroll_offset_x = 0
        self.playhead_position = 0.0  # seconds
        self.selected_clip_id: Optional[str] = None
        
        # Drag state
        self.dragging_clip_id: Optional[str] = None
        self.drag_start_x = 0
        self.drag_start_time = 0.0
        
        # Clip visual cache
        self.clip_rectangles: Dict[str, int] = {}  # clip_id -> canvas item id
        
        # Bind events
        self._bind_events()
        
        # Initial draw
        self.after(100, self.redraw)
    
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse events
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Double-Button-1>', self._on_double_click)
        
        # Mouse wheel for zoom
        self.bind('<MouseWheel>', self._on_mouse_wheel)
        self.bind('<Button-4>', self._on_mouse_wheel)  # Linux
        self.bind('<Button-5>', self._on_mouse_wheel)  # Linux
        
        # Keyboard shortcuts
        self.bind('<Delete>', self._on_delete_key)
        self.bind('<plus>', lambda e: self.zoom_in())
        self.bind('<minus>', lambda e: self.zoom_out())
        self.bind('<Home>', lambda e: self.set_playhead_position(0.0))
        self.bind('<End>', lambda e: self.set_playhead_position(self.timeline.total_duration))
        
        # Configure resize
        self.bind('<Configure>', self._on_resize)
    
    def set_timeline(self, timeline: Timeline):
        """
        Set a new timeline to display.
        
        Args:
            timeline: Timeline to display
        """
        self.timeline = timeline
        self.selected_clip_id = None
        self.playhead_position = 0.0
        self.redraw()
    
    def redraw(self):
        """Redraw the entire timeline."""
        self.delete('all')
        self.clip_rectangles.clear()
        
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 200
        
        # Draw ruler
        self._draw_ruler(canvas_width)
        
        # Draw clips
        self._draw_clips(canvas_width, canvas_height)
        
        # Draw gaps
        self._draw_gaps(canvas_height)
        
        # Draw playhead
        self._draw_playhead(canvas_height)
    
    def _draw_ruler(self, canvas_width: int):
        """Draw time ruler at top of canvas."""
        # Background
        self.create_rectangle(
            0, 0, canvas_width, self.RULER_HEIGHT,
            fill='#3E3E3E', outline='#555555', tags='ruler'
        )
        
        # Calculate time range visible
        start_time = self.scroll_offset_x / self.pixels_per_second
        end_time = (self.scroll_offset_x + canvas_width) / self.pixels_per_second
        
        # Determine tick spacing based on zoom level
        if self.pixels_per_second >= 100:
            major_interval = 1.0  # 1 second
            minor_interval = 0.2  # 200ms
        elif self.pixels_per_second >= 50:
            major_interval = 2.0
            minor_interval = 0.5
        elif self.pixels_per_second >= 20:
            major_interval = 5.0
            minor_interval = 1.0
        else:
            major_interval = 10.0
            minor_interval = 2.0
        
        # Draw ticks
        current_time = int(start_time / major_interval) * major_interval
        while current_time <= end_time + major_interval:
            x = self._time_to_x(current_time)
            
            if 0 <= x <= canvas_width:
                # Major tick
                self.create_line(
                    x, self.RULER_HEIGHT - 10, x, self.RULER_HEIGHT,
                    fill='#CCCCCC', width=2, tags='ruler'
                )
                
                # Time label
                time_str = self._format_time(current_time)
                self.create_text(
                    x, self.RULER_HEIGHT - 15,
                    text=time_str, fill='#FFFFFF',
                    font=('Segoe UI', 8), tags='ruler'
                )
            
            # Minor ticks
            for i in range(1, int(major_interval / minor_interval)):
                minor_time = current_time + (i * minor_interval)
                x_minor = self._time_to_x(minor_time)
                
                if 0 <= x_minor <= canvas_width:
                    self.create_line(
                        x_minor, self.RULER_HEIGHT - 5, x_minor, self.RULER_HEIGHT,
                        fill='#888888', width=1, tags='ruler'
                    )
            
            current_time += major_interval
    
    def _draw_clips(self, canvas_width: int, canvas_height: int):
        """Draw all clips on the timeline."""
        clip_y = self.RULER_HEIGHT + self.CLIP_MARGIN
        clip_height = self.CLIP_TRACK_HEIGHT - (2 * self.CLIP_MARGIN)
        
        for clip in self.timeline.get_sorted_clips():
            if not clip.enabled:
                continue
            
            # Calculate clip position
            x1 = self._time_to_x(clip.start_time)
            x2 = self._time_to_x(clip.end_time)
            
            # Skip if off-screen
            if x2 < 0 or x1 > canvas_width:
                continue
            
            # Draw clip rectangle
            is_selected = clip.id == self.selected_clip_id
            
            clip_rect = self._draw_clip(
                clip, x1, clip_y, x2 - x1, clip_height, is_selected
            )
            
            self.clip_rectangles[clip.id] = clip_rect
    
    def _draw_clip(
        self,
        clip: TimelineClip,
        x: float,
        y: float,
        width: float,
        height: float,
        selected: bool
    ) -> int:
        """
        Draw a single clip.
        
        Args:
            clip: Clip to draw
            x, y: Top-left position
            width, height: Dimensions
            selected: Whether clip is selected
            
        Returns:
            Canvas item ID
        """
        # Clip body
        fill_color = clip.color
        outline_color = '#FFEB3B' if selected else '#000000'
        outline_width = 3 if selected else 1
        
        rect = self.create_rectangle(
            x, y, x + width, y + height,
            fill=fill_color, outline=outline_color,
            width=outline_width, tags=('clip', f'clip_{clip.id}')
        )
        
        # Clip name
        text_x = x + 5
        text_y = y + 10
        
        self.create_text(
            text_x, text_y,
            text=clip.name, fill='#FFFFFF',
            font=('Segoe UI', 9, 'bold'),
            anchor='nw', tags=('clip', f'clip_{clip.id}')
        )
        
        # Clip info (duration, speed)
        info_text = f"{clip.duration:.1f}s"
        if clip.speed_multiplier != 1.0:
            info_text += f" • {clip.speed_multiplier}x"
        if clip.trim_start > 0 or clip.trim_end > 0:
            info_text += " • Trimmed"
        
        self.create_text(
            text_x, text_y + 15,
            text=info_text, fill='#EEEEEE',
            font=('Segoe UI', 7),
            anchor='nw', tags=('clip', f'clip_{clip.id}')
        )
        
        # Draw trim indicators if trimmed
        if clip.trim_start > 0 or clip.trim_end > 0:
            self._draw_trim_indicators(clip, x, y, width, height)
        
        return rect
    
    def _draw_trim_indicators(
        self,
        clip: TimelineClip,
        x: float,
        y: float,
        width: float,
        height: float
    ):
        """Draw visual indicators for trimmed portions."""
        if clip.original_duration <= 0:
            return
        
        # Calculate trim widths in pixels
        trim_start_width = (clip.trim_start / clip.original_duration) * width
        trim_end_width = (clip.trim_end / clip.original_duration) * width
        
        # Draw darker overlay for trimmed portions
        if clip.trim_start > 0:
            self.create_rectangle(
                x, y, x + trim_start_width, y + height,
                fill='#000000', stipple='gray50',
                outline='', tags=('clip', f'clip_{clip.id}')
            )
        
        if clip.trim_end > 0:
            self.create_rectangle(
                x + width - trim_end_width, y, x + width, y + height,
                fill='#000000', stipple='gray50',
                outline='', tags=('clip', f'clip_{clip.id}')
            )
    
    def _draw_gaps(self, canvas_height: int):
        """Draw gap indicators between clips."""
        gaps = self.timeline.get_gaps()
        
        for gap_start, gap_end in gaps:
            x1 = self._time_to_x(gap_start)
            x2 = self._time_to_x(gap_end)
            
            y = self.RULER_HEIGHT + self.CLIP_MARGIN
            height = self.CLIP_TRACK_HEIGHT - (2 * self.CLIP_MARGIN)
            
            # Draw gap region
            self.create_rectangle(
                x1, y, x2, y + height,
                fill='#1E1E1E', outline='#444444',
                dash=(4, 4), tags='gap'
            )
            
            # Gap label
            gap_duration = gap_end - gap_start
            label_x = (x1 + x2) / 2
            label_y = y + (height / 2)
            
            self.create_text(
                label_x, label_y,
                text=f"Gap\n{gap_duration:.1f}s",
                fill='#888888', font=('Segoe UI', 8),
                tags='gap'
            )
    
    def _draw_playhead(self, canvas_height: int):
        """Draw playhead indicator."""
        x = self._time_to_x(self.playhead_position)
        
        # Playhead line
        self.create_line(
            x, 0, x, canvas_height,
            fill='#FF0000', width=2, tags='playhead'
        )
        
        # Playhead handle (triangle at top)
        handle_size = 8
        self.create_polygon(
            x, self.RULER_HEIGHT,
            x - handle_size, self.RULER_HEIGHT - handle_size,
            x + handle_size, self.RULER_HEIGHT - handle_size,
            fill='#FF0000', outline='#FFFFFF', tags='playhead'
        )
    
    def _time_to_x(self, time: float) -> float:
        """Convert time (seconds) to canvas X coordinate."""
        return (time * self.pixels_per_second) - self.scroll_offset_x
    
    def _x_to_time(self, x: float) -> float:
        """Convert canvas X coordinate to time (seconds)."""
        return (x + self.scroll_offset_x) / self.pixels_per_second
    
    def _format_time(self, seconds: float) -> str:
        """Format time for display."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}:{secs:04.1f}"
    
    def _get_clip_at_position(self, x: float, y: float) -> Optional[TimelineClip]:
        """Get clip at canvas position."""
        # Check if in clip track
        clip_y_start = self.RULER_HEIGHT + self.CLIP_MARGIN
        clip_y_end = clip_y_start + self.CLIP_TRACK_HEIGHT - (2 * self.CLIP_MARGIN)
        
        if not (clip_y_start <= y <= clip_y_end):
            return None
        
        # Convert to time
        time = self._x_to_time(x)
        
        # Find clip at this time
        clips = self.timeline.get_clips_at_time(time)
        return clips[0] if clips else None
    
    def _on_click(self, event):
        """Handle mouse click."""
        clip = self._get_clip_at_position(event.x, event.y)
        
        if clip:
            # Start drag
            self.dragging_clip_id = clip.id
            self.drag_start_x = event.x
            self.drag_start_time = clip.start_time
            
            # Select clip
            self.select_clip(clip.id)
        else:
            # Check if clicked on ruler (set playhead)
            if event.y < self.RULER_HEIGHT:
                time = self._x_to_time(event.x)
                self.set_playhead_position(max(0, time))
            else:
                # Deselect
                self.select_clip(None)
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if self.dragging_clip_id:
            # Calculate new position
            dx = event.x - self.drag_start_x
            dt = dx / self.pixels_per_second
            new_time = max(0, self.drag_start_time + dt)
            
            # Move clip
            clip = self.timeline.get_clip_by_id(self.dragging_clip_id)
            if clip:
                clip.start_time = new_time
                self.redraw()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if self.dragging_clip_id and self.on_clip_move:
            clip = self.timeline.get_clip_by_id(self.dragging_clip_id)
            if clip:
                self.on_clip_move(clip.id, clip.start_time)
        
        self.dragging_clip_id = None
    
    def _on_double_click(self, event):
        """Handle double-click (edit clip)."""
        clip = self._get_clip_at_position(event.x, event.y)
        if clip and self.on_clip_select:
            self.on_clip_select(clip)
    
    def _on_delete_key(self, event):
        """Handle Delete key (remove selected clip)."""
        if self.selected_clip_id:
            self.timeline.remove_clip(self.selected_clip_id)
            self.selected_clip_id = None
            self.redraw()
            if self.on_clip_select:
                self.on_clip_select(None)
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:
            self.zoom_in()
        elif event.num == 5 or event.delta < 0:
            self.zoom_out()
    
    def _on_resize(self, event):
        """Handle canvas resize."""
        self.redraw()
    
    def select_clip(self, clip_id: Optional[str]):
        """
        Select a clip.
        
        Args:
            clip_id: Clip ID to select, or None to deselect
        """
        self.selected_clip_id = clip_id
        self.redraw()
        
        if self.on_clip_select:
            clip = self.timeline.get_clip_by_id(clip_id) if clip_id else None
            self.on_clip_select(clip)
    
    def set_playhead_position(self, time: float):
        """
        Set playhead position.
        
        Args:
            time: Time in seconds
        """
        self.playhead_position = max(0, time)
        self._draw_playhead(self.winfo_height())
        
        if self.on_playhead_change:
            self.on_playhead_change(self.playhead_position)
    
    def zoom_in(self):
        """Zoom in (show more detail)."""
        self.pixels_per_second = min(
            self.pixels_per_second * 1.5,
            self.MAX_PIXELS_PER_SECOND
        )
        self.redraw()
    
    def zoom_out(self):
        """Zoom out (show more time)."""
        self.pixels_per_second = max(
            self.pixels_per_second / 1.5,
            self.MIN_PIXELS_PER_SECOND
        )
        self.redraw()
    
    def zoom_to_fit(self):
        """Zoom to fit entire timeline in view."""
        if self.timeline.total_duration <= 0:
            return
        
        canvas_width = self.winfo_width()
        if canvas_width <= 1:
            canvas_width = 800
        
        # Calculate pixels per second to fit
        self.pixels_per_second = (canvas_width * 0.9) / self.timeline.total_duration
        self.pixels_per_second = max(
            self.MIN_PIXELS_PER_SECOND,
            min(self.pixels_per_second, self.MAX_PIXELS_PER_SECOND)
        )
        self.scroll_offset_x = 0
        self.redraw()
    
    def scroll_to_time(self, time: float):
        """
        Scroll to show a specific time.
        
        Args:
            time: Time in seconds
        """
        canvas_width = self.winfo_width()
        center_x = canvas_width / 2
        
        self.scroll_offset_x = (time * self.pixels_per_second) - center_x
        self.scroll_offset_x = max(0, self.scroll_offset_x)
        self.redraw()

