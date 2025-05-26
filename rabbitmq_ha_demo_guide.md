# 🧪 RabbitMQ News System – Demo Guide (Labo 2)

> ✅ Covers all **mandatory requirements** (M1, M2, S1, S2)  
> ✅ Demonstrates the **bonus**: availability through clustering (manual join + quorum queue)

---

## ✅ What to prepare before starting the demo

- Your project folder contains:
  - ✅ `start_ha.sh` (latest version)
  - ✅ `docker-compose-ha.yml`
  - ✅ `certs/generate-certs.sh`
  - ✅ Working Python files in `src/`
    - `publisher_main.py`
    - `subscriber_main.py`
- RabbitMQ users created via `rabbitmq_setup.json`
- Three terminal windows open:
  - **Terminal 1** → start/stop the cluster and simulate node failure
  - **Terminal 2** → subscriber
  - **Terminal 3** → publisher

---

## 🟢 STEP 1 — Start the cluster

In **Terminal 1**:

```bash
./start_ha.sh
```

Wait for:

```
✅ Cluster ready!
• Node-1 UI → http://localhost:15672
• Node-2 UI → http://localhost:15673
```

---

## 🌐 STEP 2 — Open the management UIs

Visit in your browser:

- http://localhost:15672  → node 1
- http://localhost:15673  → node 2

Login:

- Username: `admin`
- Password: `supersecureadmin`

Verify:

- ✅ *Cluster* tab shows both nodes
- ✅ *Queues* tab shows `news` with type = **quorum**

---

## 📨 STEP 3 — Run a subscriber (Terminal 2)

```bash
python src/subscriber_main.py
```

Then type:

```
Friendly name: Bob
Username: subscriber1
Password: subpass
```

At prompt:

```
subscribe sports
```

---

## ✍️ STEP 4 — Run a publisher (Terminal 3)

```bash
python src/publisher_main.py
```

Then type:

```
Friendly name: Alice
Username: editor1
Password: editorpass
```

When prompted:

```
Enter the news type(s): sports
Enter the news content: Hello world!
```

Subscriber sees the message!

---

## 🗂 STEP 5 — Test subscriber priority (**M2**)

Subscriber (Terminal 2):

```text
showPriority high
subscribe sports.hockey low
```

Publisher (Terminal 3):

```text
Enter the news type(s): sports.hockey
Enter the news content: Low priority message
```

No message received.

Now switch:

```text
showPriority low
```

Message appears!

---

## 💣 STEP 6 — Kill a node & test HA (**bonus**)

In **Terminal 1**:

```bash
docker stop rabbit1
```

Send a new message in **Terminal 3**:

```
Enter the news type(s): sports
Enter the news content: Still running!
```

✅ Subscriber (T2) still receives it!

Restart the node:

```bash
docker start rabbit1
```

Node rejoins automatically — no restarts needed on client side.

---

## 🔁 STEP 7 — Optional: Kill node 2

```bash
docker stop rabbit2
```

Test again — still works ✅

Then:

```bash
docker start rabbit2
```

---

## 🔐 STEP 8 — Confirm TLS is active between pods

> The inter-node connection uses TLS (port 25672) and mutual authentication with client certificates.

To prove this:

### ✅ Option A – terminal proof:

```bash
docker exec -it rabbit1 openssl s_client   -connect rabbit2:25672 -servername rabbit2 -brief   -CAfile /etc/rabbitmq/certs/ca_certificate.pem   -cert /etc/rabbitmq/certs/node_cert.pem   -key /etc/rabbitmq/certs/node_key.pem | head -8
```

You should see:

```
Protocol  : TLSv1.2
Ciphersuite: ECDHE-RSA-AES256-GCM-SHA384
Peer certificate: CN = rabbit2
Verification: OK
```

### ✅ Option B – Management API:

```bash
curl -s -u admin:supersecureadmin   http://localhost:15672/api/nodes/rabbit%40rabbit1 | jq '.listeners[] | select(.protocol=="clustering") | {port,ssl}'
```

Should return:

```json
{
  "port": 25672,
  "ssl": true
}
```

Take a screenshot of either result.

---

## 🧼 STEP 9 — Clean up

```bash
docker compose -f docker-compose-ha.yml down -v
```

---

## 💬 Summary to say during your demo

> “We implemented a topic-based, TLS-secured news system with:
> - user authentication (S1)
> - encrypted data (S2)
> - topic & sub-topic support (M1)
> - preference filtering (M2)
> - and HA with a quorum queue (bonus)”

This setup:
- Uses real TLS on port 5671 (AMQPS)
- Keeps working during node failures
- Shows both editors and subscriber filtering
- Confirms message delivery with UI and terminal outputs
- Secures node-to-node communication with TLS

---

## 🔄 Terminal Role Reminder

| Terminal | Role         | Example command                        |
|----------|--------------|----------------------------------------|
| **T1**   | Cluster admin| `./start_ha.sh`, `docker stop rabbit1` |
| **T2**   | Subscriber   | `python src/subscriber_main.py`        |
| **T3**   | Publisher    | `python src/publisher_main.py`         |

You can open a **T4** if you want to show multiple subscribers.
