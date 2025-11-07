"""Icon detection module using template matching and OCR fallback."""

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
    """Detects desktop icons using template matching with OCR fallback."""
    
    def __init__(
        self,
        template_path: Optional[Path] = None,
        confidence_threshold: float = TEMPLATE_MATCH_THRESHOLD
    ):
        """
        Initialize the icon detector.
        
        Args:
            template_path: Path to the icon template image. If None, uses default path.
            confidence_threshold: Minimum confidence for template matching (0.0-1.0)
        """
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
        """
        Detect icon position on desktop using template matching.
        
        Args:
            screenshot: Optional screenshot image. If None, captures a new one.
            use_ocr_fallback: Whether to use OCR if template matching fails
            
        Returns:
            Tuple of (x, y, confidence) where x,y are center coordinates.
            Returns (None, None, 0.0) if detection fails.
        """
        if screenshot is None:
            screenshot = capture_screenshot()
        
        if self.template_gray is None:
            logger.error("Template not loaded. Cannot perform detection.")
            if use_ocr_fallback:
                return self._detect_with_ocr(screenshot)
            return None, None, 0.0
        
        # Try template matching first
        x, y, confidence = self._detect_with_template_matching(screenshot)
        
        if confidence >= self.confidence_threshold:
            logger.info(f"Icon detected at ({x}, {y}) with confidence {confidence:.2f}")
            return x, y, confidence
        
        # Fallback to OCR if template matching failed
        if use_ocr_fallback:
            logger.info("Template matching failed, trying OCR fallback...")
            return self._detect_with_ocr(screenshot)
        
        logger.warning(f"Detection failed. Confidence: {confidence:.2f} < threshold: {self.confidence_threshold}")
        return None, None, confidence
    
    def _detect_with_template_matching(
        self,
        screenshot: np.ndarray
    ) -> Tuple[Optional[int], Optional[int], float]:
        """
        Detect icon using template matching with multi-scale support.
        
        Args:
            screenshot: Screenshot image in BGR format
            
        Returns:
            Tuple of (x, y, confidence)
        """
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
    
    def _detect_with_ocr(
        self,
        screenshot: np.ndarray
    ) -> Tuple[Optional[int], Optional[int], float]:
        """
        Detect icon using OCR to find "Notepad" text label.
        
        Args:
            screenshot: Screenshot image in BGR format
            
        Returns:
            Tuple of (x, y, confidence). Confidence is lower for OCR method.
        """
        try:
            # Check if Tesseract is available
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                logger.warning("Tesseract OCR not found. OCR fallback unavailable.")
                logger.info("Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
                return None, None, 0.0
            # Convert to PIL Image for pytesseract
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(screenshot_rgb)
            
            # Use OCR to find text
            # Get detailed data including bounding boxes
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            # Search for "Notepad" text
            text_found = False
            x_coords = []
            y_coords = []
            
            for i, text in enumerate(ocr_data.get('text', [])):
                if 'notepad' in text.lower():
                    text_found = True
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # Icon is typically above the text label
                    # Estimate icon position (text is usually below icon)
                    icon_x = x + w // 2
                    icon_y = y - 30  # Approximate icon position above text
                    
                    x_coords.append(icon_x)
                    y_coords.append(icon_y)
            
            if text_found and x_coords:
                # Use the first match (or could average multiple matches)
                avg_x = int(sum(x_coords) / len(x_coords))
                avg_y = int(sum(y_coords) / len(y_coords))
                
                # OCR confidence is lower, so we return a moderate value
                logger.info(f"Icon detected via OCR at ({avg_x}, {avg_y})")
                return avg_x, avg_y, 0.6
            
            logger.warning("OCR did not find 'Notepad' text on desktop")
            return None, None, 0.0
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return None, None, 0.0
    
    def detect_with_retry(
        self,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY
    ) -> Tuple[Optional[int], Optional[int], float]:
        """
        Detect icon with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Tuple of (x, y, confidence)
        """
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
        """
        Validate that detection result is acceptable.
        
        Args:
            x: X coordinate
            y: Y coordinate
            confidence: Detection confidence score
            
        Returns:
            True if detection is valid, False otherwise
        """
        if x is None or y is None:
            return False
        
        if confidence < self.confidence_threshold:
            return False
        
        # Basic bounds checking (assuming 1920x1080 resolution)
        if x < 0 or x > 1920 or y < 0 or y > 1080:
            logger.warning(f"Detected coordinates ({x}, {y}) are out of bounds")
            return False
        
        return True


def capture_icon_template(output_path: Optional[Path] = None) -> Path:
    """
    Interactive utility to capture icon template from desktop.
    
    This function displays instructions and allows the user to select
    a region containing the Notepad icon.
    
    Args:
        output_path: Path to save the captured template. If None, uses default.
        
    Returns:
        Path to the saved template image
    """
    if output_path is None:
        output_path = ICON_TEMPLATE_PATH
    
    # Ensure assets directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("ICON TEMPLATE CAPTURE UTILITY")
    print("="*60)
    print("\nInstructions:")
    print("1. Make sure the Notepad icon is visible on your desktop")
    print("2. A screenshot will be taken in 3 seconds")
    print("3. You will need to manually crop the icon region")
    print("\nPress Enter to continue...")
    input()
    
    print("\nTaking screenshot in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    from .utils import capture_screenshot
    
    screenshot = capture_screenshot()
    screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(screenshot_rgb)
    
    # Save full screenshot for manual cropping
    temp_screenshot_path = output_path.parent / "desktop_screenshot.png"
    pil_image.save(temp_screenshot_path)
    
    print(f"\nScreenshot saved to: {temp_screenshot_path}")
    print("\nPlease:")
    print("1. Open the screenshot in an image editor")
    print("2. Crop the Notepad icon (include some padding around it)")
    print("3. Save the cropped image as 'notepad_icon.png' in the assets folder")
    print(f"4. Expected path: {output_path}")
    print("\nAlternatively, you can use a screenshot tool to capture just the icon.")
    print("\nOnce the template is saved, press Enter to continue...")
    input()
    
    if output_path.exists():
        print(f"\nTemplate found at {output_path}")
        return output_path
    else:
        print(f"\nWarning: Template not found at {output_path}")
        print("You can manually place the icon template there.")
        return output_path

