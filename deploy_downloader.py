#!/usr/bin/env python3
"""
Roblox Deploy Downloader

A utility script for downloading historical Roblox clients using version hashes
from DeployHistory.txt and the RDD (Roblox Deploy Downloader) tool.
"""
import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import requests


class DeployDownloader:
    """Utility for downloading historical Roblox clients."""
    
    DEPLOY_HISTORY_URL = "https://setup.rbxcdn.com/DeployHistory.txt"
    RDD_GITHUB_URL = "https://github.com/latte-soft/rdd"
    RDD_RELEASES_URL = "https://api.github.com/repos/latte-soft/rdd/releases/latest"
    
    def __init__(self, download_dir: Union[str, Path], rdd_path: Optional[Union[str, Path]] = None):
        """
        Initialize the deploy downloader.
        
        Args:
            download_dir: Directory to save downloaded clients
            rdd_path: Path to the RDD executable (will download if not provided)
        """
        self.download_dir = Path(download_dir)
        self.rdd_path = Path(rdd_path) if rdd_path else None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging for the application."""
        log_file = self.download_dir / "deploy_downloader.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def download_deploy_history(self) -> List[Dict[str, str]]:
        """
        Download and parse the deploy history file.
        
        Returns:
            List of dictionaries containing version info
        """
        self.logger.info(f"Downloading deploy history from {self.DEPLOY_HISTORY_URL}")
        
        try:
            response = requests.get(self.DEPLOY_HISTORY_URL, timeout=30)
            response.raise_for_status()
            
            # Parse the file
            versions = []
            for line in response.text.strip().split('\n'):
                parts = line.split(',')
                if len(parts) >= 2:
                    # Format: version-hash,YYYY-MM-DD HH:MM:SS
                    version_hash = parts[0].strip()
                    timestamp = parts[1].strip()
                    
                    # Extract the version number if possible
                    version_match = re.search(r'version-([0-9a-f]+)', version_hash)
                    version_id = version_match.group(1) if version_match else None
                    
                    versions.append({
                        'hash': version_hash,
                        'timestamp': timestamp,
                        'version_id': version_id,
                        'year': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').year
                    })
            
            self.logger.info(f"Found {len(versions)} versions in deploy history")
            return versions
        
        except Exception as e:
            self.logger.error(f"Error downloading deploy history: {e}")
            return []
    
    def ensure_rdd_available(self) -> bool:
        """
        Ensure RDD is available, downloading if necessary.
        
        Returns:
            True if RDD is available, False otherwise
        """
        if self.rdd_path and self.rdd_path.exists():
            self.logger.info(f"Using existing RDD at {self.rdd_path}")
            return True
        
        self.logger.info("RDD not found, downloading latest version")
        
        try:
            # Get latest release info
            response = requests.get(self.RDD_RELEASES_URL)
            response.raise_for_status()
            release_info = response.json()
            
            # Find the appropriate asset for the current platform
            platform = sys.platform
            asset_name = None
            
            if platform.startswith('win'):
                asset_name = "rdd-windows.exe"
            elif platform.startswith('darwin'):
                asset_name = "rdd-macos"
            elif platform.startswith('linux'):
                asset_name = "rdd-linux"
            else:
                self.logger.error(f"Unsupported platform: {platform}")
                return False
            
            # Find the download URL
            download_url = None
            for asset in release_info.get('assets', []):
                if asset['name'] == asset_name:
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                self.logger.error(f"Could not find {asset_name} in the latest release")
                return False
            
            # Download the executable
            self.rdd_path = self.download_dir / asset_name
            self.logger.info(f"Downloading RDD from {download_url} to {self.rdd_path}")
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(self.rdd_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Make executable on Unix systems
            if not platform.startswith('win'):
                self.rdd_path.chmod(self.rdd_path.stat().st_mode | 0o111)
            
            self.logger.info(f"Downloaded RDD to {self.rdd_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error downloading RDD: {e}")
            return False
    
    def download_client(self, version_hash: str, client_type: str = "WindowsPlayer") -> Optional[str]:
        """
        Download a specific client version.
        
        Args:
            version_hash: The version hash to download
            client_type: The type of client to download (WindowsPlayer, WindowsStudio, etc.)
            
        Returns:
            Path to the downloaded client, or None if download failed
        """
        if not self.ensure_rdd_available():
            return None
        
        # Determine output directory
        output_dir = self.download_dir / version_hash
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Run RDD to download the client
            self.logger.info(f"Downloading {client_type} for {version_hash}")
            
            cmd = [
                str(self.rdd_path),
                "download",
                version_hash,
                client_type,
                "-o", str(output_dir)
            ]
            
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find the downloaded file in the output directory
            for file in output_dir.glob("*"):
                if file.is_file() and file.suffix.lower() == '.exe':
                    self.logger.info(f"Successfully downloaded {client_type} to {file}")
                    return str(file)
            
            self.logger.warning(f"Could not find downloaded client in {output_dir}")
            self.logger.debug(f"RDD stdout: {process.stdout}")
            return None
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running RDD: {e}")
            self.logger.error(f"stdout: {e.stdout}")
            self.logger.error(f"stderr: {e.stderr}")
            return None
        
        except Exception as e:
            self.logger.error(f"Error downloading client: {e}")
            return None
    
    def download_by_year(self, year: int, client_types: List[str] = None, max_versions: int = 1) -> Dict[str, str]:
        """
        Download clients from a specific year.
        
        Args:
            year: The year to download clients from
            client_types: Types of clients to download (defaults to WindowsPlayer)
            max_versions: Maximum number of versions to download per year
            
        Returns:
            Dictionary mapping client types to download paths
        """
        if client_types is None:
            client_types = ["WindowsPlayer"]
        
        versions = self.download_deploy_history()
        
        # Filter versions by year
        year_versions = [v for v in versions if v.get('year') == year]
        
        if not year_versions:
            self.logger.warning(f"No versions found for year {year}")
            return {}
        
        # Sort by timestamp (newest first) and take max_versions
        year_versions.sort(key=lambda v: v['timestamp'], reverse=True)
        selected_versions = year_versions[:max_versions]
        
        self.logger.info(f"Selected {len(selected_versions)} versions from {year}")
        
        results = {}
        for version in selected_versions:
            version_hash = version['hash']
            version_id = version.get('version_id', 'unknown')
            
            for client_type in client_types:
                self.logger.info(f"Downloading {client_type} for {version_hash} (Year: {year})")
                result = self.download_client(version_hash, client_type)
                
                if result:
                    key = f"{client_type}_{year}_{version_id}"
                    results[key] = result
        
        return results
    
    def download_range(self, start_year: int, end_year: int, client_types: List[str] = None, max_versions_per_year: int = 1) -> Dict[str, str]:
        """
        Download clients from a range of years.
        
        Args:
            start_year: The starting year
            end_year: The ending year
            client_types: Types of clients to download (defaults to WindowsPlayer)
            max_versions_per_year: Maximum number of versions to download per year
            
        Returns:
            Dictionary mapping client types to download paths
        """
        if client_types is None:
            client_types = ["WindowsPlayer"]
        
        results = {}
        for year in range(start_year, end_year + 1):
            year_results = self.download_by_year(year, client_types, max_versions_per_year)
            results.update(year_results)
        
        return results
    
    def download_specific_versions(self, version_hashes: List[str], client_types: List[str] = None) -> Dict[str, str]:
        """
        Download specific client versions.
        
        Args:
            version_hashes: List of version hashes to download
            client_types: Types of clients to download (defaults to WindowsPlayer)
            
        Returns:
            Dictionary mapping client types to download paths
        """
        if client_types is None:
            client_types = ["WindowsPlayer"]
        
        results = {}
        for version_hash in version_hashes:
            for client_type in client_types:
                self.logger.info(f"Downloading {client_type} for {version_hash}")
                result = self.download_client(version_hash, client_type)
                
                if result:
                    key = f"{client_type}_{version_hash}"
                    results[key] = result
        
        return results


def main() -> None:
    """Main entry point for the Roblox Deploy Downloader."""
    parser = argparse.ArgumentParser(description="Download historical Roblox clients.")
    
    # Main options
    parser.add_argument("--download-dir", "-d", type=str, default="./roblox_clients",
                      help="Directory to save downloaded clients (default: ./roblox_clients)")
    parser.add_argument("--rdd-path", "-r", type=str, default=None,
                      help="Path to RDD executable (will download if not provided)")
    
    # Download options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--year", "-y", type=int,
                     help="Download clients from a specific year")
    group.add_argument("--range", "-R", type=str,
                     help="Download clients from a range of years (format: START-END)")
    group.add_argument("--version", "-v", action="append",
                     help="Download specific version hash (can be used multiple times)")
    group.add_argument("--list-years", "-l", action="store_true",
                     help="List available years in deploy history")
    
    # Client types
    parser.add_argument("--client-types", "-c", type=str, default="WindowsPlayer",
                      help="Comma-separated list of client types to download (default: WindowsPlayer)")
    
    # Other options
    parser.add_argument("--max-versions", "-m", type=int, default=1,
                      help="Maximum number of versions to download per year (default: 1)")
    
    args = parser.parse_args()
    
    # Parse client types
    client_types = args.client_types.split(",")
    
    # Create downloader
    downloader = DeployDownloader(args.download_dir, args.rdd_path)
    
    # Handle different download options
    if args.list_years:
        versions = downloader.download_deploy_history()
        years = set(v.get('year') for v in versions if v.get('year'))
        years = sorted(list(years))
        
        print("Available years in deploy history:")
        for year in years:
            count = sum(1 for v in versions if v.get('year') == year)
            print(f"  {year}: {count} versions")
    
    elif args.year:
        results = downloader.download_by_year(args.year, client_types, args.max_versions)
        
        if results:
            print(f"\nSuccessfully downloaded {len(results)} clients:")
            for client_name, path in results.items():
                print(f"  {client_name}: {path}")
        else:
            print(f"No clients were downloaded for year {args.year}")
    
    elif args.range:
        try:
            start_year, end_year = map(int, args.range.split("-"))
            
            if start_year > end_year:
                start_year, end_year = end_year, start_year
            
            results = downloader.download_range(start_year, end_year, client_types, args.max_versions)
            
            if results:
                print(f"\nSuccessfully downloaded {len(results)} clients:")
                for client_name, path in results.items():
                    print(f"  {client_name}: {path}")
            else:
                print(f"No clients were downloaded for years {start_year}-{end_year}")
        
        except ValueError:
            print(f"Invalid range format: {args.range}. Expected format: START-END (e.g., 2008-2012)")
    
    elif args.version:
        results = downloader.download_specific_versions(args.version, client_types)
        
        if results:
            print(f"\nSuccessfully downloaded {len(results)} clients:")
            for client_name, path in results.items():
                print(f"  {client_name}: {path}")
        else:
            print("No clients were downloaded")


if __name__ == "__main__":
    main()