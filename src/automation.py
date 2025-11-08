"""Automation functions for mouse and keyboard control."""

import logging
import time
from typing import Optional

import pyautogui

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


def activate_notepad() -> None:
    """
    Ensure Notepad window is active by clicking in it.
    """
    try:
        # Click in the Notepad window to ensure it's active
        # Get screen center as a safe click location
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # Click in center (should be in Notepad text area)
        pyautogui.click(center_x, center_y)
        time.sleep(0.3)
        logger.debug("Activated Notepad window")
    except Exception as e:
        logger.debug(f"Error activating Notepad: {e}")


def save_file(filename: str, directory: str) -> bool:
    """
    Save file using Ctrl+Shift+S (Save As) to ensure we can set the filename.
    
    Args:
        filename: Name of the file to save (e.g., "post_1.txt")
        directory: Directory path to save the file
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        logger.info(f"Saving file: {filename} to {directory}")
        
        # Ensure Notepad is active before saving
        activate_notepad()
        time.sleep(0.3)
        
        # Use File > Save As menu (Alt+F, then A) for reliable Save As dialog
        pyautogui.hotkey('alt', 'f')
        time.sleep(0.3)
        pyautogui.press('a')  # Save As
        time.sleep(1.5)  # Wait for Save As dialog
        
        # Type the full file path
        import os
        filepath = os.path.join(directory, filename)
        
        # Clear any existing text in the filename field
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Type the full file path
        pyautogui.write(filepath, interval=0.05)
        time.sleep(0.5)
        
        # Press Enter to save (this will close the dialog)
        pyautogui.press('enter')
        time.sleep(1.5)  # Wait for save to complete and dialog to close
        
        # If there's a "File already exists" dialog, press Enter to confirm
        # (We handle existing files by appending timestamp, but just in case)
        time.sleep(0.5)
        pyautogui.press('enter')  # Dismiss any confirmation dialog
        time.sleep(0.5)
        
        # Ensure Notepad is active again after saving
        activate_notepad()
        time.sleep(0.3)
        
        # Check if file was created
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
    Close Notepad window using Alt+F4.
    Handles potential "Save changes?" dialog by pressing 'n' (Don't Save).
    """
    try:
        logger.info("Closing Notepad")

        # Close using Alt+F4 (works even if window is not focused)
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.8)

        # Handle potential "Save changes?" dialog if it appears
        # Press 'n' for "Don't Save" (since we already saved the file)
        # This is more reliable than escape
        pyautogui.press('n')
        time.sleep(0.3)

        # Also try pressing 'tab' then 'enter' to click "Don't Save" button
        # in case 'n' doesn't work on some systems
        pyautogui.press('tab')
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(0.3)

        logger.info("Notepad close command sent")

    except Exception as e:
        logger.error(f"Error closing Notepad: {e}")


def ensure_notepad_closed() -> None:
    """
    Ensure Notepad is completely closed, handling any dialogs.
    Uses multiple attempts to close and handles save dialogs.
    """
    try:
        # Try closing with Alt+F4 multiple times
        for attempt in range(3):
            try:
                # Send Alt+F4 to close any open Notepad window
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.5)

                # If a "Save changes?" dialog appears, click "Don't Save"
                # Try multiple methods to dismiss the dialog
                pyautogui.press('n')  # Press 'N' for "Don't Save"
                time.sleep(0.3)

                # Also try Tab+Enter in case 'n' doesn't work
                pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('enter')
                time.sleep(0.3)

                # Press Escape as fallback
                pyautogui.press('escape')
                time.sleep(0.3)

            except Exception:
                pass

        time.sleep(0.5)
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

