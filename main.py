"""
Piper Robot Automation System - Main UI
Async GUI for recording and playing back robot movements
"""

import asyncio
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import json
from typing import Optional


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
        self.root.title("Piper Robot Automation System")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # State variables
        self.is_recording = False
        self.is_playing = False
        self.loaded_file_path: Optional[Path] = None
        self.file_duration: float = 0.0
        self.loaded_data: Optional[list] = None
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """
        Create and layout all UI components.
        """
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Piper Robot Automation System",
            font=("Segoe UI", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Button container
        button_frame = ttk.Frame(main_frame)
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
            main_frame,
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
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, pady=(20, 0), sticky="ew")
        
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
            # Start recording
            self.is_recording = True
            self.record_button.configure(text="Stop")
            self.load_button.configure(state="disabled")
            self.play_button.configure(state="disabled")
            self.status_var.set("Recording...")
            
            # Schedule async recording task
            asyncio.create_task(self._record_async())
        else:
            # Stop recording
            self.is_recording = False
            self.record_button.configure(text="Record")
            self.load_button.configure(state="normal")
            if self.loaded_file_path:
                self.play_button.configure(state="normal")
            self.status_var.set("Recording stopped")
    
    def _on_play_click(self):
        """
        Handle Play/Pause button click.
        Toggles between playing and paused states.
        """
        if not self.is_playing:
            # Start playback
            if not self.loaded_data:
                self.status_var.set("Error: No valid data to play")
                return
                
            self.is_playing = True
            self.play_button.configure(text="Pause")
            self.record_button.configure(state="disabled")
            self.load_button.configure(state="disabled")
            self.status_var.set("Playing...")
            
            # Schedule async playback task
            asyncio.create_task(self._playback_async())
        else:
            # Pause playback
            self.is_playing = False
            self.play_button.configure(text="Play")
            self.record_button.configure(state="normal")
            self.load_button.configure(state="normal")
            self.status_var.set("Playback paused")
    
    def _on_load_click(self):
        """
        Handle Load New File button click.
        Opens file dialog and loads the selected file.
        """
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Recording File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=Path.cwd()
        )
        
        if file_path:
            self.loaded_file_path = Path(file_path)
            self._update_file_info()
            
            # Schedule async file processing
            asyncio.create_task(self._process_file_async())
    
    def _update_file_info(self):
        """
        Update the UI with information about the loaded file.
        """
        if self.loaded_file_path:
            # Display filename
            self.filename_var.set(self.loaded_file_path.name)
            
            # Calculate and display duration (placeholder for now)
            self._calculate_duration()
            
            self.status_var.set(f"Loaded: {self.loaded_file_path.name}")
        else:
            self.filename_var.set("No file loaded")
            self.duration_var.set("--")
            self.status_var.set("Ready")
    
    def _calculate_duration(self):
        """
        Calculate the total duration of the loaded recording file.
        Uses timestamp math to determine playback time.
        
        TODO: Implement actual timestamp calculation based on file format
        """
        if not self.loaded_file_path or not self.loaded_file_path.exists():
            self.duration_var.set("--")
            self.loaded_data = None
            self.play_button.configure(state="disabled")
            return
        
        try:
            # Read file and calculate duration
            with open(self.loaded_file_path, 'r') as f:
                data = json.load(f)
            
            # Store loaded data for playback
            self.loaded_data = data
                
            # Example duration calculation (to be implemented)
            # Extract first and last timestamps
            if isinstance(data, list) and len(data) > 0:
                if 'timestamp' in data[0] and 'timestamp' in data[-1]:
                    duration = data[-1]['timestamp'] - data[0]['timestamp']
                    self.file_duration = duration
                    self._format_duration(duration)
                    # Enable play button if data is valid
                    self.play_button.configure(state="normal")
                else:
                    self.duration_var.set("Unknown format")
                    self.loaded_data = None
                    self.play_button.configure(state="disabled")
            else:
                self.duration_var.set("Empty file")
                self.loaded_data = None
                self.play_button.configure(state="disabled")
                
        except json.JSONDecodeError:
            self.duration_var.set("Invalid file format")
            self.loaded_data = None
            self.play_button.configure(state="disabled")
        except Exception as e:
            self.duration_var.set(f"Error: {str(e)}")
            self.loaded_data = None
            self.play_button.configure(state="disabled")
    
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
    
    async def _record_async(self):
        """
        Async task for recording robot movements.
        This runs the recording loop without blocking the UI.
        
        TODO: Implement actual recording logic using Piper SDK
        """
        try:
            while self.is_recording:
                # Placeholder: Add actual recording logic here
                # Example:
                # joint_data = piper.GetArmJointMsgs()
                # Save data to recording buffer
                
                await asyncio.sleep(0.005)  # 200 Hz recording rate
                
        except Exception as e:
            self.status_var.set(f"Recording error: {str(e)}")
            self.is_recording = False
            self.record_button.configure(text="Record")
    
    async def _playback_async(self):
        """
        Async task for playing back recorded robot movements.
        This runs the playback loop without blocking the UI.
        
        TODO: Implement actual playback logic using Piper SDK
        """
        try:
            if not self.loaded_data:
                return
            
            # Calculate playback timing
            start_index = 0
            
            for i, record in enumerate(self.loaded_data):
                if not self.is_playing:
                    # Playback was paused
                    break
                
                # Placeholder: Add actual playback logic here
                # Example:
                # if 'joints' in record:
                #     piper.JointCtrl(
                #         joint_1=record['joints'][0],
                #         joint_2=record['joints'][1],
                #         ...
                #     )
                # if 'gripper' in record:
                #     piper.GripperCtrl(...)
                
                # Calculate timing between frames
                if i < len(self.loaded_data) - 1:
                    if 'timestamp' in record and 'timestamp' in self.loaded_data[i + 1]:
                        # Use actual time difference between records
                        time_diff = self.loaded_data[i + 1]['timestamp'] - record['timestamp']
                        await asyncio.sleep(max(0.001, time_diff))  # Minimum 1ms
                    else:
                        # Default to 200 Hz if no timestamps
                        await asyncio.sleep(0.005)
                else:
                    await asyncio.sleep(0.005)
            
            # Playback completed
            self.is_playing = False
            self.play_button.configure(text="Play")
            self.record_button.configure(state="normal")
            self.load_button.configure(state="normal")
            self.status_var.set("Playback completed")
                
        except Exception as e:
            self.status_var.set(f"Playback error: {str(e)}")
            self.is_playing = False
            self.play_button.configure(text="Play")
            self.record_button.configure(state="normal")
            self.load_button.configure(state="normal")
    
    async def _process_file_async(self):
        """
        Async task for processing loaded files.
        Performs file validation and parsing without blocking the UI.
        """
        try:
            self.status_var.set("Processing file...")
            
            # Simulate async file processing
            await asyncio.sleep(0.1)
            
            self.status_var.set(f"Ready to playback: {self.loaded_file_path.name}")
            
        except Exception as e:
            self.status_var.set(f"File processing error: {str(e)}")


async def async_mainloop(root: tk.Tk):
    """
    Run the tkinter event loop asynchronously.
    Allows tkinter to work with asyncio for concurrent operations.
    
    Args:
        root: The main tkinter window
    """
    while True:
        try:
            root.update()
            await asyncio.sleep(0.01)  # 100 Hz UI update rate
        except tk.TclError:
            # Window was closed
            break


def main():
    """
    Main entry point for the application.
    Initializes the UI and starts the async event loop.
    """
    # Create root window
    root = tk.Tk()
    
    # Initialize UI
    app = PiperAutomationUI(root)
    
    # Run async event loop
    try:
        asyncio.run(async_mainloop(root))
    except KeyboardInterrupt:
        print("\nApplication closed by user")


if __name__ == "__main__":
    main()

