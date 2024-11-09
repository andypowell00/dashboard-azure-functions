import os
import logging
import praw  # Reddit API wrapper
from datetime import datetime
from pymongo import MongoClient

# Set up Reddit client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Get MongoDB connection string
connection_string = os.getenv("COSMOS_DB_CONNECTION_STRING")
    
    # Create a MongoDB client
client = MongoClient(connection_string)
db = client[os.getenv("COSMOS_DB_DATABASE_NAME")]
collection = db[os.getenv("COSMOS_DB_CONTAINER_NAME")]

def fetch_and_store_reddit_posts(subreddit_name, post_limit=2):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.hot(limit=post_limit)

        post_data = []
        
        for post in posts:
            image_url = post.url if post.url.endswith(('.jpg', '.png', '.gif', '.jpeg', '.img')) else None

            post_info = {
                "type": "reddit",
                "title": post.title,
                "url": post.url,
                "score": post.score,
                "date": datetime.today().strftime('%Y-%m-%d'),  
                "subreddit": post.subreddit.display_name,
                "author": str(post.author),
                "selftext": post.selftext,
                "image_url": image_url
            }
            post_data.append(post_info)

        if post_data:
            collection.insert_many(post_data)
            logging.info(f"Inserted {len(post_data)} posts into the 'RedditPosts' collection.")
        else:
            logging.info("No posts found.")
    except Exception as e:
        logging.error(f"Fetch from Reddit failed: {str(e)}")
