import feedparser
import os
import logging
from datetime import datetime
from src.utils.db_connection import get_collection

# Set up logging
logging.basicConfig(level=logging.INFO)

# MongoDB setup
collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))  


def fetch_rss_items(feed_url):
    """Fetch and parse RSS feed items."""
    feed = feedparser.parse(feed_url)
    
    if feed.bozo:
        logging.error(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
        return []

    # Extract desired fields
    news_items = []
    for entry in feed.entries:
        news_items.append({
            "type": "music",  # Identifying the item type
            "title": entry.get("title"),
            "url": entry.get("link"),
            "date": entry.get("published", datetime.now().isoformat()),
            "description": entry.get("description", ""),
            "category": entry.get("category", "Uncategorized"),
            "thumbnail": extract_thumbnail(entry)
        })
    return news_items

def extract_thumbnail(entry):
    """Extract thumbnail URL from entry if available."""
    media_content = entry.get("media_thumbnail", [])
    if media_content and isinstance(media_content, list):
        return media_content[0].get("url")
    return None

def fetch_and_store_feeds(feed_urls):
    """Fetch items from RSS feeds and insert them into MongoDB."""
    try:
        for feed_url in feed_urls:
            logging.info(f"Processing feed: {feed_url}")
            news_items = fetch_rss_items(feed_url)

            if news_items:
                # Insert items into MongoDB with deduplication
                for item in news_items:
                    # Use URL as a unique identifier for deduplication
                    if not collection.find_one({"url": item["url"]}):
                        collection.insert_one(item)
                        logging.info(f"Inserted item: {item['title']}")
                    else:
                        logging.info(f"Skipped duplicate item: {item['title']}")
            else:
                logging.info(f"No items found for feed: {feed_url}")

    except Exception as e:
        logging.error(f"Failed to fetch and store feeds: {str(e)}")

