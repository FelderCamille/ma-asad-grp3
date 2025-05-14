#!/usr/bin/env python
import logging
import sys
import getpass

from publisher import Editor
import constants

def main():
    """
    Main program entry point.
    """
    # Set the logging configuration
    logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO, 
                    format="[%(levelname)s] %(threadName)s \t\t %(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)

    # Get parameters from the console
    publisher_name = input("Enter your publisher name: ")
    username = input("Enter your RabbitMQ username: ")
    password = getpass.getpass("Enter your RabbitMQ password: ")
    # Inform on available news types
    logging.info("You can create a news of the following types:")
    for type_ in constants.NEWS_TYPES:
        logging.info(f" - {type_}")

    try:
        # Create the publisher
        publisher = Editor(editor_name=publisher_name,
                           username=username,
                           password=password)
        publisher.name = f"Editor \"{publisher_name}\""
        publisher.start()
        # Wait for the publisher to be finished
        publisher.join()
    except KeyboardInterrupt:
        publisher.exit()
        

if __name__ == "__main__":
    main()