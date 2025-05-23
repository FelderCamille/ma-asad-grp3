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

    def __init__(self, editor_name, username, password):
        """
        Constructor
        """
        super(Editor, self).__init__()  # execute super class constructor
        self.running = True  # flag to indicate if the editor is running
        self.editor_name = editor_name.replace(' ', '_') # retain the name for creating the editor-specific news
        self.username = username
        self.password = password
        

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
            if types == '':
                continue # skip if empty
            types = types.split()
            if not self.running:
                break

            # Check if the types are valid, if not ask again
            invalid_type = False
            for type_ in types:
                typeToCheck = type_.split('.')[0]
                if typeToCheck not in constants.NEWS_TYPES:
                    logging.error(f"Invalid news type: {typeToCheck}")
                    invalid_type = True
            if invalid_type:
                continue

            # Get the news content
            content = input("Enter the news content: ")
            if content == '':
                continue # skip if empty
            # Send the news
            for type_ in types:
                self.__send_to_subscribers(
                    exchange=constants.NEWS_EXCHANGE_NAME, 
                    content=content,
                    routing=f"{self.editor_name}.{type_}"
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
            port=constants.RABBITMQ_PORT,
            virtual_host=constants.RABBITMQ_VHOST,
            credentials=credentials,
            ssl_options=pika.SSLOptions(context)
        )

        # Connect to the broker
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logging.info("Editor connected.")

        # Publish that the editor is online
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f"{self.name} is online."
        )

    def __send_to_subscribers(self, exchange: str, content: str, routing: str = ''):
        """
        Send data to the subscribers

        :param exchange: The name of the exchange
        :param content: The content to send
        :param routing: The routing key to bind. Default is ''
        """
        # Publish on the queue
        self.channel.basic_publish(exchange=exchange, body=content, routing_key=routing)
        logging.info(f"➡️ Sent \"{exchange}\" on \"{routing}\": {content}")

    def exit(self):
        """
        Close the connection
        """
        self.running = False
        # Indicate editor's deconnection
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f"{self.name} is offline.",
        )
        self.connection.close()
        logging.info("Editor disconnected.")
