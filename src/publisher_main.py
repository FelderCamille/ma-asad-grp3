#!/usr/bin/env python
import logging
import sys

from Editor import Editor
from NewsType import NewsType

def main():
    # Set the logging configuration
    logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO, 
                    format="[%(levelname)s] %(threadName)s \t\t %(message)s")

    # Get parameters from the console
    publisher_name = input("Enter your publisher name: ")

    # Create the publisher
    publisher = Editor(publisher_name)
    publisher.name = f"Editor {publisher_name}" # Name the thread
    publisher.start()

    # Send some news
    publisher.connect()
    publisher.send_news(NewsType.SPORTS.value, "Sport news 1")
    publisher.send_news(NewsType.POLITICS.value, "Politics news 1")
    publisher.send_news(NewsType.SPORTS.value, "Sport news 2")
    publisher.exit()

# Main program entry point
if __name__ == "__main__":
    main()