# EXE Runner Feature - Developer Reference

## Quick Start Guide

### Using the Feature (End User)

```
1. Open app → Click "EXE Runner" tab
2. Click "Browse..." → Select D:\MyProduct\Versions\
3. Version dropdown auto-populates
4. (Optional) Type in search box to filter versions
5. Select version → exe list updates
6. Enter log file: "test.log" or full path
7. Click "Run" → Watch console output stream live
8. Click "Stop" to terminate
```

---

## Architecture Overview

### Signal/Slot Flow

```
ExeRunnerTab (UI)
    ↓ (user actions)
    → _on_root_browse() → ExeRunnerController.validate_root_path()
    → _on_version_changed() → ExeRunnerController.get_exe_files()
    → _on_run() → ExeRunnerController.validate_log_file()
                → ExeProcessRunner.run_exe()
                    ↓
    ← ExeProcessRunner.started ← _on_process_started()
    ← ExeProcessRunner.output_received ← _on_process_output()
    ← ExeProcessRunner.finished ← _on_process_finished()
    ← ExeProcessRunner.error_occurred ← _on_process_error()
```

---

## Code Examples

### Example 1: Validating a Path

```python
from features.exe_runner.controller import ExeRunnerController

# Validate root path
is_valid, error_msg = ExeRunnerController.validate_root_path("D:\\MyProduct\\Versions\\")
if not is_valid:
    print(f"Error: {error_msg}")
else:
    print("Path is valid!")
```

### Example 2: Discovering Versions

```python
from features.exe_runner.controller import ExeRunnerController

root = "D:\\MyProduct\\Versions\\"
versions = ExeRunnerController.get_version_folders(root)
# Returns: ["v1.2.0", "v1.3.1", "release_2026_01_20"]
```

### Example 3: Finding EXE Files

```python
from features.exe_runner.controller import ExeRunnerController

version_path = "D:\\MyProduct\\Versions\\v1.2.0"
exes = ExeRunnerController.get_exe_files(version_path)
# Returns: ["test.exe", "app.exe"]  if D:\MyProduct\Versions\v1.2.0\bit\ contains them
# Returns: []  if no exe or bit folder doesn't exist
```

### Example 4: Running a Process

```python
from features.exe_runner.process_runner import ExeProcessRunner
from PySide6.QtWidgets import QApplication

app = QApplication([])

runner = ExeProcessRunner()

# Connect signals
runner.started.connect(lambda: print("Process started!"))
runner.output_received.connect(lambda data: print(f"Output: {data}"))
runner.finished.connect(lambda code: print(f"Finished with code {code}"))
runner.error_occurred.connect(lambda err: print(f"Error: {err}"))

# Start process
success = runner.run_exe(
    exe_path="D:\\MyProduct\\Versions\\v1.2.0\\bit\\test.exe",
    log_file="test.log",
    working_dir="D:\\MyProduct\\Versions\\v1.2.0\\bit"
)

if success:
    print("Process started successfully")
else:
    print("Failed to start process")
```

### Example 5: Using the UI Tab Directly

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from features.exe_runner import ExeRunnerTab

app = QApplication([])
window = QMainWindow()
window.setWindowTitle("EXE Runner Standalone")

exe_tab = ExeRunnerTab()
window.setCentralWidget(exe_tab)

# Apply dark theme
exe_tab.set_theme_dark(True)

window.show()
app.exec()
```

---

## API Reference

### ExeRunnerController

```python
@staticmethod
validate_root_path(path: str) -> Tuple[bool, str]:
    """
    Validate root folder exists and is accessible.
    Returns: (is_valid, error_message)
    """

@staticmethod
get_version_folders(root_path: str) -> List[str]:
    """
    Get all subdirectories under root.
    Returns: Sorted list of folder names (basenames only)
    """

@staticmethod
get_exe_files(version_path: str) -> List[str]:
    """
    Scan <version_path>/bit/ for .exe files.
    Returns: Sorted list of exe names (basenames only)
    """

