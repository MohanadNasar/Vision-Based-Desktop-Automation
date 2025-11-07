"""API client for fetching blog posts from JSONPlaceholder."""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

API_BASE_URL = "https://jsonplaceholder.typicode.com"


def fetch_posts(limit: int = 10) -> List[Dict]:
    """
    Fetch blog posts from JSONPlaceholder API.
    
    Args:
        limit: Maximum number of posts to fetch (default: 10)
        
    Returns:
        List of post dictionaries containing 'id', 'title', and 'body' keys
        
    Raises:
        requests.RequestException: If API request fails
    """
    try:
        url = f"{API_BASE_URL}/posts"
        logger.info(f"Fetching posts from {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        posts = response.json()
        limited_posts = posts[:limit]
        
        logger.info(f"Successfully fetched {len(limited_posts)} posts")
        return limited_posts
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        raise
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to API. Check your internet connection.")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching posts: {e}")
        raise


def format_post_content(post: Dict) -> str:
    """
    Format a post dictionary into the required text format.
    
    Args:
        post: Dictionary containing 'title' and 'body' keys
        
    Returns:
        Formatted string: "Title: {title}\n\n{body}"
    """
    title = post.get("title", "")
    body = post.get("body", "")
    return f"Title: {title}\n\n{body}"


def validate_post(post: Dict) -> bool:
    """
    Validate that a post dictionary has required fields.
    
    Args:
        post: Dictionary to validate
        
    Returns:
        True if post is valid, False otherwise
    """
    required_fields = ["id", "title", "body"]
    return all(field in post for field in required_fields)

