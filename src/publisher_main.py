#!/usr/bin/env python
import logging
import sys

from Editor import Editor
import constants

def main():
    """
    Main program entry point.
    """
    # Set the logging configuration
    logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO, 
                    format="[%(levelname)s] %(threadName)s \t\t %(message)s")

    # Get parameters from the console
    publisher_name = input("Enter your publisher name: ")

    # Inform on available news types
    logging.info("You can create a news of the following types:")
    for type in constants.NEWS_TYPES:
        logging.info(f" - {type}")

    try:
        # Create the publisher
        publisher = Editor()
        publisher.name = f"Editor \"{publisher_name}\"" # Name the thread
        publisher.start()
        # Wait for the publisher to be finished
        publisher.join()
    except KeyboardInterrupt:
        # Close the connection
        publisher.exit()
        

# Main program entry point
if __name__ == "__main__":
    main()