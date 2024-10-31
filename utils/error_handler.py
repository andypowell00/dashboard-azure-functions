# error_handler.py
import logging

logger = logging.getLogger(__name__)

def handle_error(e):
    logger.error(f"An error occurred: {e}")
    # Additional actions like sending alerts or retrying