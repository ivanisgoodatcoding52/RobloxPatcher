import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Set up logging for the application.
    
    Args:
        log_dir: Directory to store log files (default: logs in current directory)
        level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, "revival_creator.log")
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Set formatters
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup message
    logging.info("Logging initialized")


def get_patchers_dir() -> Path:
    """
    Get the path to the patchers directory.
    
    Returns:
        Path to the patchers directory
    """
    return Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "patchers"))


def backup_file(file_path: str) -> Optional[str]:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file, or None if backup failed
    """
    try:
        import shutil
        
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None


def is_admin() -> bool:
    """
    Check if the application is running with administrative privileges.
    
    Returns:
        True if running as admin, False otherwise
    """
    try:
        # Windows check
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        # Unix check (root has UID 0)
        return os.geteuid() == 0
    except:
        return False
