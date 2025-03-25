#!/usr/bin/env python
import logging
import sys

from Editor import Editor
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

        # Get parameters from the console
        publisher_name = input("Enter your publisher name: ")

        # Inform on available news types
        logging.info("You can create a news of the following types:")
        for type in constants.NEWS_TYPES:
            logging.info(f" - {type}")

        # Create the publisher
        publisher = Editor(publisher_name)
        publisher.name = f"Editor {publisher_name}" # Name the thread
        publisher.start()

        # Connect to the broker
        publisher.connect()

        # Send news
        while True:
            # Get the news type
            types = input("Enter the news type(s) (multiple types must be separated by a space): ")
            types = types.split()
            # Check if the types are valid, if not ask again
            invalid_type = False
            for type in types:
                if type not in constants.NEWS_TYPES:
                    logging.error(f"Invalid news type: {type}")
                    invalid_type = True
                    continue
            if invalid_type:
                continue
            # Get the news content
            news = input("Enter the news: ")
            # Send the news
            for type in types:
                publisher.send_news(type, news)
    except KeyboardInterrupt:
        publisher.exit()

# Main program entry point
if __name__ == "__main__":
    main()