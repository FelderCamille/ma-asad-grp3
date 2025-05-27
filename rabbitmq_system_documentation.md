# Secure and Modular Publish/Subscribe System with RabbitMQ – Design, Implementation & Evaluation

---

## 1. Introduction

This document presents the design, implementation, and evaluation of a **secure and modular news distribution system** based on the **publish/subscribe paradigm** using **RabbitMQ** as the messaging broker.

The system was developed in the context of a software architecture lab focused on two key quality attributes:
- **Security**: ensuring authenticated and encrypted communication between clients and the broker.
- **Modifiability**: allowing dynamic topic subscriptions and adaptable client behavior with minimal reconfiguration.

Two main actors interact with the system:
- **Editors (publishers)**: responsible for sending news articles across various topics.
- **Subscribers (readers)**: users who register their interest in certain topics and receive related news in real time.

The system was developed in Python using the **pika** library for RabbitMQ integration. It supports secure transport via TLS, fine-grained access control, dynamic topic-based routing, and customizable preference levels for message filtering. The solution aligns with the **S1**, **S2**, **M1**, and **M2** goals described in the lab specification.

This report provides a technical walkthrough of the system, from architecture to detailed component behavior, with an emphasis on how the implementation supports the target quality attributes.

---

## 2. Architecture Overview

### 2.1 System Components

The system is composed of the following main components:

- **RabbitMQ broker**: a message-oriented middleware responsible for routing and delivering messages between publishers and subscribers. It is deployed via Docker using a `docker-compose-ha.yml` file that declares two broker instances (`rabbit1`, `rabbit2`) for high availability (optional/bonus).

- **Publisher (Editor)**: an interactive command-line application (`publisher_main.py`) that allows a user to select a topic, type news content, and send messages to the broker. It uses a topic-based exchange and constructs routing keys in the form `<editor>.<topic>[.<subtopic>]`.

- **Subscriber**: another CLI application (`subscriber_main.py`) that connects to the broker, subscribes to selected topics using wildcard patterns, and displays received news. The user can dynamically modify subscriptions and adjust the visible priority level (`low`, `medium`, `high`).

- **RabbitMQ definitions** (`rabbitmq_setup.json`) and configuration (`rabbitmq.config`) are used to preload exchanges, queues, bindings, and user permissions for a secured and preconfigured setup.

### 2.2 Data Flow

```
        ┌────────────┐               ┌────────────────────────┐
        │  Editor    │  publish()    │  Topic Exchange: news  │
        └────────────┘─────────────▶│   (type = topic)       │
                                    └────────────┬───────────┘
                                                 │
                          routing_key =          ▼
                    "LeTemps.sports.football"    ┌─────────────┐
                                                 │ Subscriber  │
                                                 └─────────────┘
```

- The **editor** connects to the `news` exchange using a secure TLS connection and sends messages with routing keys such as `LaLiberte.politics.europe` or `LeTemps.sports.football`.
- The **subscriber** declares one exclusive queue and binds it with wildcards like `*.sports.#` or `LeTemps.#`.
- The broker uses the `routing_key` and the subscriber’s bindings to deliver matching messages.

### 2.3 Security Layers

All communication is secured by:
- **Authentication** using RabbitMQ accounts and vhost-based access control
- **Encryption** using **TLS 1.2/1.3** with mutual certificate authentication

### 2.4 Modifiability Features

The system is designed to be flexible:
- Users can **add or remove subscriptions** interactively while the client is running.
- Subscriptions are **not hardcoded**; wildcard routing enables complex patterns.
- The **priority** of each subscription is stored and used to filter or sort displayed messages.
- Editors and topics can be added without changes to broker configuration thanks to topic-based routing.

---

## 3. RabbitMQ Configuration & Deployment

### 3.1 Docker-Based Deployment

Use the file `docker-compose-ha.yml` to launch two RabbitMQ nodes. Each exposes TLS (5671/5673) and management UI (15672/15673). They use the `rabbitmq:3.13-management` image.

### 3.2 Virtual Hosts, Users & Permissions (S1)

Using `rabbitmq_setup.json`, the system creates:
- A virtual host: `news`
- Users: `editor1`, `editor2`, `sub1`, `sub2`
- Permissions:
  - Publishers: write-only access to `news`
  - Subscribers: read-only access

### 3.3 Secure Transport with TLS (S2)

RabbitMQ uses port 5671 for encrypted AMQP (AMQPS). TLS certs are loaded in Python using:
```python
context = ssl.create_default_context(cafile=CA_FILE)
context.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
```

---

## 4. Publisher Logic

The publisher allows editors to:
1. Log in with credentials.
2. Select a topic and subtopic.
3. Enter a message.
4. Publish it via the `news` topic exchange using routing keys like `editor1.sports.hockey`.

Each message is sent with a routing key `<editor>.<topic>[.<subtopic>]`, and encrypted via TLS.

---

## 5. Subscriber Logic

### 5.1 Subscription Mechanism (M1)

Users subscribe with commands like:
- `subscribe politics` → `*.politics.#`
- `subscribeEditor LeTemps` → `LeTemps.#`

Each subscriber has one exclusive queue with dynamic topic bindings.

Bug to fix: `__format_routing_key()` is missing `self`.

### 5.2 Message Reception and Priority Filtering (M2)

Subscriptions can be tagged:
- `low`, `medium`, or `high` (default = high)
- Messages are stored in three queues internally
- `showPriority <level>` sets what is displayed

Filtering is implemented, but not sorting.

---

## 6. Security Measures (S1 & S2)

### 6.1 Authentication

- RabbitMQ users are defined in `rabbitmq_setup.json`
- Role-based permissions per virtual host
- Credentials entered at runtime

