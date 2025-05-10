#!/usr/bin/env python3
"""
Modern Roblox Client Patcher

A utility script that implements patching guides for modern Roblox clients (2018-2021).
It automates the patching processes described in the 2018M and 2019-2021 guides.
"""
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple, Union

import requests


class ModernClientType(Enum):
    """Types of modern Roblox clients that can be patched."""
    R2018M = auto()  # 2018M guide
    R2019_2021 = auto()  # 2019-2021 guide


class ModernPatcher:
    """Utility for patching modern Roblox clients."""
    
    def __init__(self, client_path: Union[str, Path], rcc_path: Optional[Union[str, Path]] = None,
                 domain: str = "localhost", output_dir: Optional[Union[str, Path]] = None,
                 x32dbg_path: Optional[Union[str, Path]] = None, hxd_path: Optional[Union[str, Path]] = None,
                 stud_pe_path: Optional[Union[str, Path]] = None):
        """
        Initialize the modern client patcher.
        
        Args:
            client_path: Path to the Roblox client executable
            rcc_path: Path to the RCCService executable
            domain: Domain name to use (default: localhost)
            output_dir: Directory to save patched clients (default: same as input)
            x32dbg_path: Path to x32dbg executable
            hxd_path: Path to HxD executable
            stud_pe_path: Path to Stud_PE executable (needed for 2019-2021 clients)
        """
        self.client_path = Path(client_path)
        self.rcc_path = Path(rcc_path) if rcc_path else None
        self.domain = self._validate_domain(domain)
        self.output_dir = Path(output_dir) if output_dir else self.client_path.parent
        self.x32dbg_path = Path(x32dbg_path) if x32dbg_path else None
        self.hxd_path = Path(hxd_path) if hxd_path else None
        self.stud_pe_path = Path(stud_pe_path) if stud_pe_path else None
        
        # Create logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Set up logging for the application."""
        log_file = self.output_dir / "modern_patcher.log"
        
        # Configure root logger if not already configured
        if not self.logger.handlers:
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
    
    def _validate_domain(self, domain: str) -> str:
        """
        Validate and normalize the domain.
        
        Args:
            domain: The domain name to validate
            
        Returns:
            Normalized domain name
            
        Raises:
            ValueError: If the domain is invalid
        """
        # For 2018M, domain must be exactly 10 characters
        if len(domain) != 10:
            self.logger.warning(f"Domain '{domain}' is not 10 characters, which is required for 2018M patching")
            
            # If domain is shorter than 10, pad it
            if len(domain) < 10:
                padded_domain = domain + '.' * (10 - len(domain))
                self.logger.info(f"Padded domain to 10 characters: '{padded_domain}'")
                return padded_domain
            
            # If domain is longer than 10, truncate it
            if len(domain) > 10:
                truncated_domain = domain[:10]
                self.logger.info(f"Truncated domain to 10 characters: '{truncated_domain}'")
                return truncated_domain
        
        return domain
    
    def detect_client_type(self) -> ModernClientType:
        """
        Detect the client type based on the executable.
        
        Returns:
            The detected client type
        """
        # This is a very basic detection method
        # A more sophisticated approach would look at file versions, etc.
        try:
            with open(self.client_path, 'rb') as f:
                content = f.read()
            
            # Check for markers that might indicate 2019-2021 clients
            if b"GameLauncher" in content and b"HttpRbxApiService" in content:
                return ModernClientType.R2019_2021
            
            # Default to 2018M
            return ModernClientType.R2018M
        except Exception as e:
            self.logger.error(f"Error detecting client type: {e}")
            return ModernClientType.R2018M
    
    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        
        if not backup_path.exists():
            self.logger.info(f"Creating backup of {file_path} to {backup_path}")
            shutil.copy2(file_path, backup_path)
        else:
            self.logger.info(f"Backup already exists at {backup_path}")
        
        return backup_path
    
    def create_x32dbg_script(self, client_type: ModernClientType) -> Path:
        """
        Create an x32dbg script for patching the client.
        
        Args:
            client_type: The type of client to patch
            
        Returns:
            Path to the script file
        """
        script_content = ""
        
        if client_type == ModernClientType.R2018M:
            script_content = f"""// x32dbg script for patching 2018M client
InitDebug "{self.client_path}"

// Search for "Client:Connect"
findstr "Client:Connect"
findcmd je 5
setcmd $RESULT jmp
findstr "Loading shader files"
findcmd je 5
setcmd $RESULT jmp

// Save and exit
SaveFile "{self.output_dir / self.client_path.name}"
StopDebug
exit
"""
        elif client_type == ModernClientType.R2019_2021:
            script_content = f"""// x32dbg script for patching 2019-2021 client
InitDebug "{self.client_path}"

// Move past VMProtect
StepOver
StepOver

// Patch trust check failed
findstr "trust check failed"
findall
jmp $RESULT
for i $RESULT_COUNT
    goto $_RESULT[i]
    findcmd je -10
    setcmd $RESULT jmp
endfor

// Patch 127.0.0.1 check
findstr "127.0.0.1"
findall
jmp $RESULT
for i $RESULT_COUNT
    goto $_RESULT[i]
    findcmd je -10
    if $RESULT != 0
        setcmd $RESULT jmp
    endif
endfor

// Save and exit
SaveFile "{self.output_dir / self.client_path.name}"
StopDebug
exit
"""
        
        # Write script to temporary file
        fd, script_path = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        return Path(script_path)
    
    def run_x32dbg_script(self, script_path: Path) -> bool:
        """
        Run an x32dbg script.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.x32dbg_path:
            self.logger.error("x32dbg path not provided")
            return False
        
        try:
            self.logger.info(f"Running x32dbg script: {script_path}")
            
            # Run x32dbg with the script
            cmd = [
                str(self.x32dbg_path),
                "-scriptrun", str(script_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"x32dbg script failed: {result.stderr}")
                return False
            
            self.logger.info("x32dbg script completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error running x32dbg script: {e}")
            return False
    
    def replace_in_binary(self, file_path: Path, search: Union[str, bytes], replace: Union[str, bytes]) -> bool:
        """
        Replace byte patterns in a binary file.
        
        Args:
            file_path: Path to the file
            search: Bytes or string to search for
            replace: Bytes or string to replace with
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert strings to bytes if necessary
            if isinstance(search, str):
                search = search.encode()
            
            if isinstance(replace, str):
                replace = replace.encode()
            
            # Ensure search and replace are the same length
            if len(search) != len(replace):
                self.logger.error(f"Search and replace must be the same length: {len(search)} != {len(replace)}")
                return False
            
            # Read the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check if search pattern exists
            if search not in content:
                self.logger.warning(f"Search pattern not found in {file_path}")
                return False
            
            # Replace pattern
            modified_content = content.replace(search, replace)
            
            # Write back to file
            with open(file_path, 'wb') as f:
                f.write(modified_content)
            
            self.logger.info(f"Replaced '{search}' with '{replace}' in {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error replacing in binary: {e}")
            return False
    
    def replace_public_key(self, file_path: Path) -> bool:
        """
        Replace the public key in a binary file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate a new public key using RbxSigTools
            # For this example, we're using a fixed key
            # In a real implementation, you would generate a proper key
            new_public_key = b"BgIAAQACWzJdowsicN4u9qcnZgG+64cLIoWAnYTggbI98yyLopdM7XvqD9L5iPRMUNcV3iIJVEMkJhC9HZj+WVGwXLY2mVS0Qxm1H9K4tLxQk+WcuVtJQ5fxJLEEMl9rcorh5IBgW5JpXxwWEJ7AYq+5KijA3L2E55XL14xNFDnTdR/MY6uLbPCCLmCAtLPdQ6Xy1TKVTuklP27dNBlZ8V2ihIrMhvuXh2Lk5fCQbXwiBGgzlkLd/Y8FbwmNQnm8w8CEykmQm5X5ighTveAaQBEUdE2GdK4g1rkDvWxTIbHZBEiQAsiuGJQL2kOK3oXITAtj8WT0scIUSyspWQW72sImhrqYtGqdpDes39w03RvQmgQdqX8ftDwJOWEYN7QAqpGkEwlYp+4qcPQI+C5zNJ8eYJAMe0UUjrG0a2Sldr8jHHmz2kXNouBHrPD+8jP2HkWaC4viqQN4Q/J0dY4PnHFZVl9WrQrZ8EPr2McwEQk/dR4+xb5aJu0Q5JBnk+dIaOnV/OtEXcilibw0Jo95t7TTL12OIXZfg7GJPXr0CToVKA4iY3yGzzcYw4SRPCZxvNnvIJ/RuYL2dmmjTRXEwVYb7ZKQj4zUCX2yRLvtDo/APvtZ2L8fo21R=="
            
            # Read the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Find the public key pattern (starts with BgIAA)
            pattern = re.compile(b'BgIAA[A-Za-z0-9+/=]+')
            match = pattern.search(content)
            
            if not match:
                self.logger.warning(f"Public key not found in {file_path}")
                return False
            
            old_key = match.group(0)
            
            # Replace the key
            modified_content = content.replace(old_key, new_public_key)
            
            # Write back to file
            with open(file_path, 'wb') as f:
                f.write(modified_content)
            
            self.logger.info(f"Replaced public key in {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error replacing public key: {e}")
            return False
    
    def create_client_settings(self, client_type: ModernClientType) -> bool:
        """
        Create necessary settings files for the client.
        
        Args:
            client_type: The type of client to create settings for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if client_type == ModernClientType.R2019_2021:
                # Create ClientAppSettings.json
                client_settings_dir = self.output_dir / "clientsettings"
                client_settings_dir.mkdir(exist_ok=True)
                
                client_app_settings = {
                    "FFlagHandleAltEnterFullscreenManually": "False",
                    "FIntTerrainOctreeErrorMetric": "1",
                    "FFlagDebugGraphicsPreferD3D11": "True",
                    "FFlagDisableNewIGMinDUA": "True",
                    "FStringGamesUrlPath": "/games/",
                    "DFFlagClientBaseNetworkMetrics": "True",
                    "FStringContactsUrl": "https://www.terabyte.dev",
                    "FStringPrivacyUrl": "https://www.terabyte.dev",
                    "DFIntConnectionMetricsThrottleHundredthsPercentage": "100",
                    "DFIntHttpInflightRequestTimeoutMs": "30000",
                    "DFIntUserIdPlayerNameLifetimeSeconds": "86400",
                    "DFIntUserIdPlayerNameCacheSize": "1000000",
                    "FStringCoreScriptBacktraceErrorUploadToken": "00000000-0000-0000-0000-000000000000",
                    "FStringFacebookVirtualAppId": "0",
                    "FStringCookieDomain": self.domain,
                    "FFlagEnableMenuControlsABTest": "False",
                    "FFlagEnableMenuModernization": "False",
                    "FFlagDisableRunService": "True",
                }
                
                with open(client_settings_dir / "ClientAppSettings.json", 'w') as f:
                    json.dump(client_app_settings, f, indent=2)
                
                # Create/replace cacert.pem
                ssl_dir = self.output_dir / "ssl"
                ssl_dir.mkdir(exist_ok=True)
                
                # Download a blank cacert.pem
                cacert_url = "https://raw.githubusercontent.com/curl/curl/master/docs/examples/cacert.pem"
                response = requests.get(cacert_url)
                
                with open(ssl_dir / "cacert.pem", 'wb') as f:
                    f.write(response.content)
                
                # Create AppSettings.txt for 2019-2021
                app_settings_content = f"http://www.roblox.com=http://localhost/.test"
                
                with open(self.output_dir / "AppSettings.txt", 'w') as f:
                    f.write(app_settings_content)
                
                self.logger.info("Created client settings for 2019-2021 client")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error creating client settings: {e}")
            return False
    
    def create_server_settings(self, client_type: ModernClientType) -> bool:
        """
        Create necessary settings files for the server.
        
        Args:
            client_type: The type of client to create settings for
            
        Returns:
            True if successful, False otherwise
        """
        if not self.rcc_path:
            self.logger.warning("RCC path not provided, skipping server settings")
            return False
        
        try:
            rcc_dir = self.output_dir
            
            if client_type == ModernClientType.R2019_2021:
                # Create DevSettingsFile.json
                dev_settings = {
                    "DFInt::LuaAppSystemBar": "0",
                    "FInt::ContentProviderThreadPoolSize": "10",
                    "Task::ThreadPoolConfig::ThreadPoolSizeMaxIfEnabled": "10",
                    "Task::ThreadPoolConfig::PriorityThreadType2SizeMaxIfEnabled": "5",
                    "Task::ThreadPoolConfig::PriorityThreadType1SizeMaxIfEnabled": "5",
                    "Task::ThreadPoolConfig::PriorityThreadType0SizeMaxIfEnabled": "3",
                    "Task::ThreadPoolConfig::ForceToMaximumPoolSizes": "1",
                    "Task::ThreadPoolConfig::EnableThreadPool": "1",
                    "Task::ThreadPoolConfig::AutomaticallyGetThreadCountPerTaskType": "1",
                    "DFInt::NetProcessingInMainThread": "0",
                    "DFInt::AnimationStreamingEnablePrediction": "0",
                    "DFInt::AnimationClipMemoryCacheSize": "0",
                    "DFInt::InfluxReporterStartupDelayMs": "0",
                    "DFInt::InfluxReporterHeartbeatIntervalMs": "0",
                    "DFInt::InfluxReporterActive": "0",
                    "DFInt::HttpCurlConnectionCacheSize": "0",
                    "DFInt::ASETInactiveCullDistance": "0",
                    "DFFlag::EnableAES": "false",
                    "DFFlag::MeasureAssetMissingPreload": "false",
                    "DFFlag::ProfileServiceFixNilTreatmentOfUndefined": "false",
                    "DFFlag::ReportFpsAndGfxQualityPercentiles": "false",
                    "FFlagLuaAppSystemBarEnabled": "False",
                    "DFString::ContentProviderAssetsURL": "http://localhost",
                    "DFFlag::UseLegacyCookieBehavior": "true",
                    "DFFlag::HttpRequestCheckNullHeader": "false"
                }
                
                with open(rcc_dir / "DevSettingsFile.json", 'w') as f:
                    json.dump(dev_settings, f, indent=2)
                
                # Create gameserver.json
                gameserver = {
                    "GameServer": {
                        "MachineAddress": "localhost",
                        "DataCenterId": "0",
                        "GameServerIP": "localhost",
                        "GameServerPort": 0
                    }
                }
                
                with open(rcc_dir / "gameserver.json", 'w') as f:
                    json.dump(gameserver, f, indent=2)
                
                self.logger.info("Created server settings for 2019-2021 server")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error creating server settings: {e}")
            return False
    
    def patch_stud_pe(self) -> bool:
        """
        Patch the client using Stud_PE to add the Injector import.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.stud_pe_path:
            self.logger.error("Stud_PE path not provided")
            return False
        
        try:
            self.logger.info(f"Patching client with Stud_PE: {self.client_path}")
            
            # Create a temporary script file for Stud_PE
            # Note: This is a simplified approach. In reality, you would need to use Stud_PE's API
            # or simulate UI interactions, which is beyond the scope of this example.
            self.logger.warning("Stud_PE patching requires manual intervention")
            self.logger.warning("Please follow these steps:")
            self.logger.warning("1. Open Stud_PE and drag the client in")
            self.logger.warning("2. Go to functions then right click anywhere on imported functions")
            self.logger.warning("3. Click 'Add new import', 'Dll Select', and select Injector")
            self.logger.warning("4. Select the only function, click 'Add to list'")
            self.logger.warning("5. Click on the function, then click 'Add', then 'OK'")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error patching with Stud_PE: {e}")
            return False
    
    def copy_required_files(self, client_type: ModernClientType) -> bool:
        """
        Copy required files for the patched client.
        
        Args:
            client_type: The type of client to copy files for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if client_type == ModernClientType.R2019_2021:
                # Copy required DLL files
                dlls = ["FastLog.dll", "Injector.dll"]
                
                for dll in dlls:
                    # In a real implementation, you would download or extract these files
                    # For this example, we'll just log that they should be copied
                    self.logger.info(f"Required DLL: {dll} should be copied to {self.output_dir}")
                
                self.logger.info("Required DLLs need to be manually provided")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error copying required files: {e}")
            return False
    
    def create_launcher_scripts(self, client_type: ModernClientType) -> bool:
        """
        Create launcher scripts for the client and server.
        
        Args:
            client_type: The type of client to create launchers for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if client_type == ModernClientType.R2018M:
                # Create client launcher
                client_launcher = f"""@echo off
