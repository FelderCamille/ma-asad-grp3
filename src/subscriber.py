#!/usr/bin/env python3

"""
Manage the news subscriber
"""

import logging
import threading
import pika
import time
import re

import constants

class Subscriber(threading.Thread):
    """
    A subscriber can subscribe to editors, news types, and receive news
    """

    def __init__(self):
        """
        Constructor
        """
        super(Subscriber, self).__init__()  # execute super class constructor
        self.running = True  # flag to indicate if the subscriber is running
        self.exchange_queue_map = {} # dictionary to store the mapping of exchanges to queues
        self.online_editors = set() # set to store online editors

    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # Connect to the broker
        self.__connect()

        # Subscribe to "editors" exchange to receive announcements of who is online or offline
        self.__add_subscription(constants.EDITORS_EXCHANGE_NAME)

        # Get the news types to subscribe to
        types = input("Enter the news types you want to subscribe to (separated by a space): ")
        types = types.split()

        # Check if the types are valid (in the enum values)
        for type_ in types:
            if type_ not in constants.NEWS_TYPES:
                logging.error(f"⚡️ Invalid news type: {type_}")
            else:
                self.__add_subscription(type_)

        # Start thread to listen to subscribe/unsubscribe commands
        command_thread = threading.Thread(target=self.listen_for_commands)
        command_thread.daemon = True  # Daemonize thread
        command_thread.name = "CommandListener"
        command_thread.start()
        
        # Loop to receive messages
        self.__wait_for_news()

    def __connect(self):
        """
        Connect to the broker
        """
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=constants.RABBITMQ_HOST)
        )
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
        
        # Create a temporary queue (exclusive)
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        # Store the mapping of exchange to queue
        self.exchange_queue_map[name] = queue_name
        
        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=name, queue=queue_name)
        logging.debug(f"Queue {queue_name} created and bound to exchange {name}.")
        
        # Subscribe to the queue
        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self.__callback, auto_ack=True
        )
        logging.info(f"✅ Subscribed to {name}.")

    def __remove_subscription(self, name: str):
        """
        Unsubscribe from a queue (unbind from exchange)

        :param name: The exchange name to unsubscribe from
        """
        if name in self.exchange_queue_map:
            queue_name = self.exchange_queue_map[name]
            self.channel.queue_unbind(exchange=name, queue=queue_name)
            del self.exchange_queue_map[name]
            logging.info(f"💢 Unsubscribed from {name}.")
        else:
            logging.warning(f"⚡️ Not subscribed to {name}.")

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

    def listen_for_commands(self):
        """
        A thread that listens for user commands:
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
                    if cmd.startswith("unsubscribe "):
                        # ex: unsubscribe weather
                        self.__remove_subscription(parameter)

                    elif cmd.startswith("subscribeeditor "):
                        # ex: subscribeeditor editor_Bob
                        editor_exchange = f"editor_{parameter.replace(' ', '_')}"
                        self.__add_subscription(editor_exchange)
                    elif cmd.startswith("unsubscribeeditor "):
                        # ex: unsubscribeeditor editor_Bob
                        editor_exchange = f"editor_{parameter.replace(' ', '_')}"
                        self.__remove_subscription(editor_exchange)
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
        message = body.decode('utf-8')

        # Log the reception
        logging.info(f"➡️ Received on \"{exchange_name}\": {message}")

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
