import logging
import time
from pathlib import Path

import cv2
import pytesseract
from PIL import Image

from .utils import capture_screenshot, save_candidate_screenshots

logger = logging.getLogger(__name__)

TEMPLATE_MATCH_THRESHOLD = 0.7
MAX_RETRIES = 3
RETRY_DELAY = 1.0
ICON_TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "notepad_icon.png"


class IconDetector:

    def __init__(self, template_path=None, confidence_threshold=TEMPLATE_MATCH_THRESHOLD):
        self.template_path = template_path or ICON_TEMPLATE_PATH
        self.confidence_threshold = confidence_threshold
        self.template_gray = None

        if self.template_path.exists():
            template = cv2.imread(str(self.template_path))
            self.template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            logger.info(f"Template loaded: {self.template_gray.shape}")

    def detect_icon_position(self, screenshot=None, use_ocr_fallback=True):

        if screenshot is None:
            screenshot = capture_screenshot()

        # Try template matching first
        if self.template_gray is not None:
            x, y, confidence = self._detect_with_template_matching(screenshot)
            if confidence >= self.confidence_threshold:
                logger.info(f"Template match found at ({x}, {y}), conf={confidence:.2f}")
                return x, y, confidence

        # Fallback to OCR
        if use_ocr_fallback:
            logger.info("Using OCR fallback...")
            x, y, confidence = self._detect_with_ocr(screenshot)
            if x is not None:
                logger.info(f"OCR found at ({x}, {y}), conf={confidence:.2f}")
                return x, y, confidence

        return None, None, 0.0

    def _detect_with_template_matching(self, screenshot):

        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        best_match = None
        best_confidence = 0.0
        best_scale = 1.0

        # Multi-scale matching: 50% to 250% of template size
        scales = [0.5, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0, 2.5]

        for scale in scales:
            width = int(self.template_gray.shape[1] * scale)
            height = int(self.template_gray.shape[0] * scale)

            if width > screenshot_gray.shape[1] or height > screenshot_gray.shape[0]:
                continue

            resized_template = cv2.resize(self.template_gray, (width, height))
            result = cv2.matchTemplate(screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_confidence:
                best_confidence = max_val
                best_match = max_loc
                best_scale = scale

        if best_match and best_confidence >= self.confidence_threshold:
            template_w = int(self.template_gray.shape[1] * best_scale)
            template_h = int(self.template_gray.shape[0] * best_scale)
            x = best_match[0] + template_w // 2
            y = best_match[1] + template_h // 2
            return x, y, best_confidence

        return None, None, best_confidence

    def _calculate_similarity_to_notepad(self, text):
        text_lower = text.strip().lower()
        target = "notepad"

        if text_lower == target:
            return 1.0

        if text_lower.startswith(target):
            notepad_ratio = len(target) / len(text_lower)
            return 0.6 + (0.2 * notepad_ratio)

        if target in text_lower:
            idx = text_lower.find(target)
            is_word_start = (idx == 0 or not text_lower[idx - 1].isalnum())
            is_word_end = (idx + len(target) >= len(text_lower) or not text_lower[idx + len(target)].isalnum())

            if is_word_start and is_word_end:
                return 0.6
            else:
                return 0.4

        return 0.0

    def _detect_with_ocr(self, screenshot):
        try:
            pytesseract.get_tesseract_version()
        except:
            logger.error("Tesseract OCR not found")
            return None, None, 0.0

        # Preprocess for OCR
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)  # Reduce noise
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # Increase contrast
        contrast = clahe.apply(denoised)
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Binary threshold

        # Run OCR with PSM 11 (sparse text - works best for desktop icons)
        pil_image = Image.fromarray(binary)
        try:
            ocr_data = pytesseract.image_to_data(
                pil_image,
                output_type=pytesseract.Output.DICT,
                config='--psm 11'
            )
            all_text = [t.strip() for t in ocr_data.get('text', []) if t.strip()]
            logger.info(f"OCR detected {len(all_text)} texts")
        except:
            return None, None, 0.0

        # Find and score "notepad" matches
        candidates = []
        for i, text in enumerate(ocr_data.get('text', [])):
            text_clean = text.strip()
            if not text_clean:
                continue

            similarity = self._calculate_similarity_to_notepad(text_clean)
            if similarity > 0.0:
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                ocr_conf = ocr_data.get('conf', [0])[i] if 'conf' in ocr_data else 0

                # Icon is above text label
                icon_x = x + w // 2
                icon_y = int(y - max(h * 1.5, 40) / 2)

                # Combined score: similarity weighted with OCR confidence
                combined_score = (similarity * 0.9) + ((ocr_conf / 100.0) * 0.1)
                candidates.append({
                    'text': text_clean,
                    'x': icon_x,
                    'y': icon_y,
                    'score': combined_score
                })

        if not candidates:
            return None, None, 0.0

        save_candidate_screenshots(screenshot, candidates)

        best = max(candidates, key=lambda c: c['score'])
        logger.info(f"Best: '{best['text']}' at ({best['x']}, {best['y']})")
        return best['x'], best['y'], min(best['score'], 0.9)

    def detect_with_retry(self, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):

        for attempt in range(max_retries):
            logger.info(f"Detection attempt {attempt + 1}/{max_retries}")
            x, y, confidence = self.detect_icon_position()

            if x is not None:
                return x, y, confidence

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        logger.error(f"Failed after {max_retries} attempts")
        return None, None, 0.0

    def validate_icon_detection(self, x, y, confidence):
        if x is None or y is None:
            return False
        if confidence < self.confidence_threshold:
            return False
        if x < 0 or x > 1920 or y < 0 or y > 1080:
            return False
        return True
