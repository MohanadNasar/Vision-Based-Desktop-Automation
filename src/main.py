"""Main application entry point for vision-based desktop automation."""

import logging
import sys
import time
import pyautogui
from pathlib import Path

from .api_client import fetch_posts, format_post_content, validate_post
from .automation import (
    close_notepad,
    ensure_notepad_closed,
    launch_notepad,
    save_file,
    type_text,
    wait_before_next_iteration,
)
from .icon_detector import IconDetector
from .utils import annotate_screenshot, capture_screenshot, ensure_directory, get_desktop_path, handle_existing_file
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation.log')
    ]
)

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True

def main():
    """Main application workflow."""
    logger.info("="*60)
    logger.info("Vision-Based Desktop Automation - Starting")
    logger.info("="*60)
    
    # Step 1: Initialize detector
    try:
        detector = IconDetector()
        logger.info("Icon detector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize icon detector: {e}")
        sys.exit(1)
    
    # Step 2: Fetch posts from API
    try:
        logger.info("Fetching posts from JSONPlaceholder API...")
        posts = fetch_posts(limit=10)
        logger.info(f"Successfully fetched {len(posts)} posts")
    except Exception as e:
        logger.error(f"Failed to fetch posts: {e}")
        print("\nError: Could not fetch posts from API.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    # Step 3: Validate posts
    valid_posts = [post for post in posts if validate_post(post)]
    if len(valid_posts) < len(posts):
        logger.warning(f"Some posts were invalid. Using {len(valid_posts)} valid posts.")
    
    if not valid_posts:
        logger.error("No valid posts to process")
        sys.exit(1)
    
    # Step 6: Set up output directory
    desktop_path = get_desktop_path()
    output_dir = desktop_path / "tjm-project"
    ensure_directory(str(output_dir))

    # Create screenshots subdirectory
    screenshots_dir = output_dir / "detection_screenshots"
    ensure_directory(str(screenshots_dir))

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Screenshots directory: {screenshots_dir}")
    
    # Step 7: Process each post
    successful_saves = 0
    failed_saves = 0
    
    for i, post in enumerate(valid_posts, 1):
        logger.info("\n" + "-"*60)
        logger.info(f"Processing post {i}/{len(valid_posts)} (ID: {post['id']})")
        logger.info("-"*60)
        
        try:
            # 7a. Capture fresh desktop screenshot
            logger.info("Capturing desktop screenshot...")
            screenshot = capture_screenshot()

            # 7b. Detect Notepad icon position (with retry logic)
            logger.info("Detecting Notepad icon...")
            x, y, confidence = detector.detect_with_retry(max_retries=3, retry_delay=1.0)

            if not detector.validate_icon_detection(x, y, confidence):
                logger.error(f"Failed to detect icon for post {post['id']}")
                failed_saves += 1
                continue

            # 7b2. Save annotated screenshot showing detected icon
            logger.info("Saving annotated screenshot...")
            annotated = annotate_screenshot(
                screenshot,
                x, y,
                width=60,
                height=60,
                label="Notepad Icon",
                confidence=confidence
            )
            screenshot_filename = f"detection_post_{post['id']}.png"
            screenshot_path = screenshots_dir / screenshot_filename
            cv2.imwrite(str(screenshot_path), annotated)
            logger.info(f"Annotated screenshot saved: {screenshot_path}")
            
            # 7c. Launch Notepad
            logger.info(f"Launching Notepad from icon at ({x}, {y})...")
            if not launch_notepad(x, y, timeout=5.0):
                logger.error(f"Failed to launch Notepad for post {post['id']}")
                failed_saves += 1
                ensure_notepad_closed()
                continue
            
            # 7d. Type post content
            try:
                content = format_post_content(post)
                type_text(content)
            except Exception as e:
                logger.error(f"Error typing content: {e}")
                close_notepad()
                failed_saves += 1
                continue
            
            # 7e. Save file
            filename = f"post_{post['id']}.txt"
            filepath = output_dir / filename
            
            # Handle existing files
            if filepath.exists():
                logger.warning(f"File already exists: {filepath}")
                new_filepath = handle_existing_file(str(filepath))
                filename = Path(new_filepath).name
                logger.info(f"Using new filename: {filename}")
            
            if not save_file(filename, str(output_dir)):
                logger.error(f"Failed to save file for post {post['id']}")
                close_notepad()
                ensure_notepad_closed()
                failed_saves += 1
                continue
            
            successful_saves += 1
            logger.info(f"Successfully saved post {post['id']}")

            # 7f. Close Notepad
            close_notepad()
            time.sleep(1.0)  # Wait for window to close

            # 7g. Wait before next iteration
            if i < len(valid_posts):
                logger.info(f"Completed post {i}/{len(valid_posts)}. Preparing for next post...")
                wait_before_next_iteration(delay=1.5)
                
        except KeyboardInterrupt:
            logger.info("\nProcess interrupted by user")
            ensure_notepad_closed()
            break
        except Exception as e:
            logger.error(f"Unexpected error processing post {post['id']}: {e}")
            ensure_notepad_closed()
            failed_saves += 1
            continue
    
    # Step 8: Summary
    logger.info("\n" + "="*60)
    logger.info("AUTOMATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total posts processed: {len(valid_posts)}")
    logger.info(f"Successful saves: {successful_saves}")
    logger.info(f"Failed saves: {failed_saves}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*60)
    
    if successful_saves > 0:
        print(f"\n✓ Successfully saved {successful_saves} post(s) to:")
        print(f"  {output_dir}")
        print(f"\n✓ Annotated detection screenshots saved to:")
        print(f"  {screenshots_dir}")
        print(f"  Files named: detection_post_*.png")

    if failed_saves > 0:
        print(f"\n⚠ {failed_saves} post(s) failed to save. Check the log for details.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nApplication interrupted by user")
        ensure_notepad_closed()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        ensure_notepad_closed()
        sys.exit(1)

