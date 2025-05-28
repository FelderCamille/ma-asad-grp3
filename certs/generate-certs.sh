#!/usr/bin/env bash
set -euo pipefail

# ─── Define CERT_DIR as the folder where this script lives ───────────────
CERT_DIR="$( cd -- "$( dirname "$0" )" >/dev/null 2>&1 && pwd -P )"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "→ Generating CA..."
openssl genrsa -out ca_key.pem 2048
openssl req -x509 -new -nodes -key ca_key.pem -sha256 -days 365 \
  -out ca_certificate.pem -subj "/CN=MyRabbitCA"

echo "→ Generating server certificates (with SAN for localhost)..."
for node in rabbit1 rabbit2; do
  echo "   • $node"
  # Key + CSR
  openssl genrsa -out ${node}_key.pem 2048
  openssl req -new -key ${node}_key.pem \
    -out ${node}.csr -subj "/CN=${node}"
  # SAN config
  cat > san.cnf <<EOF
[ v3_req ]
subjectAltName = DNS:${node},DNS:localhost
EOF
  # Sign CSR with SAN
  openssl x509 -req -in ${node}.csr \
    -CA ca_certificate.pem -CAkey ca_key.pem -CAcreateserial \
    -out ${node}_cert.pem -days 365 -sha256 \
    -extfile san.cnf -extensions v3_req
  rm -f san.cnf ${node}.csr
done

echo "→ Generating client certificate..."
openssl genrsa -out client_key.pem 2048
openssl req -new -key client_key.pem \
  -out client.csr -subj "/CN=client1"
openssl x509 -req -in client.csr \
  -CA ca_certificate.pem -CAkey ca_key.pem -CAcreateserial \
  -out client_certificate.pem -days 365 -sha256
rm -f client.csr

echo "→ Securing permissions..."
chmod 600 ca_key.pem rabbit1_key.pem rabbit2_key.pem client_key.pem
chmod 644 ca_certificate.pem rabbit1_cert.pem rabbit2_cert.pem client_certificate.pem

echo "✔ Certificates generated in: $CERT_DIR"
