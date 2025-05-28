
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
  - Management console on port `15672` and `15673`

- **Publisher (Editor)**
  - Code in `publisher_main.py` and `publisher.py`.
  - Publishes to `news` exchange with routing keys:
    - Category-specific routing key `*.<routingKey` (e.g., `*.sports.#`, `*.sports.hockey`, `*.politics.#`).
    - Editor routing key `<publisherName>.#` (e.g., `Alice.#`).

- **Subscriber**
  - Code in `subscriber_main.py` and `subscriber.py`.
  - Allows:
    - Subscribing/unsubscribing to news categories (e.g. `subscribe sports`, `subscribe sports.hockey`, `subscribe weather`, etc.).
    - Subscribing/unsubscribing directly to publishers (e.g. `subscribeeditor Alice`).
    - Maintaining a list of publishers that are online/offline.
    - Showing different news priorities (e.g. `showPriority low`)

---

## ✅ Prerequisites

- **Docker** and **Docker Compose** installed.
- **Python 3** installed locally.

---

## 🐳 Start the System

Open a terminal in the **root directory** (where `README.md` resides) and run:

```bash
./start_ha.sh
```

Note: at the first pull, you might need to run `chmod +x start_ha.sh` before the command above. 

Visit [http://localhost:15672](http://localhost:15672) for the RabbitMQ Management UI.
- Default credentials: `admin` / `supersecureadmin`.

You'll see two "Nodes" into the "Overview" tab.

---

## 🚀 Test Scenario and Full Terminal Commands

Below is a detailed step-by-step sequence of commands to fully test the system.

### 🟢 Terminal 1: Publisher Setup

Open a terminal and execute:

```bash
cd src
pip install -r requirements.txt
cd ..
python3 src/publisher_main.py
```

When prompted, enter the publisher name, username and password:

```yaml
Enter your publisher name: Alice
Enter your RabbitMQ username: editor1
Enter your RabbitMQ password: 
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
cd ..
python3 subscriber_main.py
```

When prompted, enter subscriber name, username and password:

```yaml
Enter your name: Bob
Enter your RabbitMQ username: subscriber1
Enter your RabbitMQ password: 
```

You will now see an interactive prompt (`>>`).

Then enter `subscribe` followed by the news type to subscribe to:

```bash
subscribe sports
```

Bob subscribes immediately to these news type.

### ⚡ Interactive Subscriber Commands

From the subscriber prompt (`>>`), use:

- `subscribe <topic> [<low/medium/high>]` (e.g., `subscribe sports medium`)
- `unsubscribe <topic>` (e.g., `unsubscribe sports`)
- `subscribeeditor <publisher_name> [<low/medium/high>]` (e.g., `subscribeeditor Alice`)
- `unsubscribeeditor <publisher_name>` (e.g., `unsubscribeeditor Alice`)
- `showPriority <low/medium/high>` (e.g. `showPriority low`)
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

Bob subscribe to a news category with a low priority:

```bash
>> subscribe sports.baseball low
```

When Alice publishes a news on `sports`, Bob do not receives it. When Alice publishes on `sports.baseball`, Bob do not see the news.

Bob displays the news with low priority:

```bash
>> showPriority low
```

Bob sees the news sent before.

Bob displays the news with high priority:

```bash
>> showPriority high
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
./stop_ha.sh
```

Note: at the first pull, you might need to run `chmod +x stop_ha.sh` before the command above. 

This stops RabbitMQ and removes all containers, networks, and volumes and certificates.

---

Enjoy! For questions or issues, contact the **MA_ASAD - Grp3** team.
