import os
import logging
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from src.utils.db_connection import get_collection
from src.utils.constants import TRAILER_CHANNEL_IDS

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')


def fetch_channel_videos(channel_id):
    """Fetch recent trailer videos directly from a channel's uploads."""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        videos = []
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)  # Look for videos from yesterday too
        
        # First, get the channel's uploads playlist ID
        channels_response = youtube.channels().list(
            part="contentDetails,snippet",
            id=channel_id
        ).execute()

        if not channels_response.get('items'):
            logging.error(f"No channel found for ID: {channel_id}")
            return []

        # Get channel title for better logging
        channel_title = channels_response['items'][0]['snippet']['title']
        logging.info(f"Processing channel: {channel_title}")

        # Get the uploads playlist ID
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Request videos from channel's uploads with pagination
        videos_processed = 0
        next_page_token = None
        
        while videos_processed < 100:  # Limit to prevent infinite loops
            # Request videos from channel's uploads
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,  # Increase from 30 to 50 to get more videos per page
                pageToken=next_page_token
            )
            response = request.execute()
            
            # Process videos
            for item in response.get('items', []):
                snippet = item['snippet']
                
                # Skip private videos
                if snippet['title'] == 'Private video':
                    logging.info("Skipping private video")
                    continue
                    
                # Check if it's trailer-related: either has "Trailer" in title or has trailer-related keywords
                is_trailer = ('Trailer' in snippet['title'] or 
                             'trailer' in snippet['title'] or 
                             'Teaser' in snippet['title'] or
                             'teaser' in snippet['title'] or
                             'Official Video' in snippet['title'])
                
                if not is_trailer:
                    logging.info(f"Skipping non-trailer video: {snippet['title']}")
                    continue
                    
                published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                published_date = published_at.date()
                
                # Process videos from today or yesterday
                if published_date in (today, yesterday):
                    video_id = snippet['resourceId']['videoId']

                    # Safely extract thumbnails with a fallback
                    thumbnails = snippet.get('thumbnails', {})
                    thumbnail_url = (
                        thumbnails.get('high', {}).get('url') or
                        thumbnails.get('medium', {}).get('url') or
                        thumbnails.get('default', {}).get('url')
                    )

                    if not thumbnail_url:
                        logging.warning(f"No thumbnail available for video ID: {video_id}")

                    video_data = {
                        "type": "trailer",
                        "title": snippet['title'],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "date": published_date.strftime('%Y-%m-%d'),
                        "thumbnail": thumbnail_url,
                        "description": snippet.get('description', ''),
                        "published_at": snippet['publishedAt']
                    }
                    
                    videos.append(video_data)
                    logging.info(f"Found recent trailer: {video_data['title']} - {video_data['url']} - Published: {published_date}")
            
            videos_processed += len(response.get('items', []))
            next_page_token = response.get('nextPageToken')
            
            if not next_page_token:
                break

        if not videos:
            logging.info(f"No new trailers found in the last 48 hours in channel {channel_title}")
            
        return videos

    except Exception as e:
        logging.error(f"Failed to fetch channel videos: {str(e)}")
        return []

def fetch_and_store_trailers():
    """Main function to fetch and store trailer videos from multiple channels into MongoDB."""
    try:
        all_videos = []
        
        # Fetch videos from each channel
        for channel_id in TRAILER_CHANNEL_IDS:
            logging.info(f"Fetching videos from channel: {channel_id}")
            videos = fetch_channel_videos(channel_id)
            all_videos.extend(videos)
            logging.info(f"Found {len(videos)} videos in channel {channel_id}")

        logging.info(f"Total videos found across all channels: {len(all_videos)}")
        
        # Insert videos into MongoDB
        if all_videos:
            # Check for duplicates before insertion
            collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))
            new_videos = []
            for video in all_videos:
                # Check if this video URL already exists in the database
                existing = collection.find_one({"url": video["url"]})
                if not existing:
                    new_videos.append(video)
                else:
                    logging.info(f"Skipping duplicate video: {video['title']}")
            
            if new_videos:
                collection.insert_many(new_videos)
                logging.info(f"Inserted {len(new_videos)} trailers into the collection.")
            else:
                logging.info("No new unique trailers to insert.")
        else:
            logging.info(f"No new trailer videos found in the last 48 hours.")

    except Exception as e:
        logging.error(f"Failed to fetch and store trailers: {str(e)}")
