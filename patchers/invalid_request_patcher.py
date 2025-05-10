"""
Invalid request patcher implementation.
"""
import tempfile
from pathlib import Path

from config import PatchConfig
from patchers.base_patcher import BasePatcher


class InvalidRequestPatcher(BasePatcher):
    """Patcher for the 'invalid request' check in the client."""
    
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
        Apply the 'invalid request' patch to the client.
        
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
            self.logger.warning('5. Search for: "invalid request"')
            self.logger.warning("6. Double click on each result")
            self.logger.warning("7. Find 'je' (or 'jne') instructions a few lines above the result and replace with 'jmp'")
            self.logger.warning("8. Press Ctrl+P and select 'Patch file'")
            
            # Display security warning
            self.logger.warning("""
IMPORTANT SECURITY WARNING:
---------------------------
This patch bypasses a key security mechanism in the Roblox client that validates
external requests. With this patch applied, your client will no longer verify the
source and validity of network communications.

This can allow:
- Malicious scripts to be executed
- Unauthorized access to game data
- Remote code execution vulnerabilities
- Cross-site request forgery attacks

It is HIGHLY RECOMMENDED to only use this patch:
1. In a strictly controlled environment
2. For friends-only revivals
3. Behind a proper launcher that adds additional security

DO NOT use this patch for public revivals without additional security measures.
            """)
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying invalid request patch: {e}")
            return False