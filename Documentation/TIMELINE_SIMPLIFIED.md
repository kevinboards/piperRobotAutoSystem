# Timeline Playback - Simplified Approach

## 🎯 New Approach: Sequential Program Playback

Based on user feedback, we've simplified the timeline playback to be a **program organizer** rather than a complex playback engine.

---

## Concept

### Timeline = Visual Program Organizer

The timeline is now a **visual way to organize** which recordings (programs) to run and in what order:

```
┌─────────────────────────────────────────────────────┐
│  Program 1    │ GAP │  Program 2  │  Program 3     │
│  pick.ppr     │ 2s  │  move.ppr   │  place.ppr     │
│  (5.3s)       │     │  (3.2s)     │  (8.1s)        │
└─────────────────────────────────────────────────────┘
```

When you click **Play**:
1. Plays `pick.ppr` using V1 player (works perfectly)
2. Waits 2 seconds (gap)
3. Plays `move.ppr` using V1 player
4. Plays `place.ppr` using V1 player
5. Done!

---

## Why This is Better

### ✅ Advantages

**Reliability:**
- Uses proven V1 player
- No complex async logic
- No SDK conversion issues
- Just works!

**Simplicity:**
- Easy to understand
- Easy to debug
- Minimal code
- Clear behavior

**Flexibility:**
- Each recording is independent
- Can test recordings individually first (V1 tab)
- Then combine into timeline (V2 tab)

**Safety:**
- If one recording fails, doesn't crash others
- Can stop between programs
- Clear program boundaries

### ❌ What We Removed

**Complex features we don't need:**
- Live trim application (can trim recordings beforehand)
- Real-time speed changes (use V1 player's speed control)
- Async complexity
- Custom playback engine

---

## How It Works Now

### Timeline Player Algorithm

```python
for clip in timeline.clips (in order):
    # Play the recording using V1 player
    player = PiperPlayer(piper, clip.recording_file, speed=clip.speed)
    player.play()  # Synchronous, blocks until done
    
    # Check for gap after this clip
    if next_clip exists and gap between them:
        time.sleep(gap_duration)  # Hold position
    
    # Continue to next clip
```

### Super Simple!

No async, no complex timing, just:
1. Play recording
2. Wait if gap
3. Next recording
4. Repeat

---

## Features Supported

### ✅ What Works

**Sequential Playback:**
- ✅ Plays recordings in timeline order
- ✅ Uses proven V1 player
- ✅ Reliable and stable

**Gaps:**
- ✅ Waits between recordings
- ✅ Robot holds last position
- ✅ Configurable gap duration

**Speed Control:**
- ✅ Per-clip speed multipliers
- ✅ Uses V1 player's speed system
- ✅ Range: 0.1x - 4.0x

**Progress Tracking:**
- ✅ Shows current clip name
- ✅ Updates playhead position
- ✅ Progress callbacks

**Controls:**
- ✅ Play from start or any position
- ✅ Stop playback
- ⚠️ Pause (stop between clips only)

### ⚠️ Limitations

**Trims:**
- Must trim recordings beforehand in V1 tab
- Can't apply trims during timeline playback
- Or edit .ppr files to remove unwanted sections

**Pause:**
- Can't pause mid-recording
- Stops after current recording finishes

---

## Workflow

### 1. Record Individual Programs (V1 Tab)

```
Record & Playback (V1):
1. Record "pick_part.ppr"
2. Test it (click Play to verify)
3. Record "move_to_station.ppr"
4. Test it
5. Record "place_part.ppr"
6. Test it
```

Each recording is a **complete, tested program**.

### 2. Organize into Timeline (V2 Tab)

```
Timeline Editor (V2):
1. Click "➕ Add Recording" → pick_part.ppr
2. Click "➕ Add Recording" → move_to_station.ppr
3. Drag to create 2-second gap
4. Click "➕ Add Recording" → place_part.ppr
5. Save timeline
```

Timeline is now a **visual plan** of the sequence.

### 3. Run the Sequence

```
1. Click "▶ Play"
2. Watches:
   - Plays pick_part.ppr (full recording)
   - Waits 2 seconds
   - Plays move_to_station.ppr
   - Plays place_part.ppr
   - Done!
```

---

## Benefits

### For You

**Easier to Debug:**
- Test each recording individually in V1
- Know each program works
- Then combine in timeline

**More Reliable:**
- Uses proven playback code
- No new complex systems
- Just plays files in order

**Clearer Organization:**
- Timeline shows the plan
- Visual arrangement
- Easy to understand

### For Development

**Much Simpler Code:**
- ~200 lines vs 600+ lines
- No async complexity
- Uses existing player
- Less to maintain

**More Stable:**
- Fewer edge cases
- Proven components
- Less to go wrong

---

## Implementation

### Old Approach (Complex)
```python
# Custom async playback engine
async def play():
    for clip in clips:
        data = read_ppr_file(clip.file)
        apply_trims(data)
        for point in data:
            send_to_robot(point)  # Direct SDK calls
            await asyncio.sleep(interval)
```

### New Approach (Simple)
```python
# Use existing V1 player
def play():
    for clip in clips:
        player = PiperPlayer(piper, clip.file, speed=clip.speed)
        player.play()  # Already works!
        
        if gap_after_clip:
            time.sleep(gap_duration)
```

**Much simpler!** ✅

---

## Timeline as Program Organizer

Think of the timeline as a **visual programming interface**:

```
Program Flow:
┌──────────────┐
│  Program 1   │  ← Tested, working .ppr file
│  pick.ppr    │
└──────────────┘
       ↓
   [Wait 2s]
       ↓
┌──────────────┐
│  Program 2   │  ← Tested, working .ppr file
│  move.ppr    │
└──────────────┘
       ↓
┌──────────────┐
│  Program 3   │  ← Tested, working .ppr file
│  place.ppr   │
└──────────────┘
```

Each block is a **complete, tested program**.  
Timeline arranges them in order.  
Click Play → Runs them sequentially.

---

## Testing

### Test Individual Programs First (V1)

```bash
python main.py
```

1. Click "Record & Playback (V1)" tab
2. Load "pick_part.ppr"
3. Click Play
4. Verify it works perfectly
5. Repeat for each recording

### Then Combine in Timeline (V2)

1. Click "Timeline Editor (V2)" tab
2. Add all tested recordings
3. Arrange with gaps as needed
4. Click Play
5. Runs entire sequence!

---

## Summary

**Old Way:** Complex custom playback engine  
**New Way:** Sequential playback using V1 player

**Result:**
- ✅ More reliable
- ✅ Easier to understand
- ✅ Simpler code
- ✅ Uses proven components
- ✅ Better for users

**Timeline = Visual Program Organizer** 🎯

---

**Status:** Simplified timeline playback implemented  
**Date:** December 2, 2025