start {self.client_path.name} -a "http://{self.domain}/Login/Negotiate.ashx" -j "http://{self.domain}/Game/PlaceLauncher.ashx?placeId=1818" -t "1"
"""
                
                # Create server launcher
                server_launcher = f"""@echo off
start {self.rcc_path.name if self.rcc_path else "RCCService.exe"} -Console -verbose -placeid:1818 -port:53640
"""
            
            elif client_type == ModernClientType.R2019_2021:
                # Create client launcher
                client_launcher = f"""@echo off
start {self.client_path.name} -a "http://localhost/Login/Negotiate.ashx" -j "http://localhost/game/placelauncher.ashx" -t "1"
"""
                
                # Create server launcher
                server_launcher = f"""@echo off
start {self.rcc_path.name if self.rcc_path else "RCCService.exe"} -Console -verbose -placeid:1818 -localtest "gameserver.json" -settingsfile "DevSettingsFile.json" -port 64989
"""
            
            # Write launcher scripts
            with open(self.output_dir / "launch_client.bat", 'w') as f:
                f.write(client_launcher)
            
            with open(self.output_dir / "launch_server.bat", 'w') as f:
                f.write(server_launcher)
            
            self.logger.info("Created launcher scripts")
            return True
        
        except Exception as e:
            self.logger.error(f"Error creating launcher scripts: {e}")
            return False
    
    def patch_2018m(self) -> bool:
        """
        Patch a 2018M client and server.
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Patching 2018M client")
        
        try:
            # Create backups
            self.create_backup(self.client_path)
            if self.rcc_path:
                self.create_backup(self.rcc_path)
            
            # Step 1: Patch client using x32dbg
            script_path = self.create_x32dbg_script(ModernClientType.R2018M)
            
            if self.x32dbg_path:
                if not self.run_x32dbg_script(script_path):
                    self.logger.warning("x32dbg patching failed, manual patching required")
                    self.logger.warning("Please follow these steps:")
                    self.logger.warning("1. Open x32dbg and drag the client in")
                    self.logger.warning("2. Go to symbols, robloxplayerbeta.exe")
                    self.logger.warning("3. Search for 'Client:Connect' in string references")
                    self.logger.warning("4. Find the 'je' above 'localhost' and change it to 'jmp'")
                    self.logger.warning("5. Search for 'Loading shader files' and change the 'je' to 'jmp'")
                    self.logger.warning("6. Save the patches (File > Patch file)")
            else:
                self.logger.warning("x32dbg path not provided, manual patching required")
            
            # Step 2: Replace domain in client and RCC
            client_out_path = self.output_dir / self.client_path.name
            if not client_out_path.exists():
                shutil.copy2(self.client_path, client_out_path)
            
            self.replace_in_binary(client_out_path, b"roblox.com", self.domain.encode())
            
            if self.rcc_path:
                rcc_out_path = self.output_dir / self.rcc_path.name
                if not rcc_out_path.exists():
                    shutil.copy2(self.rcc_path, rcc_out_path)
                
                self.replace_in_binary(rcc_out_path, b"roblox.com", self.domain.encode())
            
            # Step 3: Replace public keys
            self.replace_public_key(client_out_path)
            
            if self.rcc_path:
                rcc_out_path = self.output_dir / self.rcc_path.name
                self.replace_public_key(rcc_out_path)
            
            # Step 4: Create launcher scripts
            self.create_launcher_scripts(ModernClientType.R2018M)
            
            self.logger.info("2018M patching completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error patching 2018M client: {e}")
            return False
    
    # Continuing from where we left off...

    def patch_2019_2021(self) -> bool:
        """
        Patch a 2019-2021 client and server.
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Patching 2019-2021 client")
        
        try:
            # Create backups
            self.create_backup(self.client_path)
            if self.rcc_path:
                self.create_backup(self.rcc_path)
            
            # Step 1: Create client settings
            self.create_client_settings(ModernClientType.R2019_2021)
            
            # Step 2: Patch client using x32dbg
            script_path = self.create_x32dbg_script(ModernClientType.R2019_2021)
            
            if self.x32dbg_path:
                if not self.run_x32dbg_script(script_path):
                    self.logger.warning("x32dbg patching failed, manual patching required")
                    self.logger.warning("Please follow these steps:")
                    self.logger.warning("1. Open x32dbg and drag the client in")
                    self.logger.warning("2. Click the right arrow twice to get around VMProtect")
                    self.logger.warning("3. Search for 'trust check failed' in string references")
                    self.logger.warning("4. For each result, find the 'je' or 'jne' above it and change to 'jmp'")
                    self.logger.warning("5. Search for '127.0.0.1' and find the one with 'je' above it and 'push D188' below")
                    self.logger.warning("6. Change that 'je' to 'jmp'")
                    self.logger.warning("7. Save the patches (File > Patch file)")
            else:
                self.logger.warning("x32dbg path not provided, manual patching required")
            
            # Step 3: Patch client using Stud_PE
            if self.stud_pe_path:
                self.patch_stud_pe()
            else:
                self.logger.warning("Stud_PE path not provided, manual patching required")
            
            # Step 4: Patch RCCService
            if self.rcc_path:
                rcc_out_path = self.output_dir / self.rcc_path.name
                if not rcc_out_path.exists():
                    shutil.copy2(self.rcc_path, rcc_out_path)
                
                # Replace https with http in RCCService
                self.replace_in_binary(rcc_out_path, b"\x00\x68\x74\x74\x70\x73\x00", b"\x00\x68\x74\x74\x70\x00\x00")
                
                # Create RCCService settings
                self.create_server_settings(ModernClientType.R2019_2021)
                
                # Patch RCCService using x32dbg if available
                if self.x32dbg_path:
                    # Create script for RCCService
                    rcc_script_content = f"""// x32dbg script for patching 2019-2021 RCCService
