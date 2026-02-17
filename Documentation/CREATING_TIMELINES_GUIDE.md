# Quick Start: Creating Your First Timeline

## 🎬 How to Create a Timeline from Recordings

Now you can easily create timelines from your `.ppr` recording files!

---

## Step-by-Step Workflow

### 1. Record Some Movements (V1 Tab)

```bash
python main.py
```

1. Click **"Record & Playback (V1)"** tab
2. Click **"Record"** button
3. Move the robot through desired motions
4. Click **"Stop Recording"**
5. Repeat for each movement you want (pick, place, move, etc.)

Your recordings are saved in `recordings/` folder as `.ppr` files.

---

### 2. Create Timeline (V2 Tab)

1. Click **"Timeline Editor (V2)"** tab
2. Click **"New"** button (or start with empty timeline)
3. Click **"➕ Add Recording"** button
4. Browse to `recordings/` folder
5. Select a `.ppr` file
6. Click "Open"

**The recording is now on your timeline!** 🎉

---

### 3. Add More Recordings

Keep clicking **"➕ Add Recording"** to add more clips:
- Each new clip is added at the **end** of the timeline
- You can then **drag clips** to rearrange them
- Create **gaps** by dragging clips apart
- **Zoom** to see everything

---

### 4. Arrange Your Timeline

Now you can:
- **Drag clips** to new positions
- **Create gaps** between clips (robot will hold position)
- **Select clips** by clicking
- **Delete clips** with Delete key
- **Zoom in/out** with mouse wheel
- **Fit view** with "Fit" button

---

### 5. Save Your Timeline

1. Click **"Save"** button
2. Choose location (defaults to `timelines/` folder)
3. Enter filename
4. Click "Save"

Your timeline is saved as a `.ppt` file!

---

## Example Workflow

Let's create a "Pick and Place" timeline:

### Step 1: Record Movements
```
Record & Playback (V1) tab:
1. Record "pick_part.ppr" - Robot picks up part
2. Record "move_to_station.ppr" - Robot moves to assembly station
3. Record "place_part.ppr" - Robot places part
4. Record "return_home.ppr" - Robot returns to home position
```

### Step 2: Build Timeline
```
Timeline Editor (V2) tab:
1. Click "New" → Name: "Assembly Sequence"
2. Click "➕ Add Recording" → Select "pick_part.ppr"
3. Click "➕ Add Recording" → Select "move_to_station.ppr"
4. Click "➕ Add Recording" → Select "place_part.ppr"
5. Click "➕ Add Recording" → Select "return_home.ppr"
```

### Step 3: Arrange
```
- Drag "move_to_station" to create 2-second gap after "pick_part"
- Drag "place_part" to create 1-second gap after "move_to_station"
- Use mouse wheel to zoom in/out
- Click "Fit" to see entire sequence
```

### Step 4: Save
```
- Click "Save"
- Save as "Assembly_Sequence.ppt"
```

---

## What Each Button Does

### Timeline Tab Buttons

| Button | What It Does |
|--------|--------------|
| **New** | Create new empty timeline |
| **Load** | Load existing `.ppt` timeline file |
| **Save** | Save timeline as `.ppt` file |
| **➕ Add Recording** | Add a `.ppr` recording to timeline |
| **▶ Play** | Play timeline (Phase 6 - coming soon) |
| **⏸ Pause** | Pause playback |
| **⏹ Stop** | Stop and return to start |
| **➕** (zoom) | Zoom in |
| **➖** (zoom) | Zoom out |
| **Fit** | Zoom to fit entire timeline |

---

## File Types Explained

### `.ppr` Files (Recordings)
- **Created by:** V1 Record function
- **Location:** `recordings/` folder
- **Contains:** Robot position data at 200 Hz
- **Used for:** Adding to timelines

### `.ppt` Files (Timelines)
- **Created by:** V2 Timeline Editor
- **Location:** `timelines/` folder  
- **Contains:** Arrangement of `.ppr` clips with gaps, trims, speeds
- **Used for:** Saving timeline projects

---

## Tips & Tricks

### 🎯 Positioning Clips
- New recordings are added at the **end** of the timeline
- **Drag** clips left/right to reposition
- **Gaps** appear automatically when clips don't touch

### 🔍 Viewing
- **Mouse wheel** over timeline to zoom
- **Click ruler** to move playhead
- **Fit button** to see everything at once

### ✂️ Editing
- **Click** clip to select (yellow border)
- **Delete key** to remove selected clip
- **Drag** to move clips around

### 💾 Saving
- **Save often!** Timeline changes aren't auto-saved
- **Descriptive names** help organize projects
- **`.ppt` files** are JSON (human-readable)

---

## Current Limitations

### ⚠️ What Doesn't Work Yet

**Playback (Phase 6)**
- Timeline playback not implemented yet
- Use V1 tab to play individual recordings
- Phase 6 will add full timeline playback

**Trimming (Phase 7)**
- Can't trim clips from timeline yet
- Trim controls exist but not integrated
- Phase 7 will add clip properties panel

**Clip Library (Phase 5)**
- No visual library of recordings yet
- Must use "Add Recording" button
- Phase 5 will add drag-and-drop library

### ✅ What Works Now

- ✅ Add recordings to timeline
- ✅ Drag clips to rearrange
- ✅ Create gaps between clips
- ✅ Zoom and navigate
- ✅ Save/load timeline projects
- ✅ Visual timeline display
- ✅ Clip selection and deletion

---

## Troubleshooting

### "Add Recording button doesn't show up"
- Make sure you're on the **"Timeline Editor (V2)"** tab
- Look for it after the New/Load/Save buttons
- It has a ➕ icon

### "Can't find my recordings"
- Recordings are in `recordings/` folder
- Must be `.ppr` files
- Record some movements first in V1 tab

### "Clip appears but I can't see it"
- Try clicking **"Fit"** button to zoom out
- New clips are added at the end
- Scroll or zoom to see them

### "How do I play the timeline?"
- Timeline playback is Phase 6 (coming soon!)
- For now, use V1 tab to play individual `.ppr` files
- Timeline arranges them for future playback

---

## Next Steps

Once you have a timeline created:

1. **Phase 5** will add a visual library of recordings
2. **Phase 6** will add timeline playback (the big one!)
3. **Phase 7** will add trim controls per clip
4. **Phase 8** will add advanced editing operations

But you can **start creating timelines now** and they'll be ready to play when Phase 6 is complete!

---

**Status:** Timeline creation fully functional!  
**Test it:** `python main.py` → Timeline Editor (V2) tab → "➕ Add Recording"  
**Date:** December 2, 2025

