import logging
import time
import os

import pyautogui
import pygetwindow as gw

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def launch_notepad(icon_x: int, icon_y: int, timeout: float = 5.0) -> bool:
    try:
        pyautogui.moveTo(icon_x, icon_y, duration=0.3)
        time.sleep(0.3)
        pyautogui.doubleClick(icon_x, icon_y, interval=0.1)
        time.sleep(0.3)
        return wait_for_window("Notepad", timeout)
    except Exception as e:
        logger.error(f"Error launching Notepad: {e}")
        return False


def wait_for_window(title: str, timeout: float = 5.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.5)
        if time.time() - start_time >= 1.0:
            return True
        time.sleep(0.2)
    return False


def type_text(text: str, interval: float = 0.02) -> None:
    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write(text, interval=interval)
        time.sleep(0.3)
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        raise


def save_file(filename: str, directory: str) -> bool:
    try:
        filepath = os.path.join(directory, filename)
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.0)
        pyautogui.write(filepath, interval=0.02)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1.5)
        return os.path.exists(filepath)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False


def close_notepad() -> None:
    try:
        notepad_windows = gw.getWindowsWithTitle('Notepad')
        if not notepad_windows:
            for title in gw.getAllTitles():
                if 'notepad' in title.lower():
                    notepad_windows = gw.getWindowsWithTitle(title)
                    break
        if notepad_windows:
            notepad_windows[0].close()
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error closing Notepad: {e}")


def ensure_notepad_closed() -> None:
    try:
        for _ in range(2):
            notepad_windows = gw.getWindowsWithTitle('Notepad')
            if not notepad_windows:
                for title in gw.getAllTitles():
                    if 'notepad' in title.lower():
                        notepad_windows = gw.getWindowsWithTitle(title)
                        break
            if notepad_windows:
                notepad_windows[0].close()
                time.sleep(0.3)
            else:
                break
    except Exception:
        pass


def wait_before_next_iteration(delay: float = 1.0) -> None:
    time.sleep(delay)

