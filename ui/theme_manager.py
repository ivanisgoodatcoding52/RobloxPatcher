"""
Theme manager for the application.
"""
import tkinter as tk


class ThemeManager:
    """Manages application themes (light/dark)."""
    
    def __init__(self, root: tk.Tk, dark_mode: bool = False):
        """
        Initialize the theme manager.
        
        Args:
            root: The root Tkinter window
            dark_mode: Whether to start in dark mode
        """
        self.root = root
        self.dark_mode = dark_mode
        
        # Define styles
        self._create_styles()
        
        # Apply the appropriate theme
        self.set_theme(dark_mode)
    
    def _create_styles(self) -> None:
        """Create custom ttk styles."""
        # Get the ttk style object
        style = tk.ttk.Style()
        
        # Define custom styles
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"))
        style.configure("Invalid.TEntry", foreground="red")
    
    def set_theme(self, dark_mode: bool) -> None:
        """
        Set the application theme.
        
        Args:
            dark_mode: Whether to use dark mode
        """
        self.dark_mode = dark_mode
        style = tk.ttk.Style()
        
        if dark_mode:
            # Dark theme colors
            bg_color = "#2c2c2c"
            fg_color = "#ffffff"
            select_bg = "#505050"
            select_fg = "#ffffff"
            button_bg = "#3c3c3c"
            button_active_bg = "#505050"
            entry_bg = "#3c3c3c"
            
            # Configure ttk styles for dark mode
            style.configure("TFrame", background=bg_color)
            style.configure("TLabel", background=bg_color, foreground=fg_color)
            style.configure("TButton", background=button_bg, foreground=fg_color)
            style.map("TButton",
                      background=[("active", button_active_bg)],
                      foreground=[("active", fg_color)])
            style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
            style.map("TCheckbutton", 
                      background=[("active", bg_color)],
                      foreground=[("active", fg_color)])
            style.configure("TRadiobutton", background=bg_color, foreground=fg_color)
            style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color)
            style.configure("TCombobox", fieldbackground=entry_bg, foreground=fg_color)
            style.map("TCombobox", 
                      fieldbackground=[("readonly", entry_bg)],
                      foreground=[("readonly", fg_color)])
            style.configure("TNotebook", background=bg_color)
            style.configure("TNotebook.Tab", background=button_bg, foreground=fg_color, padding=[10, 2])
            style.map("TNotebook.Tab",
                      background=[("selected", select_bg)],
                      foreground=[("selected", select_fg)])
            style.configure("Treeview", 
                           background=entry_bg, 
                           foreground=fg_color, 
                           fieldbackground=entry_bg)
            style.map("Treeview",
                     background=[("selected", select_bg)],
                     foreground=[("selected", select_fg)])
            
            # Configure ttk extension styles
            style.configure("Accent.TButton", background="#0078d7", foreground="white")
            style.map("Accent.TButton",
                      background=[("active", "#1a88e0")],
                      foreground=[("active", "white")])
            
            # Configure regular tkinter widgets
            self.root.configure(background=bg_color)
            text_widgets = self._find_widgets_by_class(self.root, tk.Text)
            for w in text_widgets:
                w.configure(background=entry_bg, foreground=fg_color, insertbackground=fg_color)
            
            listbox_widgets = self._find_widgets_by_class(self.root, tk.Listbox)
            for w in listbox_widgets:
                w.configure(background=entry_bg, foreground=fg_color, selectbackground=select_bg, selectforeground=select_fg)
            
            menu_widgets = self._find_widgets_by_class(self.root, tk.Menu)
            for w in menu_widgets:
                w.configure(background=bg_color, foreground=fg_color, activebackground=select_bg, activeforeground=select_fg)
        else:
            # Reset to default theme
            # This uses the system's default theme
            style.theme_use("default")
            
            # Configure custom styles for light mode
            style.configure("Accent.TButton", foreground="white", background="#0078d7")
            style.map("Accent.TButton",
                     background=[("active", "#1a88e0")],
                     foreground=[("active", "white")])
            
            # Reset regular tkinter widgets
            self.root.configure(background=style.lookup("TFrame", "background"))
            text_widgets = self._find_widgets_by_class(self.root, tk.Text)
            for w in text_widgets:
                w.configure(background="white", foreground="black", insertbackground="black")
            
            listbox_widgets = self._find_widgets_by_class(self.root, tk.Listbox)
            for w in listbox_widgets:
                w.configure(background="white", foreground="black", selectbackground="#0078d7", selectforeground="white")
            
            menu_widgets = self._find_widgets_by_class(self.root, tk.Menu)
            for w in menu_widgets:
                w.configure(background="SystemButtonFace", foreground="SystemButtonText", 
                           activebackground="SystemHighlight", activeforeground="SystemHighlightText")
    
    def _find_widgets_by_class(self, parent, widget_class):
        """
        Find all widgets of a specific class within a parent widget.
        
        Args:
            parent: The parent widget to search in
            widget_class: The class of widgets to find
            
        Returns:
            A list of widgets of the specified class
        """
        result = []
        
        if isinstance(parent, widget_class):
            result.append(parent)
        
        try:
            for child in parent.winfo_children():
                result.extend(self._find_widgets_by_class(child, widget_class))
        except (AttributeError, tk.TclError):
            pass
        
        return result