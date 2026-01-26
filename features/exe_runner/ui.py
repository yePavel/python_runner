"""
UI widgets and layout for EXE Runner tab.
"""
import os
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QGroupBox, QFileDialog, QMessageBox, QCheckBox
)

from .controller import ExeRunnerController
from .process_runner import ExeProcessRunner


class ExeRunnerTab(QWidget):
    """Main UI for the EXE Runner feature."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_path: Optional[str] = None
        self.selected_version: Optional[str] = None
        self.selected_exe: Optional[str] = None
        self.theme_is_dark = False
        
        self.runner = ExeProcessRunner(self)
        self.runner.started.connect(self._on_process_started)
        self.runner.output_received.connect(self._on_process_output)
        self.runner.finished.connect(self._on_process_finished)
        self.runner.error_occurred.connect(self._on_process_error)
        
        self._init_ui()
    
    def _init_ui(self):
        """Build the UI layout."""
        main_layout = QVBoxLayout(self)
        
        # ===== Root Path Section =====
        root_box = QGroupBox("Root Versions Folder")
        root_layout = QHBoxLayout(root_box)
        self.lbl_root = QLabel("No folder selected")
        self.btn_root_browse = QPushButton("Browse…")
        self.btn_root_browse.clicked.connect(self._on_root_browse)
        root_layout.addWidget(self.lbl_root, 1)
        root_layout.addWidget(self.btn_root_browse)
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
        log_layout = QHBoxLayout(log_box)
        self.txt_log_file = QLineEdit()
        self.txt_log_file.setPlaceholderText("e.g., test.log or full path")
        self.btn_log_browse = QPushButton("Browse…")
        self.btn_log_browse.clicked.connect(self._on_log_browse)
        log_layout.addWidget(self.txt_log_file, 1)
        log_layout.addWidget(self.btn_log_browse)
        main_layout.addWidget(log_box)
        
        # ===== Control Buttons =====
        control_layout = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setMinimumSize(100, 40)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_run.setEnabled(False)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("CancelButton")
        self.btn_stop.setMinimumSize(100, 40)
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
        self.chk_timestamps = QCheckBox("Show timestamps")
        self.chk_timestamps.setChecked(False)
        options_layout.addWidget(self.chk_timestamps)
        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        options_layout.addWidget(self.chk_autoscroll)
        self.btn_clear_output = QPushButton("Clear")
        self.btn_clear_output.setFixedWidth(80)
        self.btn_clear_output.clicked.connect(self._on_clear_output)
        options_layout.addWidget(self.btn_clear_output)
        options_layout.addStretch()
        output_layout.addLayout(options_layout)
        
        # Output text area
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setMinimumHeight(250)
        output_layout.addWidget(self.txt_output)
        
        main_layout.addWidget(output_box, 1)
        
        # ===== Status Line =====
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("Idle")
        status_layout.addWidget(self.lbl_status, 1)
        self.lbl_exit_code = QLabel("")
        status_layout.addWidget(self.lbl_exit_code)
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)
        self._update_run_button_state()
    
    def set_theme_dark(self, is_dark: bool):
        """Update theme styling."""
        self.theme_is_dark = is_dark
    
    # ===== Slot: Root folder browse =====
    @Slot()
    def _on_root_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Root Versions Folder")
        if path:
            self.root_path = path
            self.lbl_root.setText(os.path.basename(path))
            self.txt_version_search.clear()
            self._refresh_versions()
            self._set_status("Root path selected")
    
    # ===== Slot: Version search/filter =====
    @Slot(str)
    def _on_version_search(self, text: str):
        """Filter version dropdown based on search text."""
        if not self.root_path:
            return
        
        all_versions = ExeRunnerController.get_version_folders(self.root_path)
        search_text = text.strip().lower()
        
        filtered = [v for v in all_versions if search_text in v.lower()] if search_text else all_versions
        
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItems(filtered)
        self.combo_version.blockSignals(False)
        
        self._on_version_changed("")
    
    def _refresh_versions(self):
        """Refresh version list from root path."""
        if not self.root_path:
            self.combo_version.clear()
            return
        
        versions = ExeRunnerController.get_version_folders(self.root_path)
        self.combo_version.blockSignals(True)
        self.combo_version.clear()
        self.combo_version.addItems(versions)
        self.combo_version.blockSignals(False)
        
        if versions:
            self._on_version_changed(versions[0])
    
    # ===== Slot: Version changed =====
    @Slot(str)
    def _on_version_changed(self, text: str):
        """Update exe list when version changes."""
        if not self.root_path or not text:
            self.combo_exe.clear()
            self.selected_version = None
            self._update_run_button_state()
            return
        
        self.selected_version = text
        version_path = os.path.join(self.root_path, text)
        
        exes = ExeRunnerController.get_exe_files(version_path)
        
        self.combo_exe.blockSignals(True)
        self.combo_exe.clear()
        
        if not exes:
            self.combo_exe.addItem("(no .exe files found)")
            self.combo_exe.setEnabled(False)
            self._set_status(f"Error: No .exe files in {text}\\bit\\")
        else:
            self.combo_exe.addItems(exes)
            self.combo_exe.setEnabled(True)
            self.selected_exe = exes[0]
            self._set_status(f"Version: {text} ({len(exes)} exe file(s))")
        
        self.combo_exe.blockSignals(False)
        self._update_run_button_state()
    
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
            not self.runner.is_running
        )
        self.btn_run.setEnabled(can_run)
    
    # ===== Slot: Run =====
    @Slot()
    def _on_run(self):
        """Validate and start the process."""
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
        self.btn_root_browse.setEnabled(False)
        self.btn_log_browse.setEnabled(False)
        self.txt_log_file.setEnabled(False)
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
        self.btn_root_browse.setEnabled(True)
        self.btn_log_browse.setEnabled(True)
        self.txt_log_file.setEnabled(True)
        
        self.lbl_exit_code.setText(f"Exit code: {exit_code}")
        if exit_code == 0:
            self._set_status("Completed successfully")
        else:
            self._set_status(f"Completed with code {exit_code}")
    
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
        self.btn_root_browse.setEnabled(True)
        self.btn_log_browse.setEnabled(True)
        self.txt_log_file.setEnabled(True)
    
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
