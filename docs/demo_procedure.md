# Procedure for the demonstration

This file contains the procedure that is used in the demonstration.

1. 🧹 Clean and start the brokers:
   ```sh
   ./stop_ha.sh
   ./start_ha.sh
   ```
2. 🔒 Showing the certificate:
   ```sh
   openssl s_client -connect localhost:5671 -cert certs/client_certificate.pem -key certs/client_key.pem -CAfile certs/ca_certificate.pem
   ```
3. 🔐❌ Failed connection attempts of a subscriber:
   ```sh
   python3 src/subscriber_main.py
   Enter your name: Camille
   Enter your RabbitMQ username: subscriber1
   Enter your RabbitMQ password: f
   ```
   => repeat until failure
4. 🔐✅ Connect connection attempt of a subscriber:
   ```sh
   python3 src/subscriber_main.py
   Enter your name: Camille
   Enter your RabbitMQ username: subscriber1
   Enter your RabbitMQ password: subpass
   ```
5. 🔐❌ Failed connection attempts of an editor:
   ```sh
   python3 src/publisher_main.py
   Enter your name: 20Minutes
   Enter your RabbitMQ username: wrongUsername
   Enter your RabbitMQ password: f
   ```
   => repeat until failure
6. 🔐✅ Connect connection attempt of a editor:
   ```sh
   python3 src/publisher_main.py
   Enter your name: 20Minutes
   Enter your RabbitMQ username: editor1
   Enter your RabbitMQ password: editorpass
   ```
7. Subscribe to sports
   ```sh
   subscribe sports
   ```
8. Add a news:
   ```sh
   sports.cycling
   Bientôt le tour de France !
   ```
9.  Show that the news is displayed in the console
10. Change priority of news:
   ```sh
   subscribe science low
   ```
11. Add a news:
   ```sh
   science
   La chasse au moustique-tigre est lancée en Auvergne-Rhône-Alpes
   ```
12. Show that it is not displayed until:
   ```sh
   showPriority low
   ```
14. Unsubscribe:
   ```sh
   unsubscribe sports
   subscribe sports.baseball
   ```
15. Add a news:
   ```sh
   sports.hockey
   La Suisse pleure après une nouvelle défaite.
   ```
16. Show that it is NOT displayed
17. Kill rabbit1
    ```sh
    docker stop rabbit1
    ```
18. Show on subscriber and editor that it is up again.
   