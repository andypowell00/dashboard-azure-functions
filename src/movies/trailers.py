import os
import logging
from datetime import datetime
from googleapiclient.discovery import build
from src.utils.db_connection import get_collection
from src.utils.constants import TRAILER_CHANNEL_IDS

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')
collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))

def search_playlist_by_name(base_name, month, year, channel_id):
    """Search for a playlist by name in the specified channel."""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        query = f"{base_name} - {month} {year}"
        
        request = youtube.search().list(
            part="snippet",
            q=query,
            channelId=channel_id,  # Explicitly restrict to this channel
            type="playlist",
            maxResults=1
        )
        response = request.execute()

        # Return the first playlist's ID
        items = response.get('items', [])
        if items:
            # Verify the playlist's channel ID matches the provided channel ID
            playlist = items[0]
            if playlist['snippet']['channelId'] == channel_id:
                return playlist["id"]["playlistId"]
            else:
                logging.warning(f"Found playlist from a different channel: {playlist['snippet']['channelId']}")
        return None
    except Exception as e:
        logging.error(f"Failed to search playlists: {str(e)}")
        return None


def fetch_playlist_videos(playlist_id):
    """Fetch all videos from a playlist by playlist ID."""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        videos = []
        next_page_token = None

        while True:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                snippet = item['snippet']
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

                videos.append({
                    "type": "trailer",
                    "title": snippet['title'],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "date": datetime.today().strftime('%Y-%m-%d'),
                    "thumbnail": thumbnail_url,
                    "description": snippet.get('description', ''),
                    "published_at": snippet['publishedAt']
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return videos

    except Exception as e:
        logging.error(f"Failed to fetch playlist videos: {str(e)}")
        return []


def fetch_and_store_trailers():
    """Main function to fetch and store trailer videos from multiple channels into MongoDB."""
    try:
        # Determine current month and year
        base_name = "Best New Trailers"
        current_month = datetime.now().strftime("%B")
        current_year = datetime.now().year

        for channel_id in TRAILER_CHANNEL_IDS:
            logging.info(f"Processing channel ID: {channel_id}")

            # Search for the playlist in the current channel
            playlist_id = search_playlist_by_name(base_name, current_month, current_year, channel_id)
            if not playlist_id:
                logging.info(f"No playlist found for {base_name} - {current_month} {current_year} in channel {channel_id}.")
                continue

            logging.info(f"Playlist found for channel {channel_id}: {playlist_id}. Fetching videos...")

            # Fetch videos from the playlist
            videos = fetch_playlist_videos(playlist_id)

            # Insert videos into MongoDB
            if videos:
                collection.insert_many(videos)
                logging.info(f"Inserted {len(videos)} trailers from channel {channel_id} into the collection.")
            else:
                logging.info(f"No videos found in the playlist for channel {channel_id}.")

    except Exception as e:
        logging.error(f"Failed to fetch and store trailers: {str(e)}")


