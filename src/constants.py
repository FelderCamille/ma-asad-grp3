#!/usr/bin/env python

# Broker host
RABBITMQ_HOST = 'localhost'
# Broker port (TLS)
RABBITMQ_PORT = 5671
# Broker virtual host
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