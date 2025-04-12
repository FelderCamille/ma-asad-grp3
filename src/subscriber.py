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
    A subscriber can subscribe to news types and receive news
    """

    def __init__(self):
        """
        Constructor
        """
        super(Subscriber, self).__init__()  # execute super class constructor
        self.running = True  # flag to indicate if the subscriber is running

        # Dictionnaires pour stocker les queues par exchange
        self.exchange_queue_map = {}
        # Liste ou dict pour conserver les noms d’éditeurs qu’on sait "online"
        self.online_editors = set()

    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # Connect to the broker
        self.__connect()

        # 1) On s'abonne systématiquement à l’exchange "editors" pour recevoir les
        #    annonces de qui rejoint ou quitte.
        self.__add_subscription(constants.EDITORS_EXCHANGE_NAME)

        # 2) Saisie initiale des types de news
        types = input("Enter the news types you want to subscribe to (separated by a space): ")
        types = types.split()

        # Vérification
        for type_ in types:
            if type_ not in constants.NEWS_TYPES:
                logging.error(f"Invalid news type: {type_}")
            else:
                self.__add_subscription(type_)

        # 3) Lancement du thread de commande en arrière-plan
        command_thread = threading.Thread(target=self.listen_for_commands)
        command_thread.daemon = True  # Daemonize thread
        command_thread.start()
        
        # 4) Boucle de réception des messages
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

    def __add_subscription(self, exchange_name: str):
        """
        Subscribe to a queue

        :param exchange_name: The exchange name to subscribe to
        """
        # Create the exchange if not exists
        self.channel.exchange_declare(exchange=exchange_name, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {exchange_name} created if does not exist.")
        
        # Create a temporary queue (exclusive)
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        # Mémorise la correspondance
        self.exchange_queue_map[exchange_name] = queue_name
        
        # Bind the queue to the exchange
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name)
        logging.debug(f"Queue {queue_name} created and bound to exchange {exchange_name}.")
        
        # Subscribe to the queue
        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self.__callback, auto_ack=True
        )
        logging.info(f"✅ Subscribed to {exchange_name}.")

    def __remove_subscription(self, exchange_name: str):
        """
        Unsubscribe from a queue (unbind from exchange)
        """
        if exchange_name in self.exchange_queue_map:
            queue_name = self.exchange_queue_map[exchange_name]
            self.channel.queue_unbind(exchange=exchange_name, queue=queue_name)
            del self.exchange_queue_map[exchange_name]
            logging.info(f"💢 Unsubscribed from {exchange_name}.")
        else:
            logging.warning(f"Not subscribed to {exchange_name}.")

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
        print("- unsubscribe <topic>")
        print("- subscribeeditor <editorName>")
        print("- unsubscribeeditor <editorName>")
        print("- exit")

        while self.running:
            try:
                cmd = input(">> ").strip()
                if cmd.startswith("unsubscribe "):
                    # ex: unsubscribe weather
                    topic = cmd.split(" ", 1)[1]
                    self.__remove_subscription(topic)

                elif cmd.startswith("subscribeeditor "):
                    # ex: subscribeeditor EditorBob
                    editor_cmd = cmd.split(" ", 1)[1]
                    # L’exchange d’un éditeur est "editor_<nom>"
                    editor_exchange = f"editor_{editor_cmd.replace(' ', '_')}"
                    self.__add_subscription(editor_exchange)

                elif cmd.startswith("unsubscribeeditor "):
                    # ex: unsubscribeeditor EditorBob
                    editor_cmd = cmd.split(" ", 1)[1]
                    editor_exchange = f"editor_{editor_cmd.replace(' ', '_')}"
                    self.__remove_subscription(editor_exchange)

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
        message = body.decode('utf-8')

        # Log the reception
        logging.info(f"➡️ Received on \"{exchange_name}\": {message}")

        # Si on reçoit quelque chose sur l’exchange "editors", on vérifie si c’est
        # un message "is online" ou "is offline" pour MAJ la liste des éditeurs
        if exchange_name == constants.EDITORS_EXCHANGE_NAME:
            self.__handle_editor_announcement(message)

    def __handle_editor_announcement(self, announcement: str):
        """
        Gère les messages du type:
          "Editor \"Bob\" is online."
          "Editor \"Bob\" is offline."
        et met à jour la liste self.online_editors en conséquence.
        """
        # On peut extraire "Bob" via une expression régulière simple
        # Format actuel: Editor "Bob" is online.
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
