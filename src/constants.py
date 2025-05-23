#!/usr/bin/env python

# Broker host
RABBITMQ_HOST = 'localhost'
# Broker port (TLS)
RABBITMQ_PORT = 5671
# Broker virtual host
RABBITMQ_VHOST = 'news'

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