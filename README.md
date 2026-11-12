# E-Commerce Backend Engineering Lab

> A production-style backend engineering learning project built
> incrementally with Python, FastAPI, PostgreSQL, Redis/Valkey, Kafka,
> RabbitMQ, Elasticsearch/OpenSearch, Docker, Kubernetes, and modern
> observability tools.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Docker](https://img.shields.io/badge/Docker-Containers-blue)
![Architecture](https://img.shields.io/badge/Architecture-Distributed-purple)

------------------------------------------------------------------------

## 1. Project overview

This repository is a hands-on backend engineering laboratory. The
business application is intentionally small: an e-commerce
order-management system with users, products, inventory, payments
(simulated initially), and orders. The engineering environment evolves
in stages until it resembles a production-style distributed system.

The goal is not to maximize the number of technologies. The goal is to
understand the problems, failure modes, trade-offs, and recovery
procedures behind the architecture.

### User-facing functionality

-   Register and log in.
-   Browse, create, update, retrieve, and archive products.
-   Create and retrieve orders.
-   Update permitted order fields.
-   Cancel orders.
-   Search and filter products and orders.
-   View order history.
-   View inventory availability.
-   Receive order and payment-status notifications.

### Learning objectives

-   REST API design and clean architecture.
-   Authentication, authorization, and application security.
-   Relational data modelling, transactions, and SQL performance.
-   Caching, connection pooling, and distributed rate limiting.
-   Load balancing and horizontal scaling.
-   Event-driven architecture and background processing.
-   Microservices and service/data ownership.
-   Distributed transactions, idempotency, ordering, and eventual
    consistency.
-   Search indexing and schema evolution.
-   Metrics, structured logs, and distributed tracing.
-   Containers, Kubernetes, CI/CD, and infrastructure automation.
-   Performance, resilience, security, and failure testing.

### Engineering principles

1.  Start with a modular monolith and evolve deliberately.
2.  Introduce a technology only when it solves a real problem.
3.  Keep PostgreSQL as the source of truth for transactional data.
4.  Design for failure, duplicate messages, retries, timeouts, and
    recovery.
5.  Make business operations idempotent where clients or brokers may
    retry.
6.  Measure performance rather than assuming an optimization helps.
7.  Keep services independently testable and deployable.
8.  Give each microservice clear ownership of its data.
9.  Document important decisions in Architecture Decision Records
    (ADRs).
10. Prefer local, open-source development infrastructure where
    practical.

------------------------------------------------------------------------

## 2. Target system architecture

The following is the eventual target, not the day-one implementation.
Payment processing may initially be simulated inside the Order Service;
it can become an independently deployable Payment Service in a later
phase.

``` mermaid
flowchart TB
    Client[Client / Frontend]
    LB[NGINX Reverse Proxy and Load Balancer]
    Gateway[API Gateway]

    Client --> LB --> Gateway

    Gateway --> Auth[Auth Service]
    Gateway --> Order[Order Service]
    Gateway --> Product[Product Service]
    Gateway --> Inventory[Inventory Service]
    Gateway --> Search[Search API]
    Gateway --> Payment[Payment Service - later phase]

    Auth --> AuthDB[(Auth PostgreSQL)]
    Order --> OrderDB[(Order PostgreSQL)]
    Product --> ProductDB[(Product PostgreSQL)]
    Inventory --> InventoryDB[(Inventory PostgreSQL)]
    Payment --> PaymentDB[(Payment PostgreSQL)]

    Gateway --> Cache[(Redis / Valkey)]
    Order --> Cache
    Product --> Cache

    Order --> Outbox[(Transactional Outbox)]
    Outbox --> Publisher[Outbox Publisher]
    Publisher --> Kafka[(Apache Kafka)]

    Kafka --> Inventory
    Kafka --> Notification[Notification Service]
    Kafka --> Indexer[Search Indexer]
    Kafka --> Payment

    Notification --> Rabbit[(RabbitMQ Task Queues)]
    Rabbit --> Email[Email Workers]

    Indexer --> SearchDB[(Elasticsearch / OpenSearch)]
    Search --> SearchDB

    Auth --> Obs[Observability Stack]
    Order --> Obs
    Product --> Obs
    Inventory --> Obs
    Notification --> Obs
    Payment --> Obs
```

### Architecture layers

  -----------------------------------------------------------------------
  Layer                   Responsibility          Technologies
  ----------------------- ----------------------- -----------------------
  Client                  User interaction        React or minimal
                                                  frontend

  Reverse proxy           Traffic distribution    NGINX
                          and TLS termination     

  API gateway             Routing and request     FastAPI or Traefik
                          policies                

  Application             Business rules and APIs FastAPI

  Persistence             Transactional storage   PostgreSQL

  Connection pooling      Manage database         PgBouncer; SQLAlchemy
                          connections             pools

  Cache                   Frequently accessed or  Redis / Valkey
                          temporary data          

  Event streaming         Domain event            Kafka
                          distribution            

  Task queue              Background job          RabbitMQ
                          execution               

  Search                  Full-text search and    Elasticsearch /
                          indexing                OpenSearch

  Metrics                 Service and             Prometheus
                          infrastructure metrics  

  Dashboards              Visualization and       Grafana
                          alerting                

  Logging                 Centralized logs        Loki

  Tracing                 Distributed request     OpenTelemetry, Jaeger
                          traces                  

  Deployment              Containers and          Docker, Kubernetes
                          orchestration           
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Architecture evolution

Do not begin with many microservices. Build understanding in this order:

``` mermaid
flowchart TD
    A[FastAPI CRUD]
    B[Modular Monolith]
    C[Docker Compose]
    D[Performance: Cache, Pools, Limits, Load Balancing]
    E[Messaging and Background Workers]
    F[Extract Microservices]
    G[Distributed Patterns and Search]
    H[Observability and Reliability]
    I[Kubernetes and CI/CD]

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

### Stage 1 --- Modular monolith

One FastAPI application with clearly separated modules:

-   Authentication and users.
-   Products.
-   Orders.
-   Inventory.
-   Payments (simulated).
-   Shared infrastructure.

### Stage 2 --- Containerization

Run the API, PostgreSQL, Redis/Valkey, and NGINX with Docker Compose.

### Stage 3 --- Performance

Add caching, rate limiting, connection pooling, PgBouncer experiments,
multiple API instances, and load testing.

### Stage 4 --- Asynchronous workflows

Introduce Kafka for domain events and RabbitMQ for selected background
tasks.

### Stage 5 --- Microservices

Extract independently deployable services with clear data ownership.
Introduce a Payment Service when the learning objectives justify the
additional boundary.

### Stage 6 --- Distributed systems

Implement the transactional outbox, idempotent consumers, event
ordering, Saga workflows, retries, and eventual consistency.

### Stage 7 --- Production engineering

Add observability, Kubernetes, CI/CD, security scanning, backups,
disaster recovery, and operational runbooks.

------------------------------------------------------------------------

## 4. Service boundaries and responsibilities

### 4.1 Auth Service

**Responsibilities:** identity, authentication, and authorization.

Features:

-   User registration and login.
-   Password hashing.
-   Access-token generation and validation.
-   Refresh-token rotation and revocation.
-   Logout.
-   Role-based access control (RBAC).
-   Password reset flow.

Suggested stack: FastAPI, PostgreSQL, SQLAlchemy, Pydantic,
`pwdlib[argon2]`, and a maintained JWT library.

**Security note:** Benchmark and explicitly configure Argon2 memory
cost, time cost, and parallelism for the deployment environment. Keep
password verification resource usage controlled, and combine it with
rate limiting and abuse monitoring.

### 4.2 Product Service

**Responsibilities:** product catalogue management.

Features:

-   Create, retrieve, update, and archive products.
-   Categories and product status.
-   Product pricing.
-   Product metadata.
-   Cache invalidation after updates.

Suggested stack: FastAPI, PostgreSQL, SQLAlchemy, Redis/Valkey.

### 4.3 Order Service

**Responsibilities:** order lifecycle and customer order history.

Features:

-   Create and retrieve orders.
-   Update permitted order attributes.
-   Cancel orders.
-   Validate ownership.
-   Enforce order state transitions.
-   Idempotent order creation.
-   Publish order domain events through the outbox.

Suggested stack: FastAPI, PostgreSQL, Redis/Valkey, Kafka.

### 4.4 Inventory Service

**Responsibilities:** stock availability and reservation.

Features:

-   Track available and reserved quantities.
-   Reserve stock.
-   Release reservations.
-   Deduct stock after successful completion.
-   Protect against overselling.
-   Publish stock reservation outcomes.

Suggested stack: FastAPI, PostgreSQL, Kafka.

### 4.5 Search Service

**Responsibilities:** search and indexing.

Features:

-   Full-text product search.
-   Order search.
-   Filters, sorting, pagination, and aggregations.
-   Index updates from domain events.
-   Reindexing and index recovery.

Suggested stack: FastAPI, Elasticsearch or OpenSearch, Kafka consumers.

### 4.6 Notification Service

**Responsibilities:** asynchronous notifications.

Features:

-   Consume relevant domain events from Kafka.
-   Convert events into notification tasks.
-   Publish tasks to RabbitMQ.
-   Track notification delivery status.
-   Retry failed delivery.
-   Dead-letter handling.
-   Avoid scheduling duplicate notifications for duplicate input events.

Suggested stack: Python workers, Kafka, RabbitMQ, and an email adapter.
Use a local mail catcher during development rather than a paid email
service.

**Messaging boundary:**

-   Kafka distributes business/domain events, such as `OrderCreated` and
    `OrderCancelled`, to independently interested services.
-   RabbitMQ distributes executable background tasks, such as sending an
    email or generating a PDF, to competing workers.
-   A typical notification path is: Kafka event → Notification Service
    consumer → RabbitMQ task → Email Worker.

Do not use both brokers for the same workflow without a clear reason.

### 4.7 Payment Service (later phase)

**Responsibilities:** payment lifecycle and integration boundary.

Initially, simulate payment outcomes within the modular monolith. In a
later phase, extract a Payment Service with:

-   Payment authorization and capture.
-   Payment status tracking.
-   Refund handling.
-   Provider webhook processing.
-   Idempotent payment operations.
-   Reconciliation for uncertain outcomes.

Never store raw card details. Use a payment provider's tokenized
workflow. A timeout does not prove that a payment failed; the provider
may have completed it without the response reaching the application.

### Service ownership rule

Each microservice owns its data. Other services must not directly read
or modify its database tables. Communicate through APIs or messages.
During early local development, a single PostgreSQL server can host
separate databases, but logical ownership must remain clear.

------------------------------------------------------------------------

## 5. Important request and event flows

### 5.1 Registration

``` mermaid
sequenceDiagram
    actor User
    participant Client
    participant Gateway
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>Client: Submit registration
    Client->>Gateway: POST /api/v1/auth/register
    Gateway->>Auth: Forward request
    Auth->>Auth: Validate input
    Auth->>DB: Check unique email
    DB-->>Auth: Email available
    Auth->>Auth: Hash password with Argon2
    Auth->>DB: Insert user
    DB-->>Auth: User created
    Auth-->>Client: Registration response
    Client-->>User: Confirmation
```

Consider unique constraints, duplicate-registration responses, input
validation, transaction boundaries, and safe error messages.

### 5.2 Login

``` mermaid
sequenceDiagram
    actor User
    participant Client
    participant Gateway
    participant Redis
    participant Auth
    participant DB as PostgreSQL

    User->>Client: Enter credentials
    Client->>Gateway: POST /api/v1/auth/login
    Gateway->>Redis: Check login rate limit
    Redis-->>Gateway: Allowed
    Gateway->>Auth: Forward credentials
    Auth->>DB: Retrieve user
    DB-->>Auth: User record
    Auth->>Auth: Verify password
    Auth->>Auth: Create short-lived access token
    Auth->>Auth: Create refresh token
    Auth->>DB: Store refresh-token hash
    Auth-->>Client: Return token response
```

Use short-lived access tokens, refresh-token rotation, server-side
revocation, and secure storage. Never log tokens or passwords. Tune
Argon2 parameters and authentication concurrency controls for the
environment.

### 5.3 Create order with idempotency

Clients should send an `Idempotency-Key` for order creation. This
protects against duplicate orders when a user double-clicks, a client
retries, or a response is lost after the server commits.

Example request:

``` http
POST /api/v1/orders
Authorization: Bearer <access-token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

Suggested flow:

``` mermaid
sequenceDiagram
    actor User
    participant Client
    participant Gateway
    participant Order as Order Service
    participant DB as Order PostgreSQL
    participant Outbox
    participant Kafka
    participant Inventory
    participant Notification

    User->>Client: Place order
    Client->>Gateway: POST /api/v1/orders + Idempotency-Key
    Gateway->>Order: Authenticated request
    Order->>Order: Validate ownership and input
    Order->>DB: Begin transaction
    Order->>DB: Claim/check idempotency key
    Order->>DB: Insert PENDING order and items
    Order->>Outbox: Insert OrderCreated event
    Order->>DB: Store idempotency result
    Order->>DB: Commit transaction
    Order-->>Client: Original order response

    Outbox->>Kafka: Publish event asynchronously
    Kafka->>Inventory: OrderCreated
    Inventory->>Inventory: Reserve stock
    Inventory->>Kafka: StockReserved or StockRejected
    Kafka->>Order: Reservation result
    Order->>DB: Update order state
    Kafka->>Notification: Order state event
    Notification->>Notification: Enqueue notification task
```

Recommended idempotency behavior:

-   Same key and same request payload: return the original result.
-   Same key and different payload: reject, typically with HTTP 409.
-   Same key while the first request is processing: return a documented
    in-progress/conflict response.
-   Expired key: follow a documented retention and cleanup policy.

Use a unique constraint scoped to the caller, such as
`(user_id, idempotency_key)`, and store a request hash to detect payload
mismatches. PostgreSQL should provide the durable correctness guarantee.
Redis can be used as an optimization, but should not be the only record
protecting order creation.

The idempotency record, order, order items, and outbox event should be
coordinated in the same database transaction.

The initial request should not wait for every downstream service. An
order may begin in `PENDING` and later transition to `CONFIRMED` or
`REJECTED`. Define legal state transitions in the Order Service.

### 5.4 Order cancellation

``` mermaid
flowchart TD
    A[Cancellation request]
    B[Authenticate user]
    C[Validate order ownership]
    D{Cancellation allowed?}
    E[Return conflict]
    F[Update order state]
    G[Write cancellation outbox event]
    H[Publish event]
    I[Inventory receives event]
    J[Release reserved stock]
    K[Notify customer]

    A --> B --> C --> D
    D -->|No| E
    D -->|Yes| F --> G --> H --> I --> J --> K
```

Cancellation must be idempotent. Repeated requests must not release
inventory multiple times. Define behavior for cancellation racing with
payment capture or order confirmation.

------------------------------------------------------------------------

## 6. Database design

### 6.1 Logical entity relationship model

``` mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : referenced_by
    ORDERS ||--o{ PAYMENTS : has
    USERS ||--o{ REFRESH_TOKENS : owns
    PRODUCTS ||--o{ INVENTORY : tracked_in
    USERS ||--o{ IDEMPOTENCY_RECORDS : creates
    ORDERS ||--o{ OUTBOX_EVENTS : produces

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string role
        datetime created_at
    }

    PRODUCTS {
        uuid id PK
        string name
        text description
        decimal price
        string status
        datetime created_at
    }

    ORDERS {
        uuid id PK
        uuid user_id
        string status
        decimal total_amount
        string currency
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id
        uuid product_id
        int quantity
        decimal unit_price
        decimal subtotal
    }

    PAYMENTS {
        uuid id PK
        uuid order_id
        decimal amount
        string status
        string transaction_reference
    }

    INVENTORY {
        uuid id PK
        uuid product_id
        int available_quantity
        int reserved_quantity
        datetime updated_at
    }

    REFRESH_TOKENS {
        uuid id PK
        uuid user_id
        string token_hash
        datetime expires_at
        datetime revoked_at
    }

    IDEMPOTENCY_RECORDS {
        uuid id PK
        uuid user_id
        string idempotency_key
        string request_hash
        int response_status
        json response_body
        datetime expires_at
    }

    OUTBOX_EVENTS {
        uuid id PK
        uuid aggregate_id
        string event_type
        int sequence_number
        datetime created_at
        datetime published_at
    }
```

This is a logical learning model. In the final microservices
architecture, do not create cross-service foreign keys or shared-table
ownership. Each service owns its persistence model. The outbox belongs
to the service that writes the corresponding business transaction.

### 6.2 Database concepts to practise

-   Primary and foreign keys.
-   Unique and check constraints.
-   Composite and partial indexes.
-   Transactions and isolation levels.
-   Row-level locking.
-   Optimistic concurrency.
-   Connection pooling.
-   PgBouncer.
-   Alembic migrations.
-   Backup and restore.
-   Read replicas.
-   Partitioning.

Example indexes to evaluate:

``` sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);
```

Do not add indexes blindly. Inspect real query plans with
`EXPLAIN ANALYZE`, and account for the write and storage costs of
indexes.

### 6.3 Order transaction

The order database transaction should atomically:

1.  Claim or validate the idempotency key.
2.  Validate and insert the order.
3.  Insert order items.
4.  Store the idempotency result.
5.  Insert the outbox event.

Commit all database changes together. Do not assume a PostgreSQL
transaction can atomically commit a Kafka publish.

### 6.4 Connection pooling and PgBouncer

FastAPI deployments may multiply database connections across processes,
workers, and service replicas. For example, several application
processes each maintaining their own SQLAlchemy pool can exhaust
PostgreSQL's connection capacity.

Learn:

-   SQLAlchemy pool size, overflow, timeout, and recycle settings.
-   PostgreSQL connection limits and per-connection resource costs.
-   PgBouncer session, transaction, and statement pooling modes.
-   Pool sizing across all application replicas.
-   Pool wait time, saturation, and timeout monitoring.

Transaction pooling has compatibility considerations for session-level
state and prepared statements. Validate driver and application behavior
before using it. PgBouncer complements application-side pooling; it does
not remove the need to size pools responsibly.

------------------------------------------------------------------------

## 7. Cache architecture

Use Redis or Valkey for:

-   Product cache.
-   Rate-limit counters.
-   Optional idempotency lookup acceleration.
-   Temporary data.
-   Distributed coordination experiments.
-   Session-related state if needed.

### Cache-aside flow

``` mermaid
flowchart TD
    A[Client request]
    B[FastAPI]
    C{Cache hit?}
    D[Return cached result]
    E[Query PostgreSQL]
    F[Populate cache with TTL]
    G[Return database result]

    A --> B --> C
    C -->|Yes| D
    C -->|No| E --> F --> G
```

Illustrative pseudocode:

``` python
async def get_product(product_id: str):
    key = f"product:{product_id}"
    cached = await redis.get(key)

    if cached is not None:
        return deserialize(cached)

    product = await repository.get(product_id)

    if product is not None:
        await redis.setex(key, 300, serialize(product))

    return product
```

Production code must handle cache outages, serialization, stale data,
cache stampedes, and invalidation. PostgreSQL remains authoritative for
orders and other transactional records.

### Redis and Valkey compatibility

Valkey is a Redis-compatible, open-source implementation that supports
the RESP protocol. Many Redis clients and common commands work with
both, but do not assume every command, feature, or client behavior is
identical across all versions.

Keep connection settings environment-driven so the implementation can be
changed without rewriting application logic.

### Cache topics

-   Cache-aside.
-   Write-through and write-behind trade-offs.
-   TTL.
-   Negative caching.
-   Cache stampede prevention.
-   Cache warming.
-   Invalidation after updates.
-   Graceful cache degradation.

------------------------------------------------------------------------

## 8. Load balancing

Run multiple FastAPI instances behind NGINX.

``` mermaid
flowchart TD
    C[Clients]
    N[NGINX]
    A[FastAPI instance 1]
    B[FastAPI instance 2]
    D[FastAPI instance 3]
    P[PgBouncer]
    DB[(PostgreSQL)]

    C --> N
    N --> A
    N --> B
    N --> D
    A --> P
    B --> P
    D --> P
    P --> DB
```

Example NGINX configuration:

``` nginx
upstream fastapi_backend {
    least_conn;
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Study round robin, least connections, reverse proxies, health checks,
timeouts, TLS termination, graceful shutdown, and horizontal scaling.
Configure trusted proxy headers carefully; do not trust arbitrary
client-supplied forwarding headers.

------------------------------------------------------------------------

## 9. Rate limiting

Use Redis/Valkey for distributed rate limits shared across application
instances.

Example learning policies (tune them through experiments):

  Endpoint                 Initial limit
  ---------------- ---------------------
  Login                5 attempts/minute
  Registration         5 requests/minute
  Create order        10 requests/minute
  Read orders        100 requests/minute
  Product search      60 requests/minute

### Token bucket algorithm

``` mermaid
flowchart TD
    A[Incoming request]
    B[Identify user or IP]
    C[Read shared bucket]
    D{Token available?}
    E[Allow and consume token]
    F[Return HTTP 429]
    G[Refill over time]

    A --> B --> C --> D
    D -->|Yes| E
    D -->|No| F
    G --> C
```

Implement atomic updates using Redis Lua scripts or another atomic
primitive. Compare fixed-window, sliding-window, token-bucket, and
leaky-bucket approaches. Return appropriate rate-limit headers.

------------------------------------------------------------------------

## 10. Messaging: Kafka and RabbitMQ

Use the two technologies for distinct learning purposes.

### 10.1 Kafka --- domain event streaming

Possible topics:

``` text
order.created
order.confirmed
order.rejected
order.cancelled
inventory.reserved
inventory.rejected
payment.completed
payment.failed
product.updated
```

``` mermaid
flowchart LR
    O[Order Service]
    K[(Kafka)]
    I[Inventory Consumer]
    N[Notification Consumer]
    S[Search Index Consumer]
    P[Payment Consumer]

    O -->|OrderCreated| K
    K --> I
    K --> N
    K --> S
    K --> P
```

Learn producers, topics, partitions, offsets, consumer groups,
retention, replication, delivery semantics, event replay, and idempotent
processing.

Define event schemas and versions. Include an event ID, event type,
aggregate ID, occurrence timestamp, schema version, and---where ordering
matters---an aggregate sequence number.

**Ordering:** Kafka guarantees ordering within a partition, not across
all partitions. Use the aggregate ID (for example, order ID) as the
message key when events for that aggregate must be processed in order.
Consumers should still validate sequence/state and handle stale or
unexpected events.

### 10.2 RabbitMQ --- background task processing

``` mermaid
flowchart TD
    A[Notification Service]
    B[Exchange]
    C[Email Queue]
    D[Email Worker]
    E[Dead Letter Queue]

    A --> B --> C --> D
    D -->|Success| F[ACK]
    D -->|Repeated failure| E
```

Use it for email delivery, invoice/PDF generation, retryable background
jobs, and selected delayed tasks.

Learn exchanges, queues, routing keys, bindings, acknowledgements,
prefetch, durable queues, dead-letter exchanges, and retry policies.

### 10.3 Choosing between them

  Kafka                                     RabbitMQ
  ----------------------------------------- ---------------------------
  Event streaming and retained event logs   Message/task routing
  Topics and partitions                     Exchanges and queues
  Consumer offsets                          Message acknowledgements
  Replay from retained offsets              Queue-oriented redelivery
  Consumer groups                           Competing consumers

Do not use both for the same workflow without a clear reason.

### 10.4 Message delivery and idempotency

Assume messages can be delivered more than once. A consumer should
record processed event IDs or otherwise make its business effect
idempotent. Acknowledge messages only after the relevant work is safely
committed. Define retry limits, backoff, poison-message handling, and
dead-letter recovery procedures.

------------------------------------------------------------------------

## 11. Transactional outbox

### The problem

PostgreSQL may commit an order while Kafka is unavailable. If the
application simply tries to publish after committing, the event can be
lost.

A publisher can also successfully publish to Kafka and then crash before
recording `published_at`. The event may therefore be published again.

### The solution

Write the order and an outbox record in the same PostgreSQL transaction.
A separate publisher sends pending outbox records to Kafka.

``` mermaid
flowchart TD
    A[Create order request]
    B[Order Service]
    C[(PostgreSQL transaction)]
    D[Order and outbox rows]
    E[Outbox publisher]
    F[(Kafka)]
    G[Consumers]

    A --> B --> C --> D
    D --> E --> F --> G
```

Suggested outbox fields:

-   `id` --- unique event ID.
-   `aggregate_id` --- order or other aggregate.
-   `event_type`.
-   `payload`.
-   `schema_version`.
-   `sequence_number` --- if aggregate ordering is required.
-   `created_at`.
-   `published_at`.
-   `attempt_count`.
-   `last_error`.
-   Optional claim/lease fields such as `claimed_by` and `lease_until`.

### Multiple publisher replicas

If multiple publisher instances run concurrently, coordinate claims
using PostgreSQL row locks. A common pattern is:

``` sql
BEGIN;

SELECT id, aggregate_id, event_type, payload
FROM outbox_events
WHERE published_at IS NULL
  AND (lease_until IS NULL OR lease_until < NOW())
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 100;

-- Claim selected rows and set a lease.
-- Commit the claim before doing slow network publishing.

COMMIT;
```

After publishing, mark each successfully published event and clear its
lease. Use bounded leases and reclaim expired claims after worker
failure.

`FOR UPDATE SKIP LOCKED` prevents active workers from claiming the same
locked rows during the claim transaction. It does **not** guarantee
exactly-once publication. A crash after Kafka accepts a message but
before the database records success can still produce a duplicate.
Consumers must be idempotent.

Avoid holding a database transaction and row locks open while waiting on
slow broker network operations. For more advanced throughput and
CDC-based publishing, investigate Debezium and PostgreSQL change-data
capture.

------------------------------------------------------------------------

## 12. Distributed transactions and Saga

A business workflow spanning services cannot be protected by one
ordinary local database transaction. Use a Saga with compensating
actions.

``` mermaid
flowchart TD
    A[Create order]
    B[Reserve inventory]
    C[Authorize payment]
    D[Confirm order]
    E[Release inventory]
    F[Void or refund payment]
    G[Reject order]

    A --> B
    B -->|Success| C
    B -->|Failure| G
    C -->|Success| D
    C -->|Failure| E --> F --> G
```

Study choreography-based and orchestration-based Sagas, compensating
transactions, timeouts, retries, idempotency, and recovery.

Payment failure needs careful treatment:

-   A declined payment is different from an unknown payment outcome.
-   A timeout may mean the provider completed the operation but the
    response was lost.
-   Use provider idempotency keys and query/reconciliation workflows
    before retrying uncertain operations.
-   Refunds and voids are compensating business actions, not database
    rollbacks.

------------------------------------------------------------------------

## 13. Search architecture

PostgreSQL remains the source of truth. Elasticsearch/OpenSearch is a
derived search index.

``` mermaid
flowchart TD
    A[Product updated]
    B[(PostgreSQL)]
    C[Outbox]
    D[(Kafka)]
    E[Search index consumer]
    F[(Elasticsearch / OpenSearch)]
    G[Search API]
    H[Client]

    A --> B
    B --> C --> D --> E --> F
    H --> G --> F
```

Implement full-text search, fuzzy matching, filtering, sorting,
aggregations, product search, and order search.

Understand eventual consistency: a committed database update may take
time to appear in the search index. Implement retry, dead-letter
handling, monitoring of indexing lag, and reindexing procedures.

### Event schema evolution

Domain events are contracts between independently deployed services.
Practise:

-   Adding optional fields without breaking older consumers.
-   Versioning incompatible changes.
-   Handling unknown fields.
-   Testing producer/consumer compatibility.
-   Replaying retained events against updated consumers.
-   Rebuilding indexes from authoritative data or retained events.

------------------------------------------------------------------------

## 14. API design

Use a versioned base path:

``` text
/api/v1/
```

### Authentication endpoints

  Method   Endpoint           Purpose
  -------- ------------------ ----------------
  POST     `/auth/register`   Register
  POST     `/auth/login`      Login
  POST     `/auth/refresh`    Refresh tokens
  POST     `/auth/logout`     Logout
  GET      `/auth/me`         Current user

### Product endpoints

  Method   Endpoint           Purpose
  -------- ------------------ -------------------
  POST     `/products`        Create
  GET      `/products`        List
  GET      `/products/{id}`   Retrieve
  PATCH    `/products/{id}`   Update
  DELETE   `/products/{id}`   Archive or delete

### Order endpoints

  Method   Endpoint                Purpose
  -------- ----------------------- ----------------------------------
  POST     `/orders`               Create; accept `Idempotency-Key`
  GET      `/orders`               List current user's orders
  GET      `/orders/{id}`          Retrieve
  PATCH    `/orders/{id}`          Update permitted fields
  POST     `/orders/{id}/cancel`   Cancel

Cancellation is a business action, not an unrestricted delete.

### Inventory endpoints

  Method   Endpoint                                 Purpose
  -------- ---------------------------------------- ----------------
  GET      `/inventory/{product_id}`                Retrieve stock
  POST     `/inventory/reservations`                Reserve stock
  POST     `/inventory/reservations/{id}/release`   Release stock

### Search endpoints

  Method   Endpoint             Purpose
  -------- -------------------- -----------------
  GET      `/search/products`   Search products
  GET      `/search/orders`     Search orders

### Response examples

Success:

``` json
{
  "success": true,
  "message": "Order created successfully",
  "data": {
    "id": "order-uuid",
    "status": "PENDING",
    "total_amount": 1500.00,
    "currency": "INR"
  }
}
```

Paginated response:

``` json
{
  "success": true,
  "data": [],
  "meta": {
    "next_cursor": "opaque-cursor",
    "has_more": true
  }
}
```

Error:

``` json
{
  "success": false,
  "message": "Insufficient inventory",
  "error_code": "INVENTORY_UNAVAILABLE",
  "details": null
}
```

Use `meta` when it contains useful information, such as pagination
cursors. Omit it when empty rather than always returning `null`.

Use HTTP status codes consistently:

    Status Meaning
  -------- --------------------------------------------
       200 Successful retrieval or update
       201 Resource created
       202 Asynchronous operation accepted
       204 Successful operation without response body
       400 Invalid request
       401 Unauthenticated
       403 Forbidden
       404 Not found
       409 Conflict
       422 Validation failure
       429 Rate limited
       500 Internal error
       503 Temporarily unavailable

Use cursor pagination for large or frequently changing datasets; offset
pagination is acceptable for simpler early exercises.

------------------------------------------------------------------------

## 15. Security requirements

  -----------------------------------------------------------------------
  Area                                Implementation
  ----------------------------------- -----------------------------------
  Authentication                      JWT access tokens

  Password storage                    Argon2

  Authorization                       RBAC and ownership checks

  Token renewal                       Refresh-token rotation

  Token revocation                    Server-side token state

  Request validation                  Pydantic

  Rate limiting                       Redis/Valkey

  Transport                           HTTPS outside local development

  Secrets                             Environment variables locally;
                                      secret manager in production

  SQL injection prevention            Parameterized SQL / SQLAlchemy

  CORS                                Explicit origin allowlist

  Container security                  Non-root users and minimal images

  Dependency security                 Automated scanning
  -----------------------------------------------------------------------

Rules:

1.  Never commit `.env` files or credentials.
2.  Never store plaintext passwords or refresh tokens.
3.  Never trust client-supplied prices or totals.
4.  Verify order ownership on every relevant request.
5.  Prevent ordinary users from changing their own roles.
6.  Do not expose stack traces to API clients.
7.  Validate event payloads.
8.  Do not assume internal network traffic is automatically trusted.
9.  Apply authorization at the service boundary.
10. Use secure cookie settings if tokens are stored in cookies.
11. Tune Argon2 parameters and authentication concurrency controls.
12. Verify payment webhooks and protect against replay.
13. Keep secrets out of logs, traces, and event payloads.

------------------------------------------------------------------------

## 16. Observability

Observability is part of the application, not an optional final
decoration.

### Metrics --- Prometheus

Monitor:

-   Request count and duration.
-   Error rate.
-   Active requests.
-   CPU and memory.
-   Database connection usage and pool wait time.
-   PgBouncer pool saturation.
-   Cache hit ratio.
-   Kafka consumer lag.
-   RabbitMQ queue depth.
-   Background job failures.
-   Outbox backlog and oldest unpublished event age.
-   Search indexing lag.

### Dashboards --- Grafana

Create dashboards for API performance, database health, connection
pools, cache health, broker health, outbox processing, service health,
and resource utilization.

### Logging --- Loki

Use structured JSON logs. Example:

``` json
{
  "timestamp": "2026-11-09T12:00:00Z",
  "level": "INFO",
  "service": "order-service",
  "trace_id": "trace-123",
  "event": "order_created",
  "order_id": "order-456"
}
```

Do not log credentials, passwords, tokens, payment secrets, or sensitive
personal information.

### Tracing --- OpenTelemetry and Jaeger

``` mermaid
flowchart LR
    A[Client]
    B[API Gateway]
    C[Order Service]
    D[(PostgreSQL)]
    E[(Kafka)]
    F[Inventory Consumer]
    G[(RabbitMQ)]
    H[Email Worker]

    A --> B --> C
    C --> D
    C --> E --> F
    E --> G --> H
```

Propagate W3C Trace Context across HTTP and messaging boundaries:

-   Use `traceparent` and, when applicable, `tracestate`.
-   Inject trace context into Kafka message headers.
-   Extract trace context in Kafka consumers.
-   Inject trace context into RabbitMQ message properties/headers.
-   Extract trace context in RabbitMQ workers.
-   Configure OpenTelemetry instrumentation for the relevant frameworks
    and clients.

This allows a trace to connect the incoming request with downstream
consumers and background workers. Messaging spans may be linked rather
than represented as a simple parent-child chain, depending on the
processing model.

Practise tracing one order from the API request through the outbox
publisher, Kafka, Inventory Service, Notification Service, RabbitMQ, and
an email worker.

------------------------------------------------------------------------

## 17. Docker architecture

Start with a small Compose environment:

``` mermaid
flowchart TD
    D[Docker Compose]
    D --> N[NGINX]
    D --> API[FastAPI]
    D --> P[PgBouncer - optional early stage]
    D --> DB[(PostgreSQL)]
    D --> R[(Redis / Valkey)]
    N --> API
    API --> P
    P --> DB
    API --> R
```

Later add Kafka, RabbitMQ, Elasticsearch/OpenSearch, Prometheus,
Grafana, Loki, and Jaeger.

Each service should have:

-   A Dockerfile.
-   A `.dockerignore`.
-   A health check.
-   Explicit configuration.
-   A non-root runtime user where possible.
-   Persistent volumes for stateful services.
-   Resource limits where supported.
-   A documented startup and shutdown procedure.

Use separate networks where useful. Expose only ports that need host
access.

------------------------------------------------------------------------

## 18. Kubernetes architecture

Kubernetes is an advanced stage. First become comfortable with Docker
and Compose.

Learn:

-   Pods and Deployments.
-   Services.
-   ConfigMaps and Secrets.
-   Ingress.
-   Horizontal Pod Autoscaler.
-   Persistent Volumes and Claims.
-   StatefulSets.
-   Readiness, liveness, and startup probes.
-   Resource requests and limits.
-   Rolling updates.
-   Helm.

``` mermaid
flowchart TD
    Internet --> Ingress
    Ingress --> Gateway
    Gateway --> Auth
    Gateway --> Order
    Gateway --> Product
    Order --> Postgres
    Order --> PgBouncer
    Order --> Redis
    Order --> Kafka
    Kafka --> Inventory
    Kafka --> Notification
    Notification --> RabbitMQ
```

Use Minikube or k3d locally. Stateful infrastructure requires careful
storage and backup planning even in local Kubernetes.

------------------------------------------------------------------------

## 19. Testing strategy

### Unit tests

Use Pytest for business rules, order calculations, validation,
permissions, state transitions, and idempotency behavior.

### Integration tests

Test PostgreSQL, Redis/Valkey, Kafka, RabbitMQ, search indexing, and
migrations. Use isolated test environments and clean test data.

### API tests

Use HTTPX and Bruno/Postman to test valid and invalid requests,
authentication, authorization, duplicate requests, idempotency-key
reuse, pagination, filtering, and error handling.

### Concurrency tests

Make these explicit exercises:

1.  Attempt to purchase the final inventory unit from two concurrent
    requests; verify that stock cannot become negative.
2.  Submit the same order idempotency key concurrently; verify that only
    one order is created.
3.  Run multiple outbox publishers; verify that active claims do not
    overlap.
4.  Deliver the same event multiple times; verify that the business
    effect occurs once.
5.  Deliver aggregate events out of order; verify that invalid
    transitions are rejected or safely deferred.

### Load tests

Use Locust or k6. Example experiment levels:

  Scenario                 Purpose
  ------------------------ ---------------
  100 concurrent users     Baseline
  500 concurrent users     Moderate load
  1,000 concurrent users   Higher load
  Sudden traffic spike     Stress test
  Sustained traffic        Soak test

These are experiment targets, not performance promises. Measure requests
per second, p50/p95/p99 latency, error percentage, CPU, memory, database
connections, pool wait time, and broker lag.

------------------------------------------------------------------------

## 20. Chaos engineering and failure scenarios

Intentionally introduce failures and record what happens.

  -----------------------------------------------------------------------
  Failure                             Expected design behavior
  ----------------------------------- -----------------------------------
  PostgreSQL unavailable              Controlled error; no false success

  Redis unavailable                   Safe fallback where possible;
                                      documented degradation

  Kafka unavailable                   Committed outbox events remain
                                      pending

  Publisher crashes after Kafka       Duplicate may occur; consumer
  publish                             remains idempotent

  Publisher replica crashes while     Lease expires and work can be
  holding a lease                     reclaimed

  RabbitMQ unavailable                Task publication retries safely

  One API instance dies               Healthy instances continue serving

  Consumer crashes                    Unacknowledged work is redelivered

  Duplicate event                     No duplicate business effect

  Out-of-order event                  Sequence/state validation prevents
                                      invalid transition

  Slow database                       Timeouts and controlled failure

  Search unavailable                  Core transactional operations
                                      continue

  Notification worker fails           Retry without duplicating orders or
                                      notifications

  Payment provider times out          Treat outcome as unknown until
                                      reconciled

  Connection pool exhausted           Bounded waiting and controlled
                                      failure
  -----------------------------------------------------------------------

Further experiments:

-   Network latency and packet loss.
-   Container restarts.
-   CPU and memory pressure.
-   Connection exhaustion.
-   Poison messages.
-   Consumer lag.
-   Cache stampedes.
-   Database backup restoration.
-   Outbox backlog growth and recovery.
-   Lease expiration and publisher recovery.

------------------------------------------------------------------------

## 21. Recommended technology stack

  Category             Technology
  -------------------- -----------------------------
  Language             Python
  Backend              FastAPI
  Validation           Pydantic
  ORM                  SQLAlchemy
  Migrations           Alembic
  ASGI server          Uvicorn
  Database             PostgreSQL
  Connection pooling   SQLAlchemy pool / PgBouncer
  Cache                Valkey or Redis
  Search               Elasticsearch or OpenSearch
  Event streaming      Apache Kafka
  Task broker          RabbitMQ
  Reverse proxy        NGINX
  API gateway          FastAPI or Traefik
  Authentication       JWT / OAuth2
  Password hashing     Argon2
  Tests                Pytest / HTTPX
  Load testing         Locust / k6
  Containers           Docker
  Orchestration        Kubernetes
  CI/CD                GitHub Actions
  Metrics              Prometheus
  Dashboards           Grafana
  Logging              Loki
  Tracing              OpenTelemetry / Jaeger
  IaC                  Terraform
  Security scanning    Trivy / Bandit
  CDC (advanced)       Debezium

**Compatibility and configuration notes:**

-   Valkey supports RESP and is compatible with many Redis clients and
    commands; verify feature-level compatibility for the selected
    versions.
-   Argon2 memory, time, and parallelism parameters should be
    benchmarked and explicitly configured.
-   PgBouncer pooling mode must be selected with application/driver
    behavior in mind.
-   Pin and document software versions for reproducible experiments.

Licensing varies by product, version, and distribution. Check the
current license before redistributing or using a component commercially.
Self-hosting software can be free of license fees while still requiring
hardware and electricity.

------------------------------------------------------------------------

## 22. Repository structure

Build this structure progressively. During the first phase, keep modules
in one application; extract service directories only when they become
real independent services.

``` text
ecommerce-backend/
├── services/
│   ├── auth-service/
│   ├── order-service/
│   ├── product-service/
│   ├── inventory-service/
│   ├── search-service/
│   ├── notification-service/
│   └── payment-service/          # later phase
├── shared/
│   ├── schemas/
│   ├── events/
│   ├── logging/
│   ├── exceptions/
│   └── utilities/
├── infrastructure/
│   ├── nginx/
│   ├── postgres/
│   ├── pgbouncer/
│   ├── redis/
│   ├── kafka/
│   ├── rabbitmq/
│   ├── elasticsearch/
│   └── monitoring/
├── deployment/
│   ├── docker/
│   ├── kubernetes/
│   ├── helm/
│   └── terraform/
├── tests/
│   ├── integration/
│   ├── e2e/
│   ├── load/
│   └── chaos/
├── docs/
│   ├── architecture/
│   ├── diagrams/
│   ├── api/
│   ├── decisions/
│   ├── experiments/
│   └── runbooks/
├── scripts/
├── .github/
│   └── workflows/
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

------------------------------------------------------------------------

## 23. Development roadmap and completion criteria

### Phase 1 --- Backend foundation

**Build:** FastAPI, PostgreSQL, SQLAlchemy, Alembic, product and order
CRUD, registration, JWT, RBAC, tests.

**Done when:**

-   CRUD endpoints work.
-   Migrations can create and upgrade the schema.
-   Authentication and authorization work.
-   Business logic is separate from route handlers.
-   Unit and integration tests pass.

### Phase 2 --- Docker

**Build:** Dockerfile, Compose, API container, PostgreSQL container,
persistent volume, health checks, environment configuration.

**Done when:** The application starts from a documented Compose command
and data persists across container restarts.

### Phase 3 --- Redis and performance

**Build:** Cache-aside, invalidation, distributed rate limits,
connection pooling, PgBouncer experiments, load tests.

**Done when:** You can compare cached and uncached behavior, explain
consistency trade-offs, and demonstrate controlled pool behavior under
load.

### Phase 4 --- NGINX and load balancing

**Build:** NGINX, multiple API instances, health checks, traffic
distribution, graceful shutdown.

**Done when:** You can demonstrate traffic distribution and controlled
behavior when one API instance becomes unavailable.

### Phase 5 --- Messaging

**Build:** Kafka producer/consumer, RabbitMQ worker, event schemas,
retries, dead-letter handling, transactional outbox, notification
handoff.

**Done when:** An order event triggers asynchronous inventory and
notification workflows, with safe recovery after broker interruption and
duplicate delivery.

### Phase 6 --- Microservices

**Build:** Auth, Order, Product, Inventory, and Notification services;
gateway; service communication; independent data ownership. Extract
Payment Service when its boundary is introduced.

**Done when:** Services can be independently built, tested, and deployed
without direct access to another service's database.

### Phase 7 --- Distributed systems

**Build:** Saga, eventual consistency, idempotent consumers, order
idempotency, concurrency controls, event ordering, payment outcome
recovery, search synchronization.

**Done when:** Duplicate events and interrupted workflows do not produce
duplicate business effects or permanently inconsistent state. Concurrent
purchase tests cannot oversell inventory.

### Phase 8 --- Observability

**Build:** Prometheus, Grafana, Loki, OpenTelemetry, Jaeger, dashboards,
alert rules, W3C trace propagation across brokers.

**Done when:** You can trace one order workflow across services and
diagnose latency or errors, including asynchronous work.

### Phase 9 --- Kubernetes

**Build:** Deployments, Services, Ingress, ConfigMaps, Secrets,
persistent storage, probes, HPA, Helm.

**Done when:** The application runs locally in Kubernetes and you can
demonstrate a rolling update and scaling experiment.

### Phase 10 --- CI/CD and security

**Build:** GitHub Actions, tests, linting, image build, vulnerability
scans, deployment workflow, backup and restore procedure.

**Done when:** A code change triggers automated validation and produces
a deployable image.

------------------------------------------------------------------------

## 24. CI/CD pipeline

``` mermaid
flowchart TD
    A[Developer pushes code]
    B[GitHub Actions]
    C[Lint and format]
    D[Unit tests]
    E[Integration tests]
    F[Security scan]
    G[Build Docker image]
    H[Scan image]
    I[Publish image]
    J[Deploy to environment]
    K[Health verification]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K
```

Use Ruff, Pytest, Bandit, Trivy, Docker, and GitHub Actions. Keep
secrets in the CI platform's secret store, not in repository files.

------------------------------------------------------------------------

## 25. Architecture Decision Records

Create one ADR for each important architectural decision.

Suggested files:

``` text
docs/decisions/
├── 001-modular-monolith-first.md
├── 002-postgresql-as-primary-database.md
├── 003-valkey-for-caching.md
├── 004-nginx-for-load-balancing.md
├── 005-kafka-for-domain-events.md
├── 006-rabbitmq-for-background-jobs.md
├── 007-transactional-outbox.md
├── 008-microservice-data-ownership.md
├── 009-search-index-choice.md
├── 010-opentelemetry-for-tracing.md
├── 011-pgbouncer-pooling-mode.md
├── 012-order-idempotency-strategy.md
└── 013-payment-service-boundary.md
```

ADR template:

``` markdown
# ADR: Decision title

## Status
Proposed / Accepted / Superseded

## Context
What problem are we solving?

## Decision
What approach did we select?

## Alternatives
What other options did we consider?

## Consequences
What are the benefits, costs, and trade-offs?
```

Document why a choice was made, not merely what was installed.

------------------------------------------------------------------------

## 26. Free local development environment

The core learning environment can run locally without paid cloud
infrastructure.

  Requirement          Local option
  -------------------- ----------------------------
  IDE                  VS Code
  Backend              FastAPI
  Database             PostgreSQL
  Connection pooling   PgBouncer
  Cache                Valkey / Redis
  Search               Elasticsearch / OpenSearch
  Streaming            Kafka
  Queue                RabbitMQ
  Reverse proxy        NGINX
  Containers           Docker
  Orchestration        Minikube / k3d
  Monitoring           Prometheus
  Dashboards           Grafana
  Logging              Loki
  Tracing              Jaeger
  Testing              Pytest
  Load testing         Locust
  CI/CD                GitHub Actions
  Source control       GitHub

No paid cloud subscription is required to learn the core concepts.
Public hosting, managed databases, managed caches, and managed
Kubernetes are separate services and may incur charges.

### Hardware guidance

       RAM Suggested approach
  -------- --------------------------------------------------------------
      8 GB Modular monolith and a few infrastructure services at a time
     16 GB Docker Compose with selected services
     32 GB Larger local stack and more simultaneous services
    64 GB+ More extensive local Kubernetes experiments

Do not run every component simultaneously if the machine cannot handle
it. Start and stop infrastructure services as needed.

------------------------------------------------------------------------

## 27. Engineering experiments

Maintain a report for every experiment. Record the hypothesis,
environment, workload, result, graphs, and conclusion.

1.  **Redis/Valkey performance:** compare PostgreSQL-only reads, cache
    hits, and cache misses.
2.  **Load balancing:** compare one API instance with multiple instances
    behind NGINX.
3.  **Rate limiting:** verify consistent limits across multiple API
    instances.
4.  **Database concurrency:** attempt to purchase the last unit from two
    concurrent requests.
5.  **Connection pooling:** compare direct connections with PgBouncer
    under controlled concurrency.
6.  **Kafka failure:** stop Kafka after an order commits and verify
    outbox recovery.
7.  **Outbox publisher coordination:** run multiple publishers and
    verify non-overlapping claims and lease recovery.
8.  **Duplicate events:** deliver the same event more than once and
    verify idempotency.
9.  **Event ordering:** deliver aggregate events in unexpected order and
    verify safe state handling.
10. **Service failure:** stop Inventory Service and verify timeouts,
    retries, and recovery.
11. **Payment uncertainty:** simulate a provider timeout after
    successful authorization and verify reconciliation.
12. **Distributed tracing:** follow one request across the gateway,
    Order Service, database, broker, and consumers.
13. **Search consistency:** update a product and measure index
    propagation delay.
14. **Database tuning:** compare query plans and latency before and
    after selected indexes.
15. **Argon2 tuning:** benchmark password verification parameters and
    observe resource use under controlled load.

Suggested experiment report:

``` markdown
# Experiment: Redis cache comparison

## Question
Does caching reduce read latency for this workload?

## Environment
Machine, RAM, CPU, software versions, container configuration.

## Workload
Dataset size, request count, concurrency, warm-up period.

## Baseline
Results without cache.

## Experiment
Results with cache.

## Observations
Latency, throughput, CPU, memory, cache hit ratio.

## Conclusion
What changed? What trade-offs appeared?

## Reproduction
Exact commands and configuration.
```

------------------------------------------------------------------------

## 28. Definition of success

The project is successful when you can:

-   Build and explain the REST APIs.
-   Explain the schema, constraints, and indexes.
-   Implement secure authentication and authorization.
-   Explain access-token and refresh-token lifecycles.
-   Implement distributed rate limiting.
-   Explain cache invalidation and stale data.
-   Configure NGINX load balancing.
-   Manage database connections and explain PgBouncer pooling
    trade-offs.
-   Run and measure multiple API instances.
-   Explain Kafka partitions and consumer groups.
-   Implement RabbitMQ retries and dead-letter handling.
-   Implement a transactional outbox with concurrent publisher
    coordination.
-   Explain why outbox delivery can produce duplicates.
-   Implement idempotent consumers and order creation.
-   Explain and demonstrate a Saga.
-   Prevent inventory overselling under concurrent requests.
-   Handle uncertain payment outcomes safely.
-   Evolve event schemas without breaking consumers.
-   Build and recover a search index.
-   Create useful monitoring dashboards.
-   Propagate traces across HTTP and messaging boundaries.
-   Deploy with Docker Compose.
-   Deploy locally with Kubernetes.
-   Implement CI/CD and security checks.
-   Test failures and document recovery.
-   Explain architectural trade-offs and alternatives.

The goal is not to maximize the number of technologies. The goal is to
understand the problems, failure modes, and trade-offs behind the
architecture.

------------------------------------------------------------------------

## 29. Official learning resources

  Technology      Documentation
  --------------- ------------------------------------------------
  Python          https://docs.python.org/3/
  FastAPI         https://fastapi.tiangolo.com/
  PostgreSQL      https://www.postgresql.org/docs/
  SQLAlchemy      https://docs.sqlalchemy.org/
  Alembic         https://alembic.sqlalchemy.org/
  Redis           https://redis.io/docs/
  Valkey          https://valkey.io/
  PgBouncer       https://www.pgbouncer.org/
  Kafka           https://kafka.apache.org/documentation/
  RabbitMQ        https://www.rabbitmq.com/docs
  Debezium        https://debezium.io/documentation/
  Elasticsearch   https://www.elastic.co/guide/index.html
  OpenSearch      https://docs.opensearch.org/
  Docker          https://docs.docker.com/
  Kubernetes      https://kubernetes.io/docs/
  NGINX           https://nginx.org/en/docs/
  Prometheus      https://prometheus.io/docs/
  Grafana         https://grafana.com/docs/
  OpenTelemetry   https://opentelemetry.io/docs/
  Jaeger          https://www.jaegertracing.io/docs/
  Locust          https://docs.locust.io/
  Terraform       https://developer.hashicorp.com/terraform/docs

------------------------------------------------------------------------

## 30. Getting started: first milestone

Do not create every microservice on day one. First build a reliable
FastAPI application with PostgreSQL.

### Step 1 --- Create the repository

``` bash
mkdir ecommerce-backend
cd ecommerce-backend
git init
```

### Step 2 --- Create a virtual environment

``` bash
python -m venv .venv
```

Activate on Windows:

``` powershell
.venv\Scripts\activate
```

Activate on Linux/macOS:

``` bash
source .venv/bin/activate
```

### Step 3 --- Install initial dependencies

``` bash
pip install fastapi uvicorn
pip install sqlalchemy alembic
pip install "psycopg[binary]"
pip install pydantic-settings
pip install pyjwt "pwdlib[argon2]"
pip install pytest httpx
```

Pin and lock dependency versions once the initial environment works.

### Step 4 --- Create the initial application structure

``` text
app/
├── api/
│   └── v1/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── db/
├── tests/
└── main.py
```

### Step 5 --- Implement first endpoints

``` text
GET    /api/v1/health
POST   /api/v1/products
GET    /api/v1/products
GET    /api/v1/products/{id}
PATCH  /api/v1/products/{id}
DELETE /api/v1/products/{id}
```

### Step 6 --- Connect PostgreSQL

Implement database configuration, SQLAlchemy engine and sessions,
models, and Alembic migrations.

### Step 7 --- Write tests

Test every endpoint and business rule before introducing additional
infrastructure.

### First milestone completion checklist

-   [ ] FastAPI application starts.
-   [ ] Health endpoint works.
-   [ ] PostgreSQL connection works.
-   [ ] Alembic migration creates the schema.
-   [ ] Product CRUD works.
-   [ ] Order CRUD works.
-   [ ] Request validation works.
-   [ ] Error handling is consistent.
-   [ ] Unit tests pass.
-   [ ] Integration tests pass.
-   [ ] README setup instructions are reproducible.

------------------------------------------------------------------------

# Project motto

**Simple business logic. Deep engineering.**

Build incrementally. Measure everything. Document decisions. Experiment
with failures. Understand every technology you introduce.

The final achievement is not a system that merely contains many tools.
It is a system whose design, operation, failure modes, and trade-offs
you can confidently explain.
