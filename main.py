"""
Piper Robot Automation System - Main UI
Async GUI for recording and playing back robot movements
"""

import asyncio
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import logging
from typing import Optional

# Import Piper SDK
try:
    from piper_sdk import C_PiperInterface_V2
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: Piper SDK not available. Running in demo mode.")

# Import our modules
from recorder import PiperRecorder
from player import PiperPlayer
from ppr_file_handler import list_recordings, get_recording_info
from timeline_panel import TimelinePanel
from timeline import Timeline, TimelineManager
from clip_library import ClipLibrary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class PiperAutomationUI:
    """
    Main user interface for the Piper Robot automation system.
    Provides recording and file loading capabilities with async support.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the UI components and state.
        
        Args:
            root: The main tkinter window
        """
        self.root = root
        self.root.title("Piper Robot Automation System V2")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # Initialize Piper SDK
        self.piper = None
        self.recorder: Optional[PiperRecorder] = None
        self.player: Optional[PiperPlayer] = None
        self.logger = logging.getLogger(__name__)
        
        # State variables
        self.is_recording = False
        self.is_playing = False
        self.loaded_file_path: Optional[Path] = None
        self.file_duration: float = 0.0
        
        # V2 Timeline state (create single shared instance)
        self.timeline_manager = TimelineManager()
        self.current_timeline: Optional[Timeline] = None
        
        # Try to connect to robot
        self._init_robot_connection()
        
        # Setup UI
        self._setup_ui()
        
        # Start status update loop
        self.root.after(100, self._update_status_loop)
    
    def _init_robot_connection(self):
        """
        Initialize connection to Piper robot.
        """
        if not SDK_AVAILABLE:
            self.logger.warning("Piper SDK not available - running in demo mode")
            return
        
        try:
            self.logger.info("Attempting to connect to Piper robot...")
            self.piper = C_PiperInterface_V2()
            self.logger.info("SDK interface created, connecting port...")
            self.piper.ConnectPort()
            self.logger.info("Connected to Piper robot successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to robot: {e}")
            self.piper = None
            messagebox.showwarning(
                "Robot Connection",
                f"Could not connect to Piper robot.\n\nError: {e}\n\nThe application will run in demo mode."
            )
        
    def _setup_ui(self):
        """
        Create and layout all UI components.
        """
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Tab 1: V1 Record/Playback (existing functionality)
        v1_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(v1_frame, text="Record & Playback (V1)")
        
        # Tab 2: V2 Timeline Editor
        v2_frame = ttk.Frame(self.notebook)
        self.notebook.add(v2_frame, text="Timeline Editor (V2)")
        
        # Setup V1 tab
        self._setup_v1_tab(v1_frame)
        
        # Setup V2 tab
        self._setup_v2_tab(v2_frame)
    
    def _setup_v1_tab(self, parent):
        """Setup the V1 record/playback tab."""
        parent.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            parent,
            text="Record & Playback",
            font=("Segoe UI", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Button container
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        # Record/Stop button
        self.record_button = ttk.Button(
            button_frame,
            text="Record",
            command=self._on_record_click,
            width=20
        )
        self.record_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Play/Pause button
        self.play_button = ttk.Button(
            button_frame,
            text="Play",
            command=self._on_play_click,
            width=20,
            state="disabled"  # Disabled until file is loaded
        )
        self.play_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Load file button
        self.load_button = ttk.Button(
            button_frame,
            text="Load New File",
            command=self._on_load_click,
            width=20
        )
        self.load_button.grid(row=0, column=2, padx=5, pady=5)
        
        # File info container
        info_frame = ttk.LabelFrame(
            parent,
            text="Loaded File Information",
            padding="15"
        )
        info_frame.grid(row=2, column=0, pady=20, sticky="ew")
        info_frame.columnconfigure(1, weight=1)
        
        # File name label
        ttk.Label(info_frame, text="File:").grid(row=0, column=0, sticky="w", pady=5)
        self.filename_var = tk.StringVar(value="No file loaded")
        filename_label = ttk.Label(
            info_frame,
            textvariable=self.filename_var,
            font=("Segoe UI", 10),
            foreground="#555555"
        )
        filename_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # Duration label
        ttk.Label(info_frame, text="Duration:").grid(row=1, column=0, sticky="w", pady=5)
        self.duration_var = tk.StringVar(value="--")
        duration_label = ttk.Label(
            info_frame,
            textvariable=self.duration_var,
            font=("Segoe UI", 10),
            foreground="#555555"
        )
        duration_label.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # Samples label
        ttk.Label(info_frame, text="Samples:").grid(row=2, column=0, sticky="w", pady=5)
        self.samples_var = tk.StringVar(value="--")
        samples_label = ttk.Label(
            info_frame,
            textvariable=self.samples_var,
            font=("Segoe UI", 10),
            foreground="#555555"
        )
        samples_label.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # Progress bar
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, pady=20, sticky="ew")
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100.0,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill='x', pady=5)
        
        self.progress_label_var = tk.StringVar(value="0.0%")
        progress_label = ttk.Label(
            progress_frame,
            textvariable=self.progress_label_var,
            font=("Segoe UI", 9)
        )
        progress_label.pack()
        
        # Playback speed control (V2: Extended to 4x)
        speed_frame = ttk.LabelFrame(parent, text="Playback Speed (V2)", padding="10")
        speed_frame.grid(row=4, column=0, pady=10, sticky="ew")
        
        # Speed slider
        speed_control_frame = ttk.Frame(speed_frame)
        speed_control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(speed_control_frame, text="0.1x").pack(side='left', padx=5)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_slider = ttk.Scale(
            speed_control_frame,
            from_=0.1,
            to=4.0,
            variable=self.speed_var,
            orient='horizontal',
            command=self._on_speed_change
        )
        self.speed_slider.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Label(speed_control_frame, text="4.0x").pack(side='left', padx=5)
        
        self.speed_label_var = tk.StringVar(value="1.0x")
        speed_value_label = ttk.Label(
            speed_control_frame,
            textvariable=self.speed_label_var,
            font=("Segoe UI", 10, "bold"),
            width=6
        )
        speed_value_label.pack(side='left', padx=10)
        
        # Speed preset buttons
        preset_frame = ttk.Frame(speed_frame)
        preset_frame.pack(fill='x')
        
        ttk.Label(preset_frame, text="Presets:").pack(side='left', padx=(0, 10))
        
        speed_presets = [
            ("0.25x", 0.25),
            ("0.5x", 0.5),
            ("1.0x", 1.0),
            ("2.0x", 2.0),
            ("4.0x", 4.0)
        ]
        
        for label, value in speed_presets:
            btn = ttk.Button(
                preset_frame,
                text=label,
                command=lambda v=value: self._set_speed_preset(v),
                width=6
            )
            btn.pack(side='left', padx=2)
        
        # Status bar
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=5, column=0, pady=(20, 0), sticky="ew")
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        status_label.grid(row=0, column=0, sticky="w")
        
    def _on_record_click(self):
        """
        Handle Record/Stop button click.
        Toggles between recording and stopped states.
        """
        if not self.is_recording:
            # Check if robot is connected
            if not self.piper:
                messagebox.showerror("Error", "Robot not connected. Cannot start recording.")
                return
            
            # Start recording
            try:
                self.recorder = PiperRecorder(self.piper, sample_rate=200)
                filepath = self.recorder.start_recording(description="Manual recording")
                
                self.is_recording = True
                self.record_button.configure(text="Stop Recording")
                self.load_button.configure(state="disabled")
                self.play_button.configure(state="disabled")
                self.status_var.set(f"Recording to: {Path(filepath).name}")
                
            except Exception as e:
                self.logger.error(f"Failed to start recording: {e}")
                messagebox.showerror("Recording Error", f"Failed to start recording:\n{e}")
                
        else:
            # Stop recording
            try:
                if self.recorder:
                    stats = self.recorder.stop_recording()
                    self.is_recording = False
                    self.record_button.configure(text="Record")
                    self.load_button.configure(state="normal")
                    
                    # Auto-load the recorded file
                    if stats.get('filepath'):
                        self.loaded_file_path = Path(stats['filepath'])
                        self._update_file_info()
                        self.play_button.configure(state="normal")
                    
                    messagebox.showinfo(
                        "Recording Complete",
                        f"Recording saved successfully!\n\n"
                        f"File: {stats.get('filename', 'Unknown')}\n"
                        f"Samples: {stats.get('sample_count', 0)}\n"
                        f"Duration: {stats.get('duration_sec', 0):.2f} seconds\n"
                        f"Average Rate: {stats.get('average_rate', 0):.1f} Hz"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error stopping recording: {e}")
                messagebox.showerror("Error", f"Error stopping recording:\n{e}")
            
            finally:
                self.is_recording = False
                self.record_button.configure(text="Record")
                self.load_button.configure(state="normal")
                self.status_var.set("Recording stopped")
    
    def _on_play_click(self):
        """
        Handle Play/Stop button click.
        Toggles between playing and stopped states.
        """
        if not self.is_playing:
            # Check if robot is connected
            if not self.piper:
                messagebox.showerror("Error", "Robot not connected. Cannot start playback.")
                return
            
            # Check if file is loaded
            if not self.loaded_file_path:
                messagebox.showwarning("No File", "Please load a recording file first.")
                return
            
            # Start playback
            try:
                if not self.player:
                    self.player = PiperPlayer(self.piper)
                    self.player.load_recording(str(self.loaded_file_path))
                
                speed = self.speed_var.get()
                self.player.start_playback(speed_multiplier=speed)
                
                self.is_playing = True
                self.play_button.configure(text="Stop Playback")
                self.record_button.configure(state="disabled")
                self.load_button.configure(state="disabled")
                self.speed_slider.configure(state="disabled")
                self.status_var.set(f"Playing: {self.loaded_file_path.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to start playback: {e}")
                messagebox.showerror("Playback Error", f"Failed to start playback:\n{e}")
                
        else:
            # Stop playback
            try:
                if self.player:
                    self.player.stop_playback()
                    
            except Exception as e:
                self.logger.error(f"Error stopping playback: {e}")
            
            finally:
                self.is_playing = False
                self.play_button.configure(text="Play")
                self.record_button.configure(state="normal")
                self.load_button.configure(state="normal")
                self.speed_slider.configure(state="normal")
                self.progress_var.set(0.0)
                self.progress_label_var.set("0.0%")
                self.status_var.set("Playback stopped")
    
    def _on_load_click(self):
        """
        Handle Load New File button click.
        Opens file dialog and loads the selected file.
        """
        # Open file dialog
        recordings_dir = Path("recordings")
        initial_dir = recordings_dir if recordings_dir.exists() else Path.cwd()
        
        file_path = filedialog.askopenfilename(
            title="Select Recording File",
            filetypes=[
                ("Piper Recordings", "*.ppr"),
                ("All files", "*.*")
            ],
            initialdir=initial_dir
        )
        
        if file_path:
            try:
                self.loaded_file_path = Path(file_path)
                
                # Create new player and load file
                if self.piper:
                    self.player = PiperPlayer(self.piper)
                    info = self.player.load_recording(str(file_path))
                    
                    # Update UI with file info
                    self._update_file_info()
                    self.play_button.configure(state="normal")
                    self.status_var.set(f"Loaded: {self.loaded_file_path.name}")
                else:
                    messagebox.showwarning(
                        "Robot Not Connected",
                        "Robot is not connected. File loaded but playback will not be available."
                    )
                    self._update_file_info()
                    
            except Exception as e:
                self.logger.error(f"Failed to load file: {e}")
                messagebox.showerror("Load Error", f"Failed to load recording file:\n{e}")
                self.loaded_file_path = None
                self.player = None
    
    def _update_file_info(self):
        """
        Update the UI with information about the loaded file.
        """
        if self.loaded_file_path and self.loaded_file_path.exists():
            try:
                # Display filename
                self.filename_var.set(self.loaded_file_path.name)
                
                # Get recording info
                info = get_recording_info(str(self.loaded_file_path))
                
                if 'error' not in info:
                    # Display duration
                    duration_sec = info['duration_sec']
                    self._format_duration(duration_sec)
                    
                    # Display sample count
                    self.samples_var.set(f"{info['sample_count']:,}")
                    
                    self.file_duration = duration_sec
                else:
                    self.duration_var.set("Error reading file")
                    self.samples_var.set("--")
                    
            except Exception as e:
                self.logger.error(f"Error reading file info: {e}")
                self.duration_var.set("--")
                self.samples_var.set("--")
        else:
            self.filename_var.set("No file loaded")
            self.duration_var.set("--")
            self.samples_var.set("--")
    
    def _set_speed_preset(self, speed: float):
        """
        Set playback speed to a preset value.
        
        Args:
            speed: Speed multiplier (0.25, 0.5, 1.0, 2.0, or 4.0)
        """
        # Show warning for high speeds
        if speed > 2.0:
            response = messagebox.askyesno(
                "High Speed Warning",
                f"You are setting playback speed to {speed}x.\n\n"
                f"This is {speed}x faster than the original recording.\n"
                f"Please ensure:\n"
                f"  • Workspace is completely clear\n"
                f"  • Robot can safely move at this speed\n"
                f"  • You are ready to emergency stop if needed\n\n"
                f"Continue with {speed}x speed?",
                icon='warning'
            )
            if not response:
                return  # User cancelled
        
        self.speed_var.set(speed)
        self.speed_label_var.set(f"{speed:.2f}x")
        
        # Update player if currently playing
        if self.is_playing and self.player:
            try:
                self.player.set_speed(speed)
                self.logger.info(f"Playback speed changed to {speed}x during playback")
            except Exception as e:
                self.logger.error(f"Error setting speed during playback: {e}")
    
    def _on_speed_change(self, value):
        """
        Handle playback speed slider change.
        
        Args:
            value: New speed value from slider
        """
        speed = float(value)
        self.speed_label_var.set(f"{speed:.2f}x")
        
        # Show warning if crossing 2x threshold (only show once per session)
        if speed > 2.0 and not hasattr(self, '_high_speed_warning_shown'):
            self._high_speed_warning_shown = True
            messagebox.showwarning(
                "High Speed",
                f"Playback speed is now above 2x.\n\n"
                f"Monitor the robot carefully and be ready to stop if needed."
            )
        
        # Update player speed if currently playing
        if self.is_playing and self.player:
            try:
                self.player.set_speed(speed)
            except Exception as e:
                self.logger.error(f"Error setting playback speed: {e}")
    
    def _format_duration(self, seconds: float):
        """
        Format duration in seconds to a human-readable string.
        
        Args:
            seconds: Duration in seconds
        """
        if seconds < 60:
            self.duration_var.set(f"{seconds:.2f} seconds")
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            self.duration_var.set(f"{minutes}m {secs:.1f}s")
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            self.duration_var.set(f"{hours}h {minutes}m {secs:.0f}s")
    
    def _update_status_loop(self):
        """
        Update status information periodically (recording/playback progress).
        """
        try:
            # Update recording status
            if self.is_recording and self.recorder:
                stats = self.recorder.get_recording_stats()
                if stats:
                    sample_count = stats.get('sample_count', 0)
                    duration = stats.get('duration_sec', 0)
                    rate = stats.get('current_rate', 0)
                    self.status_var.set(
                        f"Recording... {sample_count:,} samples, {duration:.1f}s, {rate:.0f} Hz"
                    )
            
            # Update playback status and progress
            if self.is_playing and self.player:
                if not self.player.is_playing():
                    # Playback completed
                    self.is_playing = False
                    self.play_button.configure(text="Play")
                    self.record_button.configure(state="normal")
                    self.load_button.configure(state="normal")
                    self.speed_slider.configure(state="normal")
                    self.progress_var.set(100.0)
                    self.progress_label_var.set("100.0%")
                    self.status_var.set("Playback completed")
                    
                    messagebox.showinfo("Playback Complete", "Recording playback finished successfully!")
                else:
                    # Update progress
                    progress = self.player.get_progress()
                    self.progress_var.set(progress)
                    self.progress_label_var.set(f"{progress:.1f}%")
                    
                    info = self.player.get_playback_info()
                    current = info.get('current_sample', 0)
                    total = info.get('total_samples', 0)
                    self.status_var.set(
                        f"Playing... {current:,}/{total:,} samples ({progress:.1f}%)"
                    )
        
        except Exception as e:
            self.logger.error(f"Error in status update loop: {e}")
        
        finally:
            # Schedule next update
            self.root.after(100, self._update_status_loop)


    def _setup_v2_tab(self, parent):
        """Setup the V2 timeline editor tab."""
        parent.columnconfigure(0, weight=3)  # Timeline gets more space
        parent.columnconfigure(1, weight=1)  # Library panel
        parent.rowconfigure(0, weight=1)
        
        # Create timeline panel (left side) - pass shared timeline_manager
        self.timeline_panel = TimelinePanel(
            parent,
            timeline=self.current_timeline or Timeline(name="New Timeline"),
            timeline_manager=self.timeline_manager,  # Share the manager
            on_clip_select=self._on_timeline_clip_select,
            on_play=self._on_timeline_play,
            on_pause=self._on_timeline_pause,
            on_stop=self._on_timeline_stop
        )
        self.timeline_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Create clip library panel (right side)
        self.clip_library = ClipLibrary(
            parent,
            recordings_dir="recordings",
            timeline_manager=self.timeline_manager,  # Share the manager
            on_add_clip=self._on_library_add_clip
        )
        self.clip_library.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
    
    def _on_timeline_clip_select(self, clip):
        """Handle clip selection in timeline."""
        if clip:
            self.logger.info(f"Timeline clip selected: {clip.name}")
        else:
            self.logger.info("Timeline clip deselected")
    
    def _on_library_add_clip(self, clip):
        """Handle adding clip from library to timeline."""
        # Position clip at end of timeline
        clip.start_time = self.timeline_panel.timeline.total_duration
        
        # Add to timeline
        self.timeline_panel.add_clip(clip)
        
        self.logger.info(f"Added clip from library: {clip.name}")
        
        # Show success message
        messagebox.showinfo(
            "Clip Added",
            f"Added to timeline:\n{clip.name}\n\n"
            f"Duration: {clip.duration:.2f}s\n"
            f"Position: {clip.start_time:.2f}s"
        )
    
    def _on_timeline_play(self):
        """Handle timeline play button."""
        self.logger.info("Timeline play requested")
        messagebox.showinfo(
            "Timeline Playback",
            "Timeline playback will be implemented in Phase 6!\n\n"
            "For now, you can:\n"
            "• Arrange clips on the timeline\n"
            "• Save/load timeline projects\n"
            "• Adjust clip positions\n"
            "• Use zoom controls"
        )
    
    def _on_timeline_pause(self):
        """Handle timeline pause button."""
        self.logger.info("Timeline pause requested")
    
    def _on_timeline_stop(self):
        """Handle timeline stop button."""
        self.logger.info("Timeline stop requested")


def main():
    """
    Main entry point for the application.
    Initializes the UI and starts the event loop.
    """
    # Create root window
    root = tk.Tk()
    
    # Initialize UI
    app = PiperAutomationUI(root)
    
    # Run main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")


if __name__ == "__main__":
    main()

