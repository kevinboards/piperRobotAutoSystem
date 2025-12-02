# Piper Automation System - V2 Implementation Plan

## V1 Accomplishments ✅

Before we move forward, let's document what V1 achieved:

### Core Functionality (Complete)
- ✅ Real-time recording at 200 Hz
- ✅ Human-readable .ppr file format
- ✅ Accurate timestamp-based playback
- ✅ GUI with record/play/load functions
- ✅ Joint angles + Cartesian + Gripper capture
- ✅ Speed control (0.5x - 2.0x)
- ✅ Progress tracking
- ✅ Proper robot initialization (slave mode, enable, gripper)
- ✅ Error handling and logging
- ✅ Comprehensive documentation

### Technical Achievements
- ✅ Proper SDK integration
- ✅ Thread-safe operation
- ✅ Buffered file I/O
- ✅ Fixed all major bugs (gripper, timing, slave mode)
- ✅ Diagnostic and testing tools

**Status:** V1 is production-ready and working! 🎉

---

## V2 Vision: Timeline-Based Robot Sequencing

Transform the system from a **simple record/playback tool** into a **professional robot sequencing workstation** with timeline editing, composition, and advanced playback features.

### Key Analogy
Think: **Adobe Premiere or Audacity for Robot Movement**

---

## V2 Feature Breakdown

### 1. Extended Playback Speed Control
**Goal:** Allow faster playback up to 4x speed

**Current State:** 0.5x - 2.0x  
**V2 Target:** 0.1x - 4.0x

**Changes Required:**
- Update speed slider range
- Test robot can handle 4x speed safely
- Add speed presets (0.25x, 0.5x, 1x, 2x, 4x)
- Add safety warnings for high speeds
- Validate robot doesn't skip positions at high speed

---

### 2. Timeline Panel System ⭐ MAJOR FEATURE
**Goal:** Visual timeline where users can compose sequences from multiple recordings

**Analogy:** Like audio tracks in a DAW (Digital Audio Workstation)

**Key Components:**

#### A. Timeline Data Structure
```python
class TimelineClip:
    """Represents a recording segment on the timeline"""
    id: str                          # Unique clip ID
    recording_file: str              # Path to .ppr file
    start_time: float                # Start time on timeline (seconds)
    duration: float                  # Clip duration (seconds)
    trim_start: float                # Trim from beginning (seconds)
    trim_end: float                  # Trim from end (seconds)
    speed_multiplier: float          # Individual clip speed
    enabled: bool                    # Is clip active?
    name: str                        # Display name
    color: str                       # Visual color for UI

class Timeline:
    """Main timeline composition"""
    clips: List[TimelineClip]        # All clips on timeline
    total_duration: float            # Total timeline length
    current_position: float          # Playhead position
    name: str                        # Timeline name
    created: datetime
    modified: datetime
```

#### B. Timeline File Format (.ppt - Piper Program Timeline)
```json
{
  "version": "2.0",
  "name": "My Robot Sequence",
  "created": "2025-12-01T14:30:00",
  "modified": "2025-12-01T15:45:00",
  "clips": [
    {
      "id": "clip_001",
      "recording_file": "recordings/2025-12-01-143022.ppr",
      "start_time": 0.0,
      "duration": 10.5,
      "trim_start": 0.5,
      "trim_end": 0.2,
      "speed_multiplier": 1.0,
      "enabled": true,
      "name": "Pick Part A",
      "color": "#4CAF50"
    },
    {
      "id": "clip_002",
      "recording_file": "recordings/2025-12-01-143045.ppr",
      "start_time": 15.0,
      "duration": 8.0,
      "trim_start": 0.0,
      "trim_end": 0.0,
      "speed_multiplier": 1.5,
      "enabled": true,
      "name": "Place Part A",
      "color": "#2196F3"
    }
  ]
}
```

