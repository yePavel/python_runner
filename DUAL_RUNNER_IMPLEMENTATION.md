# Dual EXE Runner Implementation

## Overview
The EXE Runner has been refactored to support **dual side-by-side execution**. You can now run two different EXE versions simultaneously, each with its own independent controls and output console.

## Architecture Changes

### New Class Structure

#### 1. **ExeRunnerPanel** (New)
A reusable single runner panel containing:
- Version selection with search/filter
- EXE selection dropdown  
- Log file picker
- Run/Stop buttons
- Console output with timestamps and auto-scroll
- Status display

**Key Method:**
- `set_root_path(path)` - Updates the panel with a root path (called by parent)

#### 2. **ExeRunnerTab** (Refactored)
The main container now manages:
- **Shared** root path browser (at top)
- **Left Panel** - Independent ExeRunnerPanel instance
- **Right Panel** - Independent ExeRunnerPanel instance

Each panel has its own:
- `ExeProcessRunner` instance (can run simultaneously)
- Version/EXE selection state
- Output console
- Log file configuration

## User Interface

```
┌─────────────────────────────────────────────────────────┐
│          Root Versions Folder                           │
│    [Selected Path]  [Browse...]                         │
├─────────────────────┬─────────────────────┤
│   Left Runner       │   Right Runner      │
├─────────────────────┼─────────────────────┤
│ Version: [dropdown] │ Version: [dropdown] │
│ EXE: [dropdown]     │ EXE: [dropdown]     │
│ Log: [input] [btn]  │ Log: [input] [btn]  │
│ [Run] [Stop]        │ [Run] [Stop]        │
├─────────────────────┼─────────────────────┤
│ Output              │ Output              │
│ [timestamps] [auto] │ [timestamps] [auto] │
│ [console]           │ [console]           │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

## How It Works

### 1. Browse Root Folder
- Click "Browse..." to select the root versions folder
- This path is **shared** between both panels
- Both panels automatically load available versions

### 2. Independent Selection
- **Left panel**: Select version → select EXE → pick log file → Run
- **Right panel**: Select version → select EXE → pick log file → Run
- Selections are completely independent

### 3. Simultaneous Execution
- Run left EXE while right EXE is already running
- Each panel shows its own output in real-time
- Stop buttons work independently

### 4. No Conflicts
- Different log files can be used for each runner
- Different EXE versions can run simultaneously
- Output from both runners doesn't interfere

## Key Features

✅ **Independent Execution** - Run 2 EXEs at the same time
✅ **Shared Root Path** - Select once, use for both
✅ **Separate Output** - Each panel has its own console
✅ **Individual Controls** - Each panel: version, EXE, log file, run/stop
✅ **Real-time Output** - See output from both runners simultaneously
✅ **Status Tracking** - Each panel shows its own status and exit code

## Code Differences

### Before (Single Panel)
```python
class ExeRunnerTab(QWidget):
    def __init__(self):
        self.root_path = None
        self.runner = ExeProcessRunner(self)  # Single runner
        self._init_ui()  # Single UI
```

### After (Dual Panel)
```python
class ExeRunnerTab(QWidget):
    def __init__(self):
        self.left_runner = ExeRunnerPanel("Left Runner")   # Left panel
        self.right_runner = ExeRunnerPanel("Right Runner") # Right panel
        self._init_ui()  # Creates both panels side-by-side

class ExeRunnerPanel(QWidget):
    def __init__(self, panel_name):
        self.runner = ExeProcessRunner(self)  # Own runner instance
```

## No Breaking Changes
- The import still works: `from features.exe_runner import ExeRunnerTab`
- The tab still works with main runner: `self.tabs.addTab(ExeRunnerTab(), "EXE Runner")`
- All existing functionality preserved

## Example Usage

```python
from features.exe_runner import ExeRunnerTab

# In main window
tab = ExeRunnerTab()
self.tabs.addTab(tab, "EXE Runner")

# Optional: sync theme
tab.set_theme_dark(True)
```

## Testing the Dual Runner

1. Open the application
2. Go to "EXE Runner" tab
3. Click "Browse..." and select test_executables folder
4. **Left Panel**: Select all_exe_1 → pick an EXE → Enter log file → Click Run
5. **Right Panel** (while left is running): Select all_exe_2 → pick an EXE → Enter log file → Click Run
6. Both runners execute independently with separate outputs

## Performance Notes

- Each panel uses its own `ExeProcessRunner` thread
- No performance impact from having 2 panels
- Can safely run 2 CPU-intensive tasks simultaneously
- Memory usage is minimal (2 threads instead of 1)

## Future Enhancements

Possible improvements:
- Add 3+ panels (make it configurable)
- Add panel comparison view
- Add output recording/saving per panel
- Add performance metrics per runner
- Add favorites/history per panel
