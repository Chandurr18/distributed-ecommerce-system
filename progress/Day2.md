# E-Commerce Backend Engineering Lab

## Day 2 – Product & Inventory Services, Order Management, Idempotency, and Outbox Foundations

> This log records the progress discussed and confirmed in the Day 2 project conversation. It includes the Product and Inventory modules completed before the Order Management learning session, so the project history is not accidentally understated.

---

## 1. Project Context

The project is a production-style e-commerce backend being built incrementally.

- **Architecture:** Modular monolith first, with a longer-term path toward distributed services and microservices.
- **Backend:** Python + FastAPI.
- **Database:** PostgreSQL.
- **ORM:** SQLAlchemy.
- **Migrations:** Alembic.
- **Current engineering focus:** Correct business logic, database integrity, transactions, concurrency, idempotency, and reliable event publishing.

The guiding principle is to understand the problem and failure mode before introducing another technology.

---

## 2. Project Structure Discussed

The working application structure discussed in the project is:

```text
src/
├── api/
│   ├── health.py
│   ├── products.py
│   ├── inventory.py
│   └── orders.py
├── core/
│   ├── db.py
│   ├── config.py          # planned
│   ├── security.py        # planned
│   └── exceptions.py      # planned
├── models/
├── schemas/
├── repositories/
├── services/
├── dependencies/
└── main.py
```

The API version prefix is centralized in `src/main.py` using a parent router with the `/api/v1` prefix.

Database setup includes a SQLAlchemy engine, `SessionLocal`, declarative `Base`, and a `get_db` dependency. A database dependency module re-exports `get_db` for API use.

The project uses class-based repositories and services for the Product, Inventory, and Order modules.

> Note: Some originally uploaded model snapshots show earlier import paths or earlier versions of fields. The working code discussed later in the conversation uses imports such as `from src.core.db import Base`. When continuing development, use the current files in the working repository rather than copying an older uploaded snapshot over them.

---

## 3. Work Completed Before the Order Management Session: Product Module

The Product module was implemented and tested before the detailed Order Management learning session.

### Product functionality

The Product API supports:

- Create a product.
- Retrieve a product by ID.
- List products.
- Paginate product results.
- Search products.
- Filter by price.
- Sort product results.
- Update a product.
- Soft-delete a product by marking it inactive.

### Product architecture

The module follows the project's layered structure:

- **Model:** SQLAlchemy Product model.
- **Schema:** Request and response validation.
- **Repository:** Database queries and persistence.
- **Service:** Product business rules.
- **API:** FastAPI endpoints.

Repositories and services are class-based.

### Product progress

- Product model and database table were created.
- Product schemas, repository, service, and API were implemented.
- Product endpoints were tested successfully.
- Five sample products were later inserted for order-flow testing.

Sample products used during Day 2 testing:

| Product | Product ID | Price |
|---|---|---:|
| MacBook Air M3 | `11111111-1111-4111-8111-111111111111` | ₹89,999 |
| Dell XPS 15 | `22222222-2222-4222-8222-222222222222` | ₹1,29,999 |
| Logitech MX Master 3S | `33333333-3333-4333-8333-333333333333` | ₹8,999 |
| Keychron K2 | `44444444-4444-4444-8444-444444444444` | ₹7,499 |
| Samsung 990 PRO SSD | `55555555-5555-4555-8555-555555555555` | ₹16,999 |

---

## 4. Work Completed Before the Order Management Session: Inventory Module

The Inventory module was also implemented and tested before the detailed Order Management learning session.

### Inventory functionality

The Inventory API supports:

- Retrieve stock for a product.
- Add stock.
- Deduct stock.
- Check that the referenced product exists and is active.
- Prevent stock from becoming negative.
- Perform stock deduction safely using database-side/transactional protection.

### Inventory data model and rules

The Inventory model has:

- A UUID primary key.
- A `product_id` foreign key to `products.id`.
- A quantity.
- An update timestamp.

A unique constraint on `product_id` means each product has one inventory record. This became visible during test-data setup: trying to insert a second inventory row for the MacBook Air M3 produced a unique-constraint error. We queried and reused the existing row instead.

### Inventory architecture

