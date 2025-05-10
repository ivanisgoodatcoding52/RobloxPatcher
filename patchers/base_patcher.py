"""
Base patcher class that all specific patchers inherit from.
"""
import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from config import PatchConfig


class BasePatcher(ABC):
    """Base class for all patchers."""
    
    def __init__(self, config: PatchConfig):
        """
        Initialize the patcher.
        
        Args:
            config: The patch configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client_path = Path(self.config.client_path)
    
    def backup_client(self) -> Optional[Path]:
        """
        Create a backup of the client file before patching.
        
        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            if not self.client_path.exists():
                self.logger.error(f"Client file not found: {self.client_path}")
                return None
            
            backup_path = self.client_path.with_suffix(f"{self.client_path.suffix}.backup")
            
            # Only create backup if it doesn't already exist
            if not backup_path.exists():
                shutil.copy2(self.client_path, backup_path)
                self.logger.info(f"Backup created at: {backup_path}")
            else:
                self.logger.info(f"Backup already exists at: {backup_path}")
                
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_from_backup(self) -> bool:
        """
        Restore the client file from backup.
        
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            backup_path = self.client_path.with_suffix(f"{self.client_path.suffix}.backup")
            
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            shutil.copy2(backup_path, self.client_path)
            self.logger.info(f"Restored from backup: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
    
    @abstractmethod
    def apply(self) -> bool:
        """
        Apply the patch to the client.
        
        Returns:
            True if patching was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that the configuration has all required elements for this patch.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass