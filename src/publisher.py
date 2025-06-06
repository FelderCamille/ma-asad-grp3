#!/usr/bin/env python3

"""
Manage the news editor
"""

import logging
import threading
import pika
import ssl
from collections import deque
import constants

for name in list(logging.root.manager.loggerDict):
    if name.startswith("pika"):
        pika_log = logging.getLogger(name)
        pika_log.setLevel(logging.CRITICAL)
        # 2) remove any handler Pika attached (prints regardless of level)
        pika_log.handlers.clear()

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
        self._outbox = deque()
        
    def run(self):
        """
        Handle the lifecycle of the editor, with automatic fail-over.
        """
        # 1) Initial connect
        try:
            self.__connect()
        except ConnectionError as err:          # e.g. wrong password on both nodes
            logging.error(err)
            logging.error("❌ Authentication failed — publisher will exit.")
            return
        # 2) Read/send loop
        while self.running:
            try:
                types = input("Enter the news type(s) (space-separated): ").split()
                if not types:
                    continue
                content = input("Enter the news content: ")
                if not content:
                    continue

                for type_ in types:
                    self.__send_to_subscribers(
                        exchange=constants.NEWS_EXCHANGE_NAME,
                        content=content,
                        routing=f"{self.editor_name}.{type_}"
                    )
            except pika.exceptions.AMQPConnectionError as e:
                logging.warning(f"⚠️ Publisher lost connection: {e!r}, reconnecting…")
                # try each node again
                self.__connect()
            except KeyboardInterrupt:
                break

        # 3) Clean exit
        self.exit()

    def __connect(self):
        """
        Connect to the broker using TLS and authentication, with automatic fail-over.
        """
        # 1) Build SSL context
        context = ssl.create_default_context(cafile=constants.CA_CERT_FILE)
        context.load_cert_chain(constants.CLIENT_CERT_FILE, constants.CLIENT_KEY_FILE)

        # 2) Credentials
        credentials = pika.PlainCredentials(self.username, self.password)

        # 3) Try each node in turn
        last_exc = None
        for host, port in constants.RABBITMQ_NODES:
            try:
                params = pika.ConnectionParameters(
                    host=host,
                    port=port,
                    virtual_host=constants.RABBITMQ_VHOST,
                    credentials=credentials,
                    ssl_options=pika.SSLOptions(context),
                    connection_attempts=3,
                    retry_delay=2
                )
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                logging.info(f"✅ Publisher connected to {host}:{port}")
                break
            except Exception as e:
                last_exc = e
                # if it’s bad credentials, don’t show Pika’s tracebacks again
                if isinstance(e, pika.exceptions.ProbableAuthenticationError):
                    logging.error("❌ Wrong username or password.")
                    raise ConnectionError("authentication failed")   # abort fast
                logging.warning(f"⚠️ {host}:{port} unavailable ({e.__class__.__name__}); trying next…")
        else:
            logging.critical("❌  No RabbitMQ node reachable – giving up.")
            raise SystemExit(1)

        # 4) Declare your exchanges
        self.channel.exchange_declare(
            exchange=constants.EDITORS_EXCHANGE_NAME,
            exchange_type='fanout',
            durable=True
        )
        self.channel.exchange_declare(
            exchange=constants.NEWS_EXCHANGE_NAME,
            exchange_type='topic',
            durable=True
        )

        # 5) Announce this editor is online
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f'Editor "{self.name}" is online.'
        )
        # 6) If messages were queued during an outage, send them now
        self.__flush_outbox()

    def __send_to_subscribers(self, exchange: str, content: str, routing: str = ""):
        """
        Send data to the subscribers

        :param exchange: The exchange name
        :param content:  Message body
        :param routing:  Routing key (may be empty)
        """
        # Buffer-then-publish with automatic retry on connection loss
        # 1) Park the message
        self._outbox.append((exchange, content, routing))
        # 2) Try to flush (will pop on success)
        try:
            self.__flush_outbox()
        except Exception as err:
            # Reconnect already attempted inside __flush_outbox
            logging.warning(f"⚠️  Publish deferred: {err!r}")
        else:
            routingKeyFormatted = f' on "{routing}"' if routing else ""
            logging.info(f"➡️ Sent on \"{exchange}\"{routingKeyFormatted}: {content}")

    def exit(self):
        """
        Close the connection
        """
        # Try to send any buffered news before going offline
        if self._outbox:
            logging.info("⏳ Flushing unsent messages before exit…")
            self.__flush_outbox()

        self.running = False
        # Indicate editor's deconnection
        self.__send_to_subscribers(
            constants.EDITORS_EXCHANGE_NAME,
            f"{self.name} is offline.",
        )
        self.connection.close()
        logging.info("Editor disconnected.")

    # ------------------------------------------------------------------ #
    #  Retry buffer                                                      #
    # ------------------------------------------------------------------ #
    def __flush_outbox(self) -> None:
        """
        Try to publish everything currently queued in self._outbox.
        Called after every reconnect and before normal publishing.
        """
        while self._outbox:
            exch, body, rk = self._outbox[0]        # peek
            try:
                self.channel.basic_publish(
                    exchange=exch,
                    routing_key=rk,
                    body=body,
                    properties=pika.BasicProperties(delivery_mode=2)  # persistent
                )
                self._outbox.popleft()              # success → drop
            except (pika.exceptions.AMQPError, OSError):
                # Connection died again → reconnect and retry remaining msgs
                self.__connect()

