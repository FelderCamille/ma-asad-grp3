#!/usr/bin/env bash
set -euo pipefail
COMPOSE="docker compose -f docker-compose-ha.yml"
CREDS="-u admin:supersecureadmin"

echo "⏹ Stopping any leftover…"
$COMPOSE down -v

echo "🟢 Starting both brokers…"
$COMPOSE up -d

echo "⏳ Waiting for rabbit1 to become healthy…"
until curl -s $CREDS http://localhost:15672/api/healthchecks/node | grep -q ok; do
  sleep 1
done

echo "⏳ Waiting for rabbit2…"
until curl -s $CREDS http://localhost:15673/api/healthchecks/node | grep -q ok; do
  sleep 1
done

echo "🔗 Manually joining rabbit2 to rabbit1…"
docker exec rabbit2 rabbitmqctl stop_app
docker exec rabbit2 rabbitmqctl reset
docker exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1
docker exec rabbit2 rabbitmqctl start_app

echo "📦 Declaring quorum queue “news” via HTTP API…"
curl -s $CREDS \
  -H "Content-Type: application/json" \
  -X PUT \
  http://localhost:15672/api/queues/%2F/news \
  -d '{
    "durable": true,
    "auto_delete": false,
    "arguments": {"x-queue-type":"quorum"}
  }' \
  && echo "   → “news” queue declared as quorum."

echo
echo "✅ Cluster ready!"
echo "   • Node-1 UI → http://localhost:15672"
echo "   • Node-2 UI → http://localhost:15673"
