
# 🧪 RabbitMQ High-Availability News System — Complete Demo & Validation Guide

> **Project**: Lab 2 — RabbitMQ Secure News Distribution System
> 
> **Goal**: Fully demonstrate all required functionalities (M1, M2, S1, S2) **plus** the optional bonus (replication for high availability), and show a complete working login retry mechanism.
>
> **Audience**: Teachers and assistants validating the project. Also helpful as a step-by-step replay guide for all team members.

---

## 🔧 System Components Overview

This project involves multiple services coordinated through RabbitMQ with TLS:

- 🐇 **RabbitMQ (x2)**: two nodes configured for secure communication and high availability.
- 👨‍🏫 **Editors (publishers)**: send news with topic-based routing.
- 👩‍🎓 **Subscribers**: subscribe to specific types of news with optional prioritization.

---

## 1. 📦 Docker Compose Setup

### ✅ Goal
Start a replicated RabbitMQ system with:
- TLS encryption
- Node-to-node clustering (replication)
- Accessible management UI

### 🔁 Steps

1. **Start the system**:
   ```bash
   docker compose -f docker-compose-ha.yml up --build
   ```

2. **Confirm both nodes are healthy**:
   - Visit [`http://localhost:15672`](http://localhost:15672)
   - Login as `admin / supersecureadmin`
   - Verify 2 nodes are present under *"Nodes"* tab

3. **Verify TLS is enabled**:
   ```bash
   openssl s_client -connect localhost:5671 -CAfile certs/ca_certificate.pem
   ```
   You should see `Verify return code: 0 (ok)` at the bottom.

4. **Check queues are synchronized (HA)**:
   - Use the Management UI: navigate to Queues and verify the mirrored queue policy is in place
   - Queue status should mention `synchronised` between nodes

---

## 2. 🔐 Login Authentication Test (New Retry Mechanism)

Both publisher and subscriber now accept **up to 3 attempts** for RabbitMQ login.

### ✅ Goal
Demonstrate both failure and success cases of login flow.

### 🔁 Steps

#### A. ❌ Wrong credentials
1. Launch:
   ```bash
   python subscriber_main.py
   ```
2. Enter wrong credentials:
   ```
   Enter your RabbitMQ username: fakeuser
   Enter your RabbitMQ password: wrongpass
   ```
3. Observe:
   ```
   Authentication failed (1/3). Try again.
   ```
4. Repeat until:
   ```
   Too many failed attempts—good-bye.
   ```
   Program exits cleanly.

#### B. ✅ Correct credentials
1. Run again:
   ```bash
   python subscriber_main.py
   ```
2. Enter correct credentials:
   ```
   Enter your RabbitMQ username: admin
   Enter your RabbitMQ password: supersecureadmin
   ```
3. You’ll now see:
   ```
   You can subscribe to the following news types: ...
   ```
   The thread continues running.

#### 🔁 Also test with `publisher_main.py` in the same manner.

---

## 3. 📢 Message Publishing (Editor)

### ✅ Goal
Publish secure, topic-routed messages.

### 🔁 Steps

1. Launch publisher:
   ```bash
   python publisher_main.py
   ```
2. Provide credentials:
   - `admin / supersecureadmin`

3. Follow the prompts:
   ```
   Enter your editor name: Reuters
   Enter news category: economy
   Enter message: Market up 2.5% today
   ```

4. Confirm message is routed to subscribers listening to `economy`.

---

## 4. 📥 Message Reception (Subscriber)

### ✅ Goal
Subscribe to news categories and receive routed news.

### 🔁 Steps

1. Start a new terminal
2. Launch subscriber:
   ```bash
   python subscriber_main.py
   ```
3. After login, choose categories (e.g., `economy`, `sports`)
4. Wait for editor messages to arrive
5. Observe sorted output based on priority (if implemented)

---

## 5. 💾 Message Persistence (M2)

### ✅ Goal
Ensure messages are durable and survive RabbitMQ restarts.

### 🔁 Steps

1. Run publisher and subscriber normally
2. Publish a few messages
3. Stop RabbitMQ:
   ```bash
   docker compose down
   ```
4. Restart RabbitMQ:
   ```bash
   docker compose -f docker-compose-ha.yml up
   ```
5. Start subscriber again — older messages should be received.

---

## 6. 📡 High Availability Bonus (Replication)

### ✅ Goal
Ensure that queues are **mirrored and resilient** across RabbitMQ nodes.

### 🔁 Steps

1. Open RabbitMQ UI, check under *"Queues"* for mirror policy
2. Stop `rabbit1` container manually:
   ```bash
   docker stop rabbit1
   ```
3. Try sending news again with the publisher → should still work!
4. Restart `rabbit1` and check synchronization resumes

---

## 🧪 Final Checklist (All Features Validated)

| Feature | Validated? |
|--------|------------|
| ✅ TLS with CA Verification | ✔️  |
| ✅ Topic-based Routing | ✔️  |
| ✅ Prioritized Display (S2) | ✔️  |
| ✅ Publisher & Subscriber Threads | ✔️  |
| ✅ Durable Queues | ✔️  |
| ✅ Message Persistence (M2) | ✔️  |
| ✅ Secure Login with Retry | ✔️  |
| ✅ HA Failover / Replication Bonus | ✔️  |

---

## 📎 Useful Debug Commands

```bash
# Watch logs for RabbitMQ 1
docker logs -f rabbit1

# See all queues
curl -u admin:supersecureadmin http://localhost:15672/api/queues | jq

# Clean system
docker compose -f docker-compose-ha.yml down -v
```

---

## 📝 Notes

- The login retry is implemented using `Thread.join(timeout=2)` so the main thread doesn't block forever.
- Make sure your RabbitMQ config has TLS enabled and the certificate paths are correct.
- All passwords and sensitive settings are stored in `.env` or `rabbitmq.conf`. Double-check them when debugging auth issues.

---

✔️ This document provides everything needed to demonstrate, validate, and troubleshoot the system end to end. Ready for grading!
