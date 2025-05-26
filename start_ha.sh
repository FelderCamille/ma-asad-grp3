#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# start_ha.sh  –  one-command demo runner
#   • generates TLS certs the first time
#   • boots the 2-node RabbitMQ cluster
#   • forces rabbit2 to join rabbit1
#   • declares a quorum queue called “news”
# -----------------------------------------------------------------------------
set -euo pipefail

PROJECT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P )"
CERT_DIR="$PROJECT_DIR/certs"
CERT_SCRIPT="$CERT_DIR/generate-certs.sh"   # ← point to certs/ folder
COMPOSE="docker compose -f docker-compose-ha.yml"
CREDS="-u admin:supersecureadmin"

# ─────────────────────────────────────────────────────────────────────────────
# 1) Generate TLS certificates once
# ─────────────────────────────────────────────────────────────────────────────
if [[ ! -f "$CERT_DIR/ca_certificate.pem" ]]; then
  echo "🔑  TLS certs not found – generating them ..."
  chmod +x "$CERT_SCRIPT"
  "$CERT_SCRIPT"
  echo
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2) Clean any previous run (optional)
# ─────────────────────────────────────────────────────────────────────────────
echo "⏹  Stopping any leftover containers …"
$COMPOSE down -v >/dev/null 2>&1 || true

# ─────────────────────────────────────────────────────────────────────────────
# 3) Start both brokers
# ─────────────────────────────────────────────────────────────────────────────
echo "🟢  Starting both brokers …"
$COMPOSE up -d

# ─────────────────────────────────────────────────────────────────────────────
# 4) Wait until the management API of each node is healthy
# ─────────────────────────────────────────────────────────────────────────────
echo "⏳  Waiting for rabbit1 to become healthy …"
until curl -s $CREDS http://localhost:15672/api/healthchecks/node | grep -q ok; do sleep 1; done

echo "⏳  Waiting for rabbit2 …"
until curl -s $CREDS http://localhost:15673/api/healthchecks/node | grep -q ok; do sleep 1; done

# ─────────────────────────────────────────────────────────────────────────────
# 5) Force rabbit2 to (re)join rabbit1 — idempotent
# ─────────────────────────────────────────────────────────────────────────────
echo "🔗  Manually joining rabbit2 to rabbit1 …"
docker exec rabbit2 rabbitmqctl stop_app
docker exec rabbit2 rabbitmqctl reset
docker exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1
docker exec rabbit2 rabbitmqctl start_app

 # ─────────────────────────────────────────────────────────────────────────────
 # 6) Declare (or re-declare) quorum queue “news” via HTTP API
 # ─────────────────────────────────────────────────────────────────────────────

echo "📦  Declaring quorum queue “news” in vhost “news” via HTTP API …"
curl -s $CREDS \
  -H "Content-Type: application/json" \
  -X PUT \
  http://localhost:15672/api/queues/news/news \
  -d '{"durable":true,"auto_delete":false,"arguments":{"x-queue-type":"quorum"}}' \
  && echo "   → “news” queue declared as quorum in vhost “news”."

# ─────────────────────────────────────────────────────────────────────────────
# 7) All set
# ─────────────────────────────────────────────────────────────────────────────
echo
echo "✅  Cluster ready!"
echo "   • Node-1 UI → http://localhost:15672"
echo "   • Node-2 UI → http://localhost:15673"