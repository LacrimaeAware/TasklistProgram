"""UI utility functions."""
import tkinter as tk


def center_window(window, master=None):
    """
    Center a window relative to its master or on screen.
    
    Args:
        window: The Toplevel window to center
        master: Optional parent window to center relative to
    """
    window.update_idletasks()
    
    # Get window dimensions
    width = window.winfo_width()
    height = window.winfo_height()
    
    if master and master.winfo_exists():
        # Center relative to master window
        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        
        x = master_x + (master_width - width) // 2
        y = master_y + (master_height - height) // 2
    else:
        # Center on screen
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
    
    # Ensure the window is fully on screen
    x = max(0, min(x, window.winfo_screenwidth() - width))
    y = max(0, min(y, window.winfo_screenheight() - height))
    
    window.geometry(f"+{x}+{y}")
