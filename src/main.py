"""Main application entry point for vision-based desktop automation."""

import logging
import sys
import time
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
from .icon_detector import IconDetector, capture_icon_template
from .utils import ensure_directory, get_desktop_path, handle_existing_file

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


def check_icon_template() -> bool:
    """
    Check if icon template exists, prompt user to capture if not.
    
    Returns:
        True if template exists or was created, False otherwise
    """
    template_path = Path(__file__).parent.parent / "assets" / "notepad_icon.png"
    
    if template_path.exists():
        logger.info(f"Icon template found at {template_path}")
        return True
    
    logger.warning("Icon template not found!")
    print("\n" + "="*60)
    print("ICON TEMPLATE REQUIRED")
    print("="*60)
    print("\nThe Notepad icon template is required for detection.")
    print("You need to capture it before running the automation.")
    
    response = input("\nWould you like to capture it now? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            capture_icon_template()
            if template_path.exists():
                logger.info("Icon template captured successfully")
                return True
            else:
                logger.error("Icon template capture failed")
                return False
        except Exception as e:
            logger.error(f"Error capturing icon template: {e}")
            return False
    else:
        print("\nPlease manually place the Notepad icon template at:")
        print(f"  {template_path}")
        print("\nYou can use any image editor to crop the icon from a screenshot.")
        return False


def main():
    """Main application workflow."""
    logger.info("="*60)
    logger.info("Vision-Based Desktop Automation - Starting")
    logger.info("="*60)
    
    # Step 2: Initialize detector
    try:
        detector = IconDetector()
        logger.info("Icon detector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize icon detector: {e}")
        sys.exit(1)
    
    # Step 3: Fetch posts from API
    try:
        logger.info("Fetching posts from JSONPlaceholder API...")
        posts = fetch_posts(limit=10)
        logger.info(f"Successfully fetched {len(posts)} posts")
    except Exception as e:
        logger.error(f"Failed to fetch posts: {e}")
        print("\nError: Could not fetch posts from API.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    # Step 4: Validate posts
    valid_posts = [post for post in posts if validate_post(post)]
    if len(valid_posts) < len(posts):
        logger.warning(f"Some posts were invalid. Using {len(valid_posts)} valid posts.")
    
    if not valid_posts:
        logger.error("No valid posts to process")
        sys.exit(1)
    
    # Step 5: Set up output directory
    desktop_path = get_desktop_path()
    output_dir = desktop_path / "tjm-project"
    ensure_directory(str(output_dir))
    logger.info(f"Output directory: {output_dir}")
    
    # Step 6: Process each post
    successful_saves = 0
    failed_saves = 0
    
    for i, post in enumerate(valid_posts, 1):
        logger.info("\n" + "-"*60)
        logger.info(f"Processing post {i}/{len(valid_posts)} (ID: {post['id']})")
        logger.info("-"*60)
        
        try:
            # 6a. Capture fresh desktop screenshot
            logger.info("Capturing desktop screenshot...")
            from .utils import capture_screenshot
            screenshot = capture_screenshot()
            
            # 6b. Detect Notepad icon position (with retry logic)
            logger.info("Detecting Notepad icon...")
            x, y, confidence = detector.detect_with_retry(max_retries=3, retry_delay=1.0)
            
            if not detector.validate_icon_detection(x, y, confidence):
                logger.error(f"Failed to detect icon for post {post['id']}")
                failed_saves += 1
                continue
            
            # 6c. Launch Notepad
            logger.info(f"Launching Notepad from icon at ({x}, {y})...")
            if not launch_notepad(x, y, timeout=5.0):
                logger.error(f"Failed to launch Notepad for post {post['id']}")
                failed_saves += 1
                ensure_notepad_closed()
                continue
            
            # 6d. Type post content
            try:
                content = format_post_content(post)
                type_text(content)
            except Exception as e:
                logger.error(f"Error typing content: {e}")
                close_notepad()
                failed_saves += 1
                continue
            
            # 6e. Save file
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

            # 6f. Close Notepad
            close_notepad()
            time.sleep(1.0)  # Wait for window to close

            # 6g. Wait before next iteration
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
    
    # Step 7: Summary
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

