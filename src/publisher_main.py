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
    # 0) Logging setup
    logging.basicConfig(stream=sys.stderr, 
                        level=logging.INFO, 
                        format="[%(levelname)s] %(threadName)s \t\t %(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)

    # 1) Publisher name (must not be empty)
    publisher_name = ""
    while not publisher_name.strip():
        publisher_name = input("Enter your publisher name: ")
        if not publisher_name.strip():
            print("⚠️  Publisher name cannot be empty.")

    # 2) RabbitMQ credentials (must not be empty)
    username = ""
    while not username.strip():
        username = input("Enter your RabbitMQ username: ")
        if not username.strip():
            print("⚠️  Username cannot be empty.")

    password = ""
    while not password:
        password = getpass.getpass("Enter your RabbitMQ password: ")
        if not password:
            print("⚠️  Password cannot be empty.")

    # 3) Show available news types
    logging.info("You can create a news of the following types:")
    for type_ in constants.NEWS_TYPES:
        logging.info(f" - {type_}")

    try:
        # 4) Instantiate and run the editor thread
        publisher = Editor(editor_name=publisher_name,
                           username=username,
                           password=password)
        publisher.name = f"Editor \"{publisher_name}\""
        publisher.start()
        publisher.join()
    except KeyboardInterrupt:
        publisher.exit()


if __name__ == "__main__":
    main()
