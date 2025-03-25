#!/usr/bin/env python
import pika
import sys

import constants

# Establish a connection to the RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
channel = connection.channel()

# Declare the exchange
channel.exchange_declare(exchange=constants.EXCHANGE_NAME, exchange_type='direct')

# Declare a queue and bind it to the exchange
queue_name = 'test'
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(exchange=constants.EXCHANGE_NAME, queue=queue_name)

# Publish a message to the exchange
message = ' '.join(sys.argv[1:]) or "info: Hello World!"
channel.basic_publish(exchange=constants.EXCHANGE_NAME, routing_key=queue_name, body=message)
print(f" [x] Sent {message}")

# Close the connection
connection.close()