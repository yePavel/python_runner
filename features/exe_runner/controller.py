"""
Business logic for EXE Runner: folder scanning, validation, exe discovery.
"""
import os
from typing import List, Optional, Tuple


class ExeRunnerController:
    """Handles validation and discovery logic for EXE Runner."""
    
    @staticmethod
    def validate_root_path(path: str) -> Tuple[bool, str]:
        """
        Validate the root versions directory.
        
        Returns:
            (is_valid, error_message)
        """
        if not path or not path.strip():
            return False, "Root path cannot be empty"
        
        if not os.path.isdir(path):
            return False, f"Path does not exist: {path}"
        
        return True, ""
    
    @staticmethod
    def get_version_folders(root_path: str) -> List[str]:
        """
        Discover all version folders under root.
        
        Returns:
            List of folder names (basenames), sorted alphabetically
        """
        if not os.path.isdir(root_path):
            return []
        
        try:
            items = os.listdir(root_path)
            folders = [
                item for item in items
                if os.path.isdir(os.path.join(root_path, item)) and item[:1].isdigit()
            ]
            return sorted(folders)
        except Exception:
            return []
    
    @staticmethod
    def get_exe_files(version_path: str) -> List[str]:
        """
        Discover all .exe files in <version>\\64x\\ folder.
        
        Returns:
            List of exe file names (basenames), sorted alphabetically
        """
        bit_path = os.path.join(version_path, "64x")
        
        if not os.path.isdir(bit_path):
            return []
        
        try:
            items = os.listdir(bit_path)
            exe_files = [
                item for item in items
                if item.lower().endswith(".exe") and os.path.isfile(os.path.join(bit_path, item))
            ]
            return sorted(exe_files)
        except Exception:
            return []
    
    @staticmethod
    def validate_log_file(log_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate log file path.
        
        Returns:
            (is_valid, warning_message)
            is_valid=True means we can proceed (file exists or is a relative name)
            warning_message=None means no issues; otherwise a warning to show user
        """
        if not log_path or not log_path.strip():
            return False, "Log file name cannot be empty"
        
        # Absolute path
        if os.path.isabs(log_path):
            if os.path.exists(log_path):
                return True, None
            else:
                return True, f"Warning: File does not exist: {log_path}\nEXE may create it."
        
        # Relative name (e.g., "test.log")
        return True, None
    
    @staticmethod
    def build_exe_full_path(root_path: str, version_name: str, exe_name: str) -> str:
        """Build full path to exe."""
        return os.path.join(root_path, version_name, "64x", exe_name)
    
    @staticmethod
    def get_working_directory(root_path: str, version_name: str) -> str:
        """Get the working directory for exe (the 64x folder)."""
        return os.path.join(root_path, version_name, "64x")
