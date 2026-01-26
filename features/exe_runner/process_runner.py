"""
EXE process runner using QProcess for live output streaming.
"""
import os
from typing import Optional, Callable
from PySide6.QtCore import QProcess, Slot, Signal, QObject


class ExeProcessRunner(QObject):
    """Manages Windows .exe execution with live stdout/stderr streaming."""
    
    # Signals
    output_received = Signal(str)  # emitted for each output chunk
    finished = Signal(int)          # emitted on process finish with exit code
    error_occurred = Signal(str)    # emitted on process error
    started = Signal()              # emitted when process starts
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc: Optional[QProcess] = None
        self.is_running = False
    
    def run_exe(self, exe_path: str, log_file: str, working_dir: str) -> bool:
        """
        Start the exe process.
        
        Args:
            exe_path: Full path to .exe file
            log_file: Log file argument (name or path)
            working_dir: Working directory for the process
        
        Returns:
            True if process started successfully, False otherwise
        """
        if not os.path.exists(exe_path):
            self.error_occurred.emit(f"Executable not found: {exe_path}")
            return False
        
        if not os.path.isdir(working_dir):
            self.error_occurred.emit(f"Working directory not found: {working_dir}")
            return False
        
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(working_dir)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        
        # Connect signals
        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(self._on_error)
        
        # Start process with arguments
        args = [log_file]
        self.proc.setProgram(exe_path)
        self.proc.setArguments(args)
        self.proc.start()
        
        if not self.proc.waitForStarted(3000):
            self.error_occurred.emit("Failed to start process within timeout")
            return False
        
        self.is_running = True
        self.started.emit()
        return True
    
    @Slot()
    def _on_output(self):
        """Read available output from process."""
        if not self.proc:
            return
        data = self.proc.readAllStandardOutput().data().decode(errors="replace")
        if data:
            self.output_received.emit(data)
    
    @Slot(int, int)
    def _on_finished(self, exit_code: int, exit_status: int):
        """Handle process completion."""
        self.is_running = False
        self.finished.emit(exit_code)
    
    @Slot()
    def _on_error(self, error: int):
        """Handle process errors."""
        self.is_running = False
        error_msgs = {
            0: "Failed to start",
            1: "Crashed",
            2: "Timed out",
            3: "Read error",
            4: "Write error",
            5: "Unknown error"
        }
        msg = error_msgs.get(error, f"Unknown error code {error}")
        self.error_occurred.emit(f"Process error: {msg}")
    
    def stop(self):
        """Stop the running process."""
        if self.proc and self.is_running:
            self.proc.terminate()
            if not self.proc.waitForFinished(3000):
                self.proc.kill()
                self.proc.waitForFinished(1000)
            self.is_running = False
