#!/usr/bin/env python3

"""
Manage the news subscriber
"""

import logging
import threading
import pika
import time

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
        self.running = True  # flag to indicate if the subscriber is running

    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # Connect to the broker
        self.__connect()

        # Subscribe to the editors exchange so the subscriber knows which editors is available
        self.__add_subscription(constants.EDITORS_EXCHANGE_NAME)

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

        # start thread to listen ti unsubscribe commands
        command_thread = threading.Thread(target=self.listen_for_commands)
        command_thread.daemon = True  # Daemonize thread
        command_thread.start()  # Start the execution
        
        # Consume messages
        self.__wait_for_news()

        
    def __connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
        self.channel = self.connection.channel()
        logging.info("Subscriber connected.")

    def __add_subscription(self, name: str):
        """
        Subscribe to a queue

        :param name: The exchange name to subscribe to
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=name, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {name} created if does not exist.")
        # Create the queue if not exists
        result = self.channel.queue_declare(queue='', exclusive=True) # exclusive=True: delete the queue when the connection is closed
        queue_name = result.method.queue
        
        # keep track of queue names per exchange
        if not hasattr(self, 'exchange_queue_map'):
            self.exchange_queue_map = {}
        self.exchange_queue_map[name] = queue_name
        
        logging.debug(f"Queue {queue_name} created if not exists")
        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=name, queue=queue_name)
        logging.debug(f"Queue {queue_name} created and binded to exchange {name}.")
        # Subscribe to the queue
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.__callback, auto_ack=True)
        logging.info(f"✅ Subscribed to {name}.")
    
    def __remove_subscription(self, name: str):
        """
        Unsubscribe from a queue (unbind from exchange)
        """
        # keep track of queue names per exchange
        if hasattr(self, 'exchange_queue_map') and name in self.exchange_queue_map:
            queue_name = self.exchange_queue_map[name]
            self.channel.queue_unbind(exchange=name, queue=queue_name)
            logging.info(f"💢 Unsubscribed from {name}.")

    def __wait_for_news(self):
        """
        Wait for news
        """
        logging.info("🚀 Subscriber is waiting for news.")
        # Start consuming messages
        while self.running:
            self.connection.process_data_events()
            time.sleep(0.1)
        # Safely close the connection if the subscriber is stopped
        self.connection.close()
        
    def listen_for_commands(self):
        """
        A thread that listens for user commands to unsubscribe from topics
        
        """
        while self.running:
            try:
                cmd = input(">>").strip()
                if cmd.startswith("unsubscribe"):
                    topic = cmd.split(" ",1)[1]
                    if topic in self.exchange_queue_map:
                        self.__remove_subscription(topic)
                    else:
                        print(f"⚠️ Not subscribed to '{topic}'")
                elif cmd == "exit":
                    self.exit()
                    break
            except EOFError:
                break

    def __callback(self, ch, method, properties, body):
        """
        Callback function that is called when a new message is received
        """
        exchange_name = method.exchange
        logging.info(f"➡️ Received on \"{exchange_name}\": {body}")

    def exit(self):
        """
        Stop the subscriber
        """
        self.running = False
        logging.info("Subscriber stopped.")