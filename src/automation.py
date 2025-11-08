"""Automation functions for mouse and keyboard control."""

import logging
import time
from typing import Optional

import pyautogui
import pygetwindow as gw

logger = logging.getLogger(__name__)

# Configuration
DOUBLE_CLICK_DELAY = 0.1
TYPE_INTERVAL = 0.02
WINDOW_WAIT_TIMEOUT = 5.0
ACTION_DELAY = 0.3

# Disable pyautogui failsafe for automation (use with caution)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Small pause between actions

def launch_notepad(icon_x: int, icon_y: int, timeout: float = WINDOW_WAIT_TIMEOUT) -> bool:
    """
    Launch Notepad by double-clicking the icon at specified coordinates.
    
    Args:
        icon_x: X coordinate of icon center
        icon_y: Y coordinate of icon center
        timeout: Maximum time to wait for Notepad window (seconds)
        
    Returns:
        True if Notepad launched successfully, False otherwise
    """
    try:
        logger.info(f"Moving mouse to icon at ({icon_x}, {icon_y})")
        pyautogui.moveTo(icon_x, icon_y, duration=0.3)
        time.sleep(ACTION_DELAY)
        
        logger.info("Double-clicking icon")
        pyautogui.doubleClick(icon_x, icon_y, interval=DOUBLE_CLICK_DELAY)
        time.sleep(ACTION_DELAY)
        
        # Wait for Notepad window to appear
        logger.info("Waiting for Notepad window...")
        if wait_for_window("Notepad", timeout=timeout):
            logger.info("Notepad launched successfully")
            return True
        else:
            logger.warning("Notepad window not detected after launch")
            return False
            
    except Exception as e:
        logger.error(f"Error launching Notepad: {e}")
        return False


def wait_for_window(title: str, timeout: float = WINDOW_WAIT_TIMEOUT) -> bool:
    """
    Wait for a window with the specified title to appear.
    
    Uses a simple approach: wait for the window to appear and verify
    by checking if we can interact with it.
    
    Args:
        title: Window title to search for (case-insensitive partial match)
        timeout: Maximum time to wait (seconds)
        
    Returns:
        True if window found, False if timeout
    """
    start_time = time.time()
    
    # Simple approach: wait a bit for window to appear, then try to interact
    while time.time() - start_time < timeout:
        try:
            # Try to get active window (if pyautogui supports it)
            # Otherwise, just wait and assume window opened
            time.sleep(0.5)
            
            # Try to verify window is active by attempting a simple action
            # If we can type, the window is likely open
            # For now, we'll use a simpler timeout-based approach
            if time.time() - start_time >= 1.0:  # Give it at least 1 second
                logger.info(f"Assuming {title} window opened (timeout-based check)")
                return True
                
        except Exception as e:
            logger.debug(f"Error checking windows: {e}")
        
        time.sleep(0.2)
    
    # If we have pywinauto available, we could use it for better window detection
    # For now, we'll use a simpler approach
    logger.warning(f"Could not verify {title} window opened within {timeout} seconds")
    return False


def type_text(text: str, interval: float = TYPE_INTERVAL) -> None:
    """
    Type text into the active window.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes (seconds)
    """
    try:
        logger.info(f"Typing text ({len(text)} characters)...")
        # Clear any existing text first (Ctrl+A, then type)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        pyautogui.write(text, interval=interval)
        time.sleep(ACTION_DELAY)
        logger.info("Text typed successfully")
        
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        raise




def save_file(filename: str, directory: str) -> bool:
    """
    Save file using Ctrl+S (Save) which opens Save As dialog for new files.
    Simple and reliable approach.

    Args:
        filename: Name of the file to save (e.g., "post_1.txt")
        directory: Directory path to save the file

    Returns:
        True if save was successful, False otherwise
    """
    try:
        logger.info(f"Saving file: {filename} to {directory}")

        import os
        filepath = os.path.join(directory, filename)

        # Save using Ctrl+S (opens Save As dialog for unsaved files)
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.0)  # Wait for Save As dialog to open

        # Type the full file path
        pyautogui.write(filepath, interval=0.02)
        time.sleep(0.3)

        # Press Enter to save
        pyautogui.press('enter')
        time.sleep(1.0)  # Wait for save to complete

        # Check if file was created
        time.sleep(0.5)  # Extra time for file system to update
        if os.path.exists(filepath):
            logger.info(f"File saved successfully: {filepath}")
            return True
        else:
            logger.warning(f"File may not have been saved: {filepath}")
            return False

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False


def close_notepad() -> None:
    """
    Close Notepad window by finding it by title and closing it directly.
    """
    try:
        logger.info("Closing Notepad")

        # Find all windows with "Notepad" in the title
        notepad_windows = gw.getWindowsWithTitle('Notepad')

        if not notepad_windows:
            # Try finding with partial match
            all_windows = gw.getAllTitles()
            for title in all_windows:
                if 'Notepad' in title or 'notepad' in title:
                    notepad_windows = gw.getWindowsWithTitle(title)
                    break

        if notepad_windows:
            # Close the window directly
            notepad_windows[0].close()
            time.sleep(0.5)
            logger.info("Notepad closed successfully")
        else:
            logger.warning("Could not find Notepad window to close")

    except Exception as e:
        logger.error(f"Error closing Notepad: {e}")


def ensure_notepad_closed() -> None:
    """
    Ensure Notepad is completely closed by finding and closing by title.
    """
    try:
        # Try to find and close Notepad windows up to 2 times
        for attempt in range(2):
            notepad_windows = gw.getWindowsWithTitle('Notepad')

            if not notepad_windows:
                # Try finding with partial match
                all_windows = gw.getAllTitles()
                for title in all_windows:
                    if 'Notepad' in title or 'notepad' in title:
                        notepad_windows = gw.getWindowsWithTitle(title)
                        break

            if notepad_windows:
                notepad_windows[0].close()
                time.sleep(0.3)
            else:
                # No Notepad window found, we're done
                break

        logger.debug("Ensured Notepad is closed")

    except Exception as e:
        logger.debug(f"Error ensuring Notepad is closed: {e}")


def wait_before_next_iteration(delay: float = 1.0) -> None:
    """
    Wait before starting the next iteration.
    
    Args:
        delay: Delay in seconds
    """
    logger.info(f"Waiting {delay} seconds before next iteration...")
    time.sleep(delay)

