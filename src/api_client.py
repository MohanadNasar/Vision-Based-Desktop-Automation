import logging
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)


def fetch_posts(limit: int = 10) -> List[Dict]:
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/posts", timeout=10)
        response.raise_for_status()
        return response.json()[:limit]
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        raise


def format_post_content(post: Dict) -> str:
    return f"Title: {post.get('title', '')}\n\n{post.get('body', '')}"


def validate_post(post: Dict) -> bool:
    return all(field in post for field in ["id", "title", "body"])

