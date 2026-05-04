"""
UI widgets and layout for EXE Runner tab.
"""
import os
import shutil
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Slot, QSize, QTimer, QEvent, QUrl, QProcess
from PySide6.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QGroupBox, QFileDialog, QMessageBox, QCheckBox
)

from .controller import ExeRunnerController
from .process_runner import ExeProcessRunner


# Default path for exe versions (hardcoded but can be changed)
DEFAULT_ROOT_PATH = r"C:\Users\pavelye\Desktop\New folder\python_runner\test_executables"


class ExeRunnerPanel(QWidget):
    """Single EXE Runner panel (left or right side)."""
    
    def __init__(self, panel_name: str = "Runner", parent=None):
        super().__init__(parent)
        self.panel_name = panel_name
        self.root_path: Optional[str] = None
        self.selected_version: Optional[str] = None
        self.selected_exe: Optional[str] = None
        self._all_versions = []
        self._pending_search_text = ""
        self._version_search_timer = QTimer(self)
        self._version_search_timer.setSingleShot(True)
        self._version_search_timer.setInterval(200)
        self._version_search_timer.timeout.connect(self._apply_version_filter)
        
        self.runner = ExeProcessRunner(self)
        self.runner.started.connect(self._on_process_started)
        self.runner.output_received.connect(self._on_process_output)
        self.runner.finished.connect(self._on_process_finished)
        self.runner.error_occurred.connect(self._on_process_error)

        self._matlab_proc: Optional[QProcess] = None
        self._matlab_running = False
        
        self._init_ui()
    
    def set_root_path(self, path: str):
        """Set root path from parent (shared between both panels)."""
        self.root_path = path
        self.lbl_root.setText(os.path.basename(path) if path else "No folder selected")
        self.txt_version_search.clear()
        self._refresh_versions()
        self._update_matlab_button_state()
    
    def _init_ui(self):
        """Build the UI layout for this panel."""
        main_layout = QVBoxLayout(self)
        
        # ===== Title =====
        title = QLabel(f"<b>{self.panel_name}</b>")
        main_layout.addWidget(title)
        
        # ===== Root Path Display =====
        root_box = QGroupBox("Root Versions Folder")
        root_layout = QHBoxLayout(root_box)
        self.lbl_root = QLabel("No folder selected")
        self.lbl_root.setEnabled(False)  # Read-only display
        root_layout.addWidget(self.lbl_root, 1)
        main_layout.addWidget(root_box)
        
        # ===== Version Selection Section =====
        version_box = QGroupBox("Version")
        version_layout = QVBoxLayout(version_box)
        
        # Search/filter box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.txt_version_search = QLineEdit()
        self.txt_version_search.setPlaceholderText("Type to filter versions...")
        self.txt_version_search.textChanged.connect(self._on_version_search)
        search_layout.addWidget(self.txt_version_search)
        version_layout.addLayout(search_layout)
        
        # Version dropdown
        self.combo_version = QComboBox()
        self.combo_version.currentTextChanged.connect(self._on_version_changed)
        version_layout.addWidget(self.combo_version)
        
        main_layout.addWidget(version_box)
        
        # ===== EXE Selection Section =====
        exe_box = QGroupBox("Executable")
        exe_layout = QHBoxLayout(exe_box)
        exe_layout.addWidget(QLabel("EXE:"))
        self.combo_exe = QComboBox()
        self.combo_exe.currentTextChanged.connect(self._on_exe_changed)
        exe_layout.addWidget(self.combo_exe, 1)
        main_layout.addWidget(exe_box)
        
        # ===== Log File Section =====
        log_box = QGroupBox("Log File")
        self.log_box = log_box
        log_layout = QHBoxLayout(log_box)
        self.txt_log_file = QLineEdit()
        self.txt_log_file.setPlaceholderText("e.g., test.log or full path")
        self.txt_log_file.setAcceptDrops(True)
        self.txt_log_file.installEventFilter(self)
        self.txt_log_file.textChanged.connect(self._update_matlab_button_state)
        self.log_box.setAcceptDrops(True)
        self.log_box.installEventFilter(self)
        self.btn_log_browse = QPushButton("Browse…")
        self.btn_log_browse.clicked.connect(self._on_log_browse)
        log_layout.addWidget(self.txt_log_file, 1)
        log_layout.addWidget(self.btn_log_browse)
        main_layout.addWidget(log_box)
        
        # ===== Control Buttons =====
        control_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setMinimumSize(80, 35)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_run.setEnabled(False)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("CancelButton")
        self.btn_stop.setMinimumSize(80, 35)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False)
        
        control_layout.addWidget(self.btn_run)
        control_layout.addWidget(self.btn_stop)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # ===== Output Section =====
        output_box = QGroupBox("Console Output")
        output_layout = QVBoxLayout(output_box)
        
        # Options row
        options_layout = QHBoxLayout()
        self.chk_timestamps = QCheckBox("Timestamps")
        self.chk_timestamps.setChecked(False)
        options_layout.addWidget(self.chk_timestamps)
        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        options_layout.addWidget(self.chk_autoscroll)
        self.btn_clear_output = QPushButton("Clear")
        self.btn_clear_output.setFixedWidth(80)
        self.btn_clear_output.clicked.connect(self._on_clear_output)
        options_layout.addWidget(self.btn_clear_output)
        self.btn_open_log_folder = QPushButton("Open Log Folder")
        self.btn_open_log_folder.setFixedWidth(140)
        self.btn_open_log_folder.clicked.connect(self._on_open_log_output_folder)
        self.btn_open_log_folder.setEnabled(False)
        options_layout.addWidget(self.btn_open_log_folder)
        self.btn_run_matlab_pop = QPushButton("Run MATLAB Pop")
        self.btn_run_matlab_pop.setFixedWidth(150)
        self.btn_run_matlab_pop.clicked.connect(self._on_run_matlab_pop)
        self.btn_run_matlab_pop.setEnabled(False)
        options_layout.addWidget(self.btn_run_matlab_pop)
        options_layout.addStretch()
        output_layout.addLayout(options_layout)
        
        # Output text area
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setMinimumHeight(250)
        output_layout.addWidget(self.txt_output)
        
        main_layout.addWidget(output_box, 1)
        
        # ===== Status Line =====
        self.lbl_status = QLabel("Idle")
        self.lbl_exit_code = QLabel("")
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.lbl_status, 1)
        status_layout.addWidget(self.lbl_exit_code)
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)
        self._update_run_button_state()
        self._update_matlab_button_state()
    

    

    
    # ===== Slot: Version search/filter =====
    @Slot(str)
    def _on_version_search(self, text: str):
        """Filter version dropdown based on search text."""
        if not self.root_path:
            return
        
        self._pending_search_text = text
        self._version_search_timer.start()

    def _apply_version_filter(self):
        """Apply search filter to cached version list."""
        if not self.root_path:
            return

        search_text = self._pending_search_text.strip().lower()
        all_versions = self._all_versions
        filtered = [v for v in all_versions if search_text in v.lower()] if search_text else all_versions

        previous_selection = self.combo_version.currentText()

        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItems(filtered)

        new_selection = ""
        if filtered:
            if previous_selection in filtered:
                self.combo_version.setCurrentText(previous_selection)
                new_selection = previous_selection
            else:
                self.combo_version.setCurrentIndex(0)
                new_selection = self.combo_version.currentText()

        self.combo_version.blockSignals(False)

        if new_selection != previous_selection:
            self._on_version_changed(new_selection)
        elif not new_selection:
            self._on_version_changed("")
    
    def _refresh_versions(self):
        """Refresh version list from root path."""
        if not self.root_path:
            self.combo_version.clear()
            return

        self._all_versions = ExeRunnerController.get_version_folders(self.root_path)
        self._apply_version_filter()

    def eventFilter(self, obj, event):
        targets = (getattr(self, "log_box", None), getattr(self, "txt_log_file", None))
        if obj in targets:
            et = event.type()

            if et == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    self.log_box.setStyleSheet(
                        "QGroupBox { border: 2px dashed #4c8bf5; border-radius: 6px; }"
                    )
                    return True
                return False

            if et == QEvent.DragMove:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
                return False

            if et == QEvent.DragLeave:
                self.log_box.setStyleSheet("")
                return True

            if et == QEvent.Drop:
                urls = event.mimeData().urls()
                self.log_box.setStyleSheet("")
                if not urls:
                    return False
                path = urls[0].toLocalFile()
                if not path or os.path.isdir(path):
                    return False
                self.txt_log_file.setText(path)
                event.acceptProposedAction()
                return True

        return super().eventFilter(obj, event)
    
    # ===== Slot: Version changed =====
    @Slot(str)
    def _on_version_changed(self, text: str):
        """Update exe list when version changes."""
        if not self.root_path or not text:
            self.combo_exe.clear()
            self.selected_version = None
            self._update_run_button_state()
            self._update_matlab_button_state()
            return
        
        self.selected_version = text
        version_path = os.path.join(self.root_path, text)
        
        exes = ExeRunnerController.get_exe_files(version_path)
        
        self.combo_exe.blockSignals(True)
        self.combo_exe.clear()
        
        if not exes:
            self.combo_exe.addItem("(no .exe files found)")
            self.combo_exe.setEnabled(False)
            self._set_status(f"Error: No .exe files in {text}\\64x\\")
        else:
            self.combo_exe.addItems(exes)
            self.combo_exe.setEnabled(True)
            self.selected_exe = exes[0]
            self._set_status(f"Version: {text} ({len(exes)} exe file(s))")
        
        self.combo_exe.blockSignals(False)
        self._update_run_button_state()
        self._update_matlab_button_state()
    
    # ===== Slot: EXE changed =====
    @Slot(str)
    def _on_exe_changed(self, text: str):
        """Update selected exe."""
        if text != "(no .exe files found)":
            self.selected_exe = text
        self._update_run_button_state()
    
    # ===== Slot: Log file browse =====
    @Slot()
    def _on_log_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Log File",
            "",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.txt_log_file.setText(path)
    
    def _update_run_button_state(self):
        """Enable/disable Run button based on current state."""
        can_run = bool(
            self.root_path and
            self.selected_version and
            self.selected_exe and
            self.selected_exe != "(no .exe files found)" and
            not self.runner.is_running and
            not self._matlab_running
        )
        self.btn_run.setEnabled(can_run)
    
    # ===== Slot: Run =====
    @Slot()
    def _on_run(self):
        """Validate and start the process."""
        self.btn_open_log_folder.setEnabled(False)
        self.btn_run_matlab_pop.setEnabled(False)
        # Validate log file
        log_file = self.txt_log_file.text().strip()
        is_valid, warning = ExeRunnerController.validate_log_file(log_file)
        
        if not is_valid:
            QMessageBox.warning(self, "Invalid Log File", warning)
            return
        
        if warning:
            result = QMessageBox.warning(
                self,
                "Log File Warning",
                warning + "\n\nProceed anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
        
        # Build paths
        exe_full_path = ExeRunnerController.build_exe_full_path(
            self.root_path,
            self.selected_version,
            self.selected_exe
        )
        working_dir = ExeRunnerController.get_working_directory(
            self.root_path,
            self.selected_version
        )
        
        # Clear output and start
        self.txt_output.clear()
        self.lbl_exit_code.setText("")
        
        success = self.runner.run_exe(exe_full_path, log_file, working_dir)
        if not success:
            self._set_status("Failed to start process")
    
    @Slot()
    def _on_process_started(self):
        """Handle process start."""
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.combo_version.setEnabled(False)
        self.combo_exe.setEnabled(False)
        self.btn_log_browse.setEnabled(False)
        self.txt_log_file.setEnabled(False)
        self.btn_run_matlab_pop.setEnabled(False)
        self._set_status("Running...")
    
    @Slot(str)
    def _on_process_output(self, text: str):
        """Append output to text area."""
        cursor = self.txt_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        for line in text.splitlines(True):
            fmt = QTextCharFormat()
            
            # Color error/traceback lines
            if any(keyword in line.lower() for keyword in ["error", "traceback", "exception", "failed"]):
                fmt.setForeground(QColor("red"))
            
            # Add timestamp if enabled
            if self.chk_timestamps.isChecked():
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                cursor.insertText(f"[{timestamp}] ", fmt)
            
            cursor.insertText(line, fmt)
        
        self.txt_output.setTextCursor(cursor)
        
        if self.chk_autoscroll.isChecked():
            self.txt_output.ensureCursorVisible()
    
    @Slot(int)
    def _on_process_finished(self, exit_code: int):
        """Handle process completion."""
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.combo_version.setEnabled(True)
        self.combo_exe.setEnabled(True if self.selected_exe != "(no .exe files found)" else False)
        self.btn_log_browse.setEnabled(True)
        self.txt_log_file.setEnabled(True)
        
        self.lbl_exit_code.setText(f"Exit code: {exit_code}")
        if exit_code == 0:
            self._set_status("Completed successfully")
        else:
            self._set_status(f"Completed with code {exit_code}")

        self._update_open_log_folder_button()
        self._update_matlab_button_state()
    
    @Slot(str)
    def _on_process_error(self, error_msg: str):
        """Handle process errors."""
        self._on_process_finished(1)
        self.txt_output.append(f"\n[ERROR] {error_msg}\n")
        self._set_status(f"Error: {error_msg}")
    
    # ===== Slot: Stop =====
    @Slot()
    def _on_stop(self):
        """Stop the running process."""
        self.runner.stop()
        self._set_status("Stopped by user")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.combo_version.setEnabled(True)
        self.combo_exe.setEnabled(True if self.selected_exe != "(no .exe files found)" else False)
        self.btn_log_browse.setEnabled(True)
        self.txt_log_file.setEnabled(True)
        self._update_open_log_folder_button()
        self._update_matlab_button_state()
    
    # ===== Slot: Clear output =====
    @Slot()
    def _on_clear_output(self):
        """Clear the output text area."""
        self.txt_output.clear()
        self.lbl_exit_code.setText("")
        self._set_status("Output cleared")
    
    def _set_status(self, text: str):
        """Update status label."""
        self.lbl_status.setText(text)

    def _resolve_log_file_path(self) -> Optional[str]:
        log_path = self.txt_log_file.text().strip()
        if not log_path:
            return None

        if os.path.isabs(log_path):
            return log_path

        if not self.root_path or not self.selected_version:
            return None

        working_dir = ExeRunnerController.get_working_directory(
            self.root_path,
            self.selected_version
        )
        return os.path.join(working_dir, log_path) if working_dir else None

    def _get_log_base_dir(self) -> Optional[str]:
        log_path = self.txt_log_file.text().strip()
        if not log_path:
            return None

        if os.path.isabs(log_path):
            base_dir = os.path.dirname(log_path)
            return base_dir if os.path.isdir(base_dir) else None

        if not self.root_path or not self.selected_version:
            return None

        base_dir = ExeRunnerController.get_working_directory(
            self.root_path,
            self.selected_version
        )
        return base_dir if os.path.isdir(base_dir) else None

    def _find_log_output_folder(self) -> Optional[str]:
        log_path = self.txt_log_file.text().strip()
        if not log_path:
            return None

        base_dir = self._get_log_base_dir()
        if not base_dir:
            return None

        log_name = os.path.basename(log_path)
        if not log_name:
            return None

        name_no_ext = os.path.splitext(log_name)[0]
        candidates = [
            os.path.join(base_dir, name_no_ext),
            os.path.join(base_dir, log_name),
        ]
        for folder in candidates:
            if os.path.isdir(folder):
                return folder
        return None

    def _update_open_log_folder_button(self):
        folder = self._find_log_output_folder()
        self.btn_open_log_folder.setEnabled(bool(folder))

    def _update_matlab_button_state(self):
        log_full_path = self._resolve_log_file_path()
        can_run = bool(
            log_full_path and
            os.path.isfile(log_full_path) and
            not self.runner.is_running and
            not self._matlab_running
        )
        self.btn_run_matlab_pop.setEnabled(can_run)

    @Slot()
    def _on_run_matlab_pop(self):
        log_full_path = self._resolve_log_file_path()
        if not log_full_path or not os.path.isfile(log_full_path):
            QMessageBox.warning(
                self,
                "Log File Not Found",
                "Log file not found. Run the EXE first or select a valid log file."
            )
            return

        if self._matlab_running:
            return

        try:
            import matlab.engine
        except Exception:
            QMessageBox.warning(
                self,
                "MATLAB Engine",
                "MATLAB Engine for Python is not installed or not available."
            )
            return

        sessions = matlab.engine.find_matlab()
        if not sessions:
            QMessageBox.warning(
                self,
                "MATLAB Engine",
                "No shared MATLAB session found. In MATLAB, run: matlab.engine.shareEngine"
            )
            return

        log_base_path = os.path.splitext(log_full_path)[0]
        if not log_base_path.endswith("\\"):
            log_base_path += "\\"

        self._matlab_running = True
        self._set_status("Running MATLAB pop (shared session)...")
        self._update_run_button_state()
        self._update_matlab_button_state()

        try:
            eng = matlab.engine.connect_matlab(sessions[0])

            eeglab_path = os.environ.get("EEGLAB_PATH") or os.environ.get("MATLAB_POP_PATH")
            if eeglab_path:
                eng.addpath(eng.genpath(eeglab_path), nargout=0)

            if eng.exist("pop", "file") != 2:
                raise RuntimeError("pop not found on MATLAB path")

            eng.pop(log_base_path, nargout=0)
            self._set_status("MATLAB pop finished")
        except Exception as exc:
            self.txt_output.append(f"\n[MATLAB ERROR] {exc}\n")
            self._set_status("MATLAB pop failed")
        finally:
            self._matlab_running = False
            self._update_run_button_state()
            self._update_matlab_button_state()

    @Slot()
    def _on_matlab_output(self):
        if not self._matlab_proc:
            return
        data = self._matlab_proc.readAllStandardOutput().data().decode(errors="replace")
        if not data:
            return

        cursor = self.txt_output.textCursor()
        cursor.movePosition(QTextCursor.End)

        for line in data.splitlines(True):
            fmt = QTextCharFormat()
            if self.chk_timestamps.isChecked():
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                cursor.insertText(f"[{timestamp}] ", fmt)
            cursor.insertText(f"[MATLAB] {line}", fmt)

        self.txt_output.setTextCursor(cursor)
        if self.chk_autoscroll.isChecked():
            self.txt_output.ensureCursorVisible()

    @Slot(int, int)
    def _on_matlab_finished(self, exit_code: int, exit_status: int):
        self._matlab_running = False
        self._set_status(f"MATLAB pop finished (code {exit_code})")
        self._update_run_button_state()
        self._update_matlab_button_state()

    @Slot()
    def _on_matlab_error(self, error: int):
        self._matlab_running = False
        self.txt_output.append(f"\n[MATLAB ERROR] Process error code: {error}\n")
        self._set_status("MATLAB pop failed")
        self._update_run_button_state()
        self._update_matlab_button_state()

    @Slot()
    def _on_open_log_output_folder(self):
        folder = self._find_log_output_folder()
        if not folder:
            QMessageBox.information(
                self,
                "Open Log Folder",
                "Log output folder not found yet. Run the EXE first."
            )
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

class ExeRunnerTab(QWidget):
    """Main EXE Runner tab with dual side-by-side panels."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_path: Optional[str] = None
        self.theme_is_dark = False
        self._init_ui()
        self._apply_root_path(DEFAULT_ROOT_PATH)
    
    def _init_ui(self):
        """Build the main layout with 2 side-by-side panels."""
        main_layout = QVBoxLayout(self)  # Changed from QHBoxLayout to vertical
        
        # ===== Root Path Section (shared) =====
        root_box = QGroupBox("Root Versions Folder")
        root_layout = QHBoxLayout(root_box)
        self.lbl_root = QLabel("No folder selected")
        self.btn_root_browse = QPushButton("Browse…")
        self.btn_root_browse.clicked.connect(self._on_root_browse)
        root_layout.addWidget(self.lbl_root, 1)
        root_layout.addWidget(self.btn_root_browse)
        
        # ===== Left Panel =====
        left_panel = ExeRunnerPanel("Left Runner")
        self.left_runner = left_panel
        
        # ===== Right Panel =====
        right_panel = ExeRunnerPanel("Right Runner")
        self.right_runner = right_panel
        
        # ===== Panels Layout (horizontal) =====
        panels_layout = QHBoxLayout()
        panels_layout.addWidget(left_panel, 1)
        panels_layout.addWidget(right_panel, 1)
        
        # ===== Add to Main Layout =====
        main_layout.addWidget(root_box, 0)      # Root at TOP (no stretch)
        main_layout.addLayout(panels_layout, 1) # Panels BELOW (grow to fill)
        
        self.setLayout(main_layout)
    
    def set_theme_dark(self, is_dark: bool):
        """Update theme styling for both panels."""
        self.theme_is_dark = is_dark
        # Theme updates would go here if needed

    def _apply_root_path(self, path: str):
        """Apply root path to UI and both panels if valid."""
        is_valid, _ = ExeRunnerController.validate_root_path(path)
        if not is_valid:
            return

        self.root_path = path
        self.lbl_root.setText(os.path.basename(path))

        # Update both panels with the same root path
        self.left_runner.set_root_path(path)
        self.right_runner.set_root_path(path)
    
    @Slot()
    def _on_root_browse(self):
        """Browse and select root path, apply to both panels."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Root Versions Folder",
            DEFAULT_ROOT_PATH
        )
        if path:
            self._apply_root_path(path)