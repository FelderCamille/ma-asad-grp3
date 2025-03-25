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

    def __init__(self, name: str):
        """
        Constructor

        :param name: The name of the editor
        """
        super(Editor, self).__init__()  # execute super class constructor
        self.name = name

    def connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info(f"Editor {self.name} connected.")

    def send_news(self, type: str, news: str):
        """
        Send the news to the subscribers
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=type, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {type} created if does not exist.")
        # Publish the news on the queue
        self.channel.basic_publish(exchange=type, routing_key='', body=news)
        logging.info(f"➡️ Sent type: {type}.\tContent: {news}")

    def exit(self):
        """
        Close the connection
        """
        self.connection.close()
        logging.info(f"Editor {self.name} disconnected.")