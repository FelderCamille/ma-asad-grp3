#!/usr/bin/env python3

"""
Manage the news subscriber
"""

import logging
import threading
import pika

import constants

class Subscriber(threading.Thread):
    """
    A subscriber can subscribe to news types and receive news
    """

    def __init__(self, name: str):
        """
        Constructor

        :param name: The name of the subscriber
        """
        super(Subscriber, self).__init__()  # execute super class constructor
        self.name = name

    def connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info(f"Subscriber {self.name} connected.")

    def add_subscription(self, type: str):
        """
        Subscribe to a news type

        :param type: The news type to subscribe to
        """
        self.channel.basic_consume(queue=type, on_message_callback=self.__callback, auto_ack=True)

    def wait_for_news(self):
        """
        Wait for news
        """
        logging.info(f"Subscriber {self.name} is waiting for news.")
        self.channel.start_consuming()

    def __callback(self, ch, method, properties, body):
        """
        Callback function that is called when a new message is received
        """
        logging.info(f"Received: {body}")

    def exit(self):
        """
        Close the connection
        """
        self.connection.close()
        logging.info(f"Subscriber {self.name} disconnected.")