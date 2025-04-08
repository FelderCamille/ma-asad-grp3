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

    def run(self):
        """
        Handle the lifecycle of the editor
        """
        try:
            # Connect to the broker
            self.__connect()
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
                    self.__send_news(type, news)
        except KeyboardInterrupt:
            self.__exit()
        
    def __connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info("Editor connected.")

    def __send_news(self, type: str, news: str):
        """
        Send the news to the subscribers
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=type, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {type} created if does not exist.")
        # Publish the news on the queue
        self.channel.basic_publish(exchange=type, routing_key='', body=news)
        logging.info(f"➡️ Sent type: {type}.\tContent: {news}")

    def __exit(self):
        """
        Close the connection
        """
        self.connection.close()
        logging.info("Editor disconnected.")