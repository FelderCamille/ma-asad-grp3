
# MA_ASAD - Grp3

> This repository contains the code of an event-based news subscription system.

This project implements a **publish/subscribe** (event-based) architecture using **RabbitMQ**.  
Publishers can send news on specific categories (sports, politics, etc.) and also to their own dedicated exchange.  
Subscribers can subscribe or unsubscribe both by **news categories** or **publisher names**.

---

## 🏗️ Architecture Overview

- **RabbitMQ (Docker)**
  - Acts as the message broker.
  - Exposed on port `5672` (AMQP protocol).
  - Management console on port `15672`.

- **Publisher (Editor)**
  - Code in `publisher_main.py` and `publisher.py`.
  - Publishes to:
    - Category-specific exchanges (e.g., `sports`, `politics`).
    - A dedicated exchange named `editor_<publisherName>` (e.g., `editor_Alice`).

- **Subscriber**
  - Code in `subscriber_main.py` and `subscriber.py`.
  - Allows:
    - Subscribing/unsubscribing to news categories (`sports`, `weather`, etc.).
    - Subscribing/unsubscribing directly to publishers (`subscribeeditor Alice`).
    - Maintaining a list of publishers that are online/offline.

---

## ✅ Prerequisites

- **Docker** and **Docker Compose** installed.
- **Python 3** installed locally.

---

## 🐳 Start the System

Open a terminal in the **root directory** (where `docker-compose.yml` resides) and run:

```bash
sudo ./certs/generate-certs.sh
docker compose up -d
```

Visit [http://localhost:15672](http://localhost:15672) for the RabbitMQ Management UI.  
- Default credentials: `admin` / `supersecureadmin`.

---

## 🚀 Test Scenario and Full Terminal Commands

Below is a detailed step-by-step sequence of commands to fully test the system.

### 🟢 Terminal 1: Publisher Setup

Open a terminal and execute:

```bash
cd src
pip install -r requirements.txt
python3 publisher_main.py
```

When prompted, enter the publisher name:

```yaml
Enter your publisher name: Alice
```

The publisher announces `"Editor "Alice" is online."`.

You can publish news periodically by following prompts:

- Enter news type(s), e.g., `sports politics`.
- Enter news content, e.g., `Breaking news update!`.

To exit the publisher:

- Press `Ctrl + C`.

### 🔵 Terminal 2: Subscriber Setup

Open another terminal and execute:

```bash
cd src
pip install -r requirements.txt
python3 subscriber_main.py
```

When prompted, enter subscriber name:

```yaml
Enter your name: Bob
```

You will now see an interactive prompt (`>>`).

Then enter `subscribe` followed by the news type to subscribe to:

```bash
subscribe sports
```

Bob subscribes immediately to these news type.


### ⚡ Interactive Subscriber Commands

From the subscriber prompt (`>>`), use:

- `subscribe <news_type>` (e.g., `unsubscribe sports`)
- `unsubscribe <news_type>` (e.g., `unsubscribe sports`)
- `subscribeeditor <publisher_name>` (e.g., `subscribeeditor Alice`)
- `unsubscribeeditor <publisher_name>` (e.g., `unsubscribeeditor Alice`)
- `exit` (to stop subscriber)

### 🚩 Example Command Workflow

Subscriber sees `"Editor "Alice" is online."` upon publisher start.

Subscriber subscribes directly to Alice:

```bash
>> subscribeeditor Alice
```

Bob now receives **all** news from Alice.

Alice publishes news (e.g., `weather`), and Bob still receives due to direct subscription.

Bob unsubscribes from Alice:

```bash
>> unsubscribeeditor Alice
```

Bob stops receiving Alice’s direct news.

Bob unsubscribes from a news category:

```bash
>> unsubscribe sports
```

When Alice stops (`Ctrl + C`), Bob sees `"Editor "Alice" is offline."`

Bob exits:

```bash
>> exit
```

---

## 🛑 Stopping the System

To stop the system, run:

```bash
docker compose down -v
```

This stops RabbitMQ and removes all containers, networks, and volumes.

---

Enjoy! For questions or issues, contact the **MA_ASAD - Grp3** team.
