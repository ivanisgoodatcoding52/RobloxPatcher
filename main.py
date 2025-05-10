#!/usr/bin/env python3
import logging
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Add the current directory to the path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import AppConfig
from patchers import (BlockingPatcher, HtmlServicePatcher, InvalidRequestPatcher,
                     PublicKeyPatcher, RatnetKeyPatcher, TrustCheckPatcher,
                     WebsitePatcher)
from ui.main_window import MainWindow
from utils import setup_logging

def main() -> None:
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Roblox Revival Creator")

    # Create and configure the application
    app_config = AppConfig()
    
    # Initialize root window
    root = tk.Tk()
    root.title("Roblox Revival Creator")
    root.geometry("850x650")  # Larger window to accommodate new features
    
    # Create main application window
    app = MainWindow(root, app_config)
    
    # Start the application
    try:
        root.mainloop()
    except Exception as e:
        logger.exception("Uncaught exception")
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
    finally:
        logger.info("Application closed")


if __name__ == "__main__":
    main()
