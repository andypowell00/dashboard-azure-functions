import os
import logging
from datetime import datetime, timezone
from googleapiclient.discovery import build
from src.utils.db_connection import get_collection
from src.utils.constants import TRAILER_CHANNEL_IDS

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')
collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))

def fetch_channel_videos(channel_id):
    """Fetch today's trailer videos directly from a channel's uploads."""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        videos = []
        today = datetime.now(timezone.utc).date()

        # First, get the channel's uploads playlist ID
        channels_response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        if not channels_response.get('items'):
            logging.error(f"No channel found for ID: {channel_id}")
            return []

        # Get the uploads playlist ID
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Request videos from channel's uploads
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=30  # Fetch more to ensure we don't miss today's videos
        )
        response = request.execute()

        for item in response.get('items', []):
            snippet = item['snippet']
            
            # Skip private videos
            if snippet['title'] == 'Private video':
                logging.info("Skipping private video")
                continue
                
            # Skip if "Trailer" is not in the title
            if 'Trailer' not in snippet['title']:
                logging.info(f"Skipping non-trailer video: {snippet['title']}")
                continue
                
            published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')).date()
            
            # Only process videos published today
            if published_at == today:
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
                    "date": today.strftime('%Y-%m-%d'),
                    "thumbnail": thumbnail_url,
                    "description": snippet.get('description', ''),
                    "published_at": snippet['publishedAt']
                }
                
                videos.append(video_data)
                logging.info(f"Found today's trailer: {video_data['title']} - {video_data['url']}")

        if not videos:
            logging.info(f"No new trailers found today in channel {channel_id}")
            
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
            collection.insert_many(all_videos)
            logging.info(f"Inserted {len(all_videos)} trailers into the collection.")
        else:
            logging.info(f"No videos found in the channels.")

    except Exception as e:
        logging.error(f"Failed to fetch and store trailers: {str(e)}")
