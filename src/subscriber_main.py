#!/usr/bin/env python
import logging
import sys

from Subscriber import Subscriber
from NewsType import NewsType

def main():
    # Set the logging configuration
    logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO, 
                    format="[%(levelname)s] %(threadName)s \t\t %(message)s")

    # Get parameters from the console
    name = input("Enter your name: ")

    # Create the subscriber
    subscriber = Subscriber(name)
    subscriber.name = f"Subscriber {name}"
    subscriber.start()

    # Subscribe to some news
    subscriber.connect()
    subscriber.add_subscription(NewsType.SPORTS.value)
    subscriber.add_subscription(NewsType.POLITICS.value)
    subscriber.wait_for_news()

# Main program entry point
if __name__ == "__main__":
    main()