Like Product, Inventory uses class-based repository and service layers, with schemas and FastAPI routes.

### Inventory progress

- Inventory model and database table were created.
- Inventory schemas, repository, service, and API were implemented.
- Inventory endpoints and stock rules were tested successfully.
- The existing MacBook Air M3 inventory record was later found to contain 50 units.

---

## 5. Order Management Models

The Order Management work uses two core models.

| Model | Responsibility |
|---|---|
| `Order` | Represents a customer's order, references a user, and stores total amount, status, and creation time. |
| `OrderItem` | Represents one product line in an order, including product, quantity, and unit price. |

Important concepts learned:

- `Order.user_id` is a foreign key to `users.id`.
- Each `OrderItem` references its parent order and a product.
- One order can contain multiple order-item rows.
- The backend calculates the order total using product prices from the database.
- Inventory is deducted during order creation.
- The unit price is stored on the order item so the order retains the price used at purchase time.

The Order and OrderItem models were reviewed field by field. The user correctly identified that an order belongs to a user and that each order item represents a product line.

---

## 6. Idempotency

### What idempotency means

Idempotency means that sending the same request more than once produces the same result as sending it once.

Example:

1. A customer submits an order.
2. The backend creates the order and deducts inventory.
3. The response is lost due to a network problem.
4. The customer retries the same request.
5. The backend returns the original response instead of creating another order.

Without idempotency, a retry could create duplicate orders and deduct inventory more than once.

### Idempotency key

The client sends a key with the order request:

```http
POST /api/v1/orders
Idempotency-Key: test-order-001
```

The key identifies one logical operation.

### Request hash

The Order Service calculates a SHA-256 hash from normalized request data.

The current service builds request data from:

- `user_id`
- `product_id`
- `quantity`

Order items are sorted by `product_id`, so changing the order of otherwise identical items does not change the normalized request.

The request is serialized using `json.dumps(..., sort_keys=True)`, encoded to bytes, and hashed with SHA-256.

Rules:

| Key already exists? | Request hash | Expected behaviour |
|---|---|---|
| No | — | Claim the key and process the order. |
| Yes | Same | Return the previously stored response. |
| Yes | Different | Reject with HTTP `409 Conflict`. |

A changed request must not silently reuse a key that already belongs to a different operation.

### Stored response

The idempotency record stores:

- The original HTTP response status.
- The original response body.

A retry with the same key and same request can return the original response without creating another order or deducting inventory again.

### Why `user_id` and `request_hash` are both needed

They have different responsibilities:

- `user_id` identifies the owner of the idempotency record and supports the foreign key and composite unique constraint.
- `request_hash` verifies whether the incoming request content matches the original request.

The request hash includes `user_id`, so two users submitting otherwise identical order data produce different hashes. However, the hash is not a replacement for the `user_id` database column.

### User-scoped idempotency keys

Alice and Bob should be able to use the same key independently. One user's key must not collide with another user's key.

The database constraint is:

```python
UniqueConstraint(
    "user_id",
    "idempotency_key",
    name="uq_user_idempotency_key",
)
```

This allows the same key for different users while preventing one user from creating two records with the same key.

UUID4 collisions are extraordinarily unlikely, but database constraints still protect correctness if a collision occurs.

---

## 7. Idempotency Model Update and Migration

The `IdempotencyRecord` model was updated during Day 2.

### Final model structure discussed

| Field | Purpose |
|---|---|
| `id` | UUID primary key. |
| `user_id` | Non-null UUID foreign key to `users.id`. |
| `idempotency_key` | Client-provided key. |
| `request_hash` | SHA-256 fingerprint of normalized request content. |
| `response_status` | Original HTTP response status. |
| `response_body` | Original response stored as JSON. |
| `created_at` | Record creation timestamp. |

Changes made:

- Added `user_id` as a non-null UUID foreign key to `users.id`.
- Removed global `unique=True` from `idempotency_key`.
- Added composite uniqueness on `(user_id, idempotency_key)`.
- Removed the empty-string default from `request_hash`, so a real hash is required.

The `users.id` primary key is a PostgreSQL UUID, so it can be referenced directly by the UUID foreign key.

