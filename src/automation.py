import logging
import time

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

        start_time = time.time()
        while time.time() - start_time < timeout:
            windows = gw.getWindowsWithTitle("Notepad")
            if windows:
                logger.info("Notepad launched")
                return True
            time.sleep(0.3)

        logger.warning("Notepad window not detected")
        return False

    except Exception as e:
        logger.error(f"Error launching Notepad: {e}")
        return False


def type_text(text: str, interval: float = 0.02) -> None:
    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)

        pyautogui.write(text, interval=interval)
        time.sleep(0.3)
        logger.info(f"Typed {len(text)} characters")

    except Exception as e:
        logger.error(f"Error typing text: {e}")
        raise


def save_file(filename: str, directory: str) -> bool:
    try:
        import os
        filepath = os.path.join(directory, filename)

        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.0)

        pyautogui.write(filepath, interval=0.02)
        time.sleep(0.3)

        pyautogui.press('enter')
        time.sleep(0.8)

        # Handle file overwrite confirmation
        try:
            confirm_windows = gw.getWindowsWithTitle("Confirm Save As")
            if confirm_windows:
                confirm_windows[0].activate()
                time.sleep(0.3)
                pyautogui.press('y')
                time.sleep(0.5)
        except:
            pass

        time.sleep(0.5)
        if os.path.exists(filepath):
            logger.info(f"File saved: {filepath}")
            return True
        else:
            logger.warning("File may not have been saved")
            return False

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False


def close_notepad() -> None:
    try:
        notepad_windows = gw.getWindowsWithTitle('Notepad')

        if not notepad_windows:
            all_windows = gw.getAllTitles()
            for title in all_windows:
                if 'Notepad' in title or 'notepad' in title:
                    notepad_windows = gw.getWindowsWithTitle(title)
                    break

        if notepad_windows:
            notepad_windows[0].close()
            time.sleep(0.5)
            logger.info("Notepad closed")

    except Exception as e:
        logger.error(f"Error closing Notepad: {e}")


def ensure_notepad_closed() -> None:
    try:
        for attempt in range(2):
            notepad_windows = gw.getWindowsWithTitle('Notepad')

            if not notepad_windows:
                all_windows = gw.getAllTitles()
                for title in all_windows:
                    if 'Notepad' in title or 'notepad' in title:
                        notepad_windows = gw.getWindowsWithTitle(title)
                        break

            if notepad_windows:
                notepad_windows[0].close()
                time.sleep(0.3)
            else:
                break

    except Exception as e:
        logger.debug(f"Error ensuring Notepad is closed: {e}")


def wait_before_next_iteration(delay: float = 1.0) -> None:
    time.sleep(delay)
