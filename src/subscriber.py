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
import pika.exceptions
import constants

logging.getLogger("pika").setLevel(logging.ERROR)
logging.getLogger("pika.adapters.utils.io_services_utils").setLevel(logging.ERROR)

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
        self.map_news_routing_priory = {} # map to store the routing keys and their priorities
        self.messages = {
            constants.PRIORITY_LOW: [],
            constants.PRIORITY_MEDIUM: [],
            constants.PRIORITY_HIGH: []
        } # list to store messages received
        self.current_priority = constants.PRIORITY_HIGH # current priority level to show
        self.online_editors = set() # set to store online editors

    # ──────────────────────────────────────────────────────────
    # main thread life-cycle
    # ──────────────────────────────────────────────────────────
    def run(self):
        """
        Handle the lifecycle of the subscriber
        """
        # 1) Connect to the broker
        self.__connect()

        # 2) Always listen to editor announcements
        self.__add_subscription(exchange=constants.EDITORS_EXCHANGE_NAME)

        # 3) Start the CLI command listener in a helper thread
        command_thread = threading.Thread(target=self.__listen_for_commands,
                                          daemon=True,
                                          name="CommandListener")
        command_thread.start()

        # 4) Enter the main receive loop
        self.__wait_for_news()

    # ──────────────────────────────────────────────────────────
    # connection / channel setup  ← FIXED: now at class level
    # ──────────────────────────────────────────────────────────
    def __connect(self):
        """
        Connect to broker with TLS, authenticate, declare exchanges,
        declare queue and (re)bind any existing subscriptions.
        """
        # TLS setup
        context = ssl.create_default_context(cafile=constants.CA_CERT_FILE)
        context.load_cert_chain(constants.CLIENT_CERT_FILE,
                                constants.CLIENT_KEY_FILE)
        creds = pika.PlainCredentials(self.username, self.password)

        last_exc = None
        for host, port in constants.RABBITMQ_NODES:
            try:
                params = pika.ConnectionParameters(
                    host=host,
                    port=port,
                    virtual_host=constants.RABBITMQ_VHOST,
                    credentials=creds,
                    ssl_options=pika.SSLOptions(context),
                    connection_attempts=3,
                    retry_delay=2
                )
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                logging.info(f"✅ Connected to RabbitMQ at {host}:{port}")

                # Declare the two exchanges (fanout & topic)
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

                # Declare exclusive, auto-delete queue and start consuming
                qr = self.channel.queue_declare(queue='', exclusive=True)
                self.queue_name = qr.method.queue
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.__callback,
                    auto_ack=True
                )
                logging.info(f"Subscriber queue '{self.queue_name}' declared")

                # Rebind any prior subscriptions (on reconnect)
                self.__rebind_subscriptions()
                return

            except Exception as e:
                last_exc = e
                logging.warning(f"⚠️ {host}:{port} unavailable ({e.__class__.__name__}); trying next…")

        raise ConnectionError(f"❌ All connection attempts failed: {last_exc!r}")

    def __rebind_subscriptions(self):
        """
        After reconnect, re-bind the queue to all exchanges
        based on stored routing keys.
        """
        if not self.map_news_routing_priory:
            return

        for routing, _ in self.map_news_routing_priory.items():
            exch = (constants.EDITORS_EXCHANGE_NAME if routing == ""
                    else constants.NEWS_EXCHANGE_NAME)
            self.channel.queue_bind(
                exchange=exch,
                queue=self.queue_name,
                routing_key=routing
            )
        logging.info("🔄 Rebound existing subscriptions after reconnect")

    def __wait_for_news(self):
        """
        Main loop: process events and handle forced shutdowns by reconnecting.
        """
        logging.info(f"🚀 Waiting for news (showing '{self.current_priority}' priority)...")
        while self.running:
            try:
                self.connection.process_data_events()
            except pika.exceptions.AMQPConnectionError:
                logging.warning("⚠️ Lost connection to broker—reconnecting…")
                try:
                    self.__connect()
                    logging.info("🔌 Reconnected to broker.")
                except Exception:
                    logging.warning("⚠️ Reconnect attempt failed; will retry shortly.")
                    time.sleep(2)
                    continue
            time.sleep(0.1)
        self.connection.close()

    def __add_subscription(self, exchange: str, routing: str = "", priority: str = constants.PRIORITY_HIGH):
        """
        Subscribe to a queue

        :param exchange: The exchange name to subscribe to
        :param routing: The routing key to bind to the queue. Default is ""
        :param priority: The priority of the subscription. Default is constants.PRIORITY_HIGH
        """
        # Check if priority is valid
        if priority not in [constants.PRIORITY_LOW, constants.PRIORITY_MEDIUM, constants.PRIORITY_HIGH]:
            logging.error(f"⚡️ Invalid priority: {priority}. Must be one of \"{constants.PRIORITY_LOW}\", \"{constants.PRIORITY_MEDIUM}\", \"{constants.PRIORITY_HIGH}\".")
            return

        # Check if not already subscribed
        if routing in self.map_news_routing_priory:
            routingKeyFormatted = self.__format_routing_key(routing)
            if self.map_news_routing_priory[routing] == priority:
                logging.warning(f"⚡️ Already subscribed to {routingKeyFormatted} with \"{priority}\" priority.")
                return
            else:
                self.map_news_routing_priory[routing] = priority
                logging.warning(f"✅ Changed priority of subscription to {routingKeyFormatted} to to \"{priority}\".")
                return

        # Bind the queue to the exchange (if the exchange is of type 'fanout', the routing key is ignored)
        self.channel.queue_bind(exchange=exchange, queue=self.queue_name, routing_key=routing)
        logging.debug(f"Queue {self.queue_name} bound to exchange {exchange} with routing key {routing}.")
        
        # Format routing key for better readability
        routingKeyFormatted = self.__format_routing_key(routing)

        # Store the mapping of exchange to queue
        self.map_news_routing_priory[routing] = priority
        logging.info(f"✅ Subscribed to {exchange} with routing key {routingKeyFormatted} and {priority} priority.")

    def __remove_subscription(self, exchange: str, routing: str):
        """
        Unsubscribe from a queue routing key

        :param exchange: The exchange name which the queue is bound to
        :param routing: The routing key to unbind from the queue
        """
        routingKeyFormatted = self.__format_routing_key(routing)
        if routing in self.map_news_routing_priory:
            self.channel.queue_unbind(exchange=exchange, queue=self.queue_name, routing_key=routing)
            del self.map_news_routing_priory[routing]
            logging.info(f"💢 Unsubscribed from {routingKeyFormatted}.")
        else:
            logging.warning(f"⚡️ Not subscribed to {routingKeyFormatted}.")

    def __listen_for_commands(self):
        """
        A thread that listens for user commands:
          - subscribe <topic> [<priority_level_name>]
          - unsubscribe <topic> [<priority_level_name>]
          - subscribeeditor <editorName>
          - unsubscribeeditor <editorName>
          - showPriority <priority_level_name>
          - exit
        """
        print("Commands available:")
        print("- subscribe <topic> [<low/medium/high>]")
        print("- unsubscribe <topic>")
        print("- subscribeeditor <editorName> [<low/medium/high>]")
        print("- unsubscribeeditor <editorName>")
        print("- showPriority <low/medium/high>")
        print("- exit")

        while self.running:
            try:
                # Get the command from the user
                cmd = input(">> ").strip()
                args = cmd.split(" ")
                # Skip if the command is empty
                if cmd == "":
                    continue
                # Exit the system if the command is "exit"
                if cmd == "exit":
                    self.exit()
                    break
                # Handle subscribe/unsubscribe commands
                elif len(args) > 1:
                    # Get the topic or editor name
                    parameter = args[1]
                    # Get the priority if provided
                    priority = constants.PRIORITY_HIGH
                    if len(args) > 2:
                        priority = args[2]
                    if cmd.startswith("subscribe "):
                        # ex: subscribe weather
                        typeToCheck = parameter.split('.')[0]
                        if typeToCheck not in constants.NEWS_TYPES:
                            logging.error(f"⚡️ Invalid news type: {parameter}")
                            continue
                        self.__add_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"*.{parameter}.#", priority=priority)
                    elif cmd.startswith("unsubscribe "):
                        # ex: unsubscribe weather
                        self.__remove_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"*.{parameter}.#")

                    elif cmd.startswith("subscribeeditor "):
                        # ex: subscribeeditor Bob
                        self.__add_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"{parameter}.#", priority=priority)
                    elif cmd.startswith("unsubscribeeditor "):
                        # ex: unsubscribeeditor Bob
                        self.__remove_subscription(exchange=constants.NEWS_EXCHANGE_NAME, routing=f"{parameter}.#")

                    elif cmd.startswith("showPriority "):
                        priority = args[1]
                        # ex: showPriority high
                        if priority in [constants.PRIORITY_LOW, constants.PRIORITY_MEDIUM, constants.PRIORITY_HIGH]:
                            self.current_priority = priority
                            logging.info(f"🚩 Showing only news with priority \"{priority}\".")
                            if (self.messages[priority] != []):
                                logging.info(f"🏛️ News with priority \"{priority}\":")
                                for message in self.messages[priority]:
                                    logging.info(f"- {message}")
                        else:
                            logging.error(f"⚡️ Invalid priority: {priority}. Must be one of \"{constants.PRIORITY_LOW}\", \"{constants.PRIORITY_MEDIUM}\", \"{constants.PRIORITY_HIGH}\".")
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

        # Get the priority associated with the routing key
        routingKeyFormatted = self.__format_routing_key(routing_key)
        priority = None
        for pattern, p in self.map_news_routing_priory.items():
            if self.__matches_pattern(pattern, routing_key):
                priority = p
                logging.debug(f"Found priority \"{priority}\" for routing key \"{routingKeyFormatted}\".")
                break
        if (priority is None):
            logging.error(f"⚡️ No priority found for routing key \"{routingKeyFormatted}\". Ignoring message.")
            return

        # Log the reception of the message
        text = f"➡️ Received on \"{exchange_name}\" on \"{routingKeyFormatted}\": {message}"
        if (priority == self.current_priority):
            logging.info(text)

        # Store the received message in the appropriate priority list
        self.messages[priority].append(text)

        # Manage message received from the editor exchange
        if exchange_name == constants.EDITORS_EXCHANGE_NAME:
            self.__handle_editor_announcement(message, priority=priority)

    def __matches_pattern(self, pattern: str, routing_key: str) -> bool:
        """
        Check if a routing key matches a pattern with wildcards.
        RabbitMQ wildcards:
        * (star) matches exactly one word
        # (hash) matches zero or more words
        """
        pattern_parts = pattern.split('.')
        key_parts = routing_key.split('.')

        i = j = 0
        while i < len(pattern_parts) and j < len(key_parts):
            if pattern_parts[i] == '#':
                return True  # '#' matches the rest
            elif pattern_parts[i] == '*':
                i += 1
                j += 1
            elif pattern_parts[i] == key_parts[j]:
                i += 1
                j += 1
            else:
                return False

        # Handle remaining parts
        if i < len(pattern_parts) and pattern_parts[i] == '#':
            i += 1

        return i == len(pattern_parts) and j == len(key_parts)

    def __handle_editor_announcement(self, announcement: str, priority: str):
        """
        Update the editor list based on the announcement received.
        Example of announcement:
          "Editor \"Bob\" is online."
          "Editor \"Bob\" is offline."

        :param announcement: The announcement message
        :param priority: The priority of the announcement
        """
        # Regex to extract the editor name and status
        match = re.match(r'Editor "([^"]+)" is (online|offline)\.', announcement)
        if match:
            editor_name = match.group(1)
            status = match.group(2)
            text = ""
            if status == "online":
                self.online_editors.add(editor_name)
                text = f"✨ Editor {editor_name} added to online list."
            else:
                # offline
                if editor_name in self.online_editors:
                    self.online_editors.remove(editor_name)
                    text = f"🛑 Editor {editor_name} removed from online list."
            if text != "":
                self.messages[priority].append(text)
                logging.info(text)

    def __format_routing_key(self, routing_key: str) -> str:
        """
        Format the routing key to better readability in the logs
        """
        return routing_key.replace('.#', '').replace('*.', '')

    def exit(self):
        """
        Stop the subscriber
        """
        self.running = False
        logging.info("Subscriber stopped.")
