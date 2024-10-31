import logging

def configure_logging():
    logging.basicConfig(filename='error.log', level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')