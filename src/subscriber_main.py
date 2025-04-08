#!/usr/bin/env python
import logging
import sys

from Subscriber import Subscriber
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
    for type in constants.NEWS_TYPES:
        logging.info(f" - {type}")

    try:
        # Create the subscriber
        subscriber = Subscriber()
        subscriber.name = f"Subscriber \"{name}\""
        subscriber.start()
        # Wait for the subscriber to be finished
        subscriber.join()
    except KeyboardInterrupt:
        # Close the connection
        subscriber.exit()

# Main program entry point
if __name__ == "__main__":
    main()