#### C. Timeline UI Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  File  Edit  Timeline  Playback  View  Help                     │
├─────────────────────────────────────────────────────────────────┤
│  ▶ Play  ⏸ Pause  ⏹ Stop   |  🔊 0.5x [====|====] 4.0x        │
├─────────────────────────────────────────────────────────────────┤
│  Timeline: 00:00.0 / 00:35.5                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 0s    5s    10s   15s   20s   25s   30s   35s            │ │
│  │ |─────|─────|─────|─────|─────|─────|─────|               │ │
│  │ ▼ [    Pick Part A     ]                                  │ │ Clip 1
│  │              ┊    GAP    ┊                                │ │
│  │              ┊           [  Place Part A  ]               │ │ Clip 2
│  │              ┊                  ┊                         │ │
│  │              ┊                  [  Return Home  ]         │ │ Clip 3
│  │              ▲ Playhead                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Selected Clip: "Pick Part A"                                  │
│  • Start: 00:00.0  • Duration: 10.5s  • Speed: 1.0x           │
│  • Trim Start: [  0.5s  ]  • Trim End: [  0.2s  ]             │
│  [✓] Enabled  [Rename] [Duplicate] [Delete]                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. Time Gaps Between Clips
**Goal:** Add controllable delays between recordings

**Implementation:**
- Gaps are represented by empty space between clips
- No actual "gap clip" - just clip positioning
- During playback, robot holds position during gaps
- User can drag clips to create/adjust gaps

**Example:**
```
Clip 1: 0s → 10s
GAP:    10s → 15s  (5 second pause)
Clip 2: 15s → 23s
```

During gap playback:
```python
# Hold last position from previous clip
last_position = get_last_position_from_clip(clip_1)
hold_until = gap_end_time

while current_time < hold_until:
    send_position(last_position)  # Keep sending same position
    time.sleep(0.005)
```

---

### 4. Clip Trimming System
**Goal:** Trim recordings like video editing

**Features:**

#### A. Trim Start (Remove from beginning)
```
Original:  [===========RECORDING===========]
Trimmed:      [======RECORDING===========]
           ^^^
         Removed
```

#### B. Trim End (Remove from end)
```
Original:  [===========RECORDING===========]
Trimmed:   [===========RECORDING======]
                                     ^^^
                                   Removed
```

#### C. Trim UI
```
┌─────────────────────────────────────────────┐
│  Clip: "Pick Part A"                        │
│  ┌───────────────────────────────────────┐  │
│  │ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] │  │
│  │  ▲                               ▲    │  │
│  │ Trim                           Trim   │  │
│  │ Start                          End    │  │
│  └───────────────────────────────────────┘  │
│  Start: [ 0.5s ]  End: [ 0.2s ]            │
│  Duration: 10.5s → 9.8s (after trim)       │
└─────────────────────────────────────────────┘
```

#### D. Implementation
```python
def apply_trim(recording_data, trim_start, trim_end):
    """
    Apply trim to recording data.
    
    Args:
        recording_data: Full recording data
        trim_start: Seconds to remove from start
        trim_end: Seconds to remove from end
    
    Returns:
        Trimmed data list
    """
    # Convert times to sample indices
    start_idx = int(trim_start * sample_rate)
    end_idx = len(recording_data) - int(trim_end * sample_rate)
    
    # Return trimmed data
    return recording_data[start_idx:end_idx]
```

---

### 5. Timeline Playback Engine
**Goal:** Play entire timeline sequentially

**Playback Algorithm:**

```python
def play_timeline(timeline):
    """
    Play all clips in timeline order.
    """
    # Sort clips by start time
    sorted_clips = sorted(timeline.clips, key=lambda c: c.start_time)
    
    current_time = 0.0
    last_position = None
    
    for clip in sorted_clips:
        # Handle gap before this clip
        if clip.start_time > current_time:
            gap_duration = clip.start_time - current_time
            hold_position(last_position, gap_duration)
        
        # Play this clip
        last_position = play_clip(
            clip.recording_file,
            trim_start=clip.trim_start,
            trim_end=clip.trim_end,
            speed=clip.speed_multiplier
        )
        
        current_time = clip.start_time + clip.duration
```

---

## V2 Architecture

### New Modules