### Alembic migration

Before migrating, the existing `idempotency_records` table was checked and had zero rows.

Generated the migration:

```bash
alembic revision --autogenerate -m "add user scope to idempotency records"
```

The generated migration was reviewed and edited to give the foreign key a stable name:

```text
fk_idempotency_records_user_id_users
```

Applied the migration:

```bash
alembic upgrade head
```

The table was inspected in PostgreSQL using:

```sql
\d idempotency_records
```

The user confirmed that the `user_id` column, foreign key, and composite unique constraint were present.

---

## 8. Repository: Claiming an Idempotency Key

The repository's `claim_idempotency_key()` method uses PostgreSQL's `INSERT ... ON CONFLICT DO NOTHING`.

The insert now supplies:

- `user_id`
- `idempotency_key`
- `request_hash`

The conflict target uses both `user_id` and `idempotency_key`.

Conceptual flow:

1. Try inserting a new idempotency record.
2. If insertion succeeds, return the new record and indicate it is new.
3. If the composite key already exists, retrieve the existing record.
4. Use `SELECT ... FOR UPDATE` when retrieving the existing row.

The Order Service call was updated to pass the user ID:

```python
record, is_new = self.repository.claim_idempotency_key(
    payload.user_id,
    idempotency_key,
    request_hash,
)
```

### Database concepts learned

**Unique constraint**

Defines a database rule that prevents duplicate values or duplicate combinations of values.

**`ON CONFLICT DO NOTHING`**

Tells PostgreSQL not to insert another row when the specified uniqueness rule conflicts. It is useful for handling uniqueness conflicts, including simultaneous requests.

**`SELECT ... FOR UPDATE`**

Locks a selected existing row until the transaction commits or rolls back, coordinating concurrent access to that row.

**SQLAlchemy result methods**

| Method | Behaviour |
|---|---|
| `.scalar_one()` | Requires exactly one result; raises an exception for zero or multiple results. |
| `.scalar_one_or_none()` | Returns one result or `None`. |
| `.scalars().all()` | Returns all matching scalar results as a list. |

---

## 9. Database Transactions and ACID

The Order Service groups related database changes in one transaction:

- Create the order.
- Create order items.
- Deduct inventory.
- Store the idempotency response.
- Create the outbox event.

The service commits after these operations succeed. If an exception occurs, it rolls back the transaction.

> **Key takeaway: Database transaction = All-or-nothing execution.**
>
> Either every operation succeeds, or all changes roll back.

ACID properties discussed:

- **Atomicity:** All operations succeed or none do.
- **Consistency:** Data remains valid.
- **Isolation:** Concurrent transactions are controlled so they do not produce invalid results.
- **Durability:** Committed changes survive failures.

Kafka or RabbitMQ is not required to make these database operations atomic. PostgreSQL transactions handle the database changes.

---

## 10. Concurrency Concepts

Two requests can arrive almost simultaneously with the same user's idempotency key.

The composite unique constraint prevents both transactions from successfully inserting the same key.

`ON CONFLICT DO NOTHING` handles the uniqueness conflict without raising the normal duplicate-insert error. The competing request can then retrieve the existing record and use row locking while checking its stored result.

Important distinctions:

- **Unique constraint:** Defines the no-duplicates rule.
- **`ON CONFLICT`:** Defines how PostgreSQL handles an insert that violates the specified uniqueness rule.
- **Race condition:** A timing problem where concurrent operations compete.
- **Row lock:** Coordinates access to an existing database row.

If the first transaction rolls back, its uncommitted insert is rolled back and its lock is released. A competing transaction can then proceed; it may successfully insert the key if no committed record exists.

---

## 11. Order Service Flow Reviewed

The shared `OrderService` includes these main responsibilities:

### `create_order()`

- Builds normalized request data.
- Generates a SHA-256 request hash.
- Claims the user-scoped idempotency key.
- Returns the stored response for a matching retry.
- Rejects reuse of the same key with a different request hash.
- Checks that the user exists.
- Checks that products exist and are active.
- Locks inventory rows using `SELECT ... FOR UPDATE`.
- Checks available stock and deducts requested quantities.
- Calculates the total using database product prices.
- Creates the order and order items.
- Stores the original response in the idempotency record.
- Adds an `order.created` outbox event.
- Commits the transaction, or rolls back on an exception.

