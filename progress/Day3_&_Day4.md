# Day 3 & Day 4 – Transactional Outbox, Kafka, Inbox Pattern, and Notifications

This document continues `Day1.md` and `Day2.md`. It records the work implemented and observed during Days 3 and 4. Implemented features are distinguished from features that were actually tested and from future production-hardening work.

## Project context

- Architecture: modular monolith, with a longer-term path toward distributed services.
- Backend: Python and FastAPI.
- Database: PostgreSQL.
- ORM and migrations: SQLAlchemy and Alembic.
- Message broker: Apache Kafka.
- Python Kafka client: `aiokafka`.
- Local infrastructure: Docker Desktop and Docker Compose.

Guiding principles: understand the failure mode before choosing a pattern; keep database changes transactional; assume messages can be delivered more than once; and do not claim exactly-once delivery without a real guarantee.

---

# Day 3 – Transactional Outbox and Kafka Integration

## 1. Why Kafka and the Outbox Pattern?

The Order Service already writes an `OutboxEvent` row in the same PostgreSQL transaction as order creation. A separate publisher is responsible for sending those durable events to Kafka.

This avoids a dual-write failure where an order commits to PostgreSQL but publishing directly to Kafka fails.

Conceptual flow:

```text
Order API
   |
PostgreSQL transaction
   |-- create order
   |-- create order items
   |-- update inventory
   |-- save idempotency response
   |-- insert outbox event
   |
 COMMIT
   |
Outbox Worker -> Outbox Publisher -> Kafka
```

The Outbox Pattern ensures that the event is durably stored with the business transaction. It does not make Kafka publishing exactly-once.

## 2. Local Kafka setup

Kafka runs locally in Docker using the Apache Kafka image in KRaft mode (without ZooKeeper).

Key configuration:

- Container: `ecommerce-kafka`
- Image: `apache/kafka:4.1.1`
- Bootstrap address: `localhost:9092`
- Topic: `order-events`
- Partitions: `1`
- Replication factor: `1`
- Persistent Docker volume: `kafka_data`

The Compose configuration used:

```yaml
services:
  kafka:
    image: apache/kafka:4.1.1
    container_name: ecommerce-kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      CLUSTER_ID: 4L6g3nShT-eMCtK--X86sw
    volumes:
      - kafka_data:/var/lib/kafka/data

volumes:
  kafka_data:
```

Start Kafka:

```bash
docker compose up -d
docker ps
```

Create the topic:

```bash
docker exec ecommerce-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic order-events --partitions 1 --replication-factor 1
```

List and describe topics:

```bash
docker exec ecommerce-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

docker exec ecommerce-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic order-events
```

The single broker, one partition, and replication factor of one are local development settings, not a production availability configuration.

## 3. Kafka concepts learned

| Concept | Meaning |
|---|---|
| Broker | A Kafka server that stores and serves messages. |
| Cluster | A group of Kafka brokers. |
| Topic | A named stream/category of messages. |
| Partition | An ordered log within a topic. |
| Offset | A message position within a partition. |
| Producer | An application that publishes messages. |
| Consumer | An application that reads messages. |
| Consumer group | Consumers sharing work and offsets for a topic. |
| Committed offset | The consumer group's recorded progress in a partition. |

Committing a consumer offset does not delete the Kafka message. Kafka retains messages according to topic retention settings.

## 4. Kafka producer

Installed the Python client:

```bash
pip install aiokafka
```

The project uses `aiokafka==0.15.0`.

File: `src/core/kafka.py`

```python
from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
ORDER_EVENTS_TOPIC = "order-events"


def create_kafka_producer():
    return AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )
```

The producer is created during FastAPI startup and shared with the Outbox worker.

## 5. Outbox repository and safe claiming

File: `src/repositories/outbox_repository.py`

The repository retrieves pending events and marks successfully published events. The query uses:

```python
.with_for_update(skip_locked=True)
```

`SELECT FOR UPDATE SKIP LOCKED` allows concurrent workers to claim different rows: one worker locks the rows it selects, while another skips rows already locked.

The current implementation retrieves a small batch (one event at a time). This limits the number of rows locked in the transaction.

`SKIP LOCKED` coordinates database workers while row locks are active. It does not guarantee exactly-once delivery to Kafka.

