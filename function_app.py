# function_app.py
import azure.functions as func
import logging
from src.reddit.reddit_posts import fetch_and_store_reddit_posts
from src.news.news import fetch_and_store_news
from src.utils.constants import SUBREDDIT_LIST


# Create a FunctionApp instance
app = func.FunctionApp()

# 1. Reddit Trigger
@app.function_name(name="InsertRedditPostsTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * * *", arg_name="redditTimer", run_on_startup=True, use_monitor=True) 
def RedditTrigger(redditTimer: func.TimerRequest) -> None:
    if redditTimer.past_due:
        logging.info('The timer is past due!')
    for subreddit in SUBREDDIT_LIST:
        fetch_and_store_reddit_posts(subreddit, post_limit=2)
    logging.info('Reddit data fetched and stored at 5 a.m. EST')

# 2. News Trigger - Every morning at 5 a.m. EST :0 0 5 * * *  test schedule: */20 * * * * *
@app.function_name(name="InsertNewsTimerTrigger")
@app.timer_trigger(schedule="0 0 5 * * *", arg_name="newsTimer", run_on_startup=True, use_monitor=True) 
def NewsTrigger(newsTimer: func.TimerRequest) -> None:
    if newsTimer.past_due:
        logging.info('The timer is past due!')
    #fetch_and_store_news()
    logging.info('news test run success')
    logging.info('News data fetched and stored at 5 a.m. EST')
