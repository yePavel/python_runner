# Main App Changes - Exact Diff

## File: Main_Runner_Balmas.py

### Change 1: Import Section (Line 1-15)

**BEFORE:**
```python
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox, QToolBar, QToolTip
)
```

**AFTER:**
```python
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox, QToolBar, QToolTip, QTabWidget
)

from features.exe_runner import ExeRunnerTab
```

**Summary:** Added QTabWidget import + imported ExeRunnerTab

---

### Change 2: Central Widget Setup (Line ~330-437)

**BEFORE:**
```python
        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # Left panel: file chooser + scripts list + run/cancel
        left_panel = QVBoxLayout()
        root_layout.addLayout(left_panel, 0)

        # [... existing layout code for Python Runner ...]

        center_panel.addWidget(log_box, 1)

        self.current_script: Optional[Dict[str, Any]] = None
```

**AFTER:**
```python
        # Central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # ===== Tab 1: Python Runner (existing functionality) =====
        tab_runner = QWidget()
        self.tabs.addTab(tab_runner, "Python Runner")
        root_layout = QHBoxLayout(tab_runner)

        # Left panel: file chooser + scripts list + run/cancel
        left_panel = QVBoxLayout()
        root_layout.addLayout(left_panel, 0)

        # [... existing layout code for Python Runner - UNCHANGED ...]

        center_panel.addWidget(log_box, 1)
        
        # ===== Tab 2: EXE Runner (new feature) =====
        self.exe_runner_tab = ExeRunnerTab(self)
        self.tabs.addTab(self.exe_runner_tab, "EXE Runner")

        self.current_script: Optional[Dict[str, Any]] = None
```

**Summary:** Wrapped existing UI in QTabWidget with two tabs. All existing code logic unchanged - just restructured for tab layout.

---

### Change 3: Theme Toggle (Line ~523-525)

**BEFORE:**
```python
    def toggle_theme(self):
        self.theme_is_dark = not self.theme_is_dark
        self.apply_theme()
```

**AFTER:**
```python
    def toggle_theme(self):
        self.theme_is_dark = not self.theme_is_dark
        self.apply_theme()
        # Propagate theme to EXE Runner tab
        if hasattr(self, "exe_runner_tab"):
            self.exe_runner_tab.set_theme_dark(self.theme_is_dark)
```

**Summary:** Added 3 lines to propagate theme changes to the new tab

---

## Total Changes

- **Lines Added:** ~10 (imports + tab setup + theme sync)
- **Lines Removed:** 0
- **Lines Modified:** ~3 (wrapped central widget setup)
- **Breaking Changes:** None
- **Existing Functionality:** 100% preserved

## How to Apply This Patch Manually (if needed)

1. In imports section, add `QTabWidget` to the QWidget imports
2. Add `from features.exe_runner import ExeRunnerTab` after other imports
3. Replace the central widget setup:
   - Change `central = QWidget()` to `self.tabs = QTabWidget()`
   - Change `root_layout = QHBoxLayout(central)` to create a `tab_runner` widget first
   - Wrap all existing layout code in that tab
4. Add the new tab: `self.exe_runner_tab = ExeRunnerTab(self); self.tabs.addTab(self.exe_runner_tab, "EXE Runner")`
5. Add 3 lines to `toggle_theme()` to sync theme
