#!/usr/bin/env python
import logging
import sys

from Subscriber import Subscriber
import constants

def main():
    """
    Main program entry point.
    """
    try:
        # Set the logging configuration
        logging.basicConfig(stream=sys.stderr, 
                        level=logging.INFO, 
                        format="[%(levelname)s] %(threadName)s \t\t %(message)s")

        # Get the subscriber name from the console
        name = input("Enter your name: ")

        # Inform on available news types
        logging.info("You can subscribe to the following news types:")
        for type in constants.NEWS_TYPES:
            logging.info(f" - {type}")

        # Get the news types to subscribe to
        types = input("Enter the news types you want to subscribe to (separated by a space): ")
        types = types.split()

        # Check if the types are valid (in the enum values)
        for type in types:
            if type not in constants.NEWS_TYPES:
                logging.error(f"Invalid news type: {type}")
                sys.exit(0)

        # Create the subscriber
        subscriber = Subscriber(name)
        subscriber.name = f"Subscriber {name}"
        subscriber.start()

        # Subscribe to the news
        subscriber.connect()
        for type in types:
            subscriber.add_subscription(type)
        subscriber.wait_for_news()
    except KeyboardInterrupt:
        subscriber.exit()

# Main program entry point
if __name__ == "__main__":
    main()