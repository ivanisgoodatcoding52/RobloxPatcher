#!/usr/bin/env python3
"""
Modern Roblox Patcher - Standalone UI

A graphical tool to patch modern Roblox clients (2018-2021).
"""
import logging
import os
import sys
import tkinter as tk
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the ModernPatcher class
try:
    # First try to import from the current directory
    from modern_patchers import ModernPatcher, ModernClientType
except ImportError:
    try:
        # Then try as a relative import from a package
        from .modern_patchers import ModernPatcher, ModernClientType
    except ImportError:
        print("Error: Could not import modern_patchers module. Make sure it's in the same directory.")
        sys.exit(1)


class ModernPatcherApp:
    """Main application for the Modern Roblox Patcher UI."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Modern Roblox Patcher")
        self.root.geometry("800x600")
        
        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create the UI
        self._setup_ui()
    
    def _setup_logging(self):
        """Set up logging for the application."""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "modern_patcher.log")
        
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
            text="Modern Roblox Patcher (2018-2021)", 
            font=("TkDefaultFont", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Create notebook with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        patcher_tab = ttk.Frame(notebook)
        log_tab = ttk.Frame(notebook)
        
        notebook.add(patcher_tab, text="Patcher")
        notebook.add(log_tab, text="Log")
        
        # Patcher tab content
        self._setup_patcher_tab(patcher_tab)
        
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
    
    def _setup_patcher_tab(self, parent):
        """
        Set up the patcher tab content.
        
        Args:
            parent: The parent widget
        """
        patcher_frame = ttk.Frame(parent, padding="10")
        patcher_frame.pack(fill=tk.BOTH, expand=True)
        
        # Client selection
        ttk.Label(patcher_frame, text="Client Executable:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        client_frame = ttk.Frame(patcher_frame)
        client_frame.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        self.client_path_var = tk.StringVar()
        ttk.Entry(
            client_frame, 
            textvariable=self.client_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            client_frame, 
            text="Browse", 
            command=self._browse_client
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # RCCService selection
        ttk.Label(patcher_frame, text="RCCService Executable:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        rcc_frame = ttk.Frame(patcher_frame)
        rcc_frame.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        self.rcc_path_var = tk.StringVar()
        ttk.Entry(
            rcc_frame, 
            textvariable=self.rcc_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            rcc_frame, 
            text="Browse", 
            command=self._browse_rcc
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Domain
        ttk.Label(patcher_frame, text="Domain:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        domain_frame = ttk.Frame(patcher_frame)
        domain_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.domain_var = tk.StringVar(value="localhost")
        ttk.Entry(
            domain_frame, 
            textvariable=self.domain_var, 
            width=20
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            domain_frame, 
            text="(Use 'localhost' for 2019-2021 clients, 10 chars for 2018M)",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Output directory
        ttk.Label(patcher_frame, text="Output Directory:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        output_frame = ttk.Frame(patcher_frame)
        output_frame.grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        self.output_dir_var = tk.StringVar()
        ttk.Entry(
            output_frame, 
            textvariable=self.output_dir_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            output_frame, 
            text="Browse", 
            command=self._browse_output_dir
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Tool paths
        tools_frame = ttk.LabelFrame(patcher_frame, text="Tool Paths")
        tools_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # x32dbg
        ttk.Label(tools_frame, text="x32dbg:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        x32dbg_frame = ttk.Frame(tools_frame)
        x32dbg_frame.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        self.x32dbg_path_var = tk.StringVar()
        ttk.Entry(
            x32dbg_frame, 
            textvariable=self.x32dbg_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            x32dbg_frame, 
            text="Browse", 
            command=self._browse_x32dbg
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # HxD
        ttk.Label(tools_frame, text="HxD:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        hxd_frame = ttk.Frame(tools_frame)
        hxd_frame.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        self.hxd_path_var = tk.StringVar()
        ttk.Entry(
            hxd_frame, 
            textvariable=self.hxd_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            hxd_frame, 
            text="Browse", 
            command=self._browse_hxd
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Stud_PE
        ttk.Label(tools_frame, text="Stud_PE:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        stud_pe_frame = ttk.Frame(tools_frame)
        stud_pe_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        self.stud_pe_path_var = tk.StringVar()
        ttk.Entry(
            stud_pe_frame, 
            textvariable=self.stud_pe_path_var, 
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            stud_pe_frame, 
            text="Browse", 
            command=self._browse_stud_pe
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Make the tools frame columns expand properly
        tools_frame.columnconfigure(1, weight=1)
        
        # Patching method selection
        method_frame = ttk.LabelFrame(patcher_frame, text="Patching Method")
        method_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.method_var = tk.StringVar(value="auto")
        
        ttk.Radiobutton(
            method_frame, 
            text="Auto-detect", 
            variable=self.method_var, 
            value="auto"
        ).pack(side=tk.LEFT, padx=(10, 20), pady=5)
        
        ttk.Radiobutton(
            method_frame, 
            text="Force 2018M", 
            variable=self.method_var, 
            value="2018m"
        ).pack(side=tk.LEFT, padx=(0, 20), pady=5)
        
        ttk.Radiobutton(
            method_frame, 
            text="Force 2019-2021", 
            variable=self.method_var, 
            value="2019-2021"
        ).pack(side=tk.LEFT, pady=5)
        
        # Patch button
        self.patch_button = ttk.Button(
            patcher_frame, 
            text="Patch Client", 
            command=self._patch_client
        )
        self.patch_button.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(
            patcher_frame, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='determinate',
            variable=self.progress_var
        )
        progress_bar.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Make the patcher frame columns expand properly
        patcher_frame.columnconfigure(1, weight=1)
    
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
    
    def _browse_client(self):
        """Open file dialog to select client executable."""
        file_path = filedialog.askopenfilename(
            title="Select Roblox Client",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.client_path_var.set(file_path)
            
            # If output directory not set, use client directory
            if not self.output_dir_var.get():
                self.output_dir_var.set(os.path.dirname(file_path))
    
    def _browse_rcc(self):
        """Open file dialog to select RCCService."""
        file_path = filedialog.askopenfilename(
            title="Select RCCService",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.rcc_path_var.set(file_path)
    
    def _browse_output_dir(self):
        """Open directory dialog to select output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        
        if directory:
            self.output_dir_var.set(directory)
    
    def _browse_x32dbg(self):
        """Open file dialog to select x32dbg."""
        file_path = filedialog.askopenfilename(
            title="Select x32dbg",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.x32dbg_path_var.set(file_path)
    
    def _browse_hxd(self):
        """Open file dialog to select HxD ."""
        file_path = filedialog.askopenfilename(
            title="Select HxD",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.hxd_path_var.set(file_path)
    
    def _browse_stud_pe(self):
        """Open file dialog to select Stud_PE ."""
        file_path = filedialog.askopenfilename(
            title="Select Stud_PE",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.stud_pe_path_var.set(file_path)
    
    def _patch_client(self):
        """Patch the client."""
        # Get values from UI
        client_path = self.client_path_var.get()
        rcc_path = self.rcc_path_var.get() or None
        domain = self.domain_var.get()
        output_dir = self.output_dir_var.get()
        x32dbg_path = self.x32dbg_path_var.get() or None
        hxd_path = self.hxd_path_var.get() or None
        stud_pe_path = self.stud_pe_path_var.get() or None
        
        # Validate inputs
        if not client_path:
            messagebox.showwarning("Input Error", "Please select a client executable.")
            return
        
        if not os.path.exists(client_path):
            messagebox.showerror("File Error", f"Client file does not exist: {client_path}")
            return
        
        if rcc_path and not os.path.exists(rcc_path):
            messagebox.showerror("File Error", f"RCCService file does not exist: {rcc_path}")
            return
        
        if not domain:
            messagebox.showwarning("Input Error", "Please enter a domain.")
            return
        
        # Create ModernPatcher
        try:
            patcher = ModernPatcher(
                client_path=client_path,
                rcc_path=rcc_path,
                domain=domain,
                output_dir=output_dir,
                x32dbg_path=x32dbg_path,
                hxd_path=hxd_path,
                stud_pe_path=stud_pe_path
            )
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize patcher: {str(e)}")
            self._add_to_log(f"Error: {str(e)}")
            return
        
        # Disable patch button and reset progress
        self.patch_button.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Patching in progress...")
        
        # Start patching in a background thread
        thread = threading.Thread(target=self._patch_thread, args=(patcher,))
        thread.daemon = True
        thread.start()
    
    def _patch_thread(self, patcher):
        """
        Run the patching process in a background thread.
        
        Args:
            patcher: The ModernPatcher instance
        """
        try:
            # Update progress and status
            self._add_to_log("Starting patching process...")
            self.root.after(0, lambda: self.progress_var.set(10))
            self.root.after(0, lambda: self.status_var.set("Detecting client type..."))
            
            # Get the patching method
            method = self.method_var.get()
            
            # Run the appropriate patching method
            success = False
            
            if method == "auto":
                self._add_to_log("Using auto-detection for client type")
                success = patcher.patch()
            elif method == "2018m":
                self._add_to_log("Using 2018M patching method")
                success = patcher.patch_2018m()
            elif method == "2019-2021":
                self._add_to_log("Using 2019-2021 patching method")
                success = patcher.patch_2019_2021()
            
            # Update progress to 100%
            self.root.after(0, lambda: self.progress_var.set(100))
            
            # Show result
            if success:
                self.root.after(0, lambda: self.status_var.set("Patching completed successfully"))
                self._add_to_log("Patching process completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Client patched successfully!\nOutput files are in: {patcher.output_dir}"
                ))
            else:
                self.root.after(0, lambda: self.status_var.set("Patching completed with errors"))
                self._add_to_log("Patching process completed with errors!")
                self.root.after(0, lambda: messagebox.showwarning(
                    "Warning", 
                    "Patching completed with some errors. Check the log for details."
                ))
        
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self._add_to_log(f"Error during patching: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Patching failed: {str(e)}"))
        
        finally:
            # Re-enable the patch button
            self.root.after(0, lambda: self.patch_button.configure(state="normal"))
    
    def _add_to_log(self, message):
        """
        Add a message to the log.
        
        Args:
            message: The message to add
        """
        self.logger.info(message)
        
        # Update UI log
        def update_log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, update_log)
    
    def _clear_log(self):
        """Clear the log text widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _save_log(self):
        """Save the log to a file."""
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


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = ModernPatcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()