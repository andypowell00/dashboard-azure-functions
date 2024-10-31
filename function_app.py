import azure.functions as func
import logging
from utils.constants import *
from RedditFunction.reddit import fetch_and_store_reddit_posts
from NewsFunction.news import fetch_and_store_news
from WeatherFunction.weather import fetch_and_store_weather_data


app = func.FunctionApp()

# 1. Reddit Trigger - Every morning at 5 a.m. EST :0 0 5 * * *  test: */20 * * * * *
@app.timer_trigger(schedule="*/20 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def RedditTrigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    for subreddit in SUBREDDIT_LIST:
        fetch_and_store_reddit_posts(subreddit, post_limit=5)
    logging.info('Reddit data fetched and stored at 5 a.m. EST')

# 2. News Trigger - Every morning at 5 a.m. EST :0 0 5 * * *  test: */20 * * * * *
@app.timer_trigger(schedule="*/20 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def NewsTrigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_news()
    logging.info('News data fetched and stored at 5 a.m. EST')

# 3. Weather Trigger - Every Monday at 5 a.m. EST :0 0 5 * * 1  test: */20 * * * * *
@app.timer_trigger(schedule="*/20 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def WeatherTrigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    fetch_and_store_weather_data(LAT,LON)
    logging.info('Weather data fetched and stored every Monday at 5 a.m. EST')