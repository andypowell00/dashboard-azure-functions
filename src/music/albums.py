import os
import logging
import requests
from bs4 import BeautifulSoup
from src.utils.db_connection import get_collection
from src.utils.constants import ALBUM_LIMIT, ALBUM_URL

# Set up logging
logging.basicConfig(level=logging.INFO)

# MongoDB setup
collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))  

def fetch_and_store_albums():
    """Scrape album data from Metacritic and insert into MongoDB."""
    try:
        # Example URL to scrape (replace with actual URL)
        url = ALBUM_URL
        
        # Define headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
        }

        # Send a GET request to fetch the page content with headers
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all tables with class 'clamp-list'
            tables = soup.find_all('table', class_='clamp-list')
            if not tables:
                logging.error("No tables with class 'clamp-list' found.")
                return

            # Initialize a list to store all album data
            all_album_data = []

            # Loop through each table and extract album data
            for table in tables:
                albums = table.find_all('tr')
                logging.debug(f"Found {len(albums)} album rows in a 'clamp-list' table.")

                # Loop through each album and extract details
                for album in albums:
                    if len(all_album_data) >= ALBUM_LIMIT:  
                        break
                    
                    album_data = {}

                    # Extract album details
                    image_td = album.find('td', class_='clamp-image-wrap')
                    if image_td:
                        image_tag = image_td.find('img')
                        if image_tag:
                            album_data['image'] = image_tag['src']

                    title_tag = album.find('a', class_='title')
                    if title_tag:
                        album_data['title'] = title_tag.get_text(strip=True)

                    artist_tag = album.find('div', class_='artist')
                    if artist_tag:
                        album_data['artist'] = artist_tag.get_text(strip=True)

                    date_tag = album.find('span')
                    if date_tag:
                        release_date_str = date_tag.get_text(strip=True)
                        album_data['release_date'] = release_date_str

                    summary_tag = album.find('div', class_='summary')
                    if summary_tag:
                        album_data['summary'] = summary_tag.get_text(strip=True)

                    # Add the type field to indicate it's an album
                    album_data['type'] = 'album'

                    # If we have any data for the album, append it to the album_list
                    if album_data:
                        all_album_data.append(album_data)

                # Break out of the outer loop if we already have 40 albums
                if len(all_album_data) >= ALBUM_LIMIT:
                    break

            # Insert album data into MongoDB
            if all_album_data:
                try:
                    collection.insert_many(all_album_data)
                    logging.info(f"Successfully inserted {len(all_album_data)} albums into MongoDB.")
                except Exception as e:
                    logging.error(f"Error inserting into MongoDB: {e}")
            else:
                logging.info("No albums to insert.")

        else:
            logging.error(f"Failed to retrieve page. Status code: {response.status_code}")

    except Exception as e:
        logging.error(f"Failed to scrape Metacritic: {str(e)}")