#### 1. `timeline.py` - Timeline Management
```python
class TimelineManager:
    """Manages timeline composition and operations"""
    
    def __init__(self)
    def create_timeline(name: str) -> Timeline
    def load_timeline(filepath: str) -> Timeline
    def save_timeline(timeline: Timeline, filepath: str)
    def add_clip(timeline: Timeline, recording_file: str, start_time: float)
    def remove_clip(timeline: Timeline, clip_id: str)
    def move_clip(timeline: Timeline, clip_id: str, new_start: float)
    def trim_clip(timeline: Timeline, clip_id: str, trim_start: float, trim_end: float)
    def duplicate_clip(timeline: Timeline, clip_id: str)
    def get_clip_at_time(timeline: Timeline, time: float) -> TimelineClip
    def validate_timeline(timeline: Timeline) -> bool
```

#### 2. `timeline_player.py` - Timeline Playback
```python
class TimelinePlayer:
    """Plays back entire timelines"""
    
    def __init__(self, piper_interface, timeline: Timeline)
    def play()
    def pause()
    def stop()
    def seek(time: float)
    def get_progress() -> float
    def get_current_clip() -> TimelineClip
```

#### 3. `clip_editor.py` - Clip Editing Operations
```python
class ClipEditor:
    """Handles clip trimming and editing"""
    
    def __init__(self, clip: TimelineClip)
    def trim_start(seconds: float)
    def trim_end(seconds: float)
    def get_trimmed_data() -> List[Dict]
    def preview_trim() -> Dict
    def apply_speed(multiplier: float)
```

#### 4. `timeline_ui.py` - Timeline GUI Component
```python
class TimelinePanel(ttk.Frame):
    """Timeline visualization and editing UI"""
    
    def __init__(self, parent, timeline_manager: TimelineManager)
    def draw_timeline()
    def add_clip_to_timeline(recording_file: str)
    def on_clip_click(clip_id: str)
    def on_clip_drag(clip_id: str, new_position: float)
    def update_playhead(position: float)
    def zoom_in()
    def zoom_out()
```

### Updated Modules

#### 1. `main.py` - GUI Updates
- Add timeline panel below existing controls
- Add timeline menu (New, Open, Save, Export)
- Add clip library panel (available recordings)
- Add clip properties panel
- Update play button to play timeline
- Add timeline zoom controls

#### 2. `player.py` - Enhanced Features
- Support for individual clip speed
- Support for starting at arbitrary position (trimming)
- Clip-based playback (not just full files)

---

## V2 File Structure

```
PiperAutomationSystem/
├── V1 Files (Existing)
│   ├── main.py                 # Will be updated
│   ├── recorder.py             # Keep as-is
│   ├── player.py               # Will be enhanced
│   ├── ppr_file_handler.py     # Keep as-is
│   └── ...
│
├── V2 New Files
│   ├── timeline.py             # Timeline management
│   ├── timeline_player.py      # Timeline playback
│   ├── clip_editor.py          # Clip editing
│   ├── timeline_ui.py          # Timeline GUI
│   ├── ppt_file_handler.py     # .ppt timeline files
│   └── clip_library.py         # Recording library management
│
├── timelines/                  # Saved timeline files
│   └── *.ppt files
│
└── Documentation
    ├── V2_IMPLEMENTATION_PLAN.md     # This file
    ├── V2_TIMELINE_GUIDE.md          # User guide
    └── V2_API_REFERENCE.md           # Developer API docs
```

---

## Implementation Phases

### Phase 1: Extended Speed Control (1-2 days)
**Goal:** Support 0.1x - 4.0x playback speeds

**Tasks:**
- [ ] Update speed slider range in `main.py`
- [ ] Add speed preset buttons (0.25x, 0.5x, 1x, 2x, 4x)
- [ ] Test robot at high speeds (safety check)
- [ ] Add speed warning dialog for >2x
- [ ] Update player to handle full speed range
- [ ] Test with various recordings

**Deliverables:**
- Extended speed range working
- Safety checks in place
- User can select presets or custom speed

---

### Phase 2: Timeline Data Model (2-3 days)
**Goal:** Create timeline and clip data structures

