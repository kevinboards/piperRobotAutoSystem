# How to Test the Timeline System

## ✅ Timeline is Now Integrated into main.py!

The timeline system is now part of the main application. Here's how to use it:

---

## Running the Application

```bash
cd PiperAutomationSystem
python main.py
```

---

## What You'll See

The application now has **2 tabs**:

### Tab 1: Record & Playback (V1)
- The original V1 interface
- Record button
- Play button
- Load file button
- Speed controls (0.1x - 4.0x)
- Progress bar

### Tab 2: Timeline Editor (V2) ⭐ NEW!
- Visual timeline canvas
- File operations (New/Load/Save)
- Transport controls (Play/Pause/Stop)
- Zoom controls
- Timeline with clips
- Information bar

---

## How to Use the Timeline

### 1. Switch to Timeline Tab
Click the **"Timeline Editor (V2)"** tab at the top

### 2. Create a New Timeline
- Click **"New"** button
- Enter a name for your timeline
- You'll see an empty timeline canvas

### 3. Load an Existing Timeline
- Click **"Load"** button
- Browse to `timelines/` folder
- Select a `.ppt` file
- The timeline will load with all clips

### 4. Interact with Timeline
- **Click and drag** clips to move them
- **Mouse wheel** to zoom in/out
- **Click ruler** to set playhead position
- **Select clip** - Click on it (yellow border)
- **Delete clip** - Select it, press Delete key
- **Zoom buttons** - Use ➕ ➖ or "Fit"

### 5. Save Your Timeline
- Click **"Save"** button
- Choose location and filename
- Timeline saved as `.ppt` file

---

## Testing with Sample Data

### Option 1: Use the Demo Script
The demo script creates a sample timeline automatically:

```bash
python timeline_panel.py
```

This shows the timeline with 3 pre-loaded clips.

### Option 2: Create Sample Timeline
Run the sample timeline creator:

```bash
python create_sample_timeline.py
```

This creates `timelines/Sample Assembly Sequence.ppt` which you can then load in main.py.

### Option 3: Load in main.py
1. Run `python main.py`
2. Click "Timeline Editor (V2)" tab
3. Click "Load" button
4. Navigate to `timelines/` folder
5. Select `Sample Assembly Sequence.ppt`
6. You'll see the timeline with clips!

---

## Current Limitations

### ⚠️ Playback Not Yet Implemented
When you click "Play" on the timeline, you'll see a message:
> "Timeline playback will be implemented in Phase 6!"

This is expected! Phase 6 will add the playback engine.

### ✅ What Works Now
- Visual timeline display
- Drag-and-drop clips
- Zoom in/out
- Save/load timelines
- Clip selection
- File management
- All UI interactions

### ⏳ Coming in Phase 6
- Actual timeline playback
- Sending commands to robot
- Playback with gaps
- Applying trims during playback
- Speed multipliers

---

## File Locations

### Recordings
- Location: `PiperAutomationSystem/recordings/`
- Format: `.ppr` files
- Created by: V1 Record function

### Timelines
- Location: `PiperAutomationSystem/timelines/`
- Format: `.ppt` files (JSON)
- Created by: V2 Timeline Editor

---

## Troubleshooting

### "I don't see the timeline tab"
- Make sure you're running the latest `main.py`
- Check that `timeline_panel.py` exists
- Look for any error messages in console

### "Timeline is empty"
- Click "Load" to load an existing timeline
- Or run `create_sample_timeline.py` first
- Or create clips manually (Phase 5 will add clip library)

### "Drag and drop doesn't work"
- Make sure you're clicking directly on a clip
- The clip should have a yellow border when selected
- Try clicking and holding, then dragging

### "Can't zoom"
- Use mouse wheel over the timeline canvas
- Or use the ➕ ➖ buttons
- Or click "Fit" to see everything

---

## Quick Test Checklist

- [ ] Run `python main.py`
- [ ] See two tabs at top
- [ ] Click "Timeline Editor (V2)" tab
- [ ] See timeline canvas with controls
- [ ] Click "Load" button
- [ ] Browse to `timelines/` folder
- [ ] Select a `.ppt` file (or create one first)
- [ ] See clips on timeline
- [ ] Try dragging a clip
- [ ] Try zooming with mouse wheel
- [ ] Click "Save" to save changes

---

## Next Steps

### To Create Your First Timeline:

1. **Record some movements** (V1 tab)
   - Switch to "Record & Playback (V1)" tab
   - Click "Record"
   - Move robot
   - Click "Stop Recording"
   - Files saved to `recordings/`

2. **Create timeline** (V2 tab - Phase 5 will make this easier)
   - For now, use `create_sample_timeline.py`
   - Or manually create timeline in code
   - Phase 5 will add drag-from-library feature

3. **Arrange clips**
   - Load timeline in V2 tab
   - Drag clips to desired positions
   - Adjust gaps between clips
   - Save timeline

4. **Play timeline** (Phase 6)
   - Coming soon!
   - Will play entire sequence
   - With gaps and trims applied

---

## Summary

**What's Working:**
✅ Visual timeline display
✅ Drag-and-drop editing
✅ Zoom and navigation
✅ Save/load projects
✅ Integrated into main.py
✅ Two-tab interface

**What's Coming:**
⏳ Clip library panel (Phase 5)
⏳ Timeline playback (Phase 6)
⏳ Clip properties panel (Phase 7)

---

**Status:** Timeline UI fully integrated and functional!  
**Test it:** `python main.py` → Click "Timeline Editor (V2)" tab  
**Date:** December 2, 2025

