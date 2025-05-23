#!/usr/bin/env python3

"""
Manage the news subscriber
"""

import logging
import threading
import pika
import time
import re
import ssl

import constants

class Subscriber(threading.Thread):
    """
    A subscriber can subscribe to editors, news types, and receive news
    """

    def __init__(self, username, password):
        """
        Constructor
        """
        super(Subscriber, self).__init__()  # execute super class constructor
        self.username = username
        self.password = password
        self.running = True  # flag to indicate if the subscriber is running
        self.queue_name = None  # name of the queue. Defined later
        self.news_routing = set() # set to store the routing keys
        self.online_editors = set() # set to store online editors

    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # Connect to the broker
        self.__connect()

        # Subscribe to "editors" exchange to receive announcements of who is online or offline
        self.__add_subscription(exchange=constants.EDITORS_EXCHANGE_NAME)

        # Start thread to listen to subscribe/unsubscribe commands
        command_thread = threading.Thread(target=self.__listen_for_commands)
        command_thread.daemon = True  # Daemonize thread
        command_thread.name = "CommandListener"
        command_thread.start()
        
        # Loop to receive messages
        self.__wait_for_news()

    def __connect(self):
        """
        Connect to the broker using TLS and authentication
        """
        # Create SSL context with CA and client certificates
        context = ssl.create_default_context(cafile=constants.CA_CERT_FILE)
        context.load_cert_chain(constants.CLIENT_CERT_FILE, constants.CLIENT_KEY_FILE)

        # Provide RabbitMQ credentials
        credentials = pika.PlainCredentials(self.username, self.password)

        # Set connection parameters including SSL
        parameters = pika.ConnectionParameters(
            host=constants.RABBITMQ_HOST,
            port=constants.RABBITMQ_PORT,
            virtual_host=constants.RABBITMQ_VHOST,
            credentials=credentials,
            ssl_options=pika.SSLOptions(context)
        )

        # Connect to the broker
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logging.info("Subscriber connected.")

        # Create a temporary queue (exclusive)
        queue_result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = queue_result.method.queue
        logging.debug(f"Queue {self.queue_name} created.")

        # Subscribe to the queue
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self.__callback, auto_ack=True
        )
        logging.debug(f"Queue {self.queue_name} is waiting for messages.")

    def __add_subscription(self, exchange: str, routing: str = ""):
        """
        Subscribe to a queue

        :param exchange: The exchange name to subscribe to
        :param routing: The routing key to bind to the queue. Default is ""
        """        
        # Bind the queue to the exchange (if the exchange is of type 'fanout', the routing key is ignored)
        self.channel.queue_bind(exchange=exchange, queue=self.queue_name, routing_key=routing)
        logging.debug(f"Queue {self.queue_name} bound to exchange {exchange} with routing key {routing}.")
        
        # Format routing key for better readability
        routingKeyFormatted = constants.format_routing_key(routing)

        # Store the mapping of exchange to queue
        self.news_routing.add(routing)
        logging.info(f"✅ Subscribed to {exchange} with routing key {routingKeyFormatted}.")

    def __remove_subscription(self, exchange: str, routing: str):
        """
        Unsubscribe from a queue routing key

        :param exchange: The exchange name which the queue is bound to
        :param routing: The routing key to unbind from the queue
        """
        routingKeyFormatted = constants.format_routing_key(routing)
        if routing in self.news_routing:
            self.channel.queue_unbind(exchange=exchange, queue=self.queue_name, routing_key=routing)
            self.news_routing.remove(routing)
            logging.info(f"💢 Unsubscribed from {exchange} on {routingKeyFormatted}.")
        else:
            logging.warning(f"⚡️ Not subscribed to {exchange} on {routingKeyFormatted}.")

    def __wait_for_news(self):
        """
        Wait for news
        """
        logging.info("🚀 Subscriber is waiting for news.")
        while self.running:
            self.connection.process_data_events()
            time.sleep(0.1)
        # Safely close the connection
        self.connection.close()

    def __listen_for_commands(self):
        """
        A thread that listens for user commands:
          - subscribe <topic>
          - unsubscribe <topic>
          - subscribeeditor <editorName>
          - unsubscribeeditor <editorName>
          - exit
        """
        print("Commands available:")
        print("- subscribe <topic>")
        print("- unsubscribe <topic>")
        print("- subscribeeditor <editorName>")
        print("- unsubscribeeditor <editorName>")
        print("- exit")

        while self.running:
            try:
                # Get the command from the user
                cmd = input(">> ").strip()
                args = cmd.split(" ", 1)
                if cmd == "exit":
                    self.exit()
                    break
                elif len(args) > 1:
                    parameter = args[1]
                    if cmd.startswith("subscribe "):
                        # ex: subscribe weather
                        typeToCheck = parameter.split('.')[0]
                        if typeToCheck not in constants.NEWS_TYPES:
                            logging.error(f"⚡️ Invalid news type: {parameter}")
                            continue
                        self.__add_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"*.{parameter}.#")
                    elif cmd.startswith("unsubscribe "):
                        # ex: unsubscribe weather
                        self.__remove_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"*.{parameter}.#")

                    elif cmd.startswith("subscribeeditor "):
                        # ex: subscribeeditor Bob
                        self.__add_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"{parameter}.#")
                    elif cmd.startswith("unsubscribeeditor "):
                        # ex: unsubscribeeditor Bob
                        self.__remove_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"{parameter}.#")
                    else:
                        logging.error(f"⚡️ Invalid command: {cmd}")
                else:
                    logging.error(f"⚡️ Invalid command: {cmd}")
                
            except EOFError:
                break

    def __callback(self, ch, method, properties, body):
        """
        Callback function that is called when a new message is received

        :param ch: The channel
        :param method: The method frame
        :param properties: The properties frame
        :param body: The message body
        """
        exchange_name = method.exchange
        routing_key = method.routing_key
        message = body.decode('utf-8')
        logging.debug(f"Received on \"{exchange_name}\" on \"{routing_key}\": {message}")

        # Format routing key for better readability
        routingKeyFormatted = constants.format_routing_key(routing_key)

        # Log the reception
        logging.info(f"➡️ Received on \"{exchange_name}\" on \"{routingKeyFormatted}\": {message}")

        # Manage message received from the editor exchange
        if exchange_name == constants.EDITORS_EXCHANGE_NAME:
            self.__handle_editor_announcement(message)

    def __handle_editor_announcement(self, announcement: str):
        """
        Update the editor list based on the announcement received.
        Example of announcement:
          "Editor \"Bob\" is online."
          "Editor \"Bob\" is offline."

        :param announcement: The announcement message
        """
        # Regex to extract the editor name and status
        match = re.match(r'Editor "([^"]+)" is (online|offline)\.', announcement)
        if match:
            editor_name = match.group(1)
            status = match.group(2)
            if status == "online":
                self.online_editors.add(editor_name)
                logging.info(f"✨ Editor {editor_name} added to online list.")
            else:
                # offline
                if editor_name in self.online_editors:
                    self.online_editors.remove(editor_name)
                    logging.info(f"🛑 Editor {editor_name} removed from online list.")

    def exit(self):
        """
        Stop the subscriber
        """
        self.running = False
        logging.info("Subscriber stopped.")