## 6. Outbox publisher

File: `src/services/outbox_service.py`

The class-based `OutboxPublisher`:

1. Retrieves pending outbox records.
2. Builds an event envelope containing event ID, event type, and payload.
3. Serializes the envelope to JSON bytes.
4. Publishes to `order-events`.
5. Marks the event as published after Kafka acknowledges it.
6. Commits the database update.

The publisher uses:

```python
await self.kafka_producer.send_and_wait(
    ORDER_EVENTS_TOPIC,
    value=json.dumps(message).encode("utf-8"),
)
```

The observed order event contained order ID, user ID, total amount, and item product IDs and quantities.

The consumer accepts both underscore and hyphen spellings for event ID and event type because both variants were encountered during development. The envelope should be standardized in a future cleanup.

## 7. Outbox background worker

File: `src/services/outbox_worker.py`

The worker repeatedly:

1. Opens a SQLAlchemy session.
2. Creates an `OutboxPublisher`.
3. Publishes pending events.
4. Logs the number published.
5. Closes the session.
6. Sleeps for five seconds before polling again.

The worker is an async background task, but it currently uses synchronous SQLAlchemy sessions. Synchronous database calls can block the event loop; thread offloading or an async database approach may be appropriate as the workload grows.

## 8. FastAPI lifespan

File: `src/main.py`

FastAPI lifespan manages the producer and Outbox worker:

- Startup: create and start the producer, store it in `app.state`, then start the worker task.
- Shutdown: cancel and await the worker task, then stop the producer.

The Kafka consumer was added to this lifecycle on Day 4.

## 9. At-least-once delivery and duplicate scenario

A possible failure sequence:

1. The Outbox worker sends an event to Kafka.
2. Kafka successfully stores the event.
3. PostgreSQL fails to commit `status = 'published'`.
4. The outbox row remains pending.
5. The worker retries and sends the event again.

This is at-least-once delivery. The consumer must be idempotent because the same event can arrive more than once.

## 10. Day 3 verification

The following flow was exercised successfully:

- Kafka broker and `order-events` topic were created and verified.
- FastAPI started the Kafka producer and Outbox worker.
- An order was created through `POST /api/v1/orders`.
- The Outbox worker published the event.
- The outbox row was marked `published`.
- A Kafka console consumer received the event.

Observed worker log:

```text
Published 1 outbox events
```

Database verification:

```sql
SELECT id, event_type, status, published_at
FROM outbox_events
ORDER BY created_at DESC
LIMIT 5;
```

The created order events were observed with `status = 'published'`.

Console consumer:

```bash
docker exec -it ecommerce-kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic order-events --from-beginning
```

---

# Day 4 – Kafka Consumer, Inbox Pattern, and Notification Processing

## 11. Why the Inbox Pattern?

Because the Outbox publisher provides at-least-once delivery, consumers can receive duplicate events. Without duplicate detection, a consumer might create duplicate notifications or repeat another business operation.

The Inbox Pattern records processed event IDs in PostgreSQL. Before performing business logic, the consumer tries to insert the event ID:

- Insert succeeds: this event is new for the consumer.
- Unique conflict: this event was already recorded, so skip the business operation.

## 12. ProcessedEvent model and migration

File: `src/models/processed_event_model.py`

The `processed_events` table contains:

| Field | Purpose |
|---|---|
| `id` | UUID primary key. |
| `event_id` | ID of the Kafka event. |
| `consumer_name` | Logical consumer name. |
| `processed_at` | Timestamp of record creation. |

The model was imported into `migrations/env.py`:

```python
from src.models.processed_event_model import ProcessedEvent
```

Migration revision: `d539782cb07d`.

The migration was applied and the table verified:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'processed_events'
ORDER BY ordinal_position;
```

Observed columns: `id`, `event_id`, `consumer_name`, `processed_at`; all were non-nullable.

### Important current limitation

The current unique constraint is on `event_id` alone. This is suitable only for the current single logical consumer group.

Before adding independent consumer groups (for example, inventory and analytics), change Inbox uniqueness to:

```text
(consumer_name, event_id)
```

Otherwise, one consumer group's record could prevent another group from independently recording the same event.

## 13. Processed event repository

File: `src/repositories/processed_event_repository.py`

`ProcessedEventRepository.claim_event()` uses PostgreSQL `INSERT ... ON CONFLICT DO NOTHING ... RETURNING`.

It returns:

- `True` if the Inbox record was inserted.
- `False` if the event ID already existed.

The repository does not commit. The consumer owns the transaction so the Inbox record and business operation can commit together.

## 14. Kafka consumer

File: `src/services/event_consumer_service.py`

The consumer is implemented as `OrderEventConsumer` using `AIOKafkaConsumer`.

Configuration:

| Setting | Value |
|---|---|
| Topic | `order-events` |
| Bootstrap servers | `localhost:9092` |
| Group ID | `order-event-consumer` |
| `auto_offset_reset` | `earliest` |
| `enable_auto_commit` | `False` |

Methods:

- `start()` – starts the Kafka consumer.
- `consume()` – continuously reads messages.
- `process_message()` – processes one message.
- `handle_event()` – routes by event type.
- `handle_order_created()` – handles `order.created`.
- `stop()` – stops the consumer.

The consumer is started as a background task from FastAPI lifespan.

### Why disable auto-commit?

The application must commit its Kafka offset only after the database transaction succeeds.

The key ordering is:

```python
db.commit()
await self.consumer.commit()
```

If the database transaction fails, the offset is not committed and Kafka can redeliver the event.

If the database commit succeeds but the offset commit fails, Kafka may redeliver the event. The Inbox record then detects the duplicate and skips the business operation.

An offset commit records consumer-group progress; it does not delete the Kafka message.

## 15. FastAPI lifecycle integration

FastAPI lifespan now manages:

1. Kafka producer.
2. Outbox worker.
3. Order event consumer.

At startup:

- Producer starts.
- Outbox worker starts.
- Consumer starts, subscribes to `order-events`, joins its consumer group, and receives partition assignment.
- The consumer loop runs as a background task.

At shutdown, the current implementation cancels the worker and consumer tasks, awaits their cancellation, then stops the Kafka consumer and producer.

This is basic task cancellation, not a complete graceful-draining implementation that guarantees all in-progress work has finished.

## 16. Duplicate delivery verification

The Inbox Pattern was manually tested with a duplicate Kafka message.

### First delivery

An order event was received and processed. The consumer inserted the event ID into `processed_events`.

Observed log:

```text
Processed event: 4604da27-79b6-4fc3-94d0-ca41584f3eec
```

Database check:

```sql
SELECT event_id, consumer_name, processed_at
FROM processed_events
ORDER BY processed_at DESC
LIMIT 5;
```

The event ID was present for consumer `order-event-consumer`.

### Second delivery

The exact same event ID was manually published to Kafka again. After restarting the application, the consumer read the duplicate and logged:

```text
Duplicate event skipped: 4604da27-79b6-4fc3-94d0-ca41584f3eec
```

This confirmed duplicate detection for the current consumer.

---

## 17. Notification model

File: `src/models/notification_model.py`

A notification table was added to demonstrate a real database business operation in the consumer.

Fields:

| Field | Purpose |
|---|---|
| `id` | UUID primary key. |
| `user_id` | Customer receiving the notification. |
| `order_id` | Related order. |
| `notification_type` | Type, such as `order_confirmation`. |
| `message` | Notification message. |
| `status` | Current notification lifecycle state. |
| `created_at` | Creation timestamp. |

The model was imported into `migrations/env.py`:

```python
from src.models.notification_model import Notification
```

Migration revision: `57e350d115cb`.

The migration was applied and all seven columns were verified in PostgreSQL.

## 18. Notification repository

File: `src/repositories/notification_repository.py`

`NotificationRepository.create_order_confirmation(user_id, order_id)` inserts a notification with:

```text
notification_type = order_confirmation
message = Your order has been received successfully!
status = pending
```

The repository adds the model to the supplied SQLAlchemy session but does not commit. The consumer controls the transaction.

## 19. Transactional consumer business logic

The consumer's `handle_order_created(event, db)` method:

1. Reads the event payload.
2. Extracts `user_id` and `order_id`.
3. Creates `NotificationRepository` using the same database session.
4. Inserts the order confirmation notification.

The Inbox insert and notification insert use the same SQLAlchemy session. The consumer commits once:

```python
db.commit()
```

On exception, it calls:

```python
db.rollback()
```

The intended guarantee is that the Inbox record and notification record commit or roll back together.

### Important test-status distinction

The same-session transaction structure is implemented and notification persistence was verified. However, a deliberate failure-injection test proving that both inserts roll back together was not run. Record this as **implemented, not failure-tested**.

## 20. Notification status

The current notification is created with:

```text
status = pending
```

This means the notification record is persisted but no email or SMS has been sent.

Possible future lifecycle states:

| Status | Meaning |
|---|---|
| `pending` | Waiting for delivery. |
| `processing` | A delivery worker is attempting delivery. |
| `sent` | The email/SMS provider accepted the request. |
| `failed` | The delivery attempt failed. |

Only `pending` creation is implemented in this milestone. No email/SMS provider is integrated.

## 21. Notification architecture discussion

Two possible future approaches were discussed.

### Database polling

```text
order-events
     |
