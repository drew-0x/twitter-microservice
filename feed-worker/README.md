# Tweet Worker Service

This service acts as a background worker responsible for processing newly created tweet events from a message queue. Its primary function is to facilitate feed distribution by fanning out tweet notifications to the individual feed queues of users who follow the tweet's author.

## ✨ Core Logic / Workflow

1.  **Consume Tweet Events:** The worker continuously listens to the `general_tweets` RabbitMQ queue for incoming messages.
2.  **Parse Message:** Each message is expected to be a JSON payload containing at least the `user_id` of the tweet's author.
    ```json
    {
      "user_id": "string (author_uuid)",
      "tweet_id": "string (tweet_uuid)" // Present in message but not used by this worker's logic
    }
    ```
3.  **Fetch Followers:** For the `user_id` obtained from the message, the worker makes a gRPC call to the **User Service** (`GetFollowers` method) to retrieve the list of users following the author.
4.  **Fan-out to Follower Feeds:** For each follower identified:
    * A dedicated RabbitMQ queue named `user_feed_<follower_id>` is declared (or ensured to exist).
    * The *original* tweet message received in step 1 is republished to this follower-specific queue.
5.  **Concurrency:** Each incoming message from `general_tweets` is processed in its own Go routine (`go handle_message(...)`) allowing for parallel handling of tweet events.

This implements a **"fan-out on write"** pattern for feed distribution. Instead of the Feed Service calculating feeds on read, this worker pre-distributes the relevant tweet information to queues that the Feed Service can later consume.

## 🛠️ Technologies Used

### 🐹 Go
* The primary programming language used for this service.

### 🐇 RabbitMQ Client (`github.com/rabbitmq/amqp091-go`)
* Used to connect to RabbitMQ, consume messages from the `general_tweets` queue, and publish messages to individual `user_feed_<follower_id>` queues.

### 💬 gRPC Client (`google.golang.org/grpc`)
* Used to make RPC calls to the User microservice to retrieve follower lists.

### 📜 Protocol Buffers (`pb "tweet-worker/user"`)
* Utilizes Go code generated from the User service's `.proto` file (`user.proto`) to interact with its gRPC interface.

### 📄 JSON (`encoding/json`)
* Used for unmarshalling incoming message payloads from RabbitMQ.

## 🗣️ gRPC Interface (Client Usage)

### Purpose
This service acts as a gRPC client solely to interact with the User service.

### Consumed Services

1.  **User Service (`user.proto`)**
    * **Target:** `localhost:50051` (currently hardcoded).
    * **Method:** `GetFollowers`
        * **Purpose:** To retrieve the list of `FollowerId`s for a given `UserId` (the author of the tweet).
        * **Called From:** `get_user_followers` function within `handle_message`.
        * **Request:** `pb.GetFollowersReq{UserId: <author_user_id>}`
        * **Response:** `pb.GetFollowersRes` containing `repeated pb.FollowStruct followers`. The worker extracts the `FollowerId` from each struct.

## 📨 Message Queue Interface

### Consumed Queue
* **Name:** `general_tweets`
* **Producer:** Tweet Service (Python/Flask)
* **Expected Message Format:** JSON string, e.g., `{"user_id": "uuid", "tweet_id": "uuid"}`.
* **Consumer Logic:** Reads messages, parses `user_id`, triggers follower fetch and fan-out. Uses `autoAck=true`.

### Produced Queues
* **Name Pattern:** `user_feed_<follower_id>` (dynamically declared per follower).
* **Consumer:** (Implicitly) Feed Service or a component responsible for assembling user feeds.
* **Message Format:** Forwards the *original* JSON message received from `general_tweets`.
* **Purpose:** To deliver tweet notifications directly to queues designated for specific users' feeds.

