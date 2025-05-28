#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# stop_ha.sh  –  one-command demo runner
#   • stops all RabbitMQ containers
#   • remove all certs
# -----------------------------------------------------------------------------

COMPOSE="docker compose -f docker-compose-ha.yml"

# Stop the RabbitMQ containers
$COMPOSE down -v

# Remove the certificates
cd certs
find . -name "*.pem" -type f -delete
find . -name "*.srl" -type f -delete