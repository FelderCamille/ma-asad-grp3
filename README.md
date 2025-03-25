# MA_ASAD - Grp3

> This repository contains the code of the system.

## 🐳 Start the SI

```sh
docker compose up -d
```

Once the broker is started, you can access the management panel through: [http://localhost:15672](http://localhost:15672). Credentials are the default ones.

Run the subscriber:
```bash
cd src
python3 subscriber_main.py
```

Run the publisher:
```bash
cd src
python3 publisher_main.py
```

## 🛑 Stop the SI

```sh
docker compose down -v
```

## Next

- The subscribers cannot subscribe/unsubscribe to a certain news type for now.
- Handle exceptions:
  - When the subscriber tries to subscribe to an non existant queue, the program crashes
- Add a queue (`fanout` exchange?) so that the editors indicate when are connected/disconnected
- In the subscription callback, indicate the queue name