Notification Consumer
     |
PostgreSQL notifications
     |
Delivery Worker polls pending rows
     |
Email/SMS provider
```

### Separate notification topic

```text
order-events
     |
Notification Consumer
     |
PostgreSQL notification + notification outbox
     |
Notification Outbox Publisher
     |
Kafka: notification-events
     |
Notification Service Consumer
     |
Email/SMS provider
```

The separate topic is a future architectural option, not part of the current implementation. If introduced, the notification record and its notification-outbox event should be stored in one database transaction to avoid creating another dual-write problem.

---

# 22. End-to-end verification summary

### Outbox to Kafka

- Kafka broker and topic verified.
- Producer and Outbox worker started through FastAPI lifespan.
- Order creation returned HTTP `201 Created`.
- Outbox worker published one event.
- Outbox event was marked `published`.
- Kafka console consumer received the event.

### Kafka consumer and Inbox

- Consumer subscribed to `order-events`.
- Consumer joined group `order-event-consumer`.
- Partition 0 was assigned.
- Consumer processed the order event.
- Inbox record was persisted.
- Re-publishing the same event ID resulted in `Duplicate event skipped`.

### Notification creation

A later order produced these observed logs:

```text
Order confirmation notification created for order:
045609a8-6854-4511-a0c2-9a0aa69227da

Processed event:
82817427-c863-471e-983e-78da80aa58fe
```

The notification was verified using:

```sql
SELECT
    id,
    user_id,
    order_id,
    notification_type,
    message,
    status,
    created_at
FROM notifications
ORDER BY created_at DESC
LIMIT 5;
```

Observed values included:

```text
order_id:          045609a8-6854-4511-a0c2-9a0aa69227da
notification_type: order_confirmation
message:           Your order has been received successfully!
status:            pending
```

---

# 23. Relevant project structure

```text
src/
├── api/
│   ├── health.py
│   ├── products.py
│   ├── inventory.py
│   └── orders.py
│
├── core/
│   ├── db.py
│   └── kafka.py
│
├── models/
│   ├── outbox_event_model.py
│   ├── processed_event_model.py
│   └── notification_model.py
│
├── repositories/
│   ├── outbox_repository.py
│   ├── processed_event_repository.py
│   └── notification_repository.py
│
├── services/
│   ├── outbox_service.py
│   ├── outbox_worker.py
│   └── event_consumer_service.py
│
└── main.py

