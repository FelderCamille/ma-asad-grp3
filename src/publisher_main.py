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

# 2) RabbitMQ authentication – retry up to three times
    MAX_TRIES = 3
    for attempt in range(1, MAX_TRIES + 1):
        username = input("Enter your RabbitMQ username: ").strip()
        password = getpass.getpass("Enter your RabbitMQ password: ")

        publisher = Editor(editor_name=publisher_name,
                        username=username,
                        password=password)
        publisher.name = f'Editor "{publisher_name}"'
        publisher.start()
        publisher.join()                 # thread quits fast on auth failure

        if publisher.is_alive():         # connected → keep thread running
            break

        if attempt < MAX_TRIES:
            print(f"Authentication failed ({attempt}/{MAX_TRIES}). Try again.\n")
        else:
            print("Too many failed attempts—good-bye.")
            sys.exit(1)

if __name__ == "__main__":
    main()
