"""
Public key patcher implementation.
"""
import os
import re
import subprocess
from pathlib import Path

from config import PatchConfig
from patchers.base_patcher import BasePatcher


class PublicKeyPatcher(BasePatcher):
    """Patcher for changing the public key in the client."""
    
    def validate(self) -> bool:
        """
        Validate that the configuration has all required elements for this patch.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.client_path.exists():
            self.logger.error(f"Client file not found: {self.client_path}")
            return False
        
        if not self.config.rbxsigtools_path:
            self.logger.error("RbxSigTools path is required")
            return False
        
        rbxsigtools_path = Path(self.config.rbxsigtools_path)
        if not rbxsigtools_path.exists():
            self.logger.error(f"RbxSigTools not found: {rbxsigtools_path}")
            return False
        
        key_gen_path = rbxsigtools_path / "KeyGenerator.exe"
        if not key_gen_path.exists():
            self.logger.error(f"KeyGenerator.exe not found in: {rbxsigtools_path}")
            return False
        
        return True
    
    def apply(self) -> bool:
        """
        Apply the public key patch to the client.
        
        Returns:
            True if patching was successful, False otherwise
        """
        if not self.validate():
            return False
        
        try:
            # Create backup first
            if not self.backup_client():
                return False
            
            # Get RbxSigTools directory
            rbxsigtools_path = Path(self.config.rbxsigtools_path)
            key_gen_path = rbxsigtools_path / "KeyGenerator.exe"
            
            # Run KeyGenerator.exe
            self.logger.info(f"Running KeyGenerator.exe in {rbxsigtools_path}")
            result = subprocess.run(
                [str(key_gen_path)], 
                cwd=str(rbxsigtools_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"KeyGenerator.exe failed with exit code {result.returncode}")
                self.logger.error(f"Output: {result.stdout}")
                self.logger.error(f"Error: {result.stderr}")
                return False
            
            # Check for the generated public key
            public_key_path = rbxsigtools_path / "PublicKeyBlob.txt"
            if not public_key_path.exists():
                self.logger.error(f"PublicKeyBlob.txt was not created in: {rbxsigtools_path}")
                return False
            
            # Read the public key
            with open(public_key_path, 'r') as file:
                new_public_key = file.read().strip()
            
            self.logger.info(f"Generated new public key: {new_public_key[:20]}...")
            
            # Replace the public key in the client
            with open(self.client_path, 'rb') as file:
                content = file.read()
            
            # Look for public key pattern starting with "BGIAA"
            public_key_pattern = re.compile(b'BGIAA[A-Za-z0-9+/=]+')
            matches = public_key_pattern.findall(content)
            
            if not matches:
                self.logger.error("Could not find public key in client file")
                return False
            
            self.logger.info(f"Found {len(matches)} public key occurrences")
            
            # Replace each occurrence of the public key
            for old_key in matches:
                content = content.replace(old_key, new_public_key.encode())
            
            # Write the modified content back to the client
            with open(self.client_path, 'wb') as file:
                file.write(content)
            
            self.logger.info("Public key patch applied successfully")
            
            # Log success information about the generated keys
            private_key_path = rbxsigtools_path / "PrivateKeyBlob.txt"
            private_key_pem_path = rbxsigtools_path / "PrivateKey.pem"
            
            if private_key_path.exists():
                self.logger.info(f"Private key blob saved to: {private_key_path}")
            
            if private_key_pem_path.exists():
                self.logger.info(f"Private key PEM saved to: {private_key_pem_path}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying public key patch: {e}")
            return False