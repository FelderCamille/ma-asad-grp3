#!/bin/bash

mkdir -p certs
cd certs

echo "→ Generating CA..."
openssl genrsa -out ca_key.pem 2048
openssl req -x509 -new -nodes -key ca_key.pem -sha256 -days 365 -out ca_certificate.pem -subj "/CN=MyRabbitCA"

echo "→ Generating server certificate..."
openssl genrsa -out server_key.pem 2048
openssl req -new -key server_key.pem -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca_certificate.pem -CAkey ca_key.pem -CAcreateserial -out server_certificate.pem -days 365 -sha256

echo "→ Generating client certificate..."
openssl genrsa -out client_key.pem 2048
openssl req -new -key client_key.pem -out client.csr -subj "/CN=client1"
openssl x509 -req -in client.csr -CA ca_certificate.pem -CAkey ca_key.pem -CAcreateserial -out client_certificate.pem -days 365 -sha256

rm *.csr *.srl
echo "✔ Certificates generated."

echo "→ Setting permissions..."
# Private keys should only be readable by the system
chmod 644 server_key.pem
# Certificates can be public
chmod 644 server_certificate.pem
# The script itself remains executable
chmod 644 ca_certificate.pem
# Change ownership back to current user if script was run with sudo
chown $SUDO_USER:$SUDO_USER *.pem

echo "✔ Certificats générés et permissions appliquées."