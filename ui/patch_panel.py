"""
Patch panel UI component for selecting and applying patches.
"""
import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Set

from config import ClientType, PatchConfig, PatchType
from patchers import (BlockingPatcher, HtmlServicePatcher, InvalidRequestPatcher,
                    PublicKeyPatcher, RatnetKeyPatcher, TrustCheckPatcher,
                    WebsitePatcher)


class PatchPanel(ttk.Frame):
    """Panel for selecting and applying patches."""
    
    def __init__(self, parent, config: PatchConfig):
        """
        Initialize the patch panel.
        
        Args:
            parent: The parent widget
            config: The patch configuration
        """
        super().__init__(parent, padding="10")
        self.parent = parent
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.patch_vars: Dict[PatchType, tk.BooleanVar] = {}
        
        # Get a reference to the root window for after() calls
        self.root = self.winfo_toplevel()
        
        self.pack(fill=tk.BOTH, expand=True)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Title
        ttk.Label(
            self, 
            text="Select Patches to Apply", 
            font=("TkDefaultFont", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Create a frame for the patches
        patches_frame = ttk.LabelFrame(self, text="Available Patches")
        patches_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Website patch
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.WEBSITE, 
            "Website Patch", 
            "Changes 'roblox.com' to your custom domain in the client and updates AppSettings.xml",
            0
        )
        
        # Public key patch
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.PUBLIC_KEY, 
            "Public Key Patch", 
            "Generates new cryptographic keys and replaces them in the client (requires RbxSigTools)",
            1
        )
        
        # Blocking %s patch
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.BLOCKING, 
            "Blocking %s Patch (not recommended)", 
            "Allows assets to be inserted from other domains, including roblox.com after site patch",
            2
        )
        
        # Invalid request patch
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.INVALID_REQUEST, 
            "Invalid Request Patch (security risk)", 
            "Bypasses request validation - major security risk, use only for private revivals",
            3
        )
        
        # Trust check patch
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.TRUST_CHECK, 
            "Trust Check Patch (security risk)", 
            "Similar to Invalid Request patch - major security risk, use only for private revivals",
            4
        )
        
        # Ratnet key patch (RCCService only)
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.RATNET_KEY, 
            "Ratnet Key Patch (RCCService only)", 
            "Replaces the Ratnet key with a known working value, required for some RCCService versions",
            5
        )
        
        # HtmlService patch (2008 only)
        self._add_patch_checkbox(
            patches_frame, 
            PatchType.HTML_SERVICE, 
            "HtmlService Patch (2008 only)", 
            "Disables the HtmlService which can be a security risk in 2008 clients",
            6
        )
        
        # Actions frame
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, pady=10)
        
        # Select/deselect all buttons
        ttk.Button(
            actions_frame, 
            text="Select All", 
            command=self._select_all_patches
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame, 
            text="Deselect All", 
            command=self._deselect_all_patches
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame, 
            text="Select Recommended", 
            command=self._select_recommended_patches
        ).pack(side=tk.LEFT, padx=5)
        
        # Apply button
        self.apply_button = ttk.Button(
            self, 
            text="Apply Selected Patches", 
            command=self._apply_patches,
            style="Accent.TButton"
        )
        self.apply_button.pack(pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self, 
            orient=tk.HORIZONTAL, 
            length=300, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to apply patches")
        self.status_label = ttk.Label(
            self, 
            textvariable=self.status_var,
            wraplength=400
        )
        self.status_label.pack(pady=5)
        
        # Update UI based on current config
        self.update_config(self.config)
    
    def _add_patch_checkbox(self, parent, patch_type: PatchType, text: str, tooltip: str, row: int) -> None:
        """
        Add a checkbox for a patch.
        
        Args:
            parent: The parent widget
            patch_type: The type of patch
            text: The checkbox label text
            tooltip: The tooltip text
            row: The row in the grid
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        
        var = tk.BooleanVar(value=False)
        self.patch_vars[patch_type] = var
        
        checkbox = ttk.Checkbutton(
            frame, 
            text=text, 
            variable=var,
            command=lambda: self._update_config_patches()
        )
        checkbox.pack(side=tk.LEFT)
        
        # Add tooltip icon
        info_label = ttk.Label(frame, text="ℹ️", cursor="hand2")
        info_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind tooltip
        def show_tooltip(event):
            tooltip_window = tk.Toplevel(parent)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip_window, text=tooltip, wraplength=300, background="#FFFFCC", relief=tk.SOLID, borderwidth=1)
            label.pack()
            
            def hide_tooltip(event=None):
                tooltip_window.destroy()
            
            tooltip_window.after(3000, hide_tooltip)
            info_label.bind("<Leave>", hide_tooltip)
        
        info_label.bind("<Enter>", show_tooltip)
    
    def update_config(self, config: PatchConfig) -> None:
        """
        Update the UI based on the configuration.
        
        Args:
            config: The patch configuration
        """
        self.config = config
        
        # Update checkboxes based on config
        for patch_type, var in self.patch_vars.items():
            var.set(patch_type in config.patches)
        
        # Disable/enable patches based on client type and version
        self._update_patch_availability()
    
    def _update_patch_availability(self) -> None:
        """Update which patches are available based on client type and version."""
        # Reset all to enabled first
        for patch_type in self.patch_vars.keys():
            self._set_patch_enabled(patch_type, True)
        
        # Disable Ratnet key patch if not RCCService
        if self.config.client_type != ClientType.RCC_SERVICE:
            self._set_patch_enabled(PatchType.RATNET_KEY, False)
            if PatchType.RATNET_KEY in self.config.patches:
                self.config.patches.remove(PatchType.RATNET_KEY)
                self.patch_vars[PatchType.RATNET_KEY].set(False)
        
        # Disable HtmlService patch if not 2008
        if self.config.version_year != 2008:
            self._set_patch_enabled(PatchType.HTML_SERVICE, False)
            if PatchType.HTML_SERVICE in self.config.patches:
                self.config.patches.remove(PatchType.HTML_SERVICE)
                self.patch_vars[PatchType.HTML_SERVICE].set(False)
    
    def _set_patch_enabled(self, patch_type: PatchType, enabled: bool) -> None:
        """
        Enable or disable a patch checkbox.
        
        Args:
            patch_type: The type of patch
            enabled: Whether the patch should be enabled
        """
        state = "normal" if enabled else "disabled"
        
        # Get the patch name from the enum
        patch_display_name = patch_type.name.replace('_', ' ').title()
        
        # Find the checkbox for this patch type
        for widget in self.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    for sub_child in child.winfo_children():
                        if isinstance(sub_child, ttk.Checkbutton) and sub_child.cget("text").startswith(patch_display_name):
                            sub_child.configure(state=state)
    
    def _update_config_patches(self) -> None:
        """Update the config's patches based on the checkbox values."""
        # Clear existing patches
        self.config.patches.clear()
        
        # Add selected patches
        for patch_type, var in self.patch_vars.items():
            if var.get():
                self.config.patches.add(patch_type)
    
    def _select_all_patches(self) -> None:
        """Select all available patches."""
        for patch_type, var in self.patch_vars.items():
            # Only select patches that are enabled
            widget_state = self._get_patch_widget_state(patch_type)
            if widget_state != "disabled":
                var.set(True)
        
        self._update_config_patches()
    
    def _deselect_all_patches(self) -> None:
        """Deselect all patches."""
        for var in self.patch_vars.values():
            var.set(False)
        
        self._update_config_patches()
    
    def _select_recommended_patches(self) -> None:
        """Select only the recommended patches."""
        # First deselect all
        self._deselect_all_patches()
        
        # Select recommended patches
        recommended = [PatchType.WEBSITE, PatchType.PUBLIC_KEY]
        
        # Add HtmlService for 2008
        if self.config.version_year == 2008:
            recommended.append(PatchType.HTML_SERVICE)
        
        # Add Ratnet key for RCCService
        if self.config.client_type == ClientType.RCC_SERVICE:
            recommended.append(PatchType.RATNET_KEY)
        
        for patch_type in recommended:
            if patch_type in self.patch_vars:
                self.patch_vars[patch_type].set(True)
        
        self._update_config_patches()
    
    def _get_patch_widget_state(self, patch_type: PatchType) -> str:
        """
        Get the state of a patch's checkbox widget.
        
        Args:
            patch_type: The type of patch
            
        Returns:
            The state of the widget ('normal', 'disabled', etc.)
        """
        # Get the patch name from the enum
        patch_display_name = patch_type.name.replace('_', ' ').title()
        
        for widget in self.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    for sub_child in child.winfo_children():
                        if isinstance(sub_child, ttk.Checkbutton) and sub_child.cget("text").startswith(patch_display_name):
                            return sub_child.cget("state")
        
        return "normal"
    
    def _apply_patches(self) -> None:
        """Apply the selected patches."""
        # Check if any patches are selected
        if not self.config.patches:
            messagebox.showwarning("No Patches Selected", "Please select at least one patch to apply.")
            return
        
        # Confirm before proceeding
        message = "Apply the following patches?\n\n"
        message += "\n".join(f"- {p.name.replace('_', ' ').title()}" for p in self.config.patches)
        
        # Add warning for risky patches
        risky_patches = {PatchType.BLOCKING, PatchType.INVALID_REQUEST, PatchType.TRUST_CHECK}
        if any(p in risky_patches for p in self.config.patches):
            message += "\n\nWARNING: You've selected patches that may pose security risks."
        
        if not messagebox.askyesno("Confirm", message):
            return
        
        # Disable apply button during patching
        self.apply_button.configure(state="disabled")
        self.progress_var.set(0)
        
        # Start patching in a background thread
        threading.Thread(target=self._apply_patches_thread, daemon=True).start()
    
    def _apply_patches_thread(self) -> None:
        """Apply patches in a background thread."""
        try:
            # Create patchers for selected patches
            patchers = []
            
            if PatchType.WEBSITE in self.config.patches:
                patchers.append(WebsitePatcher(self.config))
            
            if PatchType.PUBLIC_KEY in self.config.patches:
                patchers.append(PublicKeyPatcher(self.config))
            
            if PatchType.BLOCKING in self.config.patches:
                patchers.append(BlockingPatcher(self.config))
            
            if PatchType.INVALID_REQUEST in self.config.patches:
                patchers.append(InvalidRequestPatcher(self.config))
            
            if PatchType.TRUST_CHECK in self.config.patches:
                patchers.append(TrustCheckPatcher(self.config))
            
            if PatchType.RATNET_KEY in self.config.patches:
                patchers.append(RatnetKeyPatcher(self.config))
            
            if PatchType.HTML_SERVICE in self.config.patches:
                patchers.append(HtmlServicePatcher(self.config))
            
            # Apply each patch
            success_count = 0
            total_patches = len(patchers)
            
            for i, patcher in enumerate(patchers):
                patch_name = patcher.__class__.__name__
                
                # Update status
                self._update_status(f"Applying {patch_name}...")
                
                # Validate patch
                if not patcher.validate():
                    self._update_status(f"Validation failed for {patch_name}")
                    continue
                
                # Apply patch
                if patcher.apply():
                    success_count += 1
                    self._update_status(f"{patch_name} applied successfully")
                else:
                    self._update_status(f"Failed to apply {patch_name}")
                
                # Update progress
                progress = (i + 1) / total_patches
                self._update_progress(progress)
            
            # Final status
            if success_count == total_patches:
                self._update_status(f"All patches applied successfully ({success_count}/{total_patches})")
            else:
                self._update_status(f"Patching completed with some failures ({success_count}/{total_patches} successful)")
        
        except Exception as e:
            self.logger.exception("Error applying patches")
            self._update_status(f"Error: {str(e)}")
        
        finally:
            # Re-enable apply button
            self.root.after(0, lambda: self.apply_button.configure(state="normal"))
    
    def _update_status(self, message: str) -> None:
        """
        Update the status message.
        
        Args:
            message: The status message
        """
        self.logger.info(message)
        
        # Update UI from the main thread
        self.root.after(0, lambda: self.status_var.set(message))
    
    def _update_progress(self, value: float) -> None:
        """
        Update the progress bar.
        
        Args:
            value: The progress value (0.0 to 1.0)
        """
        # Update UI from the main thread
        self.root.after(0, lambda: self.progress_var.set(value * 100))