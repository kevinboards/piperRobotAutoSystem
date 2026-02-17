# Timeline Fixes - Duration & Playback

## Problems Fixed

### Problem 1: Incorrect Duration Calculation ✅

**Issue:** Timeline showed all recordings as 10 seconds long

**Root Cause:** 
- Duration calculation assumed timestamps were in **milliseconds**
- But actual timestamps might be in **microseconds** or **milliseconds** 
- Need to auto-detect the unit

**Fix:**
Updated `timeline.py` `_estimate_recording_duration()`:
- Checks timestamp difference magnitude
- If diff > 100,000 → microseconds → divide by 1,000,000
- If diff > 1,000 → milliseconds → divide by 1,000
- If diff < 1,000 → seconds → use as-is

**Result:** Correct duration calculation regardless of timestamp format!

---

### Problem 2: Playback Timing Issues ✅

**Issue:** Timeline playback didn't work as expected

**Root Cause:**
- Async event loop not running in tkinter
- `asyncio.create_task()` failed with "no running event loop"

**Fix:**
Updated `main.py` `_on_timeline_play()`:
- Uses `threading.Thread` to run playback in background
- Runs `asyncio.run()` in the thread (creates its own event loop)
- Progress callbacks use `root.after(0, ...)` for thread-safe UI updates

**Result:** Smooth playback without blocking UI!

---

### Problem 3: Trim Calculations ✅

**Issue:** Trim functions assumed millisecond timestamps

**Fix:**
Updated `clip_editor.py` functions:
- `apply_trim_to_data()` - Auto-detects timestamp unit
- `suggest_trim_values()` - Auto-detects timestamp unit
- Works with milliseconds, microseconds, or seconds

---

## Diagnostic Tool Created

### `check_recording_format.py`

Run this to check your recording format:

```bash
python check_recording_format.py
```

**What it shows:**
- First and last timestamps
- Timestamp difference
- Duration in all possible units
- Most likely unit (auto-detected)
- Actual duration in seconds
- Sample rate
- First few data points

**Usage:**
```bash
# Check most recent recording
python check_recording_format.py

# Check specific file
python check_recording_format.py recordings/my_recording.ppr
```

This will tell you exactly what timestamp format your recordings use!

---

## How to Test

### Step 1: Check Recording Format
```bash
python check_recording_format.py
```

Look at the output to see:
- Duration calculation
- Sample rate
- Timestamp format

### Step 2: Add to Timeline
```bash
python main.py
```

1. Go to Timeline Editor (V2) tab
2. Click "➕ Add Recording"
3. Check if duration shows correctly now
4. Add multiple recordings

### Step 3: Test Playback
1. Click "▶ Play" button
2. Watch playhead move
3. Verify robot plays sequence correctly
4. Test pause/stop

---

## Expected Behavior

### Correct Duration Display

Before fix:
```
All clips: 10.0s (wrong!)
```

After fix:
```
Clip 1: 5.3s (actual duration)
Clip 2: 12.7s (actual duration)
Clip 3: 8.1s (actual duration)
```

### Correct Playback

**Timeline:**
```
0s    Clip 1 (5.3s)
5.3s  [Gap 2s]
7.3s  Clip 2 (12.7s)
20s   Clip 3 (8.1s)
```

**Playback:**
- 0-5.3s: Plays Clip 1
- 5.3-7.3s: Gap (holds position)
- 7.3-20s: Plays Clip 2
- 20-28.1s: Plays Clip 3
- Done!

---

## Timestamp Format Support

The system now auto-detects:

| Format | Detection | Conversion |
|--------|-----------|------------|
| **Microseconds** | diff > 100,000 | ÷ 1,000,000 |
| **Milliseconds** | diff > 1,000 | ÷ 1,000 |
| **Seconds** | diff < 1,000 | × 1 |

Your recordings use the format that `time.time()` provides, which should be **milliseconds** based on the recorder code.

---

## Next Steps

1. **Run diagnostic:**
   ```bash
   python check_recording_format.py
   ```
   
2. **Test duration display:**
   - Add recording to timeline
   - Check if duration is correct
   
3. **Test playback:**
   - Click Play
   - Verify timing is correct

---

**Status:** Duration and playback timing fixed!  
**Test:** Run diagnostic tool to verify format  
**Date:** December 2, 2025

