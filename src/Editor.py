#!/usr/bin/env python3

"""
Manage the news editor
"""

import logging
import threading
import pika

import constants

class Editor(threading.Thread):
    """
    An editor can send news to the broker
    """

    def __init__(self):
        """
        Constructor
        """
        super(Editor, self).__init__()  # execute super class constructor
        self.running = True  # flag to indicate if the editor is running

    def run(self):
        """
        Handle the lifecycle of the editor
        """
        # Connect to the broker
        self.__connect()
        # Send news
        while self.running:
            # Get the news type
            types = input("Enter the news type(s) (multiple types must be separated by a space): ")
            types = types.split()
            # Check if the user wants to exit (exit request could have been made during the input)
            if not self.running:
                break
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
                self.__send_to_subscribers(name=type, content=news)
        
    def __connect(self):
        """
        Connect to the broker
        """
        # Connect to the broker
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info("Editor connected.")
        # Indicate that the editor is online
        self.__send_to_subscribers(constants.EDITORS_EXCHANGE_NAME, f"{self.name} is online.")

    def __send_to_subscribers(self, name: str, content: str):
        """
        Send data to the subscribers

        :param name: The name of the exchange
        :param content: The content to send
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=name, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {name} created if does not exist.")
        # Publish on the queue
        self.channel.basic_publish(exchange=name, routing_key='', body=content)
        logging.info(f"➡️ Sent on \"{name}\": {content}")

    def exit(self):
        """
        Close the connection
        """
        # Set the flag to false to stop the thread
        self.running = False
        # Indicate that the editor is offline
        self.__send_to_subscribers(constants.EDITORS_EXCHANGE_NAME, f"{self.name} is offline.")
        # Close the connection
        self.connection.close()
        logging.info("Editor disconnected.")