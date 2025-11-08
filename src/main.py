import logging
import sys
import time
from pathlib import Path

from .api_client import fetch_posts, format_post_content, validate_post
from .automation import close_notepad, ensure_notepad_closed, launch_notepad, save_file, type_text, wait_before_next_iteration
from .icon_detector import IconDetector
from .utils import annotate_screenshot, capture_screenshot, ensure_directory, get_desktop_path, handle_existing_file
import cv2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('automation.log')]
)

logger = logging.getLogger(__name__)


def main():
    logger.info("="*60)
    logger.info("Vision-Based Desktop Automation - Starting")
    logger.info("="*60)

    try:
        detector = IconDetector()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)

    try:
        posts = fetch_posts(limit=10)
        logger.info(f"Fetched {len(posts)} posts")
    except Exception as e:
        logger.error(f"Failed to fetch posts: {e}")
        sys.exit(1)

    valid_posts = [post for post in posts if validate_post(post)]
    if not valid_posts:
        logger.error("No valid posts")
        sys.exit(1)

    output_dir = get_desktop_path() / "tjm-project"
    screenshots_dir = output_dir / "detection_screenshots"
    ensure_directory(str(output_dir))
    ensure_directory(str(screenshots_dir))
    
    successful_saves = 0
    failed_saves = 0

    for i, post in enumerate(valid_posts, 1):
        logger.info(f"\nProcessing {i}/{len(valid_posts)} (ID: {post['id']})")

        try:
            screenshot = capture_screenshot()
            x, y, confidence = detector.detect_with_retry(max_retries=3, retry_delay=1.0)

            if not detector.validate_icon_detection(x, y, confidence):
                logger.error(f"Detection failed for post {post['id']}")
                failed_saves += 1
                continue

            annotated = annotate_screenshot(screenshot, x, y, width=60, height=60, label="Notepad", confidence=confidence)
            cv2.imwrite(str(screenshots_dir / f"detection_post_{post['id']}.png"), annotated)

            if not launch_notepad(x, y, timeout=5.0):
                logger.error(f"Launch failed for post {post['id']}")
                failed_saves += 1
                ensure_notepad_closed()
                continue

            try:
                type_text(format_post_content(post))
            except Exception as e:
                logger.error(f"Typing error: {e}")
                close_notepad()
                failed_saves += 1
                continue

            filename = f"post_{post['id']}.txt"
            filepath = output_dir / filename
            if filepath.exists():
                filename = Path(handle_existing_file(str(filepath))).name

            if not save_file(filename, str(output_dir)):
                logger.error(f"Save failed for post {post['id']}")
                close_notepad()
                ensure_notepad_closed()
                failed_saves += 1
                continue

            successful_saves += 1
            close_notepad()
            time.sleep(1.0)

            if i < len(valid_posts):
                wait_before_next_iteration(delay=1.5)

        except KeyboardInterrupt:
            logger.info("\nInterrupted by user")
            ensure_notepad_closed()
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            ensure_notepad_closed()
            failed_saves += 1
    
    logger.info("\n" + "="*60)
    logger.info("COMPLETE")
    logger.info("="*60)
    logger.info(f"Successful: {successful_saves}, Failed: {failed_saves}")
    logger.info(f"Output: {output_dir}")
    logger.info("="*60)

    if successful_saves > 0:
        print(f"\n✓ {successful_saves} post(s) saved to: {output_dir}")
        print(f"✓ Screenshots saved to: {screenshots_dir}")
    if failed_saves > 0:
        print(f"\n⚠ {failed_saves} failed. Check automation.log")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInterrupted")
        ensure_notepad_closed()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        ensure_notepad_closed()
        sys.exit(1)

