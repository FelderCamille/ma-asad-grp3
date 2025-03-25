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
python3 subscriber.py
```

Run the publisher:
```bash
cd src
python3 publisher.py
```

## 🛑 Stop the SI

```sh
docker compose down -v
```