migrations/
└── versions/
```

This is the relevant structure for the Day 3 and Day 4 work. Other Product, Inventory, Order, and shared modules remain part of the application.

---

# 24. Day 3 checklist – Outbox and Kafka

- [x] Configured Docker Desktop for local Kafka.
- [x] Started Apache Kafka using Docker Compose.
- [x] Verified the Kafka broker.
- [x] Created `order-events`.
- [x] Learned brokers, topics, partitions, offsets, producers, and consumers.
- [x] Installed `aiokafka`.
- [x] Created the Kafka producer factory.
- [x] Implemented Outbox Repository.
- [x] Implemented Outbox Publisher.
- [x] Implemented Outbox background worker.
- [x] Added `SELECT FOR UPDATE SKIP LOCKED` for safe event claiming.
- [x] Integrated producer and worker into FastAPI lifespan.
- [x] Published order events to Kafka.
- [x] Verified published outbox records in PostgreSQL.
- [x] Verified messages with Kafka console consumer.
- [x] Learned the at-least-once delivery limitation.

# 25. Day 4 checklist – Consumer, Inbox, and notifications

- [x] Created `ProcessedEvent` model.
- [x] Registered the model with Alembic.
- [x] Generated and applied the processed-events migration.
- [x] Verified `processed_events` in PostgreSQL.
- [x] Created Processed Event Repository.
- [x] Implemented `claim_event()` with `ON CONFLICT DO NOTHING`.
- [x] Implemented class-based Kafka consumer.
- [x] Configured consumer group and manual offset commits.
- [x] Integrated consumer into FastAPI lifespan.
- [x] Received and processed `order.created`.
- [x] Manually re-published a duplicate event.
- [x] Verified duplicate detection.
- [x] Created Notification model.
- [x] Generated and applied notification migration.
- [x] Verified `notifications` in PostgreSQL.
- [x] Created Notification Repository.
- [x] Implemented order confirmation notification creation.
- [x] Used the same database session for Inbox and notification inserts.
- [x] Verified notification persistence.

---

# 26. Known limitations and future hardening

| Area | Current state | Future improvement |
|---|---|---|
| Outbox retries | Pending rows are retried by polling | Retry counters, backoff, and failed-event handling |
| Duplicate delivery | Inbox detection implemented and manually tested | Automated failure and concurrency tests |
| Inbox uniqueness | Unique `event_id` | Composite `(consumer_name, event_id)` before multiple independent groups |
| Transaction rollback | Same-session transaction implemented | Deliberate failure-injection test |
| Consumer errors | Exceptions are logged and propagated | Controlled retry policy and dead-letter handling |
| Graceful shutdown | Background tasks are cancelled | Graceful draining of in-progress work |
| Notification delivery | Notification record is created | Delivery worker and provider integration |
| Notification topic | Not implemented | Optional `notification-events` topic with its own Outbox |
| Kafka deployment | One local broker, one partition | Multi-broker production configuration, replication, monitoring |
| Database access | Synchronous SQLAlchemy sessions | Evaluate async DB access or thread offloading |
| Event schema | Consumer accepts observed key variants | Standardize envelope and add schema/version management |

### Delivery guarantee

The current design is not exactly-once delivery. It combines:

- Durable Outbox records.
- At-least-once event publishing.
- Inbox-based duplicate detection.
- Database transactions.
- Kafka offset commits after database commit.

This provides reliable, idempotent processing for the implemented single-consumer flow, subject to the Inbox uniqueness limitation and the remaining failure-handling work.

---

# 27. Suggested future engineering topics

1. Retry policies and exponential backoff.
2. Dead Letter Queues (DLQ).
3. Graceful shutdown and worker draining.
4. Automated tests for duplicate delivery and transaction rollback.
5. Multiple independent Kafka consumer groups.
6. Inventory event consumer.
7. Analytics event consumer.
8. Notification delivery worker.
9. Optional separate notification event pipeline.
10. Monitoring, structured logging, and observability.
11. Kafka partitioning and consumer scaling.
12. Deployment and production configuration.

These are future topics, not completed features.

---

# 28. Final Day 3 and Day 4 status

**Day 3:** The Transactional Outbox Publisher and local Kafka integration were implemented. Order events were successfully published from PostgreSQL to Kafka and verified.

**Day 4:** The Kafka consumer and Inbox Pattern were implemented. Duplicate delivery was manually tested and correctly skipped. A notification model and repository were added, and the consumer creates order confirmation notification records using the same database transaction as the Inbox record.

The deliberate rollback test, production-grade retries, dead-letter handling, full graceful shutdown, and external notification delivery remain future work.

Project: E-Commerce Backend Engineering Lab  
Architecture: Modular Monolith  
Backend: FastAPI  
Database: PostgreSQL  
ORM and migrations: SQLAlchemy + Alembic  
Message broker: Apache Kafka  
Kafka client: aiokafka

---

# Project motto

**Simple business logic. Deep engineering.**

Build incrementally. Measure everything. Document decisions. Experiment with failures. Understand every technology you introduce.