## ⚠️ Error Handling
* **Critical Errors:** Uses `log.Panicf` for errors during initial setup (RabbitMQ connection/channel creation, queue declaration, consuming setup). This will cause the worker to crash and likely require restarting.
* **gRPC Errors:** Uses `log.Fatalf` (via `get_user_followers` -> `handle_message` -> `log.Fatalf` on error) when the `User.GetFollowers` call fails for a specific message. This **crashes the entire worker process**, not just the handling of that single message. This strategy might lead to lost messages if not handled carefully (e.g., using `autoAck=false` and manual acknowledgments).
* **Publishing Errors:** Uses `log.Printf` for errors encountered when publishing to individual `user_feed_` queues. This logs the error but allows the worker to continue processing other followers/messages.
* **JSON Unmarshal Errors:** Uses `log.Panicf` if the incoming message cannot be unmarshalled. This also crashes the worker.
* **Logging:** Uses the standard Go `log` package for informational messages (`Received message`, `Tweet sent to user queue`).

## ⚙️ Configuration
* Configuration is currently **hardcoded** within the application:
    * **RabbitMQ Connection URL:** `amqp://server:pass@localhost:5672`
    * **User Service gRPC Target:** `localhost:50051`
* **Recommendations:** These values should be externalized using environment variables, configuration files (e.g., YAML, TOML), or a configuration management system.

## 📊 Database Schema
* This service is **stateless** and does not directly interact with or require its own database. It relies on data fetched from the User service via gRPC.

## 📈 Monitoring
* **Logging:** Current logging provides basic operational insights.
* **Metrics (Recommendations):**
    * Number of messages consumed from `general_tweets`.
    * Message processing latency (time from consumption to completion of fan-out).
    * Rate of gRPC calls to `User.GetFollowers`.
    * Latency of `User.GetFollowers` gRPC calls.
    * Number of messages published to `user_feed_` queues (fan-out factor).
    * Error rates (RabbitMQ connection/publish, gRPC calls, JSON parsing).
    * Queue depth monitoring for `general_tweets` and potentially patterns in `user_feed_` queues.

## 📝 Logging
* Uses the standard Go `log` package.
* Logs message reception, fan-out actions per follower, and errors (using `Printf`, `Fatalf`, `Panicf`).
* Log output includes timestamps and basic error messages. Consider structured logging (e.g., JSON format) for better parsing and analysis in production.

## 🧪 Testing
* **Unit Tests:**
    * Test `handle_message` logic by providing sample `amqp.Delivery` messages.
    * Mock the RabbitMQ channel (`conChan`) interface to verify queue declarations and publishes.
    * Mock the gRPC client (`pb.NewUserClient`) to simulate responses (success/error) from the User service without needing a live dependency.
* **Integration Tests:**
    * Test against a real (or containerized) RabbitMQ instance to verify queue interactions.
    * Test against a real (or mocked/containerized) User service gRPC endpoint.
    * Requires careful setup and teardown of test resources (queues, connections).

## 🚀 Build and Deployment
* **Build:** Compile the Go code into a static binary using `go build`.
    ```bash
    go build -o tweet-worker .
    ```
* **Dependencies:** Requires generated Protocol Buffer Go code for the User service (`user.pb.go`, `user_grpc.pb.go`) placed in the `user/` directory relative to the import path (`tweet-worker/user`).
* **Running:** Execute the compiled binary.
    ```bash
    ./tweet-worker
    ```
* **Deployment:** Typically deployed as a standalone process or within a container (e.g., Docker). Requires network access to RabbitMQ and the User service gRPC endpoint. Consider using a process manager (like `systemd` or `supervisor`) or container orchestrator (like Kubernetes) for lifecycle management (restarts on crash).

## 🤝 Dependencies
* **Internal Go Packages:**
    * `encoding/json`
    * `log`
    * `time`
    * `context`
    * `google.golang.org/grpc`
    * `google.golang.org/grpc/credentials/insecure`
    * `github.com/rabbitmq/amqp091-go`
    * `tweet-worker/user` (Generated gRPC/Proto code)
* **External Services:**
    * **RabbitMQ Server:** Must be running and accessible. Worker consumes from `general_tweets` and produces to `user_feed_*`.
    * **User Service:** Must be running, accessible via gRPC, and expose the `GetFollowers` method.
    * **Tweet Service (Producer):** Implicitly depends on the Tweet service publishing messages to `general_tweets`.
    * **Feed Service (Consumer):** Implicitly depends on this worker producing messages to the `user_feed_*` queues.
