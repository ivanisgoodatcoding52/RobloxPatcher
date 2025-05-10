"""
Ratnet key patcher implementation for RCCService.
"""
import re
from pathlib import Path

from config import ClientType, PatchConfig
from patchers.base_patcher import BasePatcher


class RatnetKeyPatcher(BasePatcher):
    """Patcher for the Ratnet key in RCCService."""
    
    # Known Ratnet keys for different RCCService versions
    KNOWN_KEYS = {
        "0.285.0.49012": "1ro78912031q78334p81s417q586ss732s4qr2n4",
        "0.206.0.62042": "77on3909rpn6n323ro1274963ro43776rsn18488"
    }
    
    def validate(self) -> bool:
        """
        Validate that the configuration has all required elements for this patch.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.client_path.exists():
            self.logger.error(f"Client file not found: {self.client_path}")
            return False
        
        if self.config.client_type != ClientType.RCC_SERVICE:
            self.logger.error("Ratnet key patch is only applicable to RCCService")
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
        Apply the Ratnet key patch to the client.
        
        Returns:
            True if patching was successful, False otherwise
        """
        if not self.validate():
            return False
        
        try:
            # Create backup first
            if not self.backup_client():
                return False
            
            # Display known keys information
            self.logger.info("Known Ratnet keys:")
            for version, key in self.KNOWN_KEYS.items():
                self.logger.info(f"RCCService-{version}: {key}")
            
            self.logger.warning("This is a manual step. Please follow these instructions:")
            self.logger.warning("1. Open x64dbg and select x32dbg mode")
            self.logger.warning(f"2. Drag your client ({self.client_path}) into the window")
            self.logger.warning("3. Go to Symbols, and double click on your client file")
            self.logger.warning("4. Click the [Az] icon in the top right corner to open string search")
            self.logger.warning('5. Enable RegEx and search for: "^.[A-Za-z0-9]{40}.$"')
            self.logger.warning("6. Double click on the first result")
            self.logger.warning("7. Locate the original key in the dump and replace it with the appropriate key")
            self.logger.warning("8. Press Ctrl+P and select 'Patch file'")
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying Ratnet key patch: {e}")
            return False