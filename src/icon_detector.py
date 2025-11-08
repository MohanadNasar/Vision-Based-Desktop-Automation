import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image

from .utils import capture_screenshot

logger = logging.getLogger(__name__)

ICON_TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "notepad_icon.png"


class IconDetector:
    def __init__(self, template_path: Optional[Path] = None, confidence_threshold: float = 0.7):
        self.template_path = template_path or ICON_TEMPLATE_PATH
        self.confidence_threshold = confidence_threshold
        self.template_gray = None

        if self.template_path.exists():
            template = cv2.imread(str(self.template_path))
            if template is not None:
                self.template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    def detect_icon_position(
        self,
        screenshot: Optional[np.ndarray] = None,
        use_ocr_fallback: bool = True
    ) -> Tuple[Optional[int], Optional[int], float]:
        if screenshot is None:
            screenshot = capture_screenshot()

        if self.template_gray is not None:
            x, y, confidence = self._detect_with_template_matching(screenshot)
            if confidence >= self.confidence_threshold:
                return x, y, confidence

        if use_ocr_fallback:
            return self._detect_with_ocr(screenshot)

        return None, None, 0.0
    
    def _detect_with_template_matching(self, screenshot: np.ndarray) -> Tuple[Optional[int], Optional[int], float]:
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        best_match, best_confidence, best_scale = None, 0.0, 1.0

        for scale in [0.8, 1.0, 1.2, 1.5]:
            width, height = int(self.template_gray.shape[1] * scale), int(self.template_gray.shape[0] * scale)
            if width > screenshot_gray.shape[1] or height > screenshot_gray.shape[0]:
                continue

            resized_template = cv2.resize(self.template_gray, (width, height))
            result = cv2.matchTemplate(screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_confidence:
                best_confidence, best_match, best_scale = max_val, max_loc, scale

        if best_match and best_confidence >= self.confidence_threshold:
            template_w = int(self.template_gray.shape[1] * best_scale)
            template_h = int(self.template_gray.shape[0] * best_scale)
            return best_match[0] + template_w // 2, best_match[1] + template_h // 2, best_confidence

        return None, None, best_confidence
    
    def _calculate_similarity_to_notepad(self, text: str) -> float:
        text_lower = text.strip().lower()
        target = "notepad"

        if text_lower == target:
            return 1.0
        if text_lower.startswith(target):
            return min(0.8 + (0.2 * len(target) / len(text_lower)), 1.0)
        if target in text_lower:
            idx = text_lower.find(target)
            is_word_start = idx == 0 or not text_lower[idx - 1].isalnum()
            is_word_end = idx + len(target) >= len(text_lower) or not text_lower[idx + len(target)].isalnum()
            ratio = len(target) / len(text_lower)
            return (0.6 + 0.2 * ratio) if (is_word_start and is_word_end) else (0.4 + 0.2 * ratio)
        return 0.0
    
    def _detect_with_ocr(self, screenshot: np.ndarray) -> Tuple[Optional[int], Optional[int], float]:
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            logger.error("Tesseract OCR not found")
            return None, None, 0.0

        try:
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(screenshot_rgb)
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT, config='--psm 6')

            candidates = []
            for i, text in enumerate(ocr_data.get('text', [])):
                text_clean = text.strip()
                if not text_clean:
                    continue

                similarity = self._calculate_similarity_to_notepad(text_clean)
                if similarity > 0.0:
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    ocr_conf = ocr_data.get('conf', [0])[i] if 'conf' in ocr_data else 0
                    icon_x = x + w // 2
                    icon_y = int(y - max(h * 1.5, 40) / 2)
                    combined_score = (similarity * 0.7) + ((ocr_conf / 100.0) * 0.3)
                    candidates.append({'x': icon_x, 'y': icon_y, 'combined_score': combined_score})

            if not candidates:
                return None, None, 0.0

            best_match = max(candidates, key=lambda c: c['combined_score'])
            return best_match['x'], best_match['y'], min(best_match['combined_score'], 0.9)

        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return None, None, 0.0
    
    def detect_with_retry(self, max_retries: int = 3, retry_delay: float = 1.0) -> Tuple[Optional[int], Optional[int], float]:
        for attempt in range(max_retries):
            x, y, confidence = self.detect_icon_position()
            if x is not None and y is not None:
                return x, y, confidence
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        return None, None, 0.0

    def validate_icon_detection(self, x: int, y: int, confidence: float) -> bool:
        if x is None or y is None or confidence < self.confidence_threshold:
            return False
        if x < 0 or x > 1920 or y < 0 or y > 1080:
            return False
        return True


def capture_icon_template(output_path: Optional[Path] = None) -> Path:
    output_path = output_path or ICON_TEMPLATE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("ICON TEMPLATE CAPTURE")
    print("="*60)
    print("\n1. Make sure Notepad icon is visible")
    print("2. Screenshot in 3 seconds")
    print("3. Manually crop the icon\n")
    input("Press Enter to continue...")

    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    screenshot = capture_screenshot()
    pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
    temp_path = output_path.parent / "desktop_screenshot.png"
    pil_image.save(temp_path)

    print(f"\nScreenshot saved: {temp_path}")
    print(f"Crop and save as: {output_path}\n")
    input("Press Enter when done...")

    return output_path

