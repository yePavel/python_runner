# runner_gui.py
import sys
import os
import re
from typing import List, Optional, Dict, Any

from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QIcon, QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox, QToolBar
)

PYTHON = sys.executable  # use same interpreter

"""
Field schema (per script):
{
  "key": "--user",                 # CLI flag (empty "" for positional), checkbox passes flag only when checked
  "label": "User",                 # label text
  "required": True,                # validation before run
  "type": "text" | "int" | "float" | "select" | "checkbox",
  "placeholder": "e.g. alice",     # for text
  "default": "alice",              # default value
  "min": 0, "max": 100, "step": 1, # for int/float
  "options": ["fast","accurate"],  # for select
}
"""

SCRIPTS: List[Dict[str, Any]] = [
    {
        "name": "Add numbers",
        "path": "add_numbers.py",
        "args_schema": [
            {"key": "--user", "label": "User", "type": "text", "required": True, "placeholder": "e.g. Pavel"},
            {"key": "--a", "label": "first number", "type": "int", "required": True, "min": -1_000_000, "max": 1_000_000},
            {"key": "--b", "label": "second number", "type": "int", "required": True, "min": -1_000_000, "max": 1_000_000},
            # {"key": "--threshold", "label": "Threshold", "type": "int", "required": False, "default": 50, "min": 0, "max": 100},
            # {"key": "--mode", "label": "Mode", "type": "select", "required": True, "options": ["fast", "accurate"]},
            # {"key": "--dry-run", "label": "Dry run", "type": "checkbox", "required": False, "default": False},
        ],
        # how to pass the log file: "--log <path>" or positional
        "log_arg_style": "--log"
    },
    {
        "name": "Script B",
        "path": "script_b.py",
        "args_schema": [
            {"key": "--limit", "label": "Limit", "type": "int", "required": True, "default": 10, "min": 1, "max": 1000},
            {"key": "--epsilon", "label": "Epsilon", "type": "float", "required": False, "default": 0.1, "min": 0.0, "max": 1.0, "step": 0.01},
        ],
        "log_arg_style": "positional"
    },
    {
        "name": "Script C",
        "path": "script_c.py",
        "args_schema": [
            {"key": "--profile", "label": "Profile", "type": "select", "required": True, "options": ["default", "extended"]},
        ],
        "log_arg_style": "--log"
    }
]

# ---------- Dynamic form ----------