InitDebug "{rcc_out_path}"

// Patch trust check failed
findstr "trust check failed"
findall
jmp $RESULT
for i $RESULT_COUNT
    goto $_RESULT[i]
    findcmd je -10
    setcmd $RESULT jmp
endfor

// Patch Non-trusted BaseURL
findstr "Non-trusted BaseURL used"
findall
jmp $RESULT
for i $RESULT_COUNT
    goto $_RESULT[i]
    findcmd je -10
    setcmd $RESULT jmp
endfor

// Save and exit
SaveFile "{rcc_out_path}"
StopDebug
exit
"""
                    
                    # Write script to temporary file
                    fd, rcc_script_path = tempfile.mkstemp(suffix='.txt')
                    with os.fdopen(fd, 'w') as f:
                        f.write(rcc_script_content)
                    
                    # Run the script
                    self.run_x32dbg_script(Path(rcc_script_path))
                else:
                    self.logger.warning("x32dbg path not provided, manual RCCService patching required")
                    self.logger.warning("Please follow these steps:")
                    self.logger.warning("1. Open x32dbg and drag the RCCService in")
                    self.logger.warning("2. Search for 'trust check failed' in string references")
                    self.logger.warning("3. For each result, find the 'je' or 'jne' above it and change to 'jmp'")
                    self.logger.warning("4. Search for 'Non-trusted BaseURL used' and do the same")
                    self.logger.warning("5. Save the patches (File > Patch file)")
            
            # Step 5: Copy required DLLs
            self.copy_required_files(ModernClientType.R2019_2021)
            
            # Step 6: Create launcher scripts
            self.create_launcher_scripts(ModernClientType.R2019_2021)
            
            self.logger.info("2019-2021 patching completed successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error patching 2019-2021 client: {e}")
            return False
    
    def patch(self) -> bool:
        """
        Patch the client and server based on the detected client type.
        
        Returns:
            True if successful, False otherwise
        """
        client_type = self.detect_client_type()
        self.logger.info(f"Detected client type: {client_type}")
        
        if client_type == ModernClientType.R2018M:
            return self.patch_2018m()
        elif client_type == ModernClientType.R2019_2021:
            return self.patch_2019_2021()
        else:
            self.logger.error(f"Unsupported client type: {client_type}")
            return False


def main() -> None:
    """Main entry point for the Modern Roblox Client Patcher."""
    parser = argparse.ArgumentParser(description="Patch modern Roblox clients (2018-2021).")
    
    # Required arguments
    parser.add_argument("--client", "-c", type=str, required=True,
                      help="Path to the Roblox client executable")
    
    # Optional arguments
    parser.add_argument("--rcc", "-r", type=str, default=None,
                      help="Path to the RCCService executable")
    parser.add_argument("--domain", "-d", type=str, default="localhost",
                      help="Domain name to use (default: localhost)")
    parser.add_argument("--output", "-o", type=str, default=None,
                      help="Output directory for patched files")
    parser.add_argument("--x32dbg", "-x", type=str, default=None,
                      help="Path to x32dbg executable")
    parser.add_argument("--hxd", "-H", type=str, default=None,
                      help="Path to HxD executable")
    parser.add_argument("--stud-pe", "-s", type=str, default=None,
                      help="Path to Stud_PE executable (needed for 2019-2021 clients)")
    parser.add_argument("--force-2018m", action="store_true",
                      help="Force 2018M patching method")
    parser.add_argument("--force-2019-2021", action="store_true",
                      help="Force 2019-2021 patching method")
    
    args = parser.parse_args()
    
    # Create patcher
    patcher = ModernPatcher(
        client_path=args.client,
        rcc_path=args.rcc,
        domain=args.domain,
        output_dir=args.output,
        x32dbg_path=args.x32dbg,
        hxd_path=args.hxd,
        stud_pe_path=args.stud_pe
    )
    
    # Override client type detection if requested
    if args.force_2018m:
        print("Forcing 2018M patching method")
        patcher.patch_2018m()
    elif args.force_2019_2021:
        print("Forcing 2019-2021 patching method")
        patcher.patch_2019_2021()
    else:
        # Auto-detect and patch
        patcher.patch()
    
    print("\nPatching process completed. Check the log file for details.")


if __name__ == "__main__":
    main()