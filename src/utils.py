import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pyautogui


def capture_screenshot(save_path: Optional[str] = None) -> np.ndarray:
    screenshot = pyautogui.screenshot()
    if save_path:
        screenshot.save(save_path)
    screenshot_np = np.array(screenshot)
    return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)


def ensure_directory(path: str) -> Path:
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def handle_existing_file(filepath: str) -> str:
    path = Path(filepath)
    if path.exists():
        timestamp = int(time.time())
        return str(path.parent / f"{path.stem}_{timestamp}{path.suffix}")
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
    annotated = image.copy()
    x1, y1 = max(0, x - width // 2), max(0, y - height // 2)
    x2, y2 = min(image.shape[1], x + width // 2), min(image.shape[0], y + height // 2)

    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.circle(annotated, (x, y), 5, (0, 0, 255), -1)

    label_text = f"{label} ({confidence:.2f})" if confidence else label
    font, font_scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    (text_w, text_h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)

    text_y = y1 - text_h - 10 if y1 - text_h - 10 > 0 else y2 + text_h + 10
    overlay = annotated.copy()
    cv2.rectangle(overlay, (x1, text_y - text_h - 5), (x1 + text_w + 5, text_y + 5), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
    cv2.putText(annotated, label_text, (x1 + 2, text_y - 2), font, font_scale, (0, 255, 0), thickness)

    return annotated


def get_desktop_path() -> Path:
    return Path.home() / "Desktop"


def save_candidate_screenshots(screenshot: np.ndarray, candidates: list) -> None:
    import logging
    logger = logging.getLogger(__name__)

    try:
        candidates_dir = Path.home() / "Desktop" / "tjm-project" / "detection_screenshots" / "candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)

        for idx, candidate in enumerate(candidates, start=1):
            annotated = annotate_screenshot(
                screenshot,
                candidate['x'],
                candidate['y'],
                width=60,
                height=60,
                label=f"Candidate {idx}: {candidate['text']}",
                confidence=candidate['score']
            )
            cv2.imwrite(str(candidates_dir / f"candidate{idx}.png"), annotated)
    except Exception as e:
        logger.warning(f"Failed to save candidate screenshots: {e}")

