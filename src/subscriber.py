#!/usr/bin/env python
import pika

import constants

# Establish a connection to the RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters(host=constants.RABBITMQ_HOST))
channel = connection.channel()

print(' [*] Waiting for logs. To exit press CTRL+C')

# Prepare callback function
def callback(ch, method, properties, body):
    print(f" [x] {body}")

# Subscribe to the queue
channel.basic_consume(queue='test', on_message_callback=callback, auto_ack=True)

# Start consuming messages
channel.start_consuming()