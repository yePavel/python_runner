# How to Integrate EXE Runner into Another PC

## Files You Need to Copy

Copy the entire `exe_runner` folder with these 4 files:

```
features/
├── exe_runner/
│   ├── __init__.py
│   ├── controller.py
│   ├── process_runner.py
│   └── ui.py
```

## Step-by-Step Integration Guide

### Step 1: Copy the exe_runner Module
On the other PC, create the same folder structure:
```
your_project/
├── features/
│   ├── __init__.py  (make sure this exists)
│   └── exe_runner/  (copy entire folder)
│       ├── __init__.py
│       ├── controller.py
│       ├── process_runner.py
│       └── ui.py
```

### Step 2: Update Your Main Runner (Main_Runner_Balmas.py)

**Add this import at the top:**
```python
from features.exe_runner import ExeRunnerTab
```

Example (around line 16 in current file):
```python
from features.exe_runner import ExeRunnerTab
```

### Step 3: Add the Tab to Your QTabWidget

In your `MainWindow.__init__()` method, after creating the tabs, add:

```python
# Around line 438 in current Main_Runner_Balmas.py
self.exe_runner_tab = ExeRunnerTab(self)
self.tabs.addTab(self.exe_runner_tab, "EXE Runner")
```

**Full example location:**
```python
# Central widget with tabs
self.tabs = QTabWidget()
self.setCentralWidget(self.tabs)

# ===== Tab 1: Python Runner (existing functionality) =====
tab_runner = QWidget()
self.tabs.addTab(tab_runner, "Python Runner")
# ... rest of your code ...

# ===== Tab 2: EXE Runner (NEW) =====
self.exe_runner_tab = ExeRunnerTab(self)
self.tabs.addTab(self.exe_runner_tab, "EXE Runner")
```

### Step 4: (Optional) Set Theme Sync

If you want the EXE Runner tab to follow your app's theme, add this in your `toggle_theme()` method:

```python
def toggle_theme(self):
    # ... your existing theme toggle code ...
    # Add this line to sync with exe_runner tab:
    self.exe_runner_tab.set_theme_dark(self.theme_is_dark)
```

## What Each File Does

- **`__init__.py`** - Exports the classes for easy importing
- **`controller.py`** - Business logic (folder scanning, exe discovery)
- **`process_runner.py`** - Handles subprocess execution with output capture
- **`ui.py`** - PySide6 UI widgets (has the `ExeRunnerTab` class)

## Configuration (If Needed)

The default path in `ui.py` is hardcoded:
```python
DEFAULT_ROOT_PATH = r"C:\Users\pavelye\Desktop\New folder\python_runner\test_executables"
```

You can change this to match your other PC's path by editing `ui.py` line ~19.

## Dependencies

Make sure your other PC has these packages installed:
```
PySide6
```

(Should already be installed if running the main app)

## Testing

After integration, run:
```bash
python -c "from features.exe_runner import ExeRunnerTab; print('✓ Import successful')"
```

If it works, the EXE Runner tab should appear in your main app!