### Other service methods reviewed

- `get_order_by_id()` retrieves an order for a given user and serializes its items.
- `get_all_orders()` retrieves paginated orders and groups their order items.
- `cancel_order()` locks the order, permits cancellation only while pending, restores inventory, changes the status to cancelled, adds an `order.cancelled` outbox event, and commits.

---

## 12. Transactional Outbox – Introduction

The Order Service creates an `OutboxEvent` in the same database transaction as the order.

Example event:

```text
order.created
```

The event payload contains order-related information such as:

- Order ID.
- User ID.
- Total amount.
- Product IDs and quantities.

### Why use an outbox?

If an order is committed but the server crashes before publishing an event to Kafka, the event must not be lost.

Saving the event in PostgreSQL in the same transaction preserves it for later publishing.

Conceptual flow:

```text
PostgreSQL transaction
    ├── Create order
    ├── Deduct inventory
    ├── Save idempotency response
    └── Save outbox event
             |
           COMMIT
             |
      Outbox Publisher
             |
           Kafka
             |
       Other consumers
```

After successful publishing, the publisher should mark the event as published and record its publication time.

Important limitation:

The outbox makes the event durable alongside the database transaction. It does not guarantee exactly-once delivery to Kafka. A publisher may send an event and crash before recording it as published, causing a retry and duplicate delivery. Consumers must be designed to handle duplicates.

**Day 2 implementation status:** The Order Service saves outbox events in PostgreSQL. The Outbox Publisher and Kafka integration have not yet been implemented.

---

## 13. Test Data Used

A test user was created directly in PostgreSQL:

```text
email: order-test@example.com
user_id: 04e7aa5b-83ee-4468-a79d-d379698a4e0c
```

The password hash value used for this test-only row was a placeholder:

```text
test-only-password-hash
```

This was only to satisfy the current user table's non-null field. It is not a valid production authentication setup.

The selected product:

```text
product: MacBook Air M3
product_id: 11111111-1111-4111-8111-111111111111
unit price: 89999.00
initial inventory quantity: 50
```

The product already had an inventory row. An attempted second inventory insert failed because `product_id` is unique. The existing row was queried and reused.

---

## 14. Order and Idempotency Tests

Tests were performed through FastAPI Swagger UI and a small Python concurrency script.

### Test 1 – Successful order creation

Used:

```http
Idempotency-Key: test-order-001
```

Payload:

```json
{
  "user_id": "04e7aa5b-83ee-4468-a79d-d379698a4e0c",
  "items": [
    {
      "product_id": "11111111-1111-4111-8111-111111111111",
      "quantity": 2
    }
  ]
}
```

Observed:

- HTTP `201`.
- One order created.
- Total amount: `179998.00`.
- Status: `pending`.
- Inventory decreased from 50 to 48.

### Test 2 – Same key and same payload

The exact same request was sent again using `test-order-001`.

Observed:

- Same order ID returned.
- Same response body returned.
- No second order created.
- Inventory remained at 48.

Database verification:

| Check | Result |
|---|---:|
| Orders for test user | 1 |
| MacBook inventory | 48 |
| Records for `test-order-001` | 1 |

### Test 3 – Same key and changed payload

The quantity was changed from 2 to 3, while reusing `test-order-001`.

Observed response:

```json
{
  "detail": "Idempotency key was used with a different request"
}
```

The API rejected the changed request with HTTP `409 Conflict`.

No new order was created and no additional inventory was deducted.

### Test 4 – Two simultaneous identical requests

Created and ran `test_concurrent_orders.py` using Python's `ThreadPoolExecutor` with two workers.

Both requests used:

```text
Idempotency-Key: concurrent-test-001
```

Both requests returned:

- HTTP `201`.
- The same order ID.
- The same response body.

Database verification:

| Check | Result |
|---|---:|
| Orders for test user | 2 |
| MacBook inventory | 46 |
| Records for `concurrent-test-001` | 1 |

This confirmed that the two simultaneous requests produced one order and one inventory deduction.

