"""
Main window for the Roblox Revival Creator GUI.
"""
import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional

from config import AppConfig, ClientType, PatchConfig, PatchType
from patchers import (BlockingPatcher, HtmlServicePatcher, InvalidRequestPatcher,
                    PublicKeyPatcher, RatnetKeyPatcher, TrustCheckPatcher,
                    WebsitePatcher)
from ui.patch_panel import PatchPanel
from ui.theme_manager import ThemeManager


class MainWindow:
    """Main application window for the Roblox Revival Creator."""
    
    def __init__(self, root: tk.Tk, app_config: AppConfig):
        """
        Initialize the main window.
        
        Args:
            root: The root Tkinter window
            app_config: Application configuration
        """
        self.root = root
        self.app_config = app_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_config = PatchConfig()
        self.theme_manager = ThemeManager(self.root, self.app_config.dark_mode)
        
        self._setup_ui()
        self._create_bindings()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add menu bar
        self._setup_menu()
        
        # Add notebook for different sections
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.patch_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.patch_tab, text="Patches")
        self.notebook.add(self.log_tab, text="Log")
        
        # Setup tab content
        self._setup_setup_tab()
        
        # Create patch panels
        self.patch_panel = PatchPanel(self.patch_tab, self.current_config)
        
        # Log tab content
        self._setup_log_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_menu(self) -> None:
        """Set up the application menu bar."""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Config", command=self._new_config)
        file_menu.add_command(label="Open Config...", command=self._open_config)
        file_menu.add_command(label="Save Config", command=self._save_config)
        file_menu.add_command(label="Save Config As...", command=self._save_config_as)
        file_menu.add_separator()
        
        # Recent configs submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        self._update_recent_menu()
        file_menu.add_cascade(label="Recent Configs", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="RbxSigTools", command=self._open_rbxsigtools)
        tools_menu.add_command(label="View Backup Files", command=self._view_backups)
        tools_menu.add_command(label="Restore From Backup", command=self._restore_backup)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_command(label="About", command=self._show_about)
        
        # Options menu
        options_menu = tk.Menu(menu_bar, tearoff=0)
        self.dark_mode_var = tk.BooleanVar(value=self.app_config.dark_mode)
        options_menu.add_checkbutton(
            label="Dark Mode", 
            variable=self.dark_mode_var,
            command=self._toggle_dark_mode
        )
        
        # Add menus to menubar
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        menu_bar.add_cascade(label="Options", menu=options_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def _setup_setup_tab(self) -> None:
        """Set up the content for the Setup tab."""
        setup_frame = ttk.Frame(self.setup_tab, padding="10")
        setup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Client file selection
        ttk.Label(setup_frame, text="Client File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        client_frame = ttk.Frame(setup_frame)
        client_frame.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        self.client_path_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_path_var, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(client_frame, text="Browse", command=self._browse_client).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Client type selection
        ttk.Label(setup_frame, text="Client Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.client_type_var = tk.StringVar(value=str(ClientType.PLAYER))
        client_types = [str(ct) for ct in ClientType]
        client_type_combo = ttk.Combobox(setup_frame, textvariable=self.client_type_var, values=client_types, state="readonly")
        client_type_combo.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # Version year
        ttk.Label(setup_frame, text="Version Year:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.version_year_var = tk.IntVar(value=2010)
        year_frame = ttk.Frame(setup_frame)
        year_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        years = list(range(2007, 2018))
        year_combo = ttk.Combobox(year_frame, textvariable=self.version_year_var, values=years, state="readonly", width=10)
        year_combo.pack(side=tk.LEFT)
        
        # Website domain
        ttk.Label(setup_frame, text="Website Domain:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        domain_frame = ttk.Frame(setup_frame)
        domain_frame.grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        self.website_domain_var = tk.StringVar()
        self.domain_entry = ttk.Entry(domain_frame, textvariable=self.website_domain_var, width=15)
        self.domain_entry.pack(side=tk.LEFT)
        
        ttk.Label(domain_frame, text="(must be exactly 10 characters)").pack(side=tk.LEFT, padx=(5, 0))
        
        # RbxSigTools path
        ttk.Label(setup_frame, text="RbxSigTools Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        rbx_frame = ttk.Frame(setup_frame)
        rbx_frame.grid(row=4, column=1, sticky=tk.EW, pady=5)
        
        self.rbxsigtools_path_var = tk.StringVar()
        ttk.Entry(rbx_frame, textvariable=self.rbxsigtools_path_var, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(rbx_frame, text="Browse", command=self._browse_rbxsigtools).pack(side=tk.RIGHT, padx=(5, 0))
        
        # x64dbg path
        ttk.Label(setup_frame, text="x64dbg Path:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        x64dbg_frame = ttk.Frame(setup_frame)
        x64dbg_frame.grid(row=5, column=1, sticky=tk.EW, pady=5)
        
        self.x64dbg_path_var = tk.StringVar()
        ttk.Entry(x64dbg_frame, textvariable=self.x64dbg_path_var, width=50).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(x64dbg_frame, text="Browse", command=self._browse_x64dbg).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Continue button
        button_frame = ttk.Frame(setup_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame, 
            text="Continue to Patches", 
            command=self._continue_to_patches
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Reset Form", 
            command=self._reset_form
        ).pack(side=tk.LEFT, padx=5)
        
        # Make the setup frame columns expand properly
        setup_frame.columnconfigure(1, weight=1)
    
    def _setup_log_tab(self) -> None:
        """Set up the content for the Log tab."""
        log_frame = ttk.Frame(self.log_tab, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget with scrollbar
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(self.log_tab, padding="10")
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
    
    def _create_bindings(self) -> None:
        """Create event bindings for widgets."""
        self.website_domain_var.trace_add("write", self._validate_domain)
        self.client_path_var.trace_add("write", self._update_config_from_ui)
        self.client_type_var.trace_add("write", self._update_config_from_ui)
        self.version_year_var.trace_add("write", self._update_config_from_ui)
        self.website_domain_var.trace_add("write", self._update_config_from_ui)
        self.rbxsigtools_path_var.trace_add("write", self._update_config_from_ui)
        self.x64dbg_path_var.trace_add("write", self._update_config_from_ui)
    
    def _validate_domain(self, *args) -> None:
        """Validate that the domain is exactly 10 characters."""
        domain = self.website_domain_var.get()
        if len(domain) > 10:
            self.website_domain_var.set(domain[:10])
        
        # Update entry color based on domain length
        if len(domain) != 10 and len(domain) > 0:
            self.domain_entry.configure(style="Invalid.TEntry")
        else:
            self.domain_entry.configure(style="TEntry")
    
    def _update_config_from_ui(self, *args) -> None:
        """Update the current config from UI values."""
        try:
            self.current_config.client_path = self.client_path_var.get()
            
            # Update client type
            client_type_str = self.client_type_var.get()
            for ct in ClientType:
                if str(ct) == client_type_str:
                    self.current_config.client_type = ct
                    break
            
            self.current_config.version_year = self.version_year_var.get()
            self.current_config.website_domain = self.website_domain_var.get()
            self.current_config.rbxsigtools_path = self.rbxsigtools_path_var.get()
            self.current_config.x64dbg_path = self.x64dbg_path_var.get()
            
            # Update patch panel if it exists
            if hasattr(self, 'patch_panel'):
                self.patch_panel.update_config(self.current_config)
        except Exception as e:
            self.logger.error(f"Error updating config from UI: {e}")
    
    def _update_ui_from_config(self) -> None:
        """Update UI values from the current config."""
        try:
            self.client_path_var.set(self.current_config.client_path)
            self.client_type_var.set(str(self.current_config.client_type))
            self.version_year_var.set(self.current_config.version_year)
            self.website_domain_var.set(self.current_config.website_domain)
            self.rbxsigtools_path_var.set(self.current_config.rbxsigtools_path)
            self.x64dbg_path_var.set(self.current_config.x64dbg_path)
            
            # Update patch panel if it exists
            if hasattr(self, 'patch_panel'):
                self.patch_panel.update_config(self.current_config)
        except Exception as e:
            self.logger.error(f"Error updating UI from config: {e}")
    
    def _browse_client(self) -> None:
        """Open file dialog to select client file."""
        file_path = filedialog.askopenfilename(
            title="Select Roblox Client",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.client_path_var.set(file_path)
            
            # Try to automatically determine client type from filename
            filename = os.path.basename(file_path).lower()
            if "studio" in filename:
                self.client_type_var.set(str(ClientType.STUDIO))
            elif "rccservice" in filename:
                self.client_type_var.set(str(ClientType.RCC_SERVICE))
            else:
                self.client_type_var.set(str(ClientType.PLAYER))
    
    def _browse_rbxsigtools(self) -> None:
        """Open file dialog to select RbxSigTools directory."""
        directory = filedialog.askdirectory(
            title="Select RbxSigTools Directory"
        )
        
        if directory:
            # Check if KeyGenerator.exe exists in the directory
            if os.path.exists(os.path.join(directory, "KeyGenerator.exe")):
                self.rbxsigtools_path_var.set(directory)
            else:
                messagebox.showwarning(
                    "Invalid Directory", 
                    "KeyGenerator.exe not found in the selected directory."
                )
    
    def _browse_x64dbg(self) -> None:
        """Open file dialog to select x64dbg executable."""
        file_path = filedialog.askopenfilename(
            title="Select x64dbg Executable",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.x64dbg_path_var.set(file_path)
    
    def _continue_to_patches(self) -> None:
        """Validate setup and continue to patches tab."""
        # Basic validation
        if not self.client_path_var.get():
            messagebox.showwarning("Validation Error", "Client file path is required.")
            return
        
        if len(self.website_domain_var.get()) != 10:
            messagebox.showwarning("Validation Error", "Website domain must be exactly 10 characters.")
            return
        
        # Update config and switch to patches tab
        self._update_config_from_ui()
        self.notebook.select(self.patch_tab)
        self.patch_panel.update_config(self.current_config)
    
    def _reset_form(self) -> None:
        """Reset the setup form to default values."""
        self.client_path_var.set("")
        self.client_type_var.set(str(ClientType.PLAYER))
        self.version_year_var.set(2010)
        self.website_domain_var.set("")
        self.rbxsigtools_path_var.set("")
        self.x64dbg_path_var.set("")
    
    def _new_config(self) -> None:
        """Create a new configuration."""
        if messagebox.askyesno("New Config", "Create a new configuration? Any unsaved changes will be lost."):
            self.current_config = PatchConfig()
            self._update_ui_from_config()
            self.notebook.select(self.setup_tab)
    
    def _open_config(self) -> None:
        """Open a configuration file."""
        file_path = filedialog.askopenfilename(
            title="Open Configuration",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self._load_config(file_path)
    
    def _load_config(self, file_path: str) -> None:
        """Load a configuration from a file."""
        try:
            import json
            
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            self.current_config = PatchConfig.from_dict(config_dict)
            self._update_ui_from_config()
            
            # Add to recent configs
            self.app_config.add_recent_config(file_path)
            self._update_recent_menu()
            
            self.status_var.set(f"Loaded configuration from {file_path}")
            self.logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            self.logger.error(f"Failed to load configuration: {e}")
    
    def _save_config(self) -> None:
        """Save the current configuration."""
        # Update config from UI first
        self._update_config_from_ui()
        
        # Check if we have a file path to save to
        if hasattr(self, 'current_config_path') and self.current_config_path:
            self._save_config_to_file(self.current_config_path)
        else:
            self._save_config_as()
    
    def _save_config_as(self) -> None:
        """Save the current configuration to a new file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Configuration As",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self._save_config_to_file(file_path)
            self.current_config_path = file_path
    
    def _save_config_to_file(self, file_path: str) -> None:
        """Save the current configuration to a file."""
        try:
            import json
            
            # Update config from UI first
            self._update_config_from_ui()
            
            # Convert config to dict
            config_dict = self.current_config.to_dict()
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            # Add to recent configs
            self.app_config.add_recent_config(file_path)
            self._update_recent_menu()
            
            self.status_var.set(f"Saved configuration to {file_path}")
            self.logger.info(f"Saved configuration to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _update_recent_menu(self) -> None:
        """Update the recent configs menu."""
        # Clear existing menu items
        self.recent_menu.delete(0, tk.END)
        
        if not self.app_config.recent_configs:
            self.recent_menu.add_command(label="No recent configs", state=tk.DISABLED)
            return
        
        # Add recent configs
        for i, path in enumerate(self.app_config.recent_configs):
            # Use a lambda with a default argument to avoid late binding issues
            self.recent_menu.add_command(
                label=f"{i+1}. {os.path.basename(path)}",
                command=lambda p=path: self._load_config(p)
            )
        
        # Add separator and clear option
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear Recent", command=self._clear_recent)
    
    def _clear_recent(self) -> None:
        """Clear the recent configs list."""
        self.app_config.recent_configs = []
        self.app_config.save()
        self._update_recent_menu()
    
    def _toggle_dark_mode(self) -> None:
        """Toggle dark mode."""
        self.app_config.dark_mode = self.dark_mode_var.get()
        self.app_config.save()
        self.theme_manager.set_theme(self.app_config.dark_mode)
    
    def _open_rbxsigtools(self) -> None:
        """Open RbxSigTools directory."""
        if self.rbxsigtools_path_var.get():
            path = self.rbxsigtools_path_var.get()
            if os.path.exists(path):
                # Open file explorer at the path
                if os.name == 'nt':  # Windows
                    os.startfile(path)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    subprocess.call(('xdg-open', path))
            else:
                messagebox.showwarning("Path Not Found", f"The path {path} does not exist.")
        else:
            messagebox.showinfo("No Path", "Please set the RbxSigTools path in the Setup tab.")
    
    def _view_backups(self) -> None:
        """View backup files for the current client."""
        if self.client_path_var.get():
            client_dir = os.path.dirname(self.client_path_var.get())
            if os.path.exists(client_dir):
                # Open file explorer at the client directory
                if os.name == 'nt':  # Windows
                    os.startfile(client_dir)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    subprocess.call(('xdg-open', client_dir))
            else:
                messagebox.showwarning("Path Not Found", f"The client directory {client_dir} does not exist.")
        else:
            messagebox.showinfo("No Client", "Please select a client file in the Setup tab.")
    
    def _restore_backup(self) -> None:
        """Restore client from backup."""
        if not self.client_path_var.get():
            messagebox.showinfo("No Client", "Please select a client file in the Setup tab.")
            return
        
        client_path = Path(self.client_path_var.get())
        backup_path = client_path.with_suffix(f"{client_path.suffix}.backup")
        
        if not backup_path.exists():
            messagebox.showwarning("No Backup", f"No backup file found for {client_path.name}.")
            return
        
        if messagebox.askyesno("Restore Backup", f"Restore {client_path.name} from backup? This will overwrite the current file."):
            try:
                import shutil
                shutil.copy2(backup_path, client_path)
                messagebox.showinfo("Success", f"Successfully restored {client_path.name} from backup.")
                self.logger.info(f"Restored {client_path} from backup {backup_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore from backup: {str(e)}")
                self.logger.error(f"Failed to restore from backup: {e}")
    
    # Continuation from previous code

    def _show_documentation(self) -> None:
        """Show documentation in a new window."""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("800x600")
        
        # Create a text widget with scrollbar
        text_frame = ttk.Frame(doc_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text = tk.Text(text_frame, wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text.config(yscrollcommand=scrollbar.set)
        
        # Insert documentation text
        doc_text = """# Roblox Revival Creator - Documentation

## Overview
This tool helps you create Roblox revivals by patching official Roblox clients.

## Setup
1. Select your Roblox client file (.exe)
2. Choose the client type (Player, Studio, RCCService)
3. Enter your website domain (must be exactly 10 characters)
4. Provide paths to required tools (RbxSigTools, x64dbg)

## Available Patches

### Website Patch
Changes all instances of 'roblox.com' to your custom domain and updates AppSettings.xml.

### Public Key Patch
Generates new cryptographic keys and replaces the original key in the client.
Requires RbxSigTools.

### Blocking %s Patch
Allows assets to be inserted from other domains.
Not recommended for public revivals.

### Invalid Request Patch
Bypasses request validation.
Poses a major security risk - use only for private revivals.

### Trust Check Patch
Similar to Invalid Request patch.
Poses a major security risk - use only for private revivals.

### Ratnet Key Patch
For RCCService clients only.
Replaces the Ratnet key with a known working value.

### HtmlService Patch
For 2008 clients only.
Disables the HtmlService which can be a security risk.

## Resources
- Rbx-Scripts: https://github.com/yoshi295295/rblx-scripts
- Free-for-dev: https://free-for.dev/#/?id=web-hosting
- Patching-Guides-Wiki: https://uboomblox.miraheze.org/wiki/Patching
"""
        
        text.insert(tk.END, doc_text)
        text.config(state=tk.DISABLED)
    
    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Roblox Revival Creator v1.0\n\n"
            "A tool to automate patching Roblox clients for revivals.\n\n"
            "Created with Python and Tkinter."
        )
    
    def _clear_log(self) -> None:
        """Clear the log text widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _save_log(self) -> None:
        """Save log to a file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.status_var.set(f"Log saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {str(e)}")