class DynamicForm(QWidget):
    """Builds a dynamic form for a given args schema and provides value/validation APIs."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = QFormLayout(self)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.bindings: List[Dict[str, Any]] = []  # each: {"schema":..., "widget":...}

    def clear(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.bindings.clear()

    def build(self, schema_list: List[Dict[str, Any]]):
        self.clear()
        for sch in schema_list:
            w = self._make_widget(sch)
            label_text = sch.get("label", sch.get("key", ""))
            if sch.get("required"):
                label_text += " *"
            self.form.addRow(label_text, w)
            self.bindings.append({"schema": sch, "widget": w})

    def _make_widget(self, sch: Dict[str, Any]) -> QWidget:
        t = sch.get("type", "text")
        if t == "text":
            w = QLineEdit()
            if "placeholder" in sch:
                w.setPlaceholderText(sch["placeholder"])
            if "default" in sch:
                w.setText(str(sch["default"]))
            return w
        if t == "int":
            w = QSpinBox()
            w.setMinimum(int(sch.get("min", -10**9)))
            w.setMaximum(int(sch.get("max", 10**9)))
            w.setValue(int(sch.get("default", 0)))
            w.setSingleStep(int(sch.get("step", 1)))
            return w
        if t == "float":
            w = QDoubleSpinBox()
            w.setDecimals(6)
            w.setMinimum(float(sch.get("min", -1e9)))
            w.setMaximum(float(sch.get("max", 1e9)))
            w.setValue(float(sch.get("default", 0.0)))
            w.setSingleStep(float(sch.get("step", 0.1)))
            return w
        if t == "select":
            w = QComboBox()
            options = sch.get("options", [])
            w.addItems([str(o) for o in options])
            if "default" in sch and sch["default"] in options:
                w.setCurrentText(str(sch["default"]))
            return w
        if t == "checkbox":
            w = QCheckBox()
            w.setChecked(bool(sch.get("default", False)))
            return w
        return QLineEdit()  # fallback

    def validate_and_collect(self) -> Optional[List[str]]:
        """Return list of error messages if any required fields are missing, else None."""
        errors = []
        for b in self.bindings:
            sch, w = b["schema"], b["widget"]
            val = self._value_of(w)
            if sch.get("required"):
                empty = (
                    (isinstance(w, QLineEdit) and val == "") or
                    (isinstance(w, (QSpinBox, QDoubleSpinBox)) and val is None) or
                    (isinstance(w, QComboBox) and (val is None or val == ""))
                )
                if empty:
                    errors.append(f"'{sch.get('label', sch.get('key'))}' is required.")
        return errors if errors else None

    def build_cli_args(self) -> List[str]:
        """Build CLI arg list according to schema and current values."""
        args: List[str] = []
        for b in self.bindings:
            sch, w = b["schema"], b["widget"]
            key = sch.get("key", "")
            val = self._value_of(w)
            t = sch.get("type", "text")
            if key and t != "checkbox":
                args.append(str(key))
                args.append(str(val))
            elif key and t == "checkbox":
                if bool(val):
                    args.append(str(key))
            # if key == "", you could push positional-only here if desired
        return args

    def _value_of(self, w: QWidget):
        if isinstance(w, QLineEdit):
            return w.text().strip()
        if isinstance(w, QSpinBox):
            return w.value()
        if isinstance(w, QDoubleSpinBox):
            return w.value()
        if isinstance(w, QComboBox):
            return w.currentText()
        if isinstance(w, QCheckBox):
            return w.isChecked()
        return None

# ---------- Main window ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Runner")
        self.resize(980, 640)
        self.setWindowIcon(QIcon())

        # Toolbar - optinal, can be remove if not needed
        # tb = QToolBar("Main")
        # tb.setIconSize(QSize(18, 18))
        # self.addToolBar(tb)

        # act_open = QAction("Choose log file", self)
        # act_open.triggered.connect(self.choose_log_file)
        # tb.addAction(act_open)

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # Left panel: file chooser + scripts list + run/cancel
        left_panel = QVBoxLayout()
        root_layout.addLayout(left_panel, 0)

        file_box = QGroupBox("Log file")
        file_layout = QHBoxLayout(file_box)
        self.lbl_log = QLabel("No file selected")
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self.choose_log_file)
        file_layout.addWidget(self.lbl_log, 1)
        file_layout.addWidget(btn_browse)
        left_panel.addWidget(file_box)

        scripts_box = QGroupBox("Scripts")
        scripts_layout = QVBoxLayout(scripts_box)
        self.list_scripts = QListWidget()
        for s in SCRIPTS:
            self.list_scripts.addItem(QListWidgetItem(s["name"]))
        self.list_scripts.currentRowChanged.connect(self.on_script_change)
        scripts_layout.addWidget(self.list_scripts)
        left_panel.addWidget(scripts_box, 1)

        run_row = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.on_run_clicked)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.on_cancel)
        run_row.addWidget(self.btn_run)
        run_row.addWidget(self.btn_cancel)
        left_panel.addLayout(run_row)

        # Center panel: dynamic form + progress + log
        center_panel = QVBoxLayout()
        root_layout.addLayout(center_panel, 1)

        self.form_box = QGroupBox("Parameters")
        form_layout = QVBoxLayout(self.form_box)
        self.form = DynamicForm()
        form_layout.addWidget(self.form)
        center_panel.addWidget(self.form_box)

        prog_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.lbl_status = QLabel("Ready")
        prog_row.addWidget(self.progress, 1)
        prog_row.addWidget(self.lbl_status)
        center_panel.addLayout(prog_row)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        center_panel.addWidget(log_box, 1)

        self.current_script: Optional[Dict[str, Any]] = None
        self.log_file_path: Optional[str] = None
        self.proc = None  # QProcess instance

        if SCRIPTS:
            self.list_scripts.setCurrentRow(0)

        # Simple dark theme
        self.setStyleSheet("""
            QMainWindow { background: #1e1f24; color: #f0f0f0; }
            QLabel, QGroupBox, QListWidget, QTextEdit { color: #f0f0f0; }
            QGroupBox { border: 1px solid #3a3d46; border-radius: 6px; margin-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 9px; padding: 0 3px; }
            QPushButton { background: #2b2f3a; border: 1px solid #3a3d46; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background: #3a3f4d; }
            QListWidget { background: #2b2f3a; border: 1px solid #3a3d46; }
            QTextEdit { background: #111217; border: 1px solid #3a3d46; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #2b2f3a; border: 1px solid #3a3d46; color: #f0f0f0; padding: 4px; }
            QProgressBar { background: #2b2f3a; border: 1px solid #3a3d46; border-radius: 3px; text-align: center; }
            QProgressBar::chunk { background-color: #4c8bf5; }
        """)

    # ---------- UI actions ----------

    @Slot()
    def choose_log_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose log file", "", "All Files (*);;Log Files (*.log *.txt)")
        if path:
            self.log_file_path = path
            self.lbl_log.setText(os.path.basename(path))

    @Slot(int)
    def on_script_change(self, row: int):
        if row < 0 or row >= len(SCRIPTS):
            self.current_script = None
            self.form.clear()
            return
        self.current_script = SCRIPTS[row]
        self.form.build(self.current_script.get("args_schema", []))
        self.set_status(f"Selected: {self.current_script['name']}")

    @Slot()
    def on_run_clicked(self):
        if not self.log_file_path:
            QMessageBox.warning(self, "Missing file", "Please choose a log file.")
            return
        if not self.current_script:
            QMessageBox.warning(self, "Missing script", "Please select a script.")
            return
        errors = self.form.validate_and_collect()
        if errors:
            QMessageBox.warning(self, "Validation", "\n".join(errors))
            return

        script_path = self.current_script["path"]
        args = [PYTHON, script_path]

        style = self.current_script.get("log_arg_style", "--log")
        if style == "positional":
            args.append(self.log_file_path)
        else:
            args.extend([style, self.log_file_path])

        args.extend(self.form.build_cli_args())

        if not os.path.exists(script_path):
            res = QMessageBox.question(
                self, "Script not found",
                f"Script '{script_path}' was not found. Continue anyway (demo)?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.No:
                return

        self.start_process(args)

    def start_process(self, args: List[str]):
        from PySide6.QtCore import QProcess

        self.txt_log.clear()
        self.progress.setValue(0)
        self.progress.setRange(0, 0)  # busy until we see PROGRESS
        self.set_status("Running...")

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.list_scripts.setEnabled(False)

        self.proc = QProcess(self)
        self.proc.setProgram(args[0])
        self.proc.setArguments(args[1:])
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_proc_output)
        self.proc.finished.connect(self.on_proc_finished)
        self.proc.errorOccurred.connect(self.on_proc_error)
        self.proc.start()

    @Slot()
    def on_proc_output(self):
        data = self.proc.readAllStandardOutput().data().decode(errors="replace")
        if not data:
            return
        self.txt_log.moveCursor(QTextCursor.End)
        self.txt_log.insertPlainText(data)
        self.txt_log.moveCursor(QTextCursor.End)

        # Detect "PROGRESS <0..100>"
        for line in data.splitlines():
            m = re.match(r"^\s*PROGRESS\s+(\d{1,3})\s*$", line.strip(), re.IGNORECASE)
            if m:
                val = max(0, min(100, int(m.group(1))))
                if self.progress.maximum() == 0:
                    self.progress.setRange(0, 100)
                self.progress.setValue(val)
                self.set_status(f"{val}%")

    @Slot(int, int)
    def on_proc_finished(self, exitCode, exitStatus):
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.set_status(f"Finished (code {exitCode})")
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.list_scripts.setEnabled(True)

    @Slot()
    def on_proc_error(self, err):
        self.append_log(f"[Process error] {err}\n")
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.list_scripts.setEnabled(True)
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.set_status("Error")

    @Slot()
    def on_cancel(self):
        if self.proc is not None:
            self.proc.kill()
        self.set_status("Cancelled")
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.list_scripts.setEnabled(True)

    def append_log(self, text: str):
        self.txt_log.moveCursor(QTextCursor.End)
        self.txt_log.insertPlainText(text)
        self.txt_log.moveCursor(QTextCursor.End)

    def set_status(self, text: str):
        self.lbl_status.setText(text)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
