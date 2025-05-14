#!/usr/bin/env python
import logging
import sys
import getpass

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
    logging.getLogger("pika").setLevel(logging.WARNING)

    # Get the subscriber name from the console
    name = input("Enter your name: ")
    username = input("Enter your RabbitMQ username: ")
    password = getpass.getpass("Enter your RabbitMQ password: ")
    # Inform on available news types
    logging.info("You can subscribe to the following news types:")
    for type_ in constants.NEWS_TYPES:
        logging.info(f" - {type_}")

    try:
        # Create the subscriber
        subscriber = Subscriber(
            username=username,
            password=password,
        )
        subscriber.name = f"Subscriber \"{name}\""
        subscriber.start()
        # Wait for the subscriber to be finished
        subscriber.join()
    except KeyboardInterrupt:
        subscriber.exit()

if __name__ == "__main__":
    main()
