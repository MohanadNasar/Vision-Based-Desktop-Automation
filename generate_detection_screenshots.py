"""Script to generate annotated screenshots showing icon detection in different positions."""

import logging
import sys
from pathlib import Path

import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.icon_detector import IconDetector
from src.utils import annotate_screenshot, capture_screenshot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def generate_screenshot(position_name: str, description: str) -> bool:
    """
    Generate an annotated screenshot for a specific icon position.
    
    Args:
        position_name: Name for the output file (e.g., "top_left")
        description: Description of the position
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Generating screenshot: {position_name}")
    logger.info(f"Description: {description}")
    logger.info(f"{'='*60}")
    
    print(f"\nPlease move the Notepad icon to the {description} area of your desktop.")
    print("Press Enter when ready to capture...")
    input()
    
    try:
        # Initialize detector
        detector = IconDetector()
        
        # Capture screenshot
        logger.info("Capturing screenshot...")
        screenshot = capture_screenshot()
        
        # Detect icon
        logger.info("Detecting icon...")
        x, y, confidence = detector.detect_icon_position(screenshot)
        
        if x is None or y is None:
            logger.error(f"Failed to detect icon for {position_name}")
            print(f"\n❌ Could not detect icon. Please try again.")
            return False
        
        # Annotate screenshot
        logger.info(f"Icon detected at ({x}, {y}) with confidence {confidence:.2f}")
        annotated = annotate_screenshot(
            screenshot,
            x, y,
            width=50,
            height=50,
            label="Notepad Icon",
            confidence=confidence
        )
        
        # Save annotated screenshot
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"detection_{position_name}.png"
        cv2.imwrite(str(output_path), annotated)
        
        logger.info(f"✓ Screenshot saved to: {output_path}")
        print(f"\n✓ Screenshot saved: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating screenshot: {e}")
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Generate all required detection screenshots."""
    print("\n" + "="*60)
    print("DETECTION SCREENSHOT GENERATOR")
    print("="*60)
    print("\nThis script will help you generate annotated screenshots")
    print("showing icon detection in different desktop positions.")
    print("\nYou will be prompted to move the Notepad icon to different")
    print("locations on your desktop.")
    
    # Check if template exists
    template_path = Path(__file__).parent / "assets" / "notepad_icon.png"
    if not template_path.exists():
        print(f"\n❌ Error: Icon template not found at {template_path}")
        print("Please run the main application first to capture the icon template.")
        sys.exit(1)
    
    positions = [
        ("top_left", "top-left"),
        ("center", "center"),
        ("bottom_right", "bottom-right"),
    ]
    
    successful = 0
    for position_name, description in positions:
        if generate_screenshot(position_name, description):
            successful += 1
        
        if position_name != positions[-1][0]:
            print("\n" + "-"*60)
    
    print("\n" + "="*60)
    print("SCREENSHOT GENERATION COMPLETE")
    print("="*60)
    print(f"Successfully generated: {successful}/{len(positions)} screenshots")
    print(f"Output directory: {Path(__file__).parent / 'output'}")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)

