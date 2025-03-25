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
        self.channel.exchange_declare(exchange=constants.EXCHANGE_NAME, exchange_type='direct')
        # Create the queue if not exists
        self.channel.queue_declare(queue=type, durable=True)
        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=constants.EXCHANGE_NAME, queue=type)
        logging.debug(f"Queue {type} created and binded if not exists")
        # Publish the news on the queue
        self.channel.basic_publish(exchange=constants.EXCHANGE_NAME, routing_key=type, body=news)
        logging.info(f"{type}\tSent {news}")

    def exit(self):
        """
        Close the connection
        """
        self.connection.close()
        logging.info(f"Editor {self.name} disconnected.")