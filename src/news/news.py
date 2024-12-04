import logging
import os
from datetime import datetime
import feedparser
from src.utils.db_connection import get_collection
from src.utils.constants import NEWS_URL

# Specify the collection you need
news_collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))


def fetch_rss_items(feed_url):
    """Fetch and parse RSS feed items."""
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            logging.error(f"Error parsing RSS feed {feed_url}: {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries:
            # Extract thumbnail URL if available
            thumbnail_url = None
            if "media_thumbnail" in entry:
                thumbnail_url = entry.media_thumbnail[0].get("url")
            elif "media_content" in entry:
                thumbnail_url = entry.media_content[0].get("url")

            articles.append({
                "type": "news",
                "url": entry.get("link"),
                "title": entry.get("title"),
                "body": entry.get("summary", ""),  # Use `summary` for the article content
                "thumbnail": thumbnail_url,
                "date": entry.get("published", datetime.today().strftime('%Y-%m-%d')),  # Fallback to today's date
                "insertDate": datetime.today().strftime('%Y-%m-%d'), 
            })

        return articles

    except Exception as e:
        logging.error(f"An error occurred while fetching RSS items: {e}")
        return []


def save_article_to_mongo(article_details):
    """Save article details to MongoDB."""
    try:
        if article_details:
            # Check for duplicates based on URL
            if not news_collection.find_one({"url": article_details["url"]}):
                news_collection.insert_one(article_details)
                logging.info(f"Article saved to MongoDB: {article_details['url']}")
            else:
                logging.info(f"Duplicate article skipped: {article_details['url']}")
        else:
            logging.warning("No article details provided to save.")
    except Exception as e:
        logging.error(f"Failed to save article to MongoDB: {e}")


def fetch_and_store_news():
    """Fetch news from RSS feed and store in MongoDB."""
    logging.info(f"Fetching news from RSS feed: {NEWS_URL}")
    articles = fetch_rss_items(NEWS_URL)
    
    if articles:
        for article in articles:
            save_article_to_mongo(article)
    else:
        logging.info("No articles found in the RSS feed.")

