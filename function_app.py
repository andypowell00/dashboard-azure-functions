# function_app.py
import azure.functions as func
import logging
from src.reddit.reddit_posts import fetch_and_store_reddit_posts
from src.news.news import fetch_and_store_news
from src.weather.weather import fetch_and_store_weather_data
from src.movies.trailers import fetch_and_store_trailers
from src.music.pitchfork import fetch_and_store_feeds
from src.utils.constants import SUBREDDIT_LIST, LAT, LON, PF_RSS_URLS


# Create a FunctionApp instance
app = func.FunctionApp()

# 1. Reddit Trigger - Every morning at 5 a.m. EST :0 0 5 * * *
@app.function_name(name="InsertRedditPostsTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * * *", arg_name="redditTimer", run_on_startup=False, use_monitor=False) 
def RedditTrigger(redditTimer: func.TimerRequest) -> None:
    if redditTimer.past_due:
        logging.info('The timer is past due!')
    for subreddit in SUBREDDIT_LIST:
        fetch_and_store_reddit_posts(subreddit, post_limit=5)
    logging.info('Reddit data fetched and stored at 5 a.m. EST')

# 2. News Trigger - Every morning at 5 a.m. EST :0 0 5 * * * 
@app.function_name(name="InsertNewsTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * * *", arg_name="newsTimer", run_on_startup=False, use_monitor=False) 
def NewsTrigger(newsTimer: func.TimerRequest) -> None:
    if newsTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_news()
    logging.info('News data fetched and stored at 5 a.m. EST')

# 3. Weather Trigger - Every Monday at 5 a.m. EST :0 0 5 * * 1  
@app.function_name(name="InsertWeatherTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * * 1", arg_name="weatherTimer", run_on_startup=False, use_monitor=False) 
def WeatherTrigger(weatherTimer: func.TimerRequest) -> None:
    if weatherTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_weather_data(LAT,LON)
    logging.info('Weather data fetched and stored every Monday at 5 a.m. EST')

# 4. Movie Trailer Trigger - 5th of da Month ala Bone Thugs (almost)
@app.function_name(name="InsertTrailersTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * *", arg_name="trailersTimer", run_on_startup=False, use_monitor=False)
def TrailerTrigger(trailersTimer: func.TimerRequest) -> None:
    if trailersTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_trailers()  
    logging.info('Trailer data fetched on the 1st of each month')

# 5. Music news every 2 weeks
@app.function_name(name="InsertMusicNewsTimerTrigger")
@app.timer_trigger(schedule="0 0 1,15 * *", arg_name="musicTimer", run_on_startup=False, use_monitor=False)
def MusicTrigger(musicTimer: func.TimerRequest) -> None:
    if musicTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_feeds(PF_RSS_URLS)  
    logging.info('Music info grabbed every 2 weeks')    

