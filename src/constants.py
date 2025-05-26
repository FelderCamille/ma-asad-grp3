#!/usr/bin/env python

# --- RabbitMQ nodes for failover (tls/AMQPS) ---
RABBITMQ_NODES = [
    ("localhost", 5671),   # node-1
    ("localhost", 5673),   # node-2
]
# Virtual host
RABBITMQ_VHOST = 'news'

# CA certificate path
CA_CERT_FILE = "./certs/ca_certificate.pem"
# Client certificate path
CLIENT_CERT_FILE = "./certs/client_certificate.pem"
# Client certificate path
CLIENT_KEY_FILE = "./certs/client_key.pem"

# News exchange name
NEWS_EXCHANGE_NAME = 'news'
# Editors announcement exchange name
EDITORS_EXCHANGE_NAME = 'editors'

# News types
NEWS_TYPES = [
    'sports', 
    'politics', 
    'economy', 
    'weather',
    'history',
    'technology',
    'entertainment',
    'health',
    'science',
    'education',
]

# Priority levels
PRIORITY_LOW = 'low'
PRIORITY_MEDIUM = 'medium'
PRIORITY_HIGH = 'high'