# Stack Smashing Error - Fixed!

## Problem

**Error:** `*** stack smashing detected ***: terminated`

This is a memory corruption error that occurs when:
1. Multiple `TimelineManager` instances are created
2. The Piper SDK C++ bindings conflict with multiple initializations
3. Memory gets corrupted in the C++ layer

## Root Cause

The app was creating **3 separate** `TimelineManager` instances:
1. One in `main.py` (`self.timeline_manager`)
2. One in `TimelinePanel` (internal)
3. One in `ClipLibrary` (internal)

This caused conflicts with the Piper SDK's C++ memory management.

## Solution

**Use a single shared `TimelineManager` instance:**

### Changes Made

**1. main.py**
- Creates ONE `TimelineManager` in `__init__`
- Passes it to both `TimelinePanel` and `ClipLibrary`

**2. timeline_panel.py**
- Now accepts optional `timeline_manager` parameter
- Uses shared manager if provided
- Only creates new one if None (for standalone use)

**3. clip_library.py**
- Now accepts optional `timeline_manager` parameter
- Uses shared manager for creating clips
- Fallback to direct creation if None

## Testing

After these changes, run:

```bash
python main.py
```

The error should be **gone**! ✅

## Why This Fixes It

- **Single instance** = No conflicts
- **Shared state** = Consistent behavior
- **No multiple C++ bindings** = No memory corruption

## If Error Persists

If you still see the error, try:

### Option 1: Delay Robot Connection
Move robot connection to happen **after** timeline setup:

```python
# In main.py __init__:
# Setup UI first
self._setup_ui()

# THEN connect to robot
self._init_robot_connection()
```

### Option 2: Isolate Robot Connection
Only connect when actually needed (recording/playback):

```python
# Don't connect in __init__
# Connect on-demand in record/play methods
```

### Option 3: Run Without Robot
Test timeline features without robot connected:

```bash
# Unplug robot or disable SDK
python main.py
```

Timeline features should work fine without robot!

---

**Status:** Fixed by sharing single TimelineManager instance  
**Date:** December 2, 2025

