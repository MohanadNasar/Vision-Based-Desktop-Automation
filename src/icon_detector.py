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

# Detection configuration
TEMPLATE_MATCH_THRESHOLD = 0.7
MAX_RETRIES = 3
RETRY_DELAY = 1.0
ICON_TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "notepad_icon.png"


class IconDetector:
    
    def __init__(
        self,
        template_path: Optional[Path] = None,
        confidence_threshold: float = TEMPLATE_MATCH_THRESHOLD
    ):
        self.template_path = template_path or ICON_TEMPLATE_PATH
        self.confidence_threshold = confidence_threshold
        self.template = None
        self.template_gray = None
        
        if self.template_path.exists():
            self._load_template()
        else:
            logger.warning(f"Template not found at {self.template_path}")
    
    def _load_template(self) -> None:
        """Load and preprocess the icon template."""
        try:
            self.template = cv2.imread(str(self.template_path))
            if self.template is None:
                raise ValueError(f"Could not load template from {self.template_path}")
            
            self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
            logger.info(f"Template loaded successfully: {self.template_gray.shape}")
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            raise
    
    def detect_icon_position(
        self,
        screenshot: Optional[np.ndarray] = None,
        use_ocr_fallback: bool = True
    ) -> Tuple[Optional[int], Optional[int], float]:
        
        if screenshot is None:
            screenshot = capture_screenshot()
        
        confidence = 0.0
        
        # Try template matching first (primary method) if template exists
        if self.template_gray is not None:
            logger.info("Attempting template matching detection...")
            x, y, confidence = self._detect_with_template_matching(screenshot)
            
            if confidence >= self.confidence_threshold:
                logger.info(f"Icon detected via template matching at ({x}, {y}) with confidence {confidence:.2f}")
                return x, y, confidence
            else:
                logger.warning(f"Template matching failed. Confidence: {confidence:.2f} < threshold: {self.confidence_threshold}")
        else:
            logger.info("No template found in assets. Skipping template matching.")
            x, y = None, None
        
        # Fallback to OCR if template matching failed or no template exists
        if use_ocr_fallback:
            if self.template_gray is None:
                logger.info("Falling back to OCR detection (no template available)...")
            else:
                logger.info("Falling back to OCR detection (template matching failed)...")
            
            x, y, confidence = self._detect_with_ocr(screenshot)
            
            if x is not None and y is not None:
                logger.info(f"Icon detected via OCR at ({x}, {y}) with confidence {confidence:.2f}")
                return x, y, confidence
            else:
                logger.warning("OCR detection also failed.")
        else:
            logger.warning("OCR fallback is disabled. Detection failed.")
        
        return None, None, confidence
    
    def _detect_with_template_matching(
        self,
        screenshot: np.ndarray
    ) -> Tuple[Optional[int], Optional[int], float]:
        
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        best_match = None
        best_confidence = 0.0
        best_scale = 1.0  # Default scale
        
        # Multi-scale template matching to handle different icon sizes
        scales = [0.8, 1.0, 1.2, 1.5]
        
        for scale in scales:
            # Resize template
            width = int(self.template_gray.shape[1] * scale)
            height = int(self.template_gray.shape[0] * scale)
            
            if width > screenshot_gray.shape[1] or height > screenshot_gray.shape[0]:
                continue
            
            resized_template = cv2.resize(self.template_gray, (width, height))
            
            # Perform template matching
            result = cv2.matchTemplate(
                screenshot_gray,
                resized_template,
                cv2.TM_CCOEFF_NORMED
            )
            
            # Find best match
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_match = max_loc
                best_scale = scale
        
        if best_match and best_confidence >= self.confidence_threshold:
            # Calculate center coordinates
            template_w = int(self.template_gray.shape[1] * best_scale)
            template_h = int(self.template_gray.shape[0] * best_scale)
            
            x = best_match[0] + template_w // 2
            y = best_match[1] + template_h // 2
            
            return x, y, best_confidence
        
        return None, None, best_confidence
    
    def _calculate_similarity_to_notepad(self, text: str) -> float:
        text_lower = text.strip().lower()
        target = "notepad"
        
        if text_lower == target:
            return 1.0
        
        if text_lower.startswith(target):
            notepad_ratio = len(target) / len(text_lower)
            return min(0.8 + (0.2 * notepad_ratio), 1.0)
        
        if target in text_lower:
            idx = text_lower.find(target)
            is_word_start = (idx == 0 or not text_lower[idx - 1].isalnum())
            is_word_end = (idx + len(target) >= len(text_lower) or 
                          not text_lower[idx + len(target)].isalnum())
            
            if is_word_start and is_word_end:
                notepad_ratio = len(target) / len(text_lower)
                return 0.6 + (0.2 * notepad_ratio)
            else:
                # "notepad" is part of another word
                return 0.4 + (0.2 * notepad_ratio)
        
        # No match
        return 0.0
    
    def _detect_with_ocr(
        self,
        screenshot: np.ndarray
    ) -> Tuple[Optional[int], Optional[int], float]:
        try:
            # Check if Tesseract is available
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                logger.error("Tesseract OCR not found. OCR is required for detection.")
                logger.info("Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
                return None, None, 0.0
            
            # Preprocess image to improve OCR accuracy
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

            # Reduce noise while preserving edges
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)

            # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast_enhanced = clahe.apply(denoised)

            # Apply binary thresholding to make text stand out
            # Use Otsu's method for automatic threshold determination
            _, binary = cv2.threshold(contrast_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Convert to PIL Image for pytesseract
            pil_image = Image.fromarray(binary)

            # Use OCR to find text with detailed data including bounding boxes
            # PSM 6: Assume a single uniform block of text
            ocr_data = pytesseract.image_to_data(
                pil_image,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Uniform block of text (works well for desktop icons)
            )

            # Debug: log all detected text
            all_text = [text.strip() for text in ocr_data.get('text', []) if text.strip()]
            if all_text:
                logger.info(f"OCR detected {len(all_text)} text elements: {all_text}")
            else:
                logger.warning("OCR detected no text on screen")

            # Find all text containing "notepad" and score them
            candidates = []

            for i, text in enumerate(ocr_data.get('text', [])):
                text_clean = text.strip()
                if not text_clean:
                    continue
                
                # Calculate similarity to "Notepad"
                similarity = self._calculate_similarity_to_notepad(text_clean)
                
                if similarity > 0.0:  # Found a match
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    ocr_conf = ocr_data.get('conf', [0])[i] if 'conf' in ocr_data else 0

                    # Icon is typically above the text label
                    icon_x = x + w // 2  # Center horizontally with text
                    icon_height_estimate = max(h * 1.5, 40)  # At least 40 pixels or 1.5x text height
                    icon_y = int(y - icon_height_estimate / 2)  # Center of icon above text

                    # Combined score: similarity to "Notepad" weighted with OCR confidence
                    combined_score = (similarity * 0.7) + ((ocr_conf / 100.0) * 0.3)

                    candidates.append({
                        'text': text_clean,
                        'x': icon_x,
                        'y': icon_y,
                        'similarity': similarity,
                        'ocr_conf': ocr_conf,
                        'combined_score': combined_score
                    })

                    logger.info(f"Found candidate '{text_clean}' at text_pos=({x}, {y}), icon_pos=({icon_x}, {icon_y}) - similarity: {similarity:.2f}, OCR conf: {ocr_conf:.1f}%")
            
            if not candidates:
                logger.warning("OCR did not find any text containing 'Notepad' on desktop")
                return None, None, 0.0
            
            # Select the candidate with the highest combined score (closest to "Notepad")
            best_match = max(candidates, key=lambda c: c['combined_score'])
            
            logger.info(f"Best match: '{best_match['text']}' at ({best_match['x']}, {best_match['y']}) "
                       f"- similarity: {best_match['similarity']:.2f}, OCR conf: {best_match['ocr_conf']:.1f}%")
            
            # Normalize confidence (use combined score, capped at 0.9 for OCR)
            normalized_conf = min(best_match['combined_score'], 0.9)
            
            return best_match['x'], best_match['y'], normalized_conf
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return None, None, 0.0
    
    def detect_with_retry(
        self,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY
    ) -> Tuple[Optional[int], Optional[int], float]:
        
        for attempt in range(max_retries):
            logger.info(f"Detection attempt {attempt + 1}/{max_retries}")
            
            x, y, confidence = self.detect_icon_position()
            
            if x is not None and y is not None:
                return x, y, confidence
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        logger.error(f"Failed to detect icon after {max_retries} attempts")
        return None, None, 0.0
    
    def validate_icon_detection(self, x: int, y: int, confidence: float) -> bool:

        if x is None or y is None:
            return False
        
        if confidence < self.confidence_threshold:
            return False
        
        if x < 0 or x > 1920 or y < 0 or y > 1080:
            logger.warning(f"Detected coordinates ({x}, {y}) are out of bounds")
            return False
        
        return True