@staticmethod
validate_log_file(log_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate log file path.
    Returns: (can_proceed, warning_message)
    - can_proceed=True means we can run
    - warning_message=None means no issues; string means warning to show user
    """

@staticmethod
build_exe_full_path(root_path: str, version_name: str, exe_name: str) -> str:
    """Construct full path to exe file."""

@staticmethod
get_working_directory(root_path: str, version_name: str) -> str:
    """Get the working directory (bit folder) for the exe."""
```

### ExeProcessRunner

```python
# Signals
started = Signal()              # Emitted when process starts
output_received = Signal(str)   # Emitted with each output chunk
finished = Signal(int)          # Emitted with exit code
error_occurred = Signal(str)    # Emitted with error message

# Methods
run_exe(exe_path: str, log_file: str, working_dir: str) -> bool:
    """
    Start the process.
    Returns: True if started successfully, False otherwise
    """

stop():
    """Terminate the running process gracefully, then forcefully if needed."""

is_running: bool
    """Property: True if process is currently running."""
```

### ExeRunnerTab (UI)

```python
# Constructor
ExeRunnerTab(parent=None) -> QWidget

# Methods
set_theme_dark(is_dark: bool):
    """Apply dark/light theme styling."""

# Signals (all inherited from QWidget)
# Properties (read-only, for debugging)
root_path: Optional[str]
selected_version: Optional[str]
selected_exe: Optional[str]
```

---

## Extending the Feature

### Add a New Discovery Method

Example: Scan for .dll files instead of .exe

```python
# In controller.py
@staticmethod
def get_dll_files(version_path: str) -> List[str]:
    """Discover all .dll files in <version_path>/bit/ folder."""
    bit_path = os.path.join(version_path, "bit")
    if not os.path.isdir(bit_path):
        return []
    
    try:
        items = os.listdir(bit_path)
        dll_files = [
            item for item in items
            if item.lower().endswith(".dll") and os.path.isfile(os.path.join(bit_path, item))
        ]
        return sorted(dll_files)
    except Exception:
        return []
```

### Add a New UI Section

Example: Add a "Arguments" text field

```python
# In ui.py, after Log File section:

# Arguments Section
args_box = QGroupBox("Additional Arguments")
args_layout = QHBoxLayout(args_box)
self.txt_args = QLineEdit()
self.txt_args.setPlaceholderText("e.g., --verbose --output=result.txt")
args_layout.addWidget(self.txt_args)
main_layout.addWidget(args_box)

# Then in _on_run():
extra_args = self.txt_args.text().strip().split()
args = [log_file] + extra_args

# Pass to runner:
success = self.runner.run_exe(exe_full_path, args[0], working_dir)
```

---

## Error Handling Examples

### Handling Invalid Root Path

```python
def _on_root_browse(self):
    path = QFileDialog.getExistingDirectory(...)
    if path:
        is_valid, error = ExeRunnerController.validate_root_path(path)
        if not is_valid:
            QMessageBox.critical(self, "Invalid Path", error)
            return
        self.root_path = path
```

### Handling Missing EXE Files

```python
def _on_version_changed(self, text: str):
    exes = ExeRunnerController.get_exe_files(version_path)
    
    if not exes:
        self.combo_exe.clear()
        self.combo_exe.addItem("(no .exe files found)")
        self.combo_exe.setEnabled(False)
        self._set_status(f"Error: No .exe in {text}\\bit\\")
    else:
        self.combo_exe.clear()
        self.combo_exe.addItems(exes)
        self.combo_exe.setEnabled(True)
```

### Handling Log File Warnings

```python
def _on_run(self):
    log_file = self.txt_log_file.text().strip()
    is_valid, warning = ExeRunnerController.validate_log_file(log_file)
    
    if not is_valid:
        QMessageBox.warning(self, "Invalid", warning)
        return
    
    if warning:
        result = QMessageBox.question(
            self,
            "Warning",
            warning + "\n\nProceed anyway?",
            QMessageBox.Yes | QMessageBox.No
        )
        if result != QMessageBox.Yes:
            return
    
    # Proceed with run...
```

---

## Testing Strategies

### Unit Testing Controller

```python
from features.exe_runner.controller import ExeRunnerController
import tempfile
import os

def test_validate_root_path():
    # Test invalid path
    is_valid, error = ExeRunnerController.validate_root_path("")
    assert not is_valid
    assert "empty" in error.lower()
    
    # Test nonexistent path
    is_valid, error = ExeRunnerController.validate_root_path("C:\\nonexistent\\path\\12345")
    assert not is_valid
    
    # Test valid path
    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, error = ExeRunnerController.validate_root_path(tmpdir)
        assert is_valid
        assert error == ""

def test_get_version_folders():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.mkdir(os.path.join(tmpdir, "v1.0.0"))
        os.mkdir(os.path.join(tmpdir, "v2.0.0"))
        os.mkdir(os.path.join(tmpdir, ".hidden"))
        
        versions = ExeRunnerController.get_version_folders(tmpdir)
        assert len(versions) == 3
        assert "v1.0.0" in versions
```

### Integration Testing

```python
import tempfile
import os
import subprocess

def test_exe_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create version/bit structure
        bit_dir = os.path.join(tmpdir, "v1.0", "bit")
        os.makedirs(bit_dir)
        
        # Create a simple batch file (acts like exe for testing)
        bat_file = os.path.join(bit_dir, "test.exe")
        with open(bat_file, "w") as f:
            f.write("@echo off\necho Hello World\n")
        
        runner = ExeProcessRunner()
        runner.finished.connect(lambda code: assert code == 0)
        
        success = runner.run_exe(bat_file, "test.log", bit_dir)
        assert success
```

---

## Performance Considerations

- **Version listing**: Fast for <1000 folders
- **EXE discovery**: Scans only the bit/ folder (typically 1-5 exe files)
- **Output streaming**: Uses Qt signals, minimal overhead
- **Memory**: Keeps entire output in QTextEdit (limit to ~100MB in practice)

For large outputs (>100MB), consider:
1. Limiting displayed lines
2. Auto-rotating output file
3. Using a ring buffer

---

## Troubleshooting

### Process doesn't start
- Check exe_path exists: `os.path.exists(exe_path)`
- Check working_dir exists: `os.path.isdir(working_dir)`
- Check permissions: can current user execute files in that folder?

### No output appears
- Is process actually running? Check `is_running` property
- Check output_received signal is connected
- Verify exe actually writes to stdout/stderr
- Check stderr: we merge stderr into stdout

### Theme doesn't apply to tab
- Make sure to call `exe_runner_tab.set_theme_dark(True/False)` from main window
- Check `apply_theme()` is implemented in the tab

---

## Best Practices

✅ Always validate paths before passing to runner
✅ Connect error_occurred signal to show user-friendly messages
✅ Disable controls while running to prevent duplicate execution
✅ Call stop() before app exit (QProcess cleanup)
✅ Use working_dir to ensure relative paths are resolved correctly
✅ Handle unicode in paths (already done via Python's str type)
✅ Test with spaces and special characters in paths

❌ Don't pass unvalidated user input directly to run_exe()
❌ Don't ignore process errors
❌ Don't run multiple processes in same runner (create new instance)
❌ Don't block UI thread in output handlers
❌ Don't assume exe always creates log file
