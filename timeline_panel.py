"""
Timeline Panel - Complete timeline editor UI component.

Combines TimelineCanvas with controls for a full timeline editing experience.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import logging

from timeline import Timeline, TimelineClip, TimelineManager
from timeline_canvas import TimelineCanvas
from ppt_file_handler import save_timeline, load_timeline


logger = logging.getLogger(__name__)


class TimelinePanel(ttk.Frame):
    """
    Complete timeline panel with canvas and controls.
    
    Features:
    - Timeline canvas for visual editing
    - Transport controls (play, pause, stop)
    - Zoom controls
    - Timeline info display
    - File operations (new, load, save)
    """
    
    def __init__(
        self,
        parent,
        timeline: Optional[Timeline] = None,
        on_clip_select: Optional[Callable[[Optional[TimelineClip]], None]] = None,
        on_play: Optional[Callable[[], None]] = None,
        on_pause: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize timeline panel.
        
        Args:
            parent: Parent widget
            timeline: Initial timeline (optional)
            on_clip_select: Callback when clip selected
            on_play: Callback when play button clicked
            on_pause: Callback when pause button clicked
            on_stop: Callback when stop button clicked
        """
        super().__init__(parent, **kwargs)
        
        self.timeline = timeline or Timeline(name="New Timeline")
        self.timeline_manager = TimelineManager()
        
        self.on_clip_select = on_clip_select
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_stop = on_stop
        
        self.is_playing = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the timeline panel UI."""
        # Top control bar
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        self._build_controls(control_frame)
        
        # Timeline canvas
        canvas_frame = ttk.Frame(self, relief='sunken', borderwidth=2)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.timeline_canvas = TimelineCanvas(
            canvas_frame,
            timeline=self.timeline,
            on_clip_select=self._on_clip_select_internal,
            on_clip_move=self._on_clip_move,
            on_playhead_change=self._on_playhead_change,
            height=150
        )
        self.timeline_canvas.pack(fill='both', expand=True)
        
        # Bottom info bar
        info_frame = ttk.Frame(self)
        info_frame.pack(fill='x', padx=5, pady=2)
        
        self._build_info_bar(info_frame)
    
    def _build_controls(self, parent):
        """Build control buttons."""
        # File operations
        file_frame = ttk.LabelFrame(parent, text="Timeline", padding="5")
        file_frame.pack(side='left', padx=5)
        
        ttk.Button(
            file_frame, text="New", command=self._new_timeline, width=6
        ).pack(side='left', padx=2)
        
        ttk.Button(
            file_frame, text="Load", command=self._load_timeline, width=6
        ).pack(side='left', padx=2)
        
        ttk.Button(
            file_frame, text="Save", command=self._save_timeline, width=6
        ).pack(side='left', padx=2)
        
        # Transport controls
        transport_frame = ttk.LabelFrame(parent, text="Playback", padding="5")
        transport_frame.pack(side='left', padx=5)
        
        self.play_button = ttk.Button(
            transport_frame, text="▶ Play", command=self._on_play_clicked, width=8
        )
        self.play_button.pack(side='left', padx=2)
        
        self.pause_button = ttk.Button(
            transport_frame, text="⏸ Pause", command=self._on_pause_clicked, width=8, state='disabled'
        )
        self.pause_button.pack(side='left', padx=2)
        
        ttk.Button(
            transport_frame, text="⏹ Stop", command=self._on_stop_clicked, width=8
        ).pack(side='left', padx=2)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(parent, text="View", padding="5")
        zoom_frame.pack(side='left', padx=5)
        
        ttk.Button(
            zoom_frame, text="➕", command=lambda: self.timeline_canvas.zoom_in(), width=3
        ).pack(side='left', padx=2)
        
        ttk.Button(
            zoom_frame, text="➖", command=lambda: self.timeline_canvas.zoom_out(), width=3
        ).pack(side='left', padx=2)
        
        ttk.Button(
            zoom_frame, text="Fit", command=lambda: self.timeline_canvas.zoom_to_fit(), width=4
        ).pack(side='left', padx=2)
        
        # Timeline name
        name_frame = ttk.Frame(parent)
        name_frame.pack(side='right', padx=5)
        
        ttk.Label(name_frame, text="Name:").pack(side='left', padx=2)
        self.name_var = tk.StringVar(value=self.timeline.name)
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=20)
        self.name_entry.pack(side='left', padx=2)
        self.name_entry.bind('<FocusOut>', lambda e: self._update_timeline_name())
        self.name_entry.bind('<Return>', lambda e: self._update_timeline_name())
    
    def _build_info_bar(self, parent):
        """Build information bar at bottom."""
        # Playhead position
        ttk.Label(parent, text="Position:").pack(side='left', padx=5)
        self.position_label = ttk.Label(parent, text="00:00.0", font=("Segoe UI", 9, "bold"))
        self.position_label.pack(side='left', padx=2)
        
        ttk.Separator(parent, orient='vertical').pack(side='left', padx=10, fill='y')
        
        # Timeline duration
        ttk.Label(parent, text="Duration:").pack(side='left', padx=5)
        self.duration_label = ttk.Label(parent, text="00:00.0", font=("Segoe UI", 9))
        self.duration_label.pack(side='left', padx=2)
        
        ttk.Separator(parent, orient='vertical').pack(side='left', padx=10, fill='y')
        
        # Clip count
        ttk.Label(parent, text="Clips:").pack(side='left', padx=5)
        self.clip_count_label = ttk.Label(parent, text="0", font=("Segoe UI", 9))
        self.clip_count_label.pack(side='left', padx=2)
        
        ttk.Separator(parent, orient='vertical').pack(side='left', padx=10, fill='y')
        
        # Selected clip
        ttk.Label(parent, text="Selected:").pack(side='left', padx=5)
        self.selected_label = ttk.Label(parent, text="None", font=("Segoe UI", 9))
        self.selected_label.pack(side='left', padx=2)
        
        # Update info
        self._update_info()
    
    def _new_timeline(self):
        """Create a new timeline."""
        if self.timeline.clips:
            response = messagebox.askyesno(
                "New Timeline",
                "Current timeline has clips. Create new timeline anyway?\n\n"
                "Note: Make sure to save first if you want to keep your changes."
            )
            if not response:
                return
        
        # Prompt for name
        name = tk.simpledialog.askstring("New Timeline", "Timeline name:", initialvalue="New Timeline")
        if name:
            self.timeline = Timeline(name=name)
            self.timeline_canvas.set_timeline(self.timeline)
            self.name_var.set(name)
            self._update_info()
            logger.info(f"Created new timeline: {name}")
    
    def _load_timeline(self):
        """Load a timeline from file."""
        filepath = filedialog.askopenfilename(
            title="Load Timeline",
            defaultextension=".ppt",
            filetypes=[("Piper Timeline", "*.ppt"), ("All Files", "*.*")],
            initialdir=str(self.timeline_manager.timelines_dir)
        )
        
        if filepath:
            timeline = load_timeline(filepath)
            if timeline:
                self.timeline = timeline
                self.timeline_canvas.set_timeline(self.timeline)
                self.name_var.set(timeline.name)
                self._update_info()
                messagebox.showinfo("Success", f"Loaded timeline: {timeline.name}")
                logger.info(f"Loaded timeline from: {filepath}")
            else:
                messagebox.showerror("Error", f"Failed to load timeline from:\n{filepath}")
    
    def _save_timeline(self):
        """Save the current timeline."""
        # Update timeline name from entry
        self.timeline.name = self.name_var.get()
        
        # Get save path
        default_path = str(self.timeline_manager.get_timeline_path(self.timeline.name))
        
        filepath = filedialog.asksaveasfilename(
            title="Save Timeline",
            defaultextension=".ppt",
            filetypes=[("Piper Timeline", "*.ppt"), ("All Files", "*.*")],
            initialfile=self.timeline.name + ".ppt",
            initialdir=str(self.timeline_manager.timelines_dir)
        )
        
        if filepath:
            success = save_timeline(self.timeline, filepath)
            if success:
                messagebox.showinfo("Success", f"Saved timeline: {self.timeline.name}")
                logger.info(f"Saved timeline to: {filepath}")
            else:
                messagebox.showerror("Error", f"Failed to save timeline to:\n{filepath}")
    
    def _update_timeline_name(self):
        """Update timeline name from entry."""
        new_name = self.name_var.get().strip()
        if new_name:
            self.timeline.name = new_name
    
    def _on_play_clicked(self):
        """Handle play button click."""
        self.is_playing = True
        self.play_button.config(state='disabled')
        self.pause_button.config(state='normal')
        
        if self.on_play:
            self.on_play()
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.is_playing = False
        self.play_button.config(state='normal')
        self.pause_button.config(state='disabled')
        
        if self.on_pause:
            self.on_pause()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.is_playing = False
        self.play_button.config(state='normal')
        self.pause_button.config(state='disabled')
        self.timeline_canvas.set_playhead_position(0.0)
        
        if self.on_stop:
            self.on_stop()
    
    def _on_clip_select_internal(self, clip: Optional[TimelineClip]):
        """Handle clip selection from canvas."""
        if clip:
            self.selected_label.config(text=clip.name)
        else:
            self.selected_label.config(text="None")
        
        if self.on_clip_select:
            self.on_clip_select(clip)
    
    def _on_clip_move(self, clip_id: str, new_start_time: float):
        """Handle clip movement."""
        logger.info(f"Clip {clip_id} moved to {new_start_time:.2f}s")
        self._update_info()
    
    def _on_playhead_change(self, time: float):
        """Handle playhead position change."""
        self.position_label.config(text=self._format_time(time))
    
    def _update_info(self):
        """Update information labels."""
        self.duration_label.config(text=self._format_time(self.timeline.total_duration))
        self.clip_count_label.config(text=str(len(self.timeline.clips)))
    
    def _format_time(self, seconds: float) -> str:
        """Format time for display."""
        if seconds < 60:
            return f"{seconds:05.2f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes:02d}:{secs:05.2f}"
    
    def add_clip(self, clip: TimelineClip):
        """
        Add a clip to the timeline.
        
        Args:
            clip: Clip to add
        """
        self.timeline.add_clip(clip)
        self.timeline_canvas.redraw()
        self._update_info()
    
    def remove_selected_clip(self):
        """Remove the currently selected clip."""
        if self.timeline_canvas.selected_clip_id:
            self.timeline.remove_clip(self.timeline_canvas.selected_clip_id)
            self.timeline_canvas.select_clip(None)
            self.timeline_canvas.redraw()
            self._update_info()
    
    def get_selected_clip(self) -> Optional[TimelineClip]:
        """
        Get the currently selected clip.
        
        Returns:
            Selected clip or None
        """
        if self.timeline_canvas.selected_clip_id:
            return self.timeline.get_clip_by_id(self.timeline_canvas.selected_clip_id)
        return None
    
    def set_playhead_position(self, time: float):
        """
        Set playhead position programmatically.
        
        Args:
            time: Time in seconds
        """
        self.timeline_canvas.set_playhead_position(time)
    
    def get_playhead_position(self) -> float:
        """
        Get current playhead position.
        
        Returns:
            Time in seconds
        """
        return self.timeline_canvas.playhead_position


# Demo/test function
def demo_timeline_panel():
    """Demo the timeline panel."""
    root = tk.Tk()
    root.title("Timeline Panel Demo")
    root.geometry("1000x300")
    
    # Create sample timeline
    from timeline import TimelineClip, get_clip_color
    import uuid
    
    timeline = Timeline(name="Demo Timeline")
    
    # Add some sample clips
    clip1 = TimelineClip(
        id=str(uuid.uuid4()),
        recording_file="recordings/pick.ppr",
        start_time=0.0,
        duration=10.0,
        original_duration=10.0,
        name="Pick Part A",
        color=get_clip_color("pick")
    )
    timeline.add_clip(clip1)
    
    clip2 = TimelineClip(
        id=str(uuid.uuid4()),
        recording_file="recordings/move.ppr",
        start_time=15.0,
        duration=5.0,
        original_duration=5.0,
        name="Move to Station",
        color=get_clip_color("move"),
        speed_multiplier=2.0
    )
    timeline.add_clip(clip2)
    
    clip3 = TimelineClip(
        id=str(uuid.uuid4()),
        recording_file="recordings/place.ppr",
        start_time=20.0,
        duration=8.0,
        original_duration=10.0,
        trim_start=1.0,
        trim_end=1.0,
        name="Place Part A",
        color=get_clip_color("place"),
        speed_multiplier=0.5
    )
    timeline.add_clip(clip3)
    
    def on_clip_select(clip):
        if clip:
            print(f"Selected: {clip.name}")
        else:
            print("Deselected")
    
    def on_play():
        print("Play clicked")
    
    def on_pause():
        print("Pause clicked")
    
    def on_stop():
        print("Stop clicked")
    
    # Create timeline panel
    panel = TimelinePanel(
        root,
        timeline=timeline,
        on_clip_select=on_clip_select,
        on_play=on_play,
        on_pause=on_pause,
        on_stop=on_stop
    )
    panel.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    demo_timeline_panel()