### Test 5 – Insufficient stock and transaction rollback

Sent a request for 100 MacBook Air M3 units while only 46 were available.

Used:

```text
Idempotency-Key: rollback-test-001
```

Observed response detail:

```json
{
  "detail": "Insufficient stock for product MacBook Air M3"
}
```

Database verification:

| Check | Result |
|---|---:|
| Orders for test user | 2 |
| MacBook inventory | 46 |
| Records for `rollback-test-001` | 0 |

The failed transaction left no order, no inventory deduction, and no idempotency record.

This demonstrated all-or-nothing transaction behaviour for the insufficient-stock failure case.

### Test data state at the end of Day 2

| Item | Final observed state |
|---|---:|
| Orders belonging to test user | 2 |
| MacBook Air M3 inventory | 46 |
| `test-order-001` idempotency records | 1 |
| `concurrent-test-001` idempotency records | 1 |
| `rollback-test-001` idempotency records | 0 |

The failed changed-payload request reused `test-order-001`; it did not create another idempotency record.

---

## 15. Day 2 Progress Checklist

### Foundation and core modules

- [x] Python/FastAPI/PostgreSQL/SQLAlchemy/Alembic foundation from Day 1.
- [x] Product model and migration.
- [x] Inventory model and migration.
- [x] Product schemas, repository, service, and API.
- [x] Inventory schemas, repository, service, and API.
- [x] Product endpoints tested.
- [x] Inventory endpoints and stock rules tested.
- [x] Sample products available in PostgreSQL.

### Order Management and reliability concepts

- [x] Reviewed Order and OrderItem models.
- [x] Learned idempotency.
- [x] Learned request hashing and request normalization.
- [x] Learned why the original response is stored.
- [x] Added `user_id` to `IdempotencyRecord`.
- [x] Added composite uniqueness on `(user_id, idempotency_key)`.
- [x] Removed the empty default from `request_hash`.
- [x] Generated and applied the Alembic migration.
- [x] Updated `claim_idempotency_key()` to use the composite key.
- [x] Learned `ON CONFLICT DO NOTHING`.
- [x] Learned `SELECT ... FOR UPDATE`.
- [x] Learned SQLAlchemy scalar result methods.
- [x] Learned database transactions and ACID basics.
- [x] Tested successful order creation.
- [x] Tested same-key, same-payload retry.
- [x] Tested same-key, changed-payload rejection.
- [x] Tested two simultaneous identical requests.
- [x] Tested insufficient stock and transaction rollback.
- [x] Learned the purpose of the Transactional Outbox Pattern.

### Still pending

- [ ] Inspect `outbox_event_mode.py` in detail.
- [ ] Implement the Outbox Publisher.
- [ ] Integrate Kafka publishing.
- [ ] Coordinate multiple publishers safely.
- [ ] Handle publisher retries and duplicate event delivery.
- [ ] Test the complete outbox-to-Kafka flow.
- [ ] Implement idempotent event consumers.
- [ ] Add automated tests beyond the manual API and concurrency checks.

---

## 16. Day 3 Starting Point

Continue from the exact point where Day 2 ended:

1. Inspect the actual `outbox_event_mode.py` model field by field.
2. Review the current outbox repository operations.
3. Design and implement an Outbox Publisher.
4. Publish pending events to Kafka.
5. Mark events as published after successful delivery.
6. Handle publisher crashes, retries, and duplicate delivery.
7. Test the complete outbox-to-Kafka flow.

Do not assume the publisher or Kafka integration has already been implemented.

---

## Day 2 Status

**Product and Inventory modules were already implemented and tested. Order creation, idempotency, concurrent duplicate-request handling, and insufficient-stock rollback were then tested successfully. The Transactional Outbox Pattern was introduced, but its publisher and Kafka integration remain pending.**

Project: E-Commerce Backend Engineering Lab  
Architecture: Modular Monolith  
Backend: FastAPI  
Database: PostgreSQL  
ORM and migrations: SQLAlchemy + Alembic

---

# Project motto

**Simple business logic. Deep engineering.**

Build incrementally. Measure everything. Document decisions. Experiment with failures. Understand every technology you introduce.