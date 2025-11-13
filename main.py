import logging
import sys
import time
import pyautogui
import cv2

from src.api_client import fetch_posts, format_post_content, validate_post
from src.automation import (
    close_notepad,
    ensure_notepad_closed,
    launch_notepad,
    save_file,
    type_text,
    wait_before_next_iteration,
)
from src.icon_detector import IconDetector
from src.utils import annotate_screenshot, capture_screenshot, ensure_directory, get_desktop_path

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
    logger.info("="*60)
    logger.info("Vision-Based Desktop Automation - Starting")
    logger.info("="*60)

    # Minimize editor
    pyautogui.hotkey('win', 'd')
    time.sleep(0.5)

    # Step 1: Initialize detector
    try:
        detector = IconDetector()
        logger.info("Icon detector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize icon detector: {e}")
        sys.exit(1)

    # Step 2: Fetch posts from API
    try:
        posts = fetch_posts(limit=10)
        logger.info(f"Fetched {len(posts)} posts")
    except Exception as e:
        logger.error(f"Failed to fetch posts: {e}")
        sys.exit(1)

    # Step 3: Validate posts
    valid_posts = [post for post in posts if validate_post(post)]
    if len(valid_posts) < len(posts):
        logger.warning(f"Some posts were invalid. Using {len(valid_posts)} valid posts")

    if not valid_posts:
        logger.error("No valid posts to process")
        sys.exit(1)

    # Step 4: Set up output directories
    desktop_path = get_desktop_path()
    output_dir = desktop_path / "tjm-project"
    ensure_directory(str(output_dir))

    screenshots_dir = output_dir / "detection_screenshots"
    ensure_directory(str(screenshots_dir))

    logger.info(f"Output directory: {output_dir}")

    # Step 5: Process each post
    successful_saves = 0
    failed_saves = 0

    for i, post in enumerate(valid_posts, 1):
        logger.info("\n" + "-"*60)
        logger.info(f"Processing post {i}/{len(valid_posts)} (ID: {post['id']})")
        logger.info("-"*60)

        try:
            # Capture desktop screenshot
            screenshot = capture_screenshot()

            # Detect Notepad icon
            x, y, confidence = detector.detect_with_retry(max_retries=3, retry_delay=1.0)

            if not detector.validate_icon_detection(x, y, confidence):
                logger.error(f"Failed to detect icon for post {post['id']}")
                failed_saves += 1
                continue

            # Save annotated screenshot
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
            logger.info(f"Screenshot saved: {screenshot_path}")

            # Launch Notepad
            if not launch_notepad(x, y, timeout=5.0):
                logger.error(f"Failed to launch Notepad for post {post['id']}")
                failed_saves += 1
                ensure_notepad_closed()
                continue

            # Type post content
            try:
                content = format_post_content(post)
                type_text(content)
            except Exception as e:
                logger.error(f"Error typing content: {e}")
                close_notepad()
                failed_saves += 1
                continue

            # Save file (will overwrite if exists)
            filename = f"post_{post['id']}.txt"
            filepath = output_dir / filename

            if filepath.exists():
                logger.info(f"File will be overwritten: {filepath}")

            if not save_file(filename, str(output_dir)):
                logger.error(f"Failed to save file for post {post['id']}")
                close_notepad()
                ensure_notepad_closed()
                failed_saves += 1
                continue

            successful_saves += 1
            logger.info(f"Successfully saved post {post['id']}")

            # Close Notepad
            close_notepad()
            time.sleep(1.0)

            # Wait before next iteration
            if i < len(valid_posts):
                logger.info(f"Completed post {i}/{len(valid_posts)}")
                wait_before_next_iteration(delay=0.5)

        except KeyboardInterrupt:
            logger.info("\nProcess interrupted by user")
            ensure_notepad_closed()
            break
        except Exception as e:
            logger.error(f"Unexpected error processing post {post['id']}: {e}")
            ensure_notepad_closed()
            failed_saves += 1
            continue

    # Step 6: Summary
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
