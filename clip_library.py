"""
Clip Library - Recording browser for Timeline System V2.

Provides a visual library of all available recordings that can be added to timelines.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from ppr_file_handler import list_recordings, get_recording_info
from timeline import TimelineClip, get_clip_color
import uuid


logger = logging.getLogger(__name__)


class ClipLibrary(ttk.Frame):
    """
    Visual library of available recordings.
    
    Features:
    - List all .ppr files in recordings directory
    - Show metadata (duration, date, samples)
    - Search and filter
    - Double-click to add to timeline
    - Preview recording info
    - Refresh to update list
    """
    
    def __init__(
        self,
        parent,
        recordings_dir: str = "recordings",
        timeline_manager: Optional['TimelineManager'] = None,
        on_add_clip: Optional[Callable[[TimelineClip], None]] = None,
        **kwargs
    ):
        """
        Initialize clip library.
        
        Args:
            parent: Parent widget
            recordings_dir: Directory containing recordings
            timeline_manager: Shared timeline manager (optional)
            on_add_clip: Callback when clip should be added to timeline
        """
        super().__init__(parent, **kwargs)
        
        self.recordings_dir = Path(recordings_dir)
        self.timeline_manager = timeline_manager  # Use shared manager if provided
        self.on_add_clip = on_add_clip
        
        # State
        self.recordings: List[Dict[str, Any]] = []
        self.filtered_recordings: List[Dict[str, Any]] = []
        self.selected_recording: Optional[Dict[str, Any]] = None
        
        self._build_ui()
        
        # Delay loading recordings to avoid initialization conflicts
        # Load after a short delay to let everything initialize
        self.after(100, self._load_recordings)
    
    def _build_ui(self):
        """Build the library UI."""
        # Title and controls
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        title_label = ttk.Label(
            header_frame,
            text="📁 Recording Library",
            font=("Segoe UI", 10, "bold")
        )
        title_label.pack(side='left', padx=5)
        
        ttk.Button(
            header_frame,
            text="🔄 Refresh",
            command=self._load_recordings,
            width=10
        ).pack(side='right', padx=2)
        
        # Search bar
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_recordings())
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Recordings list
        list_frame = ttk.Frame(self, relief='sunken', borderwidth=1)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview for recordings
        columns = ('duration', 'date', 'samples')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree headings',
            selectmode='browse',
            yscrollcommand=scrollbar.set
        )
        
        # Configure columns
        self.tree.heading('#0', text='Recording Name')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('date', text='Date')
        self.tree.heading('samples', text='Samples')
        
        self.tree.column('#0', width=200, minwidth=150)
        self.tree.column('duration', width=80, minwidth=60)
        self.tree.column('date', width=120, minwidth=100)
        self.tree.column('samples', width=80, minwidth=60)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind events
        self.tree.bind('<Double-Button-1>', self._on_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Button-3>', self._on_right_click)  # Context menu
        
        # Info panel
        info_frame = ttk.LabelFrame(self, text="Selected Recording", padding="5")
        info_frame.pack(fill='x', padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=4, wrap='word', state='disabled')
        self.info_text.pack(fill='x', padx=2, pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        self.add_button = ttk.Button(
            button_frame,
            text="➕ Add to Timeline",
            command=self._add_selected_to_timeline,
            state='disabled'
        )
        self.add_button.pack(side='left', padx=2, fill='x', expand=True)
        
        self.preview_button = ttk.Button(
            button_frame,
            text="👁 Preview",
            command=self._preview_selected,
            state='disabled'
        )
        self.preview_button.pack(side='left', padx=2, fill='x', expand=True)
        
        # Status label
        self.status_var = tk.StringVar(value="No recordings found")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 8),
            foreground="#666666"
        )
        status_label.pack(pady=2)
    
    def _load_recordings(self):
        """Load all recordings from directory."""
        try:
            self.recordings = []
            
            if not self.recordings_dir.exists():
                self.recordings_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all .ppr files
            recording_files = list(self.recordings_dir.glob("*.ppr"))
            
            for filepath in recording_files:
                try:
                    info = get_recording_info(str(filepath))
                    if info:
                        self.recordings.append(info)
                except Exception as e:
                    logger.warning(f"Could not read recording {filepath}: {e}")
            
            # Sort by date (newest first)
            self.recordings.sort(key=lambda x: x.get('modified', ''), reverse=True)
            
            # Update display
            self.filtered_recordings = self.recordings.copy()
            self._update_tree()
            
            # Update status
            count = len(self.recordings)
            self.status_var.set(f"{count} recording{'s' if count != 1 else ''} found")
            
            logger.info(f"Loaded {count} recordings from {self.recordings_dir}")
            
        except Exception as e:
            logger.error(f"Failed to load recordings: {e}")
            messagebox.showerror("Error", f"Failed to load recordings:\n{e}")
    
    def _filter_recordings(self):
        """Filter recordings based on search text."""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.filtered_recordings = self.recordings.copy()
        else:
            self.filtered_recordings = [
                rec for rec in self.recordings
                if search_text in rec['name'].lower()
            ]
        
        self._update_tree()
        
        # Update status
        if search_text:
            total = len(self.recordings)
            filtered = len(self.filtered_recordings)
            self.status_var.set(f"Showing {filtered} of {total} recordings")
        else:
            count = len(self.recordings)
            self.status_var.set(f"{count} recording{'s' if count != 1 else ''} found")
    
    def _update_tree(self):
        """Update the treeview with current recordings."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add recordings
        for rec in self.filtered_recordings:
            name = rec['name']
            duration = f"{rec['duration']:.1f}s"
            date = self._format_date(rec.get('modified', ''))
            samples = f"{rec['sample_count']:,}"
            
            self.tree.insert(
                '',
                'end',
                text=name,
                values=(duration, date, samples),
                tags=('recording',)
            )
        
        # Configure tag colors
        self.tree.tag_configure('recording', font=('Segoe UI', 9))
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return "Unknown"
        
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str
    
    def _on_select(self, event):
        """Handle recording selection."""
        selection = self.tree.selection()
        if not selection:
            self.selected_recording = None
            self.add_button.config(state='disabled')
            self.preview_button.config(state='disabled')
            self._update_info_panel(None)
            return
        
        # Get selected item
        item = selection[0]
        name = self.tree.item(item, 'text')
        
        # Find recording
        self.selected_recording = next(
            (rec for rec in self.filtered_recordings if rec['name'] == name),
            None
        )
        
        # Enable buttons
        self.add_button.config(state='normal')
        self.preview_button.config(state='normal')
        
        # Update info panel
        self._update_info_panel(self.selected_recording)
    
    def _update_info_panel(self, recording: Optional[Dict[str, Any]]):
        """Update the info panel with recording details."""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')
        
        if recording:
            info_lines = [
                f"File: {recording['name']}",
                f"Duration: {recording['duration']:.2f}s",
                f"Samples: {recording['sample_count']:,} ({recording['sample_rate']:.1f} Hz)",
                f"Size: {recording['file_size'] / 1024:.1f} KB"
            ]
            self.info_text.insert('1.0', '\n'.join(info_lines))
        else:
            self.info_text.insert('1.0', "No recording selected")
        
        self.info_text.config(state='disabled')
    
    def _on_double_click(self, event):
        """Handle double-click to add recording."""
        if self.selected_recording:
            self._add_selected_to_timeline()
    
    def _on_right_click(self, event):
        """Handle right-click for context menu."""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._show_context_menu(event)
    
    def _show_context_menu(self, event):
        """Show context menu for recording."""
        menu = tk.Menu(self, tearoff=0)
        
        menu.add_command(
            label="➕ Add to Timeline",
            command=self._add_selected_to_timeline
        )
        menu.add_command(
            label="👁 Preview Info",
            command=self._preview_selected
        )
        menu.add_separator()
        menu.add_command(
            label="📂 Show in Folder",
            command=self._show_in_folder
        )
        
        menu.post(event.x_root, event.y_root)
    
    def _add_selected_to_timeline(self):
        """Add selected recording to timeline."""
        if not self.selected_recording:
            return
        
        try:
            # Create clip from recording
            filepath = self.selected_recording['filepath']
            name = self.selected_recording['name'].replace('.ppr', '')
            
            # Determine clip color based on name
            color = self._guess_clip_color(name)
            
            # Use timeline_manager if available, otherwise create clip directly
            if self.timeline_manager:
                clip = self.timeline_manager.create_clip_from_recording(
                    filepath,
                    start_time=0.0,
                    name=name,
                    color=color
                )
            else:
                clip = TimelineClip(
                    id=str(uuid.uuid4()),
                    recording_file=filepath,
                    start_time=0.0,  # Timeline will position it
                    duration=self.selected_recording['duration'],
                    original_duration=self.selected_recording['duration'],
                    name=name,
                    color=color
                )
            
            # Call callback
            if self.on_add_clip:
                self.on_add_clip(clip)
                logger.info(f"Added recording to timeline: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add recording to timeline: {e}")
            messagebox.showerror("Error", f"Failed to add recording:\n{e}")
    
    def _guess_clip_color(self, name: str) -> str:
        """Guess appropriate color based on recording name."""
        name_lower = name.lower()
        
        if 'pick' in name_lower:
            return get_clip_color('pick')
        elif 'place' in name_lower:
            return get_clip_color('place')
        elif 'move' in name_lower:
            return get_clip_color('move')
        elif 'home' in name_lower or 'reset' in name_lower:
            return get_clip_color('home')
        elif 'inspect' in name_lower or 'check' in name_lower:
            return get_clip_color('inspect')
        elif 'wait' in name_lower or 'pause' in name_lower:
            return get_clip_color('wait')
        else:
            return get_clip_color('custom')
    
    def _preview_selected(self):
        """Show detailed preview of selected recording."""
        if not self.selected_recording:
            return
        
        rec = self.selected_recording
        
        # Create preview window
        preview = tk.Toplevel(self)
        preview.title(f"Recording Preview - {rec['name']}")
        preview.geometry("400x300")
        preview.transient(self)
        
        # Info text
        info_frame = ttk.Frame(preview, padding="10")
        info_frame.pack(fill='both', expand=True)
        
        info_text = tk.Text(info_frame, wrap='word')
        info_text.pack(fill='both', expand=True)
        
        # Build info
        info_lines = [
            f"Recording Information",
            f"=" * 40,
            f"",
            f"Name: {rec['name']}",
            f"File: {rec['filepath']}",
            f"",
            f"Duration: {rec['duration']:.2f} seconds",
            f"Samples: {rec['sample_count']:,}",
            f"Sample Rate: {rec['sample_rate']:.1f} Hz",
            f"",
            f"File Size: {rec['file_size'] / 1024:.1f} KB",
            f"Created: {self._format_date(rec.get('created', ''))}",
            f"Modified: {self._format_date(rec.get('modified', ''))}",
            f"",
            f"First Timestamp: {rec.get('first_timestamp', 'N/A')}",
            f"Last Timestamp: {rec.get('last_timestamp', 'N/A')}",
        ]
        
        info_text.insert('1.0', '\n'.join(info_lines))
        info_text.config(state='disabled')
        
        # Close button
        ttk.Button(
            preview,
            text="Close",
            command=preview.destroy
        ).pack(pady=10)
    
    def _show_in_folder(self):
        """Open file explorer to show recording."""
        if not self.selected_recording:
            return
        
        try:
            import subprocess
            import platform
            
            filepath = Path(self.selected_recording['filepath'])
            
            if platform.system() == 'Windows':
                subprocess.run(['explorer', '/select,', str(filepath)])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '-R', str(filepath)])
            else:  # Linux
                subprocess.run(['xdg-open', str(filepath.parent)])
                
        except Exception as e:
            logger.error(f"Failed to show in folder: {e}")
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")
    
    def refresh(self):
        """Refresh the recordings list."""
        self._load_recordings()
    
    def get_selected_recording(self) -> Optional[Dict[str, Any]]:
        """Get currently selected recording."""
        return self.selected_recording


# Demo function
def demo_clip_library():
    """Demo the clip library."""
    root = tk.Tk()
    root.title("Clip Library Demo")
    root.geometry("600x500")
    
    def on_add_clip(clip):
        print(f"Add clip to timeline: {clip.name}")
        messagebox.showinfo("Clip Added", f"Would add clip:\n{clip.name}\nDuration: {clip.duration:.2f}s")
    
    library = ClipLibrary(root, on_add_clip=on_add_clip)
    library.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    demo_clip_library()

