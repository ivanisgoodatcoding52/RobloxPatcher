#!/usr/bin/env python3
"""
Roblox Deploy Downloader - Standalone UI

A graphical tool to download historical Roblox clients.
"""
import logging
import os
import sys
import tkinter as tk
import threading
import re
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
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
                    try:
                        # Format: version-hash,YYYY-MM-DD HH:MM:SS
                        version_hash = parts[0].strip()
                        timestamp = parts[1].strip()
                        
                        # Skip any header or malformed lines
                        if version_hash.startswith("file") or ":" not in timestamp:
                            continue
                        
                        # Extract the version number if possible
                        version_match = re.search(r'version-([0-9a-f]+)', version_hash)
                        version_id = version_match.group(1) if version_match else None
                        
                        # Parse the timestamp
                        try:
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            year = dt.year
                        except ValueError:
                            # If timestamp parsing fails, try to extract year from a different format
                            year_match = re.search(r'20\d\d', timestamp)
                            year = int(year_match.group(0)) if year_match else None
                        
                        if year:
                            versions.append({
                                'hash': version_hash,
                                'timestamp': timestamp,
                                'version_id': version_id,
                                'year': year
                            })
                    except Exception as e:
                        self.logger.debug(f"Skipping malformed line: {line} (Error: {e})")
                        continue
            
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


