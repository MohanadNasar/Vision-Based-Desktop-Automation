"""Basic tests for icon detection functionality."""

import unittest
from pathlib import Path

from src.icon_detector import IconDetector


class TestIconDetector(unittest.TestCase):
    """Test cases for IconDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.template_path = Path(__file__).parent.parent / "assets" / "notepad_icon.png"
        self.detector = IconDetector(template_path=self.template_path)
    
    def test_detector_initialization(self):
        """Test that detector initializes correctly."""
        if self.template_path.exists():
            self.assertIsNotNone(self.detector)
        else:
            self.skipTest("Icon template not found")
    
    def test_template_loading(self):
        """Test template loading."""
        if self.template_path.exists():
            self.assertIsNotNone(self.detector.template)
            self.assertIsNotNone(self.detector.template_gray)
        else:
            self.skipTest("Icon template not found")
    
    def test_validation(self):
        """Test detection validation."""
        # Valid detection
        self.assertTrue(self.detector.validate_icon_detection(960, 540, 0.8))
        
        # Invalid: None coordinates
        self.assertFalse(self.detector.validate_icon_detection(None, 540, 0.8))
        
        # Invalid: Low confidence
        self.assertFalse(self.detector.validate_icon_detection(960, 540, 0.5))
        
        # Invalid: Out of bounds
        self.assertFalse(self.detector.validate_icon_detection(3000, 540, 0.8))


if __name__ == "__main__":
    unittest.main()

