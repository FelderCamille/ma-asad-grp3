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
    logging.basicConfig(stream=sys.stderr,
                        level=logging.INFO,
                        format="[%(levelname)s] %(threadName)s \t\t %(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)

    # 1) Subscriber name
    name = ""
    while not name.strip():
        name = input("Enter your name: ")
        if not name.strip():
            print("⚠️  Name cannot be empty.")

    # 2) RabbitMQ credentials
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

    logging.info("You can subscribe to the following news types:")
    for type_ in constants.NEWS_TYPES:
        logging.info(f" - {type_}")

    try:
        subscriber = Subscriber(username=username,
                                password=password)
        subscriber.name = f"Subscriber \"{name}\""
        subscriber.start()
        subscriber.join()
    except KeyboardInterrupt:
        subscriber.exit()


if __name__ == "__main__":
    main()
