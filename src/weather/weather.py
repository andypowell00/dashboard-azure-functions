import os
import requests
import logging
from datetime import datetime
from src.utils.constants import *
from src.utils.db_connection import get_collection

# OpenWeatherMap API key and base URL
API_KEY = os.getenv("WEATHER_API_KEY")

collection = get_collection(os.getenv("COSMOS_DB_CONTAINER_NAME"))

def fetch_and_store_weather_data(LAT, LON):
    try:
        # Build the request URL for the 5-day forecast
        url = f"{WEATHER_BASE_URL}?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial"
        
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Parse the JSON response
        data = response.json()

        # Dictionary to hold daily summaries
        daily_weather = {}

        # Iterate through the forecast data
        for forecast in data["list"]:
            # Extract date
            date_str = datetime.fromtimestamp(forecast["dt"]).strftime("%Y-%m-%d")
            
            # If the date is not already in the dictionary, add it
            if date_str not in daily_weather:
                daily_weather[date_str] = {
                    "status": forecast["weather"][0]["description"],
                    "high_temp": forecast["main"]["temp_max"],
                    "low_temp": forecast["main"]["temp_min"]
                }
            else:
                # Update the high and low temperatures if needed
                daily_weather[date_str]["high_temp"] = max(daily_weather[date_str]["high_temp"], forecast["main"]["temp_max"])
                daily_weather[date_str]["low_temp"] = min(daily_weather[date_str]["low_temp"], forecast["main"]["temp_min"])

        for date, weather in daily_weather.items():
            weather_data = {
                "type": "weather",
                "date": date,
                "status": weather["status"],
                "high_temp": weather["high_temp"],
                "low_temp": weather["low_temp"],
                "lat": LAT,
                "lon": LON
            }
            collection.insert_one(weather_data)

        logging.info("Weather data successfully inserted into MongoDB.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch weather data: {e}")
    except KeyError as e:
        logging.error(f"Unexpected data format: {e}")
    except Exception as e:
        logging.error(f"Failed to insert data into MongoDB: {e}")