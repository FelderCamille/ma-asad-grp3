#!/usr/bin/env python3

"""
Manage the news editor
"""

import logging
import threading
import pika
import ssl

import constants

class Editor(threading.Thread):
    """
    An editor can send news to the broker
    """

    def __init__(self, editor_name, username, password, vhost = "news"):
        """
        Constructor
        """
        super(Editor, self).__init__()  # execute super class constructor
        self.running = True  # flag to indicate if the editor is running
        self.editor_exchange = f"editor_{editor_name.replace(' ', '_')}" # retain the name for creating the editor-specific exchange
        
        self.username = username
        self.password = password
        self.vhost = vhost
        

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
            if not self.running:
                break

            # Check if the types are valid, if not ask again
            invalid_type = False
            for type_ in types:
                if type_ not in constants.NEWS_TYPES:
                    logging.error(f"Invalid news type: {type_}")
                    invalid_type = True
            if invalid_type:
                continue

            # Get the news content
            news = input("Enter the news: ")
            # Send the news
            for type_ in types:
                # 1) Send the news to the subscribers of the type of news
                self.__send_to_subscribers(name=type_, content=news)

                # 2) Send the news to the subscribers of the editor
                self.__send_to_subscribers(
                    name=self.editor_exchange,
                    content=f"[{type_}] {news}"
                )

    def __connect(self):
        """
        Connect to the broker using TLS and authentication
        """
        # Create SSL context with CA and client certificates
        context = ssl.create_default_context(cafile="certs/ca_certificate.pem")
        context.load_cert_chain("certs/client_certificate.pem", "certs/client_key.pem")

        # Provide RabbitMQ credentials
        credentials = pika.PlainCredentials(self.username, self.password)

        # Set connection parameters including SSL
        parameters = pika.ConnectionParameters(
            host=constants.RABBITMQ_HOST,
            port=5671,
            virtual_host=self.vhost,
            credentials=credentials,
            ssl_options=pika.SSLOptions(context)
        )   
        self.connection = pika.BlockingConnection(
            parameters
        )
        self.channel = self.connection.channel()
        logging.info("Editor connected.")

        # Indique que l'éditeur est en ligne sur l’exchange général "editors"
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f"{self.name} is online."
        )

    def __send_to_subscribers(self, name: str, content: str):
        """
        Send data to the subscribers

        :param name: The name of the exchange
        :param content: The content to send
        """
        self.channel.exchange_declare(exchange=name, exchange_type=constants.EXCHANGE_TYPE)
        logging.debug(f"Exchange {name} created if does not exist.")
        # Publish on the queue
        self.channel.basic_publish(exchange=name, routing_key='', body=content)
        logging.info(f"➡️ Sent on \"{name}\": {content}")

    def exit(self):
        """
        Close the connection
        """
        self.running = False
        # Annonce la déconnexion sur l’exchange 'editors'
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f"{self.name} is offline."
        )
        self.connection.close()
        logging.info("Editor disconnected.")