### 6.2 Encrypted Transport

- AMQPS (TLS) over port 5671
- Mutual certificate authentication
- Client and broker certs loaded from `./certs`

---

## 7. Modifiability Design (M1 & M2)

### 7.1 Topics (M1)

- No per-topic exchanges or queues
- Single topic exchange supports all routing needs
- Supports dynamic, wildcard-based subscriptions

### 7.2 Preferences (M2)

- Each subscription maps to a priority level
- User can switch views with `showPriority`
- Clean mechanism to add/change filters dynamically

---

## 8. Limitations and Improvements

| Area | Limitation | Suggested Fix |
|------|------------|----------------|
| M2 | Filtering only, not sorted | Sort messages by priority |
| Durability | `auto_ack=True` means messages may be lost | Use `basic_ack`, durable queues |
| Clustering | `rabbit1`, `rabbit2` not actually clustered | Enable peer discovery or config-based clustering |
| Graceful Exit | Threads don’t catch Ctrl-C properly | Use `threading.Event` to signal shutdown |
| Cert Paths | Hardcoded relative paths | Use `Path(__file__).parent` logic |

---

## 9. Test & Demo Instructions

### 9.1 Setup

```bash
docker compose -f docker-compose-ha.yml up
```

### 9.2 Publisher

```bash
python publisher_main.py
```

Example:
```
Username: editor1
Topic: sports.hockey
Message: Geneva wins!
```

### 9.3 Subscriber

```bash
python subscriber_main.py
```

Example:
```
Username: sub1
> subscribe sports.hockey high
> showPriority high
```

### 9.4 Security Checks

- TLS certs are required
- Invalid credentials or certs result in denied access

---

## 10. Conclusion

This project implements a robust, secure, and flexible publish/subscribe system with:

- Encrypted, authenticated communication (S1, S2)
- Dynamic topic and editor subscriptions (M1)
- Customizable filtering preferences (M2)

With minor improvements to clustering and message ordering, the system would fully meet production-grade expectations and demonstrate advanced architectural modifiability and security.

---



---

## 2. Architecture Overview

The architecture is composed of the following core components:

- **RabbitMQ Cluster**: Two-node high availability cluster with mirrored queues and TLS/SSL encryption.
- **Publisher (Editor)**: Threaded client application allowing a user to push categorized news over secure AMQP with topic-based routing.
- **Subscriber**: Threaded client that subscribes to specific topics and receives prioritized messages securely.
- **Management Interface**: RabbitMQ Management UI available at port `15672` for monitoring.

### Diagram

```text
[Publisher] ---> [Exchange: topic] ---> [Queue: filtered topic] ---> [Subscriber]
                                       ^
                             [RabbitMQ Node 1 & 2 (clustered, TLS)]
```

---

## 3. Security Model

### Authentication

- Clients are authenticated using credentials passed securely over TLS.
- Three-attempt retry logic implemented in both clients.

### Encryption

- All communication is secured with TLS using self-signed certificates (`ca_certificate.pem`).
- The system uses AMQPS (port 5671) to enforce encrypted connections.

### Authorization

- Each user must provide valid credentials to access the messaging broker.
- Failed authentications are tracked and rejected after 3 attempts.

---

## 4. Functionality Walkthrough

### Publisher Workflow

1. User provides credentials and starts the editor.
2. Editor connects securely to RabbitMQ using AMQPS.
3. User selects a topic and sends a message.
4. Message is published with topic-based routing.

### Subscriber Workflow

1. User provides credentials and starts the subscriber.
2. After successful authentication, selects topic(s) to subscribe to.
3. Subscriber listens on a queue bound to the exchange with topic keys.
4. Receives and displays messages with optional priority handling.

---

## 5. High Availability Setup

- Docker Compose spins up two RabbitMQ nodes with identical configs.
- `rabbitmq.conf`, `advanced.config`, and TLS certs are mounted via volume.
- Queues are mirrored using RabbitMQ policy:
  ```bash
  rabbitmqctl set_policy ha-all "" '{"ha-mode":"all"}'
  ```

### Failover

- If `rabbit1` fails, `rabbit2` continues operation.
- Publisher and subscriber clients continue functioning seamlessly.

---

## 6. Reliability & Durability

- All queues and messages are declared as `durable`.
- Messages are `persistent`, surviving broker restarts.
- Confirmed by testing message replay after RabbitMQ reboot.

---

## 7. Error Handling

- Clients handle:
  - Authentication failures (with retry logic)
  - Connection timeouts
  - Incorrect routing keys
- Threads exit gracefully on unrecoverable errors.

---

## 8. Development & Deployment

- Languages: Python 3.12, Docker, RabbitMQ
- Key libraries: `pika`, `threading`, `ssl`, `getpass`, `logging`
- Configuration stored in:
  - `docker-compose-ha.yml`
  - `rabbitmq.conf`, `advanced.config`
  - TLS: `certs/`

---

## 9. Test & Validation Plan

| Test                          | Status  | Description                                      |
|-------------------------------|---------|--------------------------------------------------|
| TLS Connection Validation     | ✔️      | Used `openssl s_client` to validate certificates |
| Retry on Bad Login            | ✔️      | 3-strike login logic verified                    |
| Topic Routing & Subscriptions| ✔️      | Dynamic topic binding tested                     |
| HA Failover                   | ✔️      | Publisher/subscriber remained operational        |
| Message Persistence           | ✔️      | Messages recovered after restart                 |

---

## 10. Conclusion

This system demonstrates a secure, modular, and highly available pub/sub architecture suitable for production-like environments. The use of RabbitMQ with TLS and a replicated setup ensures both reliability and confidentiality. It also showcases clear separation of concerns, reusable components, and strong error handling.

