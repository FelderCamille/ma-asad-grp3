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

    def __init__(self):
        """
        Constructor
        """
        super(Subscriber, self).__init__()  # execute super class constructor

    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # Connect to the broker
        self.__connect()

        # Get the news types to subscribe to
        types = input("Enter the news types you want to subscribe to (separated by a space): ")
        types = types.split()

        # Check if the types are valid (in the enum values)
        for type in types:
            if type not in constants.NEWS_TYPES:
                logging.error(f"Invalid news type: {type}")
        
        # Subscribe to the news types
        for type in types:
            self.__add_subscription(type)
        
        # Wait for the consumer thread to finish
        self.__wait_for_news()

    def __connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info("Subscriber connected.")

    def __add_subscription(self, type: str):
        """
        Subscribe to a news type

        :param type: The news type to subscribe to
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=type, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {type} created if does not exist.")
        # Create the queue if not exists
        result = self.channel.queue_declare(queue='', exclusive=True) # exclusive=True: delete the queue when the connection is closed
        queue_name = result.method.queue
        logging.debug(f"Queue {type} created if not exists")
        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=type, queue=queue_name)
        logging.debug(f"Queue {type} created and binded to exchange {type}")
        # Subscribe to the queue
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.__callback, auto_ack=True)
        logging.info(f"✅ Subscribed to news type: {type}.")

    def __wait_for_news(self):
        """
        Wait for news
        """
        try:
            logging.info("🚀 Subscriber is waiting for news.")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logging.info("🔥 Subscriber interrupted.")
            self.channel.stop_consuming()
        finally:
            self.__exit()

    def __callback(self, ch, method, properties, body):
        """
        Callback function that is called when a new message is received
        """
        type = method.exchange
        logging.info(f"➡️ Received news type: {type}.\tContent: {body}")

    def __exit(self):
        """
        Close the connection
        """
        self.connection.close()
        logging.info("Subscriber disconnected.")