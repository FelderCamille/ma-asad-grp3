# 📦 Project File Reference – RabbitMQ TLS News System


## 🔐 Certificates & TLS Configuration

### `ca_certificate.pem`
This is the public certificate of the self-signed Certificate Authority (CA) used to validate all other certificates in the system. It is trusted by both RabbitMQ and clients like publishers and subscribers. When the server receives a client certificate, it checks whether it was signed by this CA. It’s shared freely across the system but must match the private key in `ca_key.pem`.

### `ca_certificate.srl`
This file stores the serial number used by OpenSSL to track issued certificates. Each time a certificate is signed, the CA increments this number. It ensures uniqueness of issued certificates and is managed automatically by OpenSSL. This file is needed only during cert generation; it’s not used at runtime.

### `ca_key.pem`
This is the private key for the Certificate Authority. It is used to sign certificates for the RabbitMQ nodes and clients. This key must be kept secure and never shared publicly. Compromising this file would allow an attacker to forge valid certificates.

### `client_certificate.pem`
This certificate is used by publisher and subscriber clients to authenticate with the RabbitMQ server. It must be signed by the CA and is presented during the TLS handshake. It is typically validated by RabbitMQ when `verify_peer` is enabled. It ensures that only trusted clients can publish or receive messages.

### `client_key.pem`
This is the private key corresponding to the `client_certificate.pem`. It is used during the TLS handshake to prove the client’s identity. It should remain private and only be accessed by trusted applications like your Python clients. It works hand-in-hand with the certificate for secure authentication.

### `generate-certs.sh`
This shell script automates the creation of TLS certificates for the project. It generates a root Certificate Authority (CA), and uses it to sign certificates for the two RabbitMQ nodes (rabbit1, rabbit2) and an optional client certificate. The script ensures mutual TLS authentication can be enforced both between nodes and for client connections (e.g., publisher/subscriber). It’s called once at the beginning by `start_ha.sh` if certs are missing.

### `rabbit1_cert.pem`
The certificate used by the first RabbitMQ node (`rabbit1`). Signed by the project’s CA, it ensures the broker can authenticate itself to clients and to the other node. It is bound to the TLS port (5671) and the inter-node clustering port (25672). RabbitMQ presents this during incoming TLS connections.

### `rabbit1_key.pem`
The private key associated with `rabbit1_cert.pem`. It is used by `rabbit1` to establish TLS connections. Must be kept secret and secure inside the container. Only this node should ever have access to this file.

### `rabbit2_cert.pem`
The certificate used by the second RabbitMQ node (`rabbit2`). It is functionally identical to `rabbit1_cert.pem`, just for the second node. It is used both for AMQPS and inter-node TLS distribution. It must match the private key in `rabbit2_key.pem`.

### `rabbit2_key.pem`
The private key that goes with `rabbit2_cert.pem`. It is used during encrypted communication to prove the identity of rabbit2. It should only be accessed inside the container running `rabbit2`. Like all private keys, it must be protected from leaks.

## 💻 Python Source Code

### `constants.py`
*No detailed description available yet.*

### `publisher.py`
*No detailed description available yet.*

### `publisher_main.py`
*No detailed description available yet.*

### `requirements.txt`
*No detailed description available yet.*

### `subscriber.py`
*No detailed description available yet.*

### `subscriber_main.py`
*No detailed description available yet.*

## 🚀 Deployment Scripts & Docker Setup

### `docker-compose-ha.yml`
This file defines the Docker-based deployment of a two-node RabbitMQ cluster with TLS. It specifies the services, volumes, ports, environment variables, and certificates needed to run each node. It also links the services and sets up persistent configuration mounts. Used by `docker compose` to bring up or tear down the full system.

### `start_ha.sh`
A shell script that fully automates the cluster lifecycle for demo purposes. It generates certificates (if missing), boots both RabbitMQ nodes, joins `rabbit2` to `rabbit1`, and pre-declares the quorum queue. It makes the entire demo repeatable with one command. It also ensures readiness checks and proper boot order.

## ⚙️ RabbitMQ Configuration Files

### `inter_node_tls.config`
An Erlang-style config file defining TLS options for clustering (Erlang distribution). It tells RabbitMQ which certs and keys to use for inter-node encryption. It must be mounted inside the container and passed via Erlang flags. This file is necessary because RabbitMQ 3.13 does not support inter-node TLS settings in rabbitmq.conf.

### `rabbitmq-env.conf`
A config file that defines Erlang VM flags via environment variables. It is used to pass `-proto_dist inet_tls` and `-ssl_dist_optfile` so RabbitMQ uses TLS for clustering. The file ensures these flags are seen by both the broker and CLI tools. This is required for secure inter-node communication in RabbitMQ 3.13.

### `rabbitmq.conf`
The primary configuration file for RabbitMQ brokers. Defines listeners, TLS options, and management interface settings. Used to configure client TLS (AMQPS), disable guest access, and set up the HTTP API. Cluster-wide TLS for inter-node traffic is configured via `inter_node_tls.config` instead.

### `rabbitmq_setup.json`
A JSON file used to pre-configure RabbitMQ with users, vhosts, and permissions. It is automatically loaded at boot if referenced in `rabbitmq.conf`. It ensures all required roles (admin, editor, subscriber) are created ahead of the demo. You can use it to avoid running manual setup steps through the UI.

## 📚 Documentation Files

### `README.md`
*No detailed description available yet.*

### `rabbitmq_ha_demo_guide.md`
*No detailed description available yet.*

### `rabbitmq_system_documentation.md`
*No detailed description available yet.*

## 📁 Miscellaneous

### `.gitignore`
*No detailed description available yet.*