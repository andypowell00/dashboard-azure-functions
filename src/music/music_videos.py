import os
import logging
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from src.utils.constants import MUSIC_VIDEOS_CHANNEL_IDS
from src.utils.db_connection import get_collection

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')
collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))

def fetch_playlist_videos(playlist_id):
    """Fetch recent videos from a playlist by playlist ID, skipping private videos."""
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        videos = []
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)  # Look for videos from yesterday too
        
        # Get playlist title for better logging
        try:
            playlist_response = youtube.playlists().list(
                part="snippet",
                id=playlist_id
            ).execute()
            
            if playlist_response.get('items'):
                playlist_title = playlist_response['items'][0]['snippet']['title']
                logging.info(f"Processing playlist: {playlist_title}")
            else:
                playlist_title = "Unknown playlist"
                logging.warning(f"Could not get title for playlist ID: {playlist_id}")
        except Exception as e:
            playlist_title = "Error getting playlist"
            logging.error(f"Error getting playlist info: {str(e)}")

        # Request videos from playlist with pagination
        videos_processed = 0
        next_page_token = None
        
        while videos_processed < 100:  # Limit to prevent infinite loops
            # Request videos from playlist
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
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
                        "type": "music",
                        "title": snippet['title'],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "date": published_date.strftime('%Y-%m-%d'),
                        "thumbnail": thumbnail_url,
                        "insertDate": datetime.today().strftime('%Y-%m-%d'), 
                        "description": snippet.get('description', ''),
                        "published_at": snippet['publishedAt']
                    }
                    
                    videos.append(video_data)
                    logging.info(f"Found recent video: {video_data['title']} - {video_data['url']} - Published: {published_date}")
            
            videos_processed += len(response.get('items', []))
            next_page_token = response.get('nextPageToken')
            
            if not next_page_token:
                break

        if not videos:
            logging.info(f"No new videos found in the last 48 hours in playlist {playlist_title}")
            
        return videos

    except Exception as e:
        logging.error(f"Failed to fetch playlist videos: {str(e)}")
        return []

def fetch_and_store_music_videos():
    """Main function to fetch and store music videos from multiple playlists."""
    try:
        all_videos = []
        
        # Fetch videos from each playlist
        for playlist_id in MUSIC_VIDEOS_CHANNEL_IDS:  # Note: These are actually playlist IDs now
            logging.info(f"Fetching videos from playlist: {playlist_id}")
            videos = fetch_playlist_videos(playlist_id)
            all_videos.extend(videos)
            logging.info(f"Found {len(videos)} videos in playlist {playlist_id}")

        logging.info(f"Total videos found across all playlists: {len(all_videos)}")
        
        # Insert videos into MongoDB
        if all_videos:
            collection.insert_many(all_videos)
            logging.info(f"Inserted {len(all_videos)} music videos into the collection.")
        else:
            logging.info("No new music videos found in the last 48 hours.")
            
        return all_videos

    except Exception as e:
        logging.error(f"Failed to fetch and store music videos: {str(e)}")
        return []

# For testing purposes
if __name__ == "__main__":
    videos = fetch_and_store_music_videos()
    if videos:
        logging.info("Example of first video found:")
        logging.info(videos[0])