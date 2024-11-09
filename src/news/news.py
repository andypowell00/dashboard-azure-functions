import requests
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup
from src.utils.db_connection import get_collection
from src.utils.constants import *

# Specify the collection you need
news_collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))


def get_headline_urls(news_url, keywords):
    try:
        response = requests.get(news_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        headline_urls = []
        for headline in soup.find_all('a'):
            headline_text = headline.get_text().lower()
            if any(keyword in headline_text for keyword in keywords):
                url = headline.get('href')
                if url is not None:
                    headline_urls.append(url)
        return headline_urls
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve website content: {e}")
        return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

def get_article_details(article_url):
    try:
        full_url = AI_NEWS_BASE_URL + article_url
        response = requests.get(full_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get article body
        article_body = soup.find('article').text.strip() if soup.find('article') else "No content available"

        # Get image URL if available
        image_url = None
        image_tag = soup.find('img')
        if image_tag:
            image_url = image_tag.get('src')

        return {
            "type": "news",
            "url": full_url,
            "body": article_body,
            "image_url": image_url,
            "date": datetime.today().strftime('%Y-%m-%d')  # Add the current date
        }
    except Exception as e:
        logging.error(f"An error occurred while retrieving article details: {e}")
        return None

def save_article_to_mongo(article_details):
    try:
        if article_details:
            # Insert the article into the News collection
            news_collection.insert_one(article_details)
            logging.info(f"Article saved to MongoDB: {article_details['url']}")
        else:
            logging.warning("No article details provided to save.")
    except Exception as e:
        logging.error(f"Failed to save article to MongoDB: {e}")

def fetch_and_store_news():
    headline_urls = get_headline_urls(NEWS_URL, KEYWORDS)
    if headline_urls:
        for url in headline_urls:
            if url and "http" not in url:
                article_details = get_article_details(url)
                if article_details:
                    save_article_to_mongo(article_details)