**Tasks:**
- [ ] Create `timeline.py` module
- [ ] Implement `TimelineClip` class
- [ ] Implement `Timeline` class
- [ ] Create `ppt_file_handler.py` for timeline files
- [ ] Write save/load functions for .ppt files
- [ ] Create timeline validation functions
- [ ] Write unit tests for timeline operations
- [ ] Create sample timeline for testing

**Deliverables:**
- Timeline data model complete
- Can save/load timelines to JSON
- Basic timeline operations working (add, remove, move clips)

---

### Phase 3: Clip Trimming System (2-3 days)
**Goal:** Implement clip trimming functionality

**Tasks:**
- [ ] Create `clip_editor.py` module
- [ ] Implement trim_start function
- [ ] Implement trim_end function
- [ ] Add trim preview function
- [ ] Create trim UI component
- [ ] Add trim sliders/input fields
- [ ] Implement trim validation (can't trim more than duration)
- [ ] Test trimming with various recordings

**Deliverables:**
- Clip trimming works correctly
- UI for adjusting trims
- Preview shows trimmed result

---

### Phase 4: Timeline UI Component (3-4 days)
**Goal:** Build visual timeline panel

**Tasks:**
- [ ] Create `timeline_ui.py` module
- [ ] Design timeline canvas/drawing area
- [ ] Implement clip rendering on timeline
- [ ] Add playhead indicator
- [ ] Implement time ruler (0s, 5s, 10s markers)
- [ ] Add clip drag-and-drop
- [ ] Implement clip selection
- [ ] Add right-click context menu
- [ ] Implement zoom in/out
- [ ] Add scroll/pan for long timelines
- [ ] Integrate with main GUI

**Deliverables:**
- Visual timeline panel in GUI
- Can add/move/select clips
- Timeline updates in real-time

---

### Phase 5: Clip Library (2 days)
**Goal:** Manage available recordings

**Tasks:**
- [ ] Create `clip_library.py` module
- [ ] List all .ppr files in recordings/
- [ ] Show clip metadata (duration, date, name)
- [ ] Add search/filter
- [ ] Implement drag-from-library-to-timeline
- [ ] Add clip preview function
- [ ] Show clip thumbnail/info

**Deliverables:**
- Library panel shows all recordings
- Can drag recordings to timeline
- Preview recordings before adding

---

### Phase 6: Timeline Playback Engine (3-4 days)
**Goal:** Play entire timeline with gaps and trims

**Tasks:**
- [ ] Create `timeline_player.py` module
- [ ] Implement sequential clip playback
- [ ] Handle gaps between clips (hold position)
- [ ] Apply clip trims during playback
- [ ] Apply individual clip speeds
- [ ] Update playhead position during playback
- [ ] Implement pause/resume for timeline
- [ ] Implement stop and return to start
- [ ] Add progress tracking across timeline
- [ ] Handle errors gracefully

**Deliverables:**
- Timeline playback works end-to-end
- Gaps work correctly
- Trims applied during playback
- Playhead shows current position

---

### Phase 7: Clip Properties Panel (2 days)
**Goal:** Edit selected clip properties

**Tasks:**
- [ ] Create clip properties UI panel
- [ ] Show clip name (editable)
- [ ] Show start time (editable)
- [ ] Show duration (read-only after trim)
- [ ] Show trim controls
- [ ] Show speed control (per-clip)
- [ ] Add enable/disable checkbox
- [ ] Add color picker for visual organization
- [ ] Add duplicate button
- [ ] Add delete button

**Deliverables:**
- Properties panel shows selected clip
- Can edit all clip properties
- Changes update timeline visually

---

### Phase 8: Timeline Operations (2-3 days)
**Goal:** Advanced timeline editing

**Tasks:**
- [ ] Implement timeline export (bake to single .ppr)
- [ ] Add split clip function
- [ ] Add merge clips function
- [ ] Implement copy/paste clips
- [ ] Add undo/redo for timeline edits
- [ ] Implement timeline templates
- [ ] Add timeline validation warnings
- [ ] Create timeline from multiple files

**Deliverables:**
- Advanced editing operations work
- Can export timeline as single recording
- Undo/redo available

---

### Phase 9: Testing & Polish (2-3 days)
**Goal:** Test, debug, and polish V2

**Tasks:**
- [ ] Test all timeline operations
- [ ] Test playback with complex timelines
- [ ] Test at various speeds
- [ ] Test trimming edge cases
- [ ] Fix bugs
- [ ] Optimize performance
- [ ] Add keyboard shortcuts
- [ ] Improve UI/UX
- [ ] Write user documentation
- [ ] Create tutorial videos/guides

**Deliverables:**
- V2 fully tested and stable
- Documentation complete
- Ready for production use

---

### Phase 10: Advanced Features (Optional)
**Goal:** Extra features if time permits

**Tasks:**
- [ ] Add transition effects between clips
- [ ] Implement loop regions on timeline
- [ ] Add markers/labels on timeline
- [ ] Create clip groups/folders
- [ ] Add timeline comparison (A/B testing)
- [ ] Implement timeline synchronization with external triggers
- [ ] Add visual waveform for joint movement
- [ ] Create clip effects (smooth start/stop, etc.)

---

## Technical Specifications

### Speed Control (Extended)
- **Range:** 0.1x to 4.0x
- **Slider Steps:** 0.1x increments
- **Presets:** [0.1x, 0.25x, 0.5x, 1.0x, 1.5x, 2.0x, 3.0x, 4.0x]
- **Safety:** Warning dialog for speeds > 2.0x
- **Validation:** Robot tested at max speed

### Timeline Resolution
- **Display:** 100 pixels per second (zoomable)
- **Snap Grid:** 0.1 second increments
- **Minimum Clip Duration:** 0.1 seconds
- **Maximum Timeline Duration:** Unlimited (practical limit ~10 minutes)

### File Formats
- **Recording Files:** .ppr (existing, unchanged)
- **Timeline Files:** .ppt (new, JSON format)
- **Export:** Baked timeline saves as .ppr

### Performance Targets
- **Timeline Load Time:** < 1 second (100 clips)
- **Playback Latency:** < 5ms per command
- **UI Responsiveness:** 60 FPS timeline updates
- **Max Clips:** 1000+ clips supported

---

## UI/UX Considerations

### Timeline Interaction
- **Mouse:**
  - Click: Select clip
  - Drag: Move clip
  - Double-click: Edit clip name
  - Right-click: Context menu
  - Scroll: Pan timeline
  - Ctrl+Scroll: Zoom

- **Keyboard:**
  - Space: Play/Pause
  - Home: Go to start
  - End: Go to end
  - Delete: Remove selected clip
  - Ctrl+C: Copy clip
  - Ctrl+V: Paste clip
  - Ctrl+D: Duplicate clip
  - Ctrl+Z: Undo
  - Ctrl+Y: Redo
  - Arrow keys: Nudge clip position

### Visual Design
- **Clips:** Colored rectangles with rounded corners
- **Playhead:** Vertical red line
- **Time Ruler:** Gray with time markers
- **Selected Clip:** Highlighted border
- **Gaps:** Empty space (different background)
- **Trimmed Regions:** Darker/faded on clip ends

### Color Coding
- **Clip Colors:**
  - Green: Pick operations
  - Blue: Place operations
  - Yellow: Movement operations
  - Red: Home/Reset operations
  - Purple: Custom operations
  - User can customize

---

## Data Migration

### V1 → V2 Compatibility
- ✅ V2 can read all V1 .ppr files
- ✅ V2 can play V1 recordings standalone
- ✅ V1 recordings can be added to timelines
- ✅ No breaking changes to .ppr format

### New Files
- `.ppt` - Timeline project files (JSON)
- No changes to existing `.ppr` format

---

## Testing Strategy

### Unit Tests
- Timeline operations (add, remove, move, trim)
- Clip validation
- File save/load
- Trim calculations
- Speed multiplier application

### Integration Tests
- Timeline playback end-to-end
- Multi-clip sequences
- Gap handling
- Trim during playback
- Speed variations

### Manual Tests
- UI interaction (drag, click, edit)
- Visual feedback (playhead, selection)
- Long timeline performance
- Complex sequences (10+ clips)
- Edge cases (zero-length gaps, max speed, etc.)

---

## Success Criteria

### V2 is complete when:

1. ✅ User can adjust playback speed from 0.1x to 4.0x
2. ✅ Timeline panel displays visually in GUI
3. ✅ User can drag recordings onto timeline
4. ✅ Clips can be moved to create gaps
5. ✅ Clips can be trimmed from start and end
6. ✅ Timeline plays all clips sequentially
7. ✅ Gaps result in robot holding position
8. ✅ Trimmed sections are skipped during playback
9. ✅ Timeline can be saved and loaded (.ppt files)
10. ✅ System remains stable and responsive
11. ✅ V1 recordings still work in V2
12. ✅ Documentation is complete

---

## Timeline Estimate

### Total: 4-5 weeks (20-25 working days)

| Phase | Days | Start | End |
|-------|------|-------|-----|
| Phase 1: Extended Speed | 1-2 | Day 1 | Day 2 |
| Phase 2: Timeline Model | 2-3 | Day 3 | Day 5 |
| Phase 3: Clip Trimming | 2-3 | Day 6 | Day 8 |
| Phase 4: Timeline UI | 3-4 | Day 9 | Day 12 |
| Phase 5: Clip Library | 2 | Day 13 | Day 14 |
| Phase 6: Timeline Player | 3-4 | Day 15 | Day 18 |
| Phase 7: Clip Properties | 2 | Day 19 | Day 20 |
| Phase 8: Timeline Ops | 2-3 | Day 21 | Day 23 |
| Phase 9: Testing | 2-3 | Day 24 | Day 25+ |
| Phase 10: Advanced (Optional) | - | TBD | TBD |

**Note:** Can work incrementally, testing each phase before moving to next.

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Robot can't handle 4x speed | Medium | Low | Test early, cap speed if needed |
| Timeline UI performance issues | Low | Medium | Use canvas optimization, limit visible clips |
| Complex playback synchronization | Medium | High | Build incrementally, test thoroughly |
| Memory usage with many clips | Low | Medium | Load clips on-demand, cache management |

### Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | Medium | Medium | Stick to phases, optional features in Phase 10 |
| Timeline too complex for users | Low | High | Intuitive UI, good documentation, tutorials |
| V1 compatibility broken | Low | Critical | Extensive testing, keep .ppr format unchanged |

---

## Future Enhancements (Post-V2)

### V3 Ideas
- **3D Visualization:** Show robot path in 3D
- **Collaborative Editing:** Multiple users editing same timeline
- **Cloud Storage:** Save timelines to cloud
- **AI Optimization:** Auto-optimize movement paths
- **Template Library:** Pre-built sequences for common tasks
- **External Triggers:** Start timeline from sensors/buttons
- **Multi-Robot:** Coordinate multiple robots on one timeline
- **Simulation Mode:** Preview timeline without robot

---

## Questions to Consider

Before starting implementation:

1. **Speed Limits:**
   - What's the safe maximum speed for the robot?
   - Should we test 4x with real hardware first?

2. **Timeline Limits:**
   - Maximum timeline duration?
   - Maximum number of clips?

3. **File Management:**
   - Auto-save timelines?
   - Timeline backup/versioning?

4. **User Workflow:**
   - Start with library or recordings panel?
   - Default clip names?
   - Default gap duration?

5. **Export Options:**
   - Export as single .ppr?
   - Export to other formats?

---

## Getting Started

### Next Immediate Steps

1. **Review this plan** - Discuss and refine
2. **Set up V2 branch** - Version control for V2 development
3. **Start Phase 1** - Extended speed control (easiest/safest start)
4. **Create mockups** - Sketch timeline UI design
5. **Begin implementation** - Phase by phase

### Command to Start

```bash
# Create V2 development branch
git checkout -b feature/v2-timeline-system

# Or continue in current development
# Start with Phase 1: Extended Speed Control
```

---

**Document Version:** 1.0  
**Created:** December 2, 2025  
**Status:** Planning Complete - Ready for Implementation  
**Estimated Completion:** 4-5 weeks from start

