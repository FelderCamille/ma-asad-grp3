#!/usr/bin/env python
import logging
import sys

from subscriber import Subscriber
import constants

def main():
    """
    Main program entry point.
    """
    # Set the logging configuration
    logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO, 
                    format="[%(levelname)s] %(threadName)s \t\t %(message)s")

    # Get the subscriber name from the console
    name = input("Enter your name: ")

    # Inform on available news types
    logging.info("You can subscribe to the following news types:")
    for type_ in constants.NEWS_TYPES:
        logging.info(f" - {type_}")

    try:
        subscriber = Subscriber()
        subscriber.name = f"Subscriber \"{name}\""
        subscriber.start()
        subscriber.join()
    except KeyboardInterrupt:
        subscriber.exit()

if __name__ == "__main__":
    main()
