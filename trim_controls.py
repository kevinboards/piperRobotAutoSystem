"""
Trim control widgets for the Timeline UI.

Provides reusable GUI components for clip trimming.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import logging

from clip_editor import (
    format_trim_display, parse_trim_input,
    get_trim_slider_range, calculate_trim_percentage
)


logger = logging.getLogger(__name__)


class TrimControl(ttk.Frame):
    """
    A widget for controlling clip trim values.
    
    Provides dual sliders for trim start and trim end with visual feedback.
    """
    
    def __init__(
        self,
        parent,
        clip_duration: float,
        on_trim_change: Optional[Callable[[float, float], None]] = None,
        **kwargs
    ):
        """
        Initialize trim control.
        
        Args:
            parent: Parent widget
            clip_duration: Duration of the clip being trimmed
            on_trim_change: Callback when trim values change (trim_start, trim_end)
        """
        super().__init__(parent, **kwargs)
        
        self.clip_duration = clip_duration
        self.on_trim_change = on_trim_change
        
        # Trim values
        self.trim_start_var = tk.DoubleVar(value=0.0)
        self.trim_end_var = tk.DoubleVar(value=0.0)
        
        # Calculate slider range (max 50% of clip can be trimmed from each end)
        self.trim_min, self.trim_max = get_trim_slider_range(clip_duration, max_trim_percentage=50.0)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the trim control UI."""
        # Title
        title_label = ttk.Label(self, text="Clip Trimming", font=("Segoe UI", 10, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")
        
        # Trim Start Section
        trim_start_frame = ttk.LabelFrame(self, text="Trim Start", padding="5")
        trim_start_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")
        
        ttk.Label(trim_start_frame, text="Remove from beginning:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.trim_start_slider = ttk.Scale(
            trim_start_frame,
            from_=self.trim_min,
            to=self.trim_max,
            variable=self.trim_start_var,
            orient='horizontal',
            command=self._on_trim_start_change
        )
        self.trim_start_slider.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.trim_start_label = ttk.Label(trim_start_frame, text="0.0s", width=10)
        self.trim_start_label.grid(row=1, column=1, padx=5)
        
        trim_start_frame.columnconfigure(0, weight=1)
        
        # Trim End Section
        trim_end_frame = ttk.LabelFrame(self, text="Trim End", padding="5")
        trim_end_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")
        
        ttk.Label(trim_end_frame, text="Remove from end:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.trim_end_slider = ttk.Scale(
            trim_end_frame,
            from_=self.trim_min,
            to=self.trim_max,
            variable=self.trim_end_var,
            orient='horizontal',
            command=self._on_trim_end_change
        )
        self.trim_end_slider.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.trim_end_label = ttk.Label(trim_end_frame, text="0.0s", width=10)
        self.trim_end_label.grid(row=1, column=1, padx=5)
        
        trim_end_frame.columnconfigure(0, weight=1)
        
        # Info Section
        info_frame = ttk.Frame(self)
        info_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")
        
        # Visual representation
        self.visual_canvas = tk.Canvas(info_frame, height=40, bg='white', relief='solid', borderwidth=1)
        self.visual_canvas.grid(row=0, column=0, columnspan=3, sticky="ew", pady=5)
        
        # Duration info
        ttk.Label(info_frame, text="Original Duration:").grid(row=1, column=0, sticky="w", padx=5)
        self.original_duration_label = ttk.Label(info_frame, text=f"{self.clip_duration:.2f}s", font=("Segoe UI", 9))
        self.original_duration_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(info_frame, text="New Duration:").grid(row=2, column=0, sticky="w", padx=5)
        self.new_duration_label = ttk.Label(info_frame, text=f"{self.clip_duration:.2f}s", font=("Segoe UI", 9, "bold"))
        self.new_duration_label.grid(row=2, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Trimmed:").grid(row=3, column=0, sticky="w", padx=5)
        self.trimmed_percentage_label = ttk.Label(info_frame, text="0.0%", font=("Segoe UI", 9))
        self.trimmed_percentage_label.grid(row=3, column=1, sticky="w")
        
        info_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Reset", command=self._reset_trim).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Apply", command=self._apply_trim).pack(side='left', padx=5)
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        
        # Initial visual update
        self._update_visual()
    
    def _on_trim_start_change(self, value):
        """Handle trim start slider change."""
        trim_start = float(value)
        self.trim_start_label.config(text=format_trim_display(trim_start))
        self._update_visual()
        self._validate_and_callback()
    
    def _on_trim_end_change(self, value):
        """Handle trim end slider change."""
        trim_end = float(value)
        self.trim_end_label.config(text=format_trim_display(trim_end))
        self._update_visual()
        self._validate_and_callback()
    
    def _update_visual(self):
        """Update the visual trim representation."""
        trim_start = self.trim_start_var.get()
        trim_end = self.trim_end_var.get()
        
        # Update duration labels
        new_duration = max(0, self.clip_duration - trim_start - trim_end)
        self.new_duration_label.config(text=f"{new_duration:.2f}s")
        
        # Update percentage
        percentage = calculate_trim_percentage(self.clip_duration, trim_start, trim_end)
        self.trimmed_percentage_label.config(text=f"{percentage:.1f}%")
        
        # Change color based on amount trimmed
        if percentage > 75:
            self.trimmed_percentage_label.config(foreground="red")
        elif percentage > 50:
            self.trimmed_percentage_label.config(foreground="orange")
        else:
            self.trimmed_percentage_label.config(foreground="black")
        
        # Draw visual representation
        self._draw_visual_trim()
    
    def _draw_visual_trim(self):
        """Draw the visual trim representation on canvas."""
        canvas = self.visual_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        if width <= 1:  # Canvas not yet rendered
            width = 400
        
        trim_start = self.trim_start_var.get()
        trim_end = self.trim_end_var.get()
        
        if self.clip_duration <= 0:
            return
        
        # Calculate pixel positions
        trim_start_px = (trim_start / self.clip_duration) * width
        trim_end_px = width - ((trim_end / self.clip_duration) * width)
        
        # Draw trimmed portions (gray)
        if trim_start > 0:
            canvas.create_rectangle(0, 0, trim_start_px, height, fill="#CCCCCC", outline="")
            canvas.create_text(trim_start_px / 2, height / 2, text="Trimmed", fill="#666666", font=("Segoe UI", 8))
        
        if trim_end > 0:
            canvas.create_rectangle(trim_end_px, 0, width, height, fill="#CCCCCC", outline="")
            canvas.create_text((trim_end_px + width) / 2, height / 2, text="Trimmed", fill="#666666", font=("Segoe UI", 8))
        
        # Draw active portion (green)
        if trim_end_px > trim_start_px:
            canvas.create_rectangle(trim_start_px, 0, trim_end_px, height, fill="#4CAF50", outline="")
            active_width = trim_end_px - trim_start_px
            canvas.create_text(trim_start_px + active_width / 2, height / 2, text="Active", fill="white", font=("Segoe UI", 9, "bold"))
        
        # Draw boundaries
        if trim_start > 0:
            canvas.create_line(trim_start_px, 0, trim_start_px, height, fill="black", width=2)
        if trim_end > 0:
            canvas.create_line(trim_end_px, 0, trim_end_px, height, fill="black", width=2)
    
    def _validate_and_callback(self):
        """Validate trim values and call callback."""
        trim_start = self.trim_start_var.get()
        trim_end = self.trim_end_var.get()
        
        # Check if total trim exceeds duration
        if trim_start + trim_end > self.clip_duration:
            # Adjust trim_end to fit
            trim_end = max(0, self.clip_duration - trim_start)
            self.trim_end_var.set(trim_end)
            self.trim_end_label.config(text=format_trim_display(trim_end))
        
        # Call callback if set
        if self.on_trim_change:
            self.on_trim_change(trim_start, trim_end)
    
    def _reset_trim(self):
        """Reset trim values to zero."""
        self.trim_start_var.set(0.0)
        self.trim_end_var.set(0.0)
        self.trim_start_label.config(text="0.0s")
        self.trim_end_label.config(text="0.0s")
        self._update_visual()
        if self.on_trim_change:
            self.on_trim_change(0.0, 0.0)
    
    def _apply_trim(self):
        """Apply current trim values (trigger callback)."""
        if self.on_trim_change:
            self.on_trim_change(self.trim_start_var.get(), self.trim_end_var.get())
    
    def set_trim_values(self, trim_start: float, trim_end: float):
        """
        Set trim values programmatically.
        
        Args:
            trim_start: Trim from start
            trim_end: Trim from end
        """
        self.trim_start_var.set(trim_start)
        self.trim_end_var.set(trim_end)
        self.trim_start_label.config(text=format_trim_display(trim_start))
        self.trim_end_label.config(text=format_trim_display(trim_end))
        self._update_visual()
    
    def get_trim_values(self) -> tuple[float, float]:
        """
        Get current trim values.
        
        Returns:
            Tuple of (trim_start, trim_end)
        """
        return self.trim_start_var.get(), self.trim_end_var.get()
    
    def update_duration(self, new_duration: float):
        """
        Update the clip duration (if clip changes).
        
        Args:
            new_duration: New clip duration
        """
        self.clip_duration = new_duration
        self.trim_min, self.trim_max = get_trim_slider_range(new_duration, max_trim_percentage=50.0)
        
        # Update sliders
        self.trim_start_slider.config(to=self.trim_max)
        self.trim_end_slider.config(to=self.trim_max)
        
        # Update labels
        self.original_duration_label.config(text=f"{new_duration:.2f}s")
        
        # Re-validate current trim values
        trim_start = self.trim_start_var.get()
        trim_end = self.trim_end_var.get()
        
        if trim_start + trim_end > new_duration:
            # Reset if current trim is invalid
            self._reset_trim()
        else:
            self._update_visual()


class SimpleTrimControl(ttk.Frame):
    """
    A simplified trim control with just input fields (no sliders).
    
    Useful for compact UIs or when precise values are needed.
    """
    
    def __init__(
        self,
        parent,
        clip_duration: float,
        on_trim_change: Optional[Callable[[float, float], None]] = None,
        **kwargs
    ):
        """Initialize simple trim control."""
        super().__init__(parent, **kwargs)
        
        self.clip_duration = clip_duration
        self.on_trim_change = on_trim_change
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI."""
        # Trim Start
        ttk.Label(self, text="Trim Start:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.trim_start_entry = ttk.Entry(self, width=10)
        self.trim_start_entry.insert(0, "0.0")
        self.trim_start_entry.grid(row=0, column=1, padx=5, pady=2)
        self.trim_start_entry.bind("<Return>", lambda e: self._on_trim_change())
        self.trim_start_entry.bind("<FocusOut>", lambda e: self._on_trim_change())
        
        ttk.Label(self, text="s").grid(row=0, column=2, sticky="w")
        
        # Trim End
        ttk.Label(self, text="Trim End:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.trim_end_entry = ttk.Entry(self, width=10)
        self.trim_end_entry.insert(0, "0.0")
        self.trim_end_entry.grid(row=1, column=1, padx=5, pady=2)
        self.trim_end_entry.bind("<Return>", lambda e: self._on_trim_change())
        self.trim_end_entry.bind("<FocusOut>", lambda e: self._on_trim_change())
        
        ttk.Label(self, text="s").grid(row=1, column=2, sticky="w")
        
        # New Duration
        ttk.Label(self, text="New Duration:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.duration_label = ttk.Label(self, text=f"{self.clip_duration:.2f}s", font=("Segoe UI", 9, "bold"))
        self.duration_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
    
    def _on_trim_change(self):
        """Handle trim value change."""
        try:
            trim_start = parse_trim_input(self.trim_start_entry.get())
            trim_end = parse_trim_input(self.trim_end_entry.get())
            
            if trim_start is None or trim_end is None:
                return
            
            # Validate
            if trim_start < 0 or trim_end < 0:
                return
            
            if trim_start + trim_end > self.clip_duration:
                return
            
            # Update duration display
            new_duration = self.clip_duration - trim_start - trim_end
            self.duration_label.config(text=f"{new_duration:.2f}s")
            
            # Call callback
            if self.on_trim_change:
                self.on_trim_change(trim_start, trim_end)
                
        except Exception as e:
            logger.error(f"Error parsing trim values: {e}")
    
    def set_trim_values(self, trim_start: float, trim_end: float):
        """Set trim values."""
        self.trim_start_entry.delete(0, tk.END)
        self.trim_start_entry.insert(0, f"{trim_start:.2f}")
        
        self.trim_end_entry.delete(0, tk.END)
        self.trim_end_entry.insert(0, f"{trim_end:.2f}")
        
        new_duration = self.clip_duration - trim_start - trim_end
        self.duration_label.config(text=f"{new_duration:.2f}s")
    
    def get_trim_values(self) -> tuple[float, float]:
        """Get current trim values."""
        trim_start = parse_trim_input(self.trim_start_entry.get()) or 0.0
        trim_end = parse_trim_input(self.trim_end_entry.get()) or 0.0
        return trim_start, trim_end


# Demo function for testing
def demo_trim_control():
    """Demo the trim control widget."""
    root = tk.Tk()
    root.title("Trim Control Demo")
    root.geometry("500x450")
    
    def on_trim_change(trim_start, trim_end):
        print(f"Trim changed: start={trim_start:.2f}s, end={trim_end:.2f}s")
    
    # Full trim control
    trim_control = TrimControl(root, clip_duration=10.5, on_trim_change=on_trim_change)
    trim_control.pack(padx=20, pady=20, fill='both', expand=True)
    
    # Set initial trim values
    trim_control.set_trim_values(0.5, 0.2)
    
    root.mainloop()


if __name__ == "__main__":
    demo_trim_control()

