"""
Trust check patcher implementation.
"""
from pathlib import Path

from config import PatchConfig
from patchers.base_patcher import BasePatcher


class TrustCheckPatcher(BasePatcher):
    """Patcher for the 'trust check' in the client."""
    
    def validate(self) -> bool:
        """
        Validate that the configuration has all required elements for this patch.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.client_path.exists():
            self.logger.error(f"Client file not found: {self.client_path}")
            return False
        
        if not self.config.x64dbg_path:
            self.logger.error("x64dbg path is required")
            return False
        
        x64dbg_path = Path(self.config.x64dbg_path)
        if not x64dbg_path.exists():
            self.logger.error(f"x64dbg not found: {x64dbg_path}")
            return False
        
        return True
    
    def apply(self) -> bool:
        """
        Apply the trust check patch to the client.
        
        Returns:
            True if patching was successful, False otherwise
        """
        if not self.validate():
            return False
        
        try:
            # Create backup first
            if not self.backup_client():
                return False
            
            self.logger.warning("SECURITY RISK: This patch poses a major security risk!")
            self.logger.warning("This is a manual step. Please follow these instructions:")
            self.logger.warning("1. Open x64dbg and select x32dbg mode")
            self.logger.warning(f"2. Drag your client ({self.client_path}) into the window")
            self.logger.warning("3. Go to Symbols, and double click on your client file")
            self.logger.warning("4. Click the [Az] icon in the top right corner to open string search")
            self.logger.warning('5. Search for: "trust check failed for %s"')
            self.logger.warning("6. Double click on each result")
            self.logger.warning("7. Find 'je' (or 'jne') instructions a few lines above the result and replace with 'jmp'")
            self.logger.warning("8. Press Ctrl+P and select 'Patch file'")
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying trust check patch: {e}")
            return False