class DeployDownloaderApp:
    """Main application for the Deploy Downloader UI."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Roblox Deploy Downloader")
        self.root.geometry("800x700")  # Increased height for the new direct download section
        
        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create the UI
        self._setup_ui()
    
    def _setup_logging(self):
        """Set up logging for the application."""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "deploy_downloader.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Roblox Deploy Downloader", 
            font=("TkDefaultFont", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Create notebook with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        downloader_tab = ttk.Frame(notebook)
        log_tab = ttk.Frame(notebook)
        
        notebook.add(downloader_tab, text="Downloader")
        notebook.add(log_tab, text="Log")
        
        # Downloader tab content
        self._setup_downloader_tab(downloader_tab)
        
        # Log tab content
        self._setup_log_tab(log_tab)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_downloader_tab(self, parent):
        """
        Set up the downloader tab content.
        
        Args:
            parent: The parent widget
        """
        downloader_frame = ttk.Frame(parent, padding="10")
        downloader_frame.pack(fill=tk.BOTH, expand=True)
        
        # Download method selection
        ttk.Label(downloader_frame, text="Download Method:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.method_var = tk.StringVar(value="year")
        method_frame = ttk.Frame(downloader_frame)
        method_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            method_frame, 
            text="By Year", 
            variable=self.method_var, 
            value="year",
            command=self._update_method_ui
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            method_frame, 
            text="Year Range", 
            variable=self.method_var, 
            value="range",
            command=self._update_method_ui
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            method_frame, 
            text="Specific Version", 
            variable=self.method_var, 
            value="version",
            command=self._update_method_ui
        ).pack(side=tk.LEFT)
        
        # Year selection frame
        self.year_frame = ttk.LabelFrame(downloader_frame, text="Year Selection")
        self.year_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Single year
        self.single_year_frame = ttk.Frame(self.year_frame)
        ttk.Label(self.single_year_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.year_var = tk.StringVar(value="2016")
        years = [str(y) for y in range(2007, 2023)]
        ttk.Combobox(
            self.single_year_frame, 
            textvariable=self.year_var, 
            values=years, 
            width=6
        ).pack(side=tk.LEFT)
        
        # Year range
        self.year_range_frame = ttk.Frame(self.year_frame)
        ttk.Label(self.year_range_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_year_var = tk.StringVar(value="2010")
        ttk.Combobox(
            self.year_range_frame, 
            textvariable=self.start_year_var, 
            values=years, 
            width=6
        ).pack(side=tk.LEFT)
        
        ttk.Label(self.year_range_frame, text="To:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.end_year_var = tk.StringVar(value="2016")
        ttk.Combobox(
            self.year_range_frame, 
            textvariable=self.end_year_var, 
            values=years, 
            width=6
        ).pack(side=tk.LEFT)
        
        # Version hash
        self.version_frame = ttk.Frame(self.year_frame)
        ttk.Label(self.version_frame, text="Version Hash:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.version_var = tk.StringVar()
        ttk.Entry(
            self.version_frame, 
            textvariable=self.version_var, 
            width=40
        ).pack(side=tk.LEFT)
        
        # Version format hint
        ttk.Label(
            self.version_frame, 
            text="Example: version-abcdef1234567890",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Direct hash download
        direct_hash_frame = ttk.LabelFrame(downloader_frame, text="Quick Version Hash Download")
        direct_hash_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        direct_hash_input_frame = ttk.Frame(direct_hash_frame)
        direct_hash_input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Label(direct_hash_input_frame, text="Version Hash:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.direct_hash_var = tk.StringVar()
        ttk.Entry(
            direct_hash_input_frame, 
            textvariable=self.direct_hash_var, 
            width=40
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            direct_hash_input_frame, 
            text="Download This Hash", 
            command=self._download_direct_hash
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Client types selection
        ttk.Label(downloader_frame, text="Client Types:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        client_types_frame = ttk.Frame(downloader_frame)
        client_types_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        self.client_types = {
            "WindowsPlayer": tk.BooleanVar(value=True),
            "WindowsStudio": tk.BooleanVar(value=False),
            "WindowsBootstrapper": tk.BooleanVar(value=False),
            "RCCService": tk.BooleanVar(value=False)
        }
        
        for i, (client_type, var) in enumerate(self.client_types.items()):
            ttk.Checkbutton(
                client_types_frame, 
                text=client_type, 
                variable=var
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 10))
        
        # Max versions per year
        ttk.Label(downloader_frame, text="Max Versions Per Year:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.max_versions_var = tk.IntVar(value=1)
        ttk.Spinbox(
            downloader_frame, 
            from_=1, 
            to=10, 
            textvariable=self.max_versions_var, 
            width=5
        ).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Download directory
        ttk.Label(downloader_frame, text="Download Directory:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        download_dir_frame = ttk.Frame(downloader_frame)
        download_dir_frame.grid(row=5, column=1, sticky=tk.EW, pady=5)
        
        self.download_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "RobloxClients"))
        ttk.Entry(
            download_dir_frame, 
            textvariable=self.download_dir_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            download_dir_frame, 
            text="Browse", 
            command=self._browse_download_dir
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # RDD path (optional)
        ttk.Label(downloader_frame, text="RDD Path (optional):").grid(row=6, column=0, sticky=tk.W, pady=5)
        
        rdd_frame = ttk.Frame(downloader_frame)
        rdd_frame.grid(row=6, column=1, sticky=tk.EW, pady=5)
        
        self.rdd_path_var = tk.StringVar()
        ttk.Entry(
            rdd_frame, 
            textvariable=self.rdd_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            rdd_frame, 
            text="Browse", 
            command=self._browse_rdd_path
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Info and download button
        ttk.Label(
            downloader_frame, 
            text="RDD will be downloaded automatically if not provided",
            foreground="gray"
        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        self.download_button = ttk.Button(
            downloader_frame, 
            text="Download Selected Clients", 
            command=self._download_clients
        )
        self.download_button.grid(row=8, column=0, columnspan=2, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(
            downloader_frame, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='determinate',
            variable=self.progress_var
        )
        progress_bar.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Make the downloader frame columns expand properly
        downloader_frame.columnconfigure(1, weight=1)
        
        # Show the appropriate frame based on the method
        self._update_method_ui()
    
    def _setup_log_tab(self, parent):
        """
        Set up the log tab content.
        
        Args:
            parent: The parent widget
        """
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget with scrollbar
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, width=80, height=20)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(parent, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="Clear Log", 
            command=self._clear_log
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Save Log", 
            command=self._save_log
        ).pack(side=tk.LEFT, padx=5)
    
    def _update_method_ui(self):
        """Update the UI based on the selected download method."""
        method = self.method_var.get()
        
        # Hide all frames first
        for frame in [self.single_year_frame, self.year_range_frame, self.version_frame]:
            frame.pack_forget()
        
        # Show the appropriate frame
        if method == "year":
            self.single_year_frame.pack(padx=10, pady=10, fill=tk.X)
        elif method == "range":
            self.year_range_frame.pack(padx=10, pady=10, fill=tk.X)
        elif method == "version":
            self.version_frame.pack(padx=10, pady=10, fill=tk.X)
    
    def _browse_download_dir(self):
        """Open directory dialog to select download directory."""
        directory = filedialog.askdirectory(
            title="Select Download Directory"
        )
        
        if directory:
            self.download_dir_var.set(directory)
    
    def _browse_rdd_path(self):
        """Open file dialog to select RDD executable."""
        file_path = filedialog.askopenfilename(
            title="Select RDD Executable",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.rdd_path_var.set(file_path)
    
    def _download_direct_hash(self):
        """Download a client directly from the hash input field."""
        # Get the version hash
        version_hash = self.direct_hash_var.get()
        if not version_hash:
            messagebox.showwarning("No Version Hash", "Please enter a version hash.")
            return
        
        # Ensure it has the 'version-' prefix
        if not version_hash.startswith("version-"):
            version_hash = f"version-{version_hash}"
            self.direct_hash_var.set(version_hash)
        
        # Get selected client types
        client_types = [ct for ct, var in self.client_types.items() if var.get()]
        if not client_types:
            messagebox.showwarning("No Client Types", "Please select at least one client type to download.")
            return
        
        # Get download directory
        download_dir = self.download_dir_var.get()
        if not download_dir:
            messagebox.showwarning("No Download Directory", "Please specify a download directory.")
            return
        
        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Get RDD path (optional)
        rdd_path = self.rdd_path_var.get() or None
        
        # Create DeployDownloader
        try:
            downloader = DeployDownloader(download_dir, rdd_path)
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Could not initialize downloader: {str(e)}")
            self._add_to_log(f"Error: {str(e)}")
            return
        
        # Disable download button
        self.download_button.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set(f"Downloading {version_hash}...")
        
        # Start downloading in a background thread
        thread = threading.Thread(target=self._download_direct_hash_thread, args=(
            downloader, version_hash, client_types
        ))
        thread.daemon = True
        thread.start()
    
    def _download_direct_hash_thread(self, downloader, version_hash, client_types):
        """
        Thread to download a specific version hash.
        
        Args:
            downloader: The DeployDownloader instance
            version_hash: The version hash to download
            client_types: List of client types to download
        """
        try:
            self._add_to_log(f"Downloading specific version: {version_hash}")
            
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(20))
            
            # Download the version
            results = downloader.download_specific_versions([version_hash], client_types)
            
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(100))
            
            # Show results
            if results:
                self.root.after(0, lambda: self.status_var.set(f"Downloaded {len(results)} clients successfully"))
                
                result_text = "Successfully downloaded clients:\n\n"
                for client_name, path in results.items():
                    result_text += f"{client_name}: {path}\n"
                    self._add_to_log(f"Downloaded: {client_name} to {path}")
                
                self.root.after(0, lambda: messagebox.showinfo("Download Complete", result_text))
            else:
                self.root.after(0, lambda: self.status_var.set("No clients were downloaded"))
                self._add_to_log(f"No clients were downloaded for version {version_hash}")
                self.root.after(0, lambda: messagebox.showinfo("Download Complete", f"No clients were downloaded for version {version_hash}."))
        
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self._add_to_log(f"Error downloading version {version_hash}: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download faile