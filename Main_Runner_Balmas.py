# Main_Runner.py
import sys
import os
import re
from typing import List, Optional, Dict, Any

from PySide6.QtCore import Qt, QSize, Slot, QEvent,QProcess
from PySide6.QtGui import QIcon, QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox, QToolBar, QToolTip
)

PYTHON = sys.executable  # use same interpreter

"""
Field schema (per script):
{
  "key": "--user",                 # CLI flag (empty "" for positional), checkbox passes flag only when checked
  "label": "User",                 # label text
  "required": True,                # validation before run
  "type": "text" | "int" | "float" | "select" | "checkbox",
  "placeholder": "e.g. Pavel",     # for text
  "default": "Pavel",              # default value
  "min": 0, "max": 100, "step": 1, # for int/float
  "options": ["fast","accurate"],  # for select
}
"""

SCRIPTS: List[Dict[str, Any]] = [
    # example:
    # {
    #     "name": "Add numbers",
    #     "path": "add_numbers.py",
    #     "args_schema": [
    #         {"key": "--user", "label": "User", "type": "text", "required": True, "placeholder": "e.g. Pavel"},
    #         {"key": "--a", "label": "first number", "type": "int", "required": True, "min": -1_000_000, "max": 1_000_000},
    #         {"key": "--b", "label": "second number", "type": "int", "required": True, "min": -1_000_000, "max": 1_000_000},
    #         # {"key": "--threshold", "label": "Threshold", "type": "int", "required": False, "default": 50, "min": 0, "max": 100},
    #         # {"key": "--mode", "label": "Mode", "type": "select", "required": True, "options": ["fast", "accurate"]},
    #         # {"key": "--dry-run", "label": "Dry run", "type": "checkbox", "required": False, "default": False},
    #     ],
    #     # how to pass the log file: "--log <path>" or positional
    #     "log_arg_style": "--log"
    # },
    {
        "name": "Find Family",
        "path": "find_family_ids.py",
        "clue": "Finds family IDs from the input log file",
        "args_schema": [
            # {"key": "--user", "label": "User", "type": "text", "required": False, "placeholder": "e.g. Pavel"},
            {"key": "--find_family", "label": "ids", "type": "string", "required": True},
            {"key": "--inputlog", "label": "Input Log", "type": "file_open",
            "required": False, "filter": "Log/Text (*.log *.txt);;All Files (*)",
            "dialog_title": "Choose additional log file"},
            {"key": "--SN", "label": "SN", "type": "checkbox", "required": False, "default": False},
        ],
        "log_arg_style": "--log"
    },
    {
        "name": "Limit2ids",
        "path": "limit2ids.py",
        "clue": "Cut the log file by the given ids",
        "args_schema": [
            # {"key": "--user", "label": "User", "type": "text", "required": False, "placeholder": "e.g. Pavel"},
            {"key": "--Limit2ids", "label": "ids", "type": "string", "required": True},
            {"key": "--outlog", "label": "out log", "type": "file_open",
            "required": False, "filter": "Log/Text (*.log *.txt);;All Files (*)",
            "dialog_title": "Choose additional log file"},
            {"key": "--hy", "label": "hy", "type": "file_open",
            "required": False, "filter": "Log/Text (*.log *.txt);;All Files (*)",
            "dialog_title": "Choose additional log file"},
        ],
        "log_arg_style": "--log"
    },
    {
        "name": "merge_logs",
        "path": "merge_logs.py",
        "clue": "Merge input logs by given directory path",
        "args_schema": [
            # {"key": "--user", "label": "User", "type": "text", "required": False, "placeholder": "e.g. Pavel"}
        ],
        "log_arg_style": "--log"
    },
    {
    "name": "Test Script",
    "path": "Example.py",
    "args_schema": [
        {"key": "--log", "label": "Log path", "type": "text", "required": False}
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
        if t == "file_open":
            return FilePicker(
                mode="open",
                dialog_title=sch.get("dialog_title", "Choose file"),
                name_filter=sch.get("filter", "All Files (*)")
            )

        if t == "file_save":
            return FilePicker(
                mode="save",
                dialog_title=sch.get("dialog_title", "Save file as"),
                name_filter=sch.get("filter", "All Files (*)")
            )
        return QLineEdit()  # fallback

    def validate_and_collect(self) -> Optional[List[str]]:
        """Return list of error messages if any required fields are missing, else None."""
        errors = []
        for b in self.bindings:
            sch, w = b["schema"], b["widget"]
            val = self._value_of(w)
            if sch.get("required"):
                missing = (
                    (isinstance(w, FilePicker) and val == "") or
                    (isinstance(w, QLineEdit) and val == "") or
                    (isinstance(w, (QSpinBox, QDoubleSpinBox)) and val is None) or
                    (isinstance(w, QComboBox) and (val is None or val == ""))
                )
                if missing:
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
        if isinstance(w, FilePicker):
            return w.text()
        return None

# ---------- Browse another log option ----------
class FilePicker(QWidget):
    """
    Small composite widget: QLineEdit + 'Browse...' button.
    """
    def __init__(self, mode: str = "open", dialog_title: str = "Choose file",
                 name_filter: str = "All Files (*)", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.dialog_title = dialog_title
        self.name_filter = name_filter
        self.setAcceptDrops(True)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.le = QLineEdit(self)
        btn = QPushButton("Browse…", self)
        btn.clicked.connect(self._browse)
        lay.addWidget(self.le, 1)
        lay.addWidget(btn)

    def _browse(self):
        if self.mode == "save":
            path, _ = QFileDialog.getSaveFileName(self, self.dialog_title, "", self.name_filter)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.dialog_title, "", self.name_filter)
        if path:
            self.le.setText(path)

    # convenience API so DynamicForm can read value uniformly
    def text(self) -> str:
        return self.le.text().strip()
    
    # Handeling drag and drop in the parameters section
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        self.le.setText(file_path)
        # Optionally, show a status message in the main window
        mw = self.window()
        if hasattr(mw, "set_status"):
            mw.set_status(f"File dropped: {os.path.basename(file_path)}")
    
# ---------- Main window ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Runner")
        self.resize(980, 640)
        self.setWindowIcon(QIcon())
        
        # define adding Theme button (sun/moon)
        self.theme_is_dark = False
        self.btn_theme = QPushButton()
        self.btn_theme.setText("☀️")  # Sun icon
        self.btn_theme.setToolTip("Switch theme")
        self.btn_theme.setFixedSize(45, 45)
        self.btn_theme.clicked.connect(self.toggle_theme)

        # define adding Clear Button
        self.act_clear = QPushButton()
        self.act_clear.setText("🧹")  # Clear icon
        self.act_clear.setToolTip("Clear All")
        self.act_clear.setFixedSize(45, 45)
        self.act_clear.clicked.connect(self.clear_all)

        # define adding Paste from Log Button to toolbar
        self.btn_paste_raw = QPushButton("Paste from Log")
        self.btn_paste_raw.setText("📝")  # Clear icon
        self.btn_paste_raw.setToolTip("Paste selected log text into form")
        self.btn_paste_raw.setFixedSize(45, 45)
        self.btn_paste_raw.clicked.connect(self.paste_from_log_selection)
        
        # Actual addWidget theme to toolbar
        tb = QToolBar("Main")
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)
        tb.addWidget(self.btn_theme)
        tb.addWidget(self.act_clear)
        tb.addWidget(self.btn_paste_raw)


        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        # Left panel: file chooser + scripts list + run/cancel
        left_panel = QVBoxLayout()
        root_layout.addLayout(left_panel, 0)


        # Main path selector
        self.log_is_dir = False
        self.file_box = QGroupBox("Main Path")
        file_layout = QHBoxLayout(self.file_box)
        self.file_box.setAcceptDrops(True)
        self.file_box.installEventFilter(self)
        
        self.lbl_log = QLabel("No file Selected")
        self.lbl_log.setAcceptDrops(True)
        self.lbl_log.installEventFilter(self)
        
        self.log_mode = QComboBox()
        self.log_mode.addItems(["File","Folder"])
        self.log_mode.setCurrentText("File")
        self.log_mode.setAcceptDrops(True)
        self.log_mode.installEventFilter(self)
        self.log_mode.currentTextChanged.connect(self.on_log_mode_changed)
        
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self.choose_log_file)

        file_layout.addWidget(self.lbl_log,1)
        file_layout.addWidget(self.log_mode)
        file_layout.addWidget(btn_browse)
        left_panel.addWidget(self.file_box)


        scripts_box = QGroupBox("Scripts")
        scripts_layout = QVBoxLayout(scripts_box)
        self.list_scripts = QListWidget()
        
        # Adding clue button to see script description
        self.btn_clue = QPushButton("❓")
        self.btn_clue.setToolTip("Show script description")
        self.btn_clue.setFixedSize(30, 30)
        self.btn_clue.clicked.connect(self.show_script_clue)
        scripts_layout.addWidget(self.btn_clue)
        
        for s in SCRIPTS:
            self.list_scripts.addItem(QListWidgetItem(s["name"]))
        self.list_scripts.currentRowChanged.connect(self.on_script_change)
        scripts_layout.addWidget(self.list_scripts)
        left_panel.addWidget(scripts_box, 1)

        run_row = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.on_run_clicked)
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setMinimumSize(90, 40)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_cancel.setMinimumSize(90, 40)
        
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
        self.txt_log.setReadOnly(False)
        log_layout.addWidget(self.txt_log)
        center_panel.addWidget(log_box, 1)

        self.current_script: Optional[Dict[str, Any]] = None
        self.log_file_path: Optional[str] = None
        self.proc = None  # QProcess instance

        if SCRIPTS:
            self.list_scripts.setCurrentRow(0)

        self.apply_theme()

    def apply_theme(self):
        if self.theme_is_dark:
            self.setStyleSheet("""
                QMainWindow { background: #1e1f24; color: #f0f0f0; }
                QLabel, QGroupBox, QListWidget, QTextEdit { color: #f0f0f0; }
                QGroupBox { border: 1px solid #3a3d46; border-radius: 6px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 9px; padding: 0 3px; }
                QPushButton { margin: 2px; background: qlineargradient(x1:0, y1:0, x2:0,y2:1, stop:0 #555555, stop:1 #333333); border: 1px solid #3a3d46; padding: 4px 4px; border-radius: 4px; color: #E0E0E0; }
                QPushButton:hover { background: #3a3f4d; }
                QListWidget { background: #2b2f3a; border: 1px solid #3a3d46; }
                QTextEdit { background: #111217; border: 1px solid #3a3d46; }
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #2b2f3a; border: 1px solid #3a3d46; color: #f0f0f0; padding: 4px; }
                QProgressBar { background: #2b2f3a; border: 1px solid #3a3d46; border-radius: 3px; text-align: center; color: #f0f0f0; }
                QProgressBar::chunk { background-color: #4c8bf5; }
                
                QPushButton#RunButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D0D0D, stop:1 #1B5E20);
                    color: #FFFFFF;
                    border: 1px solid #2E7D32;
                    }
                QPushButton#RunButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1B5E20, stop:1 #2E7D32);
                    }
                QPushButton#CancelButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D0D0D, stop:1 #7F0000); 
                    color: #FFFFFF;
                    border: 1px solid #B71C1C;
                    }
                QPushButton#CancelButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7F0000, stop:1 #B71C1C);
                    }
                """)
            self.btn_theme.setText("🌞")  # Sun icon
        else:
            self.setStyleSheet("""
                QMainWindow { background: #f8f8f8; color: #222; }
                QLabel, QGroupBox, QListWidget, QTextEdit { color: #222; }
                QGroupBox { border: 1px solid #ccc; border-radius: 6px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; left: 9px; padding: 0 3px; }
                QPushButton { margin: 2px; background: qlineargradient(x1:0, y1:0, x2:0,y2:1, stop:0 #F5F5F5, stop:1 #ADADAD); border: 1px solid #ccc; padding: 4px 4px; border-radius: 4px; }
                QPushButton:hover { background: #eaeaea; }
                QListWidget { background: #fff; border: 1px solid #ccc; }
                QTextEdit { background: #f4f4f4; border: 1px solid #ccc; }
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #fff; border: 1px solid #ccc; color: #222; padding: 4px; }
                QProgressBar { background: #fff; border: 1px solid #ccc; border-radius: 3px; text-align: center; color: #222; }
                QProgressBar::chunk { background-color: #4c8bf5; }
                
                QPushButton#RunButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fff8, stop:1 #e0ffe0);
                    color: #222;
                    border: 1px solid #b2dfdb;
                }
                QPushButton#RunButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0ffe0, stop:1 #c8f7c8);
                }
                QPushButton#CancelButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff8f8, stop:1 #ffe0e0);
                    color: #222;
                    border: 1px solid #ef9a9a;
                }
                QPushButton#CancelButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffe0e0, stop:1 #ffcccc);
                }
                """)
            self.btn_theme.setText("🌙")  # Moon icon

    def toggle_theme(self):
        self.theme_is_dark = not self.theme_is_dark
        self.apply_theme()

    def eventFilter(self, obj, event):
        targets = (self.file_box, self.lbl_log, self.log_mode, getattr(self, "btn_browse", None))
        if obj in targets:
            et = event.type()

            if et == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction() 
                    self.file_box.setStyleSheet("QGroupBox { border: 2px dashed #4c8bf5; border-radius: 6px; }")
                    return True
                return False

            if et == QEvent.DragMove:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
                return False

            if et == QEvent.DragLeave:
                self.file_box.setStyleSheet("")  
                return True

            if et == QEvent.Drop:
                urls = event.mimeData().urls()
                self.file_box.setStyleSheet("")
                if not urls:
                    return False
                path = urls[0].toLocalFile()

                if self.log_is_dir: 
                    self.log_file_path = path if os.path.isdir(path) else os.path.dirname(path)
                else:
                    self.log_file_path = path

                base = os.path.basename(self.log_file_path.rstrip("/\\")) or self.log_file_path
                self.lbl_log.setText(base)
                self.set_status(f"Main Path set: {base}")
                event.acceptProposedAction()
                return True

        return super().eventFilter(obj, event)
            
            
    # ---------- UI actions ----------

    @Slot()
    def on_log_mode_changed(self,text:str):
        self.log_is_dir = (text.lower() == "folder")
        self.log_file_path = None
        self.lbl_log.setText("No file Selected")

    @Slot()
    def choose_log_file(self):
        if self.log_is_dir:
            path = QFileDialog.getExistingDirectory(self, "Choose log directory...")
            if path:
                self.log_file_path = path
                base = os.path.basename(path.rstrip("/\\")) or path
                self.lbl_log.setText(base)
        else:  
            path, _ = QFileDialog.getOpenFileName(self, "Choose log file", "", "All Files (*);;Log Files (*.log *.txt)")
            if path:
                self.log_file_path = path
                base = os.path.basename(path)
                self.lbl_log.setText(base)


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
        args.extend(["--mode","gui"])

        if not os.path.exists(script_path):
            QMessageBox.warning(self, "Missing script", "Script is missing in the given directory")

        self.start_process(args)

    def start_process(self, args: List[str]):

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

    def show_script_clue(self):
        row = self.list_scripts.currentRow()
        if row < 0 or row >= len(SCRIPTS):
            clue = "No script selected."
        else:
            clue = SCRIPTS[row].get("clue", "No clue available.")
        # Show tooltip near the clue button
        QToolTip.showText(self.btn_clue.mapToGlobal(self.btn_clue.rect().bottomLeft()), clue, self.btn_clue)
    
    # Add copy - paste option
    def _normalize_selected_text(self, text: str) -> str:
        # In Qt, selectedText() replaces line breaks with U+2029 (paragraph separator)
        return text.replace('\u2029', '\n').strip()

    def _focused_form_widget(self):
        """Return the currently focused input widget inside the dynamic form, or None."""
        w = QApplication.focusWidget()
        if not w:
            return None
        # ensure it's one of our inputs
        from PySide6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
        if isinstance(w, (QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox)):
            return w
        return None

    def _fallback_required_widget(self):
        """If no focus, try to find the first required field's widget."""
        if not self.form or not getattr(self.form, "bindings", None):
            return None
        for b in self.form.bindings:
            sch = b.get("schema", {})
            if sch.get("required"):
                return b.get("widget")
        # else first field
        return self.form.bindings[0]["widget"] if self.form.bindings else None

    def _set_widget_value(self, widget, text: str):
        """Set value into different widget types intelligently."""
        from PySide6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
        t = text.strip()

        if isinstance(widget, QLineEdit):
            widget.setText(t)
            return True

        if isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(float(t)))
                return True
            except Exception:
                QMessageBox.warning(self, "Paste failed", "Selected text is not an integer.")
                return False

        if isinstance(widget, QDoubleSpinBox):
            try:
                widget.setValue(float(t))
                return True
            except Exception:
                QMessageBox.warning(self, "Paste failed", "Selected text is not a number.")
                return False

        if isinstance(widget, QComboBox):
            # try exact match first
            idx = widget.findText(t)
            if idx >= 0:
                widget.setCurrentIndex(idx)
                return True
            # if not found, set editable text if combo is editable
            if widget.isEditable():
                widget.setEditText(t)
                return True
            QMessageBox.warning(self, "Paste failed", f"'{t}' is not an available option.")
            return False

        if isinstance(widget, QCheckBox):
            val = t.lower() in ("1", "true", "yes", "on")
            widget.setChecked(val)
            return True

        return False

    def _clear_process_if_running(self):
        
        if getattr(self,"proc", None) is not None:
            try:
                if self.proc.state():
                    self.proc.kill()
            except Exception:
                pass
            finally:
                self.proc = None
        
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.list_scripts.setEnabled(True)

    def clear_all(self):
        if getattr(self,"proc", None) is not None:

            res = QMessageBox.question(
                self, 
                "Confirm",
                "Kill it and clear the GUI?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No #default
            )

            if res == QMessageBox.StandardButton.No:
                return
        
        # Clear everything in the GUI
        self._clear_process_if_running()

        self.txt_log.clear()

        self.progress.setRange(0,100)
        self.progress.setValue(0)
        self.set_status("Ready")
        
        self.log_file_path = None
        self.lbl_log.setText("No file Selected")

        if self.current_script:
            self.form.build(self.current_script.get("args_schema", []))
        else: 
            self.form.clear()


    @Slot()
    def paste_from_log_selection(self):
        """Paste the currently selected log text into the focused (or first required) field."""
        # get selection from log
        cursor = self.txt_log.textCursor()
        
        if not cursor.hasSelection():
            QMessageBox.information(self, "No selection", "Select text in the Log pane first.")
            return
        
        raw = self._normalize_selected_text(cursor.selectedText())
        if not raw:
            QMessageBox.information(self, "No selection", "Select text in the Log pane first.")
            return
        
        target = self._focused_form_widget() or self._fallback_required_widget()
        if not target:
            QMessageBox.warning(self, "No target field", "Focus a form field to paste into.")
            return
        
        if self._set_widget_value(target, raw):
            self.set_status("Pasted from Log")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
