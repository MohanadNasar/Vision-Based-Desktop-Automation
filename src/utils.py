"""Utility functions for screenshot capture, file handling, and image annotation."""

import os
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui
from PIL import Image


def capture_screenshot(save_path: Optional[str] = None) -> np.ndarray:
    """
    Capture a screenshot of the desktop.
    
    Args:
        save_path: Optional path to save the screenshot. If None, screenshot is not saved.
        
    Returns:
        numpy array representing the screenshot in BGR format (OpenCV format)
    """
    screenshot = pyautogui.screenshot()
    
    if save_path:
        screenshot.save(save_path)
    
    # Convert PIL Image to numpy array (RGB to BGR for OpenCV)
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    return screenshot_bgr


def ensure_directory(path: str) -> Path:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        Path object of the created/existing directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def handle_existing_file(filepath: str) -> str:
    """
    Handle existing files by appending a timestamp.
    
    Args:
        filepath: Original file path
        
    Returns:
        Modified filepath with timestamp if original exists, otherwise original path
    """
    path = Path(filepath)
    
    if path.exists():
        timestamp = int(time.time())
        stem = path.stem
        suffix = path.suffix
        new_filename = f"{stem}_{timestamp}{suffix}"
        new_path = path.parent / new_filename
        return str(new_path)
    
    return filepath


def annotate_screenshot(
    image: np.ndarray,
    x: int,
    y: int,
    width: int = 50,
    height: int = 50,
    label: str = "Detected",
    confidence: Optional[float] = None
) -> np.ndarray:
    """
    Annotate screenshot with bounding box and label at detected location.
    
    Args:
        image: Screenshot image as numpy array (BGR format)
        x: X coordinate of center point
        y: Y coordinate of center point
        width: Width of bounding box
        height: Height of bounding box
        label: Text label to display
        confidence: Optional confidence score to display
        
    Returns:
        Annotated image as numpy array
    """
    annotated = image.copy()
    
    # Calculate bounding box coordinates
    x1 = max(0, x - width // 2)
    y1 = max(0, y - height // 2)
    x2 = min(image.shape[1], x + width // 2)
    y2 = min(image.shape[0], y + height // 2)
    
    # Draw bounding box (green rectangle)
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw center point (red circle)
    cv2.circle(annotated, (x, y), 5, (0, 0, 255), -1)
    
    # Prepare label text
    label_text = label
    if confidence is not None:
        label_text += f" ({confidence:.2f})"
    
    # Get text size for background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(
        label_text, font, font_scale, thickness
    )
    
    # Draw text background (semi-transparent black)
    text_x = x1
    text_y = y1 - text_height - 10
    if text_y < 0:
        text_y = y2 + text_height + 10
    
    overlay = annotated.copy()
    cv2.rectangle(
        overlay,
        (text_x, text_y - text_height - 5),
        (text_x + text_width + 5, text_y + 5),
        (0, 0, 0),
        -1
    )
    cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
    
    # Draw text
    cv2.putText(
        annotated,
        label_text,
        (text_x + 2, text_y - 2),
        font,
        font_scale,
        (0, 255, 0),
        thickness
    )
    
    return annotated


def get_desktop_path() -> Path:
    """
    Get the Desktop directory path.
    
    Returns:
        Path object pointing to the Desktop directory
    """
    return Path.home() / "